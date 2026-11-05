"""Deterministic read-only freshness status tests using fake network responses."""
from copy import deepcopy

import pytest

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
    report = audit_source(SOURCE, BUNDLE, fetch=raise_error, pause=lambda _: None)
    assert report["status"] == "fetch_error"
    assert report["error_type"] == "OSError"
    assert "sample-failure" not in str(report)
    assert report["attempt_count"] == 3
    assert [x["status"] for x in report["attempt_history"]] == ["fetch_error"] * 3


def test_http_error_reports_status_without_copying_server_message():
    from urllib.error import HTTPError

    def fail(_):
        raise HTTPError(URL, 403, "access denied: do not log arbitrary text", hdrs=None, fp=None)

    report = audit_source(SOURCE, BUNDLE, fetch=fail)
    assert report["status"] == "fetch_error"
    assert report["error_type"] == "HTTPError"
    assert report["http_status"] == 403
    assert "access denied" not in str(report)
    assert report["attempt_count"] == 1


def test_timeout_then_matching_page_preserves_failure_and_does_not_mutate_reviews():
    bundle = deepcopy(BUNDLE)
    calls = []
    pauses = []

    def fetch(url):
        calls.append(url)
        if len(calls) == 1:
            raise TimeoutError("never copy remote error details")
        return response()

    report = audit_source(SOURCE, bundle, fetch=fetch, pause=pauses.append)
    assert report["status"] == "unchanged"
    assert report["recorded_hash_matched"]
    assert report["missing_evidence_ids"] == []
    assert report["attempt_count"] == 2
    assert report["attempt_history"] == [
        {"attempt": 1, "status": "fetch_error", "error_type": "TimeoutError"},
        {"attempt": 2, "status": "unchanged", "http_status": 200},
    ]
    assert pauses == [1]
    assert bundle == BUNDLE
    assert "never copy" not in str(report)


@pytest.mark.parametrize("code", [408, 429, 500, 502, 503, 504])
def test_transient_http_failure_can_recover_only_after_strict_matching_page(code):
    from urllib.error import HTTPError
    calls = []

    def fetch(url):
        calls.append(url)
        if len(calls) == 1:
            raise HTTPError(url, code, "remote detail", hdrs=None, fp=None)
        return response()

    report = audit_source(SOURCE, BUNDLE, fetch=fetch, pause=lambda _: None)
    assert report["status"] == "unchanged"
    assert report["attempt_history"][0]["http_status"] == code
    assert report["attempt_count"] == 2
    assert "remote detail" not in str(report)


@pytest.mark.parametrize("live, expected", [
    (response(digest="different"), "page_changed_excerpts_present"),
    (response(wording="error page", digest="error"), "missing_reviewed_excerpt"),
    (response(url=URL + "redirect"), "url_or_http_changed"),
])
def test_semantic_or_redirect_failure_is_never_retried_to_obtain_a_pass(live, expected):
    calls = []

    def fetch(url):
        calls.append(url)
        return live if len(calls) == 1 else response()

    report = audit_source(SOURCE, BUNDLE, fetch=fetch, pause=lambda _: None)
    assert report["status"] == expected
    assert report["attempt_count"] == 1
    assert len(calls) == 1


def test_invalid_response_is_not_a_retryable_network_failure():
    report = audit_source(SOURCE, BUNDLE, fetch=lambda _: {})
    assert report["status"] == "fetch_error"
    assert report["error_type"] == "KeyError"
    assert report["attempt_count"] == 1


@pytest.mark.parametrize("attempts", [0, 4, True, 1.5])
def test_retry_limit_is_bounded(attempts):
    with pytest.raises(ValueError):
        audit_source(SOURCE, BUNDLE, fetch=lambda _: response(), attempts=attempts)
