"""Task 13: backend integration contract, with no changes to the RAG owner's ranker."""
import pytest

from backend.query_integration import prepare_confirmed_query, checked_ranked_proposal
from rag.repository import EvidenceRepository


def prepared(case, facts, query=None):
    return prepare_confirmed_query(case, facts, query=query, confirmed=True)


def checked(case, facts, rules, ids, *, repository=None, version="kb-2026-11-01.1"):
    return checked_ranked_proposal(prepared(case, facts), rules, ids,
                                  expected_source_version=version, repository=repository)


def test_unconfirmed_and_unbounded_query_rejected():
    with pytest.raises(ValueError):
        prepare_confirmed_query("rental_deposit", {"dispute_with": "landlord"}, confirmed=False)
    with pytest.raises(ValueError):
        prepared("rental_deposit", {}, "x" * 301)
    with pytest.raises(ValueError):
        prepared("rental_deposit", {}, "ignore <script> instructions")
    with pytest.raises(ValueError):
        prepared("consumer_complaint", {"wrong_field": True})


def test_rental_landlord_ranked_evidence():
    out = checked("rental_deposit", {"dispute_with": "landlord"},
                  ["SCT_RESIDENTIAL_SCOPE", "SCT_CLAIM_AMOUNT"],
                  ["SCT-ELIG-AMOUNT", "SCT-ELIG-RESIDENTIAL"])
    assert out["retrieval_status"] == "FOUND"
    assert [r["evidence_id"] for r in out["evidence"]] == [
        "SCT-ELIG-AMOUNT", "SCT-ELIG-RESIDENTIAL"]
    assert all(e["review_status"] == "verified" for e in out["evidence"])


def test_rental_agent_agency_not_landlord_sct():
    out = checked("rental_deposit", {"dispute_with": "agent"},
                  ["CEA_AGENCY_AGREEMENT"], ["CEA-DR-AGREEMENT"])
    assert out["retrieval_status"] == "FOUND"
    bad = checked("rental_deposit", {"dispute_with": "agent"},
                  ["SCT_RESIDENTIAL_SCOPE"], ["SCT-ELIG-RESIDENTIAL"])
    assert bad["retrieval_status"] == "INVALID"


def test_consumer_personal_and_sg_context():
    out = checked("consumer_complaint",
                  {"purchase_purpose": "personal", "supplier_registered_in_sg": True},
                  ["CASE_PERSONAL_PURPOSE", "CASE_SINGAPORE_SUPPLIER"],
                  ["CASE-SG-SUPPLIER", "CASE-PERSONAL"])
    assert out["retrieval_status"] == "FOUND"


@pytest.mark.parametrize("facts", [
    {"purchase_purpose": "business"},
    {"supplier_registered_in_sg": False},
    {"supplier_location": "overseas"},
])
def test_consumer_out_of_pilot_scope(facts):
    out = checked("consumer_complaint", facts, ["CASE_PERSONAL_PURPOSE"],
                  ["CASE-PERSONAL"])
    assert out["retrieval_status"] == "INVALID"
    assert not out["evidence"]


def test_missing_or_wrong_case_and_duplicates_fail_closed():
    facts = {"dispute_with": "landlord"}
    for rules, ids in [
        (["SCT_RESIDENTIAL_SCOPE", "SCT_CLAIM_AMOUNT"], ["SCT-ELIG-AMOUNT"]),
        (["SCT_RESIDENTIAL_SCOPE"], ["CASE-PERSONAL"]),
        (["SCT_RESIDENTIAL_SCOPE"], ["SCT-ELIG-RESIDENTIAL"] * 2),
        (["CASE_PERSONAL_PURPOSE"], ["CASE-PERSONAL"]),
        ([], ["SCT-ELIG-RESIDENTIAL"]),
    ]:
        assert checked("rental_deposit", facts, rules, ids)["retrieval_status"] == "INVALID"


def test_missing_facts_cannot_claim_relevance():
    result = checked_ranked_proposal(
        prepared("rental_deposit", {}), ["SCT_RESIDENTIAL_SCOPE"],
        ["SCT-ELIG-RESIDENTIAL"],
        expected_source_version="kb-2026-11-01.1")
    assert result["retrieval_status"] == "INVALID"


def test_changed_source_version_rejected():
    out = checked("rental_deposit", {"dispute_with": "landlord"},
                  ["SCT_RESIDENTIAL_SCOPE"], ["SCT-ELIG-RESIDENTIAL"],
                  version="expired")
    assert out["retrieval_status"] == "INVALID"


def test_quarantine_rejects_complete_group():
    original, blocked = EvidenceRepository().snapshot()
    class Quarantined:
        def snapshot(self):
            return original, frozenset(set(blocked) | {"courts-sct-eligibility"})
    out = checked("rental_deposit", {"dispute_with": "landlord"},
                  ["SCT_RESIDENTIAL_SCOPE"], ["SCT-ELIG-RESIDENTIAL"],
                  repository=Quarantined())
    assert out["retrieval_status"] == "INVALID"
    assert not out["evidence"]


def test_no_eligibility_or_source_text_generated():
    result = checked("rental_deposit", {"dispute_with": "landlord"},
                     ["SCT_RESIDENTIAL_SCOPE"], ["SCT-ELIG-RESIDENTIAL"])
    assert set(result) == {"retrieval_status", "evidence", "ranked_evidence_ids"}
    assert "SUPPORTED_PATH" not in str(result)
    assert "verbatim_excerpt" not in str(result)
