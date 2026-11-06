# Task 11 — bounded English problem intake API (contract proposal)

**Owner:** ZhengZaikun · **Issue:** [#71](https://github.com/Chu-Junjie/SG-Navi/issues/71) · **Reviewers:** Chu-Junjie (shared contract/citations) and Guanyu-Lu (frontend).

**Scope:** Additional Flask endpoints only. This is an English, rule-bounded *interpretation proposal*, not an LLM service, real legal eligibility check or filing endpoint. `/api/navigate` 1.0 and the current public Pages→Render release remain unchanged until a separately reviewed deployment.

## Proposed contract version 1.0 (not yet promoted to shared/)

The independently versioned source is [backend/intake_contract.json](../backend/intake_contract.json). The shared-contract owner must approve an additive shared representation before frontend production wiring. The frontend currently uses a separate presentation-only shape `{status,category,candidateFacts}` in `frontend/js/task8-home.js`. Guanyu will need to map the accepted fields **without** presenting unconfirmed facts as verified.

### 1. Propose a supported case: `POST /api/intake`

JSON request:

```json
{"intake_version":"1.0","description":"My landlord refuses to return my S$2,000 deposit."}
```

Expected shape from the deterministic implementation (no raw text returned):

```json
{
  "intake_version": "1.0",
  "intake_status": "suggested",
  "suggested_case_type": "rental_deposit",
  "candidate_facts": {"claim_amount_sgd": 2000.0, "dispute_with": "landlord"},
  "needs_confirmation": true,
  "clarification_questions": [],
  "limitations": ["This is an unconfirmed English-language interpretation, not a legal eligibility or filing decision."]
}
```

A consumer example `"I bought a faulty phone for S$200 and want a refund."` proposes `consumer_complaint`, `claim_amount_sgd: 200` and `purchase_type: goods`. It **does not** assume the seller is registered in Singapore, the purchase is personal, or that the person qualifies for SCT/CASE.

Classification vocabulary: `suggested`, `ambiguous`, `out_of_scope`, `cannot_determine`, `confirmed`, `error`. Only the `suggested` status carries a recommended category. Wrong topic, unsupported legal fields and competing case cues do not force either supported route.

The text validator accepts 1–1200 trimmed characters and English MVP text, validates JSON object, forbids unexpected payload keys, bounds the request at 8192 bytes, and never emits or stores the description. Extracted monetary values require an **explicit S$ or SGD marker**; multiple possible monetary amounts yield no single `claim_amount_sgd`. Values like `$500` or `US$500` are not assumed SGD. Only confirmed explicit phrases produce other facts; unknown residency, registration, legal deadlines and official thresholds cannot be inferred.

### 2. Confirm/edit facts: `POST /api/intake/confirm`

**Required** `confirmed: true`. The user explicitly chooses a case and independently checks/corrects any candidate facts. Do not automatically send an unconfirmed candidate as confirmed.

```json
{
  "intake_version": "1.0",
  "confirmed": true,
  "case_type": "rental_deposit",
  "confirmed_answers": {"dispute_with": "landlord", "claim_amount_sgd": 2000}
}
```

The response has `intake_status: confirmed`, `needs_confirmation: false`, `suggested_case_type: rental_deposit`, the exact confirmed `candidate_facts`, `clarification_questions` containing only **missing fields required by the current backend** (e.g. `premises_type`), and an `unresolved_fields` list for explicitly supplied `null` or `"unknown"` fields. Unlike missing fields, explicitly Unknown/Not provided is *not* blindly asked in an infinite loop; the frontend can display unresolved facts and request correction if the user chooses. `false` is preserved as false, not treated as unknown.

The `revision` is a deterministic SHA256-derived digest of the confirmed category and **structured** answers, recomputed on edits. It is a UI stale-result marker, **not a secure signature or evidence/reference identifier**. No raw dispute description is stored. Unconfirmed interpretation does not enable an Action Card or legal path.

### 3. HTTP safety, content and scope

| Condition | Actual designed behavior |
| --- | --- |
| Valid bounded English intake / confirmed facts | HTTP 200, schema-validated deterministic response |
| Ambiguous or unsupported case | HTTP 200, no forced case or extracted facts |
| Invalid version/type/schema/oversized data | HTTP 400 or 413 (415 wrong Content-Type), error response with no input echo |
| Dependency unavailable | HTTP 503 generic error, no user description in output |
| Browser preflight | Allowed `https://chu-junjie.github.io` POST/Content-Type OPTIONS 204; unapproved origin OPTIONS 403 |
| No model provider | Deterministic parser; no API keys, LLM calls or external text transmission |
| Current legal criteria | All 25 backend checks / 26 RAG mappings remain disabled; `/api/navigate` remains conservative and `action_card: null` |
| Personal data | Use synthetic data only. This is not hardened for collection of real dispute details or production data retention. |

CORS controls browser access, **not authentication**. There is no per-user database record or raw text audit log. The next release must add explicit privacy/abuse and security reviews before handling real user problems.

## Local reproducibility

```powershell
python -m pip install -r tests/contracts/requirements.txt
python -m pytest tests/backend/test_task11_intake.py -v
python -m shared.validate_contracts
python -m flask --app backend.app run --host 127.0.0.1 --port 5000
```

Then use an HTTP client such as `Invoke-RestMethod` from a second terminal:

```powershell
$body = @{intake_version="1.0"; description="My landlord has not returned my S\$2,000 deposit."} | ConvertTo-Json
Invoke-RestMethod "http://127.0.0.1:5000/api/intake" -Method Post -ContentType "application/json" -Body $body
```

These are reproduction commands, not claims that personal Windows execution occurred. The team's GitHub Actions is the source for exact CI pass/fail and commit.

## Known functional limitations and team handoff

1. A bounded regex parser cannot safely interpret every natural-language phrasing; ambiguous, unsupported, multilingual or unrecognized requests are expected to need confirmation or fallback. No hallucinated category/amount is permitted.
2. The first endpoint deliberately does **not** ask case-specific questions until the user confirms the case/facts in the second endpoint.
3. Candidate fact extraction only covers explicit amounts, landlord/agent, residential/commercial premises, purchased goods/services, personal/business purpose and an explicit supplier registration statement. It does not determine legal significance.
4. The clarification fields derive from `backend.rules.engine.QUESTION_FIELDS` and case-specific input validation, not hard-coded frontend assumptions.
5. **Task 8/9 frontend wiring is not part of this backend PR**. Guanyu owns changing the UI `runIntakeRequest()` adaptor / confirmation flow. Junjie owns the final shared-contract promotion. The deployed Render SHA does **not** automatically change when the feature PR is created.
6. Task 12 evidence-linked guidance and Tasks 13/14 passage retrieval/excerpts are separate, not implemented here. Task 15 real browser/new API integration remains future acceptance.

**Acceptance note:** link the *actual* GitHub CI run and reviewed merge commit on Issue #71 after tests finish. PR creation does not establish peer approval, deployment or full product acceptance.
