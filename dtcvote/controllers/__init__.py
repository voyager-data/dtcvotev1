import connexion
from typing import TypeVar, Generic, Callable

T = TypeVar('T')


def _search(cls: Generic[T]) -> Callable:
    """get

    Returns all records from the system that the user has access to
    """
    return lambda: (cls.search(), 200)


def _post(cls: Generic[T]) -> Callable:
    def post(dry_run: bool = False):
        return cls.post(connexion.request.get_json(), dry_run), 201
    return post


def _get(cls: Generic[T]) -> Callable:
    """election_id_get

    Returns an election based on a single id_ # noqa: E501

    :param id_: id_ of pet to fetch
    """
    def get(id_: int):
        response = cls.get(id_)
        if response:
            return response, 200
        else:
            return {'code': 404, 'message': f"{cls.__name__} ID Not Found"}, 404

    return get


def _delete(cls: Generic[T]) -> Callable:  # noqa: E501
    """election_id_delete

    deletes a single election based on the id_ supplied # noqa: E501

    :param id_: id_ of pet to fetch
    :param dry_run: Validate but don&#39;t actually do it
    :type dry_run: bool

    :rtype: None
    """
    def delete(id_: int, dry_run: bool=False):
        response = cls.delete(id_, dry_run)
        if response == 404:
            return {'code': 404, 'message': f"{cls.__name__} ID Not Found"}, 404
        else:
            return None

    return delete
