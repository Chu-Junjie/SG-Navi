"""Select a reviewed action profile from confirmed facts and current source state."""

import hashlib
import json
from datetime import datetime, timedelta, timezone
from pathlib import Path

from jsonschema import ValidationError

from rag.repository import EvidenceRepository, RepositoryError
from shared.validate_action_plan import context_revision, validate_plan

DIRECTORY = Path(__file__).with_name("action_evidence")
MAX_SOURCE_AGE = timedelta(days=30)


class ActionEvidenceUnavailable(ValueError):
    """The caller must withhold this action and its contact/source claims."""


def _unique(rows, key):
    table = {row[key]: row for row in rows}
    if len(table) != len(rows):
        raise ActionEvidenceUnavailable(f"Duplicate {key} in the action package")
    return table


def _read(directory):
    body = (directory / "package.json").read_text(encoding="utf-8").encode("utf-8")
    expected = (directory / "package.sha256").read_text(encoding="ascii").strip()
    if hashlib.sha256(body).hexdigest() != expected:
        raise ActionEvidenceUnavailable("Action package digest changed")
    return json.loads(body), expected


def _materialize(profile, records, contacts, version):
    plan = dict(profile["plan"], source_version=version)
    plan["contacts"] = [contacts[key] for key in profile["contact_ids"]]
    claims = [plan["assessment"], plan["primary_action"], *plan["checklist"]]
    claims.extend(item for group in plan["details"] for item in group["items"])
    ids = {eid for item in [*claims, *plan["contacts"]] for eid in item["evidence_ids"]}
    plan["evidence"] = [records[eid]["evidence"] for eid in sorted(ids)]
    if any(profile["case_type"] not in records[eid]["case_types"] for eid in ids):
        raise ActionEvidenceUnavailable("Evidence belongs to another case type")
    validate_plan(plan)
    return plan


def load_action_package(directory=DIRECTORY):
    """Validate the reviewed package and all claim/contact/profile links."""
    try:
        data, digest = _read(Path(directory))
        records = _unique(data["records"], "id")
        contacts = _unique(data["contacts"], "id")
        profiles = _unique(data["profiles"], "id")
        for key, item in records.items():
            if item["evidence"]["id"] != key or not item["legacy_guards"]:
                raise ActionEvidenceUnavailable("Evidence identity or source guard missing")
        for contact in contacts.values():
            claim = {key: value for key, value in contact.items() if key not in ("id", "evidence_ids")}
            if not any(records[eid].get("authorized_contact") == claim for eid in contact["evidence_ids"]):
                raise ActionEvidenceUnavailable("Contact destination or purpose lacks source authorization")
        for profile in profiles.values():
            for subtype in profile["subtypes"]:
                for goal in profile["goals"]:
                    context_revision({
                        "case_type": profile["case_type"], "issue_subtype": subtype,
                        "goal": goal, "facts": profile["requires"], "summary": "Profile schema check",
                    })
            _materialize(profile, records, contacts, data["version"])
        return data, digest, records, contacts
    except (OSError, KeyError, TypeError, ValidationError, json.JSONDecodeError) as error:
        raise ActionEvidenceUnavailable("Action package failed validation") from error


def _matches(profile, context):
    return (
        profile["case_type"] == context["case_type"]
        and context["issue_subtype"] in profile["subtypes"]
        and context["goal"] in profile["goals"]
        and all(k in context["facts"] and type(context["facts"][k]) is type(v) and context["facts"][k] == v
                for k, v in profile["requires"].items())
    )


def _out_of_scope(facts):
    return (
        facts.get("purchase_purpose") == "business"
        or facts.get("merchant_location") == "outside_singapore"
        or facts.get("supplier_registered_in_sg") is False
        or facts.get("premises_type") in ("commercial", "industrial")
    )


def select_action_plan(context, *, expected_version, repository=None,
                       directory=DIRECTORY, now=None):
    """Return a scoped plan or None if no profile fits. Input must be confirmed."""
    context_revision(context)
    if _out_of_scope(context["facts"]):
        return None
    directory = Path(directory)
    data, digest, records, contacts = load_action_package(directory)
    if expected_version != data["version"]:
        raise ActionEvidenceUnavailable("Action source version does not match")
    profile = next((p for p in data["profiles"] if _matches(p, context)), None)
    if profile is None:
        return None
    plan = _materialize(profile, records, contacts, data["version"])
    try:
        repo = repository if repository is not None else EvidenceRepository()
        bundle, blocked = repo.snapshot()
        current = now if now is not None else datetime.now(timezone.utc)
        if bundle["source_version"] != data["legacy_version"]:
            raise ActionEvidenceUnavailable("Canonical source version changed")
        for record in plan["evidence"]:
            guards = set(records[record["id"]]["legacy_guards"])
            if not guards <= bundle["sources"].keys() or guards & blocked:
                raise ActionEvidenceUnavailable("A required source is unavailable")
            captured = datetime.fromisoformat(record["captured_at"])
            if not timedelta(0) <= current - captured <= MAX_SOURCE_AGE:
                raise ActionEvidenceUnavailable("A required source capture is stale")
        latest, latest_blocked = repo.snapshot()
        if latest != bundle or latest_blocked != blocked or _read(directory)[1] != digest:
            raise ActionEvidenceUnavailable("Source or review state changed during selection")
    except (RepositoryError, OSError, KeyError, json.JSONDecodeError) as error:
        raise ActionEvidenceUnavailable("Source state cannot be verified") from error
    return plan
