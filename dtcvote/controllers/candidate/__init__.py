from dtcvote.models.orm import Candidate

from dtcvote.controllers import _search, _post, _get, _delete


delete = _delete(Candidate)
