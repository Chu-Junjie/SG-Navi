# Task 1 GitHub setup

These instructions implement Chu Junjie's repository administration responsibility. They are not evidence that the online actions have happened.

## 1 Repository created with owner-approved visibility

GitHub confirmed https://github.com/Chu-Junjie/SG-Navi exists under `Chu-Junjie`, who has admin access. The owner explicitly chose to keep it **Public**, overriding the shared guide's private-repository requirement. Public visitors can read and clone; only the owner and accepted write collaborators should push branches. Do not describe this repository as private.

The repository was initially empty. Bootstrap `main` with a README only, then submit the remaining administration files through `docs/task1-repository-setup` and an independently reviewed PR.

## 2 Invite exactly the two teammates

1. Open repository **Settings → Collaborators → Add people** (wording may vary).
2. Find and check the profile `Guanyu-Lu`, then invite that account. Profile supplied by the owner: https://github.com/Guanyu-Lu.
3. Find and check `ZhengZaikun`, then invite that account. Profile supplied by the owner: https://github.com/ZhengZaikun.
4. Ask both members to accept. Recheck that the owner and exactly those two accepted collaborators have access. Pending invitations do not count as accepted access.
5. Record accepted access and successful clone evidence for each member. Do not invite unrelated accounts. The owner has approved public read access; collaborator write access still requires acceptance.

For a private personal repository, collaborators receive write access; the owner retains administration. See [GitHub permission levels](https://docs.github.com/en/repositories/managing-your-repositorys-settings-and-features/repository-access-and-collaboration/permission-levels-for-a-personal-account-repository) and [collaborator invitations](https://docs.github.com/en/repositories/managing-your-repositorys-settings-and-features/repository-access-and-collaboration/inviting-collaborators-to-a-personal-repository).

## 3 Upload the administration files through a PR

Browser route, requiring no additional local tools:

1. On the repository, use the branch selector to create `docs/task1-repository-setup` from `main`.
2. Switch to that branch. Choose **Add file → Upload files**. Upload `AGENTS.md`, `README.md`, `.gitignore`, `.github/` and `docs/` from this package, preserving paths. Hidden folders may need to be selected explicitly; check the resulting file list before committing.
3. If upload cannot preserve a hidden path, use **Add file → Create new file**, enter its exact path (such as `.github/pull_request_template.md`) and paste the file contents.
4. Commit to the feature branch. Open a PR targeting `main`; request `Guanyu-Lu` or `ZhengZaikun` as reviewer after their invitation is accepted. Include actual validation results.
5. Resolve feedback and obtain another developer's approval, then merge. Do not claim approval before the reviewer actually submits it.

Alternatively clone the newly created repository into a separate empty directory, copy these files into it, create the same feature branch, explicitly stage only these files, commit, push the branch and open the PR. Do not run `git init` over an existing checkout or upload credentials.

## 4 Create the seven Issues

After merging the templates, go to **Issues → New issue**. Select each Task template once and submit it, preserving its checklist. An Issue template alone does not create an Issue.

| Template | Issue title | Suggested assignees |
| --- | --- | --- |
| `01-task1.md` | Task 1 — Repository and runtime setup | All three members |
| `02-task2.md` | Task 2 — Shared input and output contracts | All three members |
| `03-task3.md` | Task 3 — Verified knowledge base and rule mapping | All three members |
| `04-task4.md` | Task 4 — Independent module implementation | All three members |
| `05-task5.md` | Task 5 — Integrate backend, RAG and frontend | All three members |
| `06-task6.md` | Task 6 — Execute tests and fix defects | All three members |
| `07-task7.md` | Task 7 — Candidate freeze and handover | All three members |

Assign members only after access is accepted. Record the actual seven Issue links. Tasks 2–7 remain in Backlog until the previous Task's gate passes; creating planning Issues is part of Task 1.

## 5 Create a private task board

1. Create a GitHub Project named `SG Navi Team Board` under `Chu-Junjie`; choose a Board view and set project visibility to **Private**.
2. Give only `Guanyu-Lu` and `ZhengZaikun` project write access. Repository access and Project access must both be checked.
3. Link the Project to the repository and add the seven existing Issues.
4. Configure Status values: `Backlog`, `Ready`, `In Progress`, `In Review`, `Done`.
5. Move Task 1 to `In Progress` and keep Tasks 2–7 in `Backlog`. Move a Task to `Done` only when its acceptance evidence is complete.
6. Record the actual Project URL in the checklist.

## 6 Configure review and merge rules

For `main`, open **Settings → Branches → Add branch protection rule**, or an equivalent active branch ruleset targeting `main`:

- Require a pull request before merging and at least **1 approval** from another developer.
- Dismiss stale approvals when new commits are pushed.
- Require review conversation resolution.
- Apply enforcement to administrators / do not permit bypass, where available.
- Disable force pushes and deletion of `main`.
- After Zheng Zaikun's CI has run successfully once, require its actual pytest check name and require branches to be up to date. Do not select an invented check name or require a nonexistent workflow during bootstrap.
- In general repository settings, enable squash merging and automatic deletion of merged feature branches. Use the same PR workflow for everyone.

GitHub supports branch protection for public repositories on GitHub Free. Configure and verify enforcement in the repository settings; this package cannot save those settings through its current connector. Record protection as pending until it is actually saved. If the repository later becomes private, recheck plan support: protected private branches require a supported paid plan. Do not purchase or upgrade a plan without the owner's decision.

Source: [GitHub protected branches](https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/managing-protected-branches).

## 7 Perform the real review round and runtime gate

1. Zheng Zaikun opens his Task 1 backend/CI PR; another member reviews it.
2. Lu Guanyu opens his Task 1 homepage PR; another member reviews it.
3. Chu Junjie opens the administration PR; another member reviews it.
4. After reviewed PRs merge, all three members clone or pull and follow the actual startup/test instructions supplied by the module owners.
5. Record `/api/health`, homepage health status, pytest, CI, accepted access and human review evidence in the Task 1 checklist. Advance to Task 2 only when all required gates have real evidence.
