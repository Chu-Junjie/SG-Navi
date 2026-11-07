"""Task 18 — bounded English scenario understanding and adaptive questions.

Interpretation is an UNCONFIRMED candidate, not a legal/route decision. Task 19
owns action-plan HTTP, verified sources and next actions. No raw text persists.
"""
from __future__ import annotations

import hashlib
import json
import re
from decimal import Decimal, InvalidOperation

from jsonschema import Draft202012Validator, FormatChecker

from backend.intake import _validate_text
from pathlib import Path

CONTRACT = json.loads((Path(__file__).resolve().parents[1] / "shared" / "action_plan_contract.json").read_text(encoding="utf-8"))
CONTEXT_SCHEMA = CONTRACT["$defs"]["context"]
QUESTION_SCHEMA = CONTRACT["$defs"]["question"]
CONTEXT_VALIDATOR = Draft202012Validator(CONTEXT_SCHEMA, format_checker=FormatChecker())
QUESTION_VALIDATOR = Draft202012Validator(QUESTION_SCHEMA)
VERSION = "1.0"

def has(text, pattern):
    return bool(re.search(pattern, text, re.I))

RENTAL = r"\b(?:landlord|tenant|tenancy|rent(?:al|ed|ing)?|lease|security deposit|rental deposit|flat|roommate|property agent|estate agent|estate agency|agency agreement)\b"
RENTAL_TOPIC = r"\b(?:deposit|lease|tenan\w*|landlord|rent\w*|early (?:exit|termination|departure)|break clause|agency agreement|commission dispute)\b"
CONSUMER = r"\b(?:restaurant|cafe|dining|meal|food|bill|charged|charge|overcharg\w*|refund|purchase\w*|bought|shop|store|seller|merchant|goods|product|service|defective|faulty|warranty|double payment|duplicate payment)\b"
TRANSACTION = r"\b(?:restaurant|cafe|dining|meal|bill|charg\w*|overcharg\w*|purchase\w*|bought|shop|store|seller|merchant|goods|product|service|faulty|defective|payment)\b"
DISPUTE = r"\b(?:overcharg\w*|extra|incorrect|wrong|unexplained|disput\w*|refus\w*|deny|denied|won.t|will not|would not|do not understand|don.t understand|not return\w*|not refund\w*|duplicate|double|twice|faulty|defective|broken|complain\w*|deduct\w*|withh\w*|kept|keep|retained|missing|never arrived|not deliver\w*)\b"
PASS = r"\b(?:work pass|work permit|employment pass|s pass|pass expir\w*|pass cancel\w*|visa)\b"
STANDALONE = r"\b(?:immigration|citizenship|passport|apply for (?:a |my )?(?:work permit|visa)|renew (?:my |a )?(?:visa|pass)|salary|criminal charge|divorce|tax evasion)\b"
BOND = r"\b(?:government|employer|migrant worker|work permit)\s+(?:security\s+)?bond\b|\bsecurity bond\b"
MONEY = re.compile(r"(?<![\w])(?:S\s*\$|SGD\s*)(\d{1,3}(?:,\d{3})+(?:\.\d{1,2})?|\d+(?:\.\d{1,2})?)(?![\w,]|\.\d)", re.I)

def _amount(text):
    matches = list(MONEY.finditer(text))
    if len(matches) != 1:
        return None
    try:
        value = Decimal(matches[0].group(1).replace(",", ""))
        cents = value * 100
        if cents != cents.to_integral_value() or not 0 <= cents <= 100000000000:
            return None
        return int(cents)
    except InvalidOperation:
        return None

