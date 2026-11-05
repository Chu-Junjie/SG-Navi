"""Read-only five-source freshness audit; report drift without promoting evidence."""
from __future__ import annotations

import argparse
import json
import time
from datetime import datetime, timezone
from pathlib import Path
from urllib.error import HTTPError

from rag.import_knowledge_base import (
    DEFAULT_KB, current_reviews, load_knowledge_base, official_url
)
from rag.source_review import capture, normalize_space


def _audit_once(source, bundle, *, fetch):
    """Compare a live official page with its current signed-off review."""
    official_url(source["url"])
    result = {
        "source_id": source["source_id"],
        "url": source["url"],
        "review_version": source["version"],
        "status": "fetch_error",
        "recorded_review_status": source["status"],
    }
    try:
        live = fetch(source["url"])
        result["http_status"] = live["http_status"]
        result["retrieved_at"] = live["retrieved_at"]
        result["observed_sha256"] = live["content_sha256"]
        if live["url"] != source["url"] or live["http_status"] != 200:
            result["status"] = "url_or_http_changed"
            return result
        reviews = current_reviews(source, bundle["review_log"])
        hashes = {row["content_sha256"] for row in reviews}
        excerpts = [p for p in bundle["passages"].values()
                    if p["source_id"] == source["source_id"]]
        text = normalize_space(live["text"])
        missing = sorted(p["evidence_id"] for p in excerpts
                         if normalize_space(p["text"]) not in text)
        result["excerpt_count"] = len(excerpts)
        result["missing_evidence_ids"] = missing
        result["recorded_hash_matched"] = live["content_sha256"] in hashes
        if missing:
            result["status"] = "missing_reviewed_excerpt"
        elif not reviews or live["content_sha256"] not in hashes:
            result["status"] = "page_changed_excerpts_present"
        else:
            result["status"] = "unchanged"
        return result
    except (OSError, ValueError, KeyError, UnicodeError) as error:
        # Never log full page contents, user data or credentials.
        result["status"] = "fetch_error"
        result["error_type"] = type(error).__name__
        if isinstance(error, HTTPError):
            result["http_status"] = error.code
        return result


def audit_source(source, bundle, *, fetch=capture, attempts=3, pause=time.sleep):
    """Retry transient transport failures only; retain every attempt's outcome.

    A redirect, changed body or missing excerpt is a final review result. Even
    after a successful retry, the full existing hash/excerpt checks must pass.
    Forbidden/not-found responses are not retried or reclassified as success.
    """
    if not isinstance(attempts, int) or isinstance(attempts, bool) or not 1 <= attempts <= 3:
        raise ValueError("attempts must be an integer from 1 to 3")
    history = []
    for number in range(1, attempts + 1):
        result = _audit_once(source, bundle, fetch=fetch)
        history.append({"attempt": number, **{
            key: result[key] for key in ("status", "http_status", "error_type")
            if key in result
        }})
        transient = result.get("error_type") in {
            "TimeoutError", "URLError", "ConnectionError", "ConnectionResetError",
            "ConnectionAbortedError", "ConnectionRefusedError", "OSError",
        }
        if result.get("error_type") == "HTTPError":
            transient = result.get("http_status") in {408, 429, 500, 502, 503, 504}
        if result["status"] != "fetch_error" or not transient or number == attempts:
            result["attempt_count"] = number
            result["attempt_history"] = history
            return result
        pause(number)  # Bounded 1s/2s backoff; never changes reviewed records.


def run(directory=DEFAULT_KB, *, fetch=capture):
    """Audit all reviewed sources; distinguish non-substantive page drift."""
    bundle = load_knowledge_base(directory)
    results = [audit_source(source, bundle, fetch=fetch)
               for source in bundle["sources"].values()]
    return {
        "scope": "live_source_freshness_read_only",
        "checked_at": datetime.now(timezone.utc).isoformat(),
        "source_version": bundle["source_version"],
        "sources": results,
        "passed": all(s["status"] == "unchanged" for s in results),
        "review_required": [s["source_id"] for s in results
                            if s["status"] != "unchanged"],
        "no_changes_to_review_records": True,
    }


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--directory", type=Path, default=DEFAULT_KB)
    parser.add_argument("--output", type=Path, required=True,
                        help="Report file outside the five-file knowledge corpus")
    args = parser.parse_args(argv)
    if args.output.resolve().is_relative_to(Path(args.directory).resolve()):
        parser.error("Report must not overwrite or be created inside reviewed knowledge_base")
    report = run(args.directory)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    for row in report["sources"]:
        print(f"{row['source_id']}: {row['status']}")
    if not report["passed"]:
        print("REVIEW REQUIRED: do not auto-approve or update source hashes")
    return 0 if report["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
