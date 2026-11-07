"""Task 16 protocol examples and consequential cross-reference regressions."""

import json
from pathlib import Path

import pytest
from jsonschema import ValidationError

from shared.validate_action_plan import context_revision, validate_action_plan

EXAMPLES = Path(__file__).resolve().parents[2] / "shared/examples/task16_action_plan.json"


@pytest.fixture
def examples():
    entries = json.loads(EXAMPLES.read_text(encoding="utf-8"))["examples"]
    return {entry["id"]: entry for entry in entries}


def test_wire_examples_cover_the_design_states(examples):
    assert {row["response"]["state"] for row in examples.values()} == {
        "CONFIRM", "ASK", "READY", "LIMITED", "UNAVAILABLE"
    }
    for row in examples.values():
        validate_action_plan(row["response"], request=row["request"])


def test_changed_facts_reject_an_older_result(examples):
    row = examples["demo-rental"]
    old_revision = row["response"]["revision"]
    row["request"]["context"]["facts"]["break_clause_present"] = False
    assert context_revision(row["request"]["context"]) != old_revision
    with pytest.raises(ValidationError, match="changed confirmed facts"):
        validate_action_plan(row["response"], request=row["request"])


def test_question_cannot_repeat_unknown_or_use_wrong_case_field(examples):
    row = examples["demo-question"]
    question = row["response"]["question"]
    question["field"] = "dispute_with"
    with pytest.raises(ValidationError):
        validate_action_plan(row["response"])
    question["field"] = "purchase_purpose"
    context = row["response"]["context"]
    context["facts"]["purchase_purpose"] = "unknown"
    row["response"]["revision"] = context_revision(context)
    with pytest.raises(ValidationError, match="repeats a supplied fact"):
        validate_action_plan(row["response"])


def test_interpretation_cannot_return_action_before_confirmation(examples):
    row = examples["demo-consumer"]
    interpret = examples["demo-interpret"]["request"]
    row["response"]["request_id"] = interpret["request_id"]
    with pytest.raises(ValidationError, match="Interpretation cannot produce an action"):
        validate_action_plan(row["response"], request=interpret)


@pytest.mark.parametrize(
    ("edit", "message"),
    [
        (lambda plan: plan["evidence"][0].update(quote="Changed excerpt"), "digest mismatch"),
        (lambda plan: plan["contacts"][0].update(value="https://www.case.org.sg.evil.test/"), "official URL"),
        (lambda plan: plan["contacts"][0].update(purpose="agency_conduct"), "Wrong contact purpose"),
        (lambda plan: plan["primary_action"]["evidence_ids"].append("unlinked"), "Unknown evidence ID"),
        (
            lambda plan: plan["legal_basis"].append({
                "claim_id": "next", "evidence_id": plan["primary_action"]["evidence_ids"][0]
            }),
            "statutory text",
        ),
        (lambda plan: plan["draft"].update(body="An unresolved {different_slot}."), "Draft slots"),
    ],
)
def test_plan_rejects_broken_claim_contact_and_draft_links(examples, edit, message):
    row = examples["demo-consumer"]
    edit(row["response"]["plan"])
    with pytest.raises(ValidationError, match=message):
        validate_action_plan(row["response"], request=row["request"])
