# Task 19 — Action-first backend API and verified Task 17 contacts

Issue: https://github.com/Chu-Junjie/SG-Navi/issues/91

## Implemented (Zheng-owned backend)

- POST /api/action-plan supports the approved Task 16 request/response contract version 1.0. No replacement of /api/navigate, /api/intake, /api/guidance or /api/results/preview.
- interpret accepts only bounded English input; returns CONFIRM with Task 18 unconfirmed case/subtype/goal/facts, or LIMITED for ambiguous/outside/insufficient cases. No action or verified claim appears before confirmation.
- plan accepts confirmed typed context; returns one route-changing ASK question, READY with a real reviewed Task 17 profile, or LIMITED for scope, unmatched profile or stale/quarantined evidence. Validated requests with unexpected transient failure return UNAVAILABLE 503. Invalid JSON/content type/length/schema return safe HTTP 400/413/415 without echoing the user's description.
- READY uses rag.action_evidence.select_action_plan and Task 17's exact reviewed action package and repository guards. It provides assessment, prioritized primary action, short ordered checklist, approved web/phone/email contacts, evidence-linked conditions/pitfalls, editable slot-based draft, and only the existing exact reviewed statutory text when it supports a selected claim. No new citations, official text, phone numbers, case outcomes, filing rules or contact endpoints are invented by backend logic.
- Task 18 questions are single modal-ready question objects with labels, reasons, Not sure and schema-valid typed options. A supplied unknown/null/false stays distinct from a missing key; a local basic preparation step remains possible while full formal-claim facts are unknown.
- The official package itself has reviewed source dates, digests, quarantine guards and current repository version checks. Selection returns a plan only after a second source-state read. The response includes the confirmed context and a 24-hex revision so Task 21 can discard stale responses after edits. No storage, external model, raw text logging or automatic sending.
- Work-pass cancellation/expiry is treated as factual tenancy context. The action uses the *signed* tenancy clauses and reported notice as preparation, not a conclusion that the deposit is automatically returned or forfeited. Landlord and estate-agent complaint channels remain separate.

## Request examples

Interpret:
```json
{"action_plan_version":"1.0","request_id":"example-restaurant-001","operation":"interpret","description":"The restaurant charged me SGD 20 extra and refuses to refund it."}
```

After explicit user confirmation, plan:
```json
{
  "action_plan_version":"1.0",
  "request_id":"example-restaurant-002",
  "operation":"plan",
  "confirmed":true,
  "context":{
    "case_type":"consumer_complaint",
    "issue_subtype":"restaurant_overcharge",
    "goal":"complain",
    "facts":{
      "merchant_location":"singapore",
      "purchase_purpose":"personal",
      "consumer_context":"local_consumer",
      "resolution_attempted":true,
      "disputed_amount_cents":2000
    },
    "summary":"You reported a disputed charge in a Singapore restaurant."
  }
}
```

Task 17's registered consumer contact profile supplies the genuine CASE form, telephone and published email (each with its source, purpose and availability), only when the source is currently valid. Other contexts can receive an approved preparation action with no invented complaint portal.

## Frontend handoff to @Guanyu-Lu

Use only the Task 16 Action Plan 1.0 fields. On CONFIRM, allow editing/correction. On ASK, show *one* question and Not sure within the reusable modal. On READY, show headline, primary_action.label and corresponding approved contact first, then checklist, with optional source drawer/claim text, draft and pitfalls. If primary_action.kind=prepare, the action is informational and has null contact_id; do not fabricate an external button. Show official quote with provision and exact recorded publisher/edition; a contract template is not a statute. Check request_id and revision against current in-tab context, discard stale result/draft on edits. On LIMITED/UNAVAILABLE do not show stale buttons or unsupported success badges. Never automatically submit complaints.

## Source and owner handoff to @Chu-Junjie

This PR does not edit rag/, shared/ or frontend/. Please review the source profile ordering, consumer location/context conditions, legal-claim display limitations, Task 16 protocol alignment, and operational source freshness/quarantine behavior. Source audit notes and direct SSO/HDB access limitations remain in rag/TASK17.md; this API does not claim that direct SSO access succeeded.

## Verification

```bash
python -m pytest tests/backend/test_task19_action_plan.py -q
python -m pytest tests/contracts tests/backend tests/rag tests/integration -q
python -m shared.validate_contracts
```

Only GitHub Actions logs for the tested final commit establish actual outcomes. Public Pages-to-Render action-plan routing and Task 21 browser acceptance are separate release gates; a passing local/CI Flask test does not prove deployment.
