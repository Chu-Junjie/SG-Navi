"""Task 5 real Backend/RAG integration and fail-closed regression tests."""
from copy import deepcopy
from unittest.mock import patch

import pytest
from backend.app import create_app
from backend.rag_bridge import retrieve_checked, rule_ids_for_context
from backend.rules import load_rule_configurations
from rag.import_knowledge_base import load_knowledge_base
from shared.validate_contracts import validate

RENTAL = {"dispute_with":"landlord","premises_type":"residential","claim_amount_sgd":100}
CONSUMER = {"purchase_type":"goods","purchase_purpose":"personal",
            "supplier_registered_in_sg":True,"claim_amount_sgd":100}


@pytest.fixture()
def client():
    app = create_app()
    app.config.update(TESTING=True)
    return app.test_client()


def navigate(client, case, answers):
    response = client.post("/api/navigate", json={
        "api_version":"1.0", "case_type":case, "answers":answers
    })
    assert response.status_code == 200
    data = response.get_json()
    validate(data, "navigate_response")
    return data


@pytest.mark.parametrize("case,answers", [
    ("rental_deposit", RENTAL),
    ("consumer_complaint", CONSUMER),
])
def test_real_rag_source_context_without_eligibility_conclusion(client, case, answers):
    data = navigate(client, case, answers)
    assert data["status"] == "REFER_TO_OFFICIAL"
    assert data["action_card"] is None and not data["questions"]
    assert data["evidence"] and data["warnings"]
    assert all(x["review_status"] == "verified" and x["source_version"] == data["source_version"] for x in data["evidence"])
    assert data["source_version"] == load_knowledge_base()["source_version"]
    # Retrieved Evidence is validated internally, not displayed as an unsupported route.


@pytest.mark.parametrize("case,answers", [
    ("rental_deposit", RENTAL),
    ("consumer_complaint", CONSUMER),
])
def test_real_retrieval_itself_returns_verified_citable_records(case, answers):
    configs = load_rule_configurations()
    result, records = retrieve_checked(
        case, rule_ids_for_context(case, configs), answers,
        expected_version=load_knowledge_base()["source_version"],
    )
    assert result == "FOUND"
    assert records
    assert all(record["review_status"] == "verified" and
               record["source_version"] == load_knowledge_base()["source_version"]
               for record in records)


def test_rule_ids_are_existing_disabled_context_mappings():
    configs = load_rule_configurations()
    assert rule_ids_for_context("rental_deposit", configs) == [
        "SCT_RESIDENTIAL_SCOPE", "SCT_CLAIM_AMOUNT"
    ]
    assert rule_ids_for_context("consumer_complaint", configs) == [
        "CASE_PERSONAL_PURPOSE", "CASE_SINGAPORE_SUPPLIER"
    ]


@pytest.mark.parametrize("state", ["NO_RESULTS","ERROR"])
def test_empty_or_failed_retrieval_never_shows_evidence(client, state):
    with patch("backend.rag_bridge.retrieve_evidence", return_value={
        "retrieval_status":state, "evidence":[]
    }):
        result = navigate(client,"rental_deposit",RENTAL)
    assert result["evidence"] == [] and result["action_card"] is None
    assert result["status"] == ("ERROR" if state == "ERROR" else "REFER_TO_OFFICIAL")


@pytest.mark.parametrize("bad_result", [
    {"retrieval_status":"FOUND","evidence":[]},
    {"retrieval_status":"FOUND","evidence":[{"evidence_id":"fabricated"}]},
    {"retrieval_status":"FOUND","evidence":[
        {"evidence_id":"mock-1","source_id":"mock-1","rule_ids":["SCT_CLAIM_AMOUNT"],
         "url":"https://example.invalid/mock","review_status":"verified",
         "source_version":"kb-2026-11-01.1"}]},
    {"retrieval_status":"NO_RESULTS","evidence":[{"evidence_id":"unexpected"}]},
    {"retrieval_status":"MYSTERY","evidence":[]},
    {"retrieval_status":"FOUND","evidence":{}},
])
def test_invalid_rag_envelope_never_leaks_an_unsupported_source(client,bad_result):
    with patch("backend.rag_bridge.retrieve_evidence",return_value=bad_result):
        data = navigate(client,"consumer_complaint",CONSUMER)
    assert data["status"] in ("REFER_TO_OFFICIAL","ERROR")
    assert data["evidence"] == [] and data["action_card"] is None


def test_unhandled_retrieval_exception_returns_safe_error(client):
    with patch("backend.rag_bridge.retrieve_evidence", side_effect=RuntimeError("test-only failure")):
        data = navigate(client,"rental_deposit",RENTAL)
    assert data["status"]=="ERROR" and data["evidence"] == []


def test_citation_failure_rejects_found_records(client):
    with patch("backend.rag_bridge.validate_citations",side_effect=ValueError("bad citation")):
        data = navigate(client,"rental_deposit",RENTAL)
    assert data["status"]=="ERROR" and data["evidence"] == []


def test_unknown_facts_do_not_retrieve_or_become_false(client):
    with patch("backend.rag_bridge.retrieve_evidence") as retrieval:
        data = navigate(client,"consumer_complaint",{"purchase_purpose":"unknown","claim_amount_sgd":None})
    assert data["status"]=="NEED_CLARIFICATION" and not data["evidence"]
    retrieval.assert_not_called()


def test_out_of_scope_never_retrieves(client):
    with patch("backend.rag_bridge.retrieve_evidence") as retrieval:
        data = navigate(client,"consumer_complaint",{"purchase_purpose":"business"})
    assert data["status"]=="REFER_TO_OFFICIAL" and not data["evidence"]
    retrieval.assert_not_called()


def test_source_version_mismatch_fails_closed(client):
    real = load_knowledge_base()["source_version"]
    with patch("backend.rules.engine.retrieve_checked",return_value=("INVALID", [])):
        data=navigate(client,"rental_deposit",RENTAL)
    assert data["source_version"]==real and data["evidence"]==[]


def test_rule_configuration_not_enabled():
    configs=load_rule_configurations()
    assert all(not check["runtime_enabled"] and check["threshold"] is None
               for category in configs.values() for check in category["checks"])
