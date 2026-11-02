"""Task 4 retrieval, citations and source operations; no legal routing is inferred."""
import copy
import csv
import json
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

from rag import repository as repository_module
from rag.citations import CitationValidationError, CitationValidator, validate_citations
from rag.import_knowledge_base import DEFAULT_KB, load_knowledge_base
from rag.repository import EvidenceRepository, RepositoryError
from rag.retriever import retrieve_evidence
from shared.validate_contracts import validate

ROOT = DEFAULT_KB.parents[1]
RENTAL = "rental_deposit"
CONSUMER = "consumer_complaint"
SCT = "SCT_RESIDENTIAL_SCOPE"
CEA = "CEA_AGENCY_AGREEMENT"
CASE = "CASE_PERSONAL_PURPOSE"
SCT_SOURCE = "courts-sct-eligibility"


@pytest.fixture
def repository(tmp_path):
    directory = tmp_path / "kb"
    shutil.copytree(DEFAULT_KB, directory)
    return EvidenceRepository(directory, state_file=tmp_path / "state" / "quarantine.json")


def edit_csv(directory, filename, change):
    path = directory / filename
    with path.open(encoding="utf-8", newline="") as stream:
        reader = csv.DictReader(stream)
        fields, rows = reader.fieldnames, list(reader)
    change(rows)
    with path.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def edit_json(directory, filename, change):
    path = directory / filename
    data = json.loads(path.read_text(encoding="utf-8"))
    change(data)
    path.write_text(json.dumps(data), encoding="utf-8")


def downgrade_source(directory, source_id, status):
    """Coherent invalidation fixture, preserving original review history."""
    edit_csv(directory, "sources.csv", lambda rows: [row.update(status=status) for row in rows if row["source_id"] == source_id])
    path = directory / "passages.jsonl"
    passages = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]
    affected = set()
    for passage in passages:
        if passage["source_id"] == source_id:
            passage["review_status"] = status
            affected.add(passage["evidence_id"])
    path.write_text("".join(json.dumps(p) + "\n" for p in passages), encoding="utf-8")
    edit_json(directory, "rule_evidence_map.json", lambda data: [rule.update(review_status=status) for rule in data["rules"] if affected.intersection(rule["evidence_ids"])])
    def templates(data):
        for template in data["templates"]:
            ids = {eid for section in ("conditions", "steps", "document_checklist", "limitations") for item in template[section] for eid in item["evidence_ids"]}
            if affected.intersection(ids):
                template["review_status"] = status
    edit_json(directory, "action_templates.json", templates)


def change_version(directory, version):
    """Synthetic version transition for update tests, not a new source review."""
    edit_csv(directory, "sources.csv", lambda rows: [row.update(version=version) for row in rows])
    edit_csv(directory, "source_review_log.csv", lambda rows: [row.update(new_version=version) for row in rows])
    path = directory / "passages.jsonl"
    passages = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]
    for passage in passages:
        passage["source_version"] = version
    path.write_text("".join(json.dumps(p) + "\n" for p in passages), encoding="utf-8")
    for filename in ("rule_evidence_map.json", "action_templates.json"):
        edit_json(directory, filename, lambda data: data.update(source_version=version))


def found(repository, case_type=RENTAL, rules=None):
    result = retrieve_evidence(case_type, rules or [SCT], {}, repository=repository)
    assert result["retrieval_status"] == "FOUND"
    return result["evidence"]


def assert_status(result, status):
    validate(result, "retrieval_response")
    assert set(result) == {"retrieval_status", "evidence"}
    assert result["retrieval_status"] == status
    if status != "FOUND":
        assert result["evidence"] == []


def mock_live_pages(monkeypatch, bundle, *, changed=None, unavailable=None, missing=None):
    def capture(url):
        source = next(row for row in bundle["sources"].values() if row["url"] == url)
        source_id = source["source_id"]
        if source_id == unavailable:
            raise OSError("synthetic unavailable source")
        review = next(row for row in bundle["review_log"].values() if row["source_id"] == source_id
                      and row["reviewed_at"] == source["reviewed_at"])
        text = " ".join(p["text"] for p in bundle["passages"].values() if p["source_id"] == source_id)
        return {"url": url, "http_status": 200, "text": "Missing excerpts" if source_id == missing else text,
                "content_sha256": "0" * 64 if source_id == changed else review["content_sha256"]}
    monkeypatch.setattr(repository_module, "capture", capture)


