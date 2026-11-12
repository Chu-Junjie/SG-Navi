"""Task 19 real API/contract/RAG integration using controlled synthetic disputes."""
from copy import deepcopy
import json

import pytest

from backend.app import create_app
from backend.action_plan_service import process_action_plan
from rag.action_evidence import ActionEvidenceUnavailable
from shared.validate_action_plan import context_revision, validate_action_plan

ORIGIN = "https://chu-junjie.github.io"
RID = "task19-case-12345"


@pytest.fixture
def client():
    return create_app().test_client()


def context(case, subtype, goal, facts):
    return {
        "case_type": case, "issue_subtype": subtype, "goal": goal,
        "facts": dict(facts), "summary": "A synthetic confirmed dispute for testing.",
    }


def submit(client, ctx, request_id=RID):
    req = {
        "action_plan_version": "1.0", "request_id": request_id,
        "operation": "plan", "confirmed": True, "context": ctx,
    }
    res = client.post("/api/action-plan", json=req, headers={"Origin": ORIGIN})
    return req, res


def test_interpret_two_actual_restaurant_reproductions(client):
    for desc in (
        "I was overcharged at a restaurant in Singapore and the restaurant refuses to correct the bill.",
        "The restaurant charged me SGD 20 extra and refuses to refund it.",
    ):
        req = {
            "action_plan_version": "1.0", "request_id": RID,
            "operation": "interpret", "description": desc,
        }
        res = client.post("/api/action-plan", json=req)
        assert res.status_code == 200
        data = res.get_json()
        validate_action_plan(data, request=req)
        assert data["state"] == "CONFIRM"
        assert data["context"]["issue_subtype"] == "restaurant_overcharge"
        assert data["context"]["case_type"] == "consumer_complaint"
        assert data["question"] is None and data["plan"] is None
        assert "description" not in data
        assert desc not in str(data)


def test_one_question_and_revision_then_preparation(client):
    ctx = context("consumer_complaint", "restaurant_overcharge", "seek_refund",
                  {"merchant_location": "singapore"})
    req, response = submit(client, ctx)
    assert response.status_code == 200
    data = response.get_json()
    validate_action_plan(data, request=req)
    assert data["state"] == "ASK"
    assert data["question"]["field"] == "purchase_purpose"
    assert any(x["value"] == "unknown" for x in data["question"]["options"])
    prior_revision = data["revision"]
    ctx["facts"]["purchase_purpose"] = "personal"
    req, response = submit(client, ctx)
    data = response.get_json()
    assert data["revision"] != prior_revision
    assert data["question"] is None or data["question"]["field"] == "consumer_context"


def test_restaurant_verified_complaint_contact(client):
    ctx = context("consumer_complaint", "restaurant_overcharge", "complain", {
        "merchant_location": "singapore", "purchase_purpose": "personal",
        "consumer_context": "local_consumer", "resolution_attempted": True,
        "disputed_amount_cents": 2000,
    })
    req, res = submit(client, ctx)
    assert res.status_code == 200
    data = res.get_json()
    validate_action_plan(data, request=req)
    assert data["state"] == "READY"
    assert data["revision"] == context_revision(ctx)
    plan = data["plan"]
    assert plan["primary_action"]["kind"] == "complaint_intake"
    assert plan["primary_action"]["contact_id"] == "case-form"
    assert any(c["id"] == "case-form" and c["value"] == "https://complaints.case.org.sg/"
               for c in plan["contacts"])
    assert any(c["kind"] == "phone" for c in plan["contacts"])
    assert any(c["kind"] == "email" for c in plan["contacts"])
    assert plan["legal_basis"]
    assert all(x["evidence_ids"] for x in plan["checklist"])
    assert all(x["quote"] and x["quote_sha256"] for x in plan["evidence"])
    assert plan["draft"] is None or plan["draft"]["slots"]
    assert "guaranteed" not in data["message"].lower()


