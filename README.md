# SG Navi — developer setup and candidate handover

**Group 6 · English Rental Deposit / Consumer Complaint prototype**

SG Navi has a real Flask → RAG → browser integration. It asks for missing facts and provides **verified source context**, but it **does not determine legal eligibility**: all runtime legal rules remain disabled, and the normal result is `REFER_TO_OFFICIAL` with `action_card: null`. The seven visible card sections are fallback / verification messages, **not a supported legal Action Card**. Do not present the app as legal advice or a production filing service.

- **Task 5:** accepted; [evidence](docs/task5-checklist.md).
- **Task 6:** accepted **with limits**; [evidence](docs/task6-checklist.md) (38 IDs: 36 PASS, E2E-01/02 LIMITED).
- **Task 7:** handover in progress; [coordinator assessment](integration_acceptance.md) currently says **NOT READY FOR FREEZE**. The candidate-specific [Rental and Consumer browser demo](frontend/TASK7_CANDIDATE_DEMO.md) and screenshots are recorded; team member-specific fresh install records and final release-owner handover/approval still need reconciliation.
- **Release/recovery procedures:** [Task 7 release handover](docs/task7-release-handover.md). Do not create `v0.9.0-rc1` or call it released before final coordinator approval.
- **Current public demo (2026-11-05):** [GitHub Pages](https://chu-junjie.github.io/SG-Navi/) → [Junjie's Render Free API](https://sg-navi-api-junjie.onrender.com) → Neon Free PostgreSQL (`my-first-project`, PG18/Singapore). The service was observed **Live** on the reviewed `main` commit `71ad87d`; the Neon state/metadata/backup tables were initialized. This is a conservative referral prototype, **not a production/legal-decision release**. See the [live setup and acceptance register](docs/task7-junjie-render-neon-integration.md), not the [older paid-disk proposal](docs/task7-public-backend.md).

Repository: https://github.com/Chu-Junjie/SG-Navi

## Current free deployment and operational checks

| Component | Actual setup | Caveat |
| --- | --- | --- |
| GitHub Pages | https://chu-junjie.github.io/SG-Navi/ | Static frontend; `frontend/js/api-config.js` routes Pages to the separate API |
| Render | https://sg-navi-api-junjie.onrender.com, Singapore, plan Free, branch `main`, auto-deploy on | Sleeps and has usage quotas; Live status is not a complete UI acceptance |
| Neon | Free PostgreSQL 18, Singapore, project `my-first-project` | Private database URL is set only as the Render secret `SG_NAVI_STATE_DATABASE_URL` |
| Status persistence | `SG_NAVI_REQUIRE_PERSISTENCE=1`, `SG_NAVI_FREE_DEMO=1` | Quarantine-state initialization verified; nonempty hosted restart/recovery and offsite backup still pending |

**Do not create a new paid resource or sync another Blueprint while checking the existing service.** The root [`render.yaml`](render.yaml) now describes the Free + Neon architecture for reference; it is **not** automatically controlling the existing API-created Render service. The old paid disk configuration is archived at [`render.starter.yaml`](render.starter.yaml) and requires separate cost approval. Older `render.free.yaml` and `render-free.yaml` are historical nonpersistent demos, not current deployment recipes.

- Latest local/CI suite: [`.github/workflows/test.yml`](.github/workflows/test.yml) (ordinary suite can skip optional external browser and PostgreSQL tests).
- Live public API and published browser acceptance: [`.github/workflows/task7-junjie-render-neon-https.yml`](.github/workflows/task7-junjie-render-neon-https.yml). On `main` push checks the actual remote API; scheduled/manual runs include the published Pages browser. The public test is not equivalent to a verified source SHA on the remote host.
- Real PostgreSQL transaction/restart/recovery tests on **disposable CI PostgreSQL**, never the user's production Neon: [`.github/workflows/task7-postgres-durability.yml`](.github/workflows/task7-postgres-durability.yml).
- Weekly read-only official source freshness: [`.github/workflows/source-freshness-read-only.yml`](.github/workflows/source-freshness-read-only.yml). Failed checks need owner review; CI never silently accepts new text or edits the five reviewed files.

Do not enable currently disabled legal thresholds/rules without precise official evidence, human review and dedicated boundary tests. For now `rule_version: mock-1`, status `REFER_TO_OFFICIAL`, and `action_card: null` are intentional. Follow [Task 7 issue](https://github.com/Chu-Junjie/SG-Navi/issues/7) for unresolved member evidence, hosted recovery and final candidate signoff.

## Ownership

| Developer | Module |
| --- | --- |
| Chu Junjie (`Chu-Junjie`) | RAG, sources, shared contract, integration technical acceptance |
| Zheng Zaikun (`ZhengZaikun`) | Flask backend, backend/E2E tests, dependencies, CI, release documentation |
| Lu Guanyu (`Guanyu-Lu`) | Frontend, frontend tests, candidate demonstrations |

Respect [AGENTS.md](AGENTS.md): use feature branch → PR → peer review → merge; do not change another owner's module without coordination. Never commit secrets, `.env`, real disputes or user data.

## Prerequisites

- Git and **Python 3.12+**.
- For actual FE browser test execution: **Node.js 22+ and Chromium / Edge / Chrome**. Without them, some browser tests may skip; a green subset is **not** an FE acceptance claim.
- No API key, live production credentials, database server, `.env`, or npm dependency installation is required for the audited **local development** workflow.
- The project uses `requirements.txt` and `tests/contracts/requirements.txt`; the latter includes the former. Version ranges are not an exact lockfile. An executed resolved-package snapshot is in [Task 7 coordinator's records](docs/test-results/task7-resolved-environment.json).

## Fresh clone → isolated install (Windows PowerShell)

Use a new folder for independent Task 7 environment evidence. Do not reuse an old virtual environment:

```powershell
git clone https://github.com/Chu-Junjie/SG-Navi.git
cd SG-Navi
git rev-parse HEAD
py -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r tests/contracts/requirements.txt
```

To reproduce an **exact** reviewed commit, use `git checkout --detach <approved-sha>` before creating the environment. The coordinator's original clean-install audit used `d629033b27f9eb5a9d0998b7d55304ae86ffe528`. The later frontend navigation/demo fixes merged in `ba8c992f03d426108fdb1e1aac375e9320b92244`; **neither SHA is an approved rc1 release target**. A final commit must be selected after all Task 7 evidence is reconciled.

On macOS/Linux, replace the venv commands with:

```bash
python3 -m venv .venv
./.venv/bin/python -m pip install -r tests/contracts/requirements.txt
```

## Run the actual integrated web app

From the repo root, with the Python environment installed:

```powershell
.\.venv\Scripts\python.exe -m flask --app integration.app run --host 127.0.0.1 --port 5000
```

Open **http://127.0.0.1:5000/**, choose **Rental Deposit** or **Consumer Complaint**, or directly open **http://127.0.0.1:5000/task5-flow.html**. This is a **local Flask development server**, not a production deployment. Keep the host on `127.0.0.1`; do not publicly expose the debug/dev server or submit real dispute facts.

In a *second* PowerShell window:

```powershell
Invoke-RestMethod http://127.0.0.1:5000/api/health
Invoke-RestMethod http://127.0.0.1:5000/api/version
Invoke-WebRequest http://127.0.0.1:5000/task5-flow.html
```

Expected health response: `{"status":"ok"}`. At the audited source snapshot, API fields are `api_version: 1.0`, `rule_version: mock-1`, and `source_version: kb-2026-11-01.1`. Check the actual returned values on your commit; do not write those versions into a new release without comparing them. Stop Flask with Ctrl+C.

For Linux/macOS use `./.venv/bin/python -m flask --app integration.app run --host 127.0.0.1 --port 5000`.

## Run verification

In a separate terminal at repository root:

```powershell
.\.venv\Scripts\python.exe -m shared.validate_contracts
.\.venv\Scripts\python.exe -m rag.import_knowledge_base
.\.venv\Scripts\python.exe -m integration.checks
.\.venv\Scripts\python.exe -X utf8 -m pytest tests/contracts tests/backend frontend/tests tests/rag tests/integration -q
```

`shared.validate_contracts` checks all shared example contracts. `rag.import_knowledge_base` verifies the five-file source package offline; `integration.checks` makes real backend/RAG calls without launching a browser. Full pytest includes frontend tests, which require the browser prerequisites for complete FE coverage; **inspect skipped/failed counts**.

Optional actual browser diagnostic, with the integrated Flask server already running:

```powershell
node integration/browser_check.mjs http://127.0.0.1:5000
```

Optional *live* publisher check (requires real internet access; page changes can cause a truthful failure; does not renew review records):

```powershell
.\.venv\Scripts\python.exe -m rag.import_knowledge_base --verify-live
```

The GitHub [tests workflow](.github/workflows/test.yml) installs dependencies on Python 3.12, validates the shared examples, runs contracts/backend/RAG/integration pytest, then frontend unittest. **The default GitHub workflow alone is not a claim that every FE browser test or every team member's clean install ran.** The coordinator's actual Task 7 isolated Windows run reported **375 passed, 7 subtests** on the audited earlier candidate; Guanyu's later [candidate browser run](frontend/TASK7_CANDIDATE_DEMO.md) reported 18/18 steps. Those runs are different from a member's independent install and from tests of any future final tagged SHA.

## Record your own clean-environment evidence

Each team member should follow the same commands in **their own fresh clone/venv**, and record:

`Tester | OS | Python/Node/browser versions | Exact HEAD SHA | Clone/venv/install exit codes | App start + API/page HTTP statuses | Full suite pass/fail/skip | Executed At (UTC) | Known limitations`

Save local logs under `instance/` (gitignored); share only non-sensitive evidence with the team. A [copyable reporting template](docs/task7-member-verification-template.md) is provided. **Do not mark an unperformed member run as PASS.**

## Source operations, rollback and release

- [Release, rollback, service recovery and state backup](docs/task7-release-handover.md)
- [RAG update, quarantine and verified source handling](rag/TASK4.md) and [Task 6 source integrity](rag/TASK6.md)
- [Task 6 BE/E2E test records](docs/task6-backend-e2e-results.md)
- [Task 7 acceptance and remaining evidence](integration_acceptance.md)

The five canonical files under `rag/knowledge_base/` and **operational** `instance/rag_quarantine.json` are not interchangeable: preserve the quarantine/history file across rollback or restart. If source state becomes invalid, let the app fail closed; never delete the state file just to restore results.

## Development-only historical previews

The Task 4 fixture page (`frontend/task4-forms.html`) and mock previews are retained for historical testing. They use Mock data and **are not the Task 7 candidate**. Launch the live integrated `/` or `/task5-flow.html` paths above for any real evaluation.
