# Task 7 — ACTUAL PUBLIC Pages → Render browser acceptance (separate from local)

**Execution classification: REAL REMOTE PUBLIC CHROMIUM RUN, technical PASS WITH LIMITS.** This is a new independent public-environment evidence set, not the earlier local Flask candidate screenshot set. User-reported homepage navigation is corroborated here by the real automated Chromium browser.

| Metadata | Actual verified value |
|---|---|
| Public Pages URL | https://chu-junjie.github.io/SG-Navi/ |
| API actually contacted by browser | https://sg-navi-api-free-demo.onrender.com |
| Date/time started | 2026-11-04T07:26:26.914Z (2026-11-04, Singapore +08) |
| Execution platform | GitHub-hosted Ubuntu Actions Chromium headless via Node.js |
| CI/test harness source commit | `99bec00b7a5ce3925d07898d41ac1905f6180bef` |
| Public Pages source revision | Not independently exposed by Pages API in this run; the live browser observed the updated homepage, form and deployed API config |
| Render service deployed SHA (separate backend owner's evidence) | `635ded120e4dfa3196b6c30b3b162c9d77dd5cf5` |
| API / rule / source versions actually reported | `1.0` / `mock-1` / `kb-2026-11-01.1` |
| Real browser results | **18 PASS, 0 FAIL**, 2 scenarios × 9 steps |
| Browser JS exceptions | **0** |
| Actual public Chromium screenshots | **4** verified JPEG images, desktop 1440px + mobile 390px |
| Real 320px overflow checks | 2 PASS (no separate 320px images captured) |
| Raw real run | [GitHub Actions #41792213506](https://github.com/Chu-Junjie/SG-Navi/actions/runs/41792213506) |
| Machine-readable original trace | [task7-public-pages-results.json](demo-evidence/task7-public-pages-results.json) |
| Person's independent Windows clean install | **NOT RUN here**; CI-run evidence is not Guanyu's personal clean clone attestation |

## 1. Full ACTUAL public walkthrough (not local Flask)

### Rental Deposit — 9/9 PASS
| Step | User/browser action | Actual browser observation | Result |
|---|---|---|---|
| 01 | Start on candidate homepage; select topic | Home health Online; public path /SG-Navi/; chosen rental_deposit; form /SG-Navi/frontend/task5-flow.html | PASS |
| 02 | Submit all Not provided | NEED_CLARIFICATION; questions dispute_with, premises_type, claim_amount_sgd | PASS |
| 03 | Follow backend questions, enter nine synthetic case facts | Real focused field input-dispute_with; entered 9 synthetic fields | PASS |
| 04 | Submit complete facts to actual backend and RAG | REFER_TO_OFFICIAL; 2 verified Evidence IDs; 2 safe DOM links; 7 fallback sections | PASS |
| 05 | Capture actual desktop screenshot | Actual screenshot public-pages-rental_deposit-desktop-1440.jpg (182919 bytes); viewport 1440; document scroll/client 1425/1425 | PASS |
| 06 | Check mobile and capture screenshot | Actual screenshot public-pages-rental_deposit-mobile-390.jpg (170621 bytes); 390px scroll/client 390/390, 320px 320/320 | PASS |
| 07 | Edit answer and re-submit | Edited amount 456; backend REFER_TO_OFFICIAL; 2 linked sources; previous sources cleared during edit | PASS |
| 08 | Block backend call then restore | Service unavailable; original answer 456 retained; retry REFER_TO_OFFICIAL | PASS |
| 09 | Click header return to homepage | Clicked header, arrived /SG-Navi/ | PASS |

### Consumer Complaint — 9/9 PASS
| Step | User/browser action | Actual browser observation | Result |
|---|---|---|---|
| 01 | Start on candidate homepage; select topic | Home health Online; public path /SG-Navi/; chosen consumer_complaint; form /SG-Navi/frontend/task5-flow.html | PASS |
| 02 | Submit all Not provided | NEED_CLARIFICATION; questions purchase_type, purchase_purpose, supplier_registered_in_sg, claim_amount_sgd | PASS |
| 03 | Follow backend questions, enter nine synthetic case facts | Real focused field input-purchase_type; entered 9 synthetic fields | PASS |
| 04 | Submit complete facts to actual backend and RAG | REFER_TO_OFFICIAL; 2 verified Evidence IDs; 2 safe DOM links; 7 fallback sections | PASS |
| 05 | Capture actual desktop screenshot | Actual screenshot public-pages-consumer_complaint-desktop-1440.jpg (182965 bytes); viewport 1440; document scroll/client 1425/1425 | PASS |
| 06 | Check mobile and capture screenshot | Actual screenshot public-pages-consumer_complaint-mobile-390.jpg (168562 bytes); 390px scroll/client 390/390, 320px 320/320 | PASS |
| 07 | Edit answer and re-submit | Edited amount 456; backend REFER_TO_OFFICIAL; 2 linked sources; previous sources cleared during edit | PASS |
| 08 | Block backend call then restore | Service unavailable; original answer 456 retained; retry REFER_TO_OFFICIAL | PASS |
| 09 | Click header return to homepage | Clicked header, arrived /SG-Navi/ | PASS |

## 2. Actual source references and eligibility limitations

**rental_deposit:** `REFER_TO_OFFICIAL`; `action_card: null`; rule `mock-1`; source version `kb-2026-11-01.1`. 2 verified Evidence records, 2 rendered links:
- Evidence `SCT-ELIG-RESIDENTIAL` / source `courts-sct-eligibility` / review `verified`: [original publisher](https://www.judiciary.gov.sg/civil/cases-eligible-small-claim)
- Evidence `SCT-ELIG-AMOUNT` / source `courts-sct-eligibility` / review `verified`: [original publisher](https://www.judiciary.gov.sg/civil/cases-eligible-small-claim)
Seven fallback section headings: `Case summary`, `Potential channels`, `Conditions`, `Steps`, `Document checklist`, `Unresolved questions`, `Citations`.

**consumer_complaint:** `REFER_TO_OFFICIAL`; `action_card: null`; rule `mock-1`; source version `kb-2026-11-01.1`. 2 verified Evidence records, 2 rendered links:
- Evidence `CASE-PERSONAL` / source `case-complaint` / review `verified`: [original publisher](https://www.case.org.sg/submit-a-complaint/)
- Evidence `CASE-SG-SUPPLIER` / source `case-complaint` / review `verified`: [original publisher](https://www.case.org.sg/submit-a-complaint/)
Seven fallback section headings: `Case summary`, `Potential channels`, `Conditions`, `Steps`, `Document checklist`, `Unresolved questions`, `Citations`.

The links above were matched against the real backend response and appeared as click-capable DOM anchors with `target="_blank"` and `rel="noopener noreferrer"`. The test did **not** independently click through or verify the external publisher destination loads in a new tab; this specific external navigation is **NOT RUN** and must not be claimed as passed.

The backend still returned **`REFER_TO_OFFICIAL`** (conservative official referral), *not* `SUPPORTED_PATH`. There is **no populated seven-field legal Action Card**: `action_card: null`, and the seven visually rendered headings contain safe fallback/Needs verification text. Verified evidence metadata is context for research, **not proof of legal eligibility**. Legal routing rules remain disabled (`mock-1`).

## 3. Four ACTUAL captured public screenshots

Raw JPEG blobs were extracted from the exact GitHub Actions Chromium `Page.captureScreenshot` output, checked for intact chunk count, JPEG header and total decoded size, and committed without editing or regeneration.

| Case | Desktop real screenshot | Mobile real screenshot |
|---|---|---|
| Rental Deposit | [1440px — 182919 bytes](demo-evidence/public-pages-rental_deposit-desktop-1440.jpg) | [390px — 170621 bytes](demo-evidence/public-pages-rental_deposit-mobile-390.jpg) |
| Consumer Complaint | [1440px — 182965 bytes](demo-evidence/public-pages-consumer_complaint-desktop-1440.jpg) | [390px — 168562 bytes](demo-evidence/public-pages-consumer_complaint-mobile-390.jpg) |

Actual viewport checks: Rental 390/390, 320/320; Consumer 390/390, 320/320 (no horizontal overflow). This is Chrome device emulation, **not a physical mobile handset test**.

## 4. Actual simulated network failure and recovery

For each case, after an initial successful official referral, the browser deliberately blocked `*api/navigate*` using Chromium DevTools. The page visibly reported **Service unavailable**, removed prior source links, and preserved edited amount **456**. The block was then removed; real retry again returned `REFER_TO_OFFICIAL`, with previous answers preserved. This is a deliberate negative test, **not evidence that Render itself went offline**.

## 5. Reproduce this public run (requires actual network)

From an exact checkout with Node.js 22+ and Chromium / Edge:

```powershell
node frontend/tests/task7_public_pages_check.mjs "https://chu-junjie.github.io/SG-Navi/" "C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe" "https://sg-navi-api-free-demo.onrender.com"
```

The source script saves live images under ignored `instance/task7-public-pages-browser/`. For a fresh machine's run, save **fresh** timestamp/SHA/screenshots and results; never reuse the screenshots above as proof of another run.

## 6. Separate obligations that still remain

- Guanyu's **personal** fresh clone → isolated `.venv` → install → Flask startup → pytest with actual PASS/FAIL/SKIP totals still needs execution on his own computer. See `frontend/TASK7_INDEPENDENT_ENV_ATTEMPT.md`; earlier container DNS failure is not a project bug.
- Junjie and Zheng still own final RC freeze/recovery and Render durable state. The free Render backend has **no persistent RAG quarantine disk**; cloud persistence, restart survival and backup/restore are not accepted.
- The completed CI public browser test does not establish a physical device audit, external publisher click success, full source review renewal, any actual legal supported route, or production release.

**Conclusion: Public Pages frontend 18/18 PASS with clear limitations; Task 7 overall remains OPEN.**
