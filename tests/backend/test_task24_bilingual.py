"""Task 24 proposed bilingual projection: real Task17 profiles, strict v1 invariance."""
from copy import deepcopy
import json

import pytest

from backend.action_plan_service import envelope, process_action_plan
from backend.task24_bilingual import CATALOG, preview_zh_hans
from rag.action_evidence import _materialize, load_action_package
from shared.validate_action_plan import validate_action_plan

SUBTYPES = {
    "restaurant_overcharge": "You reported a restaurant billing overcharge.",
    "duplicate_charge": "You reported being charged twice for a transaction.",
    "unclear_charge": "You reported a disputed restaurant bill or charge.",
    "goods_dispute": "You reported a dispute about purchased goods.",
    "services_dispute": "You reported a dispute about a purchased service.",
    "deposit_return": "You reported a dispute about returning a rental deposit.",
    "deposit_deduction": "You reported disputed deductions from a rental deposit.",
    "early_exit": "You reported a rental dispute involving an early tenancy exit.",
    "pass_related_exit": "You reported a rental issue involving a work-pass event.",
    "agent_conduct": "You reported a concern about an estate agent's conduct.",
    "agency_agreement": "You reported an estate agency agreement dispute.",
    "unspecified": "You reported a dispute that needs a little more context.",
}
GOALS = {
    "complain": "make a complaint.",
    "seek_refund": "seek repayment.",
    "prepare_claim": "explore preparing a formal claim.",
    "contact_provider": "contact the relevant organisation.",
    "understand_options": "understand your available options.",
}


def context(case, sub, goal, facts=None):
    return {
        "case_type": case, "issue_subtype": sub, "goal": goal,
        "facts": dict(facts or {}),
        "summary": SUBTYPES[sub] + " You want to " + GOALS[goal],
    }


def ready(profile, records, contacts, version):
    selected_subtype = profile["subtypes"][0]
    selected_goal = profile["goals"][0]
    ctx = context(profile["case_type"], selected_subtype, selected_goal, profile["requires"])
    plan = _materialize(profile, records, contacts, version)
    return envelope("task24-case-12345", "READY", "verified_action",
                    "A reviewed preparation or assistance step is available. "
                    "This does not establish eligibility or guarantee an outcome.",
                    context=ctx, plan=plan)


def test_all_real_task17_profiles_proposed_without_missing_fields():
    package, _, records, contacts = load_action_package()
    assert len(package["profiles"]) == 13
    for profile in package["profiles"]:
        response = ready(profile, records, contacts, package["version"])
        original = deepcopy(response)
        view = preview_zh_hans(response)
        assert view["translation_status"] == "pending_review", (profile["id"], view["missing_paths"])
        assert view["display"] is not None
        assert view["missing_paths"] == []
        assert view["canonical"] == original
        assert response == original
        validate_action_plan(view["canonical"], "response")
        zh = view["display"]["plan"]
        en = response["plan"]
        assert zh["headline"] != en["headline"]
        assert [(x["id"], x["evidence_ids"]) for x in zh["checklist"]] == [
            (x["id"], x["evidence_ids"]) for x in en["checklist"]]
        assert [(x["kind"], x["value"], x["evidence_ids"]) for x in zh["contacts"]] == [
            (x["kind"], x["value"], x["evidence_ids"]) for x in en["contacts"]]
        assert en["evidence"] == view["canonical"]["plan"]["evidence"]
        assert en["legal_basis"] == view["canonical"]["plan"]["legal_basis"]
        assert en["source_version"] == view["canonical"]["plan"]["source_version"]
        if zh["draft"] is not None:
            assert [x["id"] for x in zh["draft"]["slots"]] == [
                x["id"] for x in en["draft"]["slots"]]


@pytest.mark.parametrize("case,sub,goal,facts,field", [
    ("consumer_complaint", "restaurant_overcharge", "seek_refund",
     {"merchant_location": "singapore"}, "purchase_purpose"),
    ("consumer_complaint", "restaurant_overcharge", "complain",
     {"merchant_location": "singapore", "purchase_purpose": "personal",
      "resolution_attempted": True}, "consumer_context"),
    ("rental_deposit", "deposit_return", "seek_refund", {}, "dispute_with"),
    ("rental_deposit", "pass_related_exit", "seek_refund",
     {"dispute_with": "landlord"}, "lease_ended"),
    ("rental_deposit", "pass_related_exit", "seek_refund",
     {"dispute_with": "landlord", "lease_ended": False}, "break_clause_present"),
    ("rental_deposit", "agency_agreement", "understand_options",
     {"dispute_with": "agent"}, "agency_agreement_signed"),
])
def test_live_service_ask_question_value_invariant(case, sub, goal, facts, field):
    req = {
        "action_plan_version": "1.0", "request_id": "task24-ask-12345",
        "operation": "plan", "confirmed": True,
        "context": context(case, sub, goal, facts),
    }
    en = process_action_plan(req)
    assert en["state"] == "ASK", (field, en["state"])
    assert en["question"]["field"] == field
    view = preview_zh_hans(en)
    assert view["translation_status"] == "pending_review", view["missing_paths"]
    zhq = view["display"]["question"]
    assert zhq["id"] == en["question"]["id"]
    assert zhq["field"] == en["question"]["field"]
    assert [x["value"] for x in zhq["options"]] == [x["value"] for x in en["question"]["options"]]
    assert all(x["label"] for x in zhq["options"])
    assert en["revision"] == view["canonical"]["revision"]


