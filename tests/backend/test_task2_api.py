"""Contract checks for Task 2 Flask API placeholders."""
import pytest
from shared.validate_contracts import validate
from backend.app import create_app

@pytest.fixture
def client():
    app = create_app()
    app.config["TESTING"] = True
    return app.test_client()

def test_case_types(client):
    res = client.get("/api/case-types")
    assert res.status_code == 200
    validate(res.get_json(), "case_types_response")
    assert res.get_json()["case_types"] == ["rental_deposit", "consumer_complaint"]

def test_version(client):
    res = client.get("/api/version")
    assert res.status_code == 200
    validate(res.get_json(), "version_response")

@pytest.mark.parametrize("case_type", ["rental_deposit", "consumer_complaint"])
def test_missing_amount_clarifies(client, case_type):
    payload = {"api_version": "1.0", "case_type": case_type, "answers": {"claim_amount_sgd": None}}
    res = client.post("/api/navigate", json=payload)
    assert res.status_code == 200
    data = res.get_json()
    validate(data, "navigate_response")
    assert data["status"] == "NEED_CLARIFICATION"
    assert "claim_amount_sgd" in {question["id"] for question in data["questions"]}

def test_unknown_is_not_false(client):
    payload = {"api_version": "1.0", "case_type": "rental_deposit", "answers": {"claim_amount_sgd": "unknown"}}
    res = client.post("/api/navigate", json=payload)
    assert res.get_json()["status"] == "NEED_CLARIFICATION"

def test_no_unverified_supported_path(client):
    payload = {"api_version": "1.0", "case_type": "consumer_complaint", "answers": {"claim_amount_sgd": 100}}
    res = client.post("/api/navigate", json=payload)
    data = res.get_json()
    validate(data, "navigate_response")
    assert data["status"] in {"NEED_CLARIFICATION", "REFER_TO_OFFICIAL"}
    assert data["evidence"] == []
    assert data["action_card"] is None

@pytest.mark.parametrize("payload", [
    {"api_version": "2.0", "case_type": "rental_deposit", "answers": {}},
    {"api_version": "1.0", "case_type": "invalid", "answers": {}},
    {"api_version": "1.0", "case_type": "rental_deposit", "answers": []},
    {"api_version": "1.0", "case_type": "rental_deposit", "answers": {}, "extra": True},
])
def test_invalid_requests(client, payload):
    res = client.post("/api/navigate", json=payload)
    assert res.status_code == 400
    data = res.get_json()
    assert data["status"] == "ERROR"
    validate(data, "navigate_response")

def test_invalid_content_type(client):
    res = client.post("/api/navigate", data="hello", content_type="text/plain")
    assert res.status_code == 415
    validate(res.get_json(), "navigate_response")

def test_bad_json(client):
    res = client.post("/api/navigate", data="{", content_type="application/json")
    assert res.status_code == 400
    validate(res.get_json(), "navigate_response")
