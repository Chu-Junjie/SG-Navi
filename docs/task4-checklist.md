# Task 4 independent module acceptance

Status: **Done for independent module development**. Final documentation and Issue closure take effect when this closeout PR merges. Audit date: 2026-11-02. Audited main commit: `de5e4f2c12cb107c1185334710acac490c636910`.

## Delivered and reviewed modules

| Owner and module | Merged PR | Verified CI |
| --- | --- | --- |
| ZhengZaikun backend scope, clarification, response assembly and isolated Mock Evidence simulation | [#23](https://github.com/Chu-Junjie/SG-Navi/pull/23) | [41415529365](https://github.com/Chu-Junjie/SG-Navi/actions/runs/41415529365), success |
| Guanyu-Lu schema-generated forms, answer editing and four-state Mock API display | [#24](https://github.com/Chu-Junjie/SG-Navi/pull/24) | [41416904053](https://github.com/Chu-Junjie/SG-Navi/actions/runs/41416904053), success |
| Chu-Junjie exact evidence retrieval, citation checks, source updates and quarantine | [#25](https://github.com/Chu-Junjie/SG-Navi/pull/25) | [41417932706](https://github.com/Chu-Junjie/SG-Navi/actions/runs/41417932706), success |

Each PR has actual approval submissions from another developer. This audit checked the GitHub review records and merge states; it does not invent retrospective approvals.

## Actual closeout validation

Environment: Windows, Python 3.14.6, pytest 9.1.1 and installed Microsoft Edge in headless mode for browser checks. All inputs were synthetic.

| Check | Expected | Actual |
| --- | --- | --- |
| `python -m pytest tests/contracts tests/backend frontend/tests tests/rag -q` | All independent modules and existing checks pass | **278 passed, 2 subtests passed in 31.47 seconds** |
| `python -m shared.validate_contracts` | Shared examples match the contract | All 11 passed |
| `python -m rag.import_knowledge_base` | Checked source bundle loads | Passed: 5 sources, 26 excerpts, 26 mappings, 5 templates |
| `python -m rag.repository check-live --actor Codex-task4-closeout --state-file instance/task4-closeout-live.json` | Current official-publisher pages match their recorded reviews | All five MATCHED; separate ignored local state path used |

## Frontend browser checks

The audit served the existing frontend/ files from a temporary loopback HTTP server and opened task4-forms.html in a fresh headless Edge profile. It exercised real page JavaScript and the existing local JSON fixtures, not fabricated browser results. The browser and server were closed afterward.

- Both Rental Deposit and Consumer Complaint, all four Mock statuses and widths 1366, 390 and 320 pixels: **24 combinations passed**.
- Both cases rendered the nine agreed input controls and all seven Action Card sections. Synthetic evidence remained marked Needs verification.
- No horizontal page overflow in any combination; no JavaScript exceptions observed. The 390-pixel page capture was visually inspected.
- At all three widths, Tab moved from the scenario selector to the first dynamic answer control. This is a basic keyboard check, not a full accessibility audit.
- Edited the synthetic amount from 123 to 456; switching cases and returning preserved it.
- Request JSON retained the three agreed envelope fields and distinct unknown, null and false values.
- A negative amount produced INPUT ERROR; correcting it restored the Mock flow.

To reproduce manually, run `python -m http.server 8000 --directory frontend`, open http://127.0.0.1:8000/task4-forms.html, select each case/status and repeat the edits above at the stated widths. The [browser result matrix](test-results/task4-browser-results.json) records all 24 combinations and the behavior checks. Screenshots and the browser profile remain internal QA artifacts; no private data is committed.

## Backend and RAG scope

The backend suite covers scope referral, clarification, input errors and four contract states. SUPPORTED_PATH is exercised only through an explicitly gated synthetic unit-test fixture; normal HTTP callers cannot enable that simulation or receive an unsupported legal conclusion. Rule thresholds and source-based eligibility activation remain disabled.

The RAG suite covers complete exact-rule retrieval, case/source separation, unusable evidence, provenance/citation mismatches, stale versions, changes after retrieval, persistent quarantine, explicit release, checked updates and write failures. All canonical source facts and shared fields remain unchanged by this closeout.

## Handoff to Task 5

Task 4 acceptance concerns independent modules with mocks. Frontend-to-backend wiring, replacement of Mock Evidence with the real retrieve_evidence function, source-backed routing decisions and full end-to-end flows are not claimed here. Task 5 must first verify Backend + RAG, then Frontend + Backend, and retain unknown, failure and citation checks. Source review identity remains the recorded automated check rather than official or human legal approval.
