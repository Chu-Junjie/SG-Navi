"""Task 18 independent, synthetic understanding regressions."""
import pytest

from backend.scenario_understanding import (
    interpret_scenario, next_decisive_question, context_revision,
    CONTEXT_VALIDATOR, _amount,
)

@pytest.mark.parametrize("text,subtype", [
    ("I was overcharged at a restaurant in Singapore and the restaurant refuses to correct the bill.", "restaurant_overcharge"),
    ("The restaurant charged me SGD 20 extra and refuses to refund it.", "restaurant_overcharge"),
    ("I was billed twice at a cafe and want to complain.", "duplicate_charge"),
    ("My restaurant bill has a fee I do not understand; can I ask why?", "unclear_charge"),
    ("A shop sold me a faulty phone and refuses to replace it.", "goods_dispute"),
    ("The repair service charged extra and won't refund me.", "services_dispute"),
])
def test_consumer_semantic_variants(text, subtype):
    output = interpret_scenario(text)
    assert output["status"] == "candidate"
    assert output["context"]["case_type"] == "consumer_complaint"
    assert output["context"]["issue_subtype"] == subtype
    CONTEXT_VALIDATOR.validate(output["context"])
    assert "restaurant refuses" not in str(output)
    assert not any(k in output for k in ("description", "raw_text"))

def test_restaurant_explicit_amount_and_denial():
    r = interpret_scenario("The restaurant charged me SGD 20 extra and refuses to refund it.")
    assert r["context"]["facts"]["disputed_amount_cents"] == 2000
    assert r["context"]["facts"]["resolution_attempted"] is True

def test_refund_goal_is_not_inferred_from_simple_denial():
    a = interpret_scenario("A restaurant overcharged me but denied the error.")
    assert a["context"]["goal"] == "understand_options"

def test_explicit_goal():
    assert interpret_scenario("A restaurant overcharged me and I want a refund.")["context"]["goal"] == "seek_refund"
    assert interpret_scenario("I want to complain about my restaurant bill because they charged extra.")["context"]["goal"] == "complain"
    assert interpret_scenario("My landlord kept the rental deposit. I want to file a small claim.")["context"]["goal"] == "prepare_claim"

@pytest.mark.parametrize("description,subtype", [
    ("My landlord has not returned the rental deposit.", "deposit_return"),
    ("My landlord made deductions from the rental deposit for cleaning.", "deposit_deduction"),
    ("I need to leave my rental flat early and the landlord kept my deposit.", "early_exit"),
    ("My work pass was cancelled and I need to leave my rental flat early.", "pass_related_exit"),
    ("My property agent misled me about my rented apartment deposit.", "agent_conduct"),
    ("I have a commission dispute with the estate agency agreement.", "agency_agreement"),
])
def test_rental_scenarios(description, subtype):
    d = interpret_scenario(description)
    assert d["status"] == "candidate"
    assert d["context"]["case_type"] == "rental_deposit"
    assert d["context"]["issue_subtype"] == subtype

@pytest.mark.parametrize("text", [
    "How can I renew my visa for Singapore?",
    "My employer must pay a government security bond for a work permit.",
    "My salary has not been paid.",
    "The weather is lovely.",
])
def test_standalone_or_unrelated_not_forced(text):
    assert interpret_scenario(text)["status"] != "candidate"

def test_mixed_disputes_visible():
    d = interpret_scenario("The landlord kept my rental deposit and a restaurant double charged my card.")
    assert d["status"] == "ambiguous_scope"
    assert d["context"] is None

def test_no_silent_money_choice():
    text = "A restaurant charged SGD 20 extra after I paid SGD 50 for dinner."
    assert _amount(text) is None
    assert "disputed_amount_cents" not in interpret_scenario(text)["context"]["facts"]

def test_questions_are_one_at_a_time_and_skip_supplied_facts():
    r = interpret_scenario("My landlord kept my deposit.")
    c = r["context"]
    assert next_decisive_question(c)["field"] == "dispute_with"
    c["facts"]["dispute_with"] = "landlord"
    assert next_decisive_question(c) is None
    c["facts"]["dispute_with"] = "unknown"
    assert next_decisive_question(c) is None

def test_question_is_route_decisive_for_business_consumer():
    c = interpret_scenario("I was overcharged at a restaurant in Singapore.").get("context")
    assert c is not None
    q = next_decisive_question(c)
    assert q["field"] == "purchase_purpose"
    assert [x["label"] for x in q["options"]][-1] == "Not sure"
    c["facts"]["purchase_purpose"] = "personal"
    assert next_decisive_question(c) is None
    c["facts"]["purchase_purpose"] = "business"
    assert next_decisive_question(c) is None

def test_work_pass_exit_questions_are_conditional():
    c = interpret_scenario("My work pass is expiring and I need to leave my rental flat early.")["context"]
    assert next_decisive_question(c)["field"] == "lease_ended"
    c["facts"]["lease_ended"] = False
    assert next_decisive_question(c)["field"] == "break_clause_present"
    c["facts"]["break_clause_present"] = "unknown"
    assert next_decisive_question(c) is None

def test_revision_changes_with_fact_or_goal_not_summary():
    c = interpret_scenario("My landlord kept my rental deposit.")["context"]
    before = context_revision(c)
    c["summary"] = "Updated user-readable sentence."
    assert context_revision(c) == before
    c["facts"]["dispute_with"] = "agent"
    assert context_revision(c) != before
    assert len(context_revision(c)) == 24

@pytest.mark.parametrize("bad", ["", " " * 10, "x" * 1201, "我的房东不退押金", "A restaurant charge.\x00"])
def test_bad_text_rejected(bad):
    with pytest.raises(ValueError):
        interpret_scenario(bad)
