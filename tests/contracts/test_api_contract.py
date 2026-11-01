"""Positive and adversarial contract checks; no legal routing is exercised."""
import copy
import json
import subprocess
import sys
from pathlib import Path

import pytest
from jsonschema import Draft202012Validator, ValidationError
from referencing.exceptions import NoSuchResource

from shared.validate_contracts import EXAMPLES_DIR, SHARED_DIR, _schemas, get_validator, validate

ROOT = SHARED_DIR.parent
MANIFEST = json.loads((EXAMPLES_DIR / "manifest.json").read_text(encoding="utf-8"))


def example(name):
    return json.loads((EXAMPLES_DIR / f"{name}.json").read_text(encoding="utf-8"))


def supported():
    return example("supported_path_response")


def evidence():
    return supported()["evidence"][0]


@pytest.mark.parametrize("entry", MANIFEST, ids=lambda entry: entry["file"])
def test_shared_examples_are_accepted(entry):
    payload = json.loads((EXAMPLES_DIR / entry["file"]).read_text(encoding="utf-8"))
    validate(payload, entry["definition"])


def test_schema_documents_are_valid_and_default_is_navigation_response():
    contract, evidence_schema, registry = _schemas()
    for schema in (contract, evidence_schema):
        Draft202012Validator.check_schema(schema)
    Draft202012Validator(contract, registry=registry).validate(supported())


def test_all_four_navigation_statuses_have_fixtures():
    actual = {
        example(Path(entry["file"]).stem)["status"]
        for entry in MANIFEST if entry["definition"] == "navigate_response"
    }
    assert actual == {"NEED_CLARIFICATION", "SUPPORTED_PATH", "REFER_TO_OFFICIAL", "ERROR"}


@pytest.mark.parametrize("field", ["api_version", "case_type", "answers"])
def test_request_requires_all_envelope_fields(field):
    payload = example("rental_deposit_request")
    del payload[field]
    with pytest.raises(ValidationError):
        validate(payload, "navigate_request")


@pytest.mark.parametrize("field,value", [
    ("api_version", "2.0"), ("api_version", 1), ("api_version", None),
    ("case_type", "employment"), ("case_type", "RENTAL_DEPOSIT"),
    ("answers", None), ("answers", []), ("answers", "unknown"),
    ("unexpected", True),
])
def test_request_rejects_invalid_envelope(field, value):
    payload = example("rental_deposit_request")
    payload[field] = value
    with pytest.raises(ValidationError):
        validate(payload, "navigate_request")


@pytest.mark.parametrize("answers", [
    {}, {"claim_amount_sgd": None}, {"claim_amount_sgd": None, "respondent_in_singapore": "unknown"},
    {"respondent_in_singapore": False},
])
def test_partial_unknown_and_false_answers_remain_distinct_and_unmodified(answers):
    payload = {"api_version": "1.0", "case_type": "rental_deposit", "answers": answers}
    original = copy.deepcopy(payload)
    validate(payload, "navigate_request")
    assert payload == original


@pytest.mark.parametrize("field", ["api_version", "rule_version", "source_version", "status", "questions", "action_card", "evidence", "warnings"])
def test_response_requires_all_fixed_fields(field):
    payload = supported()
    del payload[field]
    with pytest.raises(ValidationError):
        validate(payload)


@pytest.mark.parametrize("field,value", [
    ("status", "SUCCESS"), ("status", "MOCK_ONLY"), ("status", None),
    ("api_version", "1.1"), ("rule_version", ""), ("source_version", " "),
    ("questions", None), ("evidence", {}), ("warnings", "error"),
    ("action_card", "unknown"), ("error", "extra field"),
])
def test_response_rejects_invalid_fields_and_unsupported_statuses(field, value):
    payload = supported()
    payload[field] = value
    with pytest.raises(ValidationError):
        validate(payload)


@pytest.mark.parametrize("field", ["evidence_id", "source_id", "rule_ids", "url", "review_status", "source_version"])
def test_every_evidence_record_requires_all_six_fields(field):
    payload = evidence()
    del payload[field]
    with pytest.raises(ValidationError):
        validate(payload, "evidence")


@pytest.mark.parametrize("field,value", [
    ("evidence_id", ""), ("source_id", None), ("source_version", " "),
    ("rule_ids", []), ("rule_ids", [""]), ("rule_ids", ["r1", "r1"]),
    ("url", ""), ("url", "not a URL"), ("url", "javascript:alert(1)"),
    ("url", "ftp://example.invalid/source"), ("url", "https:///source"),
    ("url", "https://example.invalid/a b"), ("url", "https://example.invalid\n"),
    ("review_status", "approved_by_government"), ("extra", "field"),
])
def test_evidence_rejects_incomplete_or_malformed_metadata(field, value):
    payload = evidence()
    payload[field] = value
    with pytest.raises(ValidationError):
        validate(payload, "evidence")


