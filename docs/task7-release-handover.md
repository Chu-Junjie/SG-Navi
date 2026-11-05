# Task 7 — candidate deployment, backup, recovery and release handover

> Historical local-only handover. Current public hosting, readiness and actual
> isolated hosted/encrypted recovery are documented in
> [the active runbook](task7-junjie-render-neon-integration.md),
> [state recovery](task7-state-recovery.md), and the current section of
> [integration acceptance](../integration_acceptance.md). The dated NOT PROVIDED
> and no-host statements below describe the earlier snapshot, not today's status.

**Owner:** Zheng Zaikun (backend/dependencies/CI/release documentation)  
**Scope:** reproducible **local, loopback-only** candidate demonstration and handover.  
**Status:** PRE-FREEZE PREPARATION; **do not create the v0.9.0-rc1 tag/release yet**. Owner's [technical assessment](../integration_acceptance.md) is PASS WITH LIMITS, NOT READY FOR FREEZE, pending independent member installs and final reconciliation. This document is a procedure, **not a claim** that remote deployment or rollback drills were performed.

## 1. Release identity and boundaries

| Item | Current verified information |
| --- | --- |
| Earlier coordinator clean-environment target | `d629033b27f9eb5a9d0998b7d55304ae86ffe528`, **not** a selected final release SHA |
| Later demo/navigation merge | `ba8c992f03d426108fdb1e1aac375e9320b92244`; after that commit, revalidate before freezing |
| Application contract | API `1.0`; navigation response keys are from `shared/api_contract.json` |
| Rule metadata | `rule_version=mock-1`; legal eligibility rules disabled, no genuine supported legal Action Card |
| Source metadata | `source_version=kb-2026-11-01.1` at the audited corpus; verify against `/api/version` before publishing |
| Evidence | Five canonical `rag/knowledge_base/` files; operational state in gitignored `instance/rag_quarantine.json` |
| Dependencies | `requirements.txt` plus `tests/contracts/requirements.txt`; **version ranges, not a frozen lockfile** |
| Candidate tag | `v0.9.0-rc1` reserved for **post-acceptance** tagging of the exact selected commit |
| Delivery target | Local integrated Flask server on `127.0.0.1`; **no production host is configured or verified** |

These are **development** claims only. `REFER_TO_OFFICIAL` and source links mean materials for independent review, not legal eligibility. Never fabricate `SUPPORTED_PATH`, thresholds, official approval or source review metadata to meet release criteria.

## 2. Installation and local service startup

Use a new directory and venv; do not reuse the owner's existing Python environment:

```powershell
git clone https://github.com/Chu-Junjie/SG-Navi.git
cd SG-Navi
git rev-parse HEAD
py -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r tests/contracts/requirements.txt
.\.venv\Scripts\python.exe -m flask --app integration.app run --host 127.0.0.1 --port 5000
```

Open `http://127.0.0.1:5000/` and choose a case; `/task5-flow.html` is the direct form. This is a Flask development server; do not bind to `0.0.0.0`, enable public debug, or route public users to this build. Stop with Ctrl+C; release-owner restart is manual, not a monitored service.

In another terminal:

```powershell
Invoke-RestMethod http://127.0.0.1:5000/api/health
Invoke-RestMethod http://127.0.0.1:5000/api/version
.\.venv\Scripts\python.exe -m shared.validate_contracts
.\.venv\Scripts\python.exe -m rag.import_knowledge_base
.\.venv\Scripts\python.exe -m integration.checks
.\.venv\Scripts\python.exe -X utf8 -m pytest tests/contracts tests/backend frontend/tests tests/rag tests/integration -q
```

Node 22+ and Chromium/Edge/Chrome are needed to count the browser tests as actually run; review skipped counts. When Flask is running, `node integration/browser_check.mjs http://127.0.0.1:5000` independently tests actual transport/browser interaction. The baseline GitHub [test workflow](../.github/workflows/test.yml) runs Python 3.12 contracts, backend, RAG, integration and frontend unittest; a GitHub Actions green status is **not** proof of a fresh clone by all members.

### Last documented observations (do not extrapolate)

