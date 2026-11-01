"""Task 3 ingestion checks. Test mutations are invalid fixtures, not source reviews."""
import copy
import csv
import hashlib
import json
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

from rag import import_knowledge_base as importer
from rag.import_knowledge_base import DEFAULT_KB, FILES, KnowledgeBaseError, api_evidence, import_snapshot, load_knowledge_base
from rag.source_review import VisibleText, normalize_space
from shared.validate_contracts import validate

ROOT = DEFAULT_KB.parents[1]


@pytest.fixture
def kb_dir(tmp_path):
    destination = tmp_path / "knowledge_base"
    shutil.copytree(DEFAULT_KB, destination)
    return destination


def change_csv(directory, name, change):
    path = directory / name
    with path.open(encoding="utf-8", newline="") as stream:
        reader = csv.DictReader(stream)
        fields, rows = reader.fieldnames, list(reader)
    change(rows)
    with path.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def change_passages(directory, change):
    path = directory / "passages.jsonl"
    records = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]
    change(records)
    path.write_text("".join(json.dumps(record) + "\n" for record in records), encoding="utf-8")


def change_json(directory, name, change):
    path = directory / name
    content = json.loads(path.read_text(encoding="utf-8"))
    change(content)
    path.write_text(json.dumps(content), encoding="utf-8")


def test_live_prepared_bundle_has_five_files_and_traceable_content():
    assert {path.name for path in DEFAULT_KB.iterdir()} == FILES
    bundle = load_knowledge_base()
    assert len(bundle["sources"]) == 5
    assert len(bundle["passages"]) == 26
    assert len(bundle["rules"]) == 26
    assert len(bundle["templates"]) == 5
    assert all(not rule["runtime_enabled"] for rule in bundle["rules"].values())
    for passage in bundle["passages"].values():
        assert passage["url"] == bundle["sources"][passage["source_id"]]["url"]
        for rule_id in passage["rule_ids"]:
            assert passage["evidence_id"] in bundle["rules"][rule_id]["evidence_ids"]


def test_every_projected_record_matches_the_existing_shared_evidence_schema():
    for passage in load_knowledge_base()["passages"].values():
        projected = api_evidence(passage)
        assert set(projected) == {"evidence_id", "source_id", "rule_ids", "url", "review_status", "source_version"}
        validate(projected, "evidence")


@pytest.mark.parametrize("filename", sorted(FILES))
def test_missing_required_file_is_rejected(kb_dir, filename):
    (kb_dir / filename).unlink()
    with pytest.raises(KnowledgeBaseError, match="five fixed files"):
        load_knowledge_base(kb_dir)


def test_duplicate_evidence_id_is_rejected(kb_dir):
    change_passages(kb_dir, lambda records: records.append(copy.deepcopy(records[0])))
    with pytest.raises(KnowledgeBaseError, match="duplicate evidence_id"):
        load_knowledge_base(kb_dir)


def test_duplicate_source_id_is_rejected(kb_dir):
    change_csv(kb_dir, "sources.csv", lambda rows: rows[1].update(source_id=rows[0]["source_id"]))
    with pytest.raises(KnowledgeBaseError, match="duplicate source_id"):
        load_knowledge_base(kb_dir)


@pytest.mark.parametrize("url", ["", "https://untrusted.invalid/source", "http://www.cea.gov.sg/source", "https://user@www.cea.gov.sg/source", "https://www.cea.gov.sg:8443/source"])
def test_blank_or_untrusted_source_url_is_rejected(kb_dir, url):
    change_csv(kb_dir, "sources.csv", lambda rows: rows[0].update(url=url))
    with pytest.raises(KnowledgeBaseError, match="URL"):
        load_knowledge_base(kb_dir)


def test_passage_cannot_point_to_a_different_source_url(kb_dir):
    change_passages(kb_dir, lambda rows: rows[0].update(url="https://www.cea.gov.sg/submit-complaint/"))
    with pytest.raises(KnowledgeBaseError, match="URL differs"):
        load_knowledge_base(kb_dir)


def test_passage_cannot_reference_a_missing_source(kb_dir):
    change_passages(kb_dir, lambda rows: rows[0].update(source_id="missing-source"))
    with pytest.raises(KnowledgeBaseError, match="unknown source"):
        load_knowledge_base(kb_dir)


@pytest.mark.parametrize("status", ["unreviewed", "quarantined"])
def test_unreviewed_or_quarantined_source_cannot_back_verified_passages(kb_dir, status):
    change_csv(kb_dir, "sources.csv", lambda rows: rows[0].update(status=status))
    with pytest.raises(KnowledgeBaseError, match="unreviewed or quarantined source"):
        load_knowledge_base(kb_dir)


