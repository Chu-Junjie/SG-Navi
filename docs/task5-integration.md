# Task 5 integration coordination

Status: **In Progress — coordinator setup ready for review; team gate not accepted.**
Task 4 closeout PR #26 merged as `421370ded2ae3b0479e754c080c2c0752a67b2d5`.

Chu Junjie owns this integration configuration, diagnostics and issue coordination.
Backend, frontend, their tests and CI remain with their module owners. No shared
wire fields, source records, legal rules or activation flags were changed here.

## Work in parallel; accept in order

1. Chu prepares a shared local origin and reproducible checks while Zheng connects
   Backend + real RAG and Guanyu connects Frontend + real API.
2. Confirm the accepted backend Mock baseline, then actual Backend + RAG calls,
   source/version agreement and failed-retrieval handling.
3. Run Rental then Consumer from the real browser through the API and RAG.
   Check follow-up questions, edits, unknown facts, referrals, errors and sources.
4. Owners fix assigned issues in their own PRs. Rerun affected checks and obtain
   another developer's review before merge. Record the final main commit and
   remaining limitations before accepting Task 5 or starting Task 6.

Preparation does not depend on both owners finishing. Final acceptance does.

## One-process local origin

From the repository root, using the existing Python environment:

```powershell
python -m pip install -r tests/contracts/requirements.txt
python -m flask --app integration.app run --host 127.0.0.1 --port 5000
```

Open http://127.0.0.1:5000/task5-flow.html. This uses the real backend app and
serves the existing form/JS/schemas/mappings from the same origin. No proxy, API
key or environment file is needed for this local configuration. Stop with Ctrl+C.
The installation file already exists; installation was not rerun during this audit.

The existing frontend two-process development proxy remains an alternative;
see its owner's [instructions](../frontend/TASK5_INTEGRATION.md).
Do not point the Task 5 acceptance test at `task4-forms.html`: that historical
page intentionally retains Mock responses. The root homepage still has placeholder
entries, so open the Task 5 page directly. This is a local development setup.

## Repeat the checks

```powershell
python -m pytest tests/contracts tests/backend frontend/tests tests/rag tests/integration -q
python -m shared.validate_contracts
python -m rag.import_knowledge_base
python -m integration.checks
```

The last command is a diagnostic with JSON stdout and exit 0/1. It uses synthetic
facts from [fixtures](../integration/fixtures.json), real checked-corpus retrieval,
authoritative citation validation and the actual Flask WSGI handler. A delegating
observer counts calls to the real RAG function, including existing backend import
aliases, without replacing its output. It also compares `/api/version` with the
current bundle. It is an in-process check, not proof of browser HTTP behavior.
If the backend moves retrieval to another process, update the observer with the
owner before treating it as authoritative. All returned false checks remain visible.

With the local server running, Node 22+ and Edge installed, run:

```powershell
node integration/browser_check.mjs http://127.0.0.1:5000
```

An alternative Chromium executable can be supplied as the second argument. This
optional script uses Node's WebSocket and the browser's DevTools protocol, with no
npm packages. It observes actual page network requests; it never intercepts or
supplies API responses. For each scenario it submits blank facts, focuses a
follow-up question, submits complete synthetic facts, then edits and resubmits.
It verifies API transport, seven sections, real source context and visible source
URLs. It exits 1 when a required source display is missing. Temporary browser
profiles stay under ignored `instance/task5-browser/`; the browser is closed at exit.

These diagnostics do not certify legal eligibility, source freshness through a
new live publisher fetch, or all exception paths. No normal request is expected
to manufacture SUPPORTED_PATH while eligibility rules remain disabled.

## Observed results — 2026-11-02

Tested environment: Windows, Python 3.14.6, Node 24.18.0 and headless Microsoft Edge.

