# Task 24 — reviewed locale delivery gate + confirmed-selection UI fix

Issue #111. Backend owner @ZhengZaikun; translation/source reviewer @Chu-Junjie; frontend owner @Guanyu-Lu.

## Scope and actual effect

- No production Chinese dynamic legal content has been approved or activated.
- `backend/task24_delivery.py` accepts the **existing** Task24 static zh-Hans candidate catalog only if a separately committed, source-owner-reviewed approval file exists. The PR deliberately does **not** include that approval file.
- `backend/routes/task24.py` adds an opt-in `POST /api/action-plan/zh-hans-reviewed` route. It is **404 by default** and additionally requires a matching review record even when a developer explicitly enables it. It does not alter the existing `/api/action-plan` response, legal quotes, evidence digests, URLs, typed values, revision ID, state handling or canonical version.
- `frontend/js/task23-locale.js` adds deterministic **non-legal UI selector labels only**, such as Goods Dispute → 商品纠纷, Consumer Complaint → 消费者纠纷, Seek Refund → 请求退款. Unknown source-backed text remains visibly English. The existing `task21-live.js` calls `observeText` for these option nodes, so the known labels are translated without changing each `option.value`.
- `tests/backend/test_task24_reviewed_delivery.py` and updated frontend locale tests protect the default-off state, missing/forged approval, source-package version drift, deep-copy canonical invariants and unknown source text fallback.

## Review gate (MUST be handled by Junjie, not self-approved by backend author)

After reviewing *every* proposed Chinese explanatory string and legally sensitive meaning in `backend/locales/task24_zh_hans_proposal.json`, the source owner must approve this strict metadata file (do not insert without independent human review):

```json
{
  "approval_version": "task24-reviewed-1.0",
  "translation_catalog_version": "task24-proposal-0.1",
  "source_action_package_version": "action-kb-2026-11-07.1",
  "locale": "zh-Hans",
  "approved_by": "Chu-Junjie",
  "review_status": "approved",
  "reviewed_at": "<actual UTC ISO-8601 review time>",
  "entries_sha256": "<SHA-256 of exact catalog entries object, UTF-8, sorted JSON keys, compact separators>"
}
```

Filename: `backend/locales/task24_review_approval.json` (**intentionally absent**). Review must be evidenced by an independent GitHub APPROVED review on the approval commit; a JSON file alone is not cryptographic identity proof. Changing any candidate text or source package version invalidates this metadata. This step is not automatically completed by merging this PR.

## Proposed opt-in transport (do not enable publicly before client approval)

Backend test app may set `TASK24_ENABLE_REVIEWED_LOCALE=True`. Without the review metadata the response is 503 `translation_not_approved`, NOT unchecked Chinese output. With the approved file it returns an envelope with unchanged canonical English Action Plan and separately marked `display` explanation. Official English quote bytes are never translated.

No Pages CORS entry is introduced here: this is a gated backend implementation for review, **not a shipping bilingual client integration**. Guanyu must approve a compatible transport and implement the UI consuming that approved overlay only after version/shape review. Use Task23 to verify mid-journey EN/中文 switching without reinterpreting input, resetting checkboxes or rewriting canonical evidence.

### Why screenshot had English
In `frontend/js/task21-live.js`, `showConfirm()` uses `context.summary` directly. Its `select()` renders `LABEL(value)` (a title-case English formatter). These known **selector labels** can be translated by the locale map now, but the dynamic summary and legal/action content cannot be changed to Chinese before audited backend language fields and frontend mapping are jointly approved. Deliberate English fallback is therefore correct for unreviewed dynamic content.

## Required acceptance before Task24 can close
1. Junjie reviews legally sensitive meaning, institution names, source identity and all 155 phrases, supplies real approval provenance/time and reviewed catalog digest.
2. Junjie and Guanyu approve the response contract and source-to-claim mapping. After that Zheng can approve the transport integration in a separate production PR with schema validation.
3. Guanyu updates `task21-live.js` to consume reviewed display fields instead of formatting labels or rendering unreviewed English summaries in Chinese mode. Task23 covers public UI and language switching.
4. Tests on the final approved commit, published Pages→Render browser captures and Task22 independent acceptance. This PR alone does NOT authorize closing #111.

## Test commands

```bash
python -m pytest tests/backend/test_task24_reviewed_delivery.py tests/backend/test_task24_bilingual.py -q
python -m pytest tests/contracts tests/backend tests/rag tests/integration -q
node --test frontend/tests/test_task23_locale.cjs
```

Use final-head GitHub Actions outcome to claim any pass count. Never infer approval from success CI.
