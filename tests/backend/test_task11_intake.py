"""Task 11 English intake HTTP/contract/regression acceptance tests.

The input descriptions are synthetic. They are never persisted or forwarded to
an external AI. No test enables legal eligibility or a supported Action Card.
"""
import json

import pytest
from backend.app import create_app
from backend.intake import confirm, interpret, _sgd_amount
from backend.routes.task11 import _validate
from shared.validate_contracts import validate

ORIGIN = "https://chu-junjie.github.io"


@pytest.fixture
def client():
    app = create_app()
    app.config["TESTING"] = True
    return app.test_client()


def intake(client, description, **extra):
    return client.post("/api/intake", json={
        "intake_version": "1.0", "description": description, **extra,
    }, headers={"Origin": ORIGIN})


def confirmed(client, case_type, answers, **extra):
    return client.post("/api/intake/confirm", json={
        "intake_version": "1.0", "confirmed": True,
        "case_type": case_type, "confirmed_answers": answers, **extra,
    }, headers={"Origin": ORIGIN})


@pytest.mark.parametrize("description,case_type,field,amount", [
    ("My landlord has not returned my S$2,000 deposit.", "rental_deposit", "dispute_with", 2000),
    ("My landlord refuses to return my SGD 123.50 tenancy deposit.", "rental_deposit", "dispute_with", 123.5),
    ("I bought a faulty phone for S$200 and the seller refuses a refund.", "consumer_complaint", "purchase_type", 200),
    ("I purchased a defective product for SGD 55.90.", "consumer_complaint", "purchase_type", 55.9),
])
def test_synthetic_classification_extracts_only_confirmable_facts(client, description, case_type, field, amount):
    res = intake(client, description)
    assert res.status_code == 200
    data = res.get_json()
    _validate(data, "response")
    assert data["intake_status"] == "suggested"
    assert data["suggested_case_type"] == case_type
    assert data["candidate_facts"]["claim_amount_sgd"] == amount
    assert field in data["candidate_facts"]
    assert data["needs_confirmation"] is True
    assert data["clarification_questions"] == []
    assert "description" not in data and "action_card" not in data
    assert res.headers["Access-Control-Allow-Origin"] == ORIGIN


def test_no_unsupported_inferences_for_rental_or_consumer(client):
    rental = intake(client, "My landlord did not return S$2,000 of my deposit.").get_json()
    assert rental["candidate_facts"] == {"claim_amount_sgd": 2000, "dispute_with": "landlord"}
    consumer = intake(client, "I bought a faulty phone for S$300 and want a refund.").get_json()
    assert consumer["candidate_facts"] == {"claim_amount_sgd": 300, "purchase_type": "goods"}
    for key in ("respondent_in_singapore", "tenancy_duration_months", "relevant_event_date",
                "supplier_registered_in_sg", "purchase_purpose", "documents_available"):
        assert key not in rental["candidate_facts"]
        assert key not in consumer["candidate_facts"]


@pytest.mark.parametrize("description,status", [
    ("I want to complain about my landlord and a faulty product.", "ambiguous"),
    ("I lost my work permit and need employment advice.", "out_of_scope"),
    ("My landlord says it is about a criminal charge.", "out_of_scope"),
    ("Please help me.", "cannot_determine"),
    ("I signed a lease for an apartment.", "cannot_determine"),
    ("I bought a phone yesterday.", "cannot_determine"),
    ("I want a refund.", "cannot_determine"),
    ("The weather is hot today.", "cannot_determine"),
])
def test_ambiguous_out_of_scope_or_unrelated_never_forced(client, description, status):
    data = intake(client, description).get_json()
    assert data["intake_status"] == status
    assert data["suggested_case_type"] is None
    assert data["candidate_facts"] == {}
    assert data["needs_confirmation"]


def test_landlord_deposit_refund_is_not_forced_into_consumer_case(client):
    data = intake(client, "My landlord will not refund my S$500 deposit.").get_json()
    assert data["intake_status"] == "suggested"
    assert data["suggested_case_type"] == "rental_deposit"


def test_bad_precision_or_suffix_amount_is_not_assumed(client):
    for value in ("SGD 50.123", "S$2k", "S$1,00", "S$50.999"):
        data = intake(client, "My landlord kept a deposit of " + value).get_json()
        assert "claim_amount_sgd" not in data["candidate_facts"]


def test_explicit_landlord_agent_and_premises_conflicts_are_not_guessed(client):
    data = intake(client, "My landlord and property agent kept my S$500 rental deposit in my flat.").get_json()
    assert data["suggested_case_type"] == "rental_deposit"
    assert data["candidate_facts"] == {"claim_amount_sgd": 500, "premises_type": "residential"}
    data = intake(client, "My property agent kept my SGD 300 rental deposit.").get_json()
    assert data["candidate_facts"]["dispute_with"] == "agent"


def test_multiple_amounts_and_unsupported_currency_not_treated_as_claim(client):
    for text in (
        "I bought a faulty phone for S$200 and paid S$50 for repairs.",
        "My landlord kept a $900 deposit.",
        "My landlord kept a US$800 deposit.",
    ):
        data = intake(client, text).get_json()
        assert data["intake_status"] == "suggested"
        assert "claim_amount_sgd" not in data["candidate_facts"]
    assert _sgd_amount("S$1,000,000,000") == 1000000000


@pytest.mark.parametrize("description", [
    "", "  \n ", "x" * 1201, 123, ["faulty"], None,
    "My landlord refused.\x00", "我的房东没退押金",
])
def test_invalid_text_rejected_with_no_raw_echo(client, description):
    res = intake(client, description)
    assert res.status_code == 400
    data = res.get_json()
    assert data["intake_status"] == "error"
    assert data["candidate_facts"] == {}
    assert data["suggested_case_type"] is None
    assert description not in data["limitations"]


