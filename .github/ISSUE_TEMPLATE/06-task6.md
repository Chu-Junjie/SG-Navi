---
name: Task 6 - Tests and fixes
about: Execute reproducible tests and retest actual fixes
title: 'Task 6 — Execute tests and fix defects'
---

Prerequisite: Task 5 accepted.

## Responsibilities

- @Guanyu-Lu: FE-01–08, including unknown, editing, errors, citations, mobile width and keyboard.
- @ZhengZaikun: BE-01–10 and execute E2E-01–08.
- @Chu-Junjie: RAG-01–12, including landlord/agent separation, invalid citations, unreviewed/quarantined sources, conflicts, index rebuild and shared sources; coordinate bugs.

## Required E2E scenarios

1. Rental input → clarification → routing → official evidence → Action Card.
2. Consumer completes the same full flow.
3. Missing amount triggers a question rather than a guessed number.
4. Unclear landlord/agent triggers clarification.
5. Business-purpose consumption handled within project scope.
6. Non-Singapore supplier handled within project scope.
7. Invalid/conflicting evidence produces no invented citation or certain conclusion.
8. Backend/RAG failure shows a safe message or verified static fallback.

## Acceptance

- [ ] All three owners supply actual test output.
- [ ] All eight E2E scenarios have actual records; failures fixed and retested or explicitly limited.
- [ ] No open P0 defect involving fabricated evidence, sensitive data leakage or broken core flows.

Record: Test ID | Input | Expected | Actual | Pass/Fail/Not Run | Commit | Tester | Executed At | Bug Issue.
