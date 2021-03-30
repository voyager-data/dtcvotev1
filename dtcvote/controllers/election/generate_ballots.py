from typing import Text

from dtcvote.controllers.election import generate_manifest
from dtcvote.crypto.electionguard import (ElectionGuardBallot,
                                          ElectionGuardElection,
                                          generate_secret_number)
from dtcvote.database import commit_or_rollback, db_get_by_id
from dtcvote.models.orm import Ballot, Election
from sqlalchemy import (TIMESTAMP, Column, ForeignKey, Identity, MetaData,
                        UniqueConstraint, create_engine)
from sqlalchemy import delete
from sqlalchemy import delete as sql_delete
from sqlalchemy import inspect, select, update

#from dtcvote.ballot import PlaintextBallot



def search(ID: int, dry_run: bool = False) -> Text:
    """election_id_generate_ballots_get

    Creates ballot blanks unique to each voter in a given election. # noqa: E501

    :param ID: ID of pet to fetch
    :param dry_run: Validate but don&#39;t actually do it

    """
    e = db_get_by_id(Election, ID)

    if e:
        manifest = e.manifest if e.manifest else generate_manifest(e)
        voters = e.voters_for_election(only_new=e.opened)
        secret_number = e.secret_number if e.secret_number else generate_secret_number()
        if e.secret_ballot:
            for v in voters:
                manifest["geopolitical_units"].append(
                    {
                        "object_id": str(v.uuid),
                        "name": v.name,
                        "type": "polling-place"})
                manifest["ballot-styles"][0]["geopolitical_unit_ids"].append(str(v.uuid))
        
        e_eg = ElectionGuardElection(manifest, e.uuid, secret_number)
        # generate the ballots
        #b = ElectionGuardBallot()




        # send emails


        commit_or_rollback(dry_run)

    else:
        return {'code': 404, 'message': f"Election ID Not Found"}, 404    

    return 'Ballots created'


