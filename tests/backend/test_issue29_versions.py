"""Issue #29: source version consistency and storage failure safety."""
from unittest.mock import patch

import pytest
from backend.app import create_app
from backend.versioning import UNAVAILABLE_SOURCE_VERSION, SourceVersionUnavailable
from rag.repository import EvidenceRepository
from shared.validate_contracts import validate

RENTAL = {"dispute_with": "landlord", "premises_type": "residential",
          "claim_amount_sgd": 123}
CONSUMER = {"purchase_type": "goods", "purchase_purpose": "personal",
            "supplier_registered_in_sg": True, "claim_amount_sgd": 123}


@pytest.fixture
def client():
    app = create_app()
    app.config["TESTING"] = True
    return app.test_client()


def request_case(client, case, answers):
    result = client.post("/api/navigate", json={
        "api_version": "1.0", "case_type": case, "answers": answers
    })
    validate(result.get_json(), "navigate_response")
    return result


@pytest.mark.parametrize("case,answers", [
    ("rental_deposit", RENTAL),
    ("consumer_complaint", CONSUMER),
    ("rental_deposit", {}),
    ("consumer_complaint", {"purchase_purpose": "business"}),
    ("rental_deposit", {"claim_amount_sgd": -1}),
    ("consumer_complaint", {"claim_amount_sgd": "unknown"}),
])
def test_version_endpoint_matches_all_response_paths(client, case, answers):
    version = client.get("/api/version")
    assert version.status_code == 200
    validate(version.get_json(), "version_response")
    current = EvidenceRepository().snapshot()[0]["source_version"]
    assert version.get_json()["source_version"] == current
    assert version.get_json()["rule_version"] == "mock-1"
    result = request_case(client, case, answers)
    assert result.get_json()["source_version"] == current
    assert result.get_json()["rule_version"] == "mock-1"


def test_invalid_json_and_content_type_also_report_real_version(client):
    source = client.get("/api/version").get_json()["source_version"]
    cases = [
        client.post("/api/navigate", data="{", content_type="application/json"),
        client.post("/api/navigate", data="not-json", content_type="text/plain"),
        client.post("/api/navigate", json={"case_type": "rental_deposit"}),
    ]
    assert [r.status_code for r in cases] == [400, 415, 400]
    for result in cases:
        validate(result.get_json(), "navigate_response")
        assert result.get_json()["status"] == "ERROR"
        assert result.get_json()["source_version"] == source


def test_fail_closed_if_bundle_or_operational_state_is_unavailable(client):
    with patch("backend.versioning.EvidenceRepository.snapshot",
               side_effect=OSError("synthetic unavailable state")):
        version = client.get("/api/version")
        assert version.status_code == 503
        validate(version.get_json(), "version_response")
        assert version.get_json()["source_version"] == UNAVAILABLE_SOURCE_VERSION
        result = request_case(client, "rental_deposit", RENTAL)
        assert result.status_code == 503
        assert result.get_json()["status"] == "ERROR"
        assert result.get_json()["source_version"] == UNAVAILABLE_SOURCE_VERSION
        assert not result.get_json()["evidence"]
        assert result.get_json()["action_card"] is None


def test_read_failure_does_not_fall_back_to_mock_version(client):
    with patch("backend.versioning.EvidenceRepository.snapshot",
               side_effect=ValueError("synthetic corrupt quarantine state")):
        result = client.get("/api/version")
        assert result.status_code == 503
        assert result.get_json()["source_version"] == "unavailable"


def test_version_is_not_cached_across_requests(client):
    real = EvidenceRepository().snapshot()[0]["source_version"]
    assert client.get("/api/version").get_json()["source_version"] == real
    with patch("backend.versioning.EvidenceRepository.snapshot",
               side_effect=OSError("temporary unavailable")):
        assert client.get("/api/version").status_code == 503
    assert client.get("/api/version").get_json()["source_version"] == real
