import connexion
from dtcvote.models.orm import Election, BasicMixin
from typing import Tuple, Dict, TypeVar
from dtcvote.controllers import _search, _post, _get, _delete

search = _search(Election)
post = _post(Election)
get = _get(Election)
delete = _delete(Election)


def put(ID: int, dry_run: bool = False) -> Tuple[Dict, int]:
    """election_id_put

    Replace an election record. Returns an error if voting has been opened or closed. # noqa: E501

    :param ID: ID of pet to fetch
    :param dry_run: Validate but don&#39;t actually do it

    """
    request = connexion.request.get_json()
    response = Election.put(ID, request, dry_run)
    if response == 404:
        return {
            'code': 404,
            'message': f"{Election.__name__} ID Not Found"
        }, 404
    elif response == 418:
        return {
            'code':
            418,
            'message':
            "This election has been opened. It is too late to change it."
        }, 418
    else:
        return response, 200


def generate_manifest(e: Election) -> Dict:
    manifest = dict(
        spec_version="v0.95",
        start_date=e.opened.isoformat(),
        end_date=e.deadline.isoformat(),
        election_scope_id=e.name,
        type="primary",
        name=dict(text=[dict(value=e.name, language="en")]),
        geopolitical_units=[
            dict(
                object_id="windsor-dtc",
                name="Windsor DTC",
                type="town",
            ),
        ],
        ballot_styles=[
            dict(object_id=f"{e.name}-ballot-style",
                 geopolitical_unit_ids=["windsor-dtc"])
        ],
        contests=list(),
    )
    candidates = list()
    parties = dict()

    for q in e.questions:
        contest = {
            "@type":
            "CandidateContest",
            "object_id":
            q.name,
            "sequence_order":
            q.sequence,
            "vote_variation":
            q.algorithm.name.lower(),
            "electoral_district_id":
            "windsor-dtc",
            "name":
            "Justice of the Supreme Court",
            "number_elected":
            q.number_of_winners,
            "votes_allowed":
            q.number_of_winners
            if q.algorithm.name == "Plurality" else len(q.candidates),
            "ballot_title": {
                "text": [
                    {
                        "value": q.name,
                        "language": "en"
                    },
                ]
            },
            "ballot_subtitle": {
                "text": [
                    {
                        "value": q.algorithm.instructions,
                        "language": "en"
                    },
                ]
            },
            "ballot_selections":
            list()
        }

        for c in q.candidates:
            contest["ballot_selections"].append({
                "object_id": f"{{c.name}}-selection",
                "sequence_order": c.sequence,
                "candidate_id": c.name
            })
            candidate = dict(
                object_id=c.name,
                name={"text": [{
                    "value": c.name,
                    "language": "en"
                }]})

            if c.party:
                candidate["party_id"] = c.party.name
                if c.party.name not in contest["primary_party_ids"]:
                    contest["primary_party_ids"].append(c.party.name)
                if c.party.name not in parties.keys():
                    parties[c.party.name] = (dict(
                        object_id=c.party.name,
                        name=dict(
                            text=[dict(value=c.party.name, language="en")])))
            candidates.append(candidate)

        manifest["contests"].append(contest)

    manifest["candidates"] = candidates
    if len(parties) > 0:
        manifest["parties"] = parties.values()

    return manifest