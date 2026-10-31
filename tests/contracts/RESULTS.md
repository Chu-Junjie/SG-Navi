# Task 2 contract validation results

Executed on 2026-10-31 in the local Windows workspace, based on `main` commit `743f609cdfc0bdfac4e3c7bd9ed839f65615d9bb` (Task 1 backend PR #10 merged).

Environment: Python 3.14.6, pytest 9.1.1, jsonschema 4.26.0, referencing 0.37.0. These are local results, not GitHub Actions results or another member's environment.

| Command | Actual result |
| --- | --- |
| `python -m shared.validate_contracts` | All 11 shared Mock JSON examples passed |
| `python -m pytest tests/contracts tests/backend frontend/tests -q` | 109 passed in 5.33 seconds: 103 contract tests and 6 existing backend/homepage tests |
| `git diff --check` | No errors reported |

The first test run found a URL ending in a newline was accepted. The Evidence Schema now explicitly rejects URL whitespace. The newline regression and the other tests above passed after this fix.

Covered: all four navigation statuses, fixed envelope fields and versions, both case types, absent/null/unknown/false facts, six required Evidence fields, malformed URLs, unreviewed/quarantined Evidence rejection for cards, seven Action Card section names, real Task 1 health output, shared RAG metadata validation, offline schema resolution and CLI success/failure behavior.

Not verified: detailed case input schemas and Action Card section contents owned by the frontend developer; Task 2 endpoint stubs owned by the backend developer; actual official source reviews, rules, citations or legal outcomes; contract checks in CI; all three developers' agreement and environment runs. Task 1 acceptance is not asserted by this record.
