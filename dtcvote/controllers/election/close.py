from dtcvote.database import db_get_by_id, commit_or_rollback
from dtcvote.models.orm import Election
from datetime import datetime
from dateutil.tz import gettz

def search(id_: int, dry_run: bool=False):
    """election_id_close_get

    Closes an election based on a single ID # noqa: E5 None1

    :param ID: Election ID
    :param dry_run: Validate but don&#39;t actually do it

    :rtype: str
    """
    e = db_get_by_id(Election, id_)
    e.closed = datetime.now(tz=gettz('America/New York'))
    commit_or_rollback(dry_run)
    return "Election closed. Ballots will no longer be accepted."
