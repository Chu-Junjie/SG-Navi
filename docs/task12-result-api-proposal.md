# Task 12 — provisional evidence-linked research result API

Issue: #72. **Contract proposal only; Junjie and Guanyu must review before this is treated as an agreed frontend contract.** Task 13 query ranking and Task 14's final enriched citation schema remain separate dependencies.

## Safety and ownership
- New `POST /api/results/preview` is additive; `/api/navigate` API 1.0, its `rule_version: mock-1`, its four status values, and legally null `action_card` are unchanged.
- `guidance_status: GUIDANCE_ONLY` means checked, conditional, *information-only research guidance*, **never SUPPORTED_PATH or eligibility**.
- `LIMITED_REFERRAL` returns null `research_guidance`, no display evidence and a clear explanation. The legal rule flags remain disabled.
- Content is copied from the RAG owner's currently reviewed `action_templates.json`, with item-level evidence IDs; no AI rewrites or invented fees, filing deadlines or legal rules. Direct quotes come from `passages.jsonl.text`, editorial summaries are separate fields.
- Unknown fields remain unresolved. Agent/agency agreement paths are distinct from landlord paths; no automatic referral to a CEA conduct complaint as a contractual dispute. Business and overseas consumer situations are out of project scope.
- Evidence is rechecked per request via repository snapshots, operational quarantine, reviewed sources, exact current excerpt digest and source-review match. A template is withheld in full if any cited passage fails.
- Source review reflects the recorded snapshot, **not live real-time confirmation**. No real user data is stored or transmitted to a model.

## Request
```json
{
  "results_version": "0.1",
  "confirmed": true,
  "case_type": "rental_deposit",
  "confirmed_answers": {
    "dispute_with": "landlord",
    "premises_type": "residential",
    "claim_amount_sgd": 2000
  }
}
```

`case_type`: `rental_deposit` or `consumer_complaint`. `confirmed_answers` follows the current case-specific frontend input schema. HTTP 400: malformed/unconfirmed/version-incompatible; 413: oversized; 415: non-JSON; 503: source unavailable. No raw descriptions accepted.

## Response (illustrative structure, not a claim of a real test)
```json
{
  "results_version": "0.1",
  "result_id": "<deterministic revision digest>",
  "source_version": "<current checked corpus version>",
  "guidance_status": "GUIDANCE_ONLY",
  "research_guidance": {
    "case_summary": "User-confirmed rental deposit scenario; facts have not been independently verified.",
    "potential_channels": [{"text": "<approved conditional template channel>", "evidence_ids": ["<evidence-id>"]}],
    "conditions": [{"text": "<approved condition>", "evidence_ids": ["<evidence-id>"]}],
    "steps": [{"text": "<approved step>", "evidence_ids": ["<evidence-id>"]}],
    "document_checklist": [{"text": "<approved preparation item>", "evidence_ids": ["<evidence-id>"]}],
    "unresolved_questions": [{"field": "<field>", "text": "Confirm <field>."}],
    "citations": ["<evidence-id>"]
  },
  "display_evidence": [{
    "evidence_id": "<evidence-id>", "source_id": "<source-id>",
    "rule_ids": ["<rule-id>"], "url": "https://<official-website>",
    "review_status": "verified", "source_version": "<version>",
    "publisher": "<reviewed publisher>", "title": "<reviewed page title>",
    "verbatim_excerpt": "<exact reviewed excerpt>",
    "source_locator": "<recorded text locator>", "reviewed_at": "<recorded review time>",
    "summary": "<SG Navi editorial summary, not official quotation>",
    "excerpt_sha256": "<reviewed digest>"
  }],
  "unresolved_fields": ["<missing-field>"],
  "limitations": ["This is research and preparation information, not an eligibility, filing, deadline or legal entitlement decision. Check official services."]
}
```

A change to confirmed answers, source version or quarantined source set alters the result ID. Clients should discard the old result as soon as confirmed facts are edited and only display the latest matching result ID.

## Local verification commands
```bash
python -m pytest tests/backend/test_task12.py -q
python -m pytest tests/contracts tests/backend tests/rag tests/integration -q
python -m flask --app backend.app run
```

## Coordination required to release
1. Junjie: approve versioned response schema, decide how Task 14's final display-evidence projection should be consumed, and review quarantine/revision policy.
2. Guanyu: approve field names and result UI consumption; do not interpret GUIDANCE_ONLY as a legal Action Card.
3. Junjie/Task 13: replace broad fixed topic lookup with case-question-relevant selection. Current Task 12 conservatively selects predefined approved templates only.
4. Obtain human PR review and passing CI; do not merge this proposal without the coordinated contract decision.
