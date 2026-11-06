"""Task 15 confirmed intake -> query context -> approved guidance -> source view.

Stateless, bounded research/preparation guidance only. No legal rule activation,
model calls, raw dispute logging or production source-state mutation.
"""
import hashlib
import json
import math

from backend.intake import confirm
from backend.query_integration import prepare_confirmed_query, checked_ranked_proposal
from backend.results import assemble
from rag.display_context import DisplayContextUnavailable, enrich_display_evidence
from rag.query_retriever import retrieve_query_evidence
from rag.repository import EvidenceRepository

VERSION = "1.0"
LIMIT = "Research and preparation information only. Eligibility, deadlines and filing rights are not determined."


def empty(status, message, *, source_version=None, revision=None):
    return {"guidance_version": VERSION, "rule_version": "mock-1", "source_version": source_version,
            "context_version": None, "confirmation_revision": revision, "result_id": None,
            "guidance_status": status, "questions": [], "research_guidance": None,
            "display_evidence": [], "claim_citations": [], "matched_evidence_ids": [],
            "query_status": "NOT_RUN", "query_fallback": False, "unresolved_fields": [],
            "action_card": None, "limitations": [LIMIT, message]}


def _boundary(case, facts):
    if case == "rental_deposit":
        return str(facts.get("premises_type") or "").strip().lower() in ("commercial", "industrial")
    location = str(facts.get("supplier_location") or "").strip().lower()
    return (str(facts.get("purchase_purpose") or "").strip().lower() == "business"
            or facts.get("supplier_registered_in_sg") is False
            or location not in ("", "unknown", "singapore", "sg"))


def generate(case_type, answers, *, confirmation_revision, query=None, repository=None, freshness_report=None):
    if any(isinstance(v, float) and not math.isfinite(v) for v in answers.values()):
        raise ValueError("Invalid confirmed number")
    if query is not None and (not isinstance(query, str) or any(ord(c) < 32 or ord(c) == 127 for c in query)):
        raise ValueError("Invalid query")
    prepared = prepare_confirmed_query(case_type, answers, query=query, confirmed=True)
    confirmation = confirm(case_type, answers)
    if confirmation["revision"] != confirmation_revision:
        raise ValueError("Updated facts require confirmation")
    repo = repository or EvidenceRepository()
    bundle, _ = repo.snapshot()
    version = bundle["source_version"]
    base = empty("LIMITED_REFERRAL", "Some conditions still need confirmation; check the relevant official service.",
                 source_version=version, revision=confirmation["revision"])
    base["unresolved_fields"] = list(confirmation["unresolved_fields"])
    if _boundary(case_type, answers):
        base["limitations"].append("This situation is outside the current SG Navi pilot scope.")
        return base
    proposal = retrieve_query_evidence(prepared, expected_source_version=version, repository=repo)
    fallback = proposal["retrieval_status"] == "NO_RESULTS" and proposal["diagnostic_code"] == "NO_MATCH"
    if fallback:
        # The unmatched text remains unmatched. Only separately confirmed facts
        # may support a conservative research topic; never claim text matching.
        prepared = dict(prepared, query=None)
        proposal = retrieve_query_evidence(prepared, expected_source_version=version, repository=repo)
    questions = list(confirmation["clarification_questions"])
    agent = str(answers.get("dispute_with") or "").strip().lower() in ("agent", "agency", "property_agent")
    conduct = any(r.startswith("CEA_COMPLAINT_") or r == "CEA_CONDUCT_COMPLAINT"
                  for r in proposal["proposed_rule_ids"])
    if agent:
        questions = [q for q in questions if q["id"] == "dispute_with"]
    if agent and not conduct and "agency_agreement_signed" not in answers:
        questions.append({"id": "agency_agreement_signed", "label": "Did you sign an agreement with the estate agency?",
                          "input_type": "select", "required": True})
    if proposal["retrieval_status"] == "ERROR" or proposal["diagnostic_code"] in ("EVIDENCE_UNAVAILABLE", "STALE_VERSION"):
        base["limitations"].append("Required source records are currently unavailable; further answers cannot establish a verified result.")
        return base
    if questions:
        base["guidance_status"] = "CLARIFICATION_REQUIRED"
        base["questions"] = questions
        return base
    if proposal["retrieval_status"] != "FOUND":
        base["limitations"].append("Current confirmed details or source records do not establish a reviewable research topic.")
        return base
    verified = checked_ranked_proposal(prepared, proposal["proposed_rule_ids"], proposal["ranked_evidence_ids"],
                                       expected_source_version=version, repository=repo)
    if verified["retrieval_status"] != "FOUND":
        return base
    assembled = assemble(case_type, answers, repository=repo,
                         research_topic="agent_conduct" if agent and conduct else None)
    if assembled["research_guidance"] is None:
        base["limitations"] = list(assembled["limitations"])
        return base
    try:
        view = enrich_display_evidence(case_type, assembled["research_guidance"], assembled["display_evidence"],
                                        expected_source_version=version, repository=repo,
                                        freshness_report=freshness_report)
    except DisplayContextUnavailable:
        base["limitations"].append("The current source review could not be verified. No guidance or verified excerpt is shown.")
        return base
    ids = {r["evidence_id"] for r in view["display_evidence"]}
    matched = [eid for eid in verified["ranked_evidence_ids"] if eid in ids]
    # Query top-k is only a reading-order hint. Complete claim/template citations
    # are independently retained, including records outside its eight-ID limit.
    identity = hashlib.sha256(json.dumps([VERSION, confirmation["revision"], prepared["query"], view],
                                         sort_keys=True, separators=(",", ":")).encode()).hexdigest()[:24]
    return {**base, "guidance_status": "GUIDANCE_ONLY", "context_version": view["context_version"],
            "result_id": identity, "research_guidance": assembled["research_guidance"],
            "display_evidence": view["display_evidence"], "claim_citations": view["claim_citations"],
            "matched_evidence_ids": matched, "query_status": "FOUND", "query_fallback": fallback,
            "unresolved_fields": assembled["unresolved_fields"],
            "limitations": list(assembled["limitations"]) + (["The wording did not match a topic; this context uses your confirmed facts only."] if fallback else [])}
