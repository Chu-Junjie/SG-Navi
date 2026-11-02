"""Independent Task 4 backend rule-engine tests (no live legal decisions)."""
from copy import deepcopy
import pytest

from backend.app import create_app
from backend.rules.engine import SYNTHETIC_EVIDENCE, evaluate
from shared.validate_contracts import validate


@pytest.fixture
def client():
    app = create_app()
    app.config["TESTING"] = True
    return app.test_client()


def post(client, case_type, answers):
    return client.post("/api/navigate", json={
        "api_version": "1.0", "case_type": case_type, "answers": answers
    })


@pytest.mark.parametrize("case,answers", [
    ("rental_deposit", {"premises_type": "commercial", "claim_amount_sgd": 300}),
    ("rental_deposit", {"premises_type": "industrial", "claim_amount_sgd": 300}),
    ("consumer_complaint", {"purchase_purpose": "business", "claim_amount_sgd": 300}),
    ("consumer_complaint", {"supplier_registered_in_sg": False, "claim_amount_sgd": 300}),
])
def test_outside_pilot_scope_refers_to_official(client, case, answers):
    r = post(client, case, answers)
    assert r.status_code == 200
    data = r.get_json()
    validate(data, "navigate_response")
    assert data["status"] == "REFER_TO_OFFICIAL"
    assert data["action_card"] is None and data["evidence"] == []


@pytest.mark.parametrize("case,answers", [
    ("rental_deposit", {}),
    ("consumer_complaint", {"claim_amount_sgd": None}),
    ("rental_deposit", {"dispute_with": "unknown", "claim_amount_sgd": 50}),
    ("consumer_complaint", {"supplier_registered_in_sg": "unknown", "claim_amount_sgd": 0}),
])
def test_missing_null_and_unknown_ask_questions(client, case, answers):
    r = post(client, case, answers)
    assert r.status_code == 200
    data = r.get_json()
    validate(data, "navigate_response")
    assert data["status"] == "NEED_CLARIFICATION"
    assert data["questions"] and data["evidence"] == []
    assert all(q["required"] is True for q in data["questions"])


@pytest.mark.parametrize("case,answers", [
    ("rental_deposit", {"dispute_with": "landlord", "premises_type": "residential", "claim_amount_sgd": 100}),
    ("consumer_complaint", {"purchase_type": "goods", "purchase_purpose": "personal",
                            "supplier_registered_in_sg": True, "claim_amount_sgd": 100}),
])
def test_no_unsupported_conclusions_in_normal_api(client, case, answers):
    data = post(client, case, answers).get_json()
    validate(data, "navigate_response")
    assert data["status"] == "REFER_TO_OFFICIAL"
    assert data["action_card"] is None
    assert all(item["review_status"] == "verified" for item in data["evidence"])


def test_synthetic_supported_path_is_explicitly_test_only():
    data = evaluate("rental_deposit", {
        "dispute_with": "landlord",
        "premises_type": "residential",
        "claim_amount_sgd": 1,
    }, simulate_supported=True)
    validate(data, "navigate_response")
    assert data["status"] == "SUPPORTED_PATH"
    assert data["action_card"]["citations"] == [SYNTHETIC_EVIDENCE["evidence_id"]]
    assert data["warnings"] and "SIMULATION" in data["warnings"][0]
    assert data["evidence"][0]["url"].startswith("https://example.invalid/")


@pytest.mark.parametrize("mutator", [
    lambda e: e.update(evidence_id="invented"),
    lambda e: e.update(review_status="quarantined"),
    lambda e: e.update(url="https://not-a-real-source.example/"),
    lambda e: e.pop("source_id"),
])
def test_invalid_or_nonfixture_evidence_never_supports_a_path(mutator):
    fixture = deepcopy(SYNTHETIC_EVIDENCE)
    mutator(fixture)
    result = evaluate("rental_deposit", {
        "dispute_with": "landlord", "premises_type": "residential", "claim_amount_sgd": 1
    }, simulate_supported=True, mock_evidence=fixture)
    assert result["status"] == "REFER_TO_OFFICIAL"
    validate(result, "navigate_response")


def test_http_request_cannot_turn_on_synthetic_supported_path(client):
    data = client.post("/api/navigate", json={
        "api_version": "1.0",
        "case_type": "rental_deposit",
        "answers": {"dispute_with": "landlord", "premises_type": "residential", "claim_amount_sgd": 1},
        "simulate_supported": True,
    })
    assert data.status_code == 400
    assert data.get_json()["status"] == "ERROR"


def test_false_not_treated_as_missing(client):
    data = post(client, "consumer_complaint", {
        "purchase_type": "goods",
        "purchase_purpose": "personal",
        "supplier_registered_in_sg": False,
        "claim_amount_sgd": 0,
    }).get_json()
    assert data["status"] == "REFER_TO_OFFICIAL"


def test_negative_amount_rejected(client):
    result = post(client, "rental_deposit", {"claim_amount_sgd": -1})
    assert result.status_code == 400
    assert result.get_json()["status"] == "ERROR"
