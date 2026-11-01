"""Validate the five-file knowledge bundle and optionally export a checked snapshot."""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
from urllib.parse import urlsplit

from jsonschema.exceptions import ValidationError
from shared.validate_contracts import validate as validate_api

from rag.source_review import capture, normalize_space

DEFAULT_KB = Path(__file__).resolve().parent / "knowledge_base"
FILES = {"sources.csv", "passages.jsonl", "rule_evidence_map.json", "action_templates.json", "source_review_log.csv"}
HOSTS = {"www.judiciary.gov.sg", "www.cea.gov.sg", "www.case.org.sg"}
STATES = {"unreviewed", "verified", "quarantined"}
CASES = {"rental_deposit", "consumer_complaint"}
API_FIELDS = ("evidence_id", "source_id", "rule_ids", "url", "review_status", "source_version")
SOURCE_FIELDS = {"source_id", "publisher", "title", "url", "topic_tags", "reviewed_at", "reviewed_by", "status", "version"}
REVIEW_FIELDS = {"review_id", "source_id", "reviewed_at", "reviewed_by", "previous_version", "new_version", "change_summary", "affected_rule_ids", "retrieved_at", "http_status", "content_sha256", "review_status", "review_method", "evidence_ids", "excerpt_sha256s"}


class KnowledgeBaseError(ValueError):
    """Invalid or unverifiable source preparation data."""


def require(condition, message):
    if not condition:
        raise KnowledgeBaseError(message)


def nonblank(value):
    return isinstance(value, str) and bool(value.strip())


def unique_object(pairs):
    result = {}
    for key, value in pairs:
        require(key not in result, f"duplicate JSON key: {key}")
        result[key] = value
    return result


def read_json(text):
    return json.loads(text, object_pairs_hook=unique_object)


def read_csv(path, fields):
    with path.open(encoding="utf-8-sig", newline="") as stream:
        reader = csv.DictReader(stream)
        require(reader.fieldnames is not None and set(reader.fieldnames) == fields
                and len(reader.fieldnames) == len(fields), f"{path.name}: incorrect columns")
        rows = list(reader)
        require(rows and all(None not in row and all(value is not None for value in row.values()) for row in rows),
                f"{path.name}: empty or malformed rows")
        return rows


def timestamp(value, label):
    try:
        result = datetime.fromisoformat(value)
    except (TypeError, ValueError) as error:
        raise KnowledgeBaseError(f"{label}: invalid timestamp") from error
    require(result.utcoffset() is not None, f"{label}: timestamp needs timezone")
    require(result <= datetime.now(timezone.utc) + timedelta(minutes=1), f"{label}: timestamp is in the future")
    return result


def official_url(value):
    require(nonblank(value) and not re.search(r"\s", value), "source URL must be nonempty without whitespace")
    try:
        parsed = urlsplit(value)
        port = parsed.port
    except ValueError as error:
        raise KnowledgeBaseError("invalid source URL port") from error
    require(parsed.scheme == "https" and parsed.hostname in HOSTS and not parsed.username
            and not parsed.password and port in (None, 443), "source URL must use an allowed official HTTPS host")


def index_rows(rows, key, label):
    require(isinstance(rows, list) and rows, f"{label}: expected a nonempty list")
    result = {}
    for row in rows:
        require(isinstance(row, dict) and nonblank(row.get(key)), f"{label}: missing {key}")
        value = row[key]
        require(value not in result, f"{label}: duplicate {key} {value}")
        result[value] = row
    return result


def id_list(value, label, allow_empty=False):
    require(isinstance(value, list) and (allow_empty or value) and all(nonblank(item) for item in value),
            f"{label}: expected nonblank ID list")
    require(len(value) == len(set(value)), f"{label}: duplicate ID")
    return value


def check_cases(value, label):
    id_list(value, label)
    require(set(value) <= CASES, f"{label}: unsupported case type")


def api_evidence(passage):
    """Project stored excerpts into the existing six-field API Evidence envelope."""
    return {key: passage[key] for key in API_FIELDS}