| Code under test | Check | Actual result |
| --- | --- | --- |
| Latest main `4468d2775e10c069456772ba7c7ab2a5ef5a6237` (#27 and final #28 merged) + coordinator files | Final full pytest | **316 passed, 5 subtests passed in 32.67s** |
| Same latest main + coordinator files | Final Backend/RAG and real-browser diagnostics | Both real RAG calls pass; version agreement fails. Both browser flows clarify, focus questions, refer and resubmit edits over 3 real API calls, without JS exceptions; public Evidence is empty and sources cannot be displayed |
| Main `1790c77b860d1443734b8d876b6db47331961282` (frontend #27 merged) + coordinator files | Full pytest command above | **297 passed, 5 subtests passed in 29.31s** |
| Same coordinator configuration | Existing shared examples; checked source import | All 11 examples passed; 5 sources / 26 passages / 26 mappings / 5 templates passed |
| Coordinator development origin | Real HTTP smoke check | `/`, health, version, form, JS and both input schemas returned 200; Task 5 form delivery also covered by configuration tests and the candidate browser run |
| Temporary combination: backend #28 `8850c3feeda3ab00ae50993dac5a44389b3e99c8` + frontend #27 `9fda56249164f757230de8ba171dfd49c92b13e0` + coordinator files | Full combined pytest | **1 failed, 313 passed, 5 subtests passed in 30.31s**; the obsolete frontend empty-Evidence assertion failed |
| Same temporary combination | Backend/RAG diagnostic | Both direct retrieval/citation checks and both actual API-to-RAG checks passed; each complete navigation called real RAG once. Source-version consistency failed |
| Same temporary combination | Real browser, both scenarios | Clarification, question focus, referral with 2 Evidence records, amount edit/resubmit and 3 actual API POSTs per case passed; no JS exceptions. **Source links absent in both cases**, so the diagnostic failed |
| PR #28 head above | [CI run 41422487615](https://github.com/Chu-Junjie/SG-Navi/actions/runs/41422487615) | Backend/contracts/RAG: 277 passed. Frontend: 23 tests, 1 failure at the same empty-Evidence assertion. CI failed |

The historical temporary combination was tested in a separate worktree. Backend
#28 was subsequently changed and merged: commits 9abfeb1/ab94efe deliberately keep
validated RAG context internal on unsupported referrals and independently test
that real retrieval occurs. This resolved the empty-Evidence assertion without a
frontend test edit. Final PR #28 [CI run 41423256101](https://github.com/Chu-Junjie/SG-Navi/actions/runs/41423256101)
passed. Green CI does not supply the absent source display.

Latest-main machine-readable results:
[backend/RAG](test-results/task5-main-backend-rag.json),
[browser](test-results/task5-main-browser.json).
Historical candidate results, retained to explain the actual integration finding:
[backend/RAG](test-results/task5-candidate-backend-rag.json),
[browser](test-results/task5-candidate-browser.json).
The coordinator tests are not added to the existing CI workflow; the CI owner
must confirm that change. No new live source capture or complete Task 6 suite
was run, and no supported legal Action Card or official citation click-through
was claimed. These are actual automated checks, not another member's manual review.

## Owner follow-ups

| Issue | Owner | Required next result |
| --- | --- | --- |
| [#29](https://github.com/Chu-Junjie/SG-Navi/issues/29) | ZhengZaikun | `/api/version` source version agrees with real RAG/navigation; explicit version behavior for safe fallback responses |
| [#30](https://github.com/Chu-Junjie/SG-Navi/issues/30) | Guanyu-Lu + ZhengZaikun | Agree source exposure and presentation; make validated contextual source URLs accessible on referrals without implying eligibility. Current backend hides source records and the renderer only links supported cards |
| [#31](https://github.com/Chu-Junjie/SG-Navi/issues/31) | Resolved by backend #28 | Historical empty-Evidence test mismatch resolved; final-head CI passed. Closed with the distinct source-display gap retained in #30 |

The backend supplies real retrieval and keeps findings conservative; FOUND means
source context is available, not legal eligibility. Frontend #27 and backend #28
are merged. Source-version agreement (#29), source presentation (#30), owner fixes
with peer review, affected reruns and the final acceptance decision remain
outstanding. Task 5 and Issue #5 stay open; Tasks 6-7 have not started.
