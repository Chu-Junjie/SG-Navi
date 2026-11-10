"""Task 24: release gate for independently reviewed zh-Hans display.

A merged PR is not translation approval. The attestation must be explicitly
committed and reviewed; an environment flag on its own cannot authorize text.
Official quotes, source records, URLs and canonical Action Plan are untouched.
"""
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

from backend.task24_bilingual import CATALOG, preview_zh_hans
from rag.action_evidence import load_action_package

ATTESTATION = Path(__file__).resolve().parent / "locales" / "task24_review_approval.json"
REVISION = "task24-reviewed-1.0"


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
    return {
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
