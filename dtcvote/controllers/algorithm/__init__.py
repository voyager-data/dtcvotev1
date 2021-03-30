from dtcvote.models.orm import Algorithm
from dtcvote.controllers import _search, _post, _get, _delete

search = _search(Algorithm)
get = _get(Algorithm)
