# Task 7 independent clean environment — actual attempted execution

**Executor:** ChatGPT tool container, NOT Guanyu's personal Windows PC. This is not a human/member-owned clean-run signoff. Date: 2026-11-04 00:16:57 UTC. Linux x86_64; Git 2.47.3; Python 3.13.5; Node 22.16.0; Chromium 144.0.7559.96.

GitHub connector inspected main SHA ffb503f9f0de4fd4fbb4cf8dcf3d2a6f653b5892. Actual git clone command was executed:

    git clone --no-checkout https://github.com/Chu-Junjie/SG-Navi.git /mnt/data/sg-navi-task7-clean-clone

Actual stderr:
    Cloning into '/mnt/data/sg-navi-task7-clean-clone'...
    fatal: unable to access 'https://github.com/Chu-Junjie/SG-Navi.git/': Could not resolve host: github.com

Exit code 128. No clone created and no checkout SHA could be measured. This is DNS/network isolation in this container; NOT an observed failure of the GitHub repository.

| Step | Actual status |
| --- | --- |
| Clone | FAIL: exit 128 |
| Checkout and record SHA | NOT RUN |
| Create isolated .venv | NOT RUN |
| Install dependencies | NOT RUN |
| Start local Flask and GET health/version | NOT RUN |
| Contract + backend + frontend + RAG/E2E tests | NOT RUN |
| Clean-install browser run/screenshot | NOT RUN |

**Actual independent environment counts:** 0 PASS, 1 setup FAIL, 6 NOT RUN. There is no real pytest pass/fail/skip total from this attempt. Existing GitHub CI and Chu's clean install are separate and must not be relabeled as Guanyu's independently executed test.

## Required Guanyu Windows clean-clone rerun — NOT EXECUTED by this actor

Run in PowerShell in a NEW directory with network access. Pin the eventual approved exact candidate SHA and save actual outputs and pass/fail/skip numbers:

    git clone https://github.com/Chu-Junjie/SG-Navi.git SG-Navi-task7-clean
    cd SG-Navi-task7-clean
    git rev-parse HEAD
    py --version
    node --version
    py -m venv .venv
    .\.venv\Scripts\python.exe -m pip install -r tests/contracts/requirements.txt
    .\.venv\Scripts\python.exe -m pip freeze
    .\.venv\Scripts\python.exe -m shared.validate_contracts
    .\.venv\Scripts\python.exe -m integration.checks
    .\.venv\Scripts\python.exe -X utf8 -m pytest tests/contracts tests/backend frontend/tests tests/rag tests/integration -q

In a second terminal:

    .\.venv\Scripts\python.exe -m flask --app integration.app run --host 127.0.0.1 --port 5000

Then request /api/health and /api/version at http://127.0.0.1:5000 and exercise both scenarios. Record all actual versions, exit codes, failures, skips and dates. The personal clean-environment evidence remains NOT PROVIDED until the user performs these steps.
