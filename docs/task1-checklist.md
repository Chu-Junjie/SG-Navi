# Task 1 acceptance evidence

Local administration files have been prepared. GitHub confirmed the repository exists and is public; the owner explicitly chose to keep it public instead of the guide's private setting. The owner reports invitations sent. Accepted teammate write access, project settings, runtime checks and human review remain pending. Enter evidence only after each action actually occurs.

## Repository administration

| Check | Status | Actual evidence |
| --- | --- | --- |
| `Chu-Junjie/SG-Navi` exists, public by owner decision | Verified | https://github.com/Chu-Junjie/SG-Navi; GitHub metadata confirmed public |
| Owner `Chu-Junjie` has admin access | Verified | GitHub collaborator permission: admin |
| `Guanyu-Lu` accepted collaborator invitation | Pending | Owner reports invitation sent; API returned read, write access not yet confirmed |
| `ZhengZaikun` accepted collaborator invitation | Pending | Owner reports invitation sent; API returned read, write access not yet confirmed |
| No extra collaborators | Pending | |
| Seven actual Task Issues created | Verified | Issues #1–#7: https://github.com/Chu-Junjie/SG-Navi/issues |
| Private GitHub Project and two members' access configured | Pending | Connector has no Project administration tool; see docs/task-board.md for the repository tracking table |
| PR template and AGENTS.md merged after review | Pending | PR URL |
| `main` protection enforced | Pending | Settings evidence; record plan limitation if applicable |
| Actual pytest CI check required after its first success | Pending | Check name and settings |

## Per-member runtime evidence

All rows are initially Not run. Each member must supply their own real results, not another member's screenshot.

| Member | Clone/pull | Backend starts | Homepage and health request | pytest | Commit and evidence |
| --- | --- | --- | --- | --- | --- |
| Chu Junjie | Not run | Not run | Not run | Not run | |
| Zheng Zaikun | Not run | Not run | Not run | Not run | |
| Lu Guanyu | Not run | Not run | Not run | Not run | |

## CI and independent reviews

| Check | Status | Evidence |
| --- | --- | --- |
| `/api/health` actual response | Not run | Command, HTTP status and response |
| CI pytest workflow | Not run | Run URL and commit SHA |
| Administration PR independently reviewed | Pending | PR and reviewer |
| Backend PR independently reviewed | Pending | PR and reviewer |
| Frontend PR independently reviewed | Pending | PR and reviewer |

## Test record format

| Test ID | Input | Expected | Actual | Pass/Fail/Not Run | Commit | Tester | Executed At | Bug Issue |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| TASK1-HEALTH | GET /api/health | Successful health response defined by backend owner | Not executed | Not Run | | | | |
| TASK1-HOME | Open homepage | SG Navi, two placeholder entries, actual API status | Not executed | Not Run | | | | |
| TASK1-PYTEST | Run documented pytest command | Tests pass | Not executed | Not Run | | | | |

Use a timestamp with timezone, for example `YYYY-MM-DDTHH:mm:ss+08:00`. Do not insert placeholder timestamps as execution evidence.

Task 1 remains open until all three members can run the project, CI has a successful run, and another developer has actually reviewed the relevant PRs. Record any enforcement limitation explicitly.