@pytest.mark.parametrize("case_type,rule_id,source_id", [(RENTAL, SCT, SCT_SOURCE), (RENTAL, CEA, "cea-dispute-resolution"), (CONSUMER, CASE, "case-complaint")])
def test_exact_rule_lookup_keeps_channels_separate(repository, case_type, rule_id, source_id):
    evidence = found(repository, case_type, [rule_id])
    assert len(evidence) == 1 and evidence[0]["source_id"] == source_id
    assert evidence[0]["rule_ids"] == [rule_id]
    assert set(evidence[0]) == {"evidence_id", "source_id", "rule_ids", "url", "review_status", "source_version"}
    validate_citations(case_type, [rule_id], evidence, [evidence[0]["evidence_id"]], repository=repository)


def test_order_is_deterministic_and_response_mutation_does_not_poison_future_reads(repository):
    rules = ["SCT_EVENT_DATE", "SCT_CLAIM_AMOUNT", SCT]
    evidence = found(repository, rules=rules)
    assert [item["rule_ids"][0] for item in evidence] == rules
    evidence[0]["url"] = "https://untrusted.invalid/"
    evidence[0]["rule_ids"].clear()
    assert found(repository, rules=rules)[0]["rule_ids"] == ["SCT_EVENT_DATE"]


@pytest.mark.parametrize("rules", [[], ["UNKNOWN_RULE"], [SCT, "UNKNOWN_RULE"], [SCT, CASE]])
def test_missing_or_wrong_scope_rules_never_return_partial_evidence(repository, rules):
    assert_status(retrieve_evidence(RENTAL, rules, {"keywords": "agency consumer court"}, repository=repository), "NO_RESULTS")


def test_consumer_cannot_request_the_rental_only_agency_mapping(repository):
    assert_status(retrieve_evidence(CONSUMER, [CEA], {}, repository=repository), "NO_RESULTS")


@pytest.mark.parametrize("case_type,rules,facts", [("employment", [SCT], {}), (RENTAL, SCT, {}), (RENTAL, [SCT, SCT], {}), (RENTAL, [None], {}), (RENTAL, [SCT], None), (RENTAL, [SCT], [])])
def test_invalid_requests_return_contract_valid_error(repository, case_type, rules, facts):
    assert_status(retrieve_evidence(case_type, rules, facts, repository=repository), "ERROR")


def test_unknown_null_and_false_facts_are_preserved_and_never_used_to_guess_a_rule(repository):
    facts = {"claim_amount_sgd": None, "respondent_in_singapore": "unknown", "resolution_attempted": False}
    original = copy.deepcopy(facts)
    assert_status(retrieve_evidence(RENTAL, [], facts, repository=repository), "NO_RESULTS")
    assert_status(retrieve_evidence(RENTAL, [SCT], facts, repository=repository), "FOUND")
    assert facts == original


@pytest.mark.parametrize("status", ["unreviewed", "quarantined"])
def test_coherent_source_state_filters_only_affected_evidence(repository, status):
    downgrade_source(repository.directory, SCT_SOURCE, status)
    load_knowledge_base(repository.directory)
    assert_status(retrieve_evidence(RENTAL, [SCT], {}, repository=repository), "NO_RESULTS")
    assert_status(retrieve_evidence(RENTAL, [CEA], {}, repository=repository), "FOUND")


def test_malformed_bundle_and_missing_files_fail_without_stale_evidence(repository):
    found(repository)
    (repository.directory / "passages.jsonl").write_text("{", encoding="utf-8")
    assert_status(retrieve_evidence(RENTAL, [SCT], {}, repository=repository), "ERROR")


