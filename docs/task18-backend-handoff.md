# Task 18 — backend scenario and goal understanding

Issue #90: https://github.com/Chu-Junjie/SG-Navi/issues/90

Ownership: ZhengZaikun backend and backend tests. Task 16 schema and Task 17 source evidence were merged first. No changes to Junjie's rag/shared files or Guanyu's frontend.

## Backend functions

- backend.scenario_understanding.interpret_scenario(description) returns an *unconfirmed* candidate context (case_type, issue_subtype, goal, explicitly written typed facts, short summary). Unsupported/ambiguous inputs never force a legal route.
- backend.scenario_understanding.next_decisive_question(context) returns at most one question with human-friendly labels, an explanation, and a Not sure option. It skips already supplied values, null and unknown. Consumer business-purpose/locality and rental party/exit/contract distinctions are handled conservatively.
- backend.scenario_understanding.context_revision(context) computes a deterministic 24-hex digest of case, subtype, goal and facts, independent of summary wording. Edited answers invalidate downstream guidance while unrelated facts are retained.
- Validates against shared/action_plan_contract.json from Task 16. No external model, user text persistence, legal outcome decision or new public endpoint.

## Covered scenario categories

Restaurant overcharge and duplicate charges; merchant denial and uncertain charge; personal consumer goods/services; landlord deposit return/deduction; early tenancy exit and associated work-pass event; estate-agent conduct vs agency agreement. A work pass event alone never proves refund/forfeiture. Government/employer security bond is not presumed to be a private rental security deposit. Standalone immigration and unrelated mixed topics are not forced into one case.

Exact amounts use integer SGD cents and are only extracted when precisely one valid explicitly labelled amount is present. Unknown, null, false and absent remain separate. Confirmation is mandatory.

## Suggested Task 19 integration

- For an interpretation request, return a Task 16 CONFIRM candidate; only call next_decisive_question after explicit user confirmation and source-controlled Task 19 validation. Follow the frozen request_id, revision and response shape.
- Task 19 must own all READY results, real current contact data, source-backed priority actions and user-facing draft templates. Task 18 does not return a source-supported action itself.
- Guanyu can use the one-question modal with the Task 16 question fields; never render a fixed number of steps or re-ask facts already provided.
- Only Task 19 should bind the RAG-source action plan to this interpretation; both legacy Task 11 and older action preview endpoints remain unchanged.

## Run regression checks

    python -m pytest tests/backend/test_task18_understanding.py -q
    python -m pytest tests/contracts tests/backend tests/rag tests/integration -q
    python -m shared.validate_contracts

Record actual GitHub Actions results on the final PR head. These are deterministic synthetic regressions and do not establish deployment, legal suitability or Task 22 held-out success.
