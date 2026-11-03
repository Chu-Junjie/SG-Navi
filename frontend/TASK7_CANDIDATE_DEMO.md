# Task 7 — Candidate frontend demonstration evidence

**Status:** Frontend candidate technical journeys **PASS with explicitly retained legal and deployment limits**. This is not a production release, official case advice or complete Task 7 team acceptance.

## Test identity and reproducibility

- **Main candidate baseline before fixes:** `d629033b27f9eb5a9d0998b7d55304ae86ffe528` (Task 6 closeout main).
- **Browser-tested source commit:** `e2b0070e0fdca7e198fca4eae6d03ba8efddae22` (after candidate navigation fixes).
- **Executed:** `2026-11-03T04:33:03.439Z` UTC on 2026-11-03; Linux GitHub Actions, real headless Chromium, actual `integration.app` Flask and real same-origin `/api/navigate`. Tester: Guanyu-Lu frontend candidate automated run. [GitHub run #41578737031](https://github.com/Chu-Junjie/SG-Navi/actions/runs/41578737031).
- **Inputs:** Only synthetic facts from the already-versioned `integration/fixtures.json`, no personal or real dispute information.
- **Method:** JS DOM interactions, actual network observation and Flask+RAG backend (no API intercept), 1440px desktop and 390px browser mobile emulation, 320px overflow assertion, four actual JPEG screenshots.
- **Results:** 18/18 traced journey steps PASS (9 per case), JavaScript exceptions `0`; browser snapshots below. Both supported legal routes remain unavailable (`SUPPORTED_PATH` not demonstrated).
- **The test runner's Python verifier** asserts 2 complete cases, 4 snapshots and 0 JavaScript exceptions, then fails if any step fails. It explicitly skips if Node 22+ or Chromium is missing. Existing CI run is not a clean installation by each team member.

## Actual step-by-step walkthroughs

The steps below were **actually executed by the browser**, not extrapolated from previous Task 6 records.

### Rental Deposit — 9/9 actual browser steps
| Step | Action | Actual output | Result |
|---|---|---|---|
| 01 | Start on candidate homepage; select topic | Home Online; route /task5-flow.html; selected `rental_deposit`. | **PASS** |
| 02 | Submit all Not provided | NEED_CLARIFICATION; questions: dispute_with, premises_type, claim_amount_sgd. | **PASS** |
| 03 | Follow backend questions, enter nine synthetic case facts | Focused `input-dispute_with`; populated 9 fields. | **PASS** |
| 04 | Submit complete facts to actual backend and RAG | REFER_TO_OFFICIAL; 2 verified evidence records; 7 sections. | **PASS** |
| 05 | Capture actual desktop screenshot | Actual 1440px screenshot, 182919 bytes, horizontal scroll 1425/1425. | **PASS** |
| 06 | Check mobile and capture screenshot | Actual 390px screenshot 170621 bytes; 390px 390/390; 320px 320/320. | **PASS** |
| 07 | Edit answer and re-submit | Edited amount 456; REFER_TO_OFFICIAL; 2 source records; old links cleared while editing. | **PASS** |
| 08 | Block backend call then restore | Service unavailable; answer 456 retained; retry REFER_TO_OFFICIAL. | **PASS** |
| 09 | Click header return to homepage | Returned to /. | **PASS** |

### Consumer Complaint — 9/9 actual browser steps
| Step | Action | Actual output | Result |
|---|---|---|---|
| 01 | Start on candidate homepage; select topic | Home Online; route /task5-flow.html; selected `consumer_complaint`. | **PASS** |
| 02 | Submit all Not provided | NEED_CLARIFICATION; questions: purchase_type, purchase_purpose, supplier_registered_in_sg, claim_amount_sgd. | **PASS** |
| 03 | Follow backend questions, enter nine synthetic case facts | Focused `input-purchase_type`; populated 9 fields. | **PASS** |
| 04 | Submit complete facts to actual backend and RAG | REFER_TO_OFFICIAL; 2 verified evidence records; 7 sections. | **PASS** |
| 05 | Capture actual desktop screenshot | Actual 1440px screenshot, 182965 bytes, horizontal scroll 1425/1425. | **PASS** |
| 06 | Check mobile and capture screenshot | Actual 390px screenshot 168562 bytes; 390px 390/390; 320px 320/320. | **PASS** |
| 07 | Edit answer and re-submit | Edited amount 456; REFER_TO_OFFICIAL; 2 source records; old links cleared while editing. | **PASS** |
| 08 | Block backend call then restore | Service unavailable; answer 456 retained; retry REFER_TO_OFFICIAL. | **PASS** |
| 09 | Click header return to homepage | Returned to /. | **PASS** |


## Real sources, citations and seven sections

### Rental Deposit
- **Actual API status:** `REFER_TO_OFFICIAL` · `action_card: null`; seven sections display the unsupported/verification state, not a generated legal decision.
- **Actual wire versions:** API `1.0` · rule `mock-1` · source `kb-2026-11-01.1`.
- **Backend Evidence metadata, reviewed but not proof of eligibility:**
  - `SCT-ELIG-RESIDENTIAL` · `courts-sct-eligibility` · review `verified` · source version `kb-2026-11-01.1` · [source URL](https://www.judiciary.gov.sg/civil/cases-eligible-small-claim)
  - `SCT-ELIG-AMOUNT` · `courts-sct-eligibility` · review `verified` · source version `kb-2026-11-01.1` · [source URL](https://www.judiciary.gov.sg/civil/cases-eligible-small-claim)
- **Browser links:** 2 link elements; target `_blank` and rel `noopener noreferrer`; matching real API metadata verified. **External tabs were not opened in this run.**
- **Seven rendered card headings:** `Case summary`, `Potential channels`, `Conditions`, `Steps`, `Document checklist`, `Unresolved questions`, `Citations`.

### Consumer Complaint
- **Actual API status:** `REFER_TO_OFFICIAL` · `action_card: null`; seven sections display the unsupported/verification state, not a generated legal decision.
- **Actual wire versions:** API `1.0` · rule `mock-1` · source `kb-2026-11-01.1`.
- **Backend Evidence metadata, reviewed but not proof of eligibility:**
  - `CASE-PERSONAL` · `case-complaint` · review `verified` · source version `kb-2026-11-01.1` · [source URL](https://www.case.org.sg/submit-a-complaint/)
  - `CASE-SG-SUPPLIER` · `case-complaint` · review `verified` · source version `kb-2026-11-01.1` · [source URL](https://www.case.org.sg/submit-a-complaint/)
- **Browser links:** 2 link elements; target `_blank` and rel `noopener noreferrer`; matching real API metadata verified. **External tabs were not opened in this run.**
- **Seven rendered card headings:** `Case summary`, `Potential channels`, `Conditions`, `Steps`, `Document checklist`, `Unresolved questions`, `Citations`.


**Legal limitation:** For both cases, the backend returned **`REFER_TO_OFFICIAL`**, not `SUPPORTED_PATH`. While 2 Evidence IDs and matching source URLs were present, this is **Verified Source Context for independent checking**, not a filing recommendation, an eligibility determination or a seven-section legal Action Card with legally supported steps. Both Action Card objects were `null`, and the frontend rendered seven fallback headings. The backend still reports `rule_version: mock-1` and no active eligibility rules.

## Actual captured screenshots

Each of the following JPEGs is captured via Chromium `Page.captureScreenshot` from the real candidate page, immediately after the **actual** response and verified source display. They are not mockup images or generated previews. Full-page captures, so mobile JPEGs are tall.

| Case | Desktop 1440px | Mobile 390px |
|---|---|---|
| Rental Deposit | [Actual desktop](demo-evidence/rental_deposit-desktop-1440.jpg) | [Actual mobile](demo-evidence/rental_deposit-mobile-390.jpg) |
| Consumer Complaint | [Actual desktop](demo-evidence/consumer_complaint-desktop-1440.jpg) | [Actual mobile](demo-evidence/consumer_complaint-mobile-390.jpg) |

The raw machine-readable trace is [task7-candidate-results.json](demo-evidence/task7-candidate-results.json). The snapshots and JSON retain the original observed run identity `e2b0070e0fdca7e198fca4eae6d03ba8efddae22`; subsequent evidence-only commits do not change the UI source tested.

## Defects detected and fixed before demonstration handover

| ID | Actual pre-fix failure | Exact location | Reproduction | Frontend-only correction | Retest |
|---|---|---|---|---|---|
| T7-FE-01 | Candidate homepage cards remained Task 1 placeholders; selecting either case did not open its completed form. [Failing real CI](https://github.com/Chu-Junjie/SG-Navi/actions/runs/41574975188) | `frontend/index.html` choice labels and `[data-case]` click handler; `frontend/js/task5-flow.js` initialization | Run `integration.app`, visit `/`, click Rental/Consumer: remains on home page and shows placeholder note. | Buttons now open `./task5-flow.html?case_type=...`; the form selects only agreed case enum values from the query parameter. Also replaces stale "Flow coming soon" copy. | Candidate steps 01 PASS for both cases. |
| T7-FE-02 | Clicking SG Navi from the real form navigated to `/index.html`, not the integrated homepage `/`, so return navigation failed. [Failing real CI](https://github.com/Chu-Junjie/SG-Navi/actions/runs/41578606272) | `frontend/task5-flow.html` header `href="./index.html"` | From `/task5-flow.html`, click the SG Navi header: page route not found on the integrated Flask server. | Use `href="./"`, correctly resolving to `/` in both integrated origin and frontend static preview. | Candidate steps 09 PASS for both cases. |

No changes were made to `backend/`, `rag/`, `shared/` or legal-rule configuration. Historical failed CI runs are retained.

## Known limitations and items not asserted as passed

- **Legal action guidance:** Real `SUPPORTED_PATH` eligibility logic and a populated legal Action Card are not available. Seven sections are visible with an absence/verification message, which is not equivalent to seven supported legal recommendations.
- **Sources:** The two source URLs per case were checked against actual backend Evidence metadata and safe link attributes. The browser did not navigate external sites in this run; current publisher availability/fingerprints are covered separately by the Task 6 owner audit, not by these screenshots.
- **Mobile:** Real browser viewport emulation at 390px and 320px passed horizontal-overflow checks. This is not a test on physical iOS/Android devices or a full accessibility audit.
- **API exception:** Test step 08 deliberately blocked a browser request to simulate network failure, then unblocked it. It is not evidence of an actual production outage.
- **GitHub Pages:** The root-level Pages `index.html` was intentionally not modified in this frontend-only candidate PR; static GitHub Pages cannot expose Flask `/api/navigate`. The demonstrated candidate is the **integrated Flask-served** homepage `/`, not the existing static Pages landing page.
- **Versions/release:** A Task 7 candidate tag, rollback/deployment review, clean-install signoffs and final coordinator acceptance are still owned by Junjie/Zheng. This record does not assert any of them.

## Reproduce both demonstrations

From repository root on the exact feature branch (or a later reviewed candidate containing these changes):

```powershell
git fetch origin
git switch feat/task7-frontend-candidate-demos
python -m pip install -r tests/contracts/requirements.txt
python -m flask --app integration.app run --host 127.0.0.1 --port 5000
```

Visit `http://127.0.0.1:5000/` and click either **Open guided form** card. Follow steps 01–09 above for each case. To rerun the full automated proof (Node.js 22+ with Chromium/Edge required):

```powershell
python -m unittest frontend.tests.test_task7_candidate_demo -v
```

Alternatively use `python -m unittest discover -s frontend/tests -v`. The browser script is `frontend/tests/task7_candidate_demo.mjs`. A fresh demonstration must record its own tested commit, actual outputs and screenshots; do not reuse this run's images as evidence for another revision without retesting.