@pytest.mark.parametrize("subtype", ["goods_dispute", "services_dispute"])
def test_personal_consumer_goods_services_offer_real_contacts(client, subtype):
    ctx = context("consumer_complaint", subtype, "complain", {
        "merchant_location": "singapore", "purchase_purpose": "personal",
    })
    req, res = submit(client, ctx)
    data = res.get_json()
    validate_action_plan(data, request=req)
    assert data["state"] == "READY"
    assert {row["id"] for row in data["plan"]["contacts"]} == {"case-phone", "case-email"}
    assert data["plan"]["primary_action"]["contact_id"] is None

    ctx["facts"].update({"consumer_context": "local_consumer", "resolution_attempted": True})
    req, res = submit(client, ctx)
    data = res.get_json()
    validate_action_plan(data, request=req)
    assert data["state"] == "READY"
    assert {row["id"] for row in data["plan"]["contacts"]} == {
        "case-form", "case-phone", "case-email",
    }

    ctx["facts"]["purchase_purpose"] = "unknown"
    req, res = submit(client, ctx)
    data = res.get_json()
    validate_action_plan(data, request=req)
    assert data["state"] == "READY"
    assert data["plan"]["contacts"] == []


def test_restaurant_basic_preparation_before_full_claim_information(client):
    ctx = context("consumer_complaint", "restaurant_overcharge", "understand_options", {
        "merchant_location": "singapore", "purchase_purpose": "unknown",
    })
    req, res = submit(client, ctx)
    data = res.get_json()
    validate_action_plan(data, request=req)
    assert data["state"] == "READY"
    assert data["plan"]["primary_action"]["kind"] == "prepare"
    assert data["question"] is None


def test_rental_pass_uses_signed_terms_and_not_automatic_refund(client):
    ctx = context("rental_deposit", "pass_related_exit", "seek_refund", {
        "dispute_with": "landlord", "premises_type": "private_residential",
        "pass_event": "cancelled", "lease_ended": False,
        "break_clause_present": "unknown",
    })
    req, res = submit(client, ctx)
    data = res.get_json()
    validate_action_plan(data, request=req)
    assert data["state"] == "READY"
    assert data["plan"]["primary_action"]["kind"] == "prepare"
    assert data["plan"]["legal_basis"]
    assert any(e["kind"] == "contract_template" for e in data["plan"]["evidence"])
    assert not any(x in str(data["plan"]).lower() for x in ("automatic refund", "guaranteed refund"))


def test_rental_preparation_without_formal_claim_qualification(client):
    ctx = context("rental_deposit", "deposit_return", "seek_refund",
                  {"dispute_with": "landlord"})
    req, res = submit(client, ctx)
    d = res.get_json()
    validate_action_plan(d, request=req)
    assert d["state"] == "READY"
    assert d["plan"]["primary_action"]["kind"] == "prepare"


def test_agent_conduct_does_not_become_landlord_claim(client):
    ctx = context("rental_deposit", "agent_conduct", "complain",
                  {"dispute_with": "agent"})
    req, res = submit(client, ctx)
    d = res.get_json()
    validate_action_plan(d, request=req)
    assert d["state"] == "READY"
    assert d["plan"]["primary_action"]["contact_id"] == "cea-conduct"


@pytest.mark.parametrize("facts", [
    {"merchant_location": "outside_singapore", "purchase_purpose": "personal"},
    {"merchant_location": "singapore", "purchase_purpose": "business"},
    {"merchant_location": "singapore", "supplier_registered_in_sg": False},
])
def test_consumer_out_of_pilot_scope(client, facts):
    ctx = context("consumer_complaint", "restaurant_overcharge", "complain", facts)
    req, res = submit(client, ctx)
    d = res.get_json()
    validate_action_plan(d, request=req)
    assert d["state"] == "LIMITED" and d["plan"] is None


def test_unknown_and_null_remain_distinct_and_not_reasked(client):
    ctx = context("consumer_complaint", "restaurant_overcharge", "seek_refund", {
        "merchant_location": "singapore", "purchase_purpose": None,
    })
    req, res = submit(client, ctx)
    d = res.get_json()
    validate_action_plan(d, request=req)
    assert d["state"] == "READY" and d["context"]["facts"]["purchase_purpose"] is None


