"""Task 7 free public *demo*, intentionally NOT persistent service acceptance."""
from unittest.mock import patch
import pytest


def make(monkeypatch, *, free="1", persistent="0", render="true"):
    monkeypatch.setenv("SG_NAVI_FREE_DEMO", free)
    monkeypatch.setenv("SG_NAVI_REQUIRE_PERSISTENCE", persistent)
    monkeypatch.setenv("RENDER", render)
    from backend.production import create_production_app
    return create_production_app()


def test_free_demo_boots_without_mount_but_discloses_ephemeral_mode(monkeypatch):
    with patch("pathlib.Path.is_mount", return_value=False):
        app = make(monkeypatch)
    assert app.debug is False
    client = app.test_client()
    for url in ("/api/health", "/api/version"):
        res = client.get(url, headers={"Origin": "https://chu-junjie.github.io"})
        assert res.status_code == 200
        assert res.headers["X-SG-Navi-Deployment-Mode"] == "ephemeral-free-demo"
        assert res.headers["Access-Control-Allow-Origin"] == "https://chu-junjie.github.io"


def test_free_demo_cannot_bypass_mandatory_persistence(monkeypatch):
    monkeypatch.setenv("SG_NAVI_FREE_DEMO", "1")
    monkeypatch.setenv("SG_NAVI_REQUIRE_PERSISTENCE", "1")
    from backend.production import create_production_app
    with pytest.raises(RuntimeError, match="conflicts"):
        create_production_app()


def test_paid_mode_still_rejects_missing_disk(monkeypatch):
    from backend.production import create_production_app
    monkeypatch.setenv("SG_NAVI_FREE_DEMO", "0")
    monkeypatch.setenv("SG_NAVI_REQUIRE_PERSISTENCE", "1")
    with patch("pathlib.Path.is_mount", return_value=False):
        with pytest.raises(RuntimeError, match="persistent disk"):
            create_production_app()


def test_free_demo_retains_fail_closed_source_integrity(monkeypatch):
    monkeypatch.setenv("SG_NAVI_FREE_DEMO", "1")
    monkeypatch.setenv("SG_NAVI_REQUIRE_PERSISTENCE", "0")
    from backend.production import create_production_app
    with patch("backend.production.EvidenceRepository.snapshot",
               side_effect=ValueError("test simulated corrupt state")):
        with pytest.raises(ValueError, match="corrupt state"):
            create_production_app()


@pytest.mark.parametrize("value", ["yes", "True", "2", "false"])
def test_free_demo_invalid_flag_refused(monkeypatch, value):
    monkeypatch.setenv("SG_NAVI_FREE_DEMO", value)
    from backend.production import create_production_app
    with pytest.raises(RuntimeError, match="SG_NAVI_FREE_DEMO"):
        create_production_app()