def test_persistent_quarantine_blocks_retrieval_across_repository_instances(repository):
    canonical_before = {path.name: path.read_bytes() for path in repository.directory.iterdir()}
    repository.quarantine_source(SCT_SOURCE, actor="test-admin", reason="synthetic conflict")
    second = EvidenceRepository(repository.directory, state_file=repository.state_file)
    assert_status(retrieve_evidence(RENTAL, [SCT], {}, repository=second), "NO_RESULTS")
    assert_status(retrieve_evidence(RENTAL, [CEA], {}, repository=second), "FOUND")
    assert canonical_before == {path.name: path.read_bytes() for path in repository.directory.iterdir()}
    assert second.source_state()["events"][0]["action"] == "quarantine"


def test_repeated_same_quarantine_is_idempotent(repository):
    first = repository.quarantine_source(SCT_SOURCE, actor="test-admin", reason="synthetic conflict")
    assert repository.quarantine_source(SCT_SOURCE, actor="test-admin", reason="synthetic conflict") == first


@pytest.mark.parametrize("source,actor,reason", [("unknown", "test-admin", "reason"), (SCT_SOURCE, "", "reason"), (SCT_SOURCE, "test-admin", " ")])
def test_invalid_source_operations_do_not_create_state(repository, source, actor, reason):
    with pytest.raises(RepositoryError):
        repository.quarantine_source(source, actor=actor, reason=reason)
    assert not repository.state_file.exists()


@pytest.mark.parametrize("content", ["{", '{"format_version":2,"blocked_sources":{},"events":[]}', '{"format_version":1,"blocked_sources":[],"events":[]}', '{"format_version":1,"blocked_sources":{},"events":[],"extra":true}'])
def test_broken_operational_state_is_not_treated_as_an_empty_blocklist(repository, content):
    repository.state_file.parent.mkdir()
    repository.state_file.write_text(content, encoding="utf-8")
    assert_status(retrieve_evidence(RENTAL, [SCT], {}, repository=repository), "ERROR")


def test_failed_atomic_state_write_preserves_old_quarantine(repository, monkeypatch):
    repository.quarantine_source(SCT_SOURCE, actor="test-admin", reason="existing block")
    old = repository.state_file.read_bytes()
    def fail_replace(*args):
        raise OSError("synthetic disk error")
    monkeypatch.setattr(repository_module.os, "replace", fail_replace)
    with pytest.raises(OSError):
        repository.quarantine_source("cea-complaint", actor="test-admin", reason="new block")
    assert repository.state_file.read_bytes() == old
    assert not list(repository.state_file.parent.glob("*.tmp"))
    assert not repository.state_file.with_name(repository.state_file.name + ".lock").exists()


def test_concurrent_state_writer_is_rejected_without_overwrite(repository):
    repository.state_file.parent.mkdir()
    lock = repository.state_file.with_name(repository.state_file.name + ".lock")
    lock.write_text("synthetic active writer", encoding="utf-8")
    with pytest.raises(RepositoryError, match="busy"):
        repository.quarantine_source(SCT_SOURCE, actor="test-admin", reason="test")
    assert not repository.state_file.exists() and lock.exists()


def test_live_change_and_outage_quarantine_affected_sources_only(repository, monkeypatch):
    bundle = load_knowledge_base(repository.directory)
    mock_live_pages(monkeypatch, bundle, changed=SCT_SOURCE, unavailable="cea-complaint")
    results = repository.check_live_sources(actor="test-live-check")
    assert {row["source_id"] for row in results if row["check_status"] != "MATCHED"} == {SCT_SOURCE, "cea-complaint"}
    assert set(repository.source_state()["blocked_sources"]) == {SCT_SOURCE, "cea-complaint"}
    assert_status(retrieve_evidence(RENTAL, [SCT], {}, repository=repository), "NO_RESULTS")
    assert_status(retrieve_evidence(CONSUMER, [CASE], {}, repository=repository), "FOUND")


def test_missing_live_excerpt_is_quarantined_even_if_reported_page_digest_matches(repository, monkeypatch):
    mock_live_pages(monkeypatch, load_knowledge_base(repository.directory), missing=SCT_SOURCE)
    repository.check_live_sources(actor="test-live-check")
    assert SCT_SOURCE in repository.source_state()["blocked_sources"]


