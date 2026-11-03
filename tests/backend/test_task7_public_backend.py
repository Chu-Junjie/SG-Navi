"""Task 7 public API: CORS, real Rental/Consumer wire, and deploy guard.

These are local Flask/production-entrypoint tests; a successful CI run is NOT
evidence of a deployed HTTPS hostname or of persistent disks on Render.
"""
from unittest.mock import patch

import pytest
from backend.app import create_app
from backend.cors import DEFAULT_ORIGIN
from shared.validate_contracts import validate

ORIGIN = DEFAULT_ORIGIN
OTHER = "https://different.example.org"
RENTAL = {"dispute_with": "landlord", "premises_type": "residential", "claim_amount_sgd": 123}
CONSUMER = {
    "purchase_type": "goods", "purchase_purpose": "personal",
    "supplier_registered_in_sg": True, "claim_amount_sgd": 123,
}


@pytest.fixture
def client(monkeypatch):
    monkeypatch.delenv("SG_NAVI_CORS_ORIGINS", raising=False)
    app = create_app()
    app.config["TESTING"] = True
    return app.test_client()


@pytest.mark.parametrize("path,definition", [
    ("/api/health", "health_response"),
    ("/api/version", "version_response"),
    ("/api/case-types", "case_types_response"),
])
def test_get_api_from_real_pages_origin(client, path, definition):
    result = client.get(path, headers={"Origin": ORIGIN})
    assert result.status_code == 200
    validate(result.get_json(), definition)
    assert result.headers["Access-Control-Allow-Origin"] == ORIGIN
    assert result.headers["Cache-Control"] == "no-store"
    assert "Origin" in result.headers["Vary"]
    assert "Access-Control-Allow-Credentials" not in result.headers


@pytest.mark.parametrize("case,answers", [
    ("rental_deposit", RENTAL), ("consumer_complaint", CONSUMER),
])
def test_real_post_navigate_from_pages_is_contract_valid(client, case, answers):
    response = client.post("/api/navigate", json={
        "api_version": "1.0", "case_type": case, "answers": answers,
    }, headers={"Origin": ORIGIN})
    assert response.status_code == 200
    data = response.get_json()
    validate(data, "navigate_response")
    assert data["status"] == "REFER_TO_OFFICIAL"
    assert data["action_card"] is None
    assert data["evidence"] and data["source_version"] != "mock-1"
    assert all(record["review_status"] == "verified" for record in data["evidence"])
    assert response.headers["Access-Control-Allow-Origin"] == ORIGIN


@pytest.mark.parametrize("path,method", [
    ("/api/health", "GET"), ("/api/version", "GET"),
    ("/api/case-types", "GET"), ("/api/navigate", "POST"),
])
def test_preflight_allowed_methods_and_headers(client, path, method):
    headers = {
        "Origin": ORIGIN,
        "Access-Control-Request-Method": method,
        "Access-Control-Request-Headers": "content-type",
    }
    response = client.options(path, headers=headers)
    assert response.status_code == 204
    assert response.headers["Access-Control-Allow-Origin"] == ORIGIN
    assert method in response.headers["Access-Control-Allow-Methods"]
    assert response.headers["Access-Control-Allow-Headers"] == "Content-Type"
    assert response.headers["Access-Control-Max-Age"] == "600"


def test_invalid_cors_origin_does_not_receive_trusted_header(client):
    for origin in (OTHER, "http://chu-junjie.github.io",
                   "https://chu-junjie.github.io.evil.example"):
        ordinary = client.get("/api/health", headers={"Origin": origin})
        assert ordinary.status_code == 200
        assert "Access-Control-Allow-Origin" not in ordinary.headers
        preflight = client.options("/api/navigate", headers={
            "Origin": origin,
            "Access-Control-Request-Method": "POST",
            "Access-Control-Request-Headers": "content-type",
        })
        assert preflight.status_code == 403
        assert "Access-Control-Allow-Origin" not in preflight.headers


def test_preflight_refuses_incorrect_method_or_unsafe_headers(client):
    wrong_method = client.options("/api/navigate", headers={
        "Origin": ORIGIN, "Access-Control-Request-Method": "DELETE"
    })
    assert wrong_method.status_code == 405
    extra_header = client.options("/api/navigate", headers={
        "Origin": ORIGIN, "Access-Control-Request-Method": "POST",
        "Access-Control-Request-Headers": "authorization,content-type"
    })
    assert extra_header.status_code == 400


@pytest.mark.parametrize("value", [
    "*", "http://chu-junjie.github.io", "https://chu-junjie.github.io/SG-Navi/",
    "https://chu-junjie.github.io/",
    "https://u:password@chu-junjie.github.io",
])
def test_public_api_rejects_unsafe_origin_configuration(monkeypatch, value):
    monkeypatch.setenv("SG_NAVI_CORS_ORIGINS", value)
    with pytest.raises(ValueError):
        create_app()


def test_production_wsgi_starts_debug_off_without_paid_mount_env(monkeypatch):
    monkeypatch.delenv("SG_NAVI_REQUIRE_PERSISTENCE", raising=False)
    from backend.production import create_production_app
    app = create_production_app()
    assert not app.debug and not app.config["TESTING"]
    assert app.test_client().get("/api/health").status_code == 200


def test_public_wsgI_fails_closed_when_disk_not_mounted(monkeypatch):
    monkeypatch.setenv("SG_NAVI_REQUIRE_PERSISTENCE", "1")
    from backend.production import create_production_app
    with patch("pathlib.Path.is_mount", return_value=False):
        with pytest.raises(RuntimeError, match="persistent disk"):
            create_production_app()


def test_json_error_preserves_cors_on_response(client):
    result = client.post("/api/navigate", json={
        "api_version": "1.0", "case_type": "rental_deposit", "answers": [],
    }, headers={"Origin": ORIGIN})
    assert result.status_code == 400
    assert result.get_json()["status"] == "ERROR"
    assert result.headers["Access-Control-Allow-Origin"] == ORIGIN
