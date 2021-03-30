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

from pyRCV2.numbers import Num


class Candidate:
    def __init__(self, name):
        self.name = name

    def __repr__(self):
        return '<Candidate ' + self.name + '>'

    def toString(self):  # pragma: no cover
        return repr(self)


class CandidateState:
    HOPEFUL = 0
    PROVISIONALLY_ELECTED = 10
    DISTRIBUTING_SURPLUS = 20
    ELECTED = 30
    EXCLUDING = 40
    EXCLUDED = 50
    WITHDRAWN = 60


class Ballot:
    """
	Represents a voter's (or if weighted, multiple voters') preferences
	"""
    def __init__(self, value, preferences):
        self.value = value
        self.preferences = preferences

    def clone(self):
        return Ballot(self.value, self.preferences)


class BallotInCount:
    """
	Represents a Ballot held by a candidate at a particular value during the count
	"""

    __slots__ = ['ballot', 'ballot_value', 'last_preference']

    def __init__(self, ballot, ballot_value, last_preference):
        self.ballot = ballot
        self.ballot_value = ballot_value

        # Optimisation: Record the most-recently used preference so earlier preferences do not need to be later examined
        self.last_preference = last_preference


class Election:
    """
	Represents a BLT election
	"""
    def __init__(self,
                 name='',
                 seats=0,
                 candidates=None,
                 ballots=None,
                 withdrawn=None):
        self.name = name
        self.seats = seats
        self.candidates = candidates if candidates is not None else []
        self.ballots = ballots if ballots is not None else []
        self.withdrawn = withdrawn if withdrawn is not None else []


class CountCard:
    """
	Represents a Candidate's (or exhausted pile) current progress in the count
	"""
    def __init__(self):
        self.orig_votes = Num('0')
        self.transfers = Num('0')
        self.state = CandidateState.HOPEFUL
        self.order_elected = None  # Negative for order of exclusion

        # self.parcels = List[Parcel]
        # Parcel = List[Tuple[Ballot, Num]]
        # The exhausted/loss to fraction piles will have only one parcel
        self.parcels = []
        self._parcels_sorted = False  # Optimisation to avoid re-sorting in exclusion by_value

    @property
    def votes(self):
        __pragma__('opov')
        return self.orig_votes + self.transfers
        __pragma__('noopov')

    def step(self):
        """Roll over previous round transfers in preparation for next round"""
        self.orig_votes = self.votes
        self.transfers = Num('0')

    def clone(self):
        """Return a clone of this count card (including cloning ballots) as a record of this stage"""
        result = CountCard()
        result.orig_votes = self.orig_votes
        result.transfers = self.transfers
        result.parcels = [[(b[0].clone(), b[1]) for b in p]
                          for p in self.parcels]
        result.state = self.state
        result.order_elected = self.order_elected
        return result

    def continue_from(self, previous):
        """Adjust this count card's transfers, etc. so its total votes continue on from the previous values"""
        votes = self.votes
        self.orig_votes = previous.votes
        __pragma__('opov')
        self.transfers = votes - self.orig_votes
        __pragma__('noopov')


class CountStepResult:
    def __init__(self, comment, logs, candidates, exhausted, loss_fraction,
                 total, quota, vote_required_election):
        self.comment = comment
        self.logs = logs

        self.candidates = candidates  # SafeDict: Candidate -> CountCard
        self.exhausted = exhausted  # CountCard
        self.loss_fraction = loss_fraction  # CountCard

        self.total = total
        self.quota = quota
        self.vote_required_election = vote_required_election

    def clone(self):
        """Return a clone of this result as a record of this stage"""

        candidates = SafeDict()
        for c, cc in self.candidates.items():
            __pragma__('opov')
            candidates[c] = cc.clone()
            __pragma__('noopov')

        return CountStepResult(self.comment, candidates,
                               self.exhausted.clone(),
                               self.loss_fraction.clone(), self.total,
                               self.quota)


class CountCompleted(CountStepResult):
    pass
