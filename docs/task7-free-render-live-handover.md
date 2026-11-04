# Task 7 — Actual Render Free HTTPS backend deploy (technical demo only)

**Execution date:** 2026-11-04 UTC. **Status: PUBLIC HTTPS API VERIFIED (10/10), FREE NONPERSISTENT DEMO ONLY. NOT READY FOR TASK 7 FREEZE.**

## Verified provider/service identity

| Field | Actual provider result |
| --- | --- |
| Provider / workspace | Render / My Workspace (workspace `tea-dbkmnimgekts73ejog0g`) |
| Service | `sg-navi-api-free-demo`, `srv-dbld56on74is739q3oc0` |
| Actual public API base URL | **https://sg-navi-api-free-demo.onrender.com** |
| Render service URL | https://dashboard.render.com/web/srv-dbld56on74is739q3oc0 |
| Free plan | Render `plan=free`, region Singapore, no disk |
| Initial live deploy | `dep-dbld57on74is739q3prg`, Render status `live`, completed **2026-11-04T06:39:36.761760Z** |
| **Actual live code SHA** | **`635ded120e4dfa3196b6c30b3b162c9d77dd5cf5`** |
| CI/test script SHA for verified public requests | `e22ce642f79c482461ddd32185f1e509d1dcd31d` |
| Deploy branch | `feat/task7-free-render-demo`; autoDeploy **off**, so later docs/test commits are **not** deployed |
| WSGI command | `gunicorn --bind 0.0.0.0:$PORT --workers 1 --threads 4 --timeout 30 backend.production:app` |
| Build command | `pip install -r requirements.txt && python -m rag.import_knowledge_base` |
| CORS origin | `https://chu-junjie.github.io`, **not** `https://chu-junjie.github.io/SG-Navi/` |
| Contract / rule / source versions observed over HTTPS | API `1.0`, rule `mock-1`, source `kb-2026-11-01.1` |
| Sensitive state | `instance/rag_quarantine.json`; **NO persistent disk** in the free service |

### Actual Render install versions (from provider build logs)

Render build on the deployed SHA recorded `Flask-3.1.3`, `gunicorn-23.0.0`, `jsonschema-4.26.0`, `referencing-0.37.0`, `Werkzeug-3.1.9` and `pytest-9.2.0`. The service was configured with `PYTHON_VERSION=3.12.9`; the verified GitHub clean-install runner used Python `3.12.3`. Distinguish provider-configured version from clean-runner actual version; do not pretend the two are an identical environment. Build output also validated **5 canonical sources, 26 passages, 26 rule mappings and 5 templates** at source version `kb-2026-11-01.1`.

## Actual public HTTPS acceptance — PASS 10/10

From the independent **GitHub Actions** internet-connected runner (NOT local in-process Flask, NOT supplied mocked results), on **2026-11-04T06:41:12.209382Z**, `python -m backend.smoke_public --base-url https://sg-navi-api-free-demo.onrender.com` performed all of the following and passed:

| Remote request | Actual recorded output | Result |
| --- | --- | --- |
| GET `/api/version` with Pages Origin | API `1.0`, rule `mock-1`, source `kb-2026-11-01.1` | PASS |
| GET `/api/health` | HTTP **200**, `{"status":"ok"}` | PASS |
| GET `/api/case-types` | `rental_deposit`, `consumer_complaint` | PASS |
| OPTIONS `/api/navigate` for Rental | HTTP **204**, `Access-Control-Allow-Origin: https://chu-junjie.github.io`, allow-method POST and Content-Type | PASS |
| POST `/api/navigate` for complete Rental | HTTP **200**, `REFER_TO_OFFICIAL`, `SCT-ELIG-RESIDENTIAL` / `SCT-ELIG-AMOUNT`, `action_card: null` | PASS |
| OPTIONS `/api/navigate` for Consumer | HTTP **204**, same Pages CORS origin and method/header | PASS |
| POST `/api/navigate` for complete Consumer | HTTP **200**, `REFER_TO_OFFICIAL`, `CASE-PERSONAL` / `CASE-SG-SUPPLIER`, `action_card: null` | PASS |
| POST Rental with missing facts | `NEED_CLARIFICATION`, questions for dispute party, premises and claim amount, no asserted eligibility | PASS |
| POST invalid answer schema | HTTP **400**, `ERROR`, no Evidence or Action Card | PASS |
| OPTIONS from unapproved origin | HTTP **403**, no allow-origin | PASS |

