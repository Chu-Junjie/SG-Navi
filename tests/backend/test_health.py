"""Task 1 checks for the minimal backend and homepage wiring."""
from pathlib import Path

import pytest

from backend.app import create_app


@pytest.fixture()
def client():
    application = create_app()
    application.config.update(TESTING=True)
    return application.test_client()


def test_health_status_and_json(client):
    response = client.get("/api/health")
    assert response.status_code == 200
    assert response.is_json
    assert response.get_json() == {"status": "ok"}


def test_health_is_not_a_post_endpoint(client):
    response = client.post("/api/health")
    assert response.status_code == 405


def test_homepage_uses_existing_frontend(client):
    frontend_path = Path(__file__).resolve().parents[2] / "frontend" / "index.html"
    if not frontend_path.is_file():
        pytest.skip("Frontend belongs to Guanyu-Lu and is not available in this checkout")
    response = client.get("/")
    assert response.status_code == 200
    assert b"SG Navi" in response.data
    assert b"/api/health" in response.data
