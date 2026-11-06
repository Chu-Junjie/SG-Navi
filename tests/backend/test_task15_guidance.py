"""Development cases for integration behavior; frozen 40-case evaluation is separate."""
import json
import shutil
from copy import deepcopy

import pytest

from backend.app import create_app
from rag.import_knowledge_base import DEFAULT_KB
from rag.repository import EvidenceRepository, RepositoryError
from shared.validate_guidance import validate_guidance


@pytest.fixture
def pair(tmp_path):
    directory = tmp_path / "kb"
    shutil.copytree(DEFAULT_KB, directory)
    repo = EvidenceRepository(directory, state_file=tmp_path / "state/quarantine.json")
    app = create_app()
    app.config["SG_NAVI_REPOSITORY_FACTORY"] = lambda: repo
    return app.test_client(), repo, app


def request(client, facts, case="rental_deposit", query="landlord rental deposit"):
    confirmation = client.post("/api/intake/confirm", json={"intake_version": "1.0", "confirmed": True,
        "case_type": case, "confirmed_answers": facts})
    assert confirmation.status_code == 200
    return {"guidance_version": "1.0", "confirmed": True, "case_type": case,
            "confirmed_answers": facts, "confirmation_revision": confirmation.get_json()["revision"], "query": query}


def call(client, facts, case="rental_deposit", query="landlord rental deposit"):
    response = client.post("/api/guidance", json=request(client, facts, case, query))
    data = response.get_json()
    validate_guidance(data)
    return response, data


def test_clarification_uses_only_missing_facts_and_unknown_is_not_repeated(pair):
    client, _, _ = pair
    _, data = call(client, {"dispute_with": "landlord"})
    assert data["guidance_status"] == "CLARIFICATION_REQUIRED"
    assert {q["id"] for q in data["questions"]} == {"premises_type", "claim_amount_sgd"}
    _, data = call(client, {"dispute_with": "landlord", "premises_type": "residential", "claim_amount_sgd": "unknown"})
    assert data["guidance_status"] == "GUIDANCE_ONLY"
    assert data["questions"] == [] and "claim_amount_sgd" in data["unresolved_fields"]


def test_landlord_guidance_keeps_complete_citations_beyond_query_top_k(pair):
    client, _, _ = pair
    _, data = call(client, {"dispute_with": "landlord", "premises_type": "residential", "claim_amount_sgd": 900})
    assert data["guidance_status"] == "GUIDANCE_ONLY" and len(data["display_evidence"]) == 9
    assert len(data["matched_evidence_ids"]) <= 8
    assert {e["evidence_id"] for e in data["display_evidence"]} == set(data["research_guidance"]["citations"])
    assert all(e["display_context"] and e["preview"] is None for e in data["display_evidence"])
    assert data["action_card"] is None and data["rule_version"] == "mock-1"


def test_consumer_route_and_edit_invalidate_result_identity(pair):
    client, _, _ = pair
    facts = {"purchase_type": "goods", "purchase_purpose": "personal", "supplier_registered_in_sg": True, "claim_amount_sgd": 70}
    _, first = call(client, facts, "consumer_complaint", "faulty goods refund")
    _, second = call(client, dict(facts, claim_amount_sgd=75), "consumer_complaint", "faulty goods refund")
    assert first["guidance_status"] == second["guidance_status"] == "GUIDANCE_ONLY"
    assert first["result_id"] != second["result_id"]
    assert first["confirmation_revision"] != second["confirmation_revision"]


def test_stale_confirmation_cannot_generate_a_result(pair):
    client, _, _ = pair
    body = request(client, {"dispute_with": "landlord", "claim_amount_sgd": 90})
    body["confirmed_answers"]["claim_amount_sgd"] = 99
    response = client.post("/api/guidance", json=body)
    assert response.status_code == 400 and not response.get_json()["display_evidence"]


