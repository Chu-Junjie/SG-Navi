# Task 7 — independent member environment record (fill from a **real** run)

**Important:** This file is an unexecuted template. Do not copy the coordinator's clean-install results into another member's `PASS` column. Preserve real errors, skipped tests and the exact repository commit.

| Metadata | Actual value |
| --- | --- |
| Member / GitHub account | NOT RECORDED |
| Tester / execution method | NOT RECORDED |
| UTC executed at (start/end) | NOT RUN |
| OS, architecture | NOT RECORDED |
| Git version | NOT RECORDED |
| Python version and executable | NOT RECORDED |
| Node version | NOT RECORDED |
| Browser and version | NOT RECORDED |
| Repo URL | https://github.com/Chu-Junjie/SG-Navi |
| **Exact `git rev-parse HEAD`** | NOT RUN |
| Source/rule/API versions from real `GET /api/version` | NOT RUN |
| Isolated venv, system site-packages disabled | NOT VERIFIED |
| Actual dependency versions (`pip freeze`) | NOT RUN |

## Commands and outcomes

Run from a **new cloned repository**, ideally from a separately created working directory, using PowerShell on Windows:

```powershell
git clone https://github.com/Chu-Junjie/SG-Navi.git
cd SG-Navi
git rev-parse HEAD
py --version
node --version
py -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r tests/contracts/requirements.txt
.\.venv\Scripts\python.exe -m pip freeze
.\.venv\Scripts\python.exe -m shared.validate_contracts
.\.venv\Scripts\python.exe -m rag.import_knowledge_base
.\.venv\Scripts\python.exe -m integration.checks
.\.venv\Scripts\python.exe -X utf8 -m pytest tests/contracts tests/backend frontend/tests tests/rag tests/integration -q
```

In terminal A, start the local integrated service:

```powershell
.\.venv\Scripts\python.exe -m flask --app integration.app run --host 127.0.0.1 --port 5000
```

In terminal B, test HTTP, then optionally real-browser transport:

```powershell
Invoke-RestMethod http://127.0.0.1:5000/api/health
Invoke-RestMethod http://127.0.0.1:5000/api/version
Invoke-WebRequest http://127.0.0.1:5000/task5-flow.html
node integration/browser_check.mjs http://127.0.0.1:5000
```

| Step | Actual stdout/stderr summary | Exit code | PASS / FAIL / NOT RUN |
| --- | --- | --- | --- |
| Clone and exact checkout | NOT RUN | — | NOT RUN |
| Create isolated venv | NOT RUN | — | NOT RUN |
| Install requirements | NOT RUN | — | NOT RUN |
| Contract examples | NOT RUN | — | NOT RUN |
| RAG import | NOT RUN | — | NOT RUN |
| Five Backend/RAG diagnostics | NOT RUN | — | NOT RUN |
| Full pytest including real FE (pass/fail/skip/subtests) | NOT RUN | — | NOT RUN |
| Flask startup on loopback | NOT RUN | — | NOT RUN |
| Health, version and case form HTTP | NOT RUN | — | NOT RUN |
| Real Edge/Chromium browser diagnostic | NOT RUN | — | NOT RUN |
| Check release blockers / suspicious files | NOT RUN | — | NOT RUN |

**Actual bugs / reproducible steps:** NOT RECORDED.  
**Evidence artifact locations:** NOT RECORDED. Keep private logs in ignored `instance/` and redact personal data.  
**Differences from coordinator's clean-environment versions:** NOT REVIEWED.  
**Sign-off member:** NOT SIGNED.  
**Coordinator decision against final candidate SHA:** PENDING.

## Required classification

If Node/browser is missing, do not mark frontend tests PASS when skipped. If the app returns safe `REFER_TO_OFFICIAL` with source links and null legal Action Card, record the correct technical result and **LIMITED** supported-path functionality rather than inventing a `SUPPORTED_PATH`. Actual failed/unknown checks remain visible; never fill the table from expected outcomes.
