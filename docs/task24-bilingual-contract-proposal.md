# Task 24 — zh-Hans reviewed bilingual Action Plan proposal (pending review)

Owner: @ZhengZaikun. Contract and legal-language reviewer: @Chu-Junjie. Frontend consumer: @Guanyu-Lu. Issue: #111. This PR stages a **review proposal**; it does NOT make Chinese legal translations official, change existing production API responses or complete the release gate.

## Current baseline and inventory
- `POST /api/action-plan` has the unchanged Task 16 Action Plan 1.0 schema (`additionalProperties: false`) and English-only display content. Do not add unvalidated `message_zh` fields to the canonical response; doing so will break current clients.
- Task 17's `rag/action_evidence/package.json` presently contains 13 reviewed English profiles, 80 distinct user-visible plan strings, editable draft labels and placeholders; Task 18 adds subtype/goal summary components and adaptive one-question labels. Task 19 adds the response-state messages and additional question formats. The candidate catalog holds 155 entries including institution names, purposes and contact notes.
- The source package remains `action-kb-2026-11-07.1`. No `rag/`, `shared/`, live `frontend/`, official URLs, source IDs or quote records were modified.
- Entries are English-keyed and `review_status=pending_review`; metadata has `approved_by=null`, `approved_at=null`. **No legal/source translation approval has been received.** Chinese wording is a working draft only.

## Proposed protocol, not an approved API contract
- `backend/task24_bilingual.py::preview_zh_hans(canonical)` returns a *separate* versioned sidecar containing `locale: zh-Hans`, unchanged `canonical`, and a machine-validated `display` overlay keyed by the same claim IDs, question IDs, option values, contact IDs and exact evidence ID arrays.
- New schema `backend/locales/task24_bilingual_overlay_proposal.schema.json` validates the proposed sidecar independently. Canonical English must first pass `shared.validate_action_plan`. It is deep-copied and NEVER translated in place.
- The Chinese overlay contains message, structured subtype/goal summary, ASK prompts/reasons/options, READY headline, assessment, primary action, checklist and details, contact descriptions, and optional editable draft/slot labels.
- **Official English quotations and procedural text are not translated or duplicated in the overlay.** Canonical `plan.evidence`, `legal_basis`, contact URLs/tel/email values, source digests, reviewed dates, action-plan revision and original request ID remain byte-for-byte unchanged.
- The overlay's `translation_status` is `pending_review`, never `approved`. If any required text mapping is absent (including a user-modified/unreviewed summary) or a draft placeholder was changed, `display=null` and `translation_status=missing_translation` with a single Chinese fallback notice. The English original remains in `canonical`; do not present a partial English/Chinese legal statement as a completed Chinese route.
- Chinese intake text itself is **not** supported by Task 18's English-only interpreter. Display-language switching does not alter case understanding; Chinese-language free text needs a separate approved parser with privacy, source and regression validation.

### Illustrative projection usage (not deployed)
```python
from backend.action_plan_service import process_action_plan
from backend.task24_bilingual import preview_zh_hans

canonical = process_action_plan(english_task16_request)
proposal = preview_zh_hans(canonical)
# Verify canonical == proposal["canonical"].
# Do NOT ship/display proposal["display"] as reviewed/official yet.
```

Example human-facing Chinese only for research review:
- `CONFIRM` message: 请确认以下理解是否正确，或先更正有关信息。
- `ASK` prompt: 这笔购买用于个人用途还是商业用途？
- `READY` restaurant primary step: 在官方投诉表格中说明争议金额，以及您此前尝试与商家解决问题的经过。
- Rental/pass pitfall: 如涉及 Employment Pass（就业准证），请查阅新加坡人力部（MOM）的准证取消指引；押金问题仍须分别核对已签署的租约。
- Label must remain visible: **中文说明（非官方译文）；法律与程序依据以官方英文原文为准。**

## Human review gate — required before any production connection
1. **Junjie:** approve/revise the exact bilingual representation/versioning strategy and source-sensitive 155 phrase translations. Provide real review identity, timestamp, source-package/version mapping, stable phrase/claim IDs and a correction log. Do not modify source quote bytes or treat Chinese paraphrase as an official legal provision.
2. **Guanyu:** approve the field shape and UX for client language switch without fresh interpretation, clearing answers, losing checklist ticks, losing IDs or suppressing original English evidence. Display the non-official-explanation label near derived Chinese content. Confirm the intended authorization and a deployment/migration plan.
3. **Zheng:** after both reviews, implement the agreed opt-in transport and strict shared schema/version migration, add approved-only gating, and run actual HTTP, source-failure/quarantine and canonical compatibility tests. This branch does **not** expose an HTTP bilingual route or alter the approved Task 16 contract.
4. **All:** publish source-version- and reviewer-stamped translations only after approval. Task 23 #106 bilingual UI and Task 22 #94 public acceptance remain separate. The English legacy `/api/action-plan` should keep working unchanged.

## Verification
```bash
python -m pytest tests/backend/test_task24_bilingual.py -q
python -m pytest tests/contracts tests/backend tests/rag tests/integration -q
python -m shared.validate_contracts
```

The above tests exercise all 13 source profile payloads, 5 response states, several dynamic questions, typed-value identity, original contact/evidence identity, draft placeholder preservation and missing/unreviewed fallback. They are synthetic controlled fixtures and not evidence of official endorsement, live source re-check or public Pages→Render Chinese UI acceptance. Link exact GitHub CI results on the final PR head; do not infer a pass from older green commits.
