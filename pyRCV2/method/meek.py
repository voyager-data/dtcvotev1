#   pyRCV2: Preferential vote counting
#   Copyright © 2020–2021  Lee Yingtong Li (RunasSudo)
#
#   This program is free software: you can redistribute it and/or modify
#   it under the terms of the GNU Affero General Public License as published by
#   the Free Software Foundation, either version 3 of the License, or
#   (at your option) any later version.
#
#   This program is distributed in the hope that it will be useful,
#   but WITHOUT ANY WARRANTY; without even the implied warranty of
#   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#   GNU Affero General Public License for more details.
#
#   You should have received a copy of the GNU Affero General Public License
#   along with this program.  If not, see <https://www.gnu.org/licenses/>.

DEBUG_MEEK = False

__pragma__ = lambda x: None

from pyRCV2.method.base_stv import BaseSTVCounter, STVException
from pyRCV2.model import CandidateState, CountCard
from pyRCV2.numbers import Num
from pyRCV2.safedict import SafeDict


class MeekCountCard(CountCard):
    def __init__(self, *args):
        CountCard.__init__(self, *args)
        self.keep_value = Num(
            1)  # Not read by the count algorithm, but can be used for auditing

    def clone(self):
        """Overrides CountCard.clone"""
        result = MeekCountCard()
        result.orig_votes = self.orig_votes
        result.transfers = self.transfers
        #result.parcels = [[(b[0].clone(), b[1]) for b in p] for p in self.parcels]
        result.state = self.state
        result.order_elected = self.order_elected
        result.keep_value = keep_value
        return result


class BallotTree:
    def __init__(self):
        self.num = Num('0')
        self.ballots = []  # List of tuples (ballot, idx)

        self.next_preferences = None  # SafeDict: Candidate -> BallotTree
        self.next_exhausted = None  # BallotTree

    def descend_tree(self):
        """Expand one further level of the tree"""
        if self.next_exhausted is not None:
            raise Exception('Attempt to descend into already descended tree')

        self.next_preferences = SafeDict()
        self.next_exhausted = BallotTree()

        for ballot, idx in self.ballots:
            if idx is None:
                idx = 0
            else:
                idx = idx + 1

            if idx < len(ballot.preferences):
                cand = ballot.preferences[idx]

                __pragma__('opov')
                if cand not in self.next_preferences:
                    np = BallotTree()
                    self.next_preferences[cand] = np
                else:
                    np = self.next_preferences[cand]

                np.num += ballot.value
                __pragma__('noopov')
                np.ballots.append((ballot, idx))
            else:
                __pragma__('opov')
                self.next_exhausted.num += ballot.value
                __pragma__('noopov')
                self.next_exhausted.ballots.append((ballot, idx))