@pytest.mark.parametrize("state,reason,message", [
    ("CONFIRM", "awaiting_confirmation",
     "Please confirm this understanding or correct the details before proceeding."),
    ("LIMITED", "outside_scope",
     "This situation is outside the currently supported assistance scope. Check the relevant institution's official guidance."),
    ("LIMITED", "ambiguous_scope",
     "More than one unrelated dispute is described. Select one issue to continue."),
    ("LIMITED", "insufficient_facts",
     "Describe the disputed payment, purchase or rental deposit and what happened."),
    ("LIMITED", "source_unverified",
     "The current evidence or contact could not be verified. No source-backed action can be displayed; review the applicable official guidance."),
    ("UNAVAILABLE", "service_unavailable",
     "Service is temporarily unavailable. Please retry."),
])
def test_all_service_state_messages(state, reason, message):
    ctx = context("consumer_complaint", "restaurant_overcharge", "understand_options")
    r = envelope("task24-state-12345", state, reason, message,
                 context=ctx if state == "CONFIRM" else None)
    view = preview_zh_hans(r)
    assert view["translation_status"] == "pending_review", view["missing_paths"]
    assert view["display"]["message"] != r["message"]
    assert view["is_official_translation"] is False
    assert view["reviewed_by"] is None


def test_unreviewed_dynamic_summary_never_guessed():
    ctx = context("rental_deposit", "deposit_return", "seek_refund")
    ctx["summary"] = "The landlord definitely owes a refund."
    result = envelope("task24-test-12345", "CONFIRM", "awaiting_confirmation",
                      "Please confirm this understanding or correct the details before proceeding.",
                      context=ctx)
    view = preview_zh_hans(result)
    assert view["translation_status"] == "missing_translation"
    assert view["display"] is None
    assert "context.summary.unreviewed_dynamic" in view["missing_paths"]
    assert view["fallback_notice"]


def test_missing_translation_blocks_all_chinese_display(tmp_path):
    cat = json.loads(CATALOG.read_text(encoding="utf-8"))
    del cat["entries"]["Not sure"]
    target = tmp_path / "unreviewed.json"
    target.write_text(json.dumps(cat, ensure_ascii=False), encoding="utf-8")
    req = {
        "action_plan_version": "1.0", "request_id": "task24-ask-56789",
        "operation": "plan", "confirmed": True,
        "context": context("consumer_complaint", "restaurant_overcharge", "seek_refund",
                           {"merchant_location": "singapore"}),
    }
    r = process_action_plan(req)
    view = preview_zh_hans(r, catalog_path=target)
    assert view["display"] is None
    assert view["translation_status"] == "missing_translation"
    assert view["fallback_notice"]
    assert view["canonical"] == r


def test_missing_source_does_not_create_verified_chinese_legal_text():
    r = envelope(
        "task24-test-56789", "LIMITED", "source_unverified",
        "The current evidence or contact could not be verified. "
        "No source-backed action can be displayed; review the applicable official guidance."
    )
    view = preview_zh_hans(r)
    assert view["display"]["plan"] is None
    assert view["canonical"]["plan"] is None
    assert "中文说明" in view["disclaimer"]
    assert not view["is_official_translation"]


def test_invalid_or_unapproved_catalog_rejected(tmp_path):
    cat = json.loads(CATALOG.read_text(encoding="utf-8"))
    cat["review_status"] = "verified"  # Cannot pretend approval from a file edit.
    dest = tmp_path / "forged.json"
    dest.write_text(json.dumps(cat, ensure_ascii=False), encoding="utf-8")
    r = envelope("task24-test-56790", "UNAVAILABLE", "service_unavailable",
                 "Service is temporarily unavailable. Please retry.")
    with pytest.raises(ValueError):
        preview_zh_hans(r, catalog_path=dest)


def test_chinese_free_text_not_implicitly_supported():
    from backend.scenario_understanding import interpret_scenario
    with pytest.raises(ValueError):
        interpret_scenario("我的房东没有退还押金，我想投诉。")


def test_preview_route_off_by_default_and_english_api_still_works():
    from backend.app import create_app
    client = create_app().test_client()
    req = {
        "action_plan_version": "1.0",
        "request_id": "task24-preview-12345",
        "operation": "interpret",
        "description": "The restaurant charged me SGD 20 extra and refuses to refund it.",
    }
    assert client.post("/api/action-plan/zh-hans-preview", json=req).status_code == 404
    original = client.post("/api/action-plan", json=req)
    assert original.status_code == 200
    data = original.get_json()
    assert data["state"] == "CONFIRM"
    assert "display" not in data and "overlay_version" not in data


def test_opt_in_preview_returns_proposed_sidecar_without_touching_canonical():
    from backend.app import create_app
    app = create_app()
    app.config["TASK24_ENABLE_UNREVIEWED_PREVIEW"] = True
    client = app.test_client()
    req = {
        "action_plan_version": "1.0",
        "request_id": "task24-preview-54321",
        "operation": "interpret",
        "description": "The restaurant charged me SGD 20 extra and refuses to refund it.",
    }
    response = client.post("/api/action-plan/zh-hans-preview", json=req)
    assert response.status_code == 200
    preview = response.get_json()
    validate_action_plan(preview["canonical"], "response", request=req)
    assert preview["translation_status"] == "pending_review"
    assert preview["display"]["context_summary"]
    assert preview["canonical"]["context"]["issue_subtype"] == "restaurant_overcharge"
    assert not preview["is_official_translation"]
    assert preview["reviewed_by"] is None
    assert client.post("/api/action-plan/zh-hans-preview", data="test",
                       content_type="text/plain").status_code == 415
    assert client.post("/api/action-plan/zh-hans-preview", json={
        **req, "action_plan_version": "2.0"}).status_code == 400
