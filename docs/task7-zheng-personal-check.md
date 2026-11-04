# Task 7 — Zheng personal Windows clean-install record (execution required)

**Status: NOT RUN on Zheng's personal Windows PC.** This is an exact, reproducible command sheet, not an attestation. CI/Render results must not be renamed as member-operated results. No passwords or PostgreSQL URL should be pasted into this document, GitHub, screenshots or chat.

The user should conduct this **personally** on Windows with PowerShell and Git/Python installed. Start in a new directory where a folder named `SG-Navi-Zheng-clean` does not already exist.

## Step 1 — Fresh clone and identify exact source

```powershell
git clone https://github.com/Chu-Junjie/SG-Navi.git SG-Navi-Zheng-clean
cd SG-Navi-Zheng-clean
git rev-parse HEAD
git status --short
git --version
py -0p
node --version
```

After the PostgreSQL PR has been merged, record the **actual `main` SHA**. Before final freeze, the coordinator will supply the final approved SHA; to test that exact commit run `git checkout --detach <approved-SHA>` and record `git rev-parse HEAD` again. Do not choose or invent the SHA.

## Step 2 — New isolated Python installation

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe --version
.\.venv\Scripts\python.exe -m pip install -r tests/contracts/requirements.txt
.\.venv\Scripts\python.exe -m pip check
.\.venv\Scripts\python.exe -m pip freeze
```

If Python 3.12 is unavailable, record which actual interpreter you chose and any compatibility issues. Installing a new Python version is a separate local action, not proof of an already-run command.

## Step 3 — Actual contract/source/integration/backend/frontend tests

```powershell
.\.venv\Scripts\python.exe -m shared.validate_contracts
.\.venv\Scripts\python.exe -m rag.import_knowledge_base
.\.venv\Scripts\python.exe -m integration.checks
.\.venv\Scripts\python.exe -X utf8 -m pytest tests/contracts tests/backend frontend/tests tests/rag tests/integration -q -rs
```

**Record actual output**, including explicit `passed`, `failed`, `skipped`, subtests, any Node/Chromium test skips, timestamps and process exit status. The actual PostgreSQL durability tests require a specially authorized disposable PostgreSQL database and are expected to skip on an ordinary personal setup; that does **not** mean they passed locally.

## Step 4 — Actual local Flask startup and HTTP

In terminal A, while in the clean clone:

```powershell
.\.venv\Scripts\python.exe -m flask --app integration.app run --host 127.0.0.1 --port 5000
```

In terminal B:

```powershell
Invoke-RestMethod http://127.0.0.1:5000/api/health
Invoke-RestMethod http://127.0.0.1:5000/api/version
Invoke-WebRequest http://127.0.0.1:5000/task5-flow.html
```

Both Rental and Consumer should be tested with synthetic inputs only (as in `tests/backend/test_task7_public_backend.py`). Stop Flask using Ctrl+C; record successful shutdown. Use the observed `api_version`, `rule_version`, `source_version`; do not infer versions from the README alone.

## Actual results — fill only after running

| Requirement | Actual observed result |
| --- | --- |
| Tester / computer | ZhengZaikun / NOT RUN |
| OS and UTC/local time | NOT RUN |
| Git clone exit status | NOT RUN |
| Actual checked-out SHA | NOT RUN |
| Python / venv / pip freeze | NOT RUN |
| Dependency install and pip check | NOT RUN |
| 11 shared contract samples | NOT RUN |
| RAG source load and integration diagnostics | NOT RUN |
| pytest PASS / FAIL / SKIP / subtests | NOT RUN |
| Node/Chrome/Edge availability | NOT RUN |
| Flask startup, shutdown and HTTP | NOT RUN |
| Rental and Consumer synthetic API flow | NOT RUN |
| Actual logs/screenshots directory | NOT PROVIDED |

**Do not commit `.venv`, instance runtime state, personally identifying case data, or private database URLs.** Send only redacted execution logs/test counts to the coordinator and update this record after real testing.
