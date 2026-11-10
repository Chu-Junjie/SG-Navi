"""Task 24 release/CORS contract: no exposed Chinese before approval."""
import pytest
from backend.app import create_app
from backend import production

ORIGIN = "https://chu-junjie.github.io"
PATH = "/api/action-plan/zh-hans-reviewed"
REQUEST = {
    "action_plan_version": "1.0",
    "request_id": "task24-release-12345",
    "operation": "interpret",
    "description": "I bought a faulty product and want a refund.",
}


def preflight(client, origin=ORIGIN):
    return client.options(PATH, headers={
        "Origin": origin, "Access-Control-Request-Method": "POST",
        "Access-Control-Request-Headers": "content-type"})


def test_default_off_preflight_and_post_do_not_expose_cross_origin():
    app = create_app()
    c = app.test_client()
    pre = preflight(c)
    assert pre.status_code == 404
    assert "Access-Control-Allow-Origin" not in pre.headers
    post = c.post(PATH, json=REQUEST, headers={"Origin": ORIGIN})
    assert post.status_code == 404
    assert "Access-Control-Allow-Origin" not in post.headers


def test_pages_cors_after_explicit_approval_flag_but_no_real_approval_still_503():
    app = create_app()
    app.config["TASK24_ENABLE_REVIEWED_LOCALE"] = True
    c = app.test_client()
    pre = preflight(c)
    assert pre.status_code == 204
    assert pre.headers["Access-Control-Allow-Origin"] == ORIGIN
    assert "POST" in pre.headers["Access-Control-Allow-Methods"]
    response = c.post(PATH, json=REQUEST, headers={"Origin": ORIGIN})
    assert response.status_code == 503
    assert response.get_json()["error"] == "translation_not_approved"
    assert response.headers["Access-Control-Allow-Origin"] == ORIGIN
    assert response.headers["Cache-Control"] == "no-store"


def test_forbidden_origins_and_methods():
    app = create_app()
    app.config["TASK24_ENABLE_REVIEWED_LOCALE"] = True
    client = app.test_client()
    assert preflight(client, "https://evil.invalid").status_code == 403
    invalid = client.options(PATH, headers={
        "Origin": ORIGIN, "Access-Control-Request-Method": "DELETE"})
    assert invalid.status_code == 405
    invalid = client.options(PATH, headers={
        "Origin": ORIGIN, "Access-Control-Request-Method": "POST",
        "Access-Control-Request-Headers": "authorization"})
    assert invalid.status_code == 400
    denied = client.post(PATH, json=REQUEST, headers={"Origin": "https://evil.invalid"})
    assert "Access-Control-Allow-Origin" not in denied.headers


def test_legacy_english_action_plan_remains_working():
    app = create_app()
    response = app.test_client().post("/api/action-plan", json=REQUEST)
    assert response.status_code == 200
    assert response.get_json()["state"] == "CONFIRM"
    assert "display" not in response.get_json()


def test_production_feature_flag_off_and_invalid(monkeypatch):
    monkeypatch.delenv("RENDER", raising=False)
    monkeypatch.delenv("SG_NAVI_REQUIRE_PERSISTENCE", raising=False)
    monkeypatch.delenv("SG_NAVI_FREE_DEMO", raising=False)
    monkeypatch.delenv("SG_NAVI_STATE_DATABASE_URL", raising=False)
    monkeypatch.setenv("SG_NAVI_TASK24_REVIEWED_LOCALE", "0")
    app = production.create_production_app()
    assert app.config["TASK24_ENABLE_REVIEWED_LOCALE"] is False
    monkeypatch.setenv("SG_NAVI_TASK24_REVIEWED_LOCALE", "invalid")
    with pytest.raises(RuntimeError, match="SG_NAVI_TASK24_REVIEWED_LOCALE"):
        production.create_production_app()


def test_production_enable_requires_real_approval(monkeypatch):
    monkeypatch.delenv("RENDER", raising=False)
    monkeypatch.delenv("SG_NAVI_REQUIRE_PERSISTENCE", raising=False)
    monkeypatch.delenv("SG_NAVI_FREE_DEMO", raising=False)
    monkeypatch.delenv("SG_NAVI_STATE_DATABASE_URL", raising=False)
    monkeypatch.setenv("SG_NAVI_TASK24_REVIEWED_LOCALE", "1")
    from backend.task24_delivery import ChineseTranslationNotApproved
    with pytest.raises(ChineseTranslationNotApproved):
        production.create_production_app()
