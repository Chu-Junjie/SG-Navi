# Task 2 contract and mock baseline acceptance

Status: **Done for the contract and API-stub stage**, accepted for closeout by the owner on 2026-11-01. The three members' code is merged and the shared contract checks pass against frontend mocks and backend responses. Task 3 may start. This does not assert complete forms, legal decisions or real RAG.

Audited main commit: `0840522121be8f5ef31e1a45cba62768adbc4a03`.

| Deliverable | Evidence |
| --- | --- |
| Canonical API 1.0 contract, Evidence Schema, validator and contract tests | [PR #11](https://github.com/Chu-Junjie/SG-Navi/pull/11), merged |
| Two input schemas, seven-section Action Card schema and four-state mock preview | [PR #13](https://github.com/Chu-Junjie/SG-Navi/pull/13), merged |
| CI installs validator dependencies and runs contract checks | [PR #14](https://github.com/Chu-Junjie/SG-Navi/pull/14), merged |
| Four Flask endpoints, input validation and contract-valid placeholders | [PR #15](https://github.com/Chu-Junjie/SG-Navi/pull/15), merged |

## Actual validation

Executed on 2026-11-01 in the owner's local Windows workspace, Python 3.14.6 and pytest 9.1.1.

- `python -m shared.validate_contracts`: all 11 examples passed.
- `python -m pytest tests/contracts tests/backend frontend/tests -q`: **125 passed in 5.28 seconds**.
- Flask test-client requests to GET /api/health, GET /api/case-types and GET /api/version returned 200 and matched the shared contract.
- POST /api/navigate for both case types returned NEED_CLARIFICATION for a missing amount and REFER_TO_OFFICIAL for the supplied synthetic amount. Invalid API version returned HTTP 400 with contract-valid ERROR.
- [Backend Task 2 CI run 41290133115](https://github.com/Chu-Junjie/SG-Navi/actions/runs/41290133115) succeeded. The workflow now runs shared, backend and frontend checks.

Mock data exercises all four navigation statuses, including SUPPORTED_PATH. The API stub intentionally does not declare a supported legal path using synthetic evidence. Answers, Action Card section types and backend outputs share the agreed field names without introducing legal rules.

## Limits retained

The interface agreement here is evidenced by merged code and cross-module tests, not a fabricated record of three separate written sign-offs. The audit did not independently verify each member's machine or run the mock preview in a browser. Those facts are not claimed as passed. Detailed source verification, rule configuration and UI mapping belong to Task 3.
