"""Task 24: opt-in bilingual *review preview*, NOT a published legal translation.

Keep Action Plan 1.0 response canonical and byte-for-byte identical. Only build
a separate presentation overlay from reviewed-source-English-keyed static text.
This module does not modify a live route, source record, or official excerpt.
"""
from pathlib import Path
from copy import deepcopy
import json
from jsonschema import Draft202012Validator

from shared.validate_action_plan import validate_action_plan

HERE = Path(__file__).resolve().parent / "locales"
CATALOG = HERE / "task24_zh_hans_proposal.json"
SCHEMA = HERE / "task24_bilingual_overlay_proposal.schema.json"
COVERAGE_MESSAGE = "有些内容尚无经过审核的中文版本；请查看标明为英文原文的内容。"
UNOFFICIAL = "中文说明（非官方译文）；法律与程序依据以官方英文原文为准。"


def _translate(value, catalog, missing, path):
    if not isinstance(value, str):
        missing.append(path)
        return None
    row = catalog["entries"].get(value)
    if row is None or not row.get("zh_hans"):
        missing.append(path)
        return None
    # NEVER display pending-review text as approved content.
    return row["zh_hans"]


def _claim(claim, t, missing, path):
    return {
        "id": claim["id"],
        "text": _translate(claim["text"], t, missing, path + ".text"),
        "evidence_ids": list(claim["evidence_ids"]),
    }


def _draft(draft, t, missing):
    if draft is None:
        return None
    # Placeholders are machine IDs; verify exact 1-to-1 preservation.
    import re
    title = _translate(draft["title"], t, missing, "plan.draft.title")
    subject = _translate(draft["subject"], t, missing, "plan.draft.subject")
    body = _translate(draft["body"], t, missing, "plan.draft.body")
    original_slots = set(re.findall(r"\{([A-Za-z0-9_-]+)\}", draft["body"] + draft["subject"]))
    new_slots = set(re.findall(r"\{([A-Za-z0-9_-]+)\}", (body or "") + (subject or "")))
    declared = {slot["id"] for slot in draft["slots"]}
    if original_slots != new_slots or original_slots != declared:
        missing.append("plan.draft.placeholders")
    return {
        "title": title, "subject": subject, "body": body,
        "slots": [
            {"id": slot["id"], "label": _translate(slot["label"], t, missing, "plan.draft.slots." + slot["id"])}
            for slot in draft["slots"]
        ],
    }


def _summary(context, t, missing):
    if context is None:
        return None
    # From Task 18 only: exact known prefix and goal suffix; never translate an
    # arbitrary user-authored summary or invent legal/semantic assumptions.
    from backend.scenario_understanding import CONTEXT_VALIDATOR
    CONTEXT_VALIDATOR.validate(context)
    prefix = {
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
    }.get(context["issue_subtype"])
    suffix = {
        "complain": "make a complaint.",
        "seek_refund": "seek repayment.",
        "prepare_claim": "explore preparing a formal claim.",
        "contact_provider": "contact the relevant organisation.",
        "understand_options": "understand your available options.",
    }[context["goal"]]
    if context["summary"] != prefix + " You want to " + suffix:
        missing.append("context.summary.unreviewed_dynamic")
        return None
    a = _translate(prefix, t, missing, "context.summary.issue")
    b = _translate(suffix, t, missing, "context.summary.goal")
    return (a + " 您希望" + b) if a and b else None


def preview_zh_hans(canonical, *, catalog_path=CATALOG, schema_path=SCHEMA):
    """Validate canonical, return separate proposed overlay; NEVER alter canon.

    A missing mapping blocks the entire overlay rather than displaying a
    half-English Chinese route or a misleading official/legal quote.
    """
    validate_action_plan(canonical, "response")
    t = json.loads(Path(catalog_path).read_text(encoding="utf-8"))
    if (t.get("locale") != "zh-Hans" or t.get("review_status") != "pending_review"
            or t.get("catalog_version") != "task24-proposal-0.1"):
        raise ValueError("Unknown bilingual catalog version or approval state")
    missing = []
    display = {
        "message": _translate(canonical["message"], t, missing, "message"),
        "context_summary": _summary(canonical["context"], t, missing),
        "question": None,
        "plan": None,
    }
    q = canonical["question"]
    if q:
        display["question"] = {
            "id": q["id"], "field": q["field"],
            "prompt": _translate(q["prompt"], t, missing, "question.prompt"),
            "reason": _translate(q["reason"], t, missing, "question.reason"),
            "options": [
                {"value": deepcopy(x["value"]),
                 "label": _translate(x["label"], t, missing, "question.options." + str(i))}
                for i, x in enumerate(q["options"])
            ],
        }
    p = canonical["plan"]
    if p:
        display["plan"] = {
            "headline": _translate(p["headline"], t, missing, "plan.headline"),
            "assessment": _claim(p["assessment"], t, missing, "plan.assessment"),
            "primary_action": {
                **_claim(p["primary_action"], t, missing, "plan.primary_action"),
                "label": _translate(p["primary_action"]["label"], t, missing, "plan.primary_action.label"),
                "kind": p["primary_action"]["kind"],
                "contact_id": p["primary_action"]["contact_id"],
            },
            "checklist": [
                _claim(item, t, missing, "plan.checklist." + item["id"])
                for item in p["checklist"]
            ],
            "details": [
                {
                    "kind": group["kind"],
                    "title": _translate(group["title"], t, missing, "plan.details." + group["kind"] + ".title"),
                    "items": [
                        _claim(item, t, missing, "plan.details." + group["kind"] + "." + item["id"])
                        for item in group["items"]
                    ],
                }
                for group in p["details"]
            ],
            "contacts": [
                {
                    "id": contact["id"],
                    "institution": _translate(contact["institution"], t, missing, "plan.contacts." + contact["id"] + ".institution"),
                    "purpose": _translate(contact["purpose"], t, missing, "plan.contacts." + contact["id"] + ".purpose"),
                    "note": _translate(contact["note"], t, missing, "plan.contacts." + contact["id"] + ".note") if contact.get("note") else None,
                    "kind": contact["kind"], "value": contact["value"],
                    "evidence_ids": list(contact["evidence_ids"]),
                }
                for contact in p["contacts"]
            ],
            "draft": _draft(p["draft"], t, missing),
        }
        # No overlay for canonical evidence, legal_basis, source versions,
        # source URLs, digests, quotes, identities or official statutory text.
    status = "pending_review" if not missing else "missing_translation"
    result = {
        "overlay_version": "task24-proposal-0.1",
        "locale": "zh-Hans",
        "translation_status": status,
        "reviewed_by": None,
        "reviewed_at": None,
        "is_official_translation": False,
        "disclaimer": UNOFFICIAL,
        "canonical": deepcopy(canonical),
        "display": display if not missing else None,
        "missing_paths": sorted(set(missing)),
        "fallback_notice": None if not missing else COVERAGE_MESSAGE,
    }
    schema = json.loads(Path(schema_path).read_text(encoding="utf-8"))
    Draft202012Validator(schema).validate(result)
    return result