def _goal(text):
    # Explicit intent wins; complaints and monetary recovery are not identical.
    if has(text, r"\b(?:file|submit|bring|start)\s+(?:a\s+)?(?:small\s+)?claim\b|\btribunal\b"):
        return "prepare_claim"
    if has(text, r"\b(?:want|need|wish|hope|trying|seek|request|ask)(?:\s+to)?\s+(?:a\s+)?(?:refund|repayment|money back|deposit back)\b|\bget (?:my|the) money back\b|\brefund (?:it|me|my|the)\b"):
        return "seek_refund"
    if has(text, r"\b(?:want|need|wish|trying)\s+to\s+(?:complain|report|make a complaint)\b|\bwhere\s+(?:can|do)\s+i\s+complain\b"):
        return "complain"
    if has(text, r"\b(?:want|need)\s+to\s+(?:contact|call|email|reach)\b"):
        return "contact_provider"
    return "understand_options"

def _bool_phrase(text, yes, no):
    a, b = has(text, yes), has(text, no)
    return True if a and not b else False if b and not a else None

def _facts(case, text):
    facts = {}
    cents = _amount(text)
    if cents is not None:
        facts["disputed_amount_cents"] = cents
    if has(text, r"\b(?:already|previously)\s+(?:asked|complained|contacted|requested)|\b(?:restaurant|seller|landlord|merchant)\s+(?:refused|denied|declined)|\brefus\w*\s+(?:to|my)"):
        facts["resolution_attempted"] = True
    if case == "rental_deposit":
        landlord = has(text, r"\blandlord\b")
        agent = has(text, r"\b(?:property|estate|letting)\s+agent\b")
        if landlord != agent:
            facts["dispute_with"] = "landlord" if landlord else "agent"
        hdb = has(text, r"\bHDB\b")
        private = has(text, r"\b(?:private (?:flat|apartment|condo|house)|condo|minium|private residential)\b")
        commercial = has(text, r"\bcommercial\s+(?:lease|premises|rental)|\bshop rental\b")
        industrial = has(text, r"\bindustrial\s+(?:lease|premises|rental)\b")
        values = [v for flag,v in ((hdb,"hdb"),(private,"private_residential"),(commercial,"commercial"),(industrial,"industrial")) if flag]
        if len(values) == 1:
            facts["premises_type"] = values[0]
        if has(text, r"\b(?:pass|work permit|visa)\s+(?:was\s+|has\s+been\s+)?cancelled\b|\bcancelled\s+(?:my\s+)?(?:work pass|work permit|employment pass|s pass|visa)\b"):
            facts["pass_event"] = "cancelled"
        elif has(text, r"\b(?:pass|work permit|visa)\s+(?:is\s+)?(?:expiring|expires|about to expire)\b"):
            facts["pass_event"] = "expiring"
        ended = _bool_phrase(text, r"\b(?:already|have)\s+(?:ended|terminated|left|moved out)\b|\b(?:lease|tenancy)\s+(?:has\s+)?ended\b", r"\b(?:not yet|haven.t|have not)\s+(?:ended|terminated|left|moved out)\b|\bstill (?:living|renting|in the tenancy)\b")
        if ended is not None:
            facts["lease_ended"] = ended
        clause = _bool_phrase(text, r"\b(?:my|the|signed)\s+(?:lease|agreement|contract)\s+(?:has|includes|contains)\s+(?:a\s+)?(?:break|diplomatic)\s+clause\b", r"\b(?:no|without)\s+(?:break|diplomatic)\s+clause\b")
        if clause is not None:
            facts["break_clause_present"] = clause
    else:
        if has(text, r"\b(?:restaurant|cafe|dining|meal|food|bill)\b"):
            facts["purchase_type"] = "services"
        elif has(text, r"\b(?:phone|laptop|headphones|goods|product|device|item|appliance)\b"):
            facts["purchase_type"] = "goods"
        if has(text, r"\b(?:for (?:my |our )?personal use|for myself|personal purchase)\b"):
            facts["purchase_purpose"] = "personal"
        elif has(text, r"\b(?:for (?:my |our )?business|business use|for resale|company purchase)\b"):
            facts["purchase_purpose"] = "business"
        sg = has(text, r"\b(?:in singapore|singapore (?:restaurant|cafe|shop|store|seller|merchant))\b")
        abroad = has(text, r"\b(?:overseas|outside singapore|in malaysia|in china)\b")
        if sg != abroad:
            facts["merchant_location"] = "singapore" if sg else "outside_singapore"
    return facts