def test_agent_conduct_has_no_landlord_or_agreement_questions(pair):
    client, _, _ = pair
    _, data = call(client, {"dispute_with": "agent"}, query="unlicensed agent conduct complaint")
    assert data["guidance_status"] == "GUIDANCE_ONLY"
    assert data["questions"] == []
    assert all(e["source_id"] == "cea-complaint" for e in data["display_evidence"])


def test_agency_contract_requires_explicit_agreement_answer(pair):
    client, _, _ = pair
    _, data = call(client, {"dispute_with": "agent"}, query="agency contract mediation")
    assert [q["id"] for q in data["questions"]] == ["agency_agreement_signed"]
    _, data = call(client, {"dispute_with": "agent", "agency_agreement_signed": False}, query="agency contract mediation")
    assert data["guidance_status"] == "LIMITED_REFERRAL" and data["display_evidence"] == []


@pytest.mark.parametrize("case,facts", [
    ("rental_deposit", {"dispute_with": "landlord", "premises_type": "commercial"}),
    ("consumer_complaint", {"purchase_purpose": "business"}),
    ("consumer_complaint", {"supplier_registered_in_sg": False}),
    ("consumer_complaint", {"supplier_location": "overseas"}),
])
def test_project_boundaries_do_not_become_legal_eligibility(pair, case, facts):
    client, _, _ = pair
    _, data = call(client, facts, case, None)
    assert data["guidance_status"] == "LIMITED_REFERRAL"
    assert data["research_guidance"] is None and not data["display_evidence"]


def test_quarantined_and_unavailable_sources_never_return_partial_verified_data(pair):
    client, repo, app = pair
    repo.quarantine_source("courts-sct-filing", actor="synthetic", reason="controlled fixture")
    _, data = call(client, {"dispute_with": "landlord", "premises_type": "residential", "claim_amount_sgd": 55})
    assert data["guidance_status"] == "LIMITED_REFERRAL" and not data["display_evidence"]
    class Unavailable:
        def snapshot(self):
            raise RepositoryError("do not echo arbitrary error detail")
    app.config["SG_NAVI_REPOSITORY_FACTORY"] = Unavailable
    response, data = call(client, {"dispute_with": "landlord", "premises_type": "residential", "claim_amount_sgd": 55})
    assert response.status_code == 503 and data["guidance_status"] == "ERROR"
    assert "arbitrary error detail" not in json.dumps(data)


def test_malformed_unconfirmed_or_oversized_requests_are_bounded(pair):
    client, _, _ = pair
    body = request(client, {"dispute_with": "landlord"})
    for change in ({"confirmed": False}, {"guidance_version": "2.0"}, {"query": "<script>"},
                   {"query": "x" * 301}, {"confirmed_answers": {"claim_amount_sgd": float("nan")}}, {"extra": True}):
        invalid = deepcopy(body); invalid.update(change)
        response = client.post("/api/guidance", json=invalid)
        assert response.status_code == 400
        validate_guidance(response.get_json())
    assert client.post("/api/guidance", data="not-json").status_code == 415
    assert client.post("/api/guidance", data="x" * 9000, content_type="application/json").status_code == 413


def test_new_endpoint_cors_and_old_v1_are_preserved(pair):
    client, _, _ = pair
    response = client.options("/api/guidance", headers={"Origin":"https://chu-junjie.github.io", "Access-Control-Request-Method":"POST", "Access-Control-Request-Headers":"content-type"})
    assert response.status_code == 204 and response.headers["Access-Control-Allow-Origin"] == "https://chu-junjie.github.io"
    assert "Access-Control-Allow-Credentials" not in response.headers
    assert client.options("/api/guidance", headers={"Origin":"https://attacker.invalid", "Access-Control-Request-Method":"POST"}).status_code == 403
    old = client.post("/api/navigate", json={"api_version":"1.0", "case_type":"rental_deposit", "answers":{"dispute_with":"landlord","premises_type":"residential","claim_amount_sgd":100}}).get_json()
    assert old["action_card"] is None
    assert all(set(row)=={"evidence_id","source_id","rule_ids","url","review_status","source_version"} for row in old["evidence"])