def test_verified_source_requires_actual_review_metadata(kb_dir):
    change_csv(kb_dir, "sources.csv", lambda rows: rows[0].update(reviewed_by=""))
    with pytest.raises(KnowledgeBaseError, match="matching successful review"):
        load_knowledge_base(kb_dir)


def test_verified_review_cannot_record_failed_http_status(kb_dir):
    change_csv(kb_dir, "source_review_log.csv", lambda rows: rows[0].update(http_status="403"))
    with pytest.raises(KnowledgeBaseError, match="HTTP 200"):
        load_knowledge_base(kb_dir)


@pytest.mark.parametrize("timestamp", ["not-a-date", "2026-11-01T10:00:00", "2999-01-01T00:00:00+00:00"])
def test_invalid_naive_or_future_review_dates_are_rejected(kb_dir, timestamp):
    change_csv(kb_dir, "source_review_log.csv", lambda rows: rows[0].update(reviewed_at=timestamp))
    with pytest.raises(KnowledgeBaseError, match="timestamp"):
        load_knowledge_base(kb_dir)


def test_passage_source_version_mismatch_is_rejected(kb_dir):
    change_passages(kb_dir, lambda rows: rows[0].update(source_version="wrong-version"))
    with pytest.raises(KnowledgeBaseError, match="source_version mismatch"):
        load_knowledge_base(kb_dir)


def test_template_and_rule_bundle_versions_must_agree(kb_dir):
    change_json(kb_dir, "action_templates.json", lambda data: data.update(source_version="wrong-version"))
    with pytest.raises(KnowledgeBaseError, match="source_version mismatch"):
        load_knowledge_base(kb_dir)


def test_missing_rule_mapping_is_rejected(kb_dir):
    change_json(kb_dir, "rule_evidence_map.json", lambda data: data["rules"].pop(0))
    with pytest.raises(KnowledgeBaseError, match="reciprocal mapping"):
        load_knowledge_base(kb_dir)


def test_rule_cannot_refer_to_missing_evidence(kb_dir):
    change_json(kb_dir, "rule_evidence_map.json", lambda data: data["rules"][0]["evidence_ids"].append("MISSING"))
    with pytest.raises(KnowledgeBaseError, match="missing evidence"):
        load_knowledge_base(kb_dir)


def test_rule_cannot_change_case_scope_beyond_its_evidence(kb_dir):
    change_json(kb_dir, "rule_evidence_map.json", lambda data: data["rules"][0].update(case_types=["consumer_complaint"]))
    with pytest.raises(KnowledgeBaseError, match="scope conflicts"):
        load_knowledge_base(kb_dir)


def test_unverified_passage_cannot_make_a_rule_usable(kb_dir):
    change_passages(kb_dir, lambda rows: rows[0].update(review_status="unreviewed"))
    with pytest.raises(KnowledgeBaseError, match="unverified evidence"):
        load_knowledge_base(kb_dir)


def test_unreviewed_rule_cannot_be_runtime_enabled(kb_dir):
    change_json(kb_dir, "rule_evidence_map.json", lambda data: data["rules"][0].update(review_status="unreviewed", runtime_enabled=True))
    with pytest.raises(KnowledgeBaseError, match="cannot be enabled"):
        load_knowledge_base(kb_dir)


def test_unverified_records_can_remain_as_disabled_review_material(kb_dir):
    def downgrade_passage(rows):
        rows[0]["review_status"] = "unreviewed"
    change_passages(kb_dir, downgrade_passage)
    change_json(kb_dir, "rule_evidence_map.json", lambda data: data["rules"][0].update(review_status="unreviewed", runtime_enabled=False))
    change_json(kb_dir, "action_templates.json", lambda data: data["templates"][0].update(review_status="unreviewed"))
    bundle = load_knowledge_base(kb_dir)
    assert bundle["rules"]["SCT_RESIDENTIAL_SCOPE"]["runtime_enabled"] is False


def test_edited_excerpt_cannot_reuse_the_old_review_digest(kb_dir):
    def edit(rows):
        rows[0]["text"] = "Unreviewed replacement text"
        rows[0]["excerpt_sha256"] = hashlib.sha256(rows[0]["text"].encode()).hexdigest()
    change_passages(kb_dir, edit)
    with pytest.raises(KnowledgeBaseError, match="not recorded in source review"):
        load_knowledge_base(kb_dir)


def test_excerpt_digest_must_match_the_stored_text(kb_dir):
    change_passages(kb_dir, lambda rows: rows[0].update(excerpt_sha256="0" * 64))
    with pytest.raises(KnowledgeBaseError, match="excerpt hash mismatch"):
        load_knowledge_base(kb_dir)