@pytest.mark.parametrize("extra", [
    {"api_version": "1.0"},
    {"intake_version": "2.0"},
    {"description": "My landlord kept my deposit.", "unexpected": True},
])
def test_request_schema_rejects_wrong_version_and_extra_fields(client, extra):
    res = client.post("/api/intake", json={
        "intake_version": "1.0", "description": "My landlord kept my deposit.", **extra,
    })
    assert res.status_code == 400
    _validate(res.get_json(), "response")


def test_confirm_requires_explicit_confirmation_and_valid_schema(client):
    for payload in (
        {"intake_version": "1.0", "confirmed": False,
         "case_type": "rental_deposit", "confirmed_answers": {}},
        {"intake_version": "1.0", "confirmed": True,
         "case_type": "rental_deposit", "confirmed_answers": {"bad_field": 99}},
        {"intake_version": "1.0", "confirmed": True,
         "case_type": "wrong", "confirmed_answers": {}},
        {"intake_version": "1.0", "confirmed": True,
         "case_type": "consumer_complaint", "confirmed_answers": {"claim_amount_sgd": -1}},
    ):
        res = client.post("/api/intake/confirm", json=payload)
        assert res.status_code == 400
        assert res.get_json()["intake_status"] == "error"
        _validate(res.get_json(), "response")


def test_confirm_minimal_relevant_missing_questions_and_repeat_is_idempotent(client):
    facts = {"dispute_with": "landlord", "claim_amount_sgd": 2000}
    first = confirmed(client, "rental_deposit", facts).get_json()
    second = confirmed(client, "rental_deposit", dict(reversed(list(facts.items())))).get_json()
    assert first == second
    assert first["intake_status"] == "confirmed"
    assert first["needs_confirmation"] is False
    assert first["candidate_facts"] == facts
    assert [x["id"] for x in first["clarification_questions"]] == ["premises_type"]
    assert first["unresolved_fields"] == []
    assert len(first["revision"]) == 20


def test_unknown_and_false_and_null_distinct_without_reasking(client):
    answers = {"purchase_type": "goods", "purchase_purpose": "unknown",
               "supplier_registered_in_sg": False, "claim_amount_sgd": None}
    d = confirmed(client, "consumer_complaint", answers).get_json()
    assert d["intake_status"] == "confirmed"
    assert d["clarification_questions"] == []
    assert d["unresolved_fields"] == ["claim_amount_sgd", "purchase_purpose"]
    assert d["candidate_facts"]["supplier_registered_in_sg"] is False
    assert d["candidate_facts"]["claim_amount_sgd"] is None
    changed = dict(answers, supplier_registered_in_sg="unknown")
    next_d = confirmed(client, "consumer_complaint", changed).get_json()
    assert next_d["revision"] != d["revision"]
    assert next_d["unresolved_fields"] == [
        "claim_amount_sgd", "purchase_purpose", "supplier_registered_in_sg"
    ]


def test_consumer_confirmation_only_asks_case_specific_missing_fields(client):
    data = confirmed(client, "consumer_complaint", {"purchase_type": "goods"}).get_json()
    assert [x["id"] for x in data["clarification_questions"]] == [
        "purchase_purpose", "supplier_registered_in_sg", "claim_amount_sgd",
    ]


def test_revision_changes_when_user_corrects_amount(client):
    before = confirmed(client, "rental_deposit", {"claim_amount_sgd": 123}).get_json()
    after = confirmed(client, "rental_deposit", {"claim_amount_sgd": 456}).get_json()
    assert before["revision"] != after["revision"]
    assert before["clarification_questions"] == after["clarification_questions"]


@pytest.mark.parametrize("path", ["/api/intake", "/api/intake/confirm"])
def test_pages_cors_preflight_allowed_and_other_origin_rejected(client, path):
    good = client.options(path, headers={
        "Origin": ORIGIN, "Access-Control-Request-Method": "POST",
        "Access-Control-Request-Headers": "content-type",
    })
    assert good.status_code == 204
    assert good.headers["Access-Control-Allow-Origin"] == ORIGIN
    assert "POST" in good.headers["Access-Control-Allow-Methods"]
    bad = client.options(path, headers={
        "Origin": "https://evil.example.org", "Access-Control-Request-Method": "POST",
    })
    assert bad.status_code == 403
    assert "Access-Control-Allow-Origin" not in bad.headers


@pytest.mark.parametrize("path", ["/api/intake", "/api/intake/confirm"])
def test_bad_json_content_type_and_body_size_fail_safely(client, path):
    wrong = client.post(path, data="bad", content_type="text/plain")
    assert wrong.status_code == 415
    malformed = client.post(path, data="{", content_type="application/json")
    assert malformed.status_code == 400
    large = client.post(path, data=json.dumps({"description": "x" * 9000}),
                        content_type="application/json")
    assert large.status_code == 413
    for res in (wrong, malformed, large):
        _validate(res.get_json(), "response")


def test_existing_structured_api_unchanged(client):
    request = {
        "api_version": "1.0", "case_type": "rental_deposit",
        "answers": {"claim_amount_sgd": 123, "dispute_with": "landlord"}
    }
    response = client.post("/api/navigate", json=request)
    assert response.status_code == 200
    validate(response.get_json(), "navigate_response")
    assert response.get_json()["status"] == "NEED_CLARIFICATION"
    assert response.get_json()["action_card"] is None
