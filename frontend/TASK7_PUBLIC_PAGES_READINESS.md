# Task 7 — Public Pages / HTTPS API readiness (NOT PUBLIC E2E VERIFIED)

Status on 2026-11-04: **BLOCKED / NOT RUN**. Keep this evidence separate from the previously completed LOCAL candidate demonstration in TASK7_CANDIDATE_DEMO.md. No real public API URL or deployed SHA has been supplied by Zheng. PR #51 proposes a free, explicitly ephemeral deployment but is not proof of a running HTTPS service.

## Current blockers
- The GitHub Pages root uses repository root index.html, which is still the old Flow coming soon placeholder. The functional frontend/index.html is available as a deep static path, but is not the published home page. The proposed root fix needs approval from Junjie: see PAGES_ROOT_PATCH_PROPOSAL.md. No file outside frontend/ was changed by this PR.
- Zheng must supply the actual verified HTTPS API origin and CORS proof for the exact origin https://chu-junjie.github.io. The current API Origin constant is empty by design; never substitute a guessed service URL.
- The static Pages host has no Flask /api/navigate endpoint. Frontend source files load via /SG-Navi/frontend/ and their relative paths.

## Frontend implementation
- frontend/js/api-config.js: selects same-origin local Flask /api endpoints, or a verified explicit HTTPS backend for this exact Pages project. Invalid, mock, local or missing origins fail closed. Allowed routes are limited to health, navigate, version and case-types. No credentials are stored.
- frontend/index.html: uses the resolver to check health, shows Public API not configured when the backend is unknown. Its two working buttons still open the real form from the deep frontend path.
- frontend/task5-flow.html and js/task5-flow.js: use resolver for POST navigate; missing public API gives a visible no-submission message and preserves inputs. Existing unknown, edit, four-status display and evidence validation are unchanged.
- frontend/tests/test_api_config.cjs + Python test runner check source-origin safety. Existing local browser/Flask CI remains separate.

## Exact public handover after Zheng deploys
1. Zheng confirms actual service origin, deployed Git SHA, safe live GET /api/health and /api/version, CORS OPTIONS and both synthetic POST /api/navigate responses from the GitHub Pages origin. A provider dashboard link is not an API URL.
2. In a NEW frontend-only PR, set HTTPS_API_ORIGIN in frontend/js/api-config.js to that verified HTTPS ORIGIN (no /api path or secrets). Test in CI and browser.
3. Get Junjie's authorization to change the repo ROOT index.html per PAGES_ROOT_PATCH_PROPOSAL.md, either via Guanyu's explicitly authorized PR or Junjie's own PR. This file is out of the frontend-only scope and NOT MODIFIED here.
4. After Pages publish, run the real Chromium public Pages script below. Store new public-pages screenshots/results separately; never reuse local candidate screenshots.
5. Record the exact Pages revision, backend SHA, API/rule/source versions returned by the service, browser version/time, actual PASS/FAIL/SKIP counts and any external-source navigation failures in Issue #7.

## Public browser execution command — prepared, NOT RUN
Requires Node.js 22+ and Chromium/Edge; run from repo root:

    node frontend/tests/task7_public_pages_check.mjs "https://chu-junjie.github.io/SG-Navi/" "C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe" "https://ACTUAL-VERIFIED-HOST.onrender.com"

The third argument above is a PLACEHOLDER, not an available host. Replace it only after Zheng verifies a genuine service. The script visits the actual public homepage, checks two case buttons, real POSTs to the specified HTTPS origin, both clarification/referral journeys, reviewed source links, editing, simulated network-failure/retry, four real full-page JPEGs and 390/320px widths. It rejects wrong-origin form POSTs. Captures go to ignored instance/task7-public-pages-browser/. Do not publish captured real user input; the script uses only synthetic facts.

## Actual public verification status (do not invent pass)
| Check | Status | Reason |
| --- | --- | --- |
| HTTPS backend reachability + CORS | NOT RUN / BLOCKED | Real deployed API origin not supplied |
| Public root navigation | BLOCKED (known code defect) | Root index.html still placeholders; needs owner approval |
| Public Rental real submit, edit, referral and links | NOT RUN | Missing API/root |
| Public Consumer real submit, edit, referral and links | NOT RUN | Missing API/root |
| Public error recovery and source link click-through | NOT RUN | No genuine public browser run |
| Public mobile screenshots and width checks | NOT RUN | No genuine public browser run |
| LOCAL candidate two-case journeys | PASS (different test scope) | See prior TASK7_CANDIDATE_DEMO.md; not a public result |

Legal boundary: real conservative referral uses REFER_TO_OFFICIAL with action_card null. Seven visible fallback sections do not imply legal eligibility. Rule mock-1 is disabled at last audited local snapshot. No supported legal path, host persistence, production readiness or release tag claimed.
