"""Exercise actual reviewed profiles and fail-closed source state."""

import hashlib
import json
from datetime import datetime, timedelta

import pytest

from rag.action_evidence import (
    DIRECTORY, ActionEvidenceUnavailable, load_action_package, select_action_plan,
)
from rag.repository import EvidenceRepository


RESTAURANT = {
    "case_type": "consumer_complaint", "issue_subtype": "restaurant_overcharge",
    "goal": "complain", "summary": "You disputed a Singapore restaurant bill.",
    "facts": {"merchant_location": "singapore", "purchase_purpose": "personal",
              "consumer_context": "local_consumer", "resolution_attempted": True},
}
RENTAL = {
    "case_type": "rental_deposit", "issue_subtype": "pass_related_exit",
    "goal": "seek_refund", "summary": "You reported a work-pass cancellation and a deposit dispute.",
    "facts": {"dispute_with": "landlord", "premises_type": "private_residential",
              "pass_event": "cancelled", "break_clause_present": "unknown"},
}


@pytest.fixture
def review(tmp_path):
    package, _, _, _ = load_action_package()
    repo = EvidenceRepository(state_file=tmp_path / "state.json")
    assert repo._pgstore is None
    return package, repo, datetime.fromisoformat(package["reviewed_at"])


def select(context, review, **overrides):
    package, repo, now = review
    return select_action_plan(context, **{
        "expected_version": package["version"], "repository": repo, "now": now, **overrides,
    })


def test_restaurant_has_direct_complaint_contact_and_precise_law(review):
    plan = select(RESTAURANT, review)
    assert plan["primary_action"]["contact_id"] == "case-form"
    assert {row["value"] for row in plan["contacts"]} == {
        "https://complaints.case.org.sg/", "+6562775100", "admin@case.org.sg",
    }
    assert plan["legal_basis"] == [{"claim_id": "legal-context", "evidence_id": "CPFTA-4A"}]
    assert plan["draft"]["slots"]


def test_pass_case_checks_signed_contract_and_keeps_statute_separate(review):
    plan = select(RENTAL, review)
    assert plan["primary_action"]["kind"] == "prepare"
    records = {r["id"]: r for r in plan["evidence"]}
    assert records["CEA-TEMPLATE-BREAK"]["kind"] == "contract_template"
    assert records["SCTA-SCHEDULE-1C"]["kind"] == "statute"
    assert plan["legal_basis"] == [{"claim_id": "jurisdiction", "evidence_id": "SCTA-SCHEDULE-1C"}]
    assert {r["id"] for r in plan["contacts"]} == {"sct-criteria"}


@pytest.mark.parametrize("change", [
    {"purchase_purpose": "unknown"}, {"consumer_context": "visitor"},
    {"resolution_attempted": False}, {"resolution_attempted": "unknown"},
])
def test_unknown_or_different_route_gets_preparation_without_case_intake(review, change):
    context = {**RESTAURANT, "facts": {**RESTAURANT["facts"], **change}}
    plan = select(context, review)
    assert plan["primary_action"]["kind"] == "prepare"
    # Personal local buyers may contact CASE for guidance, but only the
    # fully reviewed post-dispute intake route offers its complaint form.
    expected = set() if change.get("purchase_purpose") == "unknown" else {"case-phone", "case-email"}
    assert {row["id"] for row in plan["contacts"]} == expected


@pytest.mark.parametrize("subtype", [
    "restaurant_overcharge", "duplicate_charge", "unclear_charge",
    "goods_dispute", "services_dispute",
])
def test_personal_local_consumer_has_verified_case_assistance(review, subtype):
    context = {**RESTAURANT, "issue_subtype": subtype, "facts": {
        "merchant_location": "singapore", "purchase_purpose": "personal",
        "resolution_attempted": False,
    }}
    plan = select(context, review)
    assert plan["primary_action"]["kind"] == "prepare"
    assert {row["id"] for row in plan["contacts"]} == {"case-phone", "case-email"}
    assert {"CASE-PHONE", "CASE-EMAIL"} <= {row["id"] for row in plan["evidence"]}


