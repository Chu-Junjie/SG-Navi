"""Structural and cross-reference checks for the action plan contract."""

import hashlib
import json
import re
from datetime import datetime
from functools import lru_cache
from pathlib import Path
from urllib.parse import urlsplit

from jsonschema import Draft202012Validator, FormatChecker, ValidationError

SCHEMA = Path(__file__).with_name("action_plan_contract.json")
OFFICIAL_HOSTS = frozenset({
    "www.case.org.sg", "complaints.case.org.sg", "www.ccs.gov.sg",
    "www.judiciary.gov.sg", "cjts.judiciary.gov.sg", "www.cea.gov.sg",
    "www.hdb.gov.sg", "www.mom.gov.sg", "sso.agc.gov.sg", "www.elitigation.sg",
})
ACTION_PURPOSE = {
    "consult": {"consumer_assistance", "agency_agreement_help", "procedure_information"},
    "complaint_intake": {"complaint_intake", "agency_conduct"},
    "check_criteria": {"procedure_information"},
}


@lru_cache(maxsize=1)
def _schema():
    schema = json.loads(SCHEMA.read_text(encoding="utf-8"))
    Draft202012Validator.check_schema(schema)
    return schema


def _validator(name):
    return Draft202012Validator(
        {"$defs": _schema()["$defs"], "$ref": "#/$defs/" + name},
        format_checker=FormatChecker(),
    )


def _require(ok, message):
    if not ok:
        raise ValidationError(message)


def _key(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False)


def _unique(items, key):
    indexed = {row[key]: row for row in items}
    _require(len(indexed) == len(items), "Duplicate " + key)
    return indexed


def context_revision(context):
    """Hash typed facts, case, subtype and goal. Display summary is editable copy."""
    _validator("context").validate(context)
    facts = {}
    for key, value in context["facts"].items():
        if type(value) in (int, float):
            _require(type(value) is int, "Numeric facts must use integer JSON values")
        facts[key] = value
    confirmed = {key: context[key] for key in ("case_type", "issue_subtype", "goal")}
    confirmed["facts"] = facts
    return hashlib.sha256(_key(confirmed).encode()).hexdigest()[:24]


def _official_url(value, *, source=False):
    try:
        url = urlsplit(value)
        allowed_query = source and url.hostname == "sso.agc.gov.sg"
        official_host = url.hostname in OFFICIAL_HOSTS or (
            source and url.hostname == "isomer-user-content.by.gov.sg"
        )
        valid = (
            url.scheme == "https" and official_host
            and url.netloc == url.hostname and not url.fragment
            and (not url.query or allowed_query)
            and not any(ch.isspace() or ch == chr(92) for ch in value)
        )
    except ValueError:
        valid = False
    _require(valid, "Unapproved official URL")


def _validate_question(question, context):
    field = question["field"]
    _require(field not in context["facts"], "Question repeats a supplied fact")
    choices = [row["value"] for row in question["options"]]
    _require("unknown" in choices, "Question must offer Not sure")
    _require(len({_key(v) for v in choices}) == len(choices), "Duplicate question value")
    for value in choices:
        _validator("context").validate({
            **context,
            "facts": {**context["facts"], field: value},
        })


def _validate_draft(draft):
    slots = set(_unique(draft["slots"], "id"))
    text = draft["subject"] + "\n" + draft["body"]
    used = set(re.findall(r"\{([A-Za-z0-9_-]+)\}", text))
    stripped = re.sub(r"\{[A-Za-z0-9_-]+\}", "", text)
    _require(used == slots and "{" not in stripped and "}" not in stripped, "Draft slots do not match")


def validate_plan(plan):
    """Check reference integrity. The RAG owner verifies actual provenance and scope."""
    _validator("plan").validate(plan)
    evidence = _unique(plan["evidence"], "id")
    contacts = _unique(plan["contacts"], "id")
    _unique(plan["details"], "kind")
    action = plan["primary_action"]
    claims = [plan["assessment"], action, *plan["checklist"]]
    claims.extend(item for group in plan["details"] for item in group["items"])
    claim_index = _unique(claims, "id")
    for record in evidence.values():
        _official_url(record["url"], source=True)
        digest = hashlib.sha256(record["quote"].encode()).hexdigest()
        _require(digest == record["quote_sha256"], "Quote digest mismatch")
        captured = datetime.fromisoformat(record["captured_at"])
        reviewed = datetime.fromisoformat(record["reviewed_at"])
        _require(captured <= reviewed, "Review precedes source capture")
    used = set()
    for row in [*claims, *contacts.values()]:
        refs = set(row["evidence_ids"])
        _require(refs <= evidence.keys(), "Unknown evidence ID")
        used.update(refs)
    _require(used == evidence.keys(), "Unreferenced evidence")
    for contact in contacts.values():
        if contact["kind"] == "web":
            _official_url(contact["value"])
    if action["kind"] == "prepare":
        _require(action["contact_id"] is None, "Preparation action opens no external contact")
    else:
        contact = contacts.get(action["contact_id"])
        _require(contact is not None, "Primary action has no matching contact")
        _require(contact["purpose"] in ACTION_PURPOSE[action["kind"]], "Wrong contact purpose")
        _require(set(contact["evidence_ids"]) <= set(action["evidence_ids"]), "Action omits contact evidence")
    for link in plan["legal_basis"]:
        claim = claim_index.get(link["claim_id"])
        eid = link["evidence_id"]
        _require(claim is not None and eid in claim["evidence_ids"], "Legal basis must support its selected claim")
        _require(evidence[eid]["kind"] == "statute", "Legal basis must be statutory text")
    if plan["draft"] is not None:
        _validate_draft(plan["draft"])


def validate_action_plan(payload, definition="response", *, request=None):
    """Check the payload and optionally bind a response to its initiating request."""
    _validator(definition).validate(payload)
    if definition == "request":
        if payload["operation"] == "plan":
            context_revision(payload["context"])
        else:
            _require(payload["description"].strip(), "Description is empty")
        return
    context = payload["context"]
    if payload["revision"] is not None:
        _require(context is not None and payload["revision"] == context_revision(context), "Stale context revision")
    if payload["question"] is not None:
        _validate_question(payload["question"], context)
    if payload["plan"] is not None:
        validate_plan(payload["plan"])
    if request is None:
        return
    validate_action_plan(request, "request")
    _require(payload["request_id"] == request["request_id"], "Response belongs to a different request")
    if request["operation"] == "interpret":
        _require(payload["state"] in ("CONFIRM", "LIMITED", "UNAVAILABLE"), "Interpretation cannot produce an action")
        _require(payload["revision"] is None, "Unconfirmed interpretation has no revision")
    else:
        _require(payload["state"] != "CONFIRM", "Confirmed plan cannot restart interpretation")
        if payload["state"] != "UNAVAILABLE":
            _require(payload["revision"] == context_revision(request["context"]), "Response changed confirmed facts")
