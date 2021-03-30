import os
from typing import Dict, List, Text
from uuid import UUID

from gmpy2 import mpz, mpz_rrandomb, random_state

from electionguard.ballot import (BallotBoxState, CiphertextBallot,
                                  PlaintextBallot, SubmittedBallot)
from electionguard.ballot_box import accept_ballot
from electionguard.data_store import DataStore
from electionguard.election import CiphertextElectionContext
from electionguard.election_builder import ElectionBuilder
from electionguard.elgamal import ElGamalKeyPair, elgamal_keypair_from_secret
from electionguard.encrypt import EncryptionDevice, EncryptionMediator
from electionguard.group import ElementModQ, Q
from electionguard.manifest import InternalManifest, Manifest
from electionguard.tally import CiphertextTally, tally_ballots


def generate_secret_number() -> ElementModQ:
    i = mpz(0)
    while i == 0:
        i = mpz_rrandomb(random_state(), 256)
        if i < Q:
            return ElementModQ(elem=i)


class ElectionGuardElection:
    internal_manifest: InternalManifest
    context: CiphertextElectionContext
    keypair: ElGamalKeyPair
    builder: ElectionBuilder
    tally: CiphertextTally
    device: EncryptionDevice
    encrypter: EncryptionMediator
    store: DataStore

    def __init__(self, manifest: Dict, uuid: UUID, secret_number: ElementModQ):
        # Open an election manifest file
        election_description = Manifest(**manifest)

        # Create an election builder instance, and configure it for a single public-private keypair.
        # in a real election, you would configure this for a group of guardians.  See Key Ceremony for more information.
        builder = ElectionBuilder(
            number_of_guardians=1,  # since we will generate a single public-private keypair, we set this to 1
            quorum=1,  # since we will generate a single public-private keypair, we set this to 1
            manifest=election_description,
        )

        # Generate an ElGamal Keypair from a secret.  In a real election you would use the Key Ceremony instead.

        self.keypair = elgamal_keypair_from_secret(secret_number)

        builder.set_public_key(self.keypair.public_key)

        # get an `InternalElectionDescription` and `CiphertextElectionContext`
        # that are used for the remainder of the election.
        self.internal_manifest, self.context = builder.build()
        self.device = EncryptionDevice(
            uuid.getnode(), "Session", secret_number, "polling-place-one"
        )
        self.encrypter = EncryptionMediator(
            self.internal_manifest, self.context, self.device
        )
        self.store = DataStore()

    def count_encrypted_ballots(self, secret_key: ElementModQ) -> Dict[str, int]:
        tally = tally_ballots(self.store, self.internal_manifest, self.context)
        assert tally is not None
        plaintext_selections: Dict[str, int] = {}
        for _, contest in tally.contests.items():
            for object_id, selection in contest.selections.items():
                plaintext_tally = selection.ciphertext.decrypt(secret_key)
                plaintext_selections[object_id] = plaintext_tally
        return plaintext_selections


class ElectionGuardBallot(PlaintextBallot):
    election: ElectionGuardElection
    ballot: PlaintextBallot
    encrypted_ballot: CiphertextBallot
    submitted_ballot: SubmittedBallot

    def __init__(
        self,
        object_id: Text,
        style_id: Text,
        ballot_request: Dict,
        election: ElectionGuardElection,
    ):
        super().__init__()
        self.ballot = ballot_request  # convert here
        self.election = election
        self.encrypted_ballot = self.election.encrypter.encrypt(self.ballot)

    def submit(self):
        self.submitted_ballot = accept_ballot(
            self.encrypted_ballot,
            BallotBoxState.CAST,
            self.election.internal_manifest,
            self.election.context,
            self.election.store,
        )
        return self.submitted_ballot
