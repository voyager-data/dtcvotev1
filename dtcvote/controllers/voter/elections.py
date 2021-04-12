from typing import List, Dict
from sqlalchemy import select
from dtcvote.database import db_exec
from dtcvote.models.orm import ElectionVoter, Election


def search(id_: int) -> List[Dict]:
    """voter_id_elections_get

    Returns all elections for voter ID

    :param id_: ID of pet to fetch
    """
    stmt = select(Election).join(ElectionVoter).where(ElectionVoter.voter_id == id_)
    elections = db_exec(stmt).scalars()
    if not elections:
        return f"No elections found for this voter.", 404
    else:
        return [e.public_rec_dict for e in elections]
