"""Task 7 public backend: production WSGI, origin CORS and persistence gates.

Tests use only synthetic case facts. None of them modify canonical source data
or the real quarantine file.
"""
from pathlib import Path
from unittest.mock import patch

import pytest
from shared.validate_contracts import validate
from backend.production import create_production_app
from backend.cors import DEFAULT_ORIGIN


@pytest.fixture
def client(monkeypatch):
    monkeypatch.delenv("SG_NAVI_REQUIRE_PERSISTENCE", raising=False)
    monkeypatch.delenv("SG_NAVI_CORS_ORIGINS", raising=False)
    return create_production_app().test_client()


def test_task7_wsgi_production_mode_and_healthy_versions(client):
    assert client.application.debug is False
    health = client.get("/api/health", headers={"Origin": DEFAULT_ORIGIN})
    assert health.status_code == 200
    validate(health.get_json(), "health_response")
    assert health.headers["Access-Control-Allow-Origin"] == DEFAULT_ORIGIN
    assert health.headers["Cache-Control"] == "no-store"
    version = client.get("/api/version", headers={"Origin": DEFAULT_ORIGIN})
    assert version.status_code == 200
    validate(version.get_json(), "version_response")
    assert version.get_json()["source_version"].startswith("kb-")
    assert version.get_json()["rule_version"] == "mock-1"


@pytest.mark.parametrize("endpoint,method", [
    ("/api/health", "GET"),
    ("/api/version", "GET"),
    ("/api/case-types", "GET"),
    ("/api/navigate", "POST"),
])
def test_task7_valid_cors_preflight(client, endpoint, method):
    response = client.options(endpoint, headers={
        "Origin": DEFAULT_ORIGIN,
        "Access-Control-Request-Method": method,
        "Access-Control-Request-Headers": "Content-Type",
    })
    assert response.status_code == 204
    assert response.headers["Access-Control-Allow-Origin"] == DEFAULT_ORIGIN
    assert method in response.headers["Access-Control-Allow-Methods"]
    assert response.headers["Access-Control-Allow-Headers"] == "Content-Type"
    assert response.headers["Access-Control-Max-Age"] == "600"
    assert response.headers.get("Access-Control-Allow-Credentials") is None


@pytest.mark.parametrize("origin", [
    "https://evil.example", "http://chu-junjie.github.io",
    "https://chu-junjie.github.io.evil.example", "null",
])
def test_task7_other_origins_denied(client, origin):
    assert client.get("/api/health", headers={
        "Origin": origin
    }).headers.get("Access-Control-Allow-Origin") is None
    forbidden = client.options("/api/navigate", headers={
        "Origin": origin, "Access-Control-Request-Method": "POST",
        "Access-Control-Request-Headers": "content-type",
    })
    assert forbidden.status_code == 403
    assert forbidden.headers.get("Access-Control-Allow-Origin") is None


def test_task7_rejects_unknown_preflight_method_or_header(client):
    headers = {"Origin": DEFAULT_ORIGIN,
               "Access-Control-Request-Method": "DELETE"}
    assert client.options("/api/navigate", headers=headers).status_code == 405
    headers["Access-Control-Request-Method"] = "POST"
    headers["Access-Control-Request-Headers"] = "Authorization"
    response = client.options("/api/navigate", headers=headers)
    assert response.status_code == 400
    assert "Authorization" not in response.headers.get("Access-Control-Allow-Headers", "")


@pytest.mark.parametrize("origin_config", [
    "*", "http://chu-junjie.github.io",
    "https://chu-junjie.github.io/SG-Navi",
    "https://chu-junjie.github.io/",
    "https://user:password@chu-junjie.github.io",
])
def test_task7_invalid_cors_config_fails_at_startup(monkeypatch, origin_config):
    monkeypatch.setenv("SG_NAVI_CORS_ORIGINS", origin_config)
    with pytest.raises(ValueError):
        create_production_app()


@pytest.mark.parametrize("case,answers", [
    ("rental_deposit", {"dispute_with": "landlord", "premises_type": "residential",
                        "claim_amount_sgd": 123}),
    ("consumer_complaint", {"purchase_type": "goods", "purchase_purpose": "personal",
                            "supplier_registered_in_sg": True, "claim_amount_sgd": 123}),
])
def test_task7_public_origin_real_rag_request_contract(client, case, answers):
    response = client.post("/api/navigate", json={
        "api_version": "1.0", "case_type": case, "answers": answers
    }, headers={"Origin": DEFAULT_ORIGIN})
    assert response.status_code == 200
    data = response.get_json()
    validate(data, "navigate_response")
    assert data["status"] == "REFER_TO_OFFICIAL"
    assert data["action_card"] is None and data["evidence"]
    assert response.headers["Access-Control-Allow-Origin"] == DEFAULT_ORIGIN
    assert all(e["review_status"] == "verified" and
               e["source_version"] == data["source_version"] for e in data["evidence"])


def test_task7_public_origin_missing_facts_stay_unknown(client):
    response = client.post("/api/navigate", json={
        "api_version": "1.0", "case_type": "rental_deposit", "answers": {}
    }, headers={"Origin": DEFAULT_ORIGIN})
    assert response.status_code == 200
    data = response.get_json()
    assert data["status"] == "NEED_CLARIFICATION"
    assert data["questions"] and not data["evidence"]


def test_task7_required_disk_missing_fails_before_public_startup(monkeypatch):
    monkeypatch.setenv("SG_NAVI_REQUIRE_PERSISTENCE", "1")
    with patch.object(Path, "is_mount", return_value=False):
        with pytest.raises(RuntimeError, match="persistent disk"):
            create_production_app()


def test_task7_unreadable_persistent_state_fails_before_public_startup(monkeypatch):
    monkeypatch.setenv("SG_NAVI_REQUIRE_PERSISTENCE", "1")
    with (patch.object(Path, "is_mount", return_value=True),
          patch("backend.production.os.access", return_value=True),
          patch("backend.production.EvidenceRepository.snapshot",
                side_effect=ValueError("synthetic corrupt state"))):
        with pytest.raises(ValueError, match="synthetic corrupt state"):
            create_production_app()


def test_task7_missing_disk_write_permission_fails_before_public_startup(monkeypatch):
    monkeypatch.setenv("SG_NAVI_REQUIRE_PERSISTENCE", "1")
    with (patch.object(Path, "is_mount", return_value=True),
          patch("backend.production.os.access", return_value=False)):
        with pytest.raises(RuntimeError, match="not writable"):
            create_production_app()
