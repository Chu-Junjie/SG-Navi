# Task 1 baseline acceptance

Status: **Done for baseline development**, accepted by the repository owner on 2026-10-31. The owner chose closeout based on working code, repository access, basic checks and CI; detailed historical review records are not a closeout blocker. This record replaces the earlier pending-only checklist and preserves unverified items explicitly.

Audited baseline: [`743f609cdfc0bdfac4e3c7bd9ed839f65615d9bb`](https://github.com/Chu-Junjie/SG-Navi/commit/743f609cdfc0bdfac4e3c7bd9ed839f65615d9bb), after backend PR #10 merged. The audit used an isolated checkout of `main`, not the Task 2 feature branch.

## Verified delivery

| Item | Result | Evidence |
| --- | --- | --- |
| Repository exists | Passed | [SG-Navi](https://github.com/Chu-Junjie/SG-Navi), public by owner decision |
| Three members have access | Passed | GitHub permissions: Chu-Junjie admin; Guanyu-Lu and ZhengZaikun write |
| Seven Task Issues and templates | Delivered | [Issues #1-7](https://github.com/Chu-Junjie/SG-Navi/issues); .github/ISSUE_TEMPLATE/ |
| Administration files and PR template | Merged | [PR #8](https://github.com/Chu-Junjie/SG-Navi/pull/8), including AGENTS.md |
| Homepage and real health fetch | Merged | [PR #9](https://github.com/Chu-Junjie/SG-Navi/pull/9) |
| Flask service, backend tests and CI | Merged | [PR #10](https://github.com/Chu-Junjie/SG-Navi/pull/10) |
| Repository tracking table | Delivered | [Task board](task-board.md) |
| Backend PR CI | Passed | [Actions run 41158326761](https://github.com/Chu-Junjie/SG-Navi/actions/runs/41158326761), conclusion success |

## Actual runtime and test results

Executed by Codex in the owner's local Windows workspace on 2026-10-31 with Python 3.14.6 and pytest 9.1.1. These are audit results, not independent environment reports from each member.

| Check | Expected | Actual | Result |
| --- | --- | --- | --- |
| `python -m pytest tests/backend -v` | Backend checks pass | 3 passed | Pass |
| `python -m unittest discover -s frontend/tests -v` | Homepage structure checks pass | 3 passed | Pass |
| Real HTTP `GET /api/health` | 200 and healthy JSON | 200, `{"status":"ok"}` | Pass |
| Real HTTP `GET /` | Homepage served by Flask | 200; SG Navi, both placeholders and same-origin health fetch present | Pass |

HTTP checks used a temporary Werkzeug server on an available loopback port and shut it down afterward. The sandbox blocked the first loopback request; rerunning with permitted local network access passed. The audit inspected served HTML and the real health endpoint; it did not execute JavaScript in a browser or assess visual layout.

## Recorded follow-up items

- All three permissions are confirmed, but independent clone/install/start/test records from every member have not all been supplied. This audit does not count as three personal runs.
- The audit found `main` branch protection disabled and no required CI check configured. Enforcement is a follow-up improvement, not a completed setting.
- Historical review records are incomplete. The owner waived detailed retrospective review as a Task 1 closeout condition. No missing approval is represented as having occurred; future PRs still follow AGENTS.md.
- Only the repository tracking table is verified. A native GitHub Project and an exhaustive collaborator inventory have not been verified.
- Some directory placeholders from the original target layout are absent. README lists actual baseline files; remaining modules and schemas belong to their assigned Tasks.

Task 2 may proceed under this baseline acceptance. Task 1 acceptance does not mean navigation, legal rules, official evidence, RAG or full case forms are implemented.
