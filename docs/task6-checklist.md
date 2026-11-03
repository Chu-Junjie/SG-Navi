# Task 6 acceptance — PASS WITH LIMITS

Decision: **Accept the technical testing stage with the explicit E2E-01/02 legal
Action Card limitation.** All 38 formal IDs have actual records: **36 PASS,
2 LIMITED, 0 FAIL, 0 NOT RUN**. Merging the peer-reviewed closeout PR records this
decision and closes Issue #6. Task 7 is not started by this record.

Audited main: `49cc19f6c9d957a256fe2024d700fab0f6d215f4`, **2026-11-03**.
Coordinator: Codex automated rerun of the merged owner tests. Environment: Windows,
Python 3.14.6, Node 24.18.0 and actual headless Microsoft Edge. Test inputs were
synthetic. This is not a claim that each member performed a fresh Windows install.

## Team gate

| Requirement | Observed evidence | Decision |
| --- | --- | --- |
| All owners provide actual output | RAG #43, FE #44 and BE/HTTP-E2E #45 merged, with real owner records, peer approvals and successful CI | Pass |
| Eight E2E IDs executed | Eight real loopback HTTP tests passed their technical assertions; E2E-01/02 do not implement supported legal Action Cards | Six Pass; two Limited |
| Real frontend behavior | FE-01–08 executed in an actual browser during the latest full suite; no skipped browser test, supplied API responses or JavaScript exceptions | Pass |
| RAG and integrity fixes | All 12 RAG groups passed; current-review and quarantine-history fixes are merged; five canonical files unchanged | Pass |
| Known serious defects addressed | #38, #41 and #42 verified closed. Repository open-Issue search returned only task Issues #6/#7, with no open defect Issue | Pass for the inspected issue register |
| Version/source evidence | All five API/RAG/version diagnostics and 11 shared examples passed; five real publisher pages matched current fingerprints and all 26 excerpts | Pass |

## Executed results

The latest complete command actually executed was:

```powershell
python -X utf8 -m pytest tests/contracts tests/backend frontend/tests tests/rag tests/integration -q --junitxml=instance/task6-closeout-suite.xml -o junit_logging=out-err -o junit_log_passing_tests=true
```

Result: **375 passed, 7 subtests passed in 56.10s**, exit 0, no skipped tests.
The local JUnit record contains 375 testcase elements. Captured stdout from the
passed real-browser test provides the eight FE results; these were extracted
directly rather than recreated from expectations. BE/E2E rows below come from
the executed JUnit testcases. Matrix IDs and parameterized framework test counts
are different measures and are not added together.

| Owner matrix | Actual latest result | Detailed evidence |
| --- | --- | --- |
| Guanyu-Lu FE-01–08 | Eight real Edge cases PASS; null/unknown/false, editing, validation, source links, failure/retry, 390/320 px and basic Tab focus; zero JS exceptions | [Current browser JSON](test-results/task6-closeout-fe.json); [owner record](../frontend/TASK6_FE_RESULTS.md) |
| ZhengZaikun BE-01–10 | Ten named backend groups PASS | [Current BE/HTTP JSON](test-results/task6-closeout-be-e2e.json); [owner record](task6-backend-e2e-results.md) |
| Chu Junjie RAG-01–12 | All 12 groups PASS; full RAG suite **121 passed in 30.78s**, no skips, canonical hashes unchanged | [Current RAG JSON](test-results/task6-closeout-rag.json); [original owner audit](task6-rag-results.md) |
| ZhengZaikun E2E-01–08 | All eight HTTP technical tests passed; six accepted as PASS and two as LIMITED | Per-ID disposition below and [current JSON](test-results/task6-closeout-be-e2e.json) |

These are complementary browser and actual HTTP checks. The HTTP E2E tests do not
drive JavaScript. FE tests observe real browser requests without stubbing API
responses. Backend failure/invalid-evidence tests deliberately inject synthetic
faults; FE network-failure checks block a browser request. They are recorded as
fault tests rather than claims of an actual publisher or deployed-service outage.

## Eight E2E dispositions

