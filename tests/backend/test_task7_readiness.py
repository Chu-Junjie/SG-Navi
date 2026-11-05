"""A healthy process must not claim that unavailable source/state data is ready."""
from unittest.mock import patch

import pytest

from backend.app import create_app
from shared.validate_contracts import validate


@pytest.mark.parametrize("failure", [OSError("private database error"), ValueError("invalid source state")])
def test_health_fails_closed_when_critical_state_cannot_be_validated(failure):
    client = create_app().test_client()
    with patch("backend.versioning.EvidenceRepository.snapshot", side_effect=failure):
        response = client.get("/api/health", headers={"Origin": "https://chu-junjie.github.io"})
    assert response.status_code == 503
    assert response.get_json() == {"status": "unavailable"}
    validate(response.get_json(), "health_response")
    assert response.headers["Access-Control-Allow-Origin"] == "https://chu-junjie.github.io"
    assert response.headers["Cache-Control"] == "no-store"
    assert b"private" not in response.data and b"invalid source" not in response.data


def test_health_recovers_when_critical_state_recovers():
    client = create_app().test_client()
    with patch("backend.versioning.EvidenceRepository.snapshot", side_effect=OSError("synthetic outage")):
        assert client.get("/api/health").status_code == 503
    assert client.get("/api/health").get_json() == {"status": "ok"}
