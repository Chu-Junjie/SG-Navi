# Task 7 — PostgreSQL quarantine durability verification and hosted handover

**Author:** ZhengZaikun (Backend + recovery), review required from Chu-Junjie (RAG source owner).  
**Date:** 2026-11-04 UTC.  
**Status:** **LOCAL / CI REAL POSTGRES PASS; RENDER HOSTED STATE NOT YET CONFIGURED; TASK 7 NOT READY FOR FREEZE.**

## What is implemented

The current SG Navi five-file knowledge corpus remains in `rag/knowledge_base/`. No legal eligibility checks have been enabled; API responses remain conservative `REFER_TO_OFFICIAL` with `action_card: null`.

- `rag/postgres_state.py`: PostgreSQL transaction-based current quarantine state, append-only backup rows, advisory locking, validated explicitly confirmed recovery, fail-closed read/write failures, initialization marker.
- `rag/repository.py`: existing source-review/event invariants and original local-file behavior preserved for unconfigured tests. When `SG_NAVI_STATE_DATABASE_URL` is set, only the default operational state is sourced from PostgreSQL. No silent file fallback on database failure.
- `backend/production.py`: production WSGI validates database connection, table initialization and existing quarantine history at startup; when free-demo plus database is active, response header discloses `postgres-backed-free-demo`. With `SG_NAVI_REQUIRE_PERSISTENCE=1` and no Postgres URL, a Render Free service refuses to start; paid-disk guard otherwise preserved.
- `requirements.txt`: adds `psycopg[binary]>=3.2,<4` to existing Flask/Gunicorn/validation packages.
- No remote management endpoint or automatic source release has been exposed; backup and restore are operator-only CLI methods.

### Verified disposable PostgreSQL / actual restart / backup / recovery

