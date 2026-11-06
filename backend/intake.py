"""Task 11: deterministic, bounded English intake with no legal inference.

Candidate facts are UNCONFIRMED even when extracted. Raw descriptions are not
stored, returned, logged or sent to any external model. The only approved case
types are rental_deposit and consumer_complaint.
"""
from __future__ import annotations

import hashlib
import json
import re

from jsonschema import Draft202012Validator, FormatChecker
from backend.rules.engine import QUESTION_FIELDS
from backend.routes.task2 import answers_validator

INTAKE_VERSION = "1.0"
MAX_CHARS = 1200
CASE_TYPES = ("rental_deposit", "consumer_complaint")
STATUS_TYPES = ("suggested", "ambiguous", "out_of_scope", "cannot_determine")
UNSUPPORTED = re.compile(
    r"\b(?:immigrat(?:ion|e)|visa|work permit|employment|employer|salary|"
    r"criminal|police arrest|criminal charge|divorce|custody|medical|"
    r"tax evasion|citizenship|personal injury|bankruptcy)\b", re.I,
)
RENTAL = re.compile(
    r"\b(?:landlord|tenan(?:t|cy)|rental deposit|security deposit|"
    r"rent deposit|lease|leased apartment|leased room|property agent|"
    r"estate agent|letting agent)\b", re.I,
)
CONSUMER = re.compile(
    r"\b(?:bought|purchase(?:d)?|refund|faulty|defective|"
    r"consumer|shop|store|retailer|seller|merchant|"
    r"product|item|goods|delivery|warranty)\b", re.I,
)
DEPOSIT = re.compile(r"\b(?:deposit|landlord|tenant|tenancy|rent|lease)\b", re.I)
CONSUMER_ACTION = re.compile(r"\b(?:bought|purchase(?:d)?|faulty|defective|consumer|warranty)\b", re.I)
MONEY = re.compile(r"(?<![\w])(?:S\s*\$|SGD\s*)(\d{1,3}(?:,\d{3})+(?:\.\d{1,2})?|\d+(?:\.\d{1,2})?)(?![\w,.])", re.I)
NUMBER = re.compile(r"^\d+(?:,\d{3})*(?:\.\d{1,2})?$")
SOURCE_LIMIT = "This is an unconfirmed English-language interpretation, not a legal eligibility or filing decision."
QUESTION_BY_CASE = {
    case: tuple({"id": field, "label": label, "input_type": input_type, "required": True}
                for field, label, input_type in fields)
    for case, fields in QUESTION_FIELDS.items()
}
# Explicitly controlled natural-language cues. Do not infer whether a business
# is legally registered, whether a person is resident, or official thresholds.
LANDLORD = re.compile(r"\b(?:my|the|our|a)\s+landlord\b", re.I)
AGENT = re.compile(r"\b(?:property|estate|letting|rental)\s+agent\b", re.I)
RESIDENTIAL = re.compile(r"\b(?:residential|apartment|flat|hdb|condo|bedroom|rented room)\b", re.I)
COMMERCIAL = re.compile(r"\b(?:commercial premises|industrial premises|office rental|shop rental)\b", re.I)
GOODS = re.compile(r"\b(?:product|goods|phone|laptop|computer|item|appliance|headphones|furniture|device)\b", re.I)
SERVICES = re.compile(r"\b(?:service|repair service|cleaning service|subscription)\b", re.I)
PERSONAL = re.compile(r"\b(?:for (?:my |our )?personal use|for myself|personal purchase)\b", re.I)
BUSINESS = re.compile(r"\b(?:for (?:my |our )?business|business use|for resale|company purchase)\b", re.I)
REGISTERED = re.compile(r"\b(?:seller|supplier|merchant|company)\s+(?:is|was)\s+(not\s+)?registered\s+in\s+singapore\b", re.I)

def _validate_text(description):
    if not isinstance(description, str):
        raise ValueError("Description must be a string.")
    if not 1 <= len(description.strip()) <= MAX_CHARS:
        raise ValueError("Description must contain 1 to 1200 characters.")
    if any(ord(char) < 32 and char not in "\n\t\r" for char in description):
        raise ValueError("Description contains unsupported control characters.")
    if "\ufffd" in description:
        raise ValueError("Description contains invalid text encoding.")
    # English MVP accepts ordinary Unicode punctuation and the Singapore dollar
    # symbol but does not attempt interpretation of other writing systems.
    if re.search(r"[\u0400-\u052f\u0600-\u06ff\u0900-\u0dff\u3040-\u30ff\u3400-\u9fff\uac00-\ud7af]", description):
        raise ValueError("Only English descriptions are supported in this MVP.")
    return description.strip()


