"""Task 6 backend owner acceptance: BE-01 through BE-10.

Every named function represents one explicit test group.  Cases use synthetic
facts and the current *real* checked corpus; no eligibility rules are enabled.
"""
from unittest.mock import patch

import pytest

from backend.app import create_app
from backend.rules import load_rule_configurations
from rag.repository import EvidenceRepository
from shared.validate_contracts import validate


RENTAL = {"dispute_with": "landlord", "premises_type": "residential",
          "claim_amount_sgd": 123}
CONSUMER = {"purchase_type": "goods", "purchase_purpose": "personal",
            "supplier_registered_in_sg": True, "claim_amount_sgd": 123}


@pytest.fixture
def client():
    app = create_app()
    app.config.update(TESTING=True)
    return app.test_client()


def post(client, case, answers, **extra):
    return client.post("/api/navigate", json={
        "api_version": "1.0", "case_type": case, "answers": answers, **extra
    })


def checked(res, *, status=None, code=200):
    assert res.status_code == code
    data = res.get_json()
    validate(data, "navigate_response")
    if status:
        assert data["status"] == status
    assert data["api_version"] == "1.0"
    return data


def test_be_01_api_health_case_types_and_version(client):
    health = client.get("/api/health")
    assert health.status_code == 200
    validate(health.get_json(), "health_response")
    case_types = client.get("/api/case-types")
    validate(case_types.get_json(), "case_types_response")
    assert set(case_types.get_json()["case_types"]) == {"rental_deposit", "consumer_complaint"}
    version = client.get("/api/version")
    validate(version.get_json(), "version_response")
    assert version.status_code == 200
    assert version.get_json()["source_version"] == EvidenceRepository().snapshot()[0]["source_version"]
    assert version.get_json()["rule_version"] == "mock-1"


def test_be_02_both_real_rag_routes_obey_contract_and_do_not_assert_eligibility(client):
    for case, answers in (("rental_deposit", RENTAL), ("consumer_complaint", CONSUMER)):
        data = checked(post(client, case, answers), status="REFER_TO_OFFICIAL")
        assert data["action_card"] is None
        assert data["evidence"], "Real, validated source context must not be silently omitted"
        assert all(item["review_status"] == "verified" and
                   item["source_version"] == data["source_version"] for item in data["evidence"])
        assert not any("example.invalid" in item["url"] for item in data["evidence"])


def test_be_03_contract_and_json_errors_are_rejected(client):
    for payload in (
        {"api_version": "2.0", "case_type": "rental_deposit", "answers": {}},
        {"api_version": "1.0", "case_type": "unknown", "answers": {}},
        {"api_version": "1.0", "case_type": "rental_deposit", "answers": [],},
        {"api_version": "1.0", "case_type": "rental_deposit", "answers": {}, "extra": 1},
    ):
        checked(client.post("/api/navigate", json=payload), status="ERROR", code=400)
    checked(client.post("/api/navigate", data="{", content_type="application/json"),
            status="ERROR", code=400)
    checked(client.post("/api/navigate", data="{}", content_type="text/plain"),
            status="ERROR", code=415)


def test_be_04_missing_null_unknown_are_not_false_or_assumed(client):
    for case, answers, expected in (
        ("rental_deposit", {}, "claim_amount_sgd"),
        ("rental_deposit", {"dispute_with": "unknown", "claim_amount_sgd": None}, "dispute_with"),
        ("consumer_complaint", {"supplier_registered_in_sg": "unknown"}, "supplier_registered_in_sg"),
    ):
        with patch("backend.rag_bridge.retrieve_evidence") as retrieve:
            data = checked(post(client, case, answers), status="NEED_CLARIFICATION")
        assert expected in {q["id"] for q in data["questions"]}
        assert not data["evidence"] and data["action_card"] is None
        retrieve.assert_not_called()


