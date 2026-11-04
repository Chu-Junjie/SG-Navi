"""Free (ephemeral) deployment safeguards; not a persistent-storage test."""
import importlib
import os
from unittest.mock import patch

import pytest


@pytest.fixture(scope="module")
def free_demo_module():
    # The WSGI module intentionally fails fast without explicit ephemeral ack.
    # Give it that acknowledgement only for its first import in this fixture.
    with patch.dict(os.environ, {
        "SG_NAVI_FREE_DEMO_ACK": "1", "SG_NAVI_REQUIRE_PERSISTENCE": "0"
    }):
        return importlib.import_module("backend.free_demo")


def test_demo_must_acknowledge_ephemeral_source_state(monkeypatch, free_demo_module):
    monkeypatch.delenv("SG_NAVI_FREE_DEMO_ACK", raising=False)
    with pytest.raises(RuntimeError, match="ephemeral"):
        free_demo_module.create_free_demo_app()


def test_demo_never_overrides_persistence_requirement(monkeypatch, free_demo_module):
    monkeypatch.setenv("SG_NAVI_FREE_DEMO_ACK", "1")
    monkeypatch.setenv("SG_NAVI_REQUIRE_PERSISTENCE", "1")
    with pytest.raises(RuntimeError, match="persistent-state"):
        free_demo_module.create_free_demo_app()


def test_demo_serves_contract_apis_debug_off_and_small_post_limit(monkeypatch, free_demo_module):
    monkeypatch.setenv("SG_NAVI_FREE_DEMO_ACK", "1")
    monkeypatch.setenv("SG_NAVI_REQUIRE_PERSISTENCE", "0")
    app = free_demo_module.create_free_demo_app()
    assert not app.debug
    assert app.config["MAX_CONTENT_LENGTH"] == 32768
    c = app.test_client()
    assert c.get("/api/health").status_code == 200
    v = c.get("/api/version")
    assert v.status_code == 200 and v.json["rule_version"] == "mock-1"
    assert c.post("/api/navigate", data="{" + " "*40000 + "}",
                  content_type="application/json").status_code == 413


def test_demo_bad_source_quarantine_fails_closed(monkeypatch, free_demo_module):
    monkeypatch.setenv("SG_NAVI_FREE_DEMO_ACK", "1")
    monkeypatch.setenv("SG_NAVI_REQUIRE_PERSISTENCE", "0")
    with patch("backend.free_demo.EvidenceRepository.snapshot", side_effect=ValueError("invalid state")):
        with pytest.raises(ValueError, match="invalid state"):
            free_demo_module.create_free_demo_app()
