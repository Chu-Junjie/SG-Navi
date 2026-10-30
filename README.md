# SG Navi

Group 6 project for Rental Deposit and Consumer Complaint navigation.

This initial package contains Chu Junjie's Task 1 repository administration files. Backend, frontend, dependencies and CI are assigned to the other two developers and are not implemented here.

## Team

| Member | GitHub login | Responsibility |
| --- | --- | --- |
| Chu Junjie | `Chu-Junjie` | Repository owner, shared contracts, RAG, integration |
| Zheng Zaikun | `ZhengZaikun` | Backend, pytest, GitHub Actions |
| Lu Guanyu | `Guanyu-Lu` | Frontend |

The owner reports sending both invitations. Accepted collaborator write access still requires verification. The repository is public by the owner's explicit decision, overriding the shared guide's original private-repository requirement.

## Task 1 setup

Follow [the GitHub setup instructions](docs/github-setup.md) to finish collaborator access, review rules and a private task board. Repository: https://github.com/Chu-Junjie/SG-Navi (public by owner decision). Administration files use a feature branch and PR; seven Task Issues track the work.

Use [the Task 1 checklist](docs/task1-checklist.md) to record real acceptance evidence. The seven actual Task Issues are linked from [the repository task board](docs/task-board.md). Tasks 2–7 remain in Backlog; their Issues do not authorize starting them early.

## Planned project layout

```text
frontend/              index.html, css/, js/              Guanyu-Lu
backend/               app.py, routes/, rules/             ZhengZaikun
rag/                   knowledge_base/, retriever.py      Chu-Junjie
shared/                api_contract.json, schemas/         Chu-Junjie
tests/                 backend/, rag/, integration/        Respective owners
docs/                  sources/, test-results/             Respective owners
.github/workflows/     test.yml                            ZhengZaikun
AGENTS.md
README.md
requirements.txt                                           ZhengZaikun
.env.example                                               Empty values only
.gitignore
```

This is the agreed target layout, not a list of implemented files. The respective owners create their Task 1 modules.

## Installation, startup and tests

Clone the public repository (write access is still required to push feature branches):

```powershell
git clone https://github.com/Chu-Junjie/SG-Navi.git
cd SG-Navi
```

No application start or pytest command is available in this administration package. Zheng Zaikun must add tested environment, Flask, `/api/health`, pytest and CI instructions in his Task 1 PR. Lu Guanyu must document how to open the homepage and verify the health request in his PR. Do not mark Task 1 complete until all three members have run the resulting project.

## Contribution workflow

Read [AGENTS.md](AGENTS.md). Branch from updated `main`, make the assigned change, open a PR using the template, and request another developer's review. Record real test results and resolve review discussions before merging.
