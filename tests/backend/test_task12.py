"""Task 12 controlled regression: no legal eligibility or fabricated citation."""
import pytest

from backend.app import create_app
from backend.results import assemble

@pytest.fixture
def client():
    return create_app().test_client()

def post(client, case_type, answers, **changes):
    body = {"results_version": "0.1", "confirmed": True, "case_type": case_type,
            "confirmed_answers": answers}
    body.update(changes)
    return client.post("/api/results/preview", json=body)

def test_rental_citations_and_original_excerpts(client):
    r = post(client, "rental_deposit", {"dispute_with": "landlord", "premises_type": "residential"})
    assert r.status_code == 200
    doc = r.get_json()
    assert doc["guidance_status"] == "GUIDANCE_ONLY"
    assert doc["research_guidance"]["steps"]
    assert doc["unresolved_fields"]
    evidence = {row["evidence_id"]: row for row in doc["display_evidence"]}
    for section in ("potential_channels", "conditions", "steps", "document_checklist"):
        for item in doc["research_guidance"][section]:
            assert item["evidence_ids"]
            assert all(key in evidence for key in item["evidence_ids"])
    assert all(row["verbatim_excerpt"] and row["source_locator"]
               and row["url"].startswith("https://") for row in evidence.values())
    assert doc["research_guidance"]["citations"] == sorted(evidence)

def test_consumer_confirmed_personal_and_sg(client):
    r = post(client, "consumer_complaint", {"purchase_purpose": "personal",
                                              "supplier_registered_in_sg": True,
                                              "supplier_location": "singapore"})
    assert r.status_code == 200
    doc = r.get_json()
    assert doc["guidance_status"] == "GUIDANCE_ONLY"
    assert all("CEA" not in item["text"] for item in
               doc["research_guidance"]["potential_channels"])

@pytest.mark.parametrize("case_type,answers", [
    ("rental_deposit", {"premises_type": "commercial", "dispute_with": "landlord"}),
    ("consumer_complaint", {"purchase_purpose": "business",
                            "supplier_registered_in_sg": True}),
    ("consumer_complaint", {"purchase_purpose": "personal",
                            "supplier_registered_in_sg": False}),
    ("consumer_complaint", {"purchase_purpose": "personal",
                            "supplier_registered_in_sg": True,
                            "supplier_location": "overseas"}),
    ("rental_deposit", {"dispute_with": "unknown"}),
    ("rental_deposit", {"dispute_with": "agent", "agency_agreement_signed": None}),
])
def test_conservative_referral(client, case_type, answers):
    doc = post(client, case_type, answers).get_json()
    assert doc["guidance_status"] == "LIMITED_REFERRAL"
    assert doc["research_guidance"] is None
    assert not doc["display_evidence"]

def test_edits_change_result_identity(client):
    first = post(client, "rental_deposit", {"dispute_with": "landlord"}).get_json()
    revised = post(client, "rental_deposit", {"dispute_with": "landlord",
                                             "claim_amount_sgd": 2000}).get_json()
    assert first["result_id"] != revised["result_id"]
    assert post(client, "rental_deposit", {"dispute_with": "landlord"}).get_json()["result_id"] == first["result_id"]

def test_unconfirmed_and_invalid_rejected(client):
    assert post(client, "rental_deposit", {}, confirmed=False).status_code == 400
    assert post(client, "rental_deposit", {"not_in_schema": "x"}).status_code == 400
    assert post(client, "rental_deposit", {}, results_version="1.0").status_code == 400
    assert client.post("/api/results/preview", data="no", content_type="text/plain").status_code == 415
    assert client.post("/api/results/preview", data="x"*9000,
                       content_type="application/json").status_code == 413

def test_legacy_v1_remains_separate(client):
    response = client.post("/api/navigate", json={
        "api_version": "1.0", "case_type": "rental_deposit",
        "answers": {"dispute_with": "landlord", "premises_type": "residential",
                    "claim_amount_sgd": 1000}})
    assert response.status_code == 200
    doc = response.get_json()
    assert doc["api_version"] == "1.0"
    assert doc["rule_version"] == "mock-1"
    assert doc["status"] == "REFER_TO_OFFICIAL"
    assert doc["action_card"] is None

def test_quarantined_source_omits_affected_guidance(monkeypatch):
    from backend import results
    real = results.EvidenceRepository().snapshot()
    class Repository:
        def snapshot(self):
            return real[0], frozenset({"courts-sct-eligibility"})
    doc = assemble("rental_deposit", {"dispute_with": "landlord"}, repository=Repository())
    assert doc["guidance_status"] == "LIMITED_REFERRAL"
    assert not doc["display_evidence"]
    assert doc["research_guidance"] is None

def test_source_excerpt_hash_change_fails_closed():
    from backend import results
    from copy import deepcopy
    original, blocked = results.EvidenceRepository().snapshot()
    bundle = deepcopy(original)
    bundle["passages"]["SCT-ELIG-RESIDENTIAL"]["text"] = "unverified invented excerpt"
    class Repository:
        def snapshot(self):
            return bundle, blocked
    doc = assemble("rental_deposit", {"dispute_with": "landlord"}, repository=Repository())
    assert doc["guidance_status"] == "LIMITED_REFERRAL"
    assert doc["research_guidance"] is None
