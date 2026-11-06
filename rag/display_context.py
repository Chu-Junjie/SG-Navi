"""Source-owner final verification and context enrichment for backend display data.

Does not assemble new guidance or generate official text. Consumes the reviewed
Task 14 backend projection, adds the separately curated context, and returns
only after a new canonical citation/state boundary succeeds. No network on read.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from functools import lru_cache
from pathlib import Path
from urllib.parse import urlsplit

from jsonschema import Draft202012Validator, FormatChecker
from jsonschema.exceptions import ValidationError
from referencing import Registry, Resource
from referencing.exceptions import NoSuchResource

from rag.citations import validate_citations
from rag.import_knowledge_base import api_evidence, current_reviews, official_url, read_json, timestamp
from rag.repository import EvidenceRepository
from rag.source_review import normalize_space

ROOT = Path(__file__).resolve().parents[1]
CONTEXT_FILE = Path(__file__).with_name("display_contexts.json")
SECTIONS = ("potential_channels", "conditions", "steps", "document_checklist")
REVIEWER = "Codex automated display-context check"
METHOD = "automated_live_context_and_digest_check"


class DisplayContextUnavailable(ValueError):
    """Fixed diagnostic only; caller must discard all tentative display output."""


def require(condition, code):
    if not condition:
        raise DisplayContextUnavailable(code)


def digest(text):
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def record_digest(record):
    return digest(json.dumps(record, sort_keys=True, separators=(",", ":"), ensure_ascii=False))


@lru_cache(maxsize=1)
def _validators():
    def deny_remote(uri):
        raise NoSuchResource(ref=uri)

    contract = json.loads((ROOT / "shared/display_evidence_contract.json").read_text(encoding="utf-8"))
    evidence = json.loads((ROOT / "shared/schemas/evidence_schema.json").read_text(encoding="utf-8"))
    registry = Registry(retrieve=deny_remote)
    for schema in (contract, evidence):
        Draft202012Validator.check_schema(schema)
        registry = registry.with_resource(schema["$id"], Resource.from_contents(schema))
    return {name: Draft202012Validator({"$ref": contract["$id"] + "#/$defs/" + name},
                                      registry=registry, format_checker=FormatChecker())
            for name in ("display_record", "enriched_result")}


def validate_display_record(record):
    """Structural validation alone does not authorize a verified badge."""
    _validators()["display_record"].validate(record)


def _check_claims(case_type, guidance, bundle):
    require(isinstance(guidance, dict) and set(guidance) == {
        "case_summary", "unresolved_questions", "citations", *SECTIONS}, "INVALID_GUIDANCE")
    require(guidance["case_summary"] == "User-confirmed " + case_type.replace("_", " ") +
            " scenario; facts have not been independently verified.", "CLAIM_MISMATCH")
    cited = guidance["citations"]
    require(isinstance(cited, list) and 0 < len(cited) <= 64 and
            all(isinstance(e, str) and e for e in cited) and len(set(cited)) == len(cited), "INVALID_CITATIONS")
    channels = guidance["potential_channels"]
    require(isinstance(channels, list) and channels, "INVALID_GUIDANCE")
    expected = {section: [] for section in SECTIONS}
    all_ids, used_templates = set(), set()
    for item in channels:
        matches = []
        for tid, template in bundle["templates"].items():
            if template["case_type"] != case_type or template["review_status"] != "verified":
                continue
            ids = {eid for s in (*SECTIONS[1:], "limitations")
                   for entry in template[s] for eid in entry["evidence_ids"]}
            approved = {"text": template["channel"] + " (conditional official source to check; not eligibility)",
                        "evidence_ids": sorted(ids)}
            if item == approved:
                matches.append((tid, template, ids, approved))
        require(len(matches) == 1, "CLAIM_MISMATCH")
        tid, template, ids, approved = matches[0]
        require(tid not in used_templates, "DUPLICATE_CLAIM")
        used_templates.add(tid)
        all_ids.update(ids)
        expected["potential_channels"].append(approved)
        for section in SECTIONS[1:]:
            expected[section].extend(template[section])
    require(set(cited) == all_ids, "INCOMPLETE_CITATIONS")
    claims = []
    for section in SECTIONS:
        require(guidance[section] == expected[section], "CLAIM_MISMATCH")
        for index, item in enumerate(guidance[section]):
            ids = item["evidence_ids"]
            require(ids and len(ids) == len(set(ids)), "INVALID_CITATIONS")
            claims.append({"claim_id": f"{section}:{index}", "section": section, "index": index,
                           "text": item["text"], "text_kind": "sg_navi_reviewed_template_text",
                           "evidence_ids": list(ids)})
    require(isinstance(guidance["unresolved_questions"], list), "INVALID_GUIDANCE")
    allowed_fields = json.loads((ROOT / f"frontend/schemas/{case_type}_input.schema.json").read_text(encoding="utf-8"))["properties"]
    seen = set()
    for q in guidance["unresolved_questions"]:
        require(isinstance(q, dict) and set(q) == {"field", "text"} and
                isinstance(q["field"], str) and q["field"] in allowed_fields and q["field"] not in seen and
                q["text"] == "Confirm " + q["field"].replace("_", " ") + ".", "INVALID_GUIDANCE")
        seen.add(q["field"])
    return cited, claims


def _context_for(eid, passage, source, bundle, curated):
    entry = curated["passages"][eid]
    capture = curated["sources"][passage["source_id"]]
    require(capture["context_bindings"].get(eid) == record_digest(entry), "CONTEXT_DIGEST_MISMATCH")
    require(entry["source_id"] == passage["source_id"] and entry["excerpt_sha256"] == passage["excerpt_sha256"]
            and entry["editorial_summary_sha256"] == digest(passage["summary"])
            and entry["source_locator_sha256"] == digest(passage["locator"]), "CONTEXT_CHANGED")
    require(capture["url"] == source["url"] and capture["http_status"] == 200
            and capture["source_version"] == bundle["source_version"]
            and capture["canonical_reviewed_at"] == source["reviewed_at"], "CONTEXT_CHANGED")
    reviews = current_reviews(source, bundle["review_log"])
    require(reviews and any(r["content_sha256"] == capture["body_sha256"] for r in reviews), "CONTEXT_CHANGED")
    require(timestamp(source["reviewed_at"], "source review") <= timestamp(capture["retrieved_at"], "context retrieval")
            <= timestamp(curated["reviewed_at"], "context review"), "CONTEXT_CHANGED")
    position = entry["position"]
    length = capture["normalized_text_length"]
    require(type(length) is int and 0 < length <= 5_000_000 and
            all(type(position[k]) is int for k in ("start", "end", "occurrence_count")) and
            0 <= position["start"] < position["end"] <= length and position["occurrence_count"] >= 1 and
            position["end"] - position["start"] == len(normalize_space(passage["text"])), "INVALID_CONTEXT_POSITION")
    surrounding = entry["surrounding_quote"]
    if surrounding is not None:
        require(isinstance(surrounding["text"], str) and 0 < len(surrounding["text"]) <= 1024
                and digest(surrounding["text"]) == surrounding["sha256"], "CONTEXT_DIGEST_MISMATCH")
        require(type(surrounding["start"]) is int and type(surrounding["end"]) is int and
                0 <= surrounding["start"] <= position["start"] < position["end"] <= surrounding["end"] <= length and
                surrounding["end"] - surrounding["start"] == len(surrounding["text"]), "INVALID_CONTEXT_POSITION")
        offset = position["start"] - surrounding["start"]
        require(surrounding["text"][offset:offset + len(normalize_space(passage["text"]))] == normalize_space(passage["text"]), "CONTEXT_CHANGED")
    require(entry["quote_completeness"] == "short_fragment_requires_official_context", "CONTEXT_CHANGED")
    return {"context_version": curated["context_version"], "quote_kind": "verbatim_official_excerpt",
            "summary_kind": "sg_navi_editorial_summary", "locator_kind": "sg_navi_textual_description",
            "quote_completeness": entry["quote_completeness"],
            "surrounding_quote": surrounding["text"] if surrounding else None,
            "surrounding_quote_sha256": surrounding["sha256"] if surrounding else None,
            "source_body_sha256": capture["body_sha256"], "checked_at": capture["retrieved_at"],
            "checked_by": curated["reviewed_by"], "check_method": curated["review_method"],
            "context_reviewed_at": curated["reviewed_at"], "canonical_reviewed_by": source["reviewed_by"],
            "canonical_review_method": reviews[0]["review_method"], "quarantine_state": "not_quarantined_at_read",
            "position_basis": "whitespace_normalized_visible_text_not_html_anchor",
            "excerpt_position": {k: position[k] for k in ("start", "end")},
            "surrounding_position": {k: surrounding[k] for k in ("start", "end")} if surrounding else None}


def _check_freshness(audit, bundle, source_ids):
    if audit is None:
        return  # verified_snapshot never asserts current live reachability.
    require(isinstance(audit, dict) and audit.get("scope") == "live_source_freshness_read_only"
            and audit.get("source_version") == bundle["source_version"], "SOURCE_PENDING")
    timestamp(audit["checked_at"], "freshness check")
    rows = audit["sources"]
    require(isinstance(rows, list) and all(isinstance(r, dict) and isinstance(r.get("source_id"), str) for r in rows), "SOURCE_PENDING")
    by_id = {r["source_id"]: r for r in rows}
    require(len(by_id) == len(rows), "SOURCE_PENDING")
    for sid in source_ids:
        row = by_id.get(sid, {})
        source = bundle["sources"][sid]
        require(row.get("status") == "unchanged" and row.get("http_status") == 200
                and row.get("recorded_hash_matched") is True and row.get("missing_evidence_ids") == []
                and row.get("url") == source["url"] and row.get("review_version") == bundle["source_version"]
                and any(r["content_sha256"] == row.get("observed_sha256") for r in current_reviews(source, bundle["review_log"]))
                and timestamp(audit["checked_at"], "freshness check") >= timestamp(source["reviewed_at"], "source review"), "SOURCE_PENDING")


def enrich_display_evidence(case_type, guidance, display_records, *, expected_source_version,
                             repository=None, context_file=CONTEXT_FILE, freshness_report=None):
    """Validate all claims/records, add checked context, then recheck source state.

    Raises DisplayContextUnavailable with a fixed code on any failure. The
    caller must withhold tentative records and return a limited/referral result.
    No partial badge, generated passage, network request or state write occurs.
    """
    try:
        require(case_type in ("rental_deposit", "consumer_complaint") and
                isinstance(display_records, list) and 0 < len(display_records) <= 64, "INVALID_INPUT")
        for record in display_records:
            validate_display_record(record)
        repo = repository or EvidenceRepository()
        bundle, blocked = repo.snapshot()
        initial_state = record_digest([bundle, sorted(blocked)])
        require(bundle["source_version"] == expected_source_version, "SOURCE_CHANGED")
        cited, claims = _check_claims(case_type, guidance, bundle)
        by_id = {r["evidence_id"]: r for r in display_records}
        require(len(by_id) == len(display_records) and set(by_id) == set(cited), "INCOMPLETE_CITATIONS")
        raw = Path(context_file).read_bytes()
        curated = read_json(raw.decode("utf-8"))
        require(set(curated) == {"format_version", "context_version", "source_version", "reviewed_at", "reviewed_by", "review_method", "sources", "passages"}
                and curated["format_version"] == "1.0" and curated["source_version"] == bundle["source_version"]
                and curated["reviewed_by"] == REVIEWER and curated["review_method"] == METHOD
                and set(curated["sources"]) == set(bundle["sources"])
                and set(curated["passages"]) == set(bundle["passages"]), "CONTEXT_UNAVAILABLE")
        timestamp(curated["reviewed_at"], "context review")
        counts = {sid: 0 for sid in curated["sources"]}
        for entry in curated["passages"].values():
            if entry["surrounding_quote"] is not None:
                counts[entry["source_id"]] += len(entry["surrounding_quote"]["text"].split())
        require(all(count <= 25 for count in counts.values()), "CONTEXT_UNAVAILABLE")
        checked, canonical, rules, source_ids = [], [], set(), set()
        for eid in cited:
            p = bundle["passages"][eid]
            source = bundle["sources"][p["source_id"]]
            require(p["source_id"] not in blocked and p["review_status"] == source["status"] == "verified"
                    and case_type in p["case_types"] and p["source_version"] == source["version"] == bundle["source_version"]
                    and p["url"] == source["url"] and p["text_kind"] == "verbatim_excerpt"
                    and digest(p["text"]) == p["excerpt_sha256"], "SOURCE_CHANGED")
            official_url(source["url"])
            require(not urlsplit(source["url"]).fragment, "SOURCE_CHANGED")
            require(any(dict(zip(r["evidence_ids"].split(";"), r["excerpt_sha256s"].split(";"))).get(eid) == p["excerpt_sha256"]
                        for r in current_reviews(source, bundle["review_log"])), "SOURCE_CHANGED")
            expected = {**api_evidence(p), "publisher": source["publisher"], "title": source["title"],
                        "verbatim_excerpt": p["text"], "source_locator": p["locator"], "reviewed_at": source["reviewed_at"],
                        "summary": p["summary"], "excerpt_sha256": p["excerpt_sha256"],
                        "display_version": "1.0", "display_state": "verified_snapshot", "preview": None}
            require(all(by_id[eid][k] == v for k, v in expected.items()), "SOURCE_CHANGED")
            expected["display_context"] = _context_for(eid, p, source, bundle, curated)
            require("display_context" not in by_id[eid] or by_id[eid]["display_context"] == expected["display_context"], "CONTEXT_CHANGED")
            checked.append(expected)
            canonical.append(api_evidence(p))
            rules.update(p["rule_ids"])
            source_ids.add(p["source_id"])
        _check_freshness(freshness_report, bundle, source_ids)

        class Boundary:
            fingerprint = None

            def snapshot(self):
                current, quarantined = repo.snapshot()
                self.fingerprint = record_digest([current, sorted(quarantined)])
                return current, quarantined

        boundary = Boundary()
        validate_citations(case_type, sorted(rules), canonical, cited,
                           expected_source_version=expected_source_version, repository=boundary)
        require(boundary.fingerprint == initial_state and Path(context_file).read_bytes() == raw, "SOURCE_CHANGED")
        result = {"display_version": "1.0", "display_state": "verified_snapshot", "context_version": curated["context_version"],
                  "source_version": bundle["source_version"], "display_evidence": checked, "claim_citations": claims}
        _validators()["enriched_result"].validate(result)
        return result
    except DisplayContextUnavailable:
        raise
    except (ValidationError, ValueError, OSError, KeyError, TypeError, AttributeError) as error:
        raise DisplayContextUnavailable("DISPLAY_UNAVAILABLE") from error


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--case-type", required=True, choices=("rental_deposit", "consumer_complaint"))
    parser.add_argument("--input", required=True, type=Path, help="Synthetic backend result JSON with research_guidance/display_evidence")
    parser.add_argument("--source-version", required=True)
    args = parser.parse_args(argv)
    try:
        data = read_json(args.input.read_text(encoding="utf-8"))
        result = enrich_display_evidence(args.case_type, data["research_guidance"], data["display_evidence"],
                                          expected_source_version=args.source_version)
    except (DisplayContextUnavailable, ValueError, OSError, KeyError, TypeError):
        print(json.dumps({"display_state": "unavailable", "display_evidence": []}))
        return 1
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
