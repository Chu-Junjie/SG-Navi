"""Free (ephemeral) deployment safeguards; not a persistent-storage test."""
import pytest
from unittest.mock import patch


def test_demo_must_acknowledge_ephemeral_source_state(monkeypatch):
    monkeypatch.delenv("SG_NAVI_FREE_DEMO_ACK", raising=False)
    from backend.free_demo import create_free_demo_app
    with pytest.raises(RuntimeError, match="ephemeral"):
        create_free_demo_app()


def test_demo_never_overrides_persistence_requirement(monkeypatch):
    monkeypatch.setenv("SG_NAVI_FREE_DEMO_ACK", "1")
    monkeypatch.setenv("SG_NAVI_REQUIRE_PERSISTENCE", "1")
    from backend.free_demo import create_free_demo_app
    with pytest.raises(RuntimeError, match="persistent-state"):
        create_free_demo_app()


def test_demo_serves_contract_apis_debug_off_and_small_post_limit(monkeypatch):
    monkeypatch.setenv("SG_NAVI_FREE_DEMO_ACK", "1")
    monkeypatch.setenv("SG_NAVI_REQUIRE_PERSISTENCE", "0")
    from backend.free_demo import create_free_demo_app
    app = create_free_demo_app()
    assert not app.debug
    assert app.config["MAX_CONTENT_LENGTH"] == 32768
    c = app.test_client()
    assert c.get("/api/health").status_code == 200
    v = c.get("/api/version")
    assert v.status_code == 200 and v.json["rule_version"] == "mock-1"
    assert c.post("/api/navigate", data="{" + " "*40000 + "}",
                  content_type="application/json").status_code == 413


def test_demo_bad_source_quarantine_fails_closed(monkeypatch):
    monkeypatch.setenv("SG_NAVI_FREE_DEMO_ACK", "1")
    monkeypatch.setenv("SG_NAVI_REQUIRE_PERSISTENCE", "0")
    from backend.free_demo import create_free_demo_app
    with patch("backend.free_demo.EvidenceRepository.snapshot", side_effect=ValueError("invalid state")):
        with pytest.raises(ValueError, match="invalid state"):
            create_free_demo_app()
