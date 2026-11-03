# Task 6 — Chu Junjie's RAG acceptance

Status: **Historical RAG owner record; PR #43 is merged and #41/#42 are closed.**
The audit below preserves its original 2026-11-02 baseline/results. The combined
2026-11-03 FE/BE/RAG/E2E decision is in [Task 6 acceptance](task6-checklist.md).

Audit baseline: main `a6b5c896de70c4f672bfc18903ae34d5e329a4e7` plus this RAG fix,
2026-11-02. The [machine record](test-results/task6-rag-results.json) binds the exact
working-tree code to SHA-256 hashes; its commit field is the baseline, not a claim
that uncommitted fixes already existed in that main commit. Tester: automated Codex
execution on Windows, Python 3.14.6. Times in machine records are UTC.

The team guide names RAG-01–12 and topics but does not define each numbered case.
The [manifest](../tests/rag/task6_matrix.json) defines this audit's operational
grouping explicitly. Groups select actual pytest outcomes from the full RAG suite;
group counts are not a replacement for the full suite count and may overlap.

## RAG-01–12

| Test ID | Input / expected behavior | Actual | Result | Bug |
| --- | --- | --- | --- | --- |
| RAG-01 | Rental exact SCT lookup, source trace and six-field Evidence schema | 3 selected cases passed | Pass | — |
| RAG-02 | Consumer exact CASE lookup, deterministic isolated results | 2 selected cases passed | Pass | — |
| RAG-03 | Rental landlord/agency mappings kept separate; wrong case/template refused | 3 selected cases passed | Pass | — |
| RAG-04 | Empty/unknown/wrong-case IDs, malformed requests, null/unknown/false facts | 12 selected cases passed; no guessed facts or partial batch | Pass | — |
| RAG-05 | Bad Evidence IDs, URLs/metadata, duplicate/partial/empty citations | 17 selected cases passed; typed rejection | Pass | — |
| RAG-06 | Unreviewed/quarantined sources and evidence obtained before quarantine | 7 selected cases passed; cross-instance block effective | Pass | — |
| RAG-07 | Current versions/review identity, stale citations and historical hash fallback | 5 selected cases passed | Pass | [#41](https://github.com/Chu-Junjie/SG-Navi/issues/41) |
| RAG-08 | Conflicting current proof and contradictory quarantine/history entries | 6 selected cases passed; no silent repair or Evidence | Pass | [#41](https://github.com/Chu-Junjie/SG-Navi/issues/41), [#42](https://github.com/Chu-Junjie/SG-Navi/issues/42) |
| RAG-09 | Synthetic page outage/change, absent excerpts, unreadable bundle or malformed state | 8 selected cases passed; safe errors/blocks | Pass | — |
| RAG-10 | Repeat checked import/export/reload and failed rebuild | 4 selected cases passed; deterministic snapshots and preserved canonical/state files | Pass for applicable rebuild | — |
| RAG-11 | Shared real SCT source in both cases, shared-rule dedup and complete mapping coverage | 3 selected cases passed | Pass | — |
| RAG-12 | Update rollback, quarantine persistence, explicit recovery, atomic failure and writer lock | 9 selected cases passed | Pass | — |

Each machine-record row includes Input, Expected, selected executed test cases and
Actual counts, Pass/Fail/Not Run, baseline commit/code hashes, tester, execution
time and linked bug numbers. A new unmatched selector, skipped case or suite
failure makes the report fail; the runner never marks absent evidence as passed.

## Actual failures and fixes

Initial command `python -X utf8 -m pytest tests/rag/test_task6_integrity.py -q`
against pre-fix runtime code produced **7 failed, 3 passed in 3.34s**.

- **#41 — current proof:** passage verification accepted a historical same-version
  digest when the current row disagreed. Conflicting rows for the same current
  review were also accepted, and import live checks could match an old page hash.
  A common current-review selector now binds version/time/reviewer consistently;
  conflicting fingerprints/digest maps fail validation. Previously retrieved
  Evidence also fails later citation checking after proof becomes inconsistent.
- **#42 — quarantine history:** field-shape checks could accept a deleted block or
  orphan release and return FOUND despite the recorded quarantine. State now
  replays the event history, checks release order and requires the replayed entries
  to match the current blocked table. Inconsistent state produces ERROR and typed
  citation rejection without deleting or repairing the original state.

The first combined post-fix RAG run reported **2 failed, 119 passed in 23.08s**:
one old assertion expected the former error wording and one synthetic successful
capture used the historical CEA review. Updating these RAG-owned fixtures to the
current-review contract preserved their original rejection/positive assertions.
The final runner passed all 121 tests. The initial failures and final evidence are
retained in the [audit record](test-results/task6-rag-audit.json).

Only RAG runtime code and related tests/reporting changed, plus coordination docs.
No canonical source file, review row, source version, legal activation flag,
shared schema, dependency, CI workflow, frontend or backend file changed.

## Exact executed checks

```powershell
python -X utf8 tests/rag/run_task6.py --output docs/test-results/task6-rag-results.json
python -X utf8 -m pytest tests/contracts tests/backend frontend/tests tests/rag tests/integration -q
python -m shared.validate_contracts
python -m integration.checks
python -X utf8 -m rag.import_knowledge_base --verify-live
```

- RAG runner: **121 passed in 20.30s**, all 12 groups passed, no skipped tests and
  all five canonical file hashes unchanged.
- Full regression: **356 passed, 7 subtests passed in 29.91s**.
- All 11 shared examples and all five backend/RAG/version diagnostics passed.
- Real publisher check: five HTTP 200 responses; current normalized page hashes
  and all 26 excerpts matched. See [live results](test-results/task6-live-source-check.json).
  This did not modify source data or create/renew review records.
- Report CLI rejected `--output rag/knowledge_base/unsafe-report.json` with exit 2
  before running tests or creating a file, preserving the five-file directory.

The dependency command remains `python -m pip install -r tests/contracts/requirements.txt`;
installation was not repeated. RAG needs no separate service. Its existing CLI is
`python -m rag.retriever rental_deposit --rule-id SCT_RESIDENTIAL_SCOPE`. For an
integrated page, the existing command remains `python -m flask --app integration.app run`.
Full Windows tests use Python UTF-8 mode as in Task 5's documented configuration.

## Remaining team acceptance and limits

- Guanyu-Lu owns FE-01–08; ZhengZaikun owns BE-01–10 and actual E2E-01–08. This
  mechanical cross-module regression does not replace their formal input/expected/
  actual logs. Issue #6 stays open until team acceptance is complete.
- Normal navigation still clarifies or refers with checked source context. Legal
  rules remain disabled. E2E-01/02 must record any supported-Action-Card limitation
  explicitly, rather than present a referral as verified legal eligibility.
- RAG-08 checks structured provenance/version/state conflicts and explicit source
  quarantine. Arbitrary natural-language contradictions or generated-prose legal
  entailment are not automatically determined by this exact-lookup module.
- RAG-10 validates snapshot rebuild/reload. There is no FTS5/vector index, so no
  nonexistent index rebuild or embedding service is claimed.
- Live-check rejection/outage scenarios use clearly labeled synthetic captures
  in isolated tests. The separate five-page publisher check used real requests.
  No real dispute facts, secrets or publisher approval claims were recorded.
- New RAG regression tests are included in the existing CI's `tests/rag` path.
  CI execution must be checked on the owner PR. The matrix report is generated
  locally; no CI workflow edit or another member's environment pass is claimed.

Task 7 has not started. Issues #41/#42 were closed by the reviewed #43 merge;
the separate team closeout record does not replace the historical evidence here.