def _subtype(case, text):
    if case == "rental_deposit":
        if has(text, r"\b(?:agent|agency)\b") and has(text, r"\b(?:misconduct|unprofessional|harass\w*|misled|decept\w*|complaint about (?:the|my) agent)\b"):
            return "agent_conduct"
        if has(text, r"\b(?:agency agreement|commission dispute|agent contract)\b"):
            return "agency_agreement"
        if has(text, PASS) and has(text, r"\b(?:early|exit|leav\w*|depart\w*|terminat\w*|deposit|lease|tenan\w*)\b"):
            return "pass_related_exit"
        if has(text, r"\b(?:early exit|leave early|leaving early|leave (?:my|the) (?:rented|rental) \w+ early|end (?:my|the) lease early|terminate (?:my|the) lease|break (?:my|the) lease)\b"):
            return "early_exit"
        if has(text, r"\b(?:deduct\w*|damage charge|cleaning charge|withh\w*)\b"):
            return "deposit_deduction"
        if has(text, r"\b(?:not return\w*|not refunded|refus\w*|kept|keep|return|refund|deposit back)\b"):
            return "deposit_return"
        return "unspecified"
    if has(text, r"\b(?:twice|double charg\w*|double billed|duplicate (?:charge|payment|transaction)|charged twice|two identical charges)\b"):
        return "duplicate_charge"
    if has(text, r"\b(?:restaurant|cafe|dining|meal|food|bill)\b"):
        if has(text, r"\b(?:overcharg\w*|charg\w*[^.?!]{0,50}\bextra|charg\w*\s+(?:me\s+)?(?:too much|more)|extra\s+(?:charge|fee|SGD|S\$|\d)|incorrect bill|wrong bill)\b"):
            return "restaurant_overcharge"
        return "unclear_charge"
    if has(text, r"\b(?:faulty|defective|broken|goods|product|phone|laptop)\b"):
        return "goods_dispute"
    if has(text, r"\b(?:service|subscription|repair|delivery)\b"):
        return "services_dispute"
    return "unspecified"

def interpret_scenario(description):
    """Return only a candidate context or bounded diagnostic; never claim verification."""
    text = _validate_text(description)
    rental = has(text, RENTAL) and has(text, RENTAL_TOPIC)
    consumer = has(text, CONSUMER) and has(text, TRANSACTION) and has(text, DISPUTE)
    # Government/employer security bond is not a private residential deposit.
    if has(text, BOND) and not has(text, r"\b(?:landlord|tenancy|lease|rental deposit)\b"):
        return {"status": "outside_scope", "context": None}
    if has(text, STANDALONE) and not rental:
        return {"status": "outside_scope", "context": None}
    if has(text, PASS) and not rental and not consumer:
        return {"status": "outside_scope", "context": None}
    if rental and consumer:
        # A rent refund is not automatically a consumer goods dispute.
        consumer_cues = has(text, r"\b(?:restaurant|cafe|dining|meal|food|phone|goods|product|bought|purchase\w*|shop|store|merchant)\b")
        if consumer_cues:
            return {"status": "ambiguous_scope", "context": None}
        consumer = False
    if not rental and not consumer:
        return {"status": "insufficient_facts", "context": None}
    case = "rental_deposit" if rental else "consumer_complaint"
    subtype = _subtype(case, text)
    facts = _facts(case, text)
    summary = {
        "restaurant_overcharge": "You reported a restaurant billing overcharge.",
        "duplicate_charge": "You reported being charged twice for a transaction.",
        "unclear_charge": "You reported a disputed restaurant bill or charge.",
        "goods_dispute": "You reported a dispute about purchased goods.",
        "services_dispute": "You reported a dispute about a purchased service.",
        "deposit_return": "You reported a dispute about returning a rental deposit.",
        "deposit_deduction": "You reported disputed deductions from a rental deposit.",
        "early_exit": "You reported a rental dispute involving an early tenancy exit.",
        "pass_related_exit": "You reported a rental issue involving a work-pass event.",
        "agent_conduct": "You reported a concern about an estate agent's conduct.",
        "agency_agreement": "You reported an estate agency agreement dispute.",
        "unspecified": "You reported a dispute that needs a little more context.",
    }[subtype]
    goal = _goal(text)
    summary += " You want to " + {
        "complain": "make a complaint.",
        "seek_refund": "seek repayment.",
        "prepare_claim": "explore preparing a formal claim.",
        "contact_provider": "contact the relevant organisation.",
        "understand_options": "understand your available options.",
    }[goal]
    context = {"case_type": case, "issue_subtype": subtype, "goal": goal,
               "facts": facts, "summary": summary}
    CONTEXT_VALIDATOR.validate(context)
    return {"status": "candidate", "context": context}