- Coordinator isolated Windows Python install, startup and tests on earlier audited commit `d629033`: **375 passed, 7 subtests**, 11 shared examples PASS, five RAG/version checks PASS, nine HTTP page/API/asset GETs 200. See [Task 7 acceptance](../integration_acceptance.md) and [machine logs](test-results/task7-clean-suite.json).
- Guanyu's frontend Task 7 [candidate demo](../frontend/TASK7_CANDIDATE_DEMO.md): 18/18 browser steps, two case types, 4 actual screenshots, zero JS exceptions on his tested frontend source. The demo did **not** click outgoing publisher links and was not an independent install by Zheng.
- Current `main` / PR-head CI must be freshly checked before final release. A documentation-only PR may not be used to claim the final release commit was already tested.
- **Zheng member fresh-clone record:** NOT PROVIDED here; to be filled by real execution on Zheng's environment. **Guanyu independent fresh-clone record:** NOT PROVIDED in the coordinator acceptance reviewed at creation of this document.

## 3. State, backups and deployment constraints

For local demonstrations the default service uses five **version-controlled and validated** RAG files and a separate optional operational state file `instance/rag_quarantine.json`. That state records blocked sources, event chronology, and actor/reason; it is ignored by Git. **Never commit it as a release asset or include real user data.**

Before any restart/rollback that changes the working tree:

1. Stop new case submissions; shut down the development server.
2. Record the *exact* commit with `git rev-parse HEAD`, the active `GET /api/version` response while the server is up, and `python -m rag.repository state` **before** shutdown.
3. Preserve `instance/rag_quarantine.json` outside the checkout with restricted access, if it exists. Example (from repo root, with server stopped): `Copy-Item instance\rag_quarantine.json ..\sg-navi-quarantine-backup.json`. Use a protected location, not a Git-tracked directory; record the backup location internally. If absent, document "absent" rather than fabricating an empty quarantine state.
4. Copy local operational logs needed for diagnosis to a protected non-repo location; **do not** include case answers, credentials or personal dispute content in released logs.
5. Confirm the backup is readable and record its SHA-256 before changing checkout: `Get-FileHash ..\sg-navi-quarantine-backup.json -Algorithm SHA256` (if present).
6. Restore the state file only as an *intact* copy when the same authoritative state/history is required. Preserve timestamps/history and do not replace it with an empty blocklist. On a version mismatch, stop and consult the RAG owner before serving evidence.

**Not executed as part of this handover:** physical backup/restore, production deployment, remote hosting, external publisher link click-through, disaster-recovery time measurement or a multi-user load test.

### Update or quarantine of source material

Source review, live checks, quarantine and release are RAG-owner actions under [rag/TASK4.md](../rag/TASK4.md) and [rag/TASK6.md](../rag/TASK6.md). The checked corpus is not a release-owner-maintained free-text fixture.

- Inspect state: `python -m rag.repository state`
- Live page recheck (with authorized actor): `python -m rag.repository check-live --actor Chu-Junjie`; this can quarantine changed/unavailable sources.
- Manual quarantine and release require a genuine actor/reason and actual source validation. Never invoke `release` to make a broken citation test pass.
- Updating evidence content requires the correct new `source_version`, five complete source files, review history and validated mappings. `update_from` is instance-scoped, **not** a global deployment switch.

## 4. Recover from a service or source failure

| Symptom | Safe diagnostic / recovery approach |
| --- | --- |
| `/api/health` does not respond | Verify Python interpreter, venv/dependencies, current working directory, and that the local port is free. Restart Flask on loopback only. |
| `/api/version` 503 / source `unavailable` | Stop case-serving, run `python -m rag.import_knowledge_base` and `python -m rag.repository state`. Investigate unreadable/malformed canonical/state files; **do not** delete quarantine history to return a version. Escalate to Junjie for RAG repairs. |
| `/api/navigate` returns `ERROR` | Inspect configuration and diagnostic command `python -m integration.checks`; maintain no-Evidence/no-Action-Card fail-closed behavior. Do not show stale URLs. |
| Retrieved sources are absent | Check declared case, rule IDs, checked source version/review, quarantine. A safe referral with no verified links is preferable to fabricated results. |
| A source page changes or no longer matches review | RAG owner checks current site, captures factual record and quarantines as necessary; do not force `verified`. |
| A stale link survives answer edits | Treat as frontend owner issue, reproduce and escalate to Guanyu; do not bypass source validation in backend. |
| Prior version needs to be restored | Stop server; preserve state/backup; checkout an **already known reviewed commit**; reinstall from that commit's requirements in isolated venv; run full schema/import/RAG tests; verify source/version compatibility; restart loopback. If state/corpus incompatible, keep service down and request RAG owner's reconciliation. |

