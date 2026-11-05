# SG Navi — Task 7 integration acceptance

## Current assessment — 2026-11-05

**Technical fixes: PASS WITH LIMITS. Final freeze: PENDING MEMBER DETAILS AND FINAL VERSION RECONCILIATION.**

This section supersedes the outstanding-item list in the historical 11-03 audit
below. The current delivery remains an English source-context/referral demo;
legal eligibility rules are disabled and normal `action_card` is null.

Readiness and hosted-WSGI checkpoint: **3994850f29a04356c3a708daee56815294278895**,
delivered through [PR #64](https://github.com/Chu-Junjie/SG-Navi/pull/64). The final
archive format 2 adds Windows/Linux newline portability; its actual code digest
and fresh hosted restore are recorded in the recovery proof. The PR's exact
merged SHA and subsequent public checks must be read from its final GitHub
record; a documentation commit is not silently described as deployed.

| Item | Actual evidence and current disposition |
| --- | --- |
| Critical dependency readiness | **FIXED**. Health now checks the same source/state dependency as navigation; a dependency failure returns 503/unavailable, not 200/ok. Both actual homepage scripts require exact ok. Four new regressions first failed, then passed. Normal API 1.0 success payload is unchanged; failure example added. |
| Official source freshness | **PASS**. Five live HTTP 200 responses and all 26 excerpts matched. Both CEA old body hashes were reconstructed exactly by replacing only two footer dates; two genuine automated review rows were appended. Historical rows, evidence text and source version remain unchanged. [Proof](docs/test-results/task7-source-recheck-20261105.json). |
| RAG corpus | Five files, five sources, 26 passages/mappings, five templates, now **nine** historical/current review rows. API 1.0 / rule mock-1 / source kb-2026-11-01.1. No human or official legal approval is claimed. |
| Readiness/archive regressions | **13 passed** in the final targeted local run; dependency failure/recovery, malformed homepage responses, wrong keys, tampering, mismatched corpus/version/history, exclusive file creation and Windows/Linux newline portability covered. |
| Full local implementation suite | **466 passed, 4 skipped, 13 subtests in 48.21s** on the complete implementation, including the health-error example. The three PG skips were separately executed in real CI; the opt-in published-browser check is recorded separately. [Machine record](docs/test-results/task7-remediation-20261105.json). |
| Actual PostgreSQL CI | [Run 42004044526](https://github.com/Chu-Junjie/SG-Navi/actions/runs/42004044526): **3 passed in 4.06s**. Real disposable PostgreSQL, separate Gunicorn starts, transaction/restore, corrupt-state rejection and encrypted external restore. Ordinary CI [42004044454](https://github.com/Chu-Junjie/SG-Navi/actions/runs/42004044454) also succeeded. |
| Actual hosted nonempty persistence | **PASS in isolation**. Free Render test service srv-dbm4v2rbc2fs738b2in0 ran the same SHA through two real deployments; one quarantine event/source remained byte-for-byte identical in the isolated Neon branch. [Provider/deploy/state proof](docs/test-results/task7-hosted-recovery-20261105.json). Production state was untouched. |
| Off-provider encrypted recovery | **PASS in isolation**. Authenticated encrypted archive exported to the coordinator Windows machine, then restored into a separate freshly created hosted database. Wrong key left the empty target unchanged. The real keygen/export/wrong-target/confirmed-restore CLI commands also passed. This is a state snapshot, not a complete provider disaster-recovery system or scheduled backup service. |
| Guanyu frontend/public evidence | **DELIVERED WITH LIMITS** via merged #54–57: actual public browser 18/18, four screenshots, and member-reported Windows 430 pass / 4 skipped / 7 subtests. The personal skips remain NOT RUN locally; later public CI is separate. |
| Zheng personal environment | **USER REPORTS EXECUTED; DETAILS PENDING** as of 11-05. User confirmed execution and will supply actual SHA, commands/results and counts. It is not yet recorded as pass/fail; no personal execution is attributed to CI or this coordinator. [Current record](docs/task7-zheng-personal-check.md). |
| Review / scope | User explicitly authorized this cross-module remediation while retaining PR workflow. Guanyu supplied a real APPROVED review on the implementation. Deferred-review authorization is preserved without inventing Zheng approval. |
| Actual Render health configuration | Owner set the existing public service Health Check Path to `/api/health`; subsequent read-only Render inspection confirmed that exact value, with service plan still Free and auto-deploy still enabled. |

The public deployment is now Render Free + Neon PostgreSQL, not the historical
ephemeral demo or expiring Render test database. See the updated
[active runbook](docs/task7-junjie-render-neon-integration.md) and
[operator recovery procedure](docs/task7-state-recovery.md).

Remaining freeze actions: receive Zheng's actual execution details; reconcile
the final merged/deployed code and current evidence; then the release owner may
create `v0.9.0-rc1` on the exact accepted commit. No tag or release is created
by these technical fixes. Source/transport success does not implement legal
eligibility or a supported legal Action Card. Provider free-tier availability,
physical-device testing and external-publisher-tab navigation are not expanded
into claims by this assessment.

## Historical assessment — 2026-11-03 (retained audit trail)

**Historical technical result: PASS WITH LIMITS. At that time: NOT READY.**

Chu Junjie's assessment is complete for the evidence available on **2026-11-03**.
The fixed candidate installs, starts and passes the full suite in a fresh Python
environment. The remaining two member-environment records, candidate demonstrations
and release/recovery handover have not been provided in the reviewed repository
or Issue #7. Their absence is missing evidence, not a claim that those members'
environments fail. Task 7 stays In Progress.

This accepts an English Rental Deposit/Consumer Complaint source-context and
conservative-referral prototype. Real legal eligibility rules remain disabled;
supported legal Action Cards are unavailable. No production readiness, final tag
or release approval is given by this report.

## Fixed version and evidence alignment

| Item | Actual observation |
| --- | --- |
| Candidate assessed | `d629033b27f9eb5a9d0998b7d55304ae86ffe528` — merged Task 6 closeout |
| Earlier combined runtime audit | `49cc19f6c9d957a256fe2024d700fab0f6d215f4`; changes to the assessed candidate are README/docs only |
| Runtime/test/dependency/CI difference from that audit | None; exact component Git trees and critical blob hashes are in [the static audit](docs/test-results/task7-static-audit.json) |
| Actual API version endpoint | `api_version: 1.0`, `rule_version: mock-1`, `source_version: kb-2026-11-01.1` |
| Rule activation | 25 backend checks disabled, thresholds null; all 26 RAG mappings disabled |
| Source package | Five fixed files, five sources, 26 passages, 26 mappings, five templates and seven review-log rows |
| Source review identity | Stored method `automated_live_page_and_excerpt_check`, identity `Codex automated page and excerpt check`; no human or official legal approval is implied |
| Candidate tag | Successful remote Git query returned no tag refs; `v0.9.0-rc1` was not present at the recorded check |
| Final freeze target | Not selected. The release owner must pin the final accepted commit after the outstanding evidence is reconciled |

The source version is genuine checked-corpus metadata. `rule_version: mock-1`
identifies the deliberately disabled rule implementation, not an enabled legal
decision engine. Module ownership remains Chu/RAG and contracts, Zheng/backend
and CI/release, Guanyu/frontend and demonstrations.

## Fresh installation and execution

A new GitHub clone, separate from all previous worktrees, was checked out at the
fixed candidate SHA. A new `.venv` was created with system site-packages disabled.
Dependencies were actually downloaded/installed from the existing requirements;
the previous Python environment was not reused. The operating system, Python
installation, Node and Edge were already present, so this is a clean Python
environment test rather than a fresh-OS claim.

| Check | Actual result |
| --- | --- |
| Clone, fixed checkout, venv and requirements install | PASS, install exit 0 |
| Tracked/visible working-tree status after the audit commands | Clean; generated caches/profiles/logs remained ignored |
| Complete candidate suite | **375 passed, 7 subtests passed in 50.56s**, exit 0; 375 JUnit testcase elements, zero failures/skips |
| Real frontend browser test | All eight FE cases passed, zero JS exceptions; actual requests, no supplied API responses |
| Documented startup | Fresh-venv Flask CLI started successfully; nine actual homepage/API/form/JS/schema GETs returned 200 |
| Shared contract examples | All 11 passed |
| Direct RAG, backend connection and version diagnostic | All five checks passed |
| Real source recheck in the fresh environment | Five HTTP 200 responses, current page hashes and all 26 excerpts matched; source records unchanged |

Actual environment: Python **3.14.6**, Node **24.18.0**, installed Microsoft Edge.
Fresh resolved Python packages include Flask **3.1.3**, Werkzeug **3.1.9**, pytest
**9.2.0**, jsonschema **4.26.0** and referencing **0.37.0**. The complete installed
set is recorded in [resolved environment](docs/test-results/task7-resolved-environment.json).
Requirements retain ranges; these recorded versions describe the executed run,
not a promise that a later install will resolve identically.

Representative reproduction from the workspace parent directory:

```powershell
git clone --no-checkout https://github.com/Chu-Junjie/SG-Navi.git task7-clean-install
git -C task7-clean-install checkout --detach d629033b27f9eb5a9d0998b7d55304ae86ffe528
python -m venv task7-clean-install/.venv
cd task7-clean-install
.\.venv\Scripts\python.exe -m pip install -r tests/contracts/requirements.txt --disable-pip-version-check
.\.venv\Scripts\python.exe -X utf8 -m pytest tests/contracts tests/backend frontend/tests tests/rag tests/integration -q
.\.venv\Scripts\python.exe -m flask --app integration.app run --host 127.0.0.1 --port 5057
```

Open http://127.0.0.1:5057/task5-flow.html directly; the homepage entries remain
baseline placeholders. Exact audited commands, including ignored JUnit/captured
output options, are preserved in the JSON records. The fresh suite requires
Node 22+ and an installed Chromium-family browser for actual FE execution. No API
key or `.env` was needed for the tested local workflow.

## Team evidence and current disposition

| Evidence | Disposition | What is actually available |
| --- | --- | --- |
| Chu/coordinator clean environment | **PASS — automated** | New clone/venv install, start and full-suite logs on the coordinator Windows workspace; no independent human-attestation claim |
| Zheng clean environment | **NOT PROVIDED** | No separate member install/start/test record found in the reviewed evidence |
| Guanyu clean environment | **NOT PROVIDED** | No separate member install/start/test record found in the reviewed evidence |
| FE/BE/RAG/E2E testing | **PASS WITH LIMITS** | Merged owner records and Task 6 closeout; 38 IDs: 36 PASS, E2E-01/02 LIMITED for real legal Cards |
| Candidate-specific two-case demonstrations/screenshots | **NOT PROVIDED** | Automated FE cases exist; they do not constitute Guanyu's separate Task 7 demonstration/screenshots record |
| Release/recovery handover | **PARTIAL** | Existing README install/start was verified here; RAG update/quarantine recovery docs exist. Candidate-specific deployment/recovery/rollback handover from the release owner remains outstanding |
| Version/source alignment | **PASS** | Fixed SHA, actual API versions, canonical data and exact Git tree/blob identities recorded |
| Targeted tracked-file checks | **PASS within stated scope** | 145 tracked files, 142 text files checked; no tracked sensitive-path or configured secret-shape match |
| Peer-review timing for the documentation continuation | **OWNER-AUTHORIZED DEFERRAL** | Actual retrospective review evidence remains pending; no approval record was invented |

The tracked-file audit checks named `.env`/key/private-data/upload paths and four
credential-shape detectors. Match values are never logged. Actual test inputs
are explicitly synthetic. This is bounded inspection, not an exhaustive security
or real-world data-classification guarantee.

## CI and repository metadata

Task 6 closeout PR #46 head `d1a508516fb5b1212a37c3b81a31b6b75d45d808`
has a verified successful [CI run 41571369561](https://github.com/Chu-Junjie/SG-Navi/actions/runs/41571369561).
Its merge candidate has unchanged runtime/test/dependency/CI trees, and was also
tested independently in the new Windows environment above. Owner PR/CI evidence
is linked from [Task 6 acceptance](docs/task6-checklist.md).

The connector lists PR-triggered commit workflows only. Anonymous GitHub API
queries for releases and exact merge-push runs returned HTTP 403 with zero rate
limit remaining; HTML fallbacks returned cache-miss errors. **Release state and
that exact push-run listing remain UNVERIFIED**, rather than being reported as
absent/failed. The remote-tag result was checked separately through Git and is
conclusive for the recorded tag snapshot. Public repository visibility was
confirmed through the authenticated connector. See [metadata evidence](docs/test-results/task7-github-metadata.json)
and [tag evidence](docs/test-results/task7-tag-check.json).

## Required completion sequence

| Item | Responsible owner | Evidence needed before freezing |
| --- | --- | --- |
| F1 — member environments | ZhengZaikun, Guanyu-Lu | Each supplies actual clone/install/start/test commands, outcomes, commit and runtime versions from their own clean Python environment |
| F2 — candidate demonstrations | Guanyu-Lu | Rental and Consumer walkthroughs on the agreed candidate; actual screenshots, seven sections, source-link/error behavior and mobile presentation; preserve the legal-Card limitation |
| F3 — handover/recovery | ZhengZaikun | Pin intended local/deployment mode and final commit; provide matching recovery/rollback instructions and final CI provenance. Existing RAG operational-state preservation procedures must be respected |
| Final reconciliation | Chu-Junjie | Check new evidence against the same code/dependency/source identities and update this acceptance decision |
| Post-acceptance release action | ZhengZaikun | Only after acceptance, create `v0.9.0-rc1` on the exact accepted commit and record its tag/release/CI relation |

Tag creation is a post-acceptance action, not a circular prerequisite for this
pre-freeze technical assessment. This audit created no tag, release or deployment.
If code or dependencies change, rerun affected acceptance checks on the final
candidate. Documentation-only changes can reuse evidence with a recorded tree
comparison; no later commit is silently described as already tested.

Source update and quarantine operations are documented in [RAG Task 4](rag/TASK4.md)
and [RAG Task 6](rag/TASK6.md). Preserve operational state across restarts and
rollback; do not delete quarantine/history files as a release/recovery shortcut.

## Review deferral and Task boundary

The owner explicitly instructed this continuation to proceed while mutual review
is deferred. PR #46 was merged as `d629033` with a merge message recording that
exception and **zero actual peer-review submissions at merge**. Issue #6 is now
closed. No `APPROVED` review was created or claimed. Retrospective review notes
remain pending, and the same owner-authorized timing exception is recorded for
this Task 7 documentation continuation. It does not manufacture missing factual
environment, demonstration or release evidence.

This completes Chu's requested technical assessment and missing-evidence list.
**Overall Task 7 and candidate freezing remain open** for F1–F3 and final
reconciliation. No supported legal pathway, official legal approval or production
release is asserted.

## Machine-readable evidence

- [Decision, gaps and governance](docs/test-results/task7-acceptance-audit.json)
- [Actual fresh dependency install](docs/test-results/task7-clean-install.json)
- [Resolved isolated Python packages](docs/test-results/task7-resolved-environment.json)
- [Full clean suite command/result](docs/test-results/task7-clean-suite.json)
- [JUnit counts and actual FE browser outcomes](docs/test-results/task7-clean-results.json)
- [Real startup/API checks](docs/test-results/task7-clean-startup.json)
- [Contract and RAG/version checks](docs/test-results/task7-contracts-and-rag.json)
- [Real publisher recheck](docs/test-results/task7-live-source-check.json)
- [Component/blob identities and targeted file audit](docs/test-results/task7-static-audit.json)
- [Remote tags](docs/test-results/task7-tag-check.json)
- [CI/metadata query provenance and limitations](docs/test-results/task7-github-metadata.json)