**GitHub Actions:** [#41806421131](https://github.com/Chu-Junjie/SG-Navi/actions/runs/41806421131), disposable `postgres:18`, Python 3.12.15, separate venv, real psycopg connection; **2 passed in 3.51 s, 0 failed** on `921382d935a8743953da72c84564483f29144718`.

Tests used a **throwaway isolated CI database**, not the user's hosted Render database:

1. Initialize PostgreSQL tables and state marker without resetting existing quarantines.
2. Save initial backup and quarantine one verified source using a synthetic test actor/reason.
3. Read back exact event/block record from a **separate Python process**.
4. Run **two distinct real Gunicorn processes**, stopping the first before starting the second; verify both connect to the same Postgres-backed RAG state.
5. Backup blocked state, restore the empty baseline with explicit confirmation and verify empty; restore the prior quarantine backup and verify exact original event/block state again.
6. Inject deliberately malformed source ID/history into the *disposable* database and verify `EvidenceRepository.snapshot()` fails closed rather than serving invalid evidence.

Actual CI machine output includes `PG_DURABILITY_PASS` showing `source_version=kb-2026-11-01.1`, `event_count=1`, two Gunicorn startups and backup IDs, plus the full JUnit/installed dependency files in workflow artifacts. It is **not** evidence of a Render host restart or an offsite backup.

**Main project suite:** [#41806421111](https://github.com/Chu-Junjie/SG-Navi/actions/runs/41806421111) on the same commit: **400 pytest passed, 2 database tests skipped** in the standard workflow (because disposable PG is intentionally not present); frontend unittest **35 tests, 1 opt-in public Pages test skipped**. The separate PostgreSQL workflow did execute both skipped database tests and passed. Test results may change with later commits; rerun on latest reviewed SHA.

## Actual free cloud DB and its limitations

The Render-connected workspace `My Workspace` has **one newly created free PostgreSQL** service:

| Property | Actual provider observation |
| --- | --- |
| Name | `sg-navi-quarantine-free-test` |
| ID | `dpg-dblfbutg1s2s73eitspg-a` |
| Region / version / plan | Singapore / PostgreSQL 18 / **Free** |
| Status at 2026-11-04T09:08 UTC | `available` |
| **Expiration** | **2026-12-04T09:08:11.669630Z** |
| Public connection | External IP allowlist empty; private credentials not shared |
| Paid resources created | **None**; no plan upgrade authorized |

**The free database is temporary and not a disaster-recovery solution.** An in-database backup is lost if the database expires or is deleted; it is **not** an off-service backup. Backup export/restore from an independent secure location is required for true disaster recovery, and remains **NOT RUN**.

## Required user configuration to test the real Render-hosted service

**No DB credentials should be sent to ChatGPT, GitHub, logs, or Issue #7.** The connected Render API does not expose the private database URL through the available commands; do not relax the empty external-IP allowlist.

After reviewing and merging the PostgreSQL PR into `main`:

1. Open [Render Database](https://dashboard.render.com/d/dpg-dblfbutg1s2s73eitspg-a) (`sg-navi-quarantine-free-test`). Find **Connections → Internal Database URL** (the exact label can vary). Copy the URL privately.
2. Open [Render SG Navi Web Service](https://dashboard.render.com/web/srv-dbld56on74is739q3oc0) → **Environment**. Add secret env key `SG_NAVI_STATE_DATABASE_URL` with the exact **Internal Database URL** value; change `SG_NAVI_REQUIRE_PERSISTENCE` to `1` while keeping `SG_NAVI_FREE_DEMO=1` and `SG_NAVI_CORS_ORIGINS=https://chu-junjie.github.io`. Do **not** share the URL in chat. Render must keep this variable private.
3. In **Settings / Build & Deploy**, change Git branch from `feat/task7-free-render-demo` to the **reviewed and merged `main`** (or a separately approved exact SHA), keep Auto Deploy **off**, then manually deploy. If the UI shows a different repository/commit, stop and reconcile.
4. Verify Render's actual deployed SHA, plan **Free**, startup command `gunicorn --bind 0.0.0.0:$PORT --workers 1 --threads 4 --timeout 30 backend.production:app`, status **Live**, and **no new charges**. The target should expose `X-SG-Navi-Deployment-Mode: postgres-backed-free-demo` on API calls. If the database URL is invalid or the database is unavailable, startup should **fail closed**, not silently fall back to ephemeral state.
5. From an independent client run `python -m backend.smoke_public --base-url https://sg-navi-api-free-demo.onrender.com`; record actual GET Health/Version, Rental/Consumer synthetic POST, permitted/denied Pages-origin CORS OPTIONS, missing facts, invalid-input behavior, exact source version and timestamps. A prior public 10/10 run on an older deployed SHA exists and must **not** be relabeled as a test of the new database-backed deployment.
6. Verify actual hosted quarantine write/restart/read and backup/restore with a **trusted operator, protected administrative execution environment and RAG owner's permission**. Do not add public endpoints for source-state management or intentionally contaminate the live public database without written test approval. Record actual backup IDs, source review/version, last healthy state, before/after restart deploy IDs and checked counts. This cloud-level check remains **NOT RUN** until the service is configured and a controlled execution method is available.

### Operator CLI for backup and recovery (only in authorized environment with private DSN set)

```powershell
# Must run in a protected shell with SG_NAVI_STATE_DATABASE_URL already configured.
python -m rag.repository state
python -m rag.repository backup --backup-label before_reviewed_change
# Copy the actual backup ID to the approved change record. Operator-only:
python -m rag.repository restore --backup-id 1 --confirm-restore
python -m rag.repository state
```

The literal ID `1` above is **illustrative**, not a verified hosted backup ID. Never restore an arbitrary old backup unless the RAG owner has validated its compatibility with the five current source files. Restoring adds a pre-restore backup row in the same database transaction; it does not export an independent offsite copy. A protected database export is still required to survive database expiration, account loss or deletion.

## Personal independent installation — NOT RUN on Zheng's own Windows PC

A fresh GitHub Actions clone / isolated venv is *different from* the **user's personal environment**, and cannot truthfully substitute for it.

To finish member F1, Zheng must execute a new clone on their Windows PC, report exact `git rev-parse HEAD`, Python/Node versions and paths, install exit status, dependency snapshot, actual full test pass/fail/skip, API local start/health/version, timestamp, and the two case outputs. The exact command block is in [Zheng personal check template](task7-zheng-personal-check.md). Current status: **PERSONAL WINDOWS NOT RUN**, no invented student-attested logs.

## Coordination and release gate

- Existing real public API (before this persistence PR): https://sg-navi-api-free-demo.onrender.com, Render **Free**; actual old live SHA must be fetched from Render before upgrading. Guanyu's Pages→Render 18/18 Chromium evidence is separately proven by PR #56, but it used the older ephemeral backend.
- Guanyu's member record was merged via PR #57: 430 passed, 4 skipped on the recorded Windows SHA. That is his user-reported evidence, not ours.
- Junjie must review changes under `rag/`, reconcile new database state and deployed code SHA, direct/accept actual hosted persistence and backup/restore results, and update `integration_acceptance.md`.
- **No `v0.9.0-rc1` tag/release before Junjie's final signed-off acceptance.**
- Existing API version `1.0`, rule `mock-1` and checked source `kb-2026-11-01.1` remain; legal eligibility remains **disabled** and real supported Action Card remains **unavailable**.
