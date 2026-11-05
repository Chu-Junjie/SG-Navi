# Task 7 — Guanyu Windows independent environment verification (2026-11-04)

**Record type:** Member-reported, actual local Windows execution evidence for Issue #7. This records terminal output and manual observations supplied by **`Guanyu-Lu`**, not execution performed by the project coordinator or by GitHub Actions. **Disposition: PASS WITH LIMITATIONS (member local checks); coordinator acceptance PENDING.**

**Final coordinator disposition (2026-11-05): ACCEPTED WITH THE RECORDED LIMITS.** The original observations below remain Guanyu's member-reported run. The owner subsequently delegated the remaining work: a fresh coordinator clone of implementation `2d14ed5a612d35e35e1f6b9cb0a5fca0c6333d87` passed the full suite and both real local candidate browser journeys (18/18 technical steps, four actual desktop/mobile screenshots, zero JS exceptions). Frontend contents match the already tested #64 implementation. [Exact identities and delegated results](test-results/task7-final-candidate-20261105.json). This is not a newly claimed Guanyu execution or physical-phone/official-publisher click audit.

## Test identity and scope

| Field | Recorded observation |
| --- | --- |
| Tester / account | `Guanyu-Lu` |
| Date | 2026-11-04 (local web-server log); exact UTC test start/end not captured |
| OS | Windows with PowerShell; edition, build and architecture not separately recorded |
| Repository | `https://github.com/Chu-Junjie/SG-Navi` |
| Branch / checkout | `main` |
| **Exact tested HEAD** | **`9ad3b92c63c696aa8dd6b16a6bfedcfa383972a9`** |
| Clone | Actual fresh `git clone` completed, 933 objects received; worktree clean at the end |
| Git | `2.45.1.windows.1` |
| Python | `3.14.10`, project-local `.venv`; base interpreter: isolated Python installation (installation path withheld) |
| Isolation evidence | `sys.prefix` reported the project's `.venv`; `sys.base_prefix` reported the separate Python 3.14 installation |
| Node.js | Not installed; Node-dependent tests **NOT RUN** locally |
| Browser | Microsoft Edge used for manual interactions; executable path/version not recorded |
| Dependency installation | `pip install --only-binary=:all: --no-cache-dir -r tests/contracts/requirements.txt`: 19 packages successfully installed |
| Dependency integrity | `pip check`: `No broken requirements found.` |
| API wire versions | `api_version=1.0`, `rule_version=mock-1`, `source_version=kb-2026-11-01.1` |

The tester reported that the pre-existing Python 3.11 installation remained the default. This local test did not require a system-wide Python replacement, API keys, database server, or `npm install`. Python `.venv` isolates dependencies but is **not** an OS security sandbox.

## Actual commands and observed results

From the fresh local checkout (commands reproduced for audit, **not** rerun by this document author):

| Step | Command / evidence | Observed result |
| --- | --- | --- |
| Fresh clone | `git clone https://github.com/Chu-Junjie/SG-Navi.git` | Completed; Git objects downloaded, clean checkout |
| Commit identity | `git rev-parse HEAD` | `9ad3b92c63c696aa8dd6b16a6bfedcfa383972a9` |
| Isolated environment | Executed `python.exe -m venv .venv` using the separately installed Python 3.14 executable (local executable path redacted) | Created; `.venv\Scripts\python.exe --version` returned `Python 3.14.10` |
| Dependency installation | `.venv\Scripts\python.exe -m pip install --only-binary=:all: --no-cache-dir -r tests/contracts/requirements.txt` | `Successfully installed` all 19 resolved distributions |
| Package consistency | `.venv\Scripts\python.exe -m pip check` | `No broken requirements found.` |
| Module import | `.venv\Scripts\python.exe -c "import flask, pytest, jsonschema; print('SG NAVI Python dependencies OK')"` | `SG NAVI Python dependencies OK` |
| Contract examples | `.venv\Scripts\python.exe -m shared.validate_contracts` | **11 PASS**, covering navigate, health, case types, version and retrieval examples |
| RAG knowledge import/validation | `.venv\Scripts\python.exe -m rag.import_knowledge_base` | **PASS**: 5 sources, 26 passages, 26 rule mappings, 5 templates; source version `kb-2026-11-01.1` |
| In-process integration | `.venv\Scripts\python.exe -m integration.checks` | `"passed": true`; **5/5** checks passed (direct RAG/citations for each case, backend-to-RAG for each case, version consistency) |
| Local Flask server | `.venv\Scripts\python.exe -m flask --app integration.app run --host 127.0.0.1 --port 5000` | Started with `Debug mode: off`; local homepage and form GET responses were HTTP 200 |
| API health | `Invoke-RestMethod http://127.0.0.1:5000/api/health` | `status: ok` |
| API versions | `Invoke-RestMethod http://127.0.0.1:5000/api/version` | `1.0 / mock-1 / kb-2026-11-01.1` |
| Git state | `git status` | `On branch main`, `nothing to commit, working tree clean` |