A rollback of the Git commit is **not** a rollback of the knowledge-source truth or quarantine events. A safe ERROR response is a successful safety outcome if validation fails. Do not silently skip migrations/version checks or pretend a stale corpus is valid.

### Example local rollback — procedure only, not an executed drill

```powershell
# Before changing refs, record the current SHA and preserve instance/rag_quarantine.json.
git rev-parse HEAD
git status --short
git checkout --detach <previous-reviewed-commit-sha>
py -m venv .venv-rollback
.\.venv-rollback\Scripts\python.exe -m pip install -r tests/contracts/requirements.txt
.\.venv-rollback\Scripts\python.exe -m rag.import_knowledge_base
.\.venv-rollback\Scripts\python.exe -m rag.repository state
.\.venv-rollback\Scripts\python.exe -X utf8 -m pytest tests/contracts tests/backend frontend/tests tests/rag tests/integration -q
```

Use a **fresh worktree/clone** when possible instead of altering a running release directory. Do not select or hardcode a previous SHA without verifying its matching approved source/dependencies. Only restart after checks pass and state compatibility is reviewed. The above commands are guidance, not evidence of a completed rollback test.

## 5. Version freeze, tag and draft release (not yet authorized)

**Required pre-tag gate:** (a) Junjie updates the Task 7 acceptance decision to READY on an agreed final commit; (b) independent member clean-install evidence is recorded and compared; (c) Guanyu's current-commit demo/screenshot and reference checks pass; (d) final CI, API/rule/source versions, source history, dependency manifest and serious-bug register reconcile; (e) any code changed after an earlier test is retested; (f) the team approves its chosen release/merge governance. Current state: **gate not met**.

Once *and only once* authorized, from a clean local clone with release-owner permission:

```powershell
git fetch origin --tags
git checkout --detach <exact-final-approved-sha>
git status --short
git rev-parse HEAD
git tag -a v0.9.0-rc1 -m "SG Navi internal release candidate; conservative source-referral prototype"
git push origin refs/tags/v0.9.0-rc1
```

Verify remotely that `refs/tags/v0.9.0-rc1` resolves to the approved commit (for an **annotated** tag, resolve the tag object to its target commit; don't confuse tag-object SHA with commit SHA). Then create a **pre-release** (not a production release) from that exact tag, link the accepted CI run and all Task 7 evidence, list unresolved limits and preserve legal/disclaimer wording. No production deployment is implied.

**Do not perform these tag/release commands before the coordinator's final acceptance.** The workflow and current GitHub connector do not prove an independent release has occurred. If there is already a tag, do not overwrite or retarget it silently.

## 6. Final handover and owner sign-off

The release package must include:

- README verified clone/start/test path; exact accepted SHA and venv dependency versions or lockfile rationale.
- API contract and version fields; all five RAG canonical files with genuine review history; safe operational quarantine handling.
- FE/BE/RAG/E2E tests with dated pass/fail/limited scope, real browser/demo screenshots and signed-off technical acceptance.
- The final GitHub Actions evidence, no P0 defects, no secret/private-data leakage within assessed checks, and rollback/restore **test evidence** or explicitly marked Not Run limitations.
- Tag `v0.9.0-rc1` and GitHub pre-release **after** approval; note whether Tag/Release were actually created.
- Each member's independent environment record from the [template](task7-member-verification-template.md), including exact commit/runtime versions and command exit codes.

**Owner status at handover authoring:** procedure prepared, technical evidence linked, **Zheng's personal fresh-install run not claimed; release tag not created; remote deploy/rollback drill not claimed**. This is truthful completion of *documentation preparation*, not final Task 7 freeze acceptance.
