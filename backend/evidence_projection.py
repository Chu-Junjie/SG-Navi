"""Task 14 backend evidence display projection, separate from canonical Evidence v1.

This is a read-time projection of already reviewed passages, not new source
approval. Source text is never generated from an Evidence ID or editorial summary.
"""
import hashlib
from urllib.parse import urlsplit

from rag.import_knowledge_base import current_reviews
from rag.repository import EvidenceRepository


class DisplayEvidenceUnavailable(ValueError):
    """A claim cannot be safely projected to a current reviewed passage."""


SECTIONS = ("potential_channels", "conditions", "steps", "document_checklist")
REVIEWED_HOSTS = frozenset(("www.judiciary.gov.sg", "www.cea.gov.sg",
                            "www.case.org.sg"))


def _checked_record(evidence_id, case_type, bundle, blocked):
    passage = bundle["passages"].get(evidence_id)
    if passage is None or passage.get("source_id") in blocked:
        raise DisplayEvidenceUnavailable("Unavailable passage")
    source = bundle["sources"].get(passage["source_id"])
    if not source or source.get("status") != "verified" or passage.get("review_status") != "verified":
        raise DisplayEvidenceUnavailable("Unverified source")
    if (passage.get("source_version") != bundle["source_version"]
            or source.get("version") != bundle["source_version"]
            or case_type not in passage.get("case_types", ())
            or source.get("url") != passage.get("url")):
        raise DisplayEvidenceUnavailable("Mismatched case or version")
    try:
        url = urlsplit(passage["url"])
        if (url.scheme != "https" or url.hostname not in REVIEWED_HOSTS
                or url.username or url.password or url.port not in (None, 443)
                or url.fragment or not passage["text"].strip()
                or passage.get("text_kind") != "verbatim_excerpt"):
            raise DisplayEvidenceUnavailable("Unsafe official source")
    except (TypeError, KeyError, ValueError) as exc:
        raise DisplayEvidenceUnavailable("Unsafe URL") from exc
    digest = hashlib.sha256(passage["text"].encode("utf-8")).hexdigest()
    if digest != passage.get("excerpt_sha256"):
        raise DisplayEvidenceUnavailable("Excerpt digest mismatch")
    reviews = current_reviews(source, bundle["review_log"])
    if not reviews or not any(
        dict(zip(row["evidence_ids"].split(";"),
                 row["excerpt_sha256s"].split(";"))).get(evidence_id) == digest
        for row in reviews
    ):
        raise DisplayEvidenceUnavailable("No current review proof")
    # No fake deep link, screenshot, page or HTML fragment.
    return {
        "evidence_id": evidence_id,
        "source_id": passage["source_id"],
        "rule_ids": list(passage["rule_ids"]),
        "url": passage["url"],
        "review_status": "verified",
        "source_version": passage["source_version"],
        "publisher": source["publisher"],
        "title": source["title"],
        "verbatim_excerpt": passage["text"],
        "source_locator": passage["locator"],
        "reviewed_at": source["reviewed_at"],
        "summary": passage["summary"],
        "excerpt_sha256": digest,
        "display_version": "1.0",
        "display_state": "verified_snapshot",
        "preview": None,
    }


def project_display_evidence(case_type, guidance, *, expected_version,
                             repository=None, expected_records=None):
    """Check each item-level citation against a NEW authoritative snapshot.

    Existing six-field Evidence and navigate v1 stay unchanged. The returned
    records are for rendering only and are not a legal recommendation.
    """
    if case_type not in ("rental_deposit", "consumer_complaint") or not isinstance(guidance, dict):
        raise DisplayEvidenceUnavailable("Invalid guidance")
    repo = repository or EvidenceRepository()
    bundle, blocked = repo.snapshot()
    if expected_version != bundle["source_version"]:
        raise DisplayEvidenceUnavailable("Source version changed")

    cited = guidance.get("citations")
    if (not isinstance(cited, list) or not cited
            or len(cited) != len(set(cited))
            or any(not isinstance(i, str) or not i.strip() for i in cited)):
        raise DisplayEvidenceUnavailable("Invalid evidence citations")
    seen = set()
    for section in SECTIONS:
        items = guidance.get(section)
        if not isinstance(items, list):
            raise DisplayEvidenceUnavailable("Invalid guidance section")
        for item in items:
            if not isinstance(item, dict) or not isinstance(item.get("text"), str) or not item["text"].strip():
                raise DisplayEvidenceUnavailable("Missing item text")
            ids = item.get("evidence_ids")
            if (not isinstance(ids, list) or not ids
                    or any(not isinstance(i, str) for i in ids)
                    or len(ids) != len(set(ids)) or not set(ids) <= set(cited)):
                raise DisplayEvidenceUnavailable("Unlinked claim")
            seen.update(ids)
    if not seen or not seen <= set(cited):
        raise DisplayEvidenceUnavailable("No individually supported claims")
    # Some citations may be referenced by approved template limitations rather
    # than a step. They must STILL have a full current checked record.
    checked = [_checked_record(i, case_type, bundle, blocked) for i in cited]
    if expected_records is not None:
        by_id = {e["evidence_id"]: e for e in expected_records}
        if len(by_id) != len(expected_records) or set(by_id) != set(cited):
            raise DisplayEvidenceUnavailable("Changed citation identity")
        keys = ("source_id", "rule_ids", "url", "review_status",
                "source_version", "verbatim_excerpt", "excerpt_sha256",
                "publisher", "title", "source_locator", "reviewed_at", "summary")
        for current in checked:
            original = by_id[current["evidence_id"]]
            if any(original.get(key) != current[key] for key in keys):
                raise DisplayEvidenceUnavailable("Evidence changed during assembly")
    return checked
