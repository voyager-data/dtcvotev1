import connexion
from dtcvote.models.orm import Ballot
from typing import Text
from uuid import UUID


def get(uuid: Text):  # noqa: E501
    """ballot_uuid_voter_uuid_get

    Returns a ballot based on UUID

    :param uuid: UUID of ballot
    """
    b = Ballot.get(UUID(uuid))
    if b == 404:
        return {'code': 404, 'message': "No ballot here by that ID."}, 404
    else:
        return b, 200


def put(uuid: Text, dry_run: bool=None):
    """ballot_id_uuid_put

    Cast a ballot. # noqa: E501

    :param uuid: UUID of ballot
    :param dry_run: Validate but don&#39;t actually do it

    """
    ballot_put_request = connexion.request.get_json()
    b = Ballot.put(UUID(uuid), votes=ballot_put_request, dry_run=dry_run)
    if b == 418:
        return {'code': 418, 'message': "Cannot cast ballot. It may not exist or the election may be closed."}, 418
    else:
        return b, 200
