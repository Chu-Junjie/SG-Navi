"""Integration configuration: deliver real modules without exposing the repo."""
from pathlib import Path

import pytest

from integration.app import create_app
from shared.validate_contracts import validate

ROOT = Path(__file__).resolve().parents[2]


@pytest.mark.parametrize("filename", [
    "task5-flow.html", "js/task5-flow.js", "task4-forms.html", "js/task4-forms.js", "schemas/rental_deposit_input.schema.json",
    "schemas/consumer_complaint_input.schema.json", "mappings/task3_display_map.json",
])
def test_same_origin_serves_existing_frontend_unchanged(filename):
    response = create_app().test_client().get("/" + filename)
    assert response.status_code == 200
    assert response.data == (ROOT / "frontend" / filename).read_bytes()


@pytest.mark.parametrize("url", [
    "/AGENTS.md", "/rag/knowledge_base/sources.csv", "/backend/app.py",
    "/js/../../AGENTS.md", "/js/%2e%2e/%2e%2e/AGENTS.md", "/api/not-a-route",
])
def test_integration_origin_does_not_expose_repository_or_swallow_api_errors(url):
    assert create_app().test_client().get(url).status_code == 404


def test_real_api_and_frontend_share_origin():
    client = create_app().test_client()
    response = client.get("/api/health")
    assert response.status_code == 200
    validate(response.get_json(), "health_response")
    response = client.post("/api/navigate", json={
        "api_version": "1.0", "case_type": "consumer_complaint", "answers": {},
    })
    assert response.status_code == 200
    validate(response.get_json(), "navigate_response")
    assert response.get_json()["status"] == "NEED_CLARIFICATION"
    assert response.get_json()["action_card"] is None