def test_recovery_never_releases_quarantine_automatically(repository, monkeypatch):
    repository.quarantine_source(SCT_SOURCE, actor="test-admin", reason="review pending")
    mock_live_pages(monkeypatch, load_knowledge_base(repository.directory))
    assert all(row["check_status"] == "MATCHED" for row in repository.check_live_sources(actor="test-live-check"))
    assert_status(retrieve_evidence(RENTAL, [SCT], {}, repository=repository), "NO_RESULTS")
    repository.release_source(SCT_SOURCE, actor="test-admin", reason="fresh source match checked")
    assert repository.source_state()["events"][-1]["action"] == "release"
    assert_status(retrieve_evidence(RENTAL, [SCT], {}, repository=repository), "FOUND")


def test_release_refuses_changed_sources_and_preserves_the_block(repository, monkeypatch):
    repository.quarantine_source(SCT_SOURCE, actor="test-admin", reason="review pending")
    mock_live_pages(monkeypatch, load_knowledge_base(repository.directory), changed=SCT_SOURCE)
    with pytest.raises(RepositoryError, match="must match"):
        repository.release_source(SCT_SOURCE, actor="test-admin", reason="test release")
    assert SCT_SOURCE in repository.source_state()["blocked_sources"]


@pytest.mark.parametrize("field,value", [("evidence_id", "FORGED"), ("source_id", "cea-complaint"), ("url", "https://www.cea.gov.sg/submit-complaint/"), ("source_version", "old-version"), ("review_status", "unreviewed"), ("rule_ids", [CEA]), ("extra", "field")])
def test_citation_validator_rejects_plausible_but_wrong_evidence_metadata(repository, field, value):
    evidence = found(repository)
    evidence[0][field] = value
    with pytest.raises(CitationValidationError):
        validate_citations(RENTAL, [SCT], evidence, [evidence[0]["evidence_id"]], repository=repository)


@pytest.mark.parametrize("citations", [None, [], ["https://www.judiciary.gov.sg/"], ["SCT-ELIG-RESIDENTIAL", "SCT-ELIG-RESIDENTIAL"], ["SCT-ELIG-RESIDENTIAL", "FORGED"], [False]])
def test_citation_list_requires_exact_unique_evidence_ids(repository, citations):
    with pytest.raises(CitationValidationError):
        validate_citations(RENTAL, [SCT], found(repository), citations, repository=repository)


def test_citations_reject_partial_coverage_extra_records_and_duplicates(repository):
    rules = [SCT, "SCT_CLAIM_AMOUNT"]
    evidence = found(repository, rules=rules)
    for records in (evidence[:1], evidence + [evidence[0]]):
        with pytest.raises(CitationValidationError):
            validate_citations(RENTAL, rules, records, [item["evidence_id"] for item in records], repository=repository)
    with pytest.raises(CitationValidationError):
        validate_citations(RENTAL, [SCT], evidence, [item["evidence_id"] for item in evidence], repository=repository)


def test_citation_validator_rechecks_quarantine_after_retrieval(repository):
    evidence = found(repository)
    validator = CitationValidator(repository)
    validator.validate(RENTAL, [SCT], evidence, [evidence[0]["evidence_id"]])
    repository.quarantine_source(SCT_SOURCE, actor="test-admin", reason="newly detected conflict")
    with pytest.raises(CitationValidationError):
        validator.validate(RENTAL, [SCT], evidence, [evidence[0]["evidence_id"]])


def test_version_updates_are_visible_without_a_stale_evidence_cache(repository, tmp_path):
    evidence = found(repository)
    candidate = tmp_path / "candidate"
    shutil.copytree(repository.directory, candidate)
    change_version(candidate, "synthetic-test-version-2")
    assert repository.update_from(candidate, verify_live=False) == "synthetic-test-version-2"
    fresh = found(repository)
    assert fresh[0]["source_version"] == "synthetic-test-version-2"
    for records, expected in ((evidence, None), (fresh, "kb-2026-11-01.1")):
        with pytest.raises(CitationValidationError):
            validate_citations(RENTAL, [SCT], records, [records[0]["evidence_id"]], expected_source_version=expected, repository=repository)


