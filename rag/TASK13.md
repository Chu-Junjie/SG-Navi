# Task 13 — query-aware research evidence, internal contract 1.0

Issue [#73](https://github.com/Chu-Junjie/SG-Navi/issues/73). RAG/shared owner:
Chu Junjie. This adds `rag.query_retriever.retrieve_query_evidence` alongside
the unchanged Task 4 exact-rule API. It ranks existing official passages, never
legal eligibility, a recommended filing route or a new supported Action Card.
No corpus, source review, operational quarantine, legal rule or dependency is
changed; no model, embeddings, paid service or remote query transfer is used.

## Bounded input and versioned output

[`shared/query_retrieval_contract.json`](../shared/query_retrieval_contract.json)
defines the additive internal protocol. It reuses the existing case answer
schemas and six-field Evidence schema through a local-only registry; it does
not extend `shared/api_contract.json` or the old v1 response envelope.

Call only with the result of Zheng's
`prepare_confirmed_query(case_type, confirmed_answers, query=..., confirmed=True)`.
RAG independently revalidates the exact four-key shape (`case_type`, `facts`,
`query`, `context_only: true`), case-specific approved fields, finite numbers,
bounded strings and optional ASCII English query (1–300 characters, the same
punctuation allowlist as the adapter). Control characters are rejected, including
before trimming. Use `SGD` rather than a dollar sign. A Python dict/shape cannot
prove human confirmation; the backend confirmation boundary remains required.
Raw intake descriptions must never be passed as already-confirmed facts.

Required keyword `expected_source_version` pins the caller's checked corpus.
Optional `mandatory_rule_ids` requires complete existing rule mappings;
`max_results` is an integer from 1 to 8. It bounds both evidence records and the
adapter's maximum eight rule groups. Facts/query are not changed, stored, logged
or returned. Missing, null, `unknown` and false remain distinct.

Output always contains `query_rag_version: "1.0"`, `context_only: true`,
`retrieval_status`, fixed `diagnostic_code`, `source_version`,
`proposed_rule_ids`, `ranked_evidence_ids`, canonical six-field `evidence`,
`match_reasons` and `missing_context_fields`. Each reason names the exact
Evidence ID, mapped rules, editorial search topics, matched approved field
names/allowlisted terms, mandatory-group membership and the recorded textual
locator. No raw facts/query, relevance score or legal confidence is exposed.
These internal reasons are not official quotations; verified display excerpts
and claim-level projection remain Task 14.

## Transparent selection and fail-closed behavior

1. Confirmed facts establish the research channel. Landlords cannot retrieve
   CEA-agent evidence. Agent conduct and agency-agreement disputes are separate;
   mixed or insufficient agent context requests clarification. Confirmed
   business/non-SG consumer or nonresidential tenancy scopes return no results.
   Text cannot override any of these facts. Unknown consumer purpose/type or
   unknown rental counterparty cannot be filled by keywords.
2. [`query_topics.py`](query_topics.py) holds reviewable search tags for current
   mapping IDs, not legal rules or duplicated Evidence IDs. Match curated topic
   terms, confirmed field presence and checked passage/summary/locator tokens.
   Internal order uses `4 * topic-term matches + min(2, document-term overlap)
   + 2 * relevant known fields + core-topic bonus`, then Rule ID/Evidence ID
   ties. No-query structured requests use core context and known fields;
   unrelated nonempty queries return `NO_MATCH`, not a publisher-wide fallback.
   Employment/cross-border exclusion passages remain available through the
   exact-rule API, but are not used to force excluded cases into this pilot.
3. Admit complete mapping groups under the limit; a mandatory group that would
   be truncated returns `LIMIT_COVERAGE`. Never take only the top passage of a
   multi-passage rule. Relevance does not authorize missing or activated rules.
4. Pass the complete selected batch through existing `retrieve_evidence` and
   `validate_citations`. They reread checked corpus/review proof and operational
   state, preserve reciprocal mappings, exact digests/versions/URLs and full
   source coverage. A mixed valid/unavailable batch returns no partial evidence;
   quarantine between ranking and final validation also fails closed. No cache
   can serve an earlier successful result after a state change.
5. Text stays data. There is no instruction evaluator or model call. Altering
   an official excerpt without a matching reviewed digest fails the existing
   importer. Query instructions cannot activate rules or invent citations.

`FOUND/MATCHED` means research evidence availability only. `NO_RESULTS` covers
insufficient context, project boundary, unmatched query, stale version,
unavailable evidence and mandatory coverage limits. `ERROR` covers invalid
input or unreadable/corrupt source/state. All non-FOUND outputs have empty
evidence, IDs, mappings and reasons; no user text or exception details leak.

## Actual backend handoff and independent CLI

```python
from backend.query_integration import prepare_confirmed_query, checked_ranked_proposal
from rag.query_retriever import retrieve_query_evidence

prepared = prepare_confirmed_query(
    "rental_deposit", {"dispute_with": "landlord", "claim_amount_sgd": 2000},
    query="landlord deposit amount", confirmed=True,
)
proposal = retrieve_query_evidence(prepared, expected_source_version="kb-2026-11-01.1")
if proposal["retrieval_status"] == "FOUND":
    checked = checked_ranked_proposal(
        prepared, proposal["proposed_rule_ids"], proposal["ranked_evidence_ids"],
        expected_source_version=proposal["source_version"],
    )
    # Consume only if checked is also FOUND; revalidate again at final projection.
```

Three offline integration cases exercise this actual composition for landlord,
agent conduct and consumer. Both the ranker and adapter can be given the same
isolated `repository=` instance for safe tests. Never exercise quarantine writes
against the public production database.

From an installed repository root:

```powershell
python -m pip install -r tests/contracts/requirements.txt
python -m rag.query_retriever rag/examples/query_rental.json --source-version kb-2026-11-01.1
python -m rag.query_retriever rag/examples/query_consumer.json --source-version kb-2026-11-01.1
python -m pytest tests/rag/test_query_retrieval.py tests/backend/test_task13_integration.py -q
python -m rag.freshness_report --output instance/task13-live-sources.json
```

CLI exit codes are 0/1/2 for FOUND/NO_RESULTS/ERROR. The example files contain
synthetic confirmed facts only. Use the actual current source version in real
caller code; do not assume the example's version remains current forever.

## Verification and integration boundary

[Task 13 execution record](../docs/test-results/task13-rag-20261106.json) records
actual commands/results and separately captured live source checks. Read-time
provenance validates the checked snapshot, not live reachability on each query.
A timeout/403/drift must remain an observed freshness failure; this feature
never auto-renews a review or replaces hashes. Historical CASE runner 403 is not
reported repaired by a later independent successful observation.

This small lexical/tag corpus is not semantic understanding: unlisted synonyms
may yield no match, and term overlap does not resolve negation or applicability.
Upstream confirmation/clarification and downstream source checks remain needed.
All legal rule flags stay disabled. Runtime connection to Task 12 preview and
the frontend remains backend/Task 15 integration work; this Task delivers the
query function, versioned handoff, deterministic tests and exact adapter proof.
