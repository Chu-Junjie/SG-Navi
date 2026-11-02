# SG Navi

Group 6 project for English Rental Deposit and Consumer Complaint navigation.

Tasks 1-3 provide a working baseline: a Flask service, a homepage with a real health indicator, shared API contracts, two case schemas, mock previews, source preparation and disabled rule configurations. Full case forms, runtime legal rules and retrieval remain later work. See [Task 2 acceptance](docs/task2-checklist.md) and [Task 3 acceptance](docs/task3-checklist.md) for verified results.

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

## Run the baseline and contract tests

From the repository root after installing dependencies:

```powershell
.\.venv\Scripts\python.exe -m shared.validate_contracts
.\.venv\Scripts\python.exe -m rag.import_knowledge_base
.\.venv\Scripts\python.exe -m pytest tests/contracts tests/backend tests/rag -v
.\.venv\Scripts\python.exe -m unittest discover -s frontend/tests -v
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

The shared contract, frontend schemas, source preparation, disabled rule configuration and Task 3 mappings are merged. See [the task board](docs/task-board.md) and [Task 3 acceptance](docs/task3-checklist.md). The 2026-11-02 closeout checks passed 186 tests; all five source pages and 26 excerpts passed the live recheck. [RAG instructions](rag/README.md) explain how to validate and import the source bundle.

Task 2 endpoints are GET /api/health, GET /api/case-types, GET /api/version and POST /api/navigate. They are contract-valid stubs with mock version identifiers. The standalone preview can be opened with `python -m http.server 8000 --directory frontend` at http://127.0.0.1:8000/mock-preview.html; this preview uses synthetic JSON, while Flask provides the API.

## Collaboration and follow-up

Read [AGENTS.md](AGENTS.md). Work on a feature branch, stay within your module, open a PR and request another developer's review before merging. Never commit secrets or real dispute data.

Enforced branch protection and required CI checks remain follow-up improvements; the last audit found `main` unprotected. Independent member environment records have not all been supplied. These limitations do not block the owner's agreed Task 1 baseline closeout. The repository task table is verified; a native GitHub Project has not been verified.