def test_invalid_candidate_does_not_replace_a_valid_repository(repository, tmp_path):
    original = repository.directory
    candidate = tmp_path / "invalid-candidate"
    shutil.copytree(original, candidate)
    (candidate / "passages.jsonl").write_text("{", encoding="utf-8")
    with pytest.raises(RepositoryError):
        repository.update_from(candidate, verify_live=False)
    assert repository.directory == original
    found(repository)


def test_source_update_keeps_existing_quarantine(repository, tmp_path):
    repository.quarantine_source(SCT_SOURCE, actor="test-admin", reason="still under review")
    candidate = tmp_path / "next-bundle"
    shutil.copytree(repository.directory, candidate)
    change_version(candidate, "synthetic-test-version-2")
    repository.update_from(candidate, verify_live=False)
    assert_status(retrieve_evidence(RENTAL, [SCT], {}, repository=repository), "NO_RESULTS")


def test_content_change_without_version_bump_is_rejected(repository, tmp_path):
    candidate = tmp_path / "same-version"
    shutil.copytree(repository.directory, candidate)
    edit_json(candidate, "action_templates.json", lambda data: data["templates"][0].update(channel="Synthetic modified template"))
    with pytest.raises(RepositoryError, match="new source_version"):
        repository.update_from(candidate, verify_live=False)


def test_update_performs_live_verification_by_default(repository, tmp_path, monkeypatch):
    candidate = tmp_path / "checked-candidate"
    shutil.copytree(repository.directory, candidate)
    mock_live_pages(monkeypatch, load_knowledge_base(candidate), changed=SCT_SOURCE)
    with pytest.raises(RepositoryError, match="live source checks"):
        repository.update_from(candidate)
    mock_live_pages(monkeypatch, load_knowledge_base(candidate))
    repository.update_from(candidate)
    assert repository.directory == candidate.resolve()


def test_operational_state_cannot_pollute_the_five_source_files(repository):
    with pytest.raises(RepositoryError, match="outside"):
        EvidenceRepository(repository.directory, state_file=repository.directory / "state.json")


def test_retriever_cli_reports_found_and_empty_request(repository):
    args = [sys.executable, "-m", "rag.retriever", RENTAL, "--directory", str(repository.directory), "--state-file", str(repository.state_file)]
    result = subprocess.run(args + ["--rule-id", SCT], cwd=ROOT, capture_output=True, text=True)
    assert result.returncode == 0, result.stderr
    assert_status(json.loads(result.stdout), "FOUND")
    result = subprocess.run(args, cwd=ROOT, capture_output=True, text=True)
    assert result.returncode == 1
    assert_status(json.loads(result.stdout), "NO_RESULTS")


def test_source_admin_cli_preserves_canonical_data(repository):
    result = subprocess.run([sys.executable, "-m", "rag.repository", "quarantine", "--source", SCT_SOURCE,
                             "--actor", "test-admin", "--reason", "synthetic test", "--directory", str(repository.directory),
                             "--state-file", str(repository.state_file)], cwd=ROOT, capture_output=True, text=True)
    assert result.returncode == 0, result.stderr
    assert SCT_SOURCE in json.loads(result.stdout)["blocked_sources"]
    load_knowledge_base(repository.directory)


def test_shared_evidence_is_deduplicated_and_keeps_each_requested_rule(repository):
    path = repository.directory / "passages.jsonl"
    passages = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]
    alias = "SYNTHETIC_SHARED_RULE"
    passages[0]["rule_ids"].append(alias)
    path.write_text("".join(json.dumps(p) + "\n" for p in passages), encoding="utf-8")
    def add_rule(data):
        rule = copy.deepcopy(data["rules"][0])
        rule["rule_id"] = alias
        data["rules"].append(rule)
    edit_json(repository.directory, "rule_evidence_map.json", add_rule)
    rules = [alias, SCT]
    evidence = found(repository, rules=rules)
    assert len(evidence) == 1 and evidence[0]["rule_ids"] == rules
    evidence[0]["rule_ids"].reverse()
    validate_citations(RENTAL, rules, evidence, [evidence[0]["evidence_id"]], repository=repository)