def test_version_request_id_and_invalid_confirmation(client):
    base = {"action_plan_version": "1.0", "request_id": RID,
            "operation": "interpret", "description": "A restaurant charged too much."}
    bad = [
        dict(base, action_plan_version="2.0"),
        dict(base, request_id="bad"),
        dict(base, description=""),
        dict(base, description="hello\x00"),
        dict(base, extra="extra"),
    ]
    for request in bad:
        assert client.post("/api/action-plan", json=request).status_code == 400
    ctx = context("rental_deposit", "deposit_return", "seek_refund",
                  {"dispute_with": "landlord"})
    request = {"action_plan_version": "1.0", "request_id": RID,
               "operation": "plan", "confirmed": False, "context": ctx}
    assert client.post("/api/action-plan", json=request).status_code == 400


def test_preflight_and_wrong_origin(client):
    pre = {"Origin": ORIGIN, "Access-Control-Request-Method": "POST",
           "Access-Control-Request-Headers": "content-type"}
    ok = client.options("/api/action-plan", headers=pre)
    assert ok.status_code == 204
    assert ok.headers["Access-Control-Allow-Origin"] == ORIGIN
    denied = client.options("/api/action-plan", headers={
        "Origin": "https://evil.invalid", "Access-Control-Request-Method": "POST"})
    assert denied.status_code == 403


def test_bad_content_type_and_request_limit(client):
    assert client.post("/api/action-plan", data="plain",
                       content_type="text/plain").status_code == 415
    assert client.post("/api/action-plan", data="{" ,
                       content_type="application/json").status_code == 400
    assert client.post("/api/action-plan", data=json.dumps({"description": "x"*9000}),
                       content_type="application/json").status_code == 413


def test_failed_source_selection_refuses_verified_badge(monkeypatch, client):
    import backend.action_plan_service as service
    def unavailable(*args, **kwargs):
        raise ActionEvidenceUnavailable("Source quarantine")
    monkeypatch.setattr(service, "select_action_plan", unavailable)
    ctx = context("consumer_complaint", "restaurant_overcharge", "complain", {
        "merchant_location": "singapore", "purchase_purpose": "personal",
        "consumer_context": "local_consumer", "resolution_attempted": True,
    })
    req, res = submit(client, ctx)
    data = res.get_json()
    validate_action_plan(data, request=req)
    assert data["state"] == "LIMITED"
    assert data["reason"] == "source_unverified"
    assert data["plan"] is None


def test_legacy_routing_untouched(client):
    original = client.post("/api/navigate", json={
        "api_version": "1.0", "case_type": "rental_deposit",
        "answers": {"dispute_with": "landlord", "premises_type": "residential",
                    "claim_amount_sgd": 1000}})
    assert original.status_code == 200
    assert original.get_json()["action_card"] is None


def test_unexpected_transient_failure_returns_versioned_unavailable(monkeypatch, client):
    import backend.routes.task19 as route
    def fail(_):
        raise RuntimeError("Synthetic transient failure")
    monkeypatch.setattr(route, "process_action_plan", fail)
    req = {
        "action_plan_version": "1.0", "request_id": RID,
        "operation": "interpret", "description": "A restaurant overcharged my bill.",
    }
    res = client.post("/api/action-plan", json=req)
    assert res.status_code == 503
    data = res.get_json()
    validate_action_plan(data, request=req)
    assert data["state"] == "UNAVAILABLE"
    assert data["reason"] == "service_unavailable"
    assert data["plan"] is None and data["context"] is None
    assert "Synthetic" not in str(data)


def test_fact_edit_changes_plan_revision_and_no_raw_persistence(client):
    ctx = context("consumer_complaint", "restaurant_overcharge", "complain", {
        "merchant_location": "singapore", "purchase_purpose": "personal",
        "consumer_context": "local_consumer", "resolution_attempted": True,
    })
    first_req, first = submit(client, ctx)
    first_data = first.get_json()
    assert first_data["state"] == "READY"
    changed = deepcopy(ctx)
    changed["facts"]["purchase_purpose"] = "business"
    second_req, second = submit(client, changed)
    second_data = second.get_json()
    assert second_data["state"] == "LIMITED" and second_data["plan"] is None
    assert second_data["revision"] != first_data["revision"]
    validate_action_plan(second_data, request=second_req)