def context_revision(context):
    """Stable context identity. Changed answers never reuse prior advice."""
    CONTEXT_VALIDATOR.validate(context)
    canonical = json.dumps({key: context[key] for key in ("case_type", "issue_subtype", "goal", "facts")},
                           ensure_ascii=True, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()[:24]

def _question(field, prompt, reason, options):
    item = {"id": "decide_" + field, "field": field, "prompt": prompt, "reason": reason,
            "options": [{"value": v, "label": label} for v, label in options]}
    QUESTION_VALIDATOR.validate(item)
    return item

def next_decisive_question(context):
    """At most ONE route-changing question; never repeat an answered key.

    Unknown/null/false are intentionally different from a missing field.
    A limited but useful source-backed preparation action belongs to Task 19.
    """
    CONTEXT_VALIDATOR.validate(context)
    f, case, sub, goal = (context["facts"], context["case_type"],
                          context["issue_subtype"], context["goal"])
    def missing(key):
        return key not in f
    if case == "consumer_complaint":
        if f.get("purchase_purpose") == "business" or f.get("merchant_location") == "outside_singapore":
            return None
        if sub == "unspecified" and missing("purchase_type"):
            return _question("purchase_type", "Is this about goods or a service?",
                             "The type of purchase changes which help may be relevant.",
                             [("goods", "Goods"), ("services", "Service"), ("unknown", "Not sure")])
        if missing("purchase_purpose"):
            return _question("purchase_purpose", "Was this for personal or business use?",
                             "Consumer assistance may depend on the purpose of the purchase.",
                             [("personal", "Personal use"), ("business", "Business use"), ("unknown", "Not sure")])
        # A verified general preparation/contact route can be offered without
        # querying supplier registration, exact amount or every formal claim fact.
        return None
    if f.get("premises_type") in ("industrial", "commercial"):
        return None
    if sub in ("deposit_return", "deposit_deduction", "unspecified") and missing("dispute_with"):
        return _question("dispute_with", "Is this dispute with your landlord or an agent?",
                         "Landlord deposit disputes and agent-conduct issues use different routes.",
                         [("landlord", "Landlord"), ("agent", "Estate agent"), ("unknown", "Not sure")])
    if sub in ("early_exit", "pass_related_exit") and missing("lease_ended"):
        return _question("lease_ended", "Have you already ended the tenancy?",
                         "The immediate step differs for a planned exit and a completed exit.",
                         [(True, "Yes"), (False, "Not yet"), ("unknown", "Not sure")])
    if sub in ("early_exit", "pass_related_exit") and missing("break_clause_present"):
        return _question("break_clause_present", "Does your signed lease include a break or diplomatic clause?",
                         "Only the signed lease can establish your particular early-exit terms.",
                         [(True, "Yes"), (False, "No"), ("unknown", "Not sure")])
    if sub == "agency_agreement" and missing("agency_agreement_signed"):
        return _question("agency_agreement_signed", "Did you sign an agreement with the estate agency?",
                         "A signed agency agreement changes the potential dispute-resolution route.",
                         [(True, "Yes"), (False, "No"), ("unknown", "Not sure")])
    # A formal claim may need more facts later; that belongs to a supported
    # claim-specific Task 19 assessment, not generic intake questioning.
    return None
