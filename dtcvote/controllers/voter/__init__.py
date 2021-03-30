import connexion
from typing import Tuple
from dtcvote.database import db_insert, commit_or_rollback
from dtcvote.models.orm import Voter, Election

from dtcvote.controllers import _search, _post, _get, _delete


search = _search(Voter)
post = _post(Voter)
get = _get(Voter)
delete = _delete(Voter)
