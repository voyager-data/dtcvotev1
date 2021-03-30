from typing import List

from sqlalchemy import select

from dtcvote.database import db_exec
from dtcvote.models.orm import ElectionVoter, Election


def search(ID):  # noqa: E501
    """voter_id_elections_get

    Returns all elections for voter ID # noqa: E501

    :param ID: ID of pet to fetch
    :type ID: int

    :rtype: List[ElectionResponse]
    """
    stmt = select(Election).join(ElectionVoter).where(ElectionVoter.voter_id == ID)
    elections = db_exec(stmt).scalars()
    if not elections:
        return f"No elections found for this voter.", 404
    else:
        return [e.public_rec_dict for e in elections]

