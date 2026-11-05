"""Deterministic read-only freshness status tests using fake network responses."""
from rag.freshness_report import audit_source

URL = "https://www.case.org.sg/submit-a-complaint/"
SOURCE = {
    "source_id": "case-complaint",
    "url": URL,
    "version": "kb-test",
    "status": "verified",
    "reviewed_at": "2026-11-01T00:00:00+00:00",
    "reviewed_by": "test reviewer",
}
BUNDLE = {
    "review_log": {"review": {
        "source_id": "case-complaint",
        "new_version": "kb-test",
        "review_status": "verified",
        "reviewed_at": "2026-11-01T00:00:00+00:00",
        "reviewed_by": "test reviewer",
        "content_sha256": "same-hash",
    }},
    "passages": {"one": {
        "source_id": "case-complaint",
        "evidence_id": "CASE-EXCERPT",
        "text": "official reviewed wording",
    }},
}


def response(*, digest="same-hash", wording="official reviewed wording", url=URL, status=200):
    return {"content_sha256": digest, "text": wording, "url": url,
            "http_status": status, "retrieved_at": "2026-11-05T00:00:00+00:00"}


def test_unchanged_source_is_accepted_without_writing_anything():
    report = audit_source(SOURCE, BUNDLE, fetch=lambda url: response())
    assert report["status"] == "unchanged"
    assert report["recorded_hash_matched"]
    assert report["missing_evidence_ids"] == []


def test_full_page_change_even_with_literal_excerpts_requires_review():
    report = audit_source(SOURCE, BUNDLE, fetch=lambda url: response(digest="new-banner"))
    assert report["status"] == "page_changed_excerpts_present"
    assert not report["recorded_hash_matched"]
    assert report["missing_evidence_ids"] == []


def test_missing_official_excerpt_is_more_severe_than_fingerprint_drift():
    report = audit_source(SOURCE, BUNDLE, fetch=lambda url: response(digest="new", wording="unrelated text"))
    assert report["status"] == "missing_reviewed_excerpt"
    assert report["missing_evidence_ids"] == ["CASE-EXCERPT"]


def test_redirect_or_unexpected_http_is_not_silently_accepted():
    report = audit_source(SOURCE, BUNDLE, fetch=lambda url: response(url="https://www.case.org.sg/other/"))
    assert report["status"] == "url_or_http_changed"


def test_network_failure_requires_review_without_exposing_remote_contents():
    def raise_error(_):
        raise OSError("sample-failure")
    report = audit_source(SOURCE, BUNDLE, fetch=raise_error)
    assert report["status"] == "fetch_error"
    assert report["error_type"] == "OSError"
    assert "sample-failure" not in str(report)
