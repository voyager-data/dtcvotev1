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
is_py = False
__pragma__('skip')
is_py = True
__pragma__('noskip')

from pyRCV2.method.base_stv import BaseSTVCounter, STVException
from pyRCV2.model import CandidateState
from pyRCV2.numbers import Num


# Stubs for JS
def groupby(iterable, keyfunc):
    if is_py:
        __pragma__('skip')
        import itertools
        return [list(g) for k, g in itertools.groupby(iterable, keyfunc)]
        __pragma__('noskip')
    else:  # pragma: no cover
        groups = []
        group = []
        last_result = None
        for i in iterable:
            this_result = keyfunc(i)
            __pragma__('opov')
            if last_result is not None and this_result != last_result:
                __pragma__('noopov')
                groups.append(group)
                group = []
            last_result = this_result
            group.append(i)
        if group:
            groups.append(group)
        return groups


class BaseGregorySTVCounter(BaseSTVCounter):
    """Abstract Gregory STV counter"""
    def _do_gregory_surplus(self, is_weighted, candidate_surplus, count_card,
                            surplus, parcels):
        next_preferences, total_ballots, total_votes, next_exhausted, exhausted_ballots, exhausted_votes = self.next_preferences(
            parcels)

        if is_weighted:
            total_units = total_votes
        else:
            total_units = total_ballots

        if self.options['papers'] == 'transferable':
            __pragma__('opov')
            if is_weighted:
                transferable_units = total_votes - exhausted_votes
                transferable_votes = transferable_units
            else:
                transferable_units = total_ballots - exhausted_ballots
                transferable_votes = total_votes - exhausted_votes
            __pragma__('noopov')

        __pragma__('opov')
        if self.options['papers'] == 'transferable':
            if transferable_votes > surplus:
                if self.options['round_tvs'] is None:
                    self.logs.append('Surplus of ' + candidate_surplus.name +
                                     ' distributed at value ' +
                                     (surplus / transferable_units).pp(2) +
                                     '.')
                else:
                    tv = self.round_tv(surplus / transferable_units)
                    self.logs.append('Surplus of ' + candidate_surplus.name +
                                     ' distributed at value ' + tv.pp(2) + '.')
            else:
                self.logs.append('Surplus of ' + candidate_surplus.name +
                                 ' distributed at value received.')
        else:
            if self.options['round_tvs'] is None:
                self.logs.append('Surplus of ' + candidate_surplus.name +
                                 ' distributed at value ' +
                                 (surplus / total_units).pp(2) + '.')
            else:
                tv = self.round_tv(surplus / total_units)
                self.logs.append('Surplus of ' + candidate_surplus.name +
                                 ' distributed at value ' + tv.pp(2) + '.')
        __pragma__('noopov')

        for candidate, x in next_preferences.items():
            cand_ballots = x[0]
            num_ballots = x[1]
            num_votes = x[2]

            if is_weighted:
                num_units = num_votes
            else:
                num_units = num_ballots

            new_parcel = []
            if len(cand_ballots) > 0:
                __pragma__('opov')
                self.candidates[candidate].parcels.append(new_parcel)
                __pragma__('noopov')

            __pragma__('opov')
            if self.options['papers'] == 'transferable':
                if transferable_votes > surplus:
                    if self.options['round_tvs'] is None:
                        self.candidates[
                            candidate].transfers += self.round_votes(
                                (num_units * surplus) / transferable_units)
                    else:
                        self.candidates[
                            candidate].transfers += self.round_votes(
                                num_units * tv)
                else:
                    self.candidates[candidate].transfers += self.round_votes(
                        num_votes)  # Do not allow weight to increase
            else:
                if self.options['round_tvs'] is None:
                    self.candidates[candidate].transfers += self.round_votes(
                        (num_units * surplus) / total_units)
                else:
                    self.candidates[candidate].transfers += self.round_votes(
                        num_units * tv)
            __pragma__('noopov')

            for bc in cand_ballots:
                __pragma__('opov')
                if self.options['papers'] == 'transferable':
                    if transferable_votes > surplus:
                        if self.options['round_tvs'] is None:
                            if is_weighted:
                                new_value = (bc.ballot_value *
                                             surplus) / transferable_units
                            else:
                                new_value = (bc.ballot.value *
                                             surplus) / transferable_units
                        else:
                            tv = self.round_tv(surplus / transferable_units)
                            if is_weighted:
                                new_value = bc.ballot_value * tv
                            else:
                                new_value = bc.ballot.value * tv
                    else:
                        new_value = bc.ballot_value
                else:
                    if self.options['round_tvs'] is None:
                        if is_weighted:
                            new_value = (bc.ballot_value *
                                         surplus) / total_units
                        else:
                            new_value = (bc.ballot.value *
                                         surplus) / total_units
                    else:
                        tv = self.round_tv(surplus / total_units)
                        if is_weighted:
                            new_value = bc.ballot_value * tv
                        else:
                            new_value = bc.ballot.value * tv

                bc.ballot_value = self.round_weight(new_value)
                new_parcel.append(bc)
                __pragma__('noopov')

        __pragma__('opov')
        if self.options['papers'] == 'transferable':
            if transferable_votes > surplus:
                pass  # No ballots exhaust
            else:
                self.exhausted.transfers += self.round_votes(
                    (surplus - transferable_votes))
        else:
            if is_weighted:
                self.exhausted.transfers += self.round_votes(
                    (exhausted_votes * surplus) / total_votes)
            else:
                self.exhausted.transfers += self.round_votes(
                    (exhausted_ballots * surplus) / total_ballots)
        __pragma__('noopov')

        __pragma__('opov')
        count_card.transfers -= surplus
        __pragma__('noopov')

        count_card.state = CandidateState.ELECTED

    def do_exclusion(self, candidates_excluded):
        """Implements BaseSTVCounter.do_exclusion"""
        # Optimisation: Pre-sort exclusion ballots if applicable
        # self._exclusion[1] -> list of ballots-per-stage ; ballots-per-stage = List[Tuple[Candidate,List[BallotInCount]]]
        if self._exclusion is None:
            if self.options['exclusion'] == 'one_round':
                self._exclusion = (candidates_excluded,
                                   [[(c, [bc for p in cc.parcels for bc in p])
                                     for c, cc in candidates_excluded]])
            elif self.options['exclusion'] == 'parcels_by_order':
                c, cc = candidates_excluded[0]
                self._exclusion = (candidates_excluded, [[(c, p)]
                                                         for p in cc.parcels])
            elif self.options['exclusion'] == 'by_value':
                # Precompute ballot transfer values
                if self.options['round_tvs']:
                    __pragma__('opov')
                    ballots = [
                        (c, bc,
                         self.round_tv(bc.ballot_value / bc.ballot.value))
                        for c, cc in candidates_excluded for p in cc.parcels
                        for bc in p
                    ]
                    __pragma__('noopov')
                else:
                    # Round to 8 decimal places to consider equality
                    # FIXME: Work out a better way of doing this
                    __pragma__('opov')
                    ballots = [(c, bc,
                                (bc.ballot_value / bc.ballot.value).round(
                                    8, bc.ballot_value.ROUND_DOWN))
                               for c, cc in candidates_excluded
                               for p in cc.parcels for bc in p]
                    __pragma__('noopov')

                # Sort ballots by value
                ballots.sort(key=lambda x: x[2], reverse=True)
                ballots_by_value = groupby(ballots, lambda x: x[2])

                # TODO: Can we combine ballots for each candidate within each stage?
                self._exclusion = (candidates_excluded,
                                   [[(c, [bc]) for c, bc, tv in x]
                                    for x in ballots_by_value])
            else:
                raise STVException(
                    'Invalid exclusion mode')  # pragma: no cover

        this_exclusion = self._exclusion[1][0]
        self._exclusion[1].remove(this_exclusion)

        # Transfer votes

        next_preferences, total_ballots, total_votes, next_exhausted, exhausted_ballots, exhausted_votes = self.next_preferences(
            [bc for c, bc in this_exclusion])

        if self.options['exclusion'] != 'one_round':
            __pragma__('opov')
            self.logs.append('Transferring ' + total_ballots.pp(0) +
                             ' ballot papers, totalling ' + total_votes.pp(2) +
                             ' votes, received at value ' +
                             (this_exclusion[0][1][0].ballot_value /
                              this_exclusion[0][1][0].ballot.value).pp(2) +
                             '.')
            __pragma__('noopov')

        for candidate, x in next_preferences.items():
            cand_ballots, num_ballots, num_votes = x[0], x[1], x[2]

            new_parcel = []
            if len(cand_ballots) > 0:
                __pragma__('opov')
                self.candidates[candidate].parcels.append(new_parcel)
                __pragma__('noopov')

            __pragma__('opov')
            self.candidates[candidate].transfers += self.round_votes(num_votes)
            __pragma__('noopov')

            for bc in cand_ballots:
                __pragma__('opov')
                new_parcel.append(bc)
                __pragma__('noopov')

        # Subtract votes

        __pragma__('opov')
        self.exhausted.transfers += self.round_votes(exhausted_votes)
        __pragma__('noopov')

        for candidate, ballots in this_exclusion:
            total_votes = Num(0)
            for bc in ballots:
                __pragma__('opov')
                total_votes += bc.ballot_value
                __pragma__('noopov')

            __pragma__('opov')
            self.candidates[candidate].transfers -= total_votes
            __pragma__('noopov')

        if len(self._exclusion[1]) == 0:
            if self.options['exclusion'] != 'one_round':
                self.logs.append('Exclusion complete.')

            for candidate_excluded, count_card in candidates_excluded:
                __pragma__('opov')
                count_card.transfers -= count_card.votes
                __pragma__('noopov')
                count_card.state = CandidateState.EXCLUDED
                self._exclusion = None


