"""Task 14 display projections: current provenance and claim-level links."""
from copy import deepcopy

import pytest

from backend.app import create_app
from backend.results import assemble
from backend.evidence_projection import (
    DisplayEvidenceUnavailable, project_display_evidence)
from rag.repository import EvidenceRepository


@pytest.fixture
def rental():
    return assemble("rental_deposit", {"dispute_with": "landlord",
                                       "premises_type": "residential",
                                       "claim_amount_sgd": 2000})


def test_real_source_excerpt_and_claims(rental):
    assert rental["guidance_status"] == "GUIDANCE_ONLY"
    assert rental["research_guidance"]
    ids = {r["evidence_id"] for r in rental["display_evidence"]}
    assert ids == set(rental["research_guidance"]["citations"])
    for section in ("potential_channels", "conditions", "steps", "document_checklist"):
        for item in rental["research_guidance"][section]:
            assert item["evidence_ids"]
            assert set(item["evidence_ids"]) <= ids
    assert all(r["display_state"] == "verified_snapshot"
               and r["display_version"] == "1.0"
               and r["preview"] is None
               and r["verbatim_excerpt"] and r["summary"] and r["source_locator"]
               and r["publisher"] and r["reviewed_at"] for r in rental["display_evidence"])
    # This is the existing canonical exact quote, not an editorial rewrite.
    assert next(x for x in rental["display_evidence"]
                if x["evidence_id"] == "SCT-ELIG-RESIDENTIAL")["verbatim_excerpt"] == (
                    "residential premises not exceeding 2 years")


def test_consumer_real_case_and_sct_quotes():
    out = assemble("consumer_complaint", {
        "purchase_purpose": "personal", "supplier_registered_in_sg": True,
        "purchase_type": "goods", "supplier_location": "singapore"})
    assert out["guidance_status"] == "GUIDANCE_ONLY"
    ids = {r["evidence_id"] for r in out["display_evidence"]}
    assert "CASE-PERSONAL" in ids and "SCT-ELIG-GOODS" in ids
    assert all(r["url"].startswith("https://") for r in out["display_evidence"])


def test_wrong_case_citation_rejected(rental):
    guidance = deepcopy(rental["research_guidance"])
    guidance["citations"].append("CASE-PERSONAL")
    with pytest.raises(DisplayEvidenceUnavailable):
        project_display_evidence("rental_deposit", guidance,
                                 expected_version=rental["source_version"])


def test_missing_step_citation_rejected(rental):
    guidance = deepcopy(rental["research_guidance"])
    guidance["steps"][0]["evidence_ids"] = []
    with pytest.raises(DisplayEvidenceUnavailable):
        project_display_evidence("rental_deposit", guidance,
                                 expected_version=rental["source_version"])


def test_duplicate_ids_rejected(rental):
    guidance = deepcopy(rental["research_guidance"])
    guidance["citations"].append(guidance["citations"][0])
    with pytest.raises(DisplayEvidenceUnavailable):
        project_display_evidence("rental_deposit", guidance,
                                 expected_version=rental["source_version"])


def test_wrong_expected_version_fails(rental):
    with pytest.raises(DisplayEvidenceUnavailable):
        project_display_evidence("rental_deposit", rental["research_guidance"],
                                 expected_version="old-corpus-version")


@pytest.mark.parametrize("field,replacement", [
    ("text", "modified but not reviewed"),
    ("url", "https://example.invalid/forged"),
    ("excerpt_sha256", "0"*64),
])
def test_changed_passage_fails_closed(rental, field, replacement):
    bundle, blocked = EvidenceRepository().snapshot()
    bundle = deepcopy(bundle)
    bundle["passages"]["SCT-ELIG-RESIDENTIAL"][field] = replacement
    class ChangedRepository:
        def snapshot(self):
            return bundle, blocked
    with pytest.raises(DisplayEvidenceUnavailable):
        project_display_evidence("rental_deposit", rental["research_guidance"],
                                 expected_version=rental["source_version"],
                                 repository=ChangedRepository())


def test_quarantine_rejects_citation(rental):
    bundle, blocked = EvidenceRepository().snapshot()
    class QuarantineRepository:
        def snapshot(self):
            return bundle, frozenset(set(blocked) | {"courts-sct-eligibility"})
    with pytest.raises(DisplayEvidenceUnavailable):
        project_display_evidence("rental_deposit", rental["research_guidance"],
                                 expected_version=rental["source_version"],
                                 repository=QuarantineRepository())


def test_assemble_downgrades_if_source_revoked_between_snapshots(monkeypatch):
    import backend.results as module
    original, blocked = EvidenceRepository().snapshot()
    class ChangingRepository:
        calls = 0
        def snapshot(self):
            self.calls += 1
            return original, (blocked if self.calls == 1 else
                              frozenset(set(blocked) | {"courts-sct-eligibility"}))
    result = assemble("rental_deposit", {"dispute_with": "landlord"},
                      repository=ChangingRepository())
    assert result["guidance_status"] == "LIMITED_REFERRAL"
    assert result["research_guidance"] is None
    assert result["display_evidence"] == []


def test_api_display_and_legacy_unchanged():
    client = create_app().test_client()
    data = client.post("/api/results/preview", json={
        "results_version": "0.1", "confirmed": True,
        "case_type": "rental_deposit",
        "confirmed_answers": {"dispute_with": "landlord"}}).get_json()
    assert data["guidance_status"] == "GUIDANCE_ONLY"
    assert all(row["preview"] is None for row in data["display_evidence"])
    old = client.post("/api/navigate", json={
        "api_version": "1.0", "case_type": "rental_deposit",
        "answers": {"dispute_with": "landlord", "premises_type": "residential",
                    "claim_amount_sgd": 2000}}).get_json()
    assert old["action_card"] is None
    assert old["rule_version"] == "mock-1"
    assert all("verbatim_excerpt" not in item for item in old["evidence"])
