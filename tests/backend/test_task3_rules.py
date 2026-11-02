"""Task 3: no rule activation, evidence traceability and failure-safe checks."""
import copy
import json
import pytest
from backend.rules import FILES, RuleConfigurationError, load_rule_configurations
from rag.import_knowledge_base import load_knowledge_base


@pytest.fixture
def config_dir(tmp_path):
    from backend.rules import DIRECTORY
    for name in FILES:
        (tmp_path / name).write_text((DIRECTORY / name).read_text(encoding="utf-8"), encoding="utf-8")
    return tmp_path


def mutate(directory, filename, fn):
    path = directory / filename
    doc = json.loads(path.read_text(encoding="utf-8"))
    fn(doc)
    path.write_text(json.dumps(doc), encoding="utf-8")


def test_all_three_categories_and_25_disabled_checks():
    configs = load_rule_configurations()
    assert set(configs) == {"rental", "consumer", "boundary"}
    assert {k:len(v["checks"]) for k,v in configs.items()} == {"rental":8,"consumer":9,"boundary":8}
    assert all(not c["runtime_enabled"] and c["threshold"] is None
               for config in configs.values() for c in config["checks"])
    assert all(config["unknown_policy"] == "clarify_or_refer" for config in configs.values())


def test_missing_evidence_stays_unverified():
    configs = load_rule_configurations()
    unknown = [check for cfg in configs.values() for check in cfg["checks"] if check["rule_id"] is None]
    assert unknown
    assert all(x["evidence_ids"] == [] and x["mapping_status"] == "unverified" for x in unknown)


@pytest.mark.parametrize("filename", FILES)
def test_unexpected_activation_is_rejected(config_dir, filename):
    mutate(config_dir, filename, lambda d: d["checks"][0].update(runtime_enabled=True))
    with pytest.raises(RuleConfigurationError, match="disabled"):
        load_rule_configurations(config_dir)


def test_fabricated_threshold_is_rejected(config_dir):
    mutate(config_dir, "rental.json", lambda d: d["checks"][0].update(threshold=20000))
    with pytest.raises(RuleConfigurationError, match="disabled"):
        load_rule_configurations(config_dir)


def test_incorrect_rule_evidence_mapping_is_rejected(config_dir):
    mutate(config_dir, "consumer.json", lambda d: d["checks"][0].update(evidence_ids=["fake-evidence"]))
    with pytest.raises(RuleConfigurationError, match="evidence ID mismatch"):
        load_rule_configurations(config_dir)


def test_unknown_rule_id_is_rejected(config_dir):
    mutate(config_dir, "boundary.json", lambda d: d["checks"][0].update(rule_id="NO_SUCH_RULE"))
    with pytest.raises(RuleConfigurationError, match="missing or unexpectedly active"):
        load_rule_configurations(config_dir)


def test_case_fields_must_come_from_frontend_schema(config_dir):
    mutate(config_dir, "consumer.json", lambda d: d["checks"][0].update(input_fields=["invented_field"]))
    with pytest.raises(RuleConfigurationError, match="field not declared"):
        load_rule_configurations(config_dir)


def test_source_version_must_match(config_dir):
    mutate(config_dir, "rental.json", lambda d: d.update(source_version="invented"))
    with pytest.raises(RuleConfigurationError, match="source_version"):
        load_rule_configurations(config_dir)


def test_unknown_policy_cannot_be_coerced_to_false(config_dir):
    mutate(config_dir, "boundary.json", lambda d: d.update(unknown_policy="treat_as_false"))
    with pytest.raises(RuleConfigurationError, match="unknown policy"):
        load_rule_configurations(config_dir)


def test_unreviewed_or_quarantined_evidence_is_rejected():
    kb = copy.deepcopy(load_knowledge_base())
    linked = load_rule_configurations()["rental"]["checks"][0]
    eid = linked["evidence_ids"][0]
    kb["passages"][eid]["review_status"] = "quarantined"
    with pytest.raises(RuleConfigurationError, match="unreviewed or quarantined"):
        load_rule_configurations(kb=kb)


def test_no_runtime_evaluation_is_added():
    from backend import app
    client = app.create_app().test_client()
    r = client.post("/api/navigate", json={
        "api_version":"1.0","case_type":"rental_deposit","answers":{"claim_amount_sgd":100}
    })
    assert r.status_code == 200
    assert r.get_json()["status"] in {"NEED_CLARIFICATION", "REFER_TO_OFFICIAL"}
    assert r.get_json()["action_card"] is None
    assert r.get_json()["evidence"] == []
