"""Task 6 provenance/history regressions and rebuild acceptance properties.

All mutations are synthetic and restricted to pytest copies of the checked bundle.
No test manufactures a review in the production knowledge files or fetches a page.
"""
import copy
import csv
import json
import shutil

import pytest

import rag.import_knowledge_base as importer
from rag.citations import CitationValidationError, validate_citations
from rag.import_knowledge_base import DEFAULT_KB, KnowledgeBaseError, import_snapshot, load_knowledge_base
from rag.repository import EvidenceRepository
from rag.retriever import retrieve_evidence
from shared.validate_contracts import validate

RENTAL = "rental_deposit"
CONSUMER = "consumer_complaint"
CEA_SOURCE = "cea-dispute-resolution"
CEA_RULE = "CEA_AGENCY_AGREEMENT"
SCT_SOURCE = "courts-sct-eligibility"
SCT_RULE = "SCT_RESIDENTIAL_SCOPE"


@pytest.fixture
def repository(tmp_path):
    directory = tmp_path / "knowledge"
    shutil.copytree(DEFAULT_KB, directory)
    return EvidenceRepository(directory, state_file=tmp_path / "state" / "quarantine.json")


def change_reviews(repository, mutation):
    path = repository.directory / "source_review_log.csv"
    with path.open(encoding="utf-8", newline="") as stream:
        reader = csv.DictReader(stream)
        fields, rows = reader.fieldnames, list(reader)
    source = load_knowledge_base(repository.directory)["sources"][CEA_SOURCE]
    current = next(row for row in rows if row["source_id"] == CEA_SOURCE
                   and row["reviewed_at"] == source["reviewed_at"]
                   and row["reviewed_by"] == source["reviewed_by"])
    mutation(rows, current)
    with path.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def assert_untrusted_bundle(repository, earlier_evidence):
    result = retrieve_evidence(RENTAL, [CEA_RULE], {}, repository=repository)
    validate(result, "retrieval_response")
    assert result == {"retrieval_status": "ERROR", "evidence": []}
    with pytest.raises(KnowledgeBaseError):
        load_knowledge_base(repository.directory)
    with pytest.raises(CitationValidationError):
        validate_citations(RENTAL, [CEA_RULE], earlier_evidence,
                           [item["evidence_id"] for item in earlier_evidence], repository=repository)


def test_current_review_digest_cannot_fall_back_to_history(repository):
    """An old review must not override the current review's excerpt mismatch."""
    earlier = retrieve_evidence(RENTAL, [CEA_RULE], {}, repository=repository)["evidence"]
    def disagree(_rows, current):
        hashes = current["excerpt_sha256s"].split(";")
        hashes[0] = "0" * 64
        current["excerpt_sha256s"] = ";".join(hashes)
    change_reviews(repository, disagree)
    assert_untrusted_bundle(repository, earlier)


def test_conflicting_current_review_records_are_rejected(repository):
    """Two identities for the same current review cannot approve different pages."""
    earlier = retrieve_evidence(RENTAL, [CEA_RULE], {}, repository=repository)["evidence"]
    def conflict(rows, current):
        alternate = dict(current, review_id="SYNTHETIC-CONFLICTING-CURRENT-REVIEW",
                         content_sha256="0" * 64,
                         change_summary="Synthetic conflicting review; not an actual publisher check")
        rows.append(alternate)
    change_reviews(repository, conflict)
    assert_untrusted_bundle(repository, earlier)


def test_live_import_rejects_historical_hash_even_when_quotes_match(repository, monkeypatch):
    bundle = load_knowledge_base(repository.directory)
    source = bundle["sources"][CEA_SOURCE]
    old = next(row for row in bundle["review_log"].values()
               if row["source_id"] == CEA_SOURCE and row["reviewed_at"] != source["reviewed_at"])

    def synthetic_capture(url):
        metadata = next(s for s in bundle["sources"].values() if s["url"] == url)
        review = next(r for r in bundle["review_log"].values()
                      if r["source_id"] == metadata["source_id"]
                      and r["reviewed_at"] == metadata["reviewed_at"])
        return {"url": url, "http_status": 200,
                "content_sha256": old["content_sha256"] if url == source["url"] else review["content_sha256"],
                "text": " ".join(p["text"] for p in bundle["passages"].values()
                                 if p["source_id"] == metadata["source_id"])}

    monkeypatch.setattr(importer, "capture", synthetic_capture)
    with pytest.raises(KnowledgeBaseError, match="content changed"):
        importer.verify_live_sources(bundle)


