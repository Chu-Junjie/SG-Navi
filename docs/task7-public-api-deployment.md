# SG Navi Task 7 — public Python API deployment handover

Status: **PROVIDER DEPLOYMENT PENDING USER CONNECTION AND PAID-RESOURCE APPROVAL.** This is code/config/CI preparation, **not** evidence of a publicly reachable Flask service. No Render service, public API hostname, persistent-disk restart, paid subscription, release tag or frontend production integration was created by this change.

## Exact deploy source and configuration

- Repository: https://github.com/Chu-Junjie/SG-Navi
- PR branch: `feat/task7-public-flask-backend`, based on audited main `b1aa596816027f9a3a37468dcd10665be954eed1` before this PR. **Pin deployed SHA to the exact reviewed merged commit when provisioned; the PR branch SHA is not evidence of a deployed release.**
- Provider proposal: Render Web Service, Singapore region, **paid Starter instance plus 1GB persistent disk**. These resources have potential recurring charges; request explicit account connection, project authorization and cost approval before applying `render.yaml`.
- `render.yaml` uses a single service with `main` branch and auto-deploy disabled. **Deploy only after PR merge/owner authorization** so its `main` build contains the reviewed changes.
- Build command: `pip install -r requirements.txt && python -m rag.import_knowledge_base`.
- Startup command: `gunicorn --bind 0.0.0.0:$PORT --workers 1 --threads 4 --timeout 30 backend.production:app`. Uses production WSGI, `debug=False`; binding `0.0.0.0` is **internal to Render's reverse proxy**, not direct public Flask debug service.
- Runtime: Python 3.12.9 set in the Blueprint; `requirements.txt` installs Flask, Gunicorn, jsonschema and referencing (pytest is currently included for existing repo tests). Exact resolved deploy packages must be captured from the actual service rather than inferred from version ranges.
- CORS: `SG_NAVI_CORS_ORIGINS=https://chu-junjie.github.io` (origin only, **not** `/SG-Navi/`). GET, POST and OPTIONS/Content-Type are handled on the four existing API paths; no credentials/cookies and no wildcard allow-origin.
- Deploy files: build the **whole repository**, not only `backend/`. Runtime reads `shared/`, `rag/knowledge_base/` five checked files, `frontend/schemas/`, `backend/rules/`, plus standard Python modules. The Pages frontend is **not** replaced.
- Source/rule contract at current reviewed corpus: `api_version: 1.0`, `rule_version: mock-1`, `source_version: kb-2026-11-01.1`; verify the actual `/api/version` after deploy. **No legal rule activation or real supported legal Action Card.**

## Persisted RAG quarantine/history — critical safety control

The default RAG state is `/opt/render/project/src/instance/rag_quarantine.json`, because `rag.repository.DEFAULT_STATE` points at the root `instance/` directory.

The Blueprint mounts a paid persistent disk at **`/opt/render/project/src/instance`** and sets `SG_NAVI_REQUIRE_PERSISTENCE=1`; `backend.production` refuses to start unless the directory is an actual mounted, writable disk and any existing quarantine/history file passes the repository validator. The one-Gunicorn-worker configuration avoids multi-process mutation races. Keep `render.yaml` disk path and repository default path aligned; if Render changes its project-root layout, correct both through a reviewed PR **before** starting the service. A disk attached at any other path does not protect state.

Never clear the quarantine file to fix a 503 or force a source back into use. Do not append or invent source reviews. Ensure the hosting plan retains the disk across restarts and rollbacks; verify with an **actual restart test** after deployment. Existing local `instance/` is Git-ignored; it is not part of the build or the canonical five-file corpus.

**Backups:** because the disk is a single operational-state copy, save periodic restricted off-service copies of `rag_quarantine.json` through the host's approved mechanism, preserving content and event order. Never include the file, any case answers, or credentials in public artifacts. This handover does not claim a Render volume snapshot or remote backup was already performed. For recovery: pause submissions, inspect Render logs and `python -m rag.repository state`, preserve a copy, validate five canonical files and exact source version, then restore an intact backed-up state on the persistent disk only with the RAG owner's approval. Source release requires a fresh genuine page review as documented in `rag/TASK4.md`; do not wipe history.

