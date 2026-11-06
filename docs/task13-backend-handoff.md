# Task 13 — Zheng backend integration handoff

Issue #73. Owner of `rag/` ranking, retrieval API and source verification: **@Chu-Junjie**. Backend interface and tests: **@ZhengZaikun**. This PR intentionally does not change `rag/`, the five canonical files, `shared/`, `frontend/`, legal activation flags, or `/api/navigate`.

## Implemented (backend-only)

- `backend/query_integration.py::prepare_confirmed_query(case_type, confirmed_answers, query=None, confirmed=False)` validates explicit confirmation, one of two case types, existing case-specific answer schema, bounded optional English text (max 300 chars), and rejects malformed or unconfirmed facts. All text is only data; no model or API calls.
- `checked_ranked_proposal(prepared, proposed_rule_ids, ranked_evidence_ids, expected_source_version=..., repository=None)` checks an **RAG-owner-proposed** ordered Evidence ID list against the current repository snapshot, existing complete rule mappings, authoritative citations, version/review states and operational quarantine. It rejects missing, extra, duplicate and wrong-case mappings rather than showing a partial set.
- The adapter refuses business/non-SG consumer scopes, commercial/industrial rental scopes, and attempts to conflate landlord SCT with estate-agent/agency evidence.
- Returns `FOUND` with ordered six-field metadata records only, or `INVALID` with empty records. It does **not** add a new public endpoint, produce original quotes, assert relevance ranking on its own, or upgrade legal eligibility.

## Required Junjie interface before real query-based integration

Please define a versioned, bounded, reviewable RAG function that accepts the validated output of `prepare_confirmed_query`, and returns:

```json
{
  "query_rag_version": "proposal-1",
  "retrieval_status": "FOUND",
  "proposed_rule_ids": ["SCT_RESIDENTIAL_SCOPE", "SCT_CLAIM_AMOUNT"],
  "ranked_evidence_ids": ["SCT-ELIG-RESIDENTIAL", "SCT-ELIG-AMOUNT"],
  "match_reasons": [
    {"evidence_id": "SCT-ELIG-RESIDENTIAL", "reason": "rental residential scope"},
    {"evidence_id": "SCT-ELIG-AMOUNT", "reason": "amount to check"}
  ]
}
```

**This is a proposed handoff shape, not an approved `shared/` contract or live API.** Junjie must own the query ranking strategy, selection of correct specific passage instead of a generic publisher URL, review/quarantine checks, false-positive tests, and optional use of `match_reasons` (strictly relevance explanations, never legal confidence). All proposed rule IDs must refer to already checked rules; `FOUND` is not eligibility. A ranked proposal with only a subset of mandatory mapped evidence must fail until the canonical rule-based retrieval check passes.

The adapter currently validates the complete canonical mapping for each proposed rule. Supporting evidence-level top-k subsets requires an explicit separate policy approved by the RAG owner; do not silently change this behavior. `validate_citations` re-reads the authoritative snapshot before final presentation. Any source/state change yields fail-closed output.

## Real commands to run

```bash
python -m pytest tests/backend/test_task13_integration.py -q
python -m pytest tests/contracts tests/backend tests/rag tests/integration -q
```

No local test outcome is claimed. Use the actual GitHub Actions run for tested commit. Baseline v1 navigation and Task 12 guidance remain unchanged. These tests use controlled scenarios, not live publisher checks or real user disputes.

## Release gate

1. Junjie implements the RAG-owned query-aware retriever and deterministic relevance tests on his branch.
2. Zheng integrates its agreed output into backend and Task 12 `research_guidance` only after contract review; verify current source/version/quarantine and negative cases again.
3. Guanyu agrees resulting preview UI behavior; review PR and CI before merge.
