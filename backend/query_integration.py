"""Task 13 backend-side, fail-closed adapter for a future query-aware RAG owner API.

This intentionally does NOT implement the RAG search/ranker (owned by Junjie).
It validates bounded, explicitly confirmed input and verifies all RAG-proposed
rule mappings using the existing strict retrieval/citation checks.
No output is a legal eligibility finding.
"""
import re

from backend.routes.task2 import answers_validator
from backend.rag_bridge import retrieve_checked, referral_source_context
from rag.repository import EvidenceRepository

CASES = frozenset(("rental_deposit", "consumer_complaint"))
MAX_QUERY = 300
SAFE_QUERY = re.compile(r"^[a-zA-Z0-9 ,.!?'-]+$")
MAX_RULES = 8

def prepare_confirmed_query(case_type, confirmed_answers, *, query=None, confirmed=False):
    """Return confirmed facts for a query-aware retriever; never infer eligibility.

    Reject unconfirmed free text even when it sounds like a case. Text is data,
    never an instruction. The RAG owner must design query parsing/ranking.
    """
    if confirmed is not True or case_type not in CASES:
        raise ValueError("Only explicitly confirmed supported cases can be queried")
    if not isinstance(confirmed_answers, dict):
        raise ValueError("Confirmed facts must be an object")
    if not answers_validator(case_type).is_valid(confirmed_answers):
        raise ValueError("Confirmed facts violate case schema")
    if any(isinstance(value, str) and (len(value) > 200 or
           any(ord(ch) < 32 for ch in value)) for value in confirmed_answers.values()):
        raise ValueError("Invalid confirmed fact")
    if query is not None:
        if (not isinstance(query, str) or not 1 <= len(query.strip()) <= MAX_QUERY
                or not SAFE_QUERY.fullmatch(query.strip())):
            raise ValueError("Query must be short, bounded English text")
        # User confirmation applies equally to structured facts and query.
        query = query.strip()
    return {"case_type": case_type, "facts": dict(confirmed_answers),
            "query": query, "context_only": True}

def checked_ranked_proposal(prepared, proposed_rule_ids, ranked_evidence_ids, *,
                            expected_source_version, repository=None):
    """Verify RAG-owner proposed ranking against full current rule mappings.

    Only existing exact-rule retrieval can authorize evidence IDs. Proposed IDs
    are ranking hints, not a shortcut around mandatory source coverage or
    current quarantine, and are never treated as applicability decisions.
    A source mismatch rejects the entire proposal, not merely that item.
    """
    if (not isinstance(prepared, dict) or
            set(prepared) != {"case_type", "facts", "query", "context_only"} or
            prepared["context_only"] is not True or
            prepared["case_type"] not in CASES):
        return {"retrieval_status": "INVALID", "evidence": [], "ranked_evidence_ids": []}
    if (not isinstance(proposed_rule_ids, list) or not proposed_rule_ids
            or len(proposed_rule_ids) > MAX_RULES
            or any(not isinstance(value, str) or not value.strip() for value in proposed_rule_ids)
            or len(set(proposed_rule_ids)) != len(proposed_rule_ids)
            or not isinstance(ranked_evidence_ids, list) or not ranked_evidence_ids
            or any(not isinstance(value, str) or not value.strip() for value in ranked_evidence_ids)
            or len(set(ranked_evidence_ids)) != len(ranked_evidence_ids)
            or not isinstance(expected_source_version, str)):
        return {"retrieval_status": "INVALID", "evidence": [], "ranked_evidence_ids": []}
    repo = repository or EvidenceRepository()
    try:
        bundle, blocked = repo.snapshot()
        if bundle["source_version"] != expected_source_version:
            raise ValueError("Stale corpus version")
        # Reject a proposed legal check being switched on or an unreviewed
        # mapping. This adapter is strictly information-only.
        for rule_id in proposed_rule_ids:
            rule = bundle["rules"].get(rule_id)
            if (rule is None or rule["runtime_enabled"] is not False
                    or rule["review_status"] != "verified"
                    or prepared["case_type"] not in rule["case_types"]):
                raise ValueError("Unusable query mapping")
        # Use the existing RAG exact-rule selector and authoritative citation
        # validator, with the same repository (including quarantine state).
        from rag.selection import select_evidence
        from rag.citations import validate_citations
        canonical = select_evidence(bundle, blocked, prepared["case_type"], proposed_rule_ids)
        validate_citations(prepared["case_type"], proposed_rule_ids, canonical,
                           [item["evidence_id"] for item in canonical],
                           expected_source_version=expected_source_version,
                           repository=repo)
        checked = referral_source_context(canonical, expected_version=expected_source_version)
        by_id = {row["evidence_id"]: row for row in checked}
        # Every explicitly mapped source must appear, so query rank cannot
        # silently omit required evidence. The ranking can reorder only.
        if not checked or set(ranked_evidence_ids) != set(by_id):
            raise ValueError("Incomplete, duplicated or wrong-case ranked evidence")
        return {"retrieval_status": "FOUND",
                "evidence": [by_id[eid] for eid in ranked_evidence_ids],
                "ranked_evidence_ids": list(ranked_evidence_ids)}
    except Exception:
        # No raw user query or facts are ever logged in the error path.
        return {"retrieval_status": "INVALID", "evidence": [], "ranked_evidence_ids": []}