class WIGSTVCounter(BaseGregorySTVCounter):
    """
	Basic weighted inclusive Gregory STV counter
	"""
    def describe_options(self):
        # WIG is the default
        return BaseSTVCounter.describe_options(self)

    def do_surplus(self, candidate_surplus, count_card, surplus):
        """Implements BaseSTVCounter.do_surplus"""
        self._do_gregory_surplus(True, candidate_surplus, count_card, surplus,
                                 count_card.parcels)


class UIGSTVCounter(BaseGregorySTVCounter):
    """
	Basic unweighted inclusive Gregory STV counter
	"""
    def describe_options(self):
        """Overrides BaseSTVCounter.describe_options"""
        return '--method uig ' + BaseSTVCounter.describe_options(self)

    def do_surplus(self, candidate_surplus, count_card, surplus):
        """Implements BaseSTVCounter.do_surplus"""
        self._do_gregory_surplus(False, candidate_surplus, count_card, surplus,
                                 count_card.parcels)


class EGSTVCounter(BaseGregorySTVCounter):
    """
	Exclusive Gregory (last bundle) STV implementation
	"""
    def describe_options(self):
        """Overrides BaseSTVCounter.describe_options"""
        return '--method eg ' + BaseSTVCounter.describe_options(self)

    def do_surplus(self, candidate_surplus, count_card, surplus):
        """Implements BaseSTVCounter.do_surplus"""
        last_bundle = count_card.parcels[len(count_card.parcels) - 1]
        self._do_gregory_surplus(False, candidate_surplus, count_card, surplus,
                                 [last_bundle])