@pytest.mark.parametrize("subtype", ["goods_dispute", "services_dispute"])
def test_goods_services_have_case_intake_after_confirmed_dispute(review, subtype):
    context = {**RESTAURANT, "issue_subtype": subtype}
    plan = select(context, review)
    assert {row["id"] for row in plan["contacts"]} == {"case-form", "case-phone", "case-email"}
    assert plan["primary_action"]["kind"] == "prepare"
    assert plan["primary_action"]["contact_id"] is None
    assert "CASE-PORTAL" in {row["id"] for row in plan["evidence"]}


def test_duplicate_and_hdb_keep_relevant_records(review):
    duplicate = {**RESTAURANT, "issue_subtype": "duplicate_charge",
                 "facts": {**RESTAURANT["facts"], "resolution_attempted": False}}
    assert select(duplicate, review)["primary_action"]["label"] == "Check both payment entries"
    hdb = {**RENTAL, "facts": {**RENTAL["facts"], "premises_type": "hdb"}}
    assert all(row["kind"] != "contract_template" for row in select(hdb, review)["evidence"])


def test_agent_conduct_and_signed_agreement_have_distinct_destinations(review):
    conduct = {**RENTAL, "issue_subtype": "agent_conduct", "goal": "complain",
               "facts": {"dispute_with": "agent"}}
    assert select(conduct, review)["primary_action"]["contact_id"] == "cea-conduct"
    agreement = {**conduct, "issue_subtype": "agency_agreement"}
    assert select(agreement, review)["primary_action"]["kind"] == "prepare"
    agreement["facts"]["agency_agreement_signed"] = True
    assert select(agreement, review)["primary_action"]["contact_id"] == "cea-agreement"
    conduct["facts"]["dispute_with"] = "landlord"
    assert select(conduct, review) is None


def test_source_version_age_and_quarantine_fail_closed(review):
    with pytest.raises(ActionEvidenceUnavailable, match="version"):
        select(RESTAURANT, review, expected_version="wrong")
    with pytest.raises(ActionEvidenceUnavailable, match="stale"):
        select(RESTAURANT, review, now=review[2] + timedelta(days=31))
    review[1].quarantine_source("case-complaint", actor="Synthetic test", reason="Test source boundary")
    with pytest.raises(ActionEvidenceUnavailable, match="required source"):
        select(RESTAURANT, review)


def test_missing_state_change_rejects_inflight_result(review):
    bundle, _ = review[1].snapshot()

    class ChangedDuringRead:
        calls = 0

        def snapshot(self):
            self.calls += 1
            return bundle, frozenset() if self.calls == 1 else frozenset({"case-complaint"})

    with pytest.raises(ActionEvidenceUnavailable, match="changed during selection"):
        select(RESTAURANT, review, repository=ChangedDuringRead())


def write_package(directory, package):
    body = (json.dumps(package, indent=2) + "\n").encode("utf-8")
    (directory / "package.json").write_bytes(body)
    (directory / "package.sha256").write_text(hashlib.sha256(body).hexdigest(), encoding="ascii")


def test_changed_contact_cannot_borrow_valid_source(review, tmp_path):
    package, _, _ = review
    package["contacts"][0]["value"] = "https://www.case.org.sg/contact-us/"
    write_package(tmp_path, package)
    with pytest.raises(ActionEvidenceUnavailable, match="lacks source authorization"):
        select(RESTAURANT, review, directory=tmp_path)


def test_unrelated_statute_does_not_support_a_restaurant_claim(review, tmp_path):
    package, _, _ = review
    profile = package["profiles"][0]["plan"]
    profile["details"][0]["items"][0]["evidence_ids"] = ["SCTA-SCHEDULE-1C"]
    profile["legal_basis"][0]["evidence_id"] = "SCTA-SCHEDULE-1C"
    write_package(tmp_path, package)
    with pytest.raises(ActionEvidenceUnavailable, match="another case type"):
        select(RESTAURANT, review, directory=tmp_path)


def test_package_accepts_windows_checkout_and_rejects_changed_bytes(review, tmp_path):
    original = (DIRECTORY / "package.json").read_bytes()
    (tmp_path / "package.json").write_bytes(original.replace(b"\n", b"\r\n"))
    (tmp_path / "package.sha256").write_bytes((DIRECTORY / "package.sha256").read_bytes())
    assert select(RESTAURANT, review, directory=tmp_path)["primary_action"]["contact_id"] == "case-form"
    (tmp_path / "package.json").write_bytes(original + b" ")
    with pytest.raises(ActionEvidenceUnavailable, match="digest"):
        select(RESTAURANT, review, directory=tmp_path)
