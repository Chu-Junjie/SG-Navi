"""Task 4 standalone rule engine: conservative routing with synthetic test evidence.

This module does not query live RAG or decide eligibility for legal procedures.
The example.invalid evidence may be used only in explicit development simulation.
"""
from copy import deepcopy

from backend.rules import load_rule_configurations
from rag.import_knowledge_base import load_knowledge_base
from shared.validate_contracts import validate
from backend.rag_bridge import retrieve_checked, rule_ids_for_context, referral_source_context

API_VERSION = "1.0"
MOCK_RULE_VERSION = "mock-1"
MOCK_SOURCE_VERSION = "mock-1"

QUESTION_FIELDS = {
    "rental_deposit": (
        ("dispute_with", "Is your dispute with the landlord or an agent?", "text"),
        ("premises_type", "What type of premises is involved?", "text"),
        ("claim_amount_sgd", "What is the disputed amount in SGD?", "number"),
    ),
    "consumer_complaint": (
        ("purchase_type", "What goods or services are involved?", "text"),
        ("purchase_purpose", "Was the purchase for personal or business use?", "text"),
        ("supplier_registered_in_sg", "Is the supplier registered in Singapore?", "select"),
        ("claim_amount_sgd", "What is the disputed amount in SGD?", "number"),
    ),
}

# Evidence intentionally exists only for isolated test simulation, never real advice.
SYNTHETIC_EVIDENCE = {
    "evidence_id": "mock-evidence-task4-1",
    "source_id": "mock-source-task4-1",
    "rule_ids": ["mock-rule-task4-1"],
    "url": "https://example.invalid/task4-fixture",
    "review_status": "verified",
    "source_version": MOCK_SOURCE_VERSION,
}

def envelope(status, questions=None, warnings=None, evidence=None, action_card=None, source_version=None):
    result = {
        "api_version": API_VERSION,
        "rule_version": MOCK_RULE_VERSION,
        "source_version": source_version or MOCK_SOURCE_VERSION,
        "status": status,
        "questions": questions if questions is not None else [],
        "action_card": action_card,
        "evidence": evidence if evidence is not None else [],
        "warnings": warnings if warnings is not None else [],
    }
    validate(result, "navigate_response")
    return result

def unknown(value):
    return value is None or value == "unknown"

def _question(field, label, input_type):
    return {"id": field, "label": label, "input_type": input_type, "required": True}

def _mock_card(case_type):
    return {
        "case_summary": "Synthetic Task 4 contract demo for " + case_type + "; no legal eligibility assessed.",
        "potential_channels": [],
        "conditions": [],
        "steps": ["Verify the relevant facts and official guidance before taking action."],
        "document_checklist": [],
        "unresolved_questions": [],
        "citations": [SYNTHETIC_EVIDENCE["evidence_id"]],
    }

def evaluate(case_type, answers, *, simulate_supported=False, mock_evidence=None, configs=None, kb=None):
    """Evaluate only explicit scope signals and missing facts, not legal thresholds.

    simulate_supported is a gated developer fixture; production API callers cannot set it.
    """
    kb = load_knowledge_base() if kb is None else kb
    configs = load_rule_configurations(kb=kb) if configs is None else configs
    source_version = kb["source_version"]
    category = "rental" if case_type == "rental_deposit" else "consumer"
    checks = configs[category]["checks"] + configs["boundary"]["checks"]
    if any(check["runtime_enabled"] is not False or check["threshold"] is not None for check in checks):
        return envelope("ERROR", warnings=["Unexpected activated or unverified rules."], source_version=source_version)

    # These are project-scope exclusions, not official legal eligibility findings.
    if case_type == "rental_deposit" and str(answers.get("premises_type", "")).lower() in ("commercial", "industrial"):
        return envelope("REFER_TO_OFFICIAL", warnings=[
            "Commercial or industrial premises are outside SG Navi's rental-deposit pilot. Confirm options with an official source."
        ], source_version=source_version)
    if case_type == "consumer_complaint":
        if str(answers.get("purchase_purpose", "")).lower() == "business":
            return envelope("REFER_TO_OFFICIAL", warnings=[
                "Business-purpose purchases are outside this project's consumer pilot. Confirm with an official source."
            ], source_version=source_version)
        if answers.get("supplier_registered_in_sg") is False:
            return envelope("REFER_TO_OFFICIAL", warnings=[
                "Supplier registration was reported as false; SG Navi cannot confirm a supported channel."
            ], source_version=source_version)

    questions = [_question(field, label, input_type)
                 for field, label, input_type in QUESTION_FIELDS[case_type]
                 if field not in answers or unknown(answers[field])]
    if questions:
        return envelope("NEED_CLARIFICATION", questions=questions, source_version=source_version)

    # Task 5: real RAG is used for *source context*, not legal rule activation.
    if not simulate_supported:
        rule_ids = rule_ids_for_context(case_type, configs)
        result, records = retrieve_checked(
            case_type, rule_ids, answers, expected_version=kb["source_version"]
        )
        if result == "ERROR":
            return envelope("ERROR", warnings=[
                "Evidence retrieval is temporarily unavailable. No decision can be made."
            ], source_version=kb["source_version"])
        if result != "FOUND":
            return envelope("REFER_TO_OFFICIAL", warnings=[
                "Verified evidence is missing or unavailable. Confirm the situation directly with official sources."
            ], source_version=kb["source_version"])
        safe_sources = referral_source_context(records, expected_version=source_version)
        if not safe_sources:
            return envelope("REFER_TO_OFFICIAL", warnings=[
                "Source context could not be safely displayed. Verify guidance with official services."
            ], source_version=source_version)
        return envelope("REFER_TO_OFFICIAL", evidence=safe_sources, warnings=[
            "Verified source references are provided for research context only, not an eligibility decision.",
            "Please check the linked official source pages and confirm the applicable procedure."
        ], source_version=source_version)

    record = deepcopy(mock_evidence if mock_evidence is not None else SYNTHETIC_EVIDENCE)
    try:
        validate(record, "evidence")
    except Exception:
        return envelope("REFER_TO_OFFICIAL", warnings=["Mock Evidence was missing or invalid."])

    if record != SYNTHETIC_EVIDENCE:
        return envelope("REFER_TO_OFFICIAL", warnings=[
            "Only the explicitly defined synthetic test fixture may simulate a supported path."
        ])

    return envelope(
        "SUPPORTED_PATH",
        evidence=[record],
        action_card=_mock_card(case_type),
        warnings=["TEST SIMULATION ONLY: no real eligibility, source review or official recommendation."],
    )
