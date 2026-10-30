# SG Navi development rules

## Scope and ownership

- Follow the current Task and inspect existing files before editing. Complete each Task's acceptance gate before starting the next.
- Chu Junjie (`Chu-Junjie`): repository administration, `rag/`, source evidence, `shared/` contracts, integration coordination.
- Zheng Zaikun (`ZhengZaikun`): `backend/`, backend tests, dependency setup and CI.
- Lu Guanyu (`Guanyu-Lu`): `frontend/` and frontend tests.
- Change only the requesting developer's assigned modules and related tests. Ask the module owner before cross-module edits.
- Task 1 administration does not authorize implementing either teammate's backend or frontend.

## Product boundaries

- Build only the English Rental Deposit and Consumer Complaint web flows.
- Do not invent legal rules, official passages, eligibility thresholds, review records, citations or test results.
- Treat unknown facts as unknown, never as false. Ask for clarification or refer to official confirmation when evidence is insufficient.
- Keep legal decisions out of frontend JavaScript. Use the shared contract once it is established in Task 2; coordinate contract changes through Chu Junjie.
- PDPC is for privacy design; ReturnLah and LifeSG are background, not eligibility evidence.

## Collaboration

- Use a feature branch, a pull request, another developer's review, then merge. Do not self-approve or push development changes directly to `main`.
- Branch names: `feat/taskN-short-description`, `fix/taskN-short-description`, or `docs/taskN-short-description`.
- Keep PRs within one Task and link their Issue. Request a reviewer other than the author. Resolve requested changes and rerun affected checks before merging.
- Do not claim repository settings, invitations, CI, human review or another member's environment passed without actual evidence.
- The initial empty-repository README bootstrap is the only setup exception; subsequent files go through a PR.

## Data and validation

- Never commit `.env`, credentials, API keys, or real dispute/user data. Use synthetic fixtures. `.env.example` may contain variable names and empty values only.
- Run checks appropriate to the changes. Record exact commands, actual outcomes and checks that were not run.
- At completion, report changed files, installation/start commands that actually exist, test results, and remaining problems. Do not describe planned commands as verified.