**Rollback:** pin an earlier reviewed application Git SHA / Render deploy, leave the persistent disk mounted and unchanged, verify source-version/state compatibility, re-run safe real HTTP health/version/RAG smoke checks, and only then resume traffic. Rollback must not silently downgrade source-review trust. If incompatible, keep service unavailable rather than dropping block history. A hosted rollback/restart drill is NOT RUN until actual service provisioning.

## Verification — execute after Render supplies actual HTTPS URL

Record the real service hostname, its deployed Git commit from Render, UTC execution time and raw response/CI logs. Do not use GitHub Pages `/api/*` paths as though it hosted Flask.

```powershell
$base = "https://ACTUAL-SERVICE.onrender.com"
Invoke-WebRequest "$base/api/health" -Headers @{ Origin="https://chu-junjie.github.io" }
Invoke-RestMethod "$base/api/version" -Headers @{ Origin="https://chu-junjie.github.io" }
.\.venv\Scripts\python.exe -m backend.smoke_public --base-url $base
```

The HTTPS smoke script actually sends:
- GET `/api/health`, `/api/version`, `/api/case-types` and checks CORS + canonical schema.
- OPTIONS `/api/navigate` from the Pages origin for both case scenarios; checks `204`, allowed methods and Content-Type.
- POST Rental and Consumer synthetic complete facts; requires source-context `REFER_TO_OFFICIAL`, real versioned verified Evidence and null Action Card.
- POST missing facts and malformed answers, and unauthorised-origin OPTIONS; rejects an unsafe response.
- Produces timestamped JSON and nonzero exit code on actual failures. **Never write an expected pass result in advance.**

Actual absence/invalid-citation/RAG exception behavior is covered with synthetic injected failures in existing backend pytest suites; **do not attempt to corrupt real RAG state on the public service** just to demonstrate an ERROR. Real cloud recovery and persistence are separate required acceptance checks. The smoke script also does not prove a browser actually called the service.

## Guanyu — GitHub Pages frontend handoff (no frontend modification in this PR)

- Static frontend remains at `https://chu-junjie.github.io/SG-Navi/`.
- **Backend Base URL: PENDING actual Render hostname**. Do not hardcode a guessed URL or a Pages `/api` path.
- API request: `POST {BASE_URL}/api/navigate`, `Content-Type: application/json`; JSON object exactly `{"api_version":"1.0","case_type":"rental_deposit" | "consumer_complaint","answers":{...}}` using the existing shared schema.
- Health: `GET {BASE_URL}/api/health`, version `GET {BASE_URL}/api/version`, case types `GET {BASE_URL}/api/case-types`.
- Frontend must use a **Guanyu-owned configurable public API base** rather than same-origin mock/Pages paths; Guanyu should own a separate PR and browser E2E against the real public endpoint.
- No `credentials: include`, cookies or API keys are required for this public referral prototype. Treat `REFER_TO_OFFICIAL` as non-eligibility source context; display verified references and preserve seven fallback card headings without inventing `SUPPORTED_PATH`.
- Check real GitHub Pages → HTTPS Render flows for both cases, clarification, edit, source URLs, safe failure/timeout and 390px mobile, after Guanyu's frontend PR. This **is not verified** by backend-only CORS tests.

## Outstanding steps before honest public-delivery signoff

| Gate | Owner | Current evidence |
| --- | --- | --- |
| Render account connected and paid Starter/disk authorized | User/repo owner | **PENDING**; no paid resources created |
| Reviewed deployment PR merged into main | Team | **PENDING**; branch is not the service |
| Provider deploy from pinned commit and HTTPS hostname supplied | Deployment owner | **NOT RUN** |
| Real remote GET/POST/OPTIONS checks & version reconciliation | Zheng | **NOT RUN**; run smoke script once URL exists |
| Persistent state across actual redeploy/restart and state backup/rollback safety | Zheng + Chu | **NOT RUN** |
| Guanyu frontend switched to real Base URL and verified in real browser | Guanyu | **NOT RUN** |
| Final coordinator acceptance / `v0.9.0-rc1` tag | Chu then release owner | **NOT AUTHORIZED** |

This is the restricted public-API preparation stage, **not** a release or legal decision system. Production users should not enter real personal dispute data until privacy/data-protection and security reviews are completed.