| ID | Actual outcome on audited main | Acceptance |
| --- | --- | --- |
| E2E-01 Rental | HTML delivered; empty facts clarify; completed facts call real API/RAG and return reviewed source-context referral; edited amount accepted. Legal Action Card remains null | **LIMITED**: technical flow passes; supported legal route/Card unavailable |
| E2E-02 Consumer | Real clarification, checked Consumer sources, conservative referral and edited response. Legal Action Card remains null | **LIMITED**: technical flow passes; supported legal route/Card unavailable |
| E2E-03 Missing amount | Null/unknown amount prompts clarification without a guessed number | PASS |
| E2E-04 Unclear landlord/agent | Null/unknown dispute party prompts clarification before any supported route | PASS |
| E2E-05 Business purchase | Project-scope referral, no unsupported Evidence/Card | PASS |
| E2E-06 Supplier outside pilot | Reported false Singapore registration produces safe referral and no source list | PASS for this declared input/scope representation |
| E2E-07 Invalid/conflicting evidence | Injected invalid/no-results records produce no invented citation/Card | PASS for structured validation/failure coverage |
| E2E-08 Backend/RAG failure | Injected exception produces safe ERROR/no Evidence; subsequent request recovers | PASS |

E2E-06 tests the registration fact defined by the present contract. It does not
establish every overseas-supplier jurisdiction rule from a free-text location.
RAG conflict checks concern structured source/version/review/state inconsistencies;
arbitrary semantic/legal contradictions are outside the implemented exact lookup.

## Merged work, actual review and CI

| PR | Owner delivery | Verified peer approvals | Latest-head successful CI |
| --- | --- | --- | --- |
| [#43](https://github.com/Chu-Junjie/SG-Navi/pull/43) | RAG matrix and #41/#42 fixes | Guanyu-Lu, ZhengZaikun | [41450161128](https://github.com/Chu-Junjie/SG-Navi/actions/runs/41450161128) |
| [#44](https://github.com/Chu-Junjie/SG-Navi/pull/44) | Actual FE-01–08 browser runner | Chu-Junjie, ZhengZaikun | [41453749559](https://github.com/Chu-Junjie/SG-Navi/actions/runs/41453749559) |
| [#45](https://github.com/Chu-Junjie/SG-Navi/pull/45) | BE/HTTP E2E records and CI integration-test coverage | Guanyu-Lu, Chu-Junjie | [41461907004](https://github.com/Chu-Junjie/SG-Navi/actions/runs/41461907004) |

The existing workflow now includes `tests/integration`; frontend unittest invokes
the browser runner when compatible Node/browser runtimes exist. Missing runtimes
produce an explicit skip, which does not qualify as FE acceptance. The latest
Windows run above had no such skip. Owner logs retain their original execution
dates/commits; this separate coordinator record covers the combined current main.

## Other actual checks and commands

```powershell
python -X utf8 tests/rag/run_task6.py --output docs/test-results/task6-closeout-rag.json
python -m shared.validate_contracts
python -m integration.checks
python -X utf8 -m rag.import_knowledge_base --verify-live
python -m pytest frontend/tests/test_verified_sources_runner.py -q
```

All passed. The last command verifies the #38 fix under Windows default encoding:
**1 passed in 0.63s**. Source checks on 2026-11-03 returned five HTTP 200 responses,
matched current normalized page fingerprints and all 26 excerpts, and wrote no
new source review or version. [Actual live result](test-results/task6-closeout-live.json).
The summary, commands, execution window, formal counts and issue audit are in
[the machine audit](test-results/task6-closeout-audit.json).

Existing install/start commands remain:

```powershell
python -m pip install -r tests/contracts/requirements.txt
python -m flask --app integration.app run --host 127.0.0.1 --port 5000
```

Open http://127.0.0.1:5000/task5-flow.html. RAG itself needs no separate service.
Full browser testing requires Node 22+ and Chromium/Edge/Chrome. Installation was
not repeated here; the full suite started actual temporary loopback servers.

## Boundaries carried to Task 7

- Acceptance covers the technical source-context/referral prototype. All real
  legal rules remain disabled (`rule_version: mock-1`); `source_version` is
  `kb-2026-11-01.1`, API version is `1.0`. E2E-01/02 must stay LIMITED in any later
  handover until genuine supported behavior is implemented and reviewed.
- Actual source links were checked in browser DOM/URL attributes and actual
  publisher pages were fetched separately. Outgoing publisher tabs were not
  opened through browser clicks during this audit.
- No release/tag, deployment, clean installation by all three members or Task 7
  candidate acceptance is claimed. Task 7 must assess these records and limits.
- This closeout edits README/docs and stores actual results. It changes no owner
  module, test implementation, source record, contract, legal rule or CI workflow.

The Task 6 gate permits failures to be fixed/retested or explicitly limited. This
record keeps the two unimplemented legal-Card outcomes visible while accepting
the completed technical test stage. It does not declare production readiness.
