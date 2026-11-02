# Task 6 — Frontend FE-01–08 executed results

Scope: Guanyu-Lu, frontend/ only. This manifest defines FE IDs for this audit using the topics in Issue #6 and the IT Team Guide (the guide does **not** prescribe individual fixed FE input vectors). Existing Task 5 browser script was adapted for eight **actual** Chromium runs. No API responses were intercepted, stubbed, or supplied by the browser tests.

- Baseline: main commit `7f5e86111dc04a5d2b4cf0e9b1862bcc7e22b48f`, 2026-11-02.
- Candidate tested: `d8649db794dfeb47960bcc5e9444235861971c66` (Task 6 frontend testing branch).
- Tester: Guanyu-Lu frontend automated runner (GitHub-hosted Ubuntu Chromium + existing integration Flask app).
- Successful execution time: **2026-11-02 13:30 UTC / 21:30 Singapore**, via [PR CI run #41453501977](https://github.com/Chu-Junjie/SG-Navi/actions/runs/41453501977).
- API: actual same-origin POST `/api/navigate`, no Playwright routing or mocked responses. Inputs are **synthetic** and do not establish eligibility.
- Limitations: production rules remain disabled; real `SUPPORTED_PATH` or an evidence-backed legal Action Card is **not** demonstrated. `REFER_TO_OFFICIAL` safely shows source references as research context only. This audit covers the frontend-owned FE suite, not the eight separate backend-owned E2E IDs.

| Test ID | Input / execution | Expected | Actual in browser | Result | Commit | Tester | Executed at | Bug issue |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| FE-01 | Rental, all fields initially null; submit; click backend follow-up | 9 fields, NEED_CLARIFICATION, focus goes to asked field | 9 fields, NEED_CLARIFICATION; focus on first question field | PASS | d8649db | Chromium automated, Guanyu FE | 21:30 SGT | — |
| FE-02 | Consumer, all initially null; submit | 9 fields, NEED_CLARIFICATION | 9 fields; NEED_CLARIFICATION | PASS | d8649db | Same | 21:30 SGT | — |
| FE-03 | Rental dispute_with=unknown, resolution_attempted=false, documents_available=unknown, claim_amount_sgd=null | Unknown distinct from false/null; backend asks for missing amount | unknown literal preserved, false preserved, amount null; NEED_CLARIFICATION with amount question | PASS | d8649db | Same | 21:30 SGT | — |
| FE-04 | Complete synthetic Rental; edit amount from 123 to 456; change case twice | Real referral, 2 source links, stale sources cleared on edit, new amount submitted, draft preserved | REFER_TO_OFFICIAL, two source links, cleared on edit, request amount 456, draft retained | PASS | d8649db | Same | 21:30 SGT | — |
| FE-05 | Enter -1 amount, then impossible 2026-02-30 date, then repair as 123 / 2026-02-28 | Invalid entries do not POST; corrected entries submit | Zero POSTs on invalid entries; corrected request processed (NEED_CLARIFICATION) | PASS | d8649db | Same | 21:30 SGT | — |
| FE-06 | Complete synthetic Consumer; inspect seven sections, source URLs and warning | REFER_TO_OFFICIAL, action_card null, 7 visible sections, 2 source links, no legal eligibility claim | REFER_TO_OFFICIAL, 7 sections, 2 valid clickable source references with safe link attrs, accurate disclaimer | PASS **after test assertion correction** | d8649db | Same | 21:30 SGT | See below |
| FE-07 | Complete Rental; Chromium blocks /api/navigate; unblock and retry | Safe error, no stale sources, answers retained, recover after retry | Service unavailable, links cleared, 123 retained; retry REFER_TO_OFFICIAL | PASS | d8649db | Same | 21:30 SGT | — |
| FE-08 | Browser device widths 390 and 320 px; focus case selector then Tab | No horizontal overflow; Tab moves to first answer select | 390/390 and 320/320 scrollWidth/clientWidth, focus input-dispute_with | PASS | d8649db | Same | 21:30 SGT | — |

## Real failure and correction history

**Initial execution failed FE-06 while FE-01–05 and FE-07–08 passed**, recorded in [GitHub push run #41453216243](https://github.com/Chu-Junjie/SG-Navi/actions/runs/41453216243), commit `4e8c4c8`. The browser actually produced the disclaimer `does not establish legal eligibility`, but the test script asserted the different wording `do not establish legal eligibility`. Evidence links were present; the failure arose from a mismatched test text assertion, not from a missing API response or an application defect.

Reproduction at the original test commit:
1. Start the existing integration Flask app and run the real Chromium FE test runner (command below).
2. FE-06 completes Consumer facts, gets a real REFER_TO_OFFICIAL result, verifies two source URLs and seven sections, then tests exact disclaimer text.
3. The assertion fails at `frontend/tests/task6_fe_browser.mjs` (the FE-06 `note.includes(...)` assertion). Browser throws an `AssertionError` for `do not establish legal eligibility`.

**Frontend-only fix:** update the expectation to the existing, semantically accurate `does not establish legal eligibility` from `frontend/task5-flow.html`. No production application code, backend rule, shared contract, or evidence record changed. Correction commit: `021d71d`. Real full-suite recheck passed eight cases on [PR run #41453344023](https://github.com/Chu-Junjie/SG-Navi/actions/runs/41453344023) and again on run #41453501977. A later frontend-only commit `d8649db` prints the full browser result matrix in CI logs; it does not change test logic.

## Reproduce on a machine with Flask, Node.js 22+, and Chrome/Chromium/Edge

From the repository root:

```powershell
python -m pip install -r tests/contracts/requirements.txt
python -m unittest discover -s frontend/tests -v
```

The Python test `frontend/tests/test_task6_real_browser.py` runs Flask on a temporary loopback port, launches a real Chromium/Edge browser via Node, and checks FE-01–08. If no compatible Node/browser executable is found, the Python test explicitly reports **SKIP / NOT RUN**. In that case the FE acceptance must not be inferred from other unit-test successes. The browser check script can also run against an already-started one-process integration server:

```powershell
python -m flask --app integration.app run --host 127.0.0.1 --port 5055
node frontend/tests/task6_fe_browser.mjs http://127.0.0.1:5055 "C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"
```

The CI evidence above is a real Ubuntu Chromium run. **A separate Windows Edge run was not performed for this FE suite.** Frontend evidence validation was additionally covered in previously merged Node source safety tests, but this run does not establish that external websites were actually opened or that any legal path is supported.

## Team acceptance boundary

FE-01–08 are complete for this execution environment. Team Task 6 is **not closed** by these results: Zheng must supply BE-01–10 plus E2E-01–08 (and explain the disabled legal Action Card limitation); Junjie supplies RAG-01–12. Team review and unresolved bugs must be evaluated before candidate acceptance.
