from dtcvote.database import db_insert, commit_or_rollback
from dtcvote.models.orm import ElectionVoter, Election

import connexion
from typing import Iterable, Tuple, Union, List

from sqlalchemy import Column, Integer, Unicode, Boolean, TIMESTAMP, Identity, ForeignKey, UniqueConstraint, \
    select, update, inspect, delete as sql_delete
from sqlalchemy.exc import IntegrityError
from dtcvote.database import db_exec, db_insert, db_del, db_get_by_id, commit_or_rollback


def search(id_):  # noqa: E501
    """election_id_voters_get

    List all voters for the election ID.

    :param ID: ID of pet to fetch
    :type ID: int
    """
    e = db_get_by_id(Election, id_)
    if not e:
        return f"Election ID Not Found", 404
    else:
        return e.voters_for_election(only_new=False), 200


def delete(id_, dry_run=False):  # noqa: E501
    """election_id_voters_delete

    clears all voters from an election based on the ID supplied # noqa: E501

    :param ID: ID of pet to fetch
    :type ID: int
    :param dry_run: Validate but don&#39;t actually do it
    :type dry_run: bool

    :rtype: None
    """
    e = db_get_by_id(Election, id_)
    if not e:
        return f"Election ID Not Found", 404
    elif e.opened:
        return "This election has been opened. It is too late to remove voters.", 418
    else:
        stmt = sql_delete(ElectionVoter).where(ElectionVoter.election_id==id_)
        db_exec(stmt)
        commit_or_rollback(dry_run)
        return None


def post(id_, dry_run=False):  # noqa: E501
    """election_id_voters_post

    Add voters to an election. # noqa: E501

    :param ID: ID of pet to fetch
    :type ID: int
    :param dry_run: Validate but don&#39;t actually do it
    :type dry_run: bool
    """
    request = connexion.request.get_json()
    try:
        ev = [ElectionVoter(election_id=id_, voter_id=v) for v in request]
        ev = db_insert(ev)
        commit_or_rollback(dry_run)
        return 'OK', 201
    except IntegrityError:
        return {'code': 404, 'message': 'You specified a voter that does not exist'}, 404
