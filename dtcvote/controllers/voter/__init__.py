from dtcvote.models.orm import Voter
from dtcvote.controllers import _search, _post, _get, _delete


search = _search(Voter)
post = _post(Voter)
get = _get(Voter)
delete = _delete(Voter)
