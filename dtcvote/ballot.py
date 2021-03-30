from collections import OrderedDict
from uuid import UUID
from electionguard.elgamal import ElGamalKeyPair, elgamal_keypair_from_secret
from electionguard.ballot import CiphertextBallot, PlaintextBallotSelection, PlaintextBallotContest, PlaintextBallot
from electionguard.encrypt import SelectionDescription
from dtcvote.models.orm import Election







class BasicBallot(OrderedDict):
    def __init__(self, e: Election):
        super().__init__(
            election_id=e.ID,
            election_name=e.name,
            election_deadline=e.deadline,
            election_secret=e.secret_ballot,
            questions = [OrderedDict(
               question_id = q.ID,
               question_name = q.name,
               algorithm_name = q.algorithm.name,
               algorithm_instructions = q.algorithm.instructions,
               question_number_of_winners = q.number_of_winners,
               candidates = [OrderedDict(
                   candidate_sequence = c.sequence,
                   candidate_name = c.name,
                   candidate_party = c.party.name,
                   voter_ranking = 0
                   ) for c in q.candidates]
                ) for q in e.questions]
            )


    def encrypt(self):
        ballot_pt = PlaintextBallot(None,
                                    self.get("election_name"),
                                    [   PlaintextBallotContest(q.get("question_name"),
                                        [   PlaintextBallotSelection(c.get("candidate_name"), c.get("voter_ranking"))
                                            for c in q.candidates ]
                                        )
                                        for q in self.get("questions") ]
                                    )
