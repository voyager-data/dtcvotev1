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

__pragma__ = lambda x: None

from pyRCV2.model import BallotInCount, CandidateState, CountCard, CountCompleted, CountStepResult
import pyRCV2.numbers
from pyRCV2.numbers import Num
from pyRCV2.safedict import SafeDict
import pyRCV2.ties


class STVException(Exception):
    def __init__(self, message):
        Exception.__init__(self)
        self.message = message


class BaseSTVCounter:
    """
	Basic STV counter for various different variations
	"""
    def __init__(self, election, options=None):
        self.election = election

        # Default options
        self.options = {
            'bulk_elect': True,  # Bulk election?
            'bulk_exclude': False,  # Bulk exclusion?
            'defer_surpluses': False,  # Defer surpluses?
            'quota': 'droop',  # 'droop', 'droop_exact', 'hare' or 'hare_exact'
            'quota_criterion': 'geq',  # 'geq' or 'gt'
            'quota_mode': 'static',  # 'static', 'progressive' or 'ers97'
            'surplus_order': 'size',  # 'size' or 'order'
            'papers': 'both',  # 'both' or 'transferable'
            'exclusion':
            'one_round',  # 'one_round', 'parcels_by_order', 'by_value' or 'wright'
            'ties': [],  # List of tie strategies (e.g. TiesRandom)
            'round_quota': None,  # Number of decimal places or None
            'round_votes': None,  # Number of decimal places or None
            'round_tvs': None,  # Number of decimal places or None
            'round_weights': None,  # Number of decimal places or None
        }

        if options is not None:
            self.options.update(options)

        self.candidates = SafeDict([(c, CountCard())
                                    for c in self.election.candidates])
        self.exhausted = CountCard()
        self.loss_fraction = CountCard()

        self.total_orig = sum((b.value for b in self.election.ballots),
                              Num('0'))

        self.logs = []
        self.step_results = []
        self.num_elected = 0
        self.num_excluded = 0
        self.num_withdrawn = 0

        # Withdraw candidates
        for candidate in self.election.withdrawn:
            __pragma__('opov')
            self.candidates[candidate].state = CandidateState.WITHDRAWN
            __pragma__('noopov')
            self.num_withdrawn += 1

    def reset(self):
        """
		Public function:
		Perform the first step (distribute first preferences)
		Does not reset the states of candidates, etc.
		"""

        self._exclusion = None  # Optimisation to avoid re-collating/re-sorting ballots

        self.distribute_first_preferences()
        self.logs.append('First preferences distributed.')

        self.quota = None
        self.vote_required_election = None  # For ERS97
        self.compute_quota()
        self.elect_meeting_quota()

        return self.make_result('First preferences')

    def distribute_first_preferences(self):
        """
		Distribute first preferences (called as part of the reset() step)
		"""

        for ballot in self.election.ballots:
            __pragma__('opov')
            for i, candidate in enumerate(ballot.preferences):
                count_card = self.candidates[candidate]

                if count_card.state == CandidateState.HOPEFUL:
                    count_card.transfers += ballot.value
                    if len(count_card.parcels) == 0:
                        count_card.parcels.append(
                            [BallotInCount(ballot, Num(ballot.value), i)])
                    else:
                        count_card.parcels[0].append(
                            BallotInCount(ballot, Num(ballot.value), i))
                    break
            else:
                # No available preference
                self.exhausted.transfers += ballot.value
                #self.exhausted.parcels[0].append((ballot, Num(ballot.value)))
            __pragma__('noopov')

    def step(self):
        """
		Public function:
		Perform one step of the STV count
		"""

        # Step count cards
        self.step_count_cards()

        # Check if done
        result = self.before_surpluses()
        if result:
            return result

        # Distribute surpluses
        result = self.distribute_surpluses()
        if result:
            return result

        # Check if done (2)
        result = self.before_exclusion()
        if result:
            return result

        # Insufficient winners and no surpluses to distribute
        # Exclude the lowest ranked hopeful(s)
        result = self.exclude_candidates()
        if result:
            return result

        raise STVException('Unable to complete step')  # pragma: no cover

    def step_count_cards(self):
        """
		Reset the count cards for the beginning of a new step
		"""

        for candidate, count_card in self.candidates.items():
            count_card.step()
        self.exhausted.step()
        self.loss_fraction.step()

    def before_surpluses(self):
        """
		Check if the count can be completed before distributing surpluses
		"""

        # Have sufficient candidates been elected?
        if self.num_elected >= self.election.seats:
            __pragma__('opov')
            return CountCompleted(
                'Count complete',
                self.logs,
                self.candidates,
                self.exhausted,
                self.loss_fraction,
                self.total + self.exhausted.votes + self.loss_fraction.votes,
                self.quota,
                self.vote_required_election,
            )
            __pragma__('noopov')

        # Are there just enough candidates to fill all the seats?
        if self.options['bulk_elect']:
            # Include EXCLUDING to avoid interrupting an exclusion
            if len(self.election.candidates
                   ) - self.num_withdrawn - self.num_excluded + sum(
                       1 for c, cc in self.candidates.items() if cc.state ==
                       CandidateState.EXCLUDING) <= self.election.seats:
                # Declare elected all remaining candidates
                candidates_elected = [(c, cc)
                                      for c, cc in self.candidates.items()
                                      if cc.state == CandidateState.HOPEFUL]
                if len(candidates_elected) == 1:
                    self.logs.append(
                        candidates_elected[0][0].name +
                        ' is elected to fill the remaining vacancy.')
                else:
                    self.logs.append(
                        self.pretty_join(
                            [c.name for c, cc in candidates_elected]) +
                        ' are elected to fill the remaining vacancies.')

                for candidate, count_card in candidates_elected:
                    count_card.state = CandidateState.PROVISIONALLY_ELECTED
                    self.num_elected += 1
                    count_card.order_elected = self.num_elected

                return self.make_result('Bulk election')

    def can_defer_surpluses(self, has_surplus):
        """
		Determine if the specified surpluses can be deferred
		"""

        # Do not defer if this could change the last 2 candidates
        __pragma__('opov')
        total_surpluses = sum((cc.votes - self.quota for c, cc in has_surplus),
                              Num(0))
        __pragma__('noopov')
        hopefuls = [(c, cc) for c, cc in self.candidates.items()
                    if cc.state == CandidateState.HOPEFUL]
        hopefuls.sort(key=lambda x: x[1].votes)
        __pragma__('opov')
        if total_surpluses > hopefuls[1][1].votes - hopefuls[0][1].votes:
            return False
        __pragma__('noopov')

        # Do not defer if this could affect a bulk exclusion
        if self.options['bulk_exclude']:
            to_bulk_exclude = self.candidates_to_bulk_exclude(hopefuls)
            if len(to_bulk_exclude) > 0:
                total_excluded = sum((cc.votes for c, cc in to_bulk_exclude),
                                     Num(0))
                __pragma__('opov')
                if total_surpluses > hopefuls[len(to_bulk_exclude) +
                                              1][1].votes - total_excluded:
                    return False
                __pragma__('opov')

        # Can defer surpluses
        self.logs.append('Distribution of surpluses totalling ' +
                         total_surpluses.pp(2) + ' votes will be deferred.')
        return True

    def distribute_surpluses(self):
        """
		Distribute surpluses, if any
		"""

        # Do not interrupt an exclusion
        if any(cc.state == CandidateState.EXCLUDING
               for c, cc in self.candidates.items()):
            return

        candidate_surplus, count_card = None, None

        # Are we distributing a surplus?
        has_surplus = [(c, cc) for c, cc in self.candidates.items()
                       if cc.state == CandidateState.DISTRIBUTING_SURPLUS]
        if len(has_surplus) > 0:
            candidate_surplus, count_card = has_surplus[0]
        else:
            # Do surpluses need to be distributed?
            __pragma__('opov')
            has_surplus = [(c, cc) for c, cc in self.candidates.items()
                           if cc.state == CandidateState.PROVISIONALLY_ELECTED
                           and cc.votes > self.quota]
            __pragma__('noopov')

            if len(has_surplus) > 0:
                # Distribute surpluses in specified order
                if self.options['surplus_order'] == 'size':
                    has_surplus.sort(key=lambda x: x[1].votes, reverse=True)
                elif self.options['surplus_order'] == 'order':
                    has_surplus.sort(key=lambda x: x[1].order_elected)
                else:  # pragma: no cover
                    raise STVException('Invalid surplus order option')

                # Attempt to defer all remaining surpluses if possible
                if self.options['defer_surpluses']:
                    if self.can_defer_surpluses(has_surplus):
                        has_surplus = []

                if len(has_surplus) > 0:
                    # Cannot defer any surpluses
                    if self.options['surplus_order'] == 'size':
                        candidate_surplus, count_card = self.choose_highest(
                            has_surplus)  # May need to break ties
                    elif self.options['surplus_order'] == 'order':
                        candidate_surplus, count_card = has_surplus[
                            0]  # Ties were already broken when these were assigned

        if candidate_surplus is not None:
            count_card.state = CandidateState.DISTRIBUTING_SURPLUS

            __pragma__('opov')
            surplus = count_card.votes - self.quota
            __pragma__('noopov')

            # Transfer surplus
            self.do_surplus(candidate_surplus, count_card, surplus)

            # Declare elected any candidates meeting the quota as a result of surpluses
            self.compute_quota()

            self.elect_meeting_quota()

            return self.make_result('Surplus of ' + candidate_surplus.name)

    def do_surplus(self, candidate_surplus, count_card, surplus):
        """
		Transfer the surplus of the given candidate
		Subclasses must override this function
		"""
        raise NotImplementedError('Method not implemented')  # pragma: no cover

    def before_exclusion(self):
        """
		Check before excluding a candidate
		"""

        # If we did not perform bulk election in before_surpluses: Are there just enough candidates to fill all the seats?
        if not self.options['bulk_elect']:
            if len(
                    self.election.candidates
            ) - self.num_withdrawn - self.num_excluded <= self.election.seats:
                # Declare elected one remaining candidate at a time
                hopefuls = [(c, cc) for c, cc in self.candidates.items()
                            if cc.state == CandidateState.HOPEFUL]
                hopefuls.sort(key=lambda x: x[1].votes, reverse=True)

                order_elected = []

                while len(hopefuls) > 0:
                    x = self.choose_highest(hopefuls)

                    x[1].state = CandidateState.PROVISIONALLY_ELECTED
                    self.num_elected += 1
                    x[1].order_elected = self.num_elected

                    order_elected.append(x[0].name)
                    hopefuls.remove(x)

                if len(order_elected) == 1:
                    self.logs.append(
                        order_elected[0].name +
                        ' is elected to fill the remaining vacancy.')
                else:
                    self.logs.append(
                        self.pretty_join(order_elected) +
                        ' are elected to fill the remaining vacancies.')

                return self.make_result('Bulk election')

    def exclude_candidates(self):
        """
		Exclude the lowest ranked hopeful(s)
		"""

        candidates_excluded = self.candidates_to_exclude()
        for candidate, count_card in candidates_excluded:
            if count_card.state != CandidateState.EXCLUDING:
                count_card.state = CandidateState.EXCLUDING
                self.num_excluded += 1
                count_card.order_elected = -self.num_excluded

        # Handle Wright STV
        if self.options['exclusion'] == 'wright':
            for candidate, count_card in candidates_excluded:
                count_card.state = CandidateState.EXCLUDED

            # Reset the count
            # Carry over certain candidate states
            new_candidates = SafeDict()
            for candidate, count_card in self.candidates.items():
                new_count_card = CountCard()

                if count_card.state == CandidateState.WITHDRAWN:
                    new_count_card.state = CandidateState.WITHDRAWN
                elif count_card.state == CandidateState.EXCLUDED:
                    new_count_card.state = CandidateState.EXCLUDED

                __pragma__('opov')
                new_candidates[candidate] = new_count_card
                __pragma__('noopov')

            self.candidates = new_candidates
            self.exhausted = CountCard()
            self.loss_fraction = CountCard()
            self.num_elected = 0

            step_results = self.step_results  # Carry over step results
            result = self.reset()
            self.step_results = step_results
            result.comment = 'Exclusion of ' + ', '.join(
                [c.name for c, cc in candidates_excluded])

            return result

        # Exclude this candidate
        self.do_exclusion(candidates_excluded)

        # Declare any candidates meeting the quota as a result of exclusion
        self.compute_quota()

        self.elect_meeting_quota()

        return self.make_result(
            'Exclusion of ' +
            ', '.join([c.name for c, cc in candidates_excluded]))

    def candidates_to_bulk_exclude(self, hopefuls):
        """
		Determine which candidates can be bulk excluded
		Returns List[Tuple[Candidate, CountCard]]
		"""

        remaining_candidates = len(
            self.election.candidates) - self.num_withdrawn - self.num_excluded
        __pragma__('opov')
        total_surpluses = sum(
            (cc.votes - self.quota
             for c, cc in self.candidates.items() if cc.votes > self.quota),
            Num(0))
        __pragma__('noopov')

        # Attempt to exclude as many candidates as possible
        for i in range(0, len(hopefuls)):
            try_exclude = hopefuls[0:len(hopefuls) - i]

            # Do not exclude if this splits tied candidates
            __pragma__('opov')
            if i != 0 and try_exclude[len(hopefuls) - i -
                                      1][1].votes == hopefuls[len(hopefuls) -
                                                              i][1].votes:
                continue
            __pragma__('noopov')

            # Do not exclude if this leaves insufficient candidates
            if remaining_candidates - len(try_exclude) < self.election.seats:
                continue

            # Do not exclude if this could change the order of exclusion
            total_votes = sum((cc.votes for c, cc in try_exclude), Num(0))
            __pragma__('opov')
            if i != 0 and total_votes + total_surpluses > hopefuls[
                    len(hopefuls) - i][1].votes:
                continue
            __pragma__('noopov')

            # Can bulk exclude
            return try_exclude

        return []

    def candidates_to_exclude(self):
        """
		Determine the candidate(s) to exclude
		Returns List[Tuple[Candidate, CountCard]]
		"""

        # Continue current exclusion if applicable
        if self._exclusion is not None:
            self.logs.append(
                'Continuing exclusion of ' +
                self.pretty_join([c.name
                                  for c, cc in self._exclusion[0]]) + '.')
            __pragma__('opov')
            return self._exclusion[0]
            __pragma__('noopov')

        hopefuls = [(c, cc) for c, cc in self.candidates.items()
                    if cc.state == CandidateState.HOPEFUL]
        hopefuls.sort(key=lambda x: x[1].votes)

        candidates_excluded = []

        # Bulk exclusion
        if self.options['bulk_exclude']:
            if self.options['exclusion'] == 'parcels_by_order':
                # Ordering of parcels is not defined in this case
                raise STVException(
                    'Cannot use bulk_exclude with parcels_by_order')

            candidates_excluded = self.candidates_to_bulk_exclude(hopefuls)

        if len(candidates_excluded) > 0:
            if len(candidates_excluded) == 1:
                self.logs.append('No surpluses to distribute, so ' +
                                 candidates_excluded[0][0].name +
                                 ' is excluded.')
            else:
                self.logs.append(
                    'No surpluses to distribute, so ' +
                    self.pretty_join([c.name
                                      for c, cc in candidates_excluded]) +
                    ' are excluded.')
        else:
            candidates_excluded = [self.choose_lowest(hopefuls)]
            self.logs.append('No surpluses to distribute, so ' +
                             candidates_excluded[0][0].name + ' is excluded.')

        return candidates_excluded

    def do_exclusion(self, candidates_excluded):
        """
		Exclude the given candidate and transfer the votes
		Subclasses must override this function
		"""
        raise NotImplementedError('Method not implemented')  # pragma: no cover

    def compute_quota(self):
        """
		Recount total votes and (if applicable) recalculate the quota
		"""

        __pragma__('opov')
        self.total = sum((cc.votes for c, cc in self.candidates.items()),
                         Num('0'))
        self.loss_fraction.transfers += (
            self.total_orig - self.total -
            self.exhausted.votes) - self.loss_fraction.votes

        if self.quota is None or self.options['quota_mode'] == 'progressive':
            if self.options['quota'] == 'droop' or self.options[
                    'quota'] == 'droop_exact':
                self.quota = self.total / Num(self.election.seats + 1)
            elif self.options['quota'] == 'hare' or self.options[
                    'quota'] == 'hare_exact':
                self.quota = self.total / Num(self.election.seats)
            else:
                raise STVException('Invalid quota option')  # pragma: no cover

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

            self.logs.append(
                self.total.pp(2) + ' usable votes, so the quota is ' +
                self.quota.pp(2) + '.')
        __pragma__('noopov')

        if self.options[
                'quota_mode'] == 'ers97' and self.num_elected < self.election.seats:
            # Calculate the total active vote
            __pragma__('opov')
            orig_vre = self.vote_required_election
            total_active_vote = \
             sum((cc.votes for c, cc in self.candidates.items() if cc.state == CandidateState.HOPEFUL or cc.state == CandidateState.EXCLUDING), Num('0')) + \
             sum((cc.votes - self.quota for c, cc in self.candidates.items() if (cc.state == CandidateState.PROVISIONALLY_ELECTED or cc.state == CandidateState.DISTRIBUTING_SURPLUS or cc.state == CandidateState.ELECTED) and cc.votes > self.quota), Num('0'))
            self.vote_required_election = total_active_vote / Num(
                self.election.seats - self.num_elected + 1)
            if self.options['round_votes'] is not None:
                self.vote_required_election = self.vote_required_election.round(
                    self.options['round_votes'],
                    self.vote_required_election.ROUND_UP)
            if (orig_vre is None or self.vote_required_election != orig_vre
                ) and self.vote_required_election < self.quota:
                self.logs.append('Total active vote is ' +
                                 total_active_vote.pp(2) +
                                 ', so the vote required for election is ' +
                                 self.vote_required_election.pp(2) + '.')
            __pragma__('noopov')

    def meets_quota(self, count_card):
        """
		Determine if the given candidate meets the quota
		"""

        if self.options['quota_criterion'] == 'geq':
            __pragma__('opov')
            return count_card.votes >= self.quota or (
                self.options['quota_mode'] == 'ers97'
                and count_card.votes >= self.vote_required_election)
            __pragma__('noopov')
        elif self.options['quota_criterion'] == 'gt':
            __pragma__('opov')
            return count_card.votes > self.quota or (
                self.options['quota_mode'] == 'ers97'
                and count_card.votes > self.vote_required_election)
            __pragma__('noopov')
        else:
            raise STVException('Invalid quota criterion')  # pragma: no cover

    def elect_meeting_quota(self):
        """
		Elect all candidates meeting the quota
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

                count_card.state = CandidateState.PROVISIONALLY_ELECTED
                self.num_elected += 1
                count_card.order_elected = self.num_elected

                meets_quota.remove(x)

                if self.options['quota_mode'] == 'ers97':
                    self.compute_quota(
                    )  # Vote required for election may have changed

            if self.options['quota_mode'] == 'ers97':
                self.elect_meeting_quota(
                )  # Repeat as the vote required for election may have changed
                return

    def describe_options(self):
        result = []
        if self.options['quota'] != 'droop':
            result.append('--quota ' + self.options['quota'])
        if self.options['quota_criterion'] != 'geq':
            result.append('--quota-criterion ' +
                          self.options['quota_criterion'])
        if self.options['quota_mode'] != 'static':
            result.append('--quota-mode ' + self.options['quota_mode'])
        if not self.options['bulk_elect']:
            result.append('--no-bulk-elect')
        if self.options['bulk_exclude']:
            result.append('--bulk-exclude')
        if self.options['defer_surpluses']:
            result.append('--defer-surpluses')
        if pyRCV2.numbers._numclass is pyRCV2.numbers.Rational:
            result.append('--numbers rational')
        elif pyRCV2.numbers._numclass is pyRCV2.numbers.Native:
            result.append('--numbers native')
        elif pyRCV2.numbers._numclass is pyRCV2.numbers.FixedGuarded:
            result.append('--numbers gfixed')
            if pyRCV2.numbers.get_dps() != 5:
                result.append('--decimals ' + str(pyRCV2.numbers.get_dps()))
        else:
            # Fixed
            if pyRCV2.numbers.get_dps() != 5:
                result.append('--decimals ' + str(pyRCV2.numbers.get_dps()))
        if self.options['round_quota'] is not None:
            result.append('--round-quota ' + str(self.options['round_quota']))
        if self.options['round_votes'] is not None:
            result.append('--round-votes ' + str(self.options['round_votes']))
        if self.options['round_tvs'] is not None:
            result.append('--round-tvs ' + str(self.options['round_tvs']))
        if self.options['round_weights'] is not None:
            result.append('--round-weights ' +
                          str(self.options['round_weights']))
        if self.options['surplus_order'] != 'size':
            result.append('--surplus-order ' + self.options['surplus_order'])
        if self.options['papers'] == 'transferable':
            result.append('--transferable-only')
        if self.options['exclusion'] != 'one_round':
            result.append('--exclusion ' + self.options['exclusion'])
        if len(self.options['ties']) == 1 and isinstance(
                self.options['ties'][0], pyRCV2.ties.TiesPrompt):
            pass
        else:
            for t in self.options['ties']:
                if isinstance(t, pyRCV2.ties.TiesBackwards):
                    result.append('--ties backwards')
                elif isinstance(t, pyRCV2.ties.TiesForwards):
                    result.append('--ties forwards')
                elif isinstance(t, pyRCV2.ties.TiesRandom):
                    result.append('--ties random')
                    result.append('--random-seed ' + t.random.seed)
                elif isinstance(t, pyRCV2.ties.TiesPrompt):
                    result.append('--ties prompt')
        return ' '.join(result)

    # -----------------
    # UTILITY FUNCTIONS
    # -----------------

    def next_preferences(self, parcels):
        """
		Examine the specified ballots and group ballot papers by next available preference
		"""
        # SafeDict: Candidate -> [List[BallotInCount], ballots, votes]
        next_preferences = SafeDict([(c, [[], Num('0'), Num('0')])
                                     for c, cc in self.candidates.items()])
        total_ballots = Num('0')
        total_votes = Num('0')

        next_exhausted = []
        exhausted_ballots = Num('0')
        exhausted_votes = Num('0')

        for parcel in parcels:
            for bc in parcel:
                __pragma__('opov')
                total_ballots += bc.ballot.value
                total_votes += bc.ballot_value

                for i in range(bc.last_preference + 1,
                               len(bc.ballot.preferences)):
                    candidate = bc.ballot.preferences[i]
                    count_card = self.candidates[candidate]

                    if count_card.state == CandidateState.HOPEFUL:
                        #next_preferences[candidate][0].append(BallotInCount(bc.ballot, bc.ballot_value, i))
                        bc.last_preference = i
                        next_preferences[candidate][0].append(bc)
                        next_preferences[candidate][1] += bc.ballot.value
                        next_preferences[candidate][2] += bc.ballot_value
                        break
                else:
                    # No next available preference
                    next_exhausted.append(bc)
                    exhausted_ballots += bc.ballot.value
                    exhausted_votes += bc.ballot_value
                __pragma__('noopov')

        return next_preferences, total_ballots, total_votes, next_exhausted, exhausted_ballots, exhausted_votes

    def choose_lowest(self, l):
        """
		Provided a list of tuples (Candidate, CountCard), sorted in ASCENDING order of votes, choose the tuple with the fewest votes, breaking ties appropriately
		"""

        if len(l) == 1:
            return l[0]

        __pragma__('opov')
        # Do not use (c, cc) for c, cc in ... as this will break equality in JS
        tied = [x for x in l if x[1].votes == l[0][1].votes]
        __pragma__('noopov')

        if len(tied) == 1:
            return tied[0]

        # A tie exists
        for tie in self.options['ties']:
            result = tie.choose_lowest(tied)
            if result is not None:
                self.logs.append('A tie for last place was resolved ' +
                                 tie.adverb + ' against ' + result[0].name +
                                 '.')
                return result

        raise STVException('Unable to resolve tie')

    def choose_highest(self, l):
        """
		Provided a list of tuples (Candidate, CountCard), sorted in DESCENDING order of votes, choose the tuple with the most votes, breaking ties appropriately
		"""

        if len(l) == 1:
            return l[0]

        __pragma__('opov')
        # Do not use (c, cc) for c, cc in ... as this will break equality in JS
        tied = [x for x in l if x[1].votes == l[0][1].votes]
        __pragma__('noopov')

        if len(tied) == 1:
            return tied[0]

        # A tie exists
        for tie in self.options['ties']:
            result = tie.choose_highest(tied)
            if result is not None:
                self.logs.append('A tie for first place was resolved ' +
                                 tie.adverb + ' in favour of ' +
                                 result[0].name + '.')
                return result

        raise STVException('Unable to resolve tie')

    def round_votes(self, num):
        if self.options['round_votes'] is None:
            return num
        return num.round(self.options['round_votes'], num.ROUND_DOWN)

    def round_weight(self, num):
        if self.options['round_weights'] is None:
            return num
        return num.round(self.options['round_weights'], num.ROUND_DOWN)

    def round_tv(self, num):
        if self.options['round_tvs'] is None:
            return num
        return num.round(self.options['round_tvs'], num.ROUND_DOWN)

    def make_result(self, comment):
        __pragma__('opov')
        result = CountStepResult(
            comment,
            self.logs,
            self.candidates,
            self.exhausted,
            self.loss_fraction,
            self.total + self.exhausted.votes + self.loss_fraction.votes,
            self.quota,
            self.vote_required_election,
        )
        __pragma__('noopov')
        self.logs = []
        self.step_results.append(result)
        return result

    def pretty_join(self, strs):
        if len(strs) == 0:
            return ''
        if len(strs) == 1:
            return strs[0]
        if len(strs) == 2:
            return strs[0] + ' and ' + strs[1]
        return ', '.join(strs[0:-1]) + ' and ' + strs[len(strs) - 1]
