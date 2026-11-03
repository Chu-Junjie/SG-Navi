# Task 7 — SG Navi HTTPS backend deployment handover

**Implementation owner:** Zheng Zaikun · **Status:** deployment-ready proposal, **NOT publicly deployed** at this writing. No Render service has been provisioned, no paid plan authorized, no real HTTPS Base URL assigned, and no remote GET/POST/OPTIONS result is claimed. Task 7 freeze/tag is separate.

## Why a separate backend

The existing public [GitHub Pages site](https://chu-junjie.github.io/SG-Navi/) is static. Its own `/api/health` is not the Flask API. Keep that Pages site unchanged, and host the API at a separately deployed HTTPS service on **Render**. Render is a potential hosting provider, **not yet connected or authorized** in this ChatGPT workflow.

The reviewed `render.yaml` proposes a Python 3.12 service in Singapore, a **paid Starter compute plan and 1 GB persistent disk**. This is intentionally **not a free-service proposal**: Render's free disk is ephemeral, and losing `instance/rag_quarantine.json` would lose source quarantine/history. **Do not apply the paid Blueprint or enable billing without explicit approval by the repository/account owner**.

- Candidate Render service name: `sg-navi-api` (name availability is not reserved).
- **Public Base URL: NOT ASSIGNED**. After a successful real deploy, copy the actual HTTPS URL from Render; do not guess its `.onrender.com` subdomain.
- Render Blueprint: [`render.yaml`](../render.yaml), `autoDeployTrigger: off` to avoid unreviewed deployments.
- Web service runtime: Python 3.12.9, production **Gunicorn**, debug off.
- Build command: `pip install -r requirements.txt && python -m rag.import_knowledge_base`.
- Startup command: `gunicorn --bind 0.0.0.0:$PORT --workers 1 --threads 4 --timeout 30 backend.production:app`.
- Health probe: `/api/health`.
- Render persistent disk: `/opt/render/project/src/instance` (1 GB), holding the immutable-history operational state at `instance/rag_quarantine.json`.
- Env: `SG_NAVI_REQUIRE_PERSISTENCE=1`, `SG_NAVI_CORS_ORIGINS=https://chu-junjie.github.io`; do not use wildcard origins, cross-site cookies, or commit secrets. Render also exposes `RENDER=true`, which makes the WSGI app enforce persistent state even if someone omits the flag.
- One Gunicorn worker: the attached disk is owned by a single service instance; Render does not provide zero-downtime deploys with a persistent disk.

### Required files / build context

Render's service root is the **repository root**, not just `backend/`. The checked knowledge bundle is the exact five files under `rag/knowledge_base/` and the state is a separate disk file. Startup also imports `rag/repository.py`, `rag/retriever.py`, `rag/citations.py`, `shared/validate_contracts.py`, `shared/api_contract.json`, `backend/rules/*.json` and two input schemas under `frontend/schemas/`. **Do not configure a Render rootDir of `backend`**, or omit the rest of the repository from the build. The GitHub Pages frontend stays separate.

New dependencies in `requirements.txt` include production `gunicorn` and runtime `jsonschema`/`referencing`, which previously arrived only through the test requirements.

## 1. Deployment prerequisite and authorization

The account owner must connect/enable a Render account/workspace with permission to create a Web Service, configure a disk and deploy from GitHub. Before doing this, confirm the **ongoing cost** of Starter compute plus 1 GB disk and any usage charges in the Render dashboard. No permission should be assumed. The least information needed from the owner:

1. Confirm the Render account/workspace is connected and the owner has approved the displayed paid compute + disk charges.
2. Confirm the repository access/branch selected for Render and whether the final deployment commit/PR has been reviewed/merged.
3. After Render reports a successful deployment, provide the actual `https://...onrender.com` URL or make the connected service available for inspection.

Do **not** enter passwords or API keys into GitHub code or conversation. Use the Render account connection and environment settings. A repository URL alone does not grant cloud billing permissions.

### Render deployment sequence (only after approval)

1. Review and merge the feature PR to the approved target branch. Confirm `git rev-parse HEAD` is the reviewed commit; the service must deploy that **exact** commit, not a guessed branch-tip SHA.
2. In the Render dashboard, create a Blueprint from this repository's `render.yaml` **after the paid plan/disk is approved**. Confirm branch, Singapore region, plan, mount and storage size; no automatic deploy. Avoid accidentally creating a duplicate paid service.
3. Check build logs for successful installation and the offline five-file RAG import. Confirm Gunicorn started with the exact startup command, `DEBUG=False`, and persistent state check did not fail. The service **must not** start if the disk is missing/unwritable or the persisted quarantine state is corrupt.
4. Copy the actual public HTTPS Base URL, service ID, deploy ID/commit SHA, UTC execution time and Python/Gunicorn versions. Confirm `/api/health` responds in the Render dashboard and externally.
5. Execute the **actual remote probe** and record *raw status, response schema and CORS headers*; see next section.
6. Share the Base URL and this handover with Guanyu. Frontend changes remain owned by Guanyu; no attempt to alter GitHub Pages in this PR.
7. Record any feature limitations, release/rollback state and remaining issues in Issue #7. **Do not tag `v0.9.0-rc1` until the coordinator's final freeze acceptance.**

## 2. Public HTTPS validation — not yet run

With the real deployed URL and the local source checkout matching the selected commit:

```powershell
python -m backend.public_probe --base-url https://ACTUAL-RENDER-DOMAIN.onrender.com
```

The script refuses non-HTTPS/non-origin inputs. It performs **actual external** GET `/api/health`, `/api/case-types`, `/api/version`, CORS OPTIONS preflight for GET and POST, both complete Rental and Consumer synthetic POST `/api/navigate` requests, both missing-information cases, a forbidden synthetic supported-path override, and a negative-origin preflight. It validates the shared response schemas and checks deployed `source_version` against the local checked knowledge bundle. Output is structured JSON with PASS/FAIL for each check.

**Public verification results at documentation time:** `NOT RUN` — no deployed URL/account authorization exists here. Do not convert CI's local tests into public results. Public backend/RAG outages and quarantine/invalid-source injections are covered **in isolated backend tests**, not by breaking a live service. If an actual public outage or source inconsistency occurs, record the true result separately without exposing private content.

Once deployed, record:

| Field | Verified value |
| --- | --- |
| Render service / public HTTPS Base URL | NOT ASSIGNED |
| Render plan/disk and cost authorization | NOT CONFIRMED |
| Actual deployed Git commit and deploy ID | NOT DEPLOYED |
| `GET /api/health` / `/api/version` | NOT RUN |
| Rental and Consumer HTTPS POST | NOT RUN |
| `OPTIONS` preflight / returned CORS headers | NOT RUN |
| Missing/invalid/failed Evidence checks | Local CI only, remote NOT RUN |
| Actual availability after restart with preserved quarantine | NOT RUN |
| Actual rollback and recovery drill | NOT RUN |

### API contract / status limits

`GET /api/health` returns `{"status":"ok"}` when the Flask process is alive. `GET /api/version` returns `api_version=1.0`, `rule_version=mock-1`, and a checked `source_version` currently `kb-2026-11-01.1` (must be confirmed on the deployed commit). Both normal case flows are conservative `REFER_TO_OFFICIAL` with reviewed Evidence links and **`action_card: null`**. Unknown facts prompt `NEED_CLARIFICATION`. None of these are legal eligibility results; supported legal Action Cards are not enabled.

## 3. Give Guanyu these integration parameters

**This handoff is actionable only after the Base URL is real and confirmed.**

| Parameter | Value |
| --- | --- |
| Frontend site | `https://chu-junjie.github.io/SG-Navi/` (unchanged) |
| API_BASE_URL | **Pending real Render URL**, e.g. `https://<real-service>.onrender.com` is illustrative only |
| API endpoints | `/api/health`, `/api/version`, `/api/case-types`, `/api/navigate` |
| POST Content-Type | `application/json` |
| POST body | Exactly `{"api_version":"1.0","case_type":"rental_deposit"|"consumer_complaint","answers":{...}}` |
| Accepted Origin | Exactly `https://chu-junjie.github.io` (the **origin**, not `/SG-Navi/` path) |
| CORS | GET/POST allowed per endpoint, OPTIONS preflight with `Content-Type`; no wildcard/cookies |
| API response | Existing `shared/api_contract.json`, no field additions |
| Evidence UI | Show `REFER_TO_OFFICIAL` as source context only; no legal Action Card |

Guanyu must arrange a new frontend PR to use the real Base URL and verify the full Pages → HTTPS API → RAG two-case flow **in a browser**. The backend owner must not change the frontend module unilaterally.

## 4. State persistence, restart and recovery

The default `rag.repository.DEFAULT_STATE` resolves to `instance/rag_quarantine.json` relative to the repository root. Mounting `/opt/render/project/src/instance` retains it across restarts/deploys. The production WSGI module checks the mount is genuinely present, writable, and validates the checked corpus/quarantine history before serving HTTP. **The check does not itself constitute a real restart test.**

- Before deployment/rollback, preserve and independently back up any quarantine file. Never reset/delete it to make a page or test pass. Do not commit the file or its operational events.
- Render provides paid-disk snapshots; check the service/disk settings and available recovery points before restoring. Snapshots are not a guarantee of zero data loss since the last snapshot.
- On unavailable/corrupt state or invalid corpus, **leave the service unavailable** until the RAG owner reconciles source files, blocked-source history and `source_version`; do not silently continue with an empty blocklist.
- The attached disk does not provide zero-downtime deployments; expect a short service interruption. Restrict one instance; avoid separate writer processes.
- Keep source review and update procedures with Junjie: [RAG quarantine](../rag/TASK4.md), [RAG integrity](../rag/TASK6.md), and [release recovery](task7-release-handover.md).
- For code rollback, select an already-reviewed earlier deployed commit using Render's deploy history, verify it is compatible with the **current quarantine history and corpus**, redeploy on the same persistent disk and rerun public probes. If incompatible, keep the service down; never roll back the state history invisibly.

## 5. Actual testing versus deployment state

This PR adds `tests/backend/test_task7_public_deploy.py` for direct production-WSGI requests including real local checked RAG retrieval, CORS preflights/forbidden origins, bad CORS configurations, and synthetic corrupt/missing disk conditions. `tests/backend/run_task7_wsgi_smoke.py` launches a **real local Gunicorn subprocess** on GitHub Ubuntu, verifies health/version/OPTIONS and both actual loopback POST routes, then shuts down cleanly.

These results, when the exact-head CI succeeds, are local/CI results and **not a public HTTPS test**. The final Task 7 report must cite both the exact CI SHA and a separate real deployed Render SHA/URL/probe log. If the latter cannot be obtained, report deployment as **BLOCKED**, not as completed.

## 6. Known limitations

- Render connection and paid compute/disk authorization remain required; no live deployment has been attempted.
- GitHub Pages and the newly hosted API have separate origins; browser CORS works only after Guanyu uses the actual HTTPS URL.
- CORS is a browser isolation mechanism, **not authentication**; the public referral endpoint should be considered accessible to other HTTP clients. Do not submit real sensitive case information to this limited prototype. Rate limiting, abuse monitoring and operational production-hardening are not claimed.
- Existing legal eligibility checks remain disabled; backend source context is not a legal determination.
- Do not create the rc1 tag before the final coordinator acceptance and member installation checks.