def test_be_05_outside_pilot_scope_defers_without_source_or_guess(client):
    inputs = (
        ("rental_deposit", dict(RENTAL, premises_type="commercial")),
        ("rental_deposit", dict(RENTAL, premises_type="industrial")),
        ("consumer_complaint", dict(CONSUMER, purchase_purpose="business")),
        ("consumer_complaint", dict(CONSUMER, supplier_registered_in_sg=False)),
    )
    for case, answers in inputs:
        with patch("backend.rag_bridge.retrieve_evidence") as retrieve:
            data = checked(post(client, case, answers), status="REFER_TO_OFFICIAL")
        assert data["warnings"] and not data["evidence"] and data["action_card"] is None
        retrieve.assert_not_called()


def test_be_06_amount_type_range_and_extra_fields_are_validated(client):
    for value in (-1, "one hundred", [], {}):
        checked(post(client, "rental_deposit", dict(RENTAL, claim_amount_sgd=value)),
                status="ERROR", code=400)
    checked(post(client, "consumer_complaint", dict(CONSUMER, claim_amount_sgd=-0.01)),
            status="ERROR", code=400)
    checked(post(client, "rental_deposit", dict(RENTAL, unexpected_field="test")),
            status="ERROR", code=400)


def test_be_07_version_consistency_and_unavailable_bundle_fail_closed(client):
    version = client.get("/api/version").get_json()
    for case, facts in (("rental_deposit", RENTAL), ("consumer_complaint", CONSUMER),
                        ("rental_deposit", {})):
        assert checked(post(client, case, facts))["source_version"] == version["source_version"]
    with patch("backend.versioning.EvidenceRepository.snapshot",
               side_effect=OSError("synthetic unreadable state")):
        data = checked(post(client, "rental_deposit", RENTAL), status="ERROR", code=503)
        assert data["source_version"] == "unavailable"
        assert data["evidence"] == [] and data["action_card"] is None
        v = client.get("/api/version")
        assert v.status_code == 503 and v.get_json()["source_version"] == "unavailable"


def test_be_08_missing_and_failed_retrieval_fail_safely(client):
    for rag_status, expected in (("NO_RESULTS", "REFER_TO_OFFICIAL"), ("ERROR", "ERROR")):
        with patch("backend.rag_bridge.retrieve_evidence", return_value={
            "retrieval_status": rag_status, "evidence": []
        }):
            data = checked(post(client, "consumer_complaint", CONSUMER), status=expected)
        assert not data["evidence"] and data["action_card"] is None
        assert data["warnings"]
    with patch("backend.rag_bridge.retrieve_evidence", side_effect=RuntimeError("synthetic failure")):
        data = checked(post(client, "rental_deposit", RENTAL), status="ERROR")
        assert data["evidence"] == []


def test_be_09_invalid_schema_version_and_citation_are_not_released(client):
    for record in (
        {"retrieval_status": "FOUND", "evidence": [{"evidence_id": "forged"}]},
        {"retrieval_status": "MYSTERY", "evidence": []},
        {"retrieval_status": "FOUND", "evidence": []},
    ):
        with patch("backend.rag_bridge.retrieve_evidence", return_value=record):
            data = checked(post(client, "rental_deposit", RENTAL))
        assert data["status"] in ("ERROR", "REFER_TO_OFFICIAL")
        assert not data["evidence"] and data["action_card"] is None
    with patch("backend.rag_bridge.validate_citations", side_effect=ValueError("synthetic invalid citation")):
        data = checked(post(client, "consumer_complaint", CONSUMER), status="ERROR")
        assert data["evidence"] == []


def test_be_10_disabled_rules_and_simulation_cannot_escape_over_http(client):
    configs = load_rule_configurations()
    assert all(check["runtime_enabled"] is False and check["threshold"] is None
               for category in configs.values() for check in category["checks"])
    for case, facts in (("rental_deposit", RENTAL), ("consumer_complaint", CONSUMER)):
        checked(post(client, case, facts, simulate_supported=True), status="ERROR", code=400)
        data = checked(post(client, case, facts))
        assert data["status"] != "SUPPORTED_PATH" and data["action_card"] is None
