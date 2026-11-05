# SG Navi — Junjie Render Free + Neon PostgreSQL integration

Status (2026-11-05): **Render new service LIVE; Neon DATABASE NOT YET ATTACHED; public end-to-end and persistence checks PENDING.** This is a controlled demo, not a legal-advice service or an accepted Task 7 release.

## Repository and deployment ownership

- Source: https://github.com/Chu-Junjie/SG-Navi (branch `main`).
- New Render service: `sg-navi-api-junjie` (Free, Singapore), service `srv-dbluspoae00c73fqp4v0`.
- Dashboard: https://dashboard.render.com/web/srv-dbluspoae00c73fqp4v0
- API origin: https://sg-navi-api-junjie.onrender.com
- First deployed SHA: `98f72a6685e494061c84e10ef71226ed9758a743`.
- Render auto-deploy on `main` is on. A draft PR alone does not deploy.
- Browser frontend: https://chu-junjie.github.io/SG-Navi/ (GitHub Pages).
- Do not confuse the new service with the historical `sg-navi-api-free-demo` in another Render workspace. No migration from that account is assumed or authorised.

## Actual app runtime

The service was created with:
- Python runtime, region Singapore, plan `free`, full repo root as build context.
- Build: `pip install -r requirements.txt && python -m rag.import_knowledge_base`
- Start: `gunicorn --bind 0.0.0.0:$PORT --workers 1 --threads 4 --timeout 30 backend.production:app`
- `PYTHON_VERSION=3.12.9`
- `SG_NAVI_CORS_ORIGINS=https://chu-junjie.github.io` (origin, no path).
- `SG_NAVI_FREE_DEMO=1`, `SG_NAVI_REQUIRE_PERSISTENCE=0` initially.

Render reported a Live deploy; build logs reported the checked knowledge corpus: five sources, 26 passages, 26 mappings, five templates. This does **not** prove new public browser flows, durable storage, or recovery. The Free instance can sleep and has usage limits. No fixed Web Service expiry does not mean a guarantee of permanent availability.

## Neon database (must be configured privately)

Neon is a managed **PostgreSQL database**. The GitHub repository is the source code, **not** the database; no database password or connection URL belongs in GitHub, commits, CI logs, Issues, PRs, or chat.

1. In https://console.neon.tech/ create a Free PostgreSQL project, e.g. `sg-navi`. Select Singapore if offered; record the actual region. A GitHub integration is optional for tooling and does not replace a PostgreSQL connection.
2. In Neon Console select the project and **Connect**. Obtain the project's **direct** PostgreSQL connection string (disable connection pooling for this initial low-concurrency deployment to simplify connection and advisory-lock testing). Keep its supplied TLS parameters, including `sslmode=require`.
3. In the **new Render** dashboard, open **Environment**. Add secret `SG_NAVI_STATE_DATABASE_URL` with the actual Neon PostgreSQL URL. Update `SG_NAVI_REQUIRE_PERSISTENCE=1`. Keep `SG_NAVI_FREE_DEMO=1` until the demo is independently accepted, along with `SG_NAVI_CORS_ORIGINS=https://chu-junjie.github.io`.
4. Apply changes together; Render will redeploy. `backend.production` connects to Postgres and `PostgresStateStore.prepare()` creates/validates the quarantine tables at startup. On missing/invalid connection it fails closed; **do not** switch persistence off just to make the service green.
5. Verify the actual deploy SHA, Live status, that the HTTP response header `X-SG-Navi-Deployment-Mode` reports `postgres-backed-free-demo`, and run the external API smoke script `python -m backend.smoke_public --base-url https://sg-navi-api-junjie.onrender.com` using synthetic inputs only.
6. With authorisation and an operator-controlled process, check persisted quarantine history across a **real** hosted restart, then validated backup/recovery. Do not make a public state-mutation endpoint or claim disaster recovery from an in-database-only backup.

Neon Free does not have a fixed trial end date as of the preparation date, but provider policy, quota and inactivity rules may change. Backup/export off-provider is needed for long-term protection; this document does not claim one exists.

## Frontend integration PR and acceptance

This candidate PR changes only the deployment-owned public API origin in `frontend/js/api-config.js`; it does not add credentials or legal rules. Frontend owner `Guanyu-Lu` must review before merge. After merge, verify actual **GitHub Pages** browser flows for rental deposits and consumer complaints, missing facts, retry and invalid input, links, CORS, and mobile width. Until these tests pass, keep Task 7 final release/RC1 claims blocked.

Remote diagnostics:
- `GET https://sg-navi-api-junjie.onrender.com/api/health`
- `GET https://sg-navi-api-junjie.onrender.com/api/version`
- `GET https://sg-navi-api-junjie.onrender.com/api/case-types`
- `OPTIONS/POST https://sg-navi-api-junjie.onrender.com/api/navigate` with the allowlisted GitHub Pages origin.

**Open gates:** Neon account connection and database URL setup; new hosted persistence test; source-currentness and UI end-to-end test; frontend owner review; final coordinator acceptance.