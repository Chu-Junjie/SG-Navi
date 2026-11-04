# Task 7 — Public GitHub Pages frontend: real API configuration and verification status

**Updated:** 2026-11-04 UTC. **Frontend code configured for the verified HTTPS demo backend; public browser end-to-end NOT RUN / NOT ACCEPTED.** This document is independent of the earlier LOCAL candidate browser evidence in `TASK7_CANDIDATE_DEMO.md`.

## Actual remote API evidence — supplied by Zheng (not Guanyu's browser run)

- URL: **https://sg-navi-api-free-demo.onrender.com**
- Provider: **Render Free, ephemeral**, no persistent RAG quarantine disk and no guaranteed retention after restart. **Not** a production deployment or an accepted release candidate.
- Backend deploy SHA: `635ded120e4dfa3196b6c30b3b162c9d77dd5cf5`, deployed 2026-11-04 06:39 UTC.
- Remote 10/10 checks: [Zheng's GitHub Actions run 41787144159](https://github.com/Chu-Junjie/SG-Navi/actions/runs/41787144159), JSON at `docs/test-results/task7-free-render-remote-smoke.json`. **These are Zheng's remote API checks, not Pages browser results.**
- The remote data says `GET /api/health = 200`, `/api/version = 1.0 / mock-1 / kb-2026-11-01.1`, Pages-Origin OPTIONS = 204, both synthetic POSTs = 200 `REFER_TO_OFFICIAL` with two verified source Evidence records and `action_card: null`.
- Public RAG quarantine persistence/restart/restore remains unverified/unsupported on this free instance. No legal eligibility or supported pathway is claimed.

## Frontend changes in this PR

- `frontend/js/api-config.js`: pinned **the real owner-provided HTTPS demo origin** above; GitHub Pages URLs resolve to this host rather than Pages' own missing `/api/`; local Flask still resolves to same-origin `/api/`.
- `frontend/task5-flow.html`: header now links to `../` so it returns to the real GitHub Pages project root `/SG-Navi/`, and still returns to `/` on local Flask.
- `frontend/tests/test_api_config.cjs`, `test_task7_public_config.py`, and `test_task7_home_links.py`: updated to assert the real demo URL and page navigation. The existing form validation, unknown/null/false, source URL verification and fail-closed rules remain unmodified.
- `frontend/tests/task7_public_pages_check.mjs`: fixed its erroneous initial `new URL('/', base)` navigation (which escaped the `/SG-Navi/` Pages project), adjusted cold-start browser timing, and asserts every `/api/navigate` POST goes only to the approved origin. The prepared script uses real Chromium and real remote API responses, no intercepted mocks.
- All production code changes remain in `frontend/` (not backend, shared, RAG or GitHub Pages root).

## Current blocker — Pages root index.html is OUTSIDE Guanyu's owner scope

The published GitHub Pages project root is **https://chu-junjie.github.io/SG-Navi/**, served by repository root `index.html`; it still has two **FLOW COMING SOON** placeholders and no navigation to real forms. Although `frontend/index.html` works in local Flask and is accessible as a separate deep page after publishing, it is **not** the actual Pages root.

User/Junjie instructions require owner coordination before modifying files outside `frontend/`. There is **no verified explicit authorization** in this conversation/Issue #7 comments to change repository root `index.html`. Therefore **we have not edited it**. Obtain an explicit approval and make a separate root-index PR, or ask Junjie to apply `frontend/PAGES_ROOT_PATCH_PROPOSAL.md`. The real target form URLs will be:
- `https://chu-junjie.github.io/SG-Navi/frontend/task5-flow.html?case_type=rental_deposit`
- `https://chu-junjie.github.io/SG-Navi/frontend/task5-flow.html?case_type=consumer_complaint`

## Public verification classification — as actually observed

| Check | Result | Evidence / limitation |
|---|---|---|
| Zheng real remote HTTPS backend and Pages CORS | **PASS per Zheng's separate API smoke** | GitHub Actions run 41787144159, 10/10; NOT Guanyu's browser run |
| Frontend API origin configured with verified real URL | **CODE COMPLETE** | This branch; existing local CI checked; no Pages publication yet |
| GitHub Pages root buttons open the real forms | **BLOCKED (known stale root code)** | Root index.html remains untouched pending owner approval |
| Pages browser Rental initial clarification/complete referral/edit | **NOT RUN** | Pages root fix and publication not complete |
| Pages browser Consumer initial clarification/complete referral/edit | **NOT RUN** | Same |
| Public external source click-out | **NOT RUN** | DOM links tested in separate local Task 7 only |
| Public network failure/retry, 390px/320px layouts | **NOT RUN** | Same |
| Public desktop/mobile screenshots | **NOT RUN; 0 actual Pages screenshots** | Prior local screenshots must not be reused |
| Guanyu personal clean clone/install/test | **NOT RUN on personal workstation** | Container clone failed DNS; see independent record |

**No public browser PASS is claimed.** GitHub Actions Python/Node CI, even when passing, is NOT equivalent to deploying this PR to Pages and running the public browser. A complete public acceptance requires the owner-approved root entry, actual Pages publication, two real browser journeys with 18/18 steps, four newly captured public screenshots, external source click observation if required, and exact published/frontend/API SHA.

## Commands for the next authorized public run

From a machine with Node.js 22+ and Chromium/Edge, after root fix and API config are **merged/published**:

```powershell
node frontend/tests/task7_public_pages_check.mjs "https://chu-junjie.github.io/SG-Navi/" "C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe" "https://sg-navi-api-free-demo.onrender.com"
```

The script saves real screenshots under ignored `instance/task7-public-pages-browser/`. Add actual public trace/screenshots to **new `frontend/demo-evidence/public-pages-*` files** in a follow-up PR, separate from previous local candidate evidence. If the public service sleeps or fails, record the actual time/error and do not fabricate successful browser steps.

## Remaining owner tasks

1. **Junjie:** explicit authorization or own PR to fix root `index.html`, and accept/review this frontend PR.
2. **Guanyu:** after publication, actual Pages browser tests/screenshots/results; additionally do own Windows fresh clone, .venv/install/start/test and record exit codes, SHA, PASS/FAIL/SKIP.
3. **Zheng:** clarify ephemeral free backend state and any real restart/backup limitation before release; remote backend 10/10 is valid but not durable storage acceptance.
4. **Junjie:** final candidate/version reconciliation and freeze only after all evidence; no `v0.9.0-rc1` claimed here.
