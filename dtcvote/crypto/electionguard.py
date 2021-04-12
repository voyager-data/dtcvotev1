import os
from typing import Dict, List, Text
from uuid import UUID, getnode
from flask import current_app
from gmpy2 import mpz, mpz_rrandomb, random_state
from json import dumps
from electionguard.ballot import (BallotBoxState, CiphertextBallot, PlaintextBallotSelection,
                                  PlaintextBallot, SubmittedBallot, PlaintextBallotContest)
from electionguard.ballot_box import accept_ballot
from electionguard.data_store import DataStore
from electionguard.election import CiphertextElectionContext
from electionguard.election_builder import ElectionBuilder
from electionguard.elgamal import ElGamalKeyPair, elgamal_keypair_from_secret
from electionguard.encrypt import EncryptionDevice, EncryptionMediator
from electionguard.group import ElementModQ
from electionguard.manifest import InternalManifest, Manifest
from electionguard.tally import CiphertextTally, tally_ballots
from electionguard.key_ceremony import CeremonyDetails
from electionguard.key_ceremony_mediator import Guardian, KeyCeremonyMediator


def key_ceremony():
    # Setup Guardians
    guardian = Guardian(f"Admin", 1, 1, 1)

    mediator = KeyCeremonyMediator(CeremonyDetails(number_of_guardians=1, quorum=1))

    # Attendance (Public Key Share)
    mediator.announce(guardian)
    # Orchestation (Private Key Share)
    orchestrated = mediator.orchestrate()
    # Verify (Prove the guardians acted in good faith)
    verified = mediator.verify()
    # Publish the Joint Public Key
    joint_public_key = mediator.publish_joint_key()
    return joint_public_key

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
        # Open an election manifest
        election_description = Manifest.from_json(dumps(manifest))

        # Create an election builder instance, and configure it for a single public-private keypair.
        # in a real election, you would configure this for a group of guardians.  See Key Ceremony for more information.
        builder = ElectionBuilder(
            number_of_guardians=1,  # since we will generate a single public-private keypair, we set this to 1
            quorum=1,  # since we will generate a single public-private keypair, we set this to 1
            manifest=election_description,
        )

        # Generate an ElGamal Keypair from a secret.  In a real election you would use the Key Ceremony instead.

        self.keypair = elgamal_keypair_from_secret(secret_number)

        pub_key, commitment_hash = key_ceremony()
        builder.set_public_key(pub_key)
        builder.set_commitment_hash(commitment_hash)

        # get an `InternalElectionDescription` and `CiphertextElectionContext`
        # that are used for the remainder of the election.

        # current_app.logger.warning(builder.elgamal_public_key)

        self.internal_manifest, self.context = builder.build()
        self.device = EncryptionDevice(
            getnode(), "Session", secret_number, "polling-place-one"
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
    statuses = {}

    def __init__(
        self,
        object_id: Text,
        style_id: Text,
        ballot_request: Dict,
        election: ElectionGuardElection,
    ):
        super().__init__()

        # for k, v in ballot_request.items():
            # PlaintextBallotSelection()
            # this_contest = PlaintextBallotContest(contest_id, [PlaintextBallotSelection(selection_id, vote_1_or_0) for blah in blech])

        # self.encrypted_ballot = election.encrypter.encrypt(self.ballot)



    def submit(self, election):
        self.submitted_ballot = accept_ballot(
            self.encrypted_ballot,
            BallotBoxState.CAST,
            election.internal_manifest,
            election.context,
            election.store,
        )
        return self.submitted_ballot