def test_template_cannot_cite_missing_evidence(kb_dir):
    change_json(kb_dir, "action_templates.json", lambda data: data["templates"][0]["steps"][0]["evidence_ids"].append("MISSING"))
    with pytest.raises(KnowledgeBaseError, match="missing evidence"):
        load_knowledge_base(kb_dir)


def test_agent_template_cannot_use_unrelated_consumer_evidence(kb_dir):
    change_json(kb_dir, "action_templates.json", lambda data: data["templates"][1]["steps"][0].update(evidence_ids=["CASE-PERSONAL"]))
    with pytest.raises(KnowledgeBaseError, match="wrong case"):
        load_knowledge_base(kb_dir)


def test_verified_template_cannot_cite_quarantined_evidence(kb_dir):
    change_passages(kb_dir, lambda rows: rows[-1].update(review_status="quarantined"))
    change_json(kb_dir, "rule_evidence_map.json", lambda data: data["rules"][-1].update(review_status="quarantined"))
    with pytest.raises(KnowledgeBaseError, match="unverified evidence"):
        load_knowledge_base(kb_dir)


def test_malformed_json_and_duplicate_keys_fail_explicitly(kb_dir):
    path = kb_dir / "action_templates.json"
    path.write_text('{"source_version":"a","source_version":"b"}', encoding="utf-8")
    with pytest.raises(KnowledgeBaseError, match="duplicate JSON key"):
        load_knowledge_base(kb_dir)
    path.write_text("{", encoding="utf-8")
    with pytest.raises(KnowledgeBaseError, match="cannot read"):
        load_knowledge_base(kb_dir)


def test_export_is_a_checked_snapshot_and_preserves_existing_output(tmp_path):
    output = tmp_path / "validated.json"
    bundle = import_snapshot(DEFAULT_KB, output)
    assert json.loads(output.read_text(encoding="utf-8")) == bundle
    original = output.read_bytes()
    with pytest.raises(FileExistsError):
        import_snapshot(DEFAULT_KB, output)
    assert output.read_bytes() == original


def test_invalid_data_is_not_exported(kb_dir, tmp_path):
    change_passages(kb_dir, lambda rows: rows.append(rows[0]))
    output = tmp_path / "rejected.json"
    with pytest.raises(KnowledgeBaseError):
        import_snapshot(kb_dir, output)
    assert not output.exists()


def test_export_cannot_pollute_the_five_file_directory(kb_dir):
    with pytest.raises(KnowledgeBaseError, match="outside"):
        import_snapshot(kb_dir, kb_dir / "export.json")
    assert not (kb_dir / "export.json").exists()


def test_live_verification_accepts_only_matching_content_and_present_excerpts(monkeypatch):
    bundle = load_knowledge_base()
    original = copy.deepcopy(bundle)
    def fake_capture(url):
        source = next(s for s in bundle["sources"].values() if s["url"] == url)
        review = next(r for r in bundle["review_log"].values() if r["source_id"] == source["source_id"])
        text = " ".join(p["text"] for p in bundle["passages"].values() if p["source_id"] == source["source_id"])
        return {"url": url, "http_status": 200, "content_sha256": review["content_sha256"], "text": text}
    monkeypatch.setattr(importer, "capture", fake_capture)
    assert len(importer.verify_live_sources(bundle)) == 5
    assert bundle == original
    monkeypatch.setattr(importer, "capture", lambda url: {**fake_capture(url), "content_sha256": "0" * 64})
    with pytest.raises(KnowledgeBaseError, match="content changed"):
        importer.verify_live_sources(bundle)
    monkeypatch.setattr(importer, "capture", lambda url: {**fake_capture(url), "text": "No reviewed excerpts"})
    with pytest.raises(KnowledgeBaseError, match="excerpt is absent"):
        importer.verify_live_sources(bundle)


def test_visible_text_ignores_scripts_and_preserves_inline_words():
    parser = VisibleText()
    parser.feed('<p>Hello <a>source</a>.</p><script>untrusted text</script><style>style text</style>')
    text = normalize_space("".join(parser.parts))
    assert text == "Hello source."


def test_cli_validates_default_bundle():
    result = subprocess.run([sys.executable, "-m", "rag.import_knowledge_base"], cwd=ROOT, capture_output=True, text=True)
    assert result.returncode == 0, result.stderr
    assert "5 sources, 26 passages" in result.stdout


def test_cli_reports_invalid_bundle_without_export(kb_dir, tmp_path):
    change_csv(kb_dir, "sources.csv", lambda rows: rows[0].update(url=""))
    output = tmp_path / "not-created.json"
    result = subprocess.run([sys.executable, "-m", "rag.import_knowledge_base", "--directory", str(kb_dir), "--output", str(output)], cwd=ROOT, capture_output=True, text=True)
    assert result.returncode == 1
    assert "FAIL:" in result.stderr
    assert not output.exists()
