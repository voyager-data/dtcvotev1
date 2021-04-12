from typing import Dict, Tuple
import connexion
from dtcvote.controllers import _delete, _get, _post, _search
from dtcvote.models.orm import BasicMixin, Election
from electionguard.manifest import ElectionType

search = _search(Election)
post = _post(Election)
get = _get(Election)
delete = _delete(Election)


def put(id_: int, dry_run: bool = False) -> Tuple[Dict, int]:
    """election_id_put

    Replace an election record. Returns an error if voting has been opened or closed. # noqa: E501

    :param id_: id_ of pet to fetch
    :param dry_run: Validate but don&#39;t actually do it

    """
    request = connexion.request.get_json()
    response = Election.put(id_, request, dry_run)
    if response == 404:
        return {"code": 404, "message": f"{Election.__name__} id_ Not Found"}, 404
    elif response == 418:
        return {
            "code": 418,
            "message": "This election has been opened. It is too late to change it.",
        }, 418
    else:
        return response, 200


def generate_manifest(e: Election) -> Dict:
    manifest = dict(
        spec_version="v0.95",
        election_scope_id=e.name,
        type="primary",
        name=dict(text=[dict(value=e.name, language="en")]),
        geopolitical_units=[
            dict(
                object_id="windsor-dtc",
                name="Windsor DTC",
                type="township",
            ),
        ],
        ballot_styles=[
            dict(
                object_id=f"{e.name}-ballot-style",
                geopolitical_unit_ids=["windsor-dtc"],
            )
        ],
        contests=list(),
    )
    candidates = list()
    parties = dict()
    if e.opened:
        manifest["start_date"] = e.opened.isoformat()
    if e.deadline:
        manifest["end_date"] = e.deadline.isoformat()
    for q in e.questions:
        rcv = False if q.algorithm.name in ("Plurality", "Majority") else True
        contest = {
            "@type": "CandidateContest",
            "object_id": q.id,
            "sequence_order": q.sequence,
            "vote_variation": 'rcv' if rcv else q.algorithm.name.lower(),
            "electoral_district_id": "windsor-dtc",
            "name": q.name,
            "number_elected": q.number_of_winners,
            "votes_allowed": len(q.candidates) if rcv else q.number_of_winners,
            "ballot_title": {
                "text": [
                    {"value": q.name, "language": "en"},
                ]
            },
            "ballot_subtitle": {
                "text": [
                    {"value": q.algorithm.instructions, "language": "en"},
                ]
            },
            "ballot_selections": list(),
        }

        seq = 1
        for c in q.candidates:
            candidate = dict()
            for n in range(1, len(q.candidates)):
                if candidate.get("object_id", str()) != c.name:
                    candidate_id = f"{c.name}-rank-{n}" if rcv else c.name
                    contest["ballot_selections"].append(
                        {
                            "object_id": f"{candidate_id}-selection",
                            "sequence_order": seq,
                            "candidate_id": candidate_id,
                        }
                    )
                    seq = seq + 1
                    candidate = dict(
                        object_id=candidate_id, name={"text": [{"value": c.name, "language": "en"}]}
                    )

                    if c.party:
                        candidate["party_id"] = c.party.name
                        if c.party.name not in contest["primary_party_ids"]:
                            contest["primary_party_ids"].append(c.party.name)
                        if c.party.name not in parties.keys():
                            parties[c.party.name] = dict(
                                object_id=c.party.name,
                                name=dict(text=[dict(value=c.party.name, language="en")]),
                            )
                    candidates.append(candidate)

        manifest["contests"].append(contest)

    manifest["candidates"] = candidates
    manifest["parties"] = parties.values() if len(parties) > 0 else list()

    return manifest