def _case_type(description):
    rental = bool(RENTAL.search(description))
    consumer = bool(CONSUMER.search(description))
    # A landlord may use the word "refund" about a deposit. That word alone
    # is not evidence of a separate consumer purchase/dispute.
    if rental and not CONSUMER_ACTION.search(description) and not re.search(
        r"\\b(?:shop|store|retailer|seller|merchant|product|item|goods|delivery)\\b", description, re.I
    ):
        consumer = False
    if UNSUPPORTED.search(description):
        return "out_of_scope", None
    if rental and consumer:
        # "landlord refused my refund" should be clarified, never forced.
        return "ambiguous", None
    if rental and DEPOSIT.search(description):
        return "suggested", "rental_deposit"
    if consumer and CONSUMER_ACTION.search(description):
        return "suggested", "consumer_complaint"
    return "cannot_determine", None


def _sgd_amount(description):
    values = []
    for match in MONEY.finditer(description):
        literal = match.group(1).replace(",", "")
        if not NUMBER.fullmatch(literal):
            return None
        value = float(literal)
        if not 0 <= value <= 1000000000:
            return None
        values.append(value)
    # More than one monetary value may represent purchase price vs claim;
    # do not choose arbitrarily, even if repeated.
    return values[0] if len(values) == 1 else None


def _facts(case_type, text):
    facts = {}
    amount = _sgd_amount(text)
    if amount is not None:
        facts["claim_amount_sgd"] = amount
    if case_type == "rental_deposit":
        landlord, agent = bool(LANDLORD.search(text)), bool(AGENT.search(text))
        if landlord != agent:
            facts["dispute_with"] = "landlord" if landlord else "agent"
        residential, commercial = bool(RESIDENTIAL.search(text)), bool(COMMERCIAL.search(text))
        if residential != commercial:
            facts["premises_type"] = "residential" if residential else "commercial"
    if case_type == "consumer_complaint":
        goods, services = bool(GOODS.search(text)), bool(SERVICES.search(text))
        if goods != services:
            facts["purchase_type"] = "goods" if goods else "services"
        personal, business = bool(PERSONAL.search(text)), bool(BUSINESS.search(text))
        if personal != business:
            facts["purchase_purpose"] = "personal" if personal else "business"
        registration = list(REGISTERED.finditer(text))
        if len(registration) == 1:
            facts["supplier_registered_in_sg"] = not bool(registration[0].group(1))
    return facts


def interpret(description):
    text = _validate_text(description)
    status, case = _case_type(text)
    facts = _facts(case, text) if case else {}
    return {
        "intake_version": INTAKE_VERSION,
        "intake_status": status,
        "suggested_case_type": case,
        "candidate_facts": facts,
        "needs_confirmation": True,
        "clarification_questions": [],
        "limitations": [SOURCE_LIMIT] + ([] if case else
                        ["Choose the correct supported case yourself or consult an appropriate official source."]),
    }


def _validate_answers(case_type, answers):
    if case_type not in CASE_TYPES or not isinstance(answers, dict):
        raise ValueError("A supported case and confirmed answers object are required.")
    if any(isinstance(value, str) and (
            len(value) > 200 or any(ord(char) < 32 for char in value))
            for value in answers.values()):
        raise ValueError("Confirmed fields exceed permitted length or contain control characters.")
    if not answers_validator(case_type).is_valid(answers):
        raise ValueError("Confirmed answers do not match the selected case schema.")


def confirm(case_type, answers):
    _validate_answers(case_type, answers)
    # The explicit JSON contract differentiates missing, null, 'unknown', false.
    # A user selecting Unknown has already answered; do not loop indefinitely.
    missing = [dict(question) for question in QUESTION_BY_CASE[case_type]
               if question["id"] not in answers]
    unresolved = [field for field in answers if answers[field] is None or answers[field] == "unknown"]
    canonical = json.dumps({"case_type": case_type, "answers": answers},
                           ensure_ascii=True, sort_keys=True, separators=(",", ":"))
    revision = hashlib.sha256(canonical.encode("utf-8")).hexdigest()[:20]
    return {
        "intake_version": INTAKE_VERSION,
        "intake_status": "confirmed",
        "suggested_case_type": case_type,
        "candidate_facts": dict(answers),
        "needs_confirmation": False,
        "clarification_questions": missing,
        "unresolved_fields": sorted(unresolved),
        "revision": revision,
        "limitations": [
            "These facts were confirmed by the user; this API does not determine eligibility.",
            "Unknown and not-provided answers remain unresolved; never treat them as false.",
        ],
    }
