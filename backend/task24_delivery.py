"""Task 24: release gate for independently reviewed zh-Hans display.

A merged PR is not translation approval. The attestation must be explicitly
committed and reviewed; an environment flag on its own cannot authorize text.
Official quotes, source records, URLs and canonical Action Plan are untouched.
"""
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from jsonschema import Draft202012Validator, FormatChecker, ValidationError
from shared.validate_action_plan import validate_action_plan

from backend.task24_bilingual import CATALOG, preview_zh_hans
from rag.action_evidence import load_action_package

ATTESTATION = Path(__file__).resolve().parent / "locales" / "task24_review_approval.json"
REVISION = "task24-reviewed-1.0"
REVIEWED_SCHEMA = Path(__file__).resolve().parent / "locales" / "task24_bilingual_overlay_reviewed.schema.json"


class ChineseTranslationNotApproved(ValueError):
    pass


def _digest(entries):
    return hashlib.sha256(json.dumps(
        entries, ensure_ascii=False, sort_keys=True,
        separators=(",", ":")).encode("utf-8")).hexdigest()


def checked_review_attestation(*, catalog_path=CATALOG, approval_path=ATTESTATION):
    """Return approved review metadata, or refuse without guessing.

    Only a source-owner-created review attestation can enable this feature.
    No attestation is included in this PR. Each change to entries invalidates
    the attestation SHA-256.
    """
    try:
        catalog = json.loads(Path(catalog_path).read_text(encoding="utf-8"))
        approval = json.loads(Path(approval_path).read_text(encoding="utf-8"))
        action_package, _, _, _ = load_action_package()
        if (action_package["version"] != catalog.get("source_action_package_version")
                or approval.get("approval_version") != REVISION
                or approval.get("translation_catalog_version") != catalog.get("catalog_version")
                or approval.get("source_action_package_version") != catalog.get("source_action_package_version")
                or approval.get("locale") != "zh-Hans"
                or approval.get("approved_by") != "Chu-Junjie"
                or approval.get("review_status") != "approved"
                or approval.get("entries_sha256") != _digest(catalog["entries"])
                or len(catalog["entries"]) < 155):
            raise ChineseTranslationNotApproved("No matching translation review")
        timestamp = datetime.fromisoformat(approval["reviewed_at"].replace("Z", "+00:00"))
        if (timestamp.tzinfo is None or timestamp > datetime.now(timezone.utc)):
            raise ChineseTranslationNotApproved("Invalid approval date")
        if any(row.get("review_status") != "pending_review"
               or not row.get("zh_hans") for row in catalog["entries"].values()):
            raise ChineseTranslationNotApproved("Unreviewed or empty translations")
        return {"approved_by": approval["approved_by"], "reviewed_at": approval["reviewed_at"],
                "entries_sha256": approval["entries_sha256"]}
    except (OSError, KeyError, ValueError, TypeError, AttributeError) as exc:
        raise ChineseTranslationNotApproved("Reviewed Chinese language pack unavailable") from exc


def reviewed_overlay(canonical, *, catalog_path=CATALOG, approval_path=ATTESTATION):
    """Add a sidecar ONLY after independent human sign-off, never alter v1."""
    approval = checked_review_attestation(
        catalog_path=catalog_path, approval_path=approval_path)
    candidate = preview_zh_hans(canonical, catalog_path=catalog_path)
    if candidate["translation_status"] != "pending_review" or candidate["display"] is None:
        raise ChineseTranslationNotApproved("Full Chinese display not covered")
    output = {
        "overlay_version": REVISION,
        "locale": "zh-Hans",
        "translation_status": "approved_explanation",
        "is_official_translation": False,
        "reviewed_by": approval["approved_by"],
        "reviewed_at": approval["reviewed_at"],
        "entries_sha256": approval["entries_sha256"],
        "disclaimer": candidate["disclaimer"],
        "canonical": candidate["canonical"],
        "display": candidate["display"],
    }

    # Strict reviewed response validation; proposal schema is NOT sufficient.
    schema = json.loads(REVIEWED_SCHEMA.read_text(encoding="utf-8"))
    Draft202012Validator(schema, format_checker=FormatChecker()).validate(output)
    validate_action_plan(output["canonical"], "response")
    if output["canonical"] != canonical:
        raise ChineseTranslationNotApproved("Canonical response was changed")
    # Every machine identity, citation, contact destination and typed option is
    # checked against its authoritative canonical counterpart.
    display = output["display"]
    if canonical["question"] is not None:
        a, b = canonical["question"], display["question"]
        if (not b or b["id"] != a["id"] or b["field"] != a["field"]
                or [v["value"] for v in b["options"]] != [v["value"] for v in a["options"]]):
            raise ChineseTranslationNotApproved("Question semantics changed")
    if canonical["plan"] is not None:
        a, b = canonical["plan"], display["plan"]
        if not b:
            raise ChineseTranslationNotApproved("Plan missing")
        for name in ("assessment", "primary_action"):
            if (a[name]["id"], a[name]["evidence_ids"]) != (b[name]["id"], b[name]["evidence_ids"]):
                raise ChineseTranslationNotApproved("Claim provenance changed")
        for name in ("checklist",):
            if [(v["id"], v["evidence_ids"]) for v in a[name]] != [(v["id"], v["evidence_ids"]) for v in b[name]]:
                raise ChineseTranslationNotApproved("Checklist citations changed")
        if len(a["details"]) != len(b["details"]):
            raise ChineseTranslationNotApproved("Detail count changed")
        for aa, bb in zip(a["details"], b["details"]):
            if aa["kind"] != bb["kind"] or [(z["id"], z["evidence_ids"]) for z in aa["items"]] != [(z["id"], z["evidence_ids"]) for z in bb["items"]]:
                raise ChineseTranslationNotApproved("Detail citations changed")
        if [(z["id"], z["value"], z["evidence_ids"]) for z in a["contacts"]] != [(z["id"], z["value"], z["evidence_ids"]) for z in b["contacts"]]:
            raise ChineseTranslationNotApproved("Contact destination changed")
        if a["draft"] is not None:
            if b["draft"] is None or [z["id"] for z in a["draft"]["slots"]] != [z["id"] for z in b["draft"]["slots"]]:
                raise ChineseTranslationNotApproved("Draft placeholder identities changed")
    return output
