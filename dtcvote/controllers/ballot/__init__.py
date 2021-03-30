from dtcvote.models.orm import Ballot
import connexion
from dtcvote.models.orm import Election, BasicMixin, Ballot



def get(ID, uuid):  # noqa: E501
    """ballot_id_uuid_get

    Returns a ballot based on a ballot ID and voter UUID # noqa: E501

    :param ID: ID of pet to fetch
    :type ID: int
    :param uuid: UUID of pet to fetch
    :type uuid:

    :rtype: BallotResponse
    """

    return 'do some magic!'


def put(ID, uuid, ballot_put_request, dry_run=None):  # noqa: E501
    """ballot_id_uuid_put

    Cast a ballot. # noqa: E501

    :param ID: ID of pet to fetch
    :type ID: int
    :param uuid: UUID of pet to fetch
    :type uuid:
    :param ballot_put_request: Completed ballot
    :type ballot_put_request: dict | bytes
    :param dry_run: Validate but don&#39;t actually do it
    :type dry_run: bool

    :rtype: BallotResponse
    """
    if connexion.request.is_json:
        ballot_put_request = connexion.request.get_json()
    return 'do some magic!'

