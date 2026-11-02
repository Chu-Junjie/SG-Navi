# Task 4 RAG validation results

Executed on 2026-11-02 in the owner's Windows workspace, based on main commit `83273596e5b75b9ecfe9622804fb64f70c743fd3` after Task 3 closeout PR #22 merged.

Environment: Python 3.14.6, pytest 9.1.1, jsonschema 4.26.0 and referencing 0.37.0.

| Check | Actual result |
| --- | --- |
| `python -m pytest tests/rag/test_retrieval.py -q` | 67 passed in 17.04 seconds |
| `python -m pytest tests/contracts tests/backend frontend/tests tests/rag -q` | 255 passed and 2 subtests passed in 26.88 seconds |
| `python -m shared.validate_contracts` | All 11 shared examples passed |
| `python -m rag.import_knowledge_base` | Passed: 5 sources, 26 passages, 26 mappings and 5 templates |
| Rental batch retrieval plus Citation Validator on the real checked corpus | FOUND, complete Evidence records and citation validation passed |
| Consumer CASE Rule ID CLI query | FOUND with the correct source and six-field Evidence format |
| `python -m rag.repository check-live --actor Codex-live-source-check --state-file instance/task4-live-check.json` | All five current official-publisher pages MATCHED the current review fingerprints and excerpts |

The live check used a separate ignored local state path. No source facts, review metadata, canonical files, backend/frontend code or shared schema changed. The module does not activate rules or infer legal applicability from facts.

The new tests cover exact lookup and source separation, deterministic ordering, many-rule/shared-evidence deduplication, complete batch coverage, unreviewed/quarantined filtering, invalid requests, unknown/null/false facts, bad metadata/IDs/citations, stale versions, source changes after retrieval, fresh state reads, source updates and invalid update refusal. They also exercise persistent quarantine across instances/versions, no automatic release, release checks, changed/offline source detection, malformed state, atomic write failure, writer contention and CLI exit behavior.

Negative source/version fixtures and mocked live pages are synthetic tests, not actual source approvals. Backend integration, runtime legal routing, frontend flows, performance at a larger corpus and a new FTS5 index are outside this Task 4 RAG validation. Existing CI is configured to include tests/rag/; the CI result for this PR must be checked separately from these local results.
