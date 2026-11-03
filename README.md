# SG Navi

Group 6 project for English Rental Deposit and Consumer Complaint navigation.

Tasks 1-4 provide a working development baseline: Flask APIs, schema-generated mock forms, shared contracts, source preparation, conservative backend logic and independent evidence retrieval/citation checks. Task 5 connects the real frontend/API/RAG call chain with consistent versions and visible verified source context. See [Task 5 acceptance](docs/task5-checklist.md) for real browser results and the remaining boundary: legal eligibility rules stay disabled.

[Task 6 acceptance](docs/task6-checklist.md) records the combined 2026-11-03 audit: **375 tests and 7 subtests passed**, including the actual FE browser runner. All 38 formal IDs have records: **36 PASS, 2 LIMITED** because genuine supported legal Action Cards remain unavailable. Task 7 candidate acceptance is separate.

## Team and repository

| Member | GitHub login | Responsibility | Verified access |
| --- | --- | --- | --- |
| Chu Junjie | `Chu-Junjie` | Repository administration, shared contracts, RAG, integration | Admin |
| Zheng Zaikun | `ZhengZaikun` | Backend, tests, dependencies and CI | Write |
| Lu Guanyu | `Guanyu-Lu` | Frontend and frontend tests | Write |

Repository: [Chu-Junjie/SG-Navi](https://github.com/Chu-Junjie/SG-Navi). It is public by the owner's explicit decision. Task 1 was accepted for baseline development on 2026-10-31; see [the acceptance record](docs/task1-checklist.md) for verified results and remaining limitations.

## Install and run on Windows

Use Python 3.12 or newer and Git. From PowerShell:

```powershell
git clone https://github.com/Chu-Junjie/SG-Navi.git
cd SG-Navi
py -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r tests/contracts/requirements.txt
.\.venv\Scripts\python.exe -m flask --app backend.app run --host 127.0.0.1 --port 5000
```

Open [the homepage](http://127.0.0.1:5000/). It displays SG Navi, Rental Deposit and Consumer Complaint placeholder entries, and a health status fetched from the same Flask service. The placeholders do not yet open complete case flows. The health indicator should show Online when its request succeeds; use Refresh to check again.

In a second PowerShell window, verify the backend:

```powershell
Invoke-RestMethod http://127.0.0.1:5000/api/health
```

The response is `{"status":"ok"}`. Stop the development server with Ctrl+C. No API key or `.env` is required for this baseline. A static server for `frontend/` alone does not provide `/api/health`; use Flask for the integrated page and health endpoint.

## Preview Task 4 forms

In another terminal, serve the frontend prototype and open [the form preview](http://127.0.0.1:8000/task4-forms.html):

```powershell
.\.venv\Scripts\python.exe -m http.server 8000 --directory frontend
```

Select Rental Deposit or Consumer Complaint, edit answers and choose one of the four Mock API statuses. The page preserves unknown/null/false values and shows the seven Action Card sections. Synthetic source examples stay marked Needs verification. This prototype loads fixture JSON; it is an independent Task 4 demonstration rather than a full API/RAG flow.

For independent RAG usage:

```powershell
.\.venv\Scripts\python.exe -m rag.retriever rental_deposit --rule-id SCT_RESIDENTIAL_SCOPE
```

[RAG Task 4 instructions](rag/TASK4.md) document the retrieval response, citation validation, quarantine and source update procedures.

## Task 5 local integration

The coordinator's same-origin configuration serves the real frontend and backend in one process:

```powershell
.\.venv\Scripts\python.exe -m flask --app integration.app run --host 127.0.0.1 --port 5000
```

Open http://127.0.0.1:5000/task5-flow.html. Run `python -m integration.checks` for real Backend/RAG diagnostics, and optionally `node integration/browser_check.mjs http://127.0.0.1:5000` for actual browser requests (Node 22+ and Edge). Both diagnostics passed on audited main `913304e`. [Task 5 acceptance](docs/task5-checklist.md) records 346 tests and 7 subtests passed, real source links in both scenarios, owner fixes and exact commands. A nonzero diagnostic exit still indicates a failure that must be investigated.

For the complete local suite on Windows, use UTF-8 mode so the Python test reader can decode Node output:

```powershell
.\.venv\Scripts\python.exe -X utf8 -m pytest tests/contracts tests/backend frontend/tests tests/rag tests/integration -q
```

FE-01–08 require Node 22+ and an installed Chromium/Edge/Chrome browser. Missing runtimes are explicitly reported as skipped/NOT RUN and must not be counted as FE acceptance. The audited Windows run had no skipped tests. [Frontend reproduction](frontend/TASK6_FE_RESULTS.md) and [backend/HTTP E2E records](docs/task6-backend-e2e-results.md) explain the separate test scopes.

## Run the baseline and contract tests

From the repository root after installing dependencies:

```powershell
.\.venv\Scripts\python.exe -m shared.validate_contracts
.\.venv\Scripts\python.exe -m rag.import_knowledge_base
.\.venv\Scripts\python.exe -m pytest tests/contracts tests/backend tests/rag -v
.\.venv\Scripts\python.exe -X utf8 -m unittest discover -s frontend/tests -v
```

The 2026-10-31 audit of baseline commit `743f609cdfc0bdfac4e3c7bd9ed839f65615d9bb` passed 3 backend tests and 3 homepage structure tests. A temporary real HTTP server returned 200 for `/` and `/api/health`. Backend PR #10's CI passed. These are results from the audited environment, not proof that all three members independently ran the project or that the audit executed browser JavaScript.

## Current baseline layout

```text
backend/                 Flask app and health route
frontend/                Homepage and structure tests
tests/backend/           Backend tests
tests/contracts/         Shared contract tests
shared/                  Canonical contracts, examples and validator
rag/                     Source preparation, knowledge files and import validator
tests/rag/               Source ingestion tests
docs/                    Setup instructions, acceptance record and task board
.github/ISSUE_TEMPLATE/  Task 1-7 templates
.github/workflows/       Task 1 CI
.github/pull_request_template.md
AGENTS.md
requirements.txt
.gitignore
```

The frontend forms, backend logic and RAG module are merged through PRs #23-25. See [the task board](docs/task-board.md) and [Task 4 acceptance](docs/task4-checklist.md). The 2026-11-02 combined audit passed 278 tests and 2 subtests, 24 browser case/status/width combinations and the five-page live source check. [RAG instructions](rag/README.md) explain source validation and import.

The API exposes GET /api/health, GET /api/case-types, GET /api/version and POST /api/navigate. Normal navigation requests use conservative scope/clarification behavior and call real RAG for source context after required facts are supplied. Valid referrals expose checked Evidence links with the real source version; unavailable or invalid sources remain hidden. Source-based legal eligibility rules remain disabled and no eligible legal route is asserted. The earlier four-state fixture viewer remains available at http://127.0.0.1:8000/mock-preview.html when the frontend static server is running.

## Collaboration and follow-up

Read [AGENTS.md](AGENTS.md). Work on a feature branch, stay within your module, open a PR and request another developer's review before merging. Never commit secrets or real dispute data.

Enforced branch protection and required CI checks remain follow-up improvements; the last audit found `main` unprotected. Independent member environment records have not all been supplied. These limitations do not block the owner's agreed Task 1 baseline closeout. The repository task table is verified; a native GitHub Project has not been verified.
