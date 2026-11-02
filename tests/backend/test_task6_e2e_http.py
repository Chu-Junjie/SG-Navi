"""Task 6 E2E-01..08: real loopback HTTP through integration app/API/RAG.

These are *transport-level* checks, not claims of executed browser JavaScript.
The application deliberately has no enabled eligibility rules or supported
legal Action Cards; E2E-01/02 verify safe contextual referrals instead.
"""
import json
import threading
from unittest.mock import patch
from urllib.request import Request, urlopen
from urllib.error import HTTPError

import pytest
from werkzeug.serving import make_server

from integration.app import create_app
from shared.validate_contracts import validate


RENTAL = {"dispute_with": "landlord", "premises_type": "residential",
          "claim_amount_sgd": 123}
CONSUMER = {"purchase_type": "goods", "purchase_purpose": "personal",
            "supplier_registered_in_sg": True, "claim_amount_sgd": 123}


@pytest.fixture(scope="module")
def live_server():
    server = make_server("127.0.0.1", 0, create_app(), threaded=True)
    worker = threading.Thread(target=server.serve_forever, daemon=True)
    worker.start()
    try:
        yield "http://127.0.0.1:" + str(server.server_port)
    finally:
        server.shutdown()
        server.server_close()
        worker.join(timeout=5)


def send(base, case_type, answers, **more):
    data = json.dumps({"api_version": "1.0", "case_type": case_type,
                       "answers": answers, **more}).encode("utf-8")
    req = Request(base + "/api/navigate", data=data, method="POST",
                  headers={"Content-Type": "application/json"})
    try:
        with urlopen(req, timeout=8) as response:
            status, body = response.status, response.read()
    except HTTPError as failure:
        status, body = failure.code, failure.read()
    result = json.loads(body)
    validate(result, "navigate_response")
    return status, result


def assert_safe_referral(status, data, *, sources):
    assert status == 200 and data["status"] == "REFER_TO_OFFICIAL"
    assert data["action_card"] is None and data["warnings"]
    assert len(data["evidence"]) > 0 if sources else data["evidence"] == []
    assert all(s["review_status"] == "verified" and
               s["source_version"] == data["source_version"] for s in data["evidence"])


def test_e2e_01_rental_http_questions_real_sources_and_edit(live_server):
    with urlopen(live_server + "/task5-flow.html", timeout=8) as page:
        assert page.status == 200 and b"task5-flow.js" in page.read()
    _, blank = send(live_server, "rental_deposit", {})
    assert blank["status"] == "NEED_CLARIFICATION"
    assert "claim_amount_sgd" in {q["id"] for q in blank["questions"]}
    status, complete = send(live_server, "rental_deposit", RENTAL)
    assert_safe_referral(status, complete, sources=True)
    assert all(s["url"].startswith("https://") for s in complete["evidence"])
    _, edited = send(live_server, "rental_deposit", dict(RENTAL, claim_amount_sgd=456))
    assert edited["status"] == "REFER_TO_OFFICIAL"
    # LIMIT: a confirmed supported legal Action Card is not implemented by design.


def test_e2e_02_consumer_http_questions_real_sources_and_edit(live_server):
    _, blank = send(live_server, "consumer_complaint", {})
    assert blank["status"] == "NEED_CLARIFICATION"
    assert "purchase_purpose" in {q["id"] for q in blank["questions"]}
    status, complete = send(live_server, "consumer_complaint", CONSUMER)
    assert_safe_referral(status, complete, sources=True)
    _, edited = send(live_server, "consumer_complaint", dict(CONSUMER, claim_amount_sgd=456))
    assert edited["status"] == "REFER_TO_OFFICIAL"
    # LIMIT: no actual legal eligibility decision or supported Action Card.


def test_e2e_03_missing_amount_or_unknown_never_guesses(live_server):
    for amount in (None, "unknown"):
        _, data = send(live_server, "rental_deposit", dict(RENTAL, claim_amount_sgd=amount))
        assert data["status"] == "NEED_CLARIFICATION"
        assert "claim_amount_sgd" in {q["id"] for q in data["questions"]}
        assert not data["evidence"] and data["action_card"] is None


def test_e2e_04_unknown_landlord_or_agent_is_clarified(live_server):
    for dispute in (None, "unknown"):
        _, data = send(live_server, "rental_deposit", dict(RENTAL, dispute_with=dispute))
        assert data["status"] == "NEED_CLARIFICATION"
        assert "dispute_with" in {q["id"] for q in data["questions"]}
        assert data["action_card"] is None and data["evidence"] == []


def test_e2e_05_business_purchase_fails_closed(live_server):
    code, data = send(live_server, "consumer_complaint",
                      dict(CONSUMER, purchase_purpose="business"))
    assert_safe_referral(code, data, sources=False)
    assert "business" in " ".join(data["warnings"]).lower()


def test_e2e_06_supplier_outside_singapore_pilot(live_server):
    code, data = send(live_server, "consumer_complaint",
                      dict(CONSUMER, supplier_registered_in_sg=False))
    assert_safe_referral(code, data, sources=False)
    assert "supplier" in " ".join(data["warnings"]).lower()


def test_e2e_07_invalid_or_mismatched_evidence_never_exposed(live_server):
    for bad in (("INVALID", []), ("NO_RESULTS", [])):
        with patch("backend.rules.engine.retrieve_checked", return_value=bad):
            code, data = send(live_server, "rental_deposit", RENTAL)
        assert_safe_referral(code, data, sources=False)


def test_e2e_08_backend_rag_failure_yields_safe_error(live_server):
    with patch("backend.rag_bridge.retrieve_evidence", side_effect=RuntimeError("synthetic outage")):
        code, data = send(live_server, "consumer_complaint", CONSUMER)
    assert code == 200 and data["status"] == "ERROR"
    assert not data["evidence"] and data["action_card"] is None and data["warnings"]
    # A following successful request can be made without a process restart.
    code, recovered = send(live_server, "consumer_complaint", CONSUMER)
    assert_safe_referral(code, recovered, sources=True)