class MeekSTVCounter(BaseSTVCounter):
    def describe_options(self):
        """Overrides BaseSTVCounter.describe_options"""
        return '--method meek ' + BaseSTVCounter.describe_options(self)

    def __init__(self, *args):
        BaseSTVCounter.__init__(self, *args)

        # Convert to MeekCountCard
        self.candidates = SafeDict([(c, MeekCountCard())
                                    for c in self.election.candidates])
        for candidate in self.election.withdrawn:
            __pragma__('opov')
            self.candidates[candidate].state = CandidateState.WITHDRAWN
            __pragma__('noopov')

        self._quota_tolerance = Num('1.0001')

        # For tree packing
        self.ballots_tree = BallotTree()
        for ballot in self.election.ballots:
            __pragma__('opov')
            self.ballots_tree.num += ballot.value
            __pragma__('noopov')
            self.ballots_tree.ballots.append((ballot, None))

    def reset(self):
        if self.options['quota_mode'] != 'progressive':
            raise STVException('Meek method requires --quota-mode progressive')
        if self.options['bulk_exclude']:
            raise STVException(
                'Meek method is incompatible with --bulk_exclude')
        if self.options['defer_surpluses']:
            raise STVException(
                'Meek method is incompatible with --defer-surpluses')
        if self.options['papers'] != 'both':
            raise STVException(
                'Meek method is incompatible with --transferable-only')
        if self.options['exclusion'] != 'one_round':
            raise STVException('Meek method requires --exclusion one_round')
        if self.options['round_votes'] is not None:
            raise STVException(
                'Meek method is incompatible with --round-votes')
        if self.options['round_tvs'] is not None:
            raise STVException('Meek method is incompatible with --round-tvs')
        if self.options['round_weights'] is not None:
            raise STVException(
                'Meek method is incompatible with --round-weights')

        self._exclusion = None  # Optimisation to avoid re-collating/re-sorting ballots

        self.distribute_first_preferences()
        self.logs.append('First preferences distributed.')

        self.quota = None
        self.vote_required_election = None  # For ERS97
        self.compute_quota()
        self.logs.append(
            self.total.pp(2) + ' usable votes, so the quota is ' +
            self.quota.pp(2) + '.')
        self.elect_meeting_quota()

        return self.make_result('First preferences')

    def distribute_recursively(self, tree, remaining_multiplier):
        if tree.next_exhausted is None:
            tree.descend_tree()

        # Credit votes at this level
        for candidate, cand_tree in tree.next_preferences.items():
            __pragma__('opov')
            count_card = self.candidates[candidate]
            __pragma__('noopov')

            if count_card.state == CandidateState.HOPEFUL:
                # Hopeful candidate has keep value 1, so transfer entire remaining value
                __pragma__('opov')
                count_card.transfers += remaining_multiplier * cand_tree.num
                __pragma__('noopov')
            elif count_card.state == CandidateState.EXCLUDED or count_card.state == CandidateState.WITHDRAWN:
                # Excluded candidate has keep value 0, so skip over this candidate
                # Recurse
                self.distribute_recursively(cand_tree, remaining_multiplier)
            elif count_card.state == CandidateState.ELECTED:
                # Transfer according to elected candidate's keep value
                __pragma__('opov')
                count_card.transfers += remaining_multiplier * cand_tree.num * count_card.keep_value
                new_remaining_multiplier = remaining_multiplier * (
                    Num(1) - count_card.keep_value)
                __pragma__('noopov')
                # Recurse
                self.distribute_recursively(cand_tree,
                                            new_remaining_multiplier)
            else:
                raise STVException('Unexpected candidate state')

        # Credit exhausted votes at this level
        __pragma__('opov')
        self.exhausted.transfers += remaining_multiplier * tree.next_exhausted.num
        __pragma__('noopov')

    def distribute_first_preferences(self):
        """
		Overrides BaseSTVCounter.distribute_first_preferences
		Unlike in other STV methods, this is called not only as part of reset() but also at other stages
		"""

        # Reset the count
        # Carry over candidate states, keep values, etc.
        new_candidates = SafeDict()
        for candidate, count_card in self.candidates.items():
            new_count_card = MeekCountCard()
            new_count_card.state = count_card.state
            new_count_card.keep_value = count_card.keep_value
            new_count_card.order_elected = count_card.order_elected

            __pragma__('opov')
            new_candidates[candidate] = new_count_card
            __pragma__('noopov')

        self.candidates = new_candidates
        self.exhausted = CountCard()
        self.loss_fraction = CountCard()

        # Distribute votes
        self.distribute_recursively(self.ballots_tree, Num('1'))

        # Recompute transfers
        if len(self.step_results) > 0:
            last_result = self.step_results[len(self.step_results) - 1]
            __pragma__('opov')
            for candidate, count_card in self.candidates.items():
                count_card.continue_from(last_result.candidates[candidate])
            self.exhausted.continue_from(last_result.exhausted)
            self.loss_fraction.continue_from(last_result.loss_fraction)
            __pragma__('noopov')

    def distribute_surpluses(self):
        """
		Overrides BaseSTVCounter.distribute_surpluses
		Surpluses are distributed in Meek STV by recomputing the keep values, and redistributing all votes
		"""

        # Do surpluses need to be distributed?
        __pragma__('opov')
        has_surplus = [(c, cc) for c, cc in self.candidates.items()
                       if cc.state == CandidateState.ELECTED and cc.votes /
                       self.quota > self._quota_tolerance]
        __pragma__('noopov')

        if len(has_surplus) > 0:
            num_iterations = 0
            orig_quota = self.quota
            while len(has_surplus) > 0:
                num_iterations += 1

                # Recompute keep values
                for candidate, count_card in has_surplus:
                    __pragma__('opov')
                    # Perform in steps to avoid rounding error
                    count_card.keep_value *= self.quota
                    count_card.keep_value /= count_card.votes
                    __pragma__('noopov')

                # Redistribute votes
                self.distribute_first_preferences()

                # Recompute quota if more ballots have become exhausted
                self.compute_quota()

                __pragma__('opov')
                has_surplus = [
                    (c, cc) for c, cc in self.candidates.items()
                    if cc.state == CandidateState.ELECTED and cc.votes /
                    self.quota > self._quota_tolerance
                ]
                __pragma__('noopov')

                if DEBUG_MEEK:
                    break

            if num_iterations == 1:
                self.logs.append(
                    'Surpluses distributed, requiring 1 iteration.')
            else:
                self.logs.append('Surpluses distributed, requiring ' +
                                 str(num_iterations) + ' iterations.')

            self.logs.append('Keep values of elected candidates are: ' +
                             ', '.join([
                                 c.name + ' (' + cc.keep_value.pp(2) + ')'
                                 for c, cc in self.candidates.items()
                                 if cc.state == CandidateState.ELECTED
                             ]) + '.')

            if self.quota != orig_quota:
                self.logs.append(
                    self.total.pp(2) + ' usable votes, so the quota is ' +
                    self.quota.pp(2) + '.')

            # Declare elected any candidates meeting the quota as a result of surpluses
            # NB: We could do this earlier, but this shows the flow of the election more clearly in the count sheet
            self.elect_meeting_quota()

            return self.make_result('Surpluses distributed')

    def do_exclusion(self, candidates_excluded):
        """
		Overrides BaseSTVCounter.do_exclusion
		"""
        for candidate, count_card in candidates_excluded:
            count_card.state = CandidateState.EXCLUDED

        # Redistribute votes
        self.distribute_first_preferences()

    def elect_meeting_quota(self):
        """
		Overrides BaseSTVCounter.elect_meeting_quota
		Skip directly to CandidateState.ELECTED
		"""

        # Does a candidate meet the quota?
        meets_quota = [
            (c, cc) for c, cc in self.candidates.items()
            if cc.state == CandidateState.HOPEFUL and self.meets_quota(cc)
        ]

        if len(meets_quota) > 0:
            meets_quota.sort(key=lambda x: x[1].votes, reverse=True)
            if len(meets_quota) == 1:
                self.logs.append(meets_quota[0][0].name +
                                 ' meets the quota and is elected.')
            else:
                self.logs.append(
                    self.pretty_join([c.name for c, cc in meets_quota]) +
                    ' meet the quota and are elected.')

            # Declare elected any candidate who meets the quota
            while len(meets_quota) > 0:
                x = self.choose_highest(meets_quota)
                candidate, count_card = x[0], x[1]

                count_card.state = CandidateState.ELECTED
                self.num_elected += 1
                count_card.order_elected = self.num_elected

                meets_quota.remove(x)

    def compute_quota(self):
        """
		Overrides BaseSTVCounter.compute_quota
		Do not log quota changes
		"""

        __pragma__('opov')
        self.total = sum((cc.votes for c, cc in self.candidates.items()),
                         Num('0'))
        self.loss_fraction.transfers += (
            self.total_orig - self.total -
            self.exhausted.votes) - self.loss_fraction.votes

        if self.options['quota'] == 'droop' or self.options[
                'quota'] == 'droop_exact':
            self.quota = self.total / Num(self.election.seats + 1)
        elif self.options['quota'] == 'hare' or self.options[
                'quota'] == 'hare_exact':
            self.quota = self.total / Num(self.election.seats)
        else:
            raise STVException('Invalid quota option')

        if self.options['round_quota'] is not None:
            if self.options['quota'] == 'droop' or self.options[
                    'quota'] == 'hare':
                # Increment to next available increment
                factor = Num(10).__pow__(self.options['round_quota'])
                __pragma__('opov')
                self.quota = (
                    (self.quota * factor).__floor__() + Num(1)) / factor
                __pragma__('noopov')
            else:
                # Round up (preserving the original quota if exact)
                self.quota = self.quota.round(self.options['round_quota'],
                                              self.quota.ROUND_UP)

        __pragma__('noopov')
