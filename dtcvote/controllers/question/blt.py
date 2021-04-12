from dtcvote.database import db_get_by_id
from dtcvote.models.orm import Question


def search(id_):  # noqa: E501
    """question_id_blt_get

    Tabulates ballots for a question by ID to blt format # noqa: E501

    :param id_: ID of pet to fetch

    :rtype: str
    """
    q = db_get_by_id(Question, id_)
    return q.blt()
