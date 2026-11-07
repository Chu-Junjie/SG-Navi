# Task 22 acceptance preparation

[Task 22 #94](https://github.com/Chu-Junjie/SG-Navi/issues/94) records final integration, usability and release acceptance for the action-first iteration. This preparation freezes the tests and records the legacy baseline. The new release gate remains pending the actual service and result UI handoffs.

## Frozen case set and scoring

The versioned [synthetic inputs and expected outcomes](../tests/integration/task22_cases.json) include 15 rental, 15 consumer and 10 boundary cases. The [LF-normalized SHA-256](../tests/integration/task22_cases.sha256) was fixed before the baseline. These cases are separate from the Task 16 wire examples and Task 17 demonstration traces. Keep the first execution of the new service, each actual response digest, all defect IDs and the frozen expectations. Treat later executions of the same data as regressions. If a material fixture error is found, preserve the original result and version the correction explicitly.

1. **Interpretation.** Record the proposed case type, issue subtype and user goal separately. Unknown or ambiguous topics should allow correction. Only confirm the predetermined synthetic facts. A displayed confirmation cannot supply facts the user never gave.
2. **Immediate action.** Compare the final state, action kind and contact ID to each expectation. An `ASK` result must ask the specified decisive fact. A precondition-sensitive route stays limited if confirmation is missing. Record the count and reason for each question. An `ASK` with a useful scoped preparation plan is accepted only where the expected state and action permit it. A generic referral is a failed tailored answer.
3. **Evidence.** For each action and checklist item, verify its evidence link and current snapshot. For contacts check institution, purpose and exact destination. Compare quote bytes and digests, legal provision, source kind and relevant context. Include visible assessment, conditions, warnings and draft assertions in the review. Record claim ID, evidence ID and actual support determination. Any invented consequential claim or exposed personal data is critical.
4. **Checklist.** Match the independently required concepts for each core case to the visible or directly accessible checklist. Equivalent wording is acceptable. Record every missing concept and its defect ID. A missing core result scores zero for completeness. Average within each case type.
5. **Boundaries.** Match scope/reason, question necessity and safe absence of inapplicable actions. Source quarantine and service unavailability use the specified isolated fixtures. These are genuine controlled failure tests. They cannot stand in for actual public browser execution.
6. **Release gates.** Require at least 14/15 routing in each core case type, 10/10 boundaries and at least 38/40 overall. Require 95% support overall, 100% for consequential legal and contact claims and at least 90% mandatory checklist completeness in each core group. Require zero critical defects. Report goal/subtype and first-action/contact correctness separately, with per-case errors. An unmet action or contact gate stays visible even if case classification meets its threshold.

## Actual browser and human measurement

Follow [Task 16](task16-action-first-design.md). Execute both complete synthetic journeys against the published page and verified deployed API. On 1366×768 and 1440×900 capture the initial input, one active question and result. Verify no outer scrolling to see the primary action. Record that the official route and its exact source can each be reached in one click. Check 320/390-pixel layouts, 200% zoom, keyboard focus/return, edit/back, request cancellation, stale data, offline and timeout recovery. Verify actual request origin, API version, deployment commit, correct CORS preflight, source hashes and absence of user data in URLs/storage. Preserve real screenshot and network evidence.

For each real walkthrough record an anonymised participant identifier and role, fixture ID, device/viewport, actual first-view time, time to name both the responsible party and next action, clicks, extra questions, errors and verbatim feedback with permission. The target is five seconds from first result exposure to correct identification. A reviewer may inspect a case on both desktop and mobile, but describe the participant pool honestly. No recorded human timings means **NOT RUN** for comprehension. Scripted keyboard or screenshot checks measure interaction only.

## Current status and commands

The standalone design and evidence delivery are tracked in #88 and #89. The live homepage shell was delivered under #92. Interpretation #90, the action-plan response API #91 and the actual result integration #93 are open at this checkpoint. The public synthetic request and local route inventory are recorded separately. New action and public acceptance measurements remain **NOT RUN** until these handoffs are available. Technical, usability and legal/production dispositions are separate.

With the existing dependencies installed from `tests/contracts/requirements.txt`:

```powershell
python -X utf8 -m integration.task22_baseline --output instance/task22-baseline.json
python -X utf8 -m pytest tests/integration/test_task22_frozen_cases.py -q
python -m flask --app integration.app run --host 127.0.0.1 --port 5000
```

The executed baseline used real local Flask requests to the legacy intake endpoint. It checked the frozen digest before sending 40 synthetic cases and saved an exclusive output file. The legacy intake proposed the expected core case for **12/15 rental** and **2/15 consumer** descriptions. The boundary cases have observations only. The proposed action-plan route returned HTTP 404 locally and in the synthetic public probe. These are [baseline and readiness records](test-results/task22-readiness.json). The focused frozen-fixture test returned **1 passed in 2.17 seconds**. The frozen case set will be used for actual action, route, checklist and citation measurement after integration.