@pytest.mark.parametrize("damage", ["missing_block", "missing_history", "changed_reason", "orphan_release"])
def test_quarantine_state_must_agree_with_event_history(repository, damage):
    evidence = retrieve_evidence(RENTAL, [SCT_RULE], {}, repository=repository)["evidence"]
    repository.quarantine_source(SCT_SOURCE, actor="task6-synthetic", reason="synthetic source conflict")
    state = repository.source_state()
    if damage == "missing_block":
        state["blocked_sources"] = {}
    elif damage == "missing_history":
        state["events"] = []
    elif damage == "changed_reason":
        state["blocked_sources"][SCT_SOURCE]["reason"] = "Synthetic inconsistent state entry"
    else:
        state["blocked_sources"] = {}
        state["events"][0]["action"] = "release"
    repository.state_file.write_text(json.dumps(state), encoding="utf-8")
    result = retrieve_evidence(RENTAL, [SCT_RULE], {}, repository=repository)
    assert result == {"retrieval_status": "ERROR", "evidence": []}
    with pytest.raises(CitationValidationError):
        validate_citations(RENTAL, [SCT_RULE], evidence,
                           [item["evidence_id"] for item in evidence], repository=repository)


def test_rebuild_reload_is_deterministic_and_preserves_checked_files(repository, tmp_path):
    before = {p.name: p.read_bytes() for p in repository.directory.iterdir()}
    first = import_snapshot(repository.directory, tmp_path / "first.json")
    second = import_snapshot(repository.directory, tmp_path / "second.json")
    assert first == second == load_knowledge_base(repository.directory)
    assert (tmp_path / "first.json").read_bytes() == (tmp_path / "second.json").read_bytes()
    assert before == {p.name: p.read_bytes() for p in repository.directory.iterdir()}
    assert all(rule["runtime_enabled"] is False for rule in first["rules"].values())
    restarted = EvidenceRepository(repository.directory, state_file=repository.state_file)
    assert retrieve_evidence(RENTAL, [SCT_RULE], {}, repository=repository) == retrieve_evidence(
        RENTAL, [SCT_RULE], {}, repository=restarted)


def test_failed_rebuild_does_not_replace_export_or_lift_quarantine(repository, tmp_path):
    output = tmp_path / "existing-checked-snapshot.json"
    import_snapshot(repository.directory, output)
    original = output.read_bytes()
    repository.quarantine_source(SCT_SOURCE, actor="task6-synthetic", reason="synthetic conflict")
    state_before = repository.state_file.read_bytes()
    candidate = tmp_path / "broken-candidate"
    shutil.copytree(repository.directory, candidate)
    (candidate / "passages.jsonl").write_text("{", encoding="utf-8")
    with pytest.raises(KnowledgeBaseError):
        import_snapshot(candidate, output)
    assert output.read_bytes() == original
    assert repository.state_file.read_bytes() == state_before
    assert retrieve_evidence(RENTAL, [SCT_RULE], {}, repository=repository) == {
        "retrieval_status": "NO_RESULTS", "evidence": []}


def test_real_shared_source_is_consistent_in_both_cases(repository):
    rules = ["SCT_CLAIM_AMOUNT"]
    rental = retrieve_evidence(RENTAL, rules, {}, repository=repository)
    consumer = retrieve_evidence(CONSUMER, rules, {}, repository=repository)
    assert rental["retrieval_status"] == consumer["retrieval_status"] == "FOUND"
    assert rental == consumer
    for case_type in (RENTAL, CONSUMER):
        evidence = copy.deepcopy(rental["evidence"])
        validate_citations(case_type, rules, evidence,
                           [item["evidence_id"] for item in evidence], repository=repository)