def load_knowledge_base(directory=DEFAULT_KB):
    directory = Path(directory)
    try:
        require(directory.is_dir(), "knowledge base directory does not exist")
        require({path.name for path in directory.iterdir()} == FILES, "knowledge base must contain exactly the five fixed files")
        sources = index_rows(read_csv(directory / "sources.csv", SOURCE_FIELDS), "source_id", "sources")
        require(len(sources) == 5, "baseline needs exactly five distinct sources")
        reviews = index_rows(read_csv(directory / "source_review_log.csv", REVIEW_FIELDS), "review_id", "review log")
        passages = index_rows([read_json(line) for line in (directory / "passages.jsonl").read_text(encoding="utf-8").splitlines()], "evidence_id", "passages")
        rule_file = read_json((directory / "rule_evidence_map.json").read_text(encoding="utf-8"))
        template_file = read_json((directory / "action_templates.json").read_text(encoding="utf-8"))
        require(isinstance(rule_file, dict) and isinstance(template_file, dict), "rule and template files must be objects")
        version = rule_file.get("source_version")
        require(nonblank(version) and template_file.get("source_version") == version, "bundle source_version mismatch")
        rules = index_rows(rule_file.get("rules"), "rule_id", "rule map")
        templates = index_rows(template_file.get("templates"), "template_id", "templates")
        _validate_records(sources, passages, rules, templates, reviews, version)
    except (OSError, UnicodeError, json.JSONDecodeError, csv.Error) as error:
        raise KnowledgeBaseError(f"cannot read knowledge bundle: {error}") from error
    return {"source_version": version, "sources": sources, "passages": passages,
            "rules": rules, "templates": templates, "review_log": reviews}


def _validate_records(sources, passages, rules, templates, reviews, version):
    for review in reviews.values():
        require(review["source_id"] in sources, "review log: unknown source")
        require(review["review_status"] in STATES, "review log: unknown status")
        retrieved = timestamp(review["retrieved_at"], "review retrieval")
        reviewed = timestamp(review["reviewed_at"], "review time")
        require(retrieved <= reviewed, "review cannot precede retrieval")
        require(nonblank(review["reviewed_by"]) and nonblank(review["change_summary"]), "review needs reviewer and change summary")
        require(bool(re.fullmatch(r"[0-9a-f]{64}", review["content_sha256"])), "review needs a content SHA256")
        require(review["review_method"] == "automated_live_page_and_excerpt_check", "review method must identify the actual automated check")
        reviewed_ids = review["evidence_ids"].split(";")
        reviewed_hashes = review["excerpt_sha256s"].split(";")
        require(len(reviewed_ids) == len(reviewed_hashes) and len(reviewed_ids) == len(set(reviewed_ids))
                and all(re.fullmatch(r"[0-9a-f]{64}", digest) for digest in reviewed_hashes),
                "review needs one excerpt digest per evidence ID")
        if review["review_status"] == "verified":
            require(review["http_status"] == "200", "verified review requires HTTP 200")

    for source in sources.values():
        for field in ("publisher", "title", "topic_tags"):
            require(nonblank(source[field]), f"source: missing {field}")
        official_url(source["url"])
        require(source["status"] in STATES, "source: unknown status")
        require(source["version"] == version, "source version differs from bundle version")
        if source["status"] == "verified":
            timestamp(source["reviewed_at"], "source review")
            matches = [row for row in reviews.values() if row["source_id"] == source["source_id"]
                       and row["new_version"] == source["version"] and row["review_status"] == "verified"
                       and row["reviewed_at"] == source["reviewed_at"] and row["reviewed_by"] == source["reviewed_by"]]
            require(matches, "verified source needs a matching successful review record")

    for passage in passages.values():
        source = sources.get(passage.get("source_id"))
        require(source is not None, "passage: unknown source")
        require(passage.get("url") == source["url"], "passage URL differs from its source")
        require(passage.get("source_version") == source["version"], "passage source_version mismatch")
        require(isinstance(passage.get("review_status"), str) and passage["review_status"] in STATES, "passage: unknown status")
        for field in ("text", "summary", "locator"):
            require(nonblank(passage.get(field)), f"passage: missing {field}")
        require(passage.get("text_kind") == "verbatim_excerpt", "passage must label original excerpt explicitly")
        require(passage.get("excerpt_sha256") == hashlib.sha256(passage["text"].encode()).hexdigest(), "passage excerpt hash mismatch")
        check_cases(passage.get("case_types"), "passage cases")
        id_list(passage.get("rule_ids"), "passage rules")
        try:
            validate_api(api_evidence(passage), "evidence")
        except (ValidationError, KeyError) as error:
            raise KnowledgeBaseError("passage metadata fails shared Evidence Schema") from error
        if passage["review_status"] == "verified":
            require(source["status"] == "verified", "verified passage cannot use an unreviewed or quarantined source")
            require(any(dict(zip(row["evidence_ids"].split(";"), row["excerpt_sha256s"].split(";"))).get(passage["evidence_id"]) == passage["excerpt_sha256"]
                        for row in reviews.values() if row["source_id"] == source["source_id"]
                        and row["new_version"] == version and row["review_status"] == "verified"),
                    "verified passage not recorded in source review")
        for rule_id in passage["rule_ids"]:
            require(rule_id in rules and passage["evidence_id"] in rules[rule_id].get("evidence_ids", []), "passage rule lacks reciprocal mapping")

    for rule in rules.values():
        check_cases(rule.get("case_types"), "rule cases")
        evidence_ids = id_list(rule.get("evidence_ids"), "rule evidence")
        require(isinstance(rule.get("review_status"), str) and rule["review_status"] in STATES
                and isinstance(rule.get("runtime_enabled"), bool), "rule needs review status and boolean activation flag")
        require(not rule["runtime_enabled"] or rule["review_status"] == "verified", "unreviewed rule cannot be enabled")
        for evidence_id in evidence_ids:
            passage = passages.get(evidence_id)
            require(passage is not None, "rule references missing evidence")
            require(rule["rule_id"] in passage["rule_ids"], "rule lacks reciprocal passage annotation")
            require(set(rule["case_types"]) <= set(passage["case_types"]), "rule case scope conflicts with evidence")
            if rule["review_status"] == "verified" or rule["runtime_enabled"]:
                require(passage["review_status"] == "verified", "usable rule references unverified evidence")

    for template in templates.values():
        require(isinstance(template.get("case_type"), str) and template["case_type"] in CASES
                and nonblank(template.get("channel")), "template needs case type and channel")
        require(isinstance(template.get("review_status"), str) and template["review_status"] in STATES, "template: unknown review status")
        for section in ("conditions", "steps", "document_checklist", "limitations"):
            entries = template.get(section)
            require(isinstance(entries, list) and entries, f"template: missing {section}")
            for entry in entries:
                require(isinstance(entry, dict) and nonblank(entry.get("text")), "template item needs text")
                for evidence_id in id_list(entry.get("evidence_ids"), "template citations"):
                    passage = passages.get(evidence_id)
                    require(passage is not None, "template references missing evidence")
                    require(template["case_type"] in passage["case_types"], "template cites evidence for the wrong case")
                    if template["review_status"] == "verified":
                        require(passage["review_status"] == "verified", "verified template cites unverified evidence")

    for review in reviews.values():
        require(set(filter(None, review["evidence_ids"].split(";"))) <= passages.keys(), "review log references unknown evidence")
        require(set(filter(None, review["affected_rule_ids"].split(";"))) <= rules.keys(), "review log references unknown rules")


