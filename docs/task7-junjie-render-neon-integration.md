# SG Navi — current free deployment, evidence and recovery gates

**Authoritative current-architecture reference, as observed on 2026-11-05.**
Current remediation and actual isolated hosted persistence/encrypted recovery
are recorded in [PR #64](https://github.com/Chu-Junjie/SG-Navi/pull/64),
[the recovery record](task7-state-recovery.md) and the updated root acceptance.
The old pending recovery list below is superseded by these actual results;
production state remains untouched. Zheng's user-reported personal run still
needs exact execution details before final freeze.
The application is publicly demonstrated, but Task 7 candidate freeze and legal
eligibility decisions remain **NOT APPROVED**. Older Render handovers document
historical experiments; do not use their URLs, expiring database or old branches
for the current deployment.

## Active resources

| Component | Actual reference | Observed state |
| --- | --- | --- |
| Source | https://github.com/Chu-Junjie/SG-Navi | Public `main`; remediation implementation 3994850f29a04356c3a708daee56815294278895 and final merge identity recorded in PR #64 |
| Site | https://chu-junjie.github.io/SG-Navi/ | Pages publish job passed on that SHA |
| Render backend | https://sg-navi-api-junjie.onrender.com | Service `srv-dbluspoae00c73fqp4v0`, Free, Singapore, auto-deploy on `main`; inspect the exact Live deploy, not a historical README SHA |
| Render dashboard | https://dashboard.render.com/web/srv-dbluspoae00c73fqp4v0 | Owned by Junjie's currently connected `My Workspace` |
| Neon | `my-first-project`, project `damp-scene-05807412` | Free v3 plan, Singapore (`aws-ap-southeast-1`), PostgreSQL 18, branch `production`, database `neondb` |
| Durable state tables | `sgnavi_quarantine_state`, `sgnavi_quarantine_metadata`, `sgnavi_quarantine_backups` | Created by Render app startup; 1 initial state row + 1 metadata row + 0 backup rows as observed 2026-11-05 |

The site is static; browsers call the separate HTTPS Flask API.
The app's read-only official evidence bundle contains five reviewed source
records, 26 passages, 26 rule mappings and five conditional templates.
The database stores quarantine/review state, **not** the checked-in knowledge
corpus or a history of user dispute submissions.

## Render runtime and secrets

The existing service was created via Render API, not by applying the root
Blueprint. The root `render.yaml` is a free-plan reproducibility reference.
**Do not create or sync an additional Blueprint without examining the intended
resources and costs.**

- Region `singapore`, service plan `free`, runtime `python`, branch `main`.
- Build `pip install -r requirements.txt && python -m rag.import_knowledge_base`.
- Start `gunicorn --bind 0.0.0.0:$PORT --workers 1 --threads 4 --timeout 30 backend.production:app`.
- `PYTHON_VERSION=3.12.9`.
- `SG_NAVI_CORS_ORIGINS=https://chu-junjie.github.io`.
- `SG_NAVI_FREE_DEMO=1`: public demo disclosure, no production/legal release claim.
- `SG_NAVI_REQUIRE_PERSISTENCE=1`: fail closed when state cannot be persisted.
- `SG_NAVI_STATE_DATABASE_URL`: **only a Render secret**; its value comes from
  Neon and must never appear in this repository, PRs, issues, CI logs or chats.
- The owner configured **Health Check Path `/api/health`** on the existing
  service; Render read-back confirmed it. The application now checks critical
  validated source/state readiness and returns 503/unavailable on failure.

The Neon connection was configured privately on 2026-11-05 and triggered
a Render deployment; Render reported it Live. The app created the above tables
on Neon. The connection URL supplied by Neon used a **pooled hostname**. Real
transaction/advisory-lock logic must continue to be regression-tested when
provider settings change. No credentials are exposed by this document.

A missing or unreachable database causes `backend.production` startup to fail
rather than switching to ephemeral files. **Do not disable this protection to
make the deployment look healthy.** Free plans have quotas, idle sleep and policy
changes; no hosting provider guarantees indefinite availability or backups.

## Automated quality gates

- `test.yml`: ordinary contract, backend, RAG, local WSGI and frontend tests.
  **Green does not mean optional PostgreSQL or remote browser tests ran.**
- `task7-postgres-durability.yml`: real disposable PostgreSQL 18 in GitHub
  Actions; verifies nonempty quarantine, separate Gunicorn process restarts,
  backup/restore and corrupt-history fail-closed. This is independent of Neon
  and never mutates its live data.
- `task7-junjie-render-neon-https.yml`: live API requests against the actual
  Render hostname on `main` push, weekly scheduled run or manual dispatch.
  Checks the database-backed mode header and the 10-check synthetic API smoke.
  Scheduled/manual tests also run real published Pages in Chromium for the
  Rental Deposit and Consumer Complaint flows and save screenshots.
  An external pass must be read from the **actual workflow run**, not inferred
  from its definition. The remote SHA is not proven by HTTP alone.
- `source-freshness-read-only.yml`: weekly fetch and fingerprint/excerpt checks
  of all five official URLs, with per-source JSON. Any failure must be triaged
  as changed content, network failure or endpoint issue. It never alters review
  records or promotes new source content automatically. GitHub can automatically
  disable scheduled workflows in public repos after 60 days of inactivity;
  check Actions settings and re-enable if necessary.

### Manual independent checks

```bash
python -m backend.smoke_public --base-url https://sg-navi-api-junjie.onrender.com
python -m rag.import_knowledge_base --verify-live
```

An actual public smoke run must check `GET /api/health`,
`GET /api/version`, `GET /api/case-types`, both synthetic
`POST /api/navigate` scenarios, missing/invalid facts and CORS preflights.
Expected demo header is `X-SG-Navi-Deployment-Mode:
postgres-backed-free-demo`. Do not treat a status code alone as acceptance.

## Recovery procedure and final acceptance

The isolated nonempty hosted state and off-provider encrypted archive drill
have now passed as described in [the current recovery procedure](task7-state-recovery.md).
The following controls still apply to future maintenance; they are not all
unexecuted tasks. Use the updated root acceptance for the current disposition.

1. Obtain independent successful **post-merge** public API workflow evidence
   from the deployed service, and a real published Pages browser run. Review
   actual evidence and reported caveats.
2. Verify **nonempty state** survives a real hosted restart without writing
   synthetic quarantine to the live `production` database. Use an **isolated
   Neon branch/role or disposable test database** and an approved operator
   procedure. CI on disposable Postgres proves app logic but not host wiring.
3. Test guarded backup/restore and fail-closed behavior in a disposable
   environment. Do not expose an administrative HTTP mutation endpoint,
   paste credentials, or reset/poison the production branch.
4. Arrange off-provider encrypted exports and a restoration drill in a safe
   location. The in-database `sgnavi_quarantine_backups` table is **not**
   sufficient protection against project deletion, lockout or provider outage.
5. Record independent team environment checks, source approval and release
   owner signoff in [Issue #7](https://github.com/Chu-Junjie/SG-Navi/issues/7).
   Do not tag `v0.9.0-rc1` or claim a production filing tool until accepted.

## Evidence-grounded feature boundary

All legal decision thresholds / eligibility checks remain intentionally
disabled. `rule_version: mock-1` and `REFER_TO_OFFICIAL` with
`action_card: null` mean visitors receive official research context, **not**
a legal route or eligibility determination. Enabling rules requires separate
official-source evidence, explicit source-to-check mapping, human review,
negative/boundary tests and team approval; it is **not** a deployment fix.

## Historical deployment files

- `render.yaml`: current Free + Neon **reference** Blueprint.
- `render.starter.yaml`: archived paid Starter/disk design, not authorized.
- `render.free.yaml` and `render-free.yaml`: older **nonpersistent**
  `sg-navi-api-free-demo` proposals in another workspace; do not apply.
- `docs/task7-postgres-durability-handover.md`: dated evidence about an old
  expiring Render Free PostgreSQL test instance. It is **not** the current Neon
  project and its 30-day expiry does not apply to the new Neon database.

No real user dispute data or credentials should be committed or submitted
as part of any public acceptance test.