**Original machine-readable JSON:** [task7-free-render-remote-smoke.json](test-results/task7-free-render-remote-smoke.json). The independently executed [GitHub Actions run #41787144159](https://github.com/Chu-Junjie/SG-Navi/actions/runs/41787144159) produced [the original 30-day Artifact (ID 13301946588)](https://github.com/Chu-Junjie/SG-Navi/actions/runs/41787144159/artifacts/13301946588). The earlier initial smoke run #41786884083 FAILED because the smoke test incorrectly compared HTTP header-name casing; fixed by a test-only commit `e22ce642f79c482461ddd32185f1e509d1dcd31d` and **retested against the same deployed SHA**; this result was not silently discarded.

**Not tested against the public service:** forced corrupt RAG sources, physical disk write/restart preservation, backup restoration, or GitHub Pages browser submission. Backend unit/integration tests cover synthetic injected RAG exceptions and invalid Evidence; they are not public destructive-fault tests.

## Independent clean-environment verification (not the member's own computer)

[Automated fresh-clone GitHub Actions run #41787143999](https://github.com/Chu-Junjie/SG-Navi/actions/runs/41787143999) really executed a **new remote `git clone --no-checkout`**, detached checkout of test SHA **`e22ce642f79c482461ddd32185f1e509d1dcd31d`**, a **new Python virtual environment**, a fresh requirements installation, contract and actual RAG checks, pytest, frontend unittest, and **real Gunicorn localhost HTTP** checks. Output: **400 pytest passed, 31 frontend unittest passed**, 11 shared examples valid. Captured Python version **3.12.3**; resolved packages include Flask 3.1.3 / Gunicorn 23.0.0 / Werkzeug 3.1.9 / jsonschema 4.26.0 / referencing 0.37.0 / pytest 9.2.0. No failures/skips were reported in that successful run. Actual test output and environment manifest were saved as workflow artifacts.

The separate current-turn container attempted `git ls-remote https://github.com/Chu-Junjie/SG-Navi.git`, but DNS resolution failed; an independent **user-operated** clone/venv/install/start/test on Zheng's own Windows computer remains **NOT RUN** here. Do not label an automated GitHub Actions run as the user's personal laptop execution.

## RAG state — blocker NOT PASSED

This free Render service has no persistent disk. It cannot guarantee preservation of `instance/rag_quarantine.json` across restart, shutdown or redeploy. **Do not claim requirement 4 passed.**

| Verification | Status | Truthful limitation |
| --- | --- | --- |
| Canonical five-file source validation at build | PASS | Existing reviewed repo snapshot, not persistent mutable state |
| Free demo validates any *existing* RAG quarantine state and fails closed on corruption | PASS (test and WSGI startup) | Safeguard prevents serving corrupt state; does not create durable storage |
| Actual cloud quarantine write → restart → inspect retained history | **NOT RUN — free platform does not provide durable disk** | Expected unsupported; no real quarantine write injected |
| Actual cloud state backup and restore | **NOT RUN** | No durable state volume or recovery target; no backup result claimed |
| Persistent production fallback configuration | CONFIGURATION PREPARED | Paid Render disk Blueprint remains separate; not deployed or charged |

The free API should be used only with synthetic data for transport/CORS and front-end integration experiments, not as a reliable reviewed-source quarantine system or production legal assistant. A future durable storage architecture or paid disk must be implemented and actually tested before Task 7 candidate freeze.

## Guanyu public frontend handoff

GitHub Pages remains `https://chu-junjie.github.io/SG-Navi/` and is **not** modified by this backend-owned PR.

- **Backend Base URL:** `https://sg-navi-api-free-demo.onrender.com`.
- **Allowlisted browser origin:** `https://chu-junjie.github.io`.
- Request health: `GET ${BASE_URL}/api/health`; version: `GET ${BASE_URL}/api/version`; navigation: `POST ${BASE_URL}/api/navigate`, `Content-Type: application/json`, body fields `api_version`, `case_type` and `answers` according to current canonical shared/front-end schemas.
- The browser will send a CORS OPTIONS preflight for JSON POST. Real remote tests verify 204 and allow-origin/method/header. Do not send credentials or attach API secrets.
- Frontend API Base URL/config belongs to Guanyu, in a separate frontend PR. Test a real GitHub Pages browser origin with full Rental and Consumer flow, incomplete facts, invalid requests, source links, edit/retry, and mobile width. **NOT RUN** until Guanyu's integration and browser acceptance.
- Current legal rules are **disabled**. Successful full facts return `REFER_TO_OFFICIAL` source metadata with `action_card: null`; seven displayed card headings are fallback/verification, not a verified legal recommendation or `SUPPORTED_PATH`.

## Next checks / release gate

1. Guanyu integrates Pages with the **actual HTTPS Base URL** and records real browser outcomes (separate frontend ownership).
2. Team owner selects durable state approach; actually test quarantining, restart, state preservation, backup and restoration. Free Render is **not sufficient** for this acceptance.
3. Zheng conducts personally operated fresh Windows clone/install/test and shares accurate command/exit-code evidence separately; the automated runner record above must remain labeled as automated.
4. Team reviews PR, reconciles exact deployed Git SHA vs new code/doc commits, and approves final candidate. Render autoDeploy is disabled, so a new branch commit does not silently update the live service.
5. **No `v0.9.0-rc1` tag**, candidate freeze or production claim before Junjie's final Task 7 approval.

**Links:** [Render Dashboard](https://dashboard.render.com/web/srv-dbld56on74is739q3oc0) · [real public health endpoint](https://sg-navi-api-free-demo.onrender.com/api/health) · [service deploy event](https://dashboard.render.com/web/srv-dbld56on74is739q3oc0) · [Task 7 Issue #7](https://github.com/Chu-Junjie/SG-Navi/issues/7).