def verify_live_sources(bundle):
    """Fail on changed content or absent quotes; never silently renew a review."""
    results = []
    for source in bundle["sources"].values():
        official_url(source["url"])
        current = capture(source["url"])
        require(current["http_status"] == 200 and current["url"] == source["url"], "live source failed or redirected; review required")
        matching = [row for row in bundle["review_log"].values() if row["source_id"] == source["source_id"]
                    and row["new_version"] == source["version"] and row["review_status"] == "verified"]
        require(matching and any(row["content_sha256"] == current["content_sha256"] for row in matching),
                f"{source['source_id']}: content changed; review and version update required")
        excerpts = [p for p in bundle["passages"].values() if p["source_id"] == source["source_id"]]
        require(all(normalize_space(p["text"]) in normalize_space(current["text"]) for p in excerpts),
                f"{source['source_id']}: an excerpt is absent from the live page")
        results.append({"source_id": source["source_id"], "http_status": 200, "excerpts_checked": len(excerpts)})
    return results


def import_snapshot(directory, output, verify_live=False):
    bundle = load_knowledge_base(directory)
    if verify_live:
        verify_live_sources(bundle)
    output = Path(output)
    require(output.suffix == ".json", "export path must end in .json")
    require(not output.resolve().is_relative_to(Path(directory).resolve()), "export must be outside the five-file source directory")
    output.parent.mkdir(parents=True, exist_ok=True)
    # Exclusive creation preserves any existing output; invalid bundles never reach this write.
    with output.open("x", encoding="utf-8") as stream:
        json.dump(bundle, stream, indent=2, ensure_ascii=False)
        stream.write("\n")
    return bundle


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--directory", type=Path, default=DEFAULT_KB)
    parser.add_argument("--verify-live", action="store_true", help="check official URLs, full-text hashes and exact excerpts")
    parser.add_argument("--output", type=Path, help="export a validated JSON snapshot to a new file")
    args = parser.parse_args(argv)
    try:
        if args.output:
            bundle = import_snapshot(args.directory, args.output, args.verify_live)
        else:
            bundle = load_knowledge_base(args.directory)
            if args.verify_live:
                for result in verify_live_sources(bundle):
                    print(f"LIVE {result['source_id']}: HTTP 200, {result['excerpts_checked']} excerpts checked")
        print(f"PASS {bundle['source_version']}: {len(bundle['sources'])} sources, {len(bundle['passages'])} passages, {len(bundle['rules'])} rule mappings, {len(bundle['templates'])} templates")
        return 0
    except (KnowledgeBaseError, OSError, ValueError) as error:
        print(f"FAIL: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