The Flask log recorded actual `POST /api/navigate` requests returning HTTP 200 and GETs for both the root page and rental form and required JS/JSON assets; `favicon.ico` returned a nonblocking 404. An HTTP 200 by itself does not establish legal-route correctness.

### Python/Frontend/RAG automated suite

Executed from the local checkout:

~~~powershell
.\.venv\Scripts\python.exe -X utf8 -m pytest tests/contracts tests/backend frontend/tests tests/rag tests/integration -q -rs
~~~

**Actual result:** `430 passed, 4 skipped, 7 subtests passed in 19.52s`, with **zero reported failures**. An earlier `-q` execution returned the same counts in 21.00s.

Exactly four tests were skipped, with the following recorded reasons:

| Test | Actual skip reason |
| --- | --- |
| `frontend/tests/test_task6_real_browser.py` | `NOT RUN: Node.js or Chromium/Chrome/Edge executable not found` |
| `frontend/tests/test_task7_candidate_demo.py` | `NOT RUN: Node.js 22+ or Chromium/Chrome/Edge not installed` |
| `frontend/tests/test_task7_public_config.py` | `NOT RUN: Node.js unavailable` |
| `frontend/tests/test_verified_sources_runner.py` | `Node.js is not available in this Python CI` |

These are **NOT RUN**, not PASS; local JavaScript/Chromium automated coverage is incomplete. The skip messages do not by themselves establish that Edge is absent; the tester used Edge manually, but Node.js was unavailable.

### Manual real-browser checks (tester-reported)

Tester reported **8/8 manually checked items PASS** on the local Flask-served frontend, using only synthetic inputs:

| Check | Reported result |
| --- | --- |
| Rental Deposit entry opens the guided form | PASS |
| Rental Deposit missing facts trigger clarification | PASS |
| Rental Deposit synthetic answers submit and display official source context | PASS |
| Consumer Complaint entry opens the guided form | PASS |
| Consumer Complaint missing facts trigger clarification | PASS |
| Consumer Complaint synthetic answers submit and display official source context | PASS |
| Edit prior answers and resubmit | PASS |
| Return home and reopen case forms | PASS |

A copied example Rental Deposit response showed `REFER_TO_OFFICIAL`, verified Judiciary source-reference metadata and seven rendered **fallback/Needs verification** headings; it was **not** a populated legal Action Card. These manual checks are tester-reported observations, not a formal automated browser trace or a captured physical-device test. This record does not claim measured 320px/390px mobile results, JavaScript exception counts or network-failure retry results from this local run.

## Resolved package snapshot (local pip freeze)

~~~text
attrs==26.1.0
blinker==1.9.0
click==8.5.0
colorama==0.4.6
Flask==3.1.3
gunicorn==23.0.0
iniconfig==2.3.1
itsdangerous==2.2.0
Jinja2==3.1.6
jsonschema==4.26.0
jsonschema-specifications==2025.9.1
MarkupSafe==3.0.4
packaging==26.3
pluggy==1.7.0
Pygments==2.21.0
pytest==9.2.0
referencing==0.37.0
rpds-py==2026.9.1
Werkzeug==3.1.9
~~~

This is a resolved-version observation of this execution, **not** a pinned project lockfile or proof that a subsequent fresh install will resolve the same versions. The repository's main CI workflow uses Python 3.12; this check used Python 3.14.10.

## Boundaries, remaining verification and handover

- **Local technical result: PASS WITH LIMITATIONS.** The 430 executed tests passed and both reported manual case flows worked, but four Node-dependent browser/JS tests were skipped locally.
- Current rule version is `mock-1`. Both paths are conservative referrals; `SUPPORTED_PATH` eligibility determination and a supported populated legal Action Card remain unavailable. Seven fallback sections must not be represented as a legal decision.
- The already recorded CI browser demonstrations in `frontend/TASK7_CANDIDATE_DEMO.md` are **separate execution evidence**, not browser tests executed on the tester's Windows machine. The final candidate commit must be reconciled with that evidence.
- The exact UTC test start/end, Windows edition and Edge version were not captured and are **NOT RECORDED**, not invented.
- The primary evidence for this member record is the tester's supplied PowerShell output and manual checks in the project conversation; original local terminal transcripts/screenshots are **not attached** to this PR. Do not claim independent reproduction or reviewer sign-off based only on this record.
- This document changes **only member verification documentation**, not backend code, legal rules, source reviews, API configuration, deployment, CI or the release tag.
- **Coordinator action:** Chu Junjie to assess whether this member-local PASS WITH LIMITATIONS plus separately available CI browser evidence satisfies the Task 7 member-environment acceptance gate. Do not freeze `v0.9.0-rc1` or mark the team Task 7 accepted from this record alone.

**Submission for review:** Guanyu-Lu Windows member evidence; **peer review and coordinator decision PENDING**.