@pytest.mark.parametrize("review_status", ["unreviewed", "quarantined", "verified"])
def test_evidence_schema_can_represent_actual_review_states(review_status):
    payload = evidence()
    payload["review_status"] = review_status
    validate(payload, "evidence")


@pytest.mark.parametrize("review_status", ["unreviewed", "quarantined"])
def test_supported_path_rejects_unusable_evidence(review_status):
    payload = supported()
    payload["evidence"][0]["review_status"] = review_status
    with pytest.raises(ValidationError):
        validate(payload)


@pytest.mark.parametrize("field,value", [("evidence", []), ("action_card", None), ("questions", [{"id": "q", "label": "Question", "input_type": "text", "required": True}])])
def test_supported_path_needs_evidence_card_and_no_followup(field, value):
    payload = supported()
    payload[field] = value
    with pytest.raises(ValidationError):
        validate(payload)


@pytest.mark.parametrize("section", ["case_summary", "potential_channels", "conditions", "steps", "document_checklist", "unresolved_questions", "citations"])
def test_action_card_requires_the_seven_agreed_sections(section):
    payload = supported()
    del payload["action_card"][section]
    with pytest.raises(ValidationError):
        validate(payload)


def test_action_card_rejects_an_unagreed_eighth_section():
    payload = supported()
    payload["action_card"]["eligibility_decision"] = True
    with pytest.raises(ValidationError):
        validate(payload)


def test_clarification_requires_a_question_and_no_card():
    payload = example("need_clarification_response")
    payload["questions"] = []
    with pytest.raises(ValidationError):
        validate(payload)
    payload = example("need_clarification_response")
    payload["action_card"] = supported()["action_card"]
    with pytest.raises(ValidationError):
        validate(payload)


@pytest.mark.parametrize("field,value", [("id", ""), ("label", None), ("input_type", ""), ("required", "true"), ("new_field", 1)])
def test_followup_question_rejects_invalid_shapes(field, value):
    payload = example("need_clarification_response")
    payload["questions"][0][field] = value
    with pytest.raises(ValidationError):
        validate(payload)


@pytest.mark.parametrize("name", ["refer_to_official_response", "error_response"])
def test_referral_and_error_work_without_evidence_but_require_a_message(name):
    payload = example(name)
    validate(payload)
    assert payload["evidence"] == [] and payload["action_card"] is None
    payload["warnings"] = []
    with pytest.raises(ValidationError):
        validate(payload)


def test_referral_card_requires_reviewed_evidence_too():
    payload = example("refer_to_official_response")
    payload["action_card"] = supported()["action_card"]
    with pytest.raises(ValidationError):
        validate(payload)


@pytest.mark.parametrize("case_types", [["rental_deposit"], ["rental_deposit", "rental_deposit"], ["rental_deposit", "employment"]])
def test_case_types_endpoint_cannot_drop_duplicate_or_expand_cases(case_types):
    with pytest.raises(ValidationError):
        validate({"api_version": "1.0", "case_types": case_types}, "case_types_response")


def test_real_task1_health_response_matches_shared_contract():
    from backend.app import create_app

    response = create_app().test_client().get("/api/health")
    assert response.status_code == 200
    validate(response.get_json(), "health_response")


def test_rag_boundary_preserves_unknown_facts_and_uses_the_same_evidence_schema():
    request = example("retrieval_request")
    original = copy.deepcopy(request)
    validate(request, "retrieval_request")
    assert request == original and request["facts"]["claim_amount_sgd"] is None
    response = example("retrieval_response")
    del response["evidence"][0]["source_id"]
    with pytest.raises(ValidationError):
        validate(response, "retrieval_response")


def test_schema_registry_refuses_remote_fetches():
    _, _, registry = _schemas()
    with pytest.raises(NoSuchResource):
        registry.get_or_retrieve("https://unregistered.invalid/schema.json")


def test_unknown_definition_fails_explicitly():
    with pytest.raises(ValueError, match="Unknown contract definition"):
        get_validator("made_up_schema")


def test_cli_checks_all_examples():
    result = subprocess.run([sys.executable, "-m", "shared.validate_contracts"], cwd=ROOT, capture_output=True, text=True)
    assert result.returncode == 0, result.stderr
    assert result.stdout.count("PASS ") == len(MANIFEST)


def test_cli_reports_invalid_json_with_nonzero_exit(tmp_path):
    path = tmp_path / "invalid.json"
    path.write_text('{"status": "SUCCESS"}', encoding="utf-8")
    result = subprocess.run([sys.executable, "-m", "shared.validate_contracts", str(path)], cwd=ROOT, capture_output=True, text=True)
    assert result.returncode == 1
    assert "FAIL" in result.stderr