def test_each_rule_requires_its_entire_mapped_evidence_set(repository):
    path = repository.directory / "passages.jsonl"
    passages = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]
    passages[1]["rule_ids"].append(SCT)
    path.write_text("".join(json.dumps(p) + "\n" for p in passages), encoding="utf-8")
    edit_json(repository.directory, "rule_evidence_map.json", lambda data: data["rules"][0]["evidence_ids"].append("SCT-ELIG-AMOUNT"))
    evidence = found(repository)
    assert len(evidence) == 2
    with pytest.raises(CitationValidationError):
        validate_citations(RENTAL, [SCT], evidence[:1], [evidence[0]["evidence_id"]], repository=repository)


def test_in_place_version_changes_are_observed_on_the_next_read(repository):
    old = found(repository)
    change_version(repository.directory, "synthetic-in-place-version")
    assert found(repository)[0]["source_version"] == "synthetic-in-place-version"
    with pytest.raises(CitationValidationError):
        validate_citations(RENTAL, [SCT], old, [old[0]["evidence_id"]], repository=repository)


def test_historical_page_hash_cannot_replace_the_current_source_review(repository, monkeypatch):
    bundle = load_knowledge_base(repository.directory)
    source_id = "cea-dispute-resolution"
    current_time = bundle["sources"][source_id]["reviewed_at"]
    old = next(row for row in bundle["review_log"].values() if row["source_id"] == source_id and row["reviewed_at"] != current_time)
    mock_live_pages(monkeypatch, bundle)
    matching_capture = repository_module.capture
    def old_capture(url):
        result = matching_capture(url)
        if url == bundle["sources"][source_id]["url"]:
            result["content_sha256"] = old["content_sha256"]
        return result
    monkeypatch.setattr(repository_module, "capture", old_capture)
    repository.check_live_sources(actor="test-live-check")
    assert source_id in repository.source_state()["blocked_sources"]


def test_release_rejects_a_bundle_changed_during_the_live_check(repository, monkeypatch):
    repository.quarantine_source(SCT_SOURCE, actor="test-admin", reason="pending check")
    mock_live_pages(monkeypatch, load_knowledge_base(repository.directory))
    matching_capture = repository_module.capture
    def changed_capture(url):
        result = matching_capture(url)
        change_version(repository.directory, "synthetic-during-release")
        return result
    monkeypatch.setattr(repository_module, "capture", changed_capture)
    with pytest.raises(RepositoryError, match="changed during release"):
        repository.release_source(SCT_SOURCE, actor="test-admin", reason="attempt release")
    assert SCT_SOURCE in repository.source_state()["blocked_sources"]


def test_live_match_does_not_promote_unreviewed_source_metadata(repository, monkeypatch):
    downgrade_source(repository.directory, SCT_SOURCE, "unreviewed")
    bundle = load_knowledge_base(repository.directory)
    mock_live_pages(monkeypatch, bundle)
    results = repository.check_live_sources(actor="test-live-check")
    assert next(row["check_status"] for row in results if row["source_id"] == SCT_SOURCE) == "UNVERIFIED"
    assert load_knowledge_base(repository.directory)["sources"][SCT_SOURCE]["status"] == "unreviewed"
    with pytest.raises(RepositoryError):
        repository.release_source(SCT_SOURCE, actor="test-admin", reason="HTTP success alone is not a review")


@pytest.mark.parametrize("case_type,rules,evidence,citations", [(RENTAL, [], [], []), ("employment", [SCT], [], []), (RENTAL, [SCT], None, None)])
def test_citation_validation_never_treats_an_empty_or_invalid_claim_as_supported(repository, case_type, rules, evidence, citations):
    with pytest.raises(CitationValidationError):
        validate_citations(case_type, rules, evidence, citations, repository=repository)


def test_retriever_cli_rejects_state_path_inside_corpus_without_traceback(repository):
    result = subprocess.run([sys.executable, "-m", "rag.retriever", RENTAL, "--rule-id", SCT,
                             "--directory", str(repository.directory), "--state-file", str(repository.directory / "bad-state.json")],
                            cwd=ROOT, capture_output=True, text=True)
    assert result.returncode == 2
    assert_status(json.loads(result.stdout), "ERROR")
    assert "Traceback" not in result.stderr
