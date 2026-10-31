# SG Navi

Group 6 project for English Rental Deposit and Consumer Complaint navigation.

Task 1 provides a working development baseline: a Flask service, a homepage with two placeholder case entries, a real backend health indicator, basic tests and GitHub Actions. Full case forms, the navigation API, legal rules and retrieval are later Tasks.

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
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m flask --app backend.app run --host 127.0.0.1 --port 5000
```

Open [the homepage](http://127.0.0.1:5000/). It displays SG Navi, Rental Deposit and Consumer Complaint placeholder entries, and a health status fetched from the same Flask service. The placeholders do not yet open complete case flows. The health indicator should show Online when its request succeeds; use Refresh to check again.

In a second PowerShell window, verify the backend:

```powershell
Invoke-RestMethod http://127.0.0.1:5000/api/health
```

The response is `{"status":"ok"}`. Stop the development server with Ctrl+C. No API key or `.env` is required for this baseline. A static server for `frontend/` alone does not provide `/api/health`; use Flask for the integrated page and health endpoint.

## Run the Task 1 tests

From the repository root after installing dependencies:

```powershell
.\.venv\Scripts\python.exe -m pytest tests/backend -v
.\.venv\Scripts\python.exe -m unittest discover -s frontend/tests -v
```

The 2026-10-31 audit of baseline commit `743f609cdfc0bdfac4e3c7bd9ed839f65615d9bb` passed 3 backend tests and 3 homepage structure tests. A temporary real HTTP server returned 200 for `/` and `/api/health`. Backend PR #10's CI passed. These are results from the audited environment, not proof that all three members independently ran the project or that the audit executed browser JavaScript.

## Current baseline layout

```text
backend/                 Flask app and health route
frontend/                Homepage and structure tests
tests/backend/           Backend tests
docs/                    Setup instructions, acceptance record and task board
.github/ISSUE_TEMPLATE/  Task 1-7 templates
.github/workflows/       Task 1 CI
.github/pull_request_template.md
AGENTS.md
requirements.txt
.gitignore
```

Shared contracts and remaining module directories are added in their assigned Tasks. See [the task board](docs/task-board.md). Task 2 contracts are being reviewed in [PR #11](https://github.com/Chu-Junjie/SG-Navi/pull/11).

## Collaboration and follow-up

Read [AGENTS.md](AGENTS.md). Work on a feature branch, stay within your module, open a PR and request another developer's review before merging. Never commit secrets or real dispute data.

Enforced branch protection and required CI checks remain follow-up improvements; the last audit found `main` unprotected. Independent member environment records have not all been supplied. These limitations do not block the owner's agreed Task 1 baseline closeout. The repository task table is verified; a native GitHub Project has not been verified.
