import random
import subprocess
from datetime import datetime
from typing import Text

#from dtcvote.ballot import PlaintextBallot
from dill import dump, dumps, load, loads
from dtcvote.controllers.election import generate_manifest
from dtcvote.crypto.electionguard import (ElectionGuardBallot,
                                          ElectionGuardElection)
from dtcvote.database import (commit_or_rollback, db_exec, db_flush,
                              db_get_by_id, db_insert)
from dtcvote.models.orm import Ballot, Election
from electionguard.group import rand_q
from flask import current_app
from sqlalchemy import (TIMESTAMP, Column, ForeignKey, Identity, MetaData,
                        UniqueConstraint, create_engine)
from sqlalchemy import delete as sql_delete
from sqlalchemy import inspect, select, text, update

# TODO: Send emails to voters

def random_words(number_of_voters: int):
    number_of_words = number_of_voters * 2
    counter = range(0, number_of_voters)
    words = subprocess.check_output(('shuf', '-n', str(number_of_words), '/usr/share/dict/words'), text=True).splitlines()
    return [f"{words.pop()} {words.pop()}" for i in counter]


def search(id_: int, dry_run: bool = False) -> Text:
    """election_id_generate_ballots_get

    Creates ballot blanks unique to each voter in a given election. # noqa: E501

    :param id_: ID of pet to fetch
    :param dry_run: Validate but don&#39;t actually do it

    """
    e = db_get_by_id(Election, id_)

    if e:
        if e.opened:
            only_new = True
        else:
            e.opened = text("CURRENT_TIMESTAMP")
            only_new = False
            db_flush()
        manifest = e.manifest if e.manifest else generate_manifest(e)
        voters = e.voters_for_election(only_new=only_new)

        if not voters:
            return {'code': 404, 'message': f"No voters to generate ballots for"}, 404

        secret_number = e.secret_number if e.secret_number else rand_q()

        # generate the ballots
        secret_phrases = random_words(len(voters))
        emails = list()
        for v in voters:
            # update the manifest for each voter
            # if e.secret_ballot:
            #     manifest["geopolitical_units"].append(
            #         {
            #             "object_id": str(v.uuid),
            #             "name": v.name,
            #             "type": "polling-place"})
            #     manifest["ballot-styles"][0]["geopolitical_unit_ids"].append(str(v.uuid))

            # Create ballot
            ballot_content = e.dict_from_colset()
            for q in ballot_content.get("questions"):
                # randomize candidate order
                if q.get("randomize_candidates") == True:
                    random.shuffle(q["candidates"])
            b = Ballot(election_id=e.id, secret_phrase=secret_phrases.pop(), ballot_content=dumps(ballot_content))
            b = db_insert([b])[0]

            # send email with link to ballot and secret phrase
            add_message = f"""\n\nTo vote in this election, click this link: {current_app.config.get("GUI_URL") + '/vote/' + str(b.uuid)}

            Before voting, verify that the secret phrase displayed on the screen is "{b.secret_phrase}."

            If the phrase does not match or you have trouble voting, contact your election administrator.
            """
            emails.append(
                dict(email_body=e.vote_email + add_message,
                    email_to = v.email,
                    email_from = current_app.config.get("EMAIL_FROM")
                )
            )



        e_eg = ElectionGuardElection(manifest, e.uuid, secret_number)


        # persist
        e.manifest = manifest
        e.pickle_jar = dumps(e_eg)
        # send emails here
        current_app.logger.warning(emails)

        commit_or_rollback(dry_run)

    else:
        return {'code': 404, 'message': f"Election ID Not Found"}, 404

    return 'Ballots created'
