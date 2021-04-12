from typing import Iterable, List, Tuple, Union

import connexion
from dtcvote.database import (commit_or_rollback, db_exec, db_get_by_id,
                              db_insert)
from dtcvote.models.orm import Election, ElectionVoter
from sqlalchemy import delete as sql_delete
from sqlalchemy.exc import IntegrityError


def search(id_: int):  # noqa: E501
    """election_id_voters_get

    List all voters for the election ID.

    :param id_: ID of pet to fetch
    """
    e = db_get_by_id(Election, id_)
    if not e:
        return {'code': 404, 'message': "Election ID Not Found"}, 404
    else:

        return e.voters_for_election(only_new=False, as_dict=True), 200


def delete(id_: int, dry_run=False):
    """election_id_voters_delete

    clears all voters from an election based on the ID supplied # noqa: E501

    :param id_: ID of pet to fetch
    :param dry_run: Validate but don&#39;t actually do it

    """
    e = db_get_by_id(Election, id_)
    if not e:
        return {'code': 404, 'message': "Election ID Not Found"}, 404
    elif e.opened:
        return {'code': 418, 'message': "This election has been opened. It is too late to remove voters."}, 418
    else:
        stmt = sql_delete(ElectionVoter).where(ElectionVoter.election_id==id_)
        db_exec(stmt)
        commit_or_rollback(dry_run)
        return None


def post(id_: int, dry_run=False):  # noqa: E501
    """election_id_voters_post

    Add voters to an election. # noqa: E501

    :param id_: ID of pet to fetch
    :param dry_run: Validate but don&#39;t actually do it
    """
    request = connexion.request.get_json()
    try:
        ev = [ElectionVoter(election_id=id_, voter_id=v) for v in request]
        ev = db_insert(ev)
        commit_or_rollback(dry_run)
        return 'OK', 201
    except IntegrityError:
        return {'code': 404, 'message': 'You specified a voter that does not exist'}, 404
