# Task 24 — production reviewed-zh-Hans activation checklist

Issue: #111. This is Zheng's backend shipping gate; the independently reviewed translation attestation must be committed by Junjie *before* activation.

## State verified on 2026-11-10

- PR #114 merged, PR #121 merged. Both change sets are present on GitHub `main`.
- The approved translation provenance file `backend/locales/task24_review_approval.json` is **not present** and Issue #111 contains no recorded reviewer approval. The catalog still says `pending_review`. It would be misleading to publish a green verified translation response now.
- The Render service visible to Zheng's connected account is **sg-navi-api-free-demo**, tracking `feat/task7-free-render-demo`, auto-deploy **off**, live commit `635ded120e4dfa3196b6c30b3b162c9d77dd5cf5`. It is NOT the `main` service described in `render.yaml`, which names `sg-navi-api-junjie`. No deployment is claimed on that separately managed service.

## Changed in this PR

- `SG_NAVI_TASK24_REVIEWED_LOCALE=0` (default) keeps the reviewed Chinese endpoint disabled.
- `SG_NAVI_TASK24_REVIEWED_LOCALE=1` checks the *actual* source-owner attestation, current Task17 source-package version and exact catalog entry digest at Gunicorn process startup. If missing or invalid, the process fails startup rather than serving unreviewed text.
- Only when enabled, `POST /api/action-plan/zh-hans-reviewed` supports exact-origin `https://chu-junjie.github.io` CORS. Its OPTIONS preflight allows POST / Content-Type and no credentials; other origins and methods are denied. Disabled preflight returns HTTP 404 without CORS headers.
- Even when manually enabled in a local Flask test without approval, the real API returns HTTP 503 `translation_not_approved`.
- Canonical `POST /api/action-plan` English 1.0, request and revision IDs, original English official excerpts, their hashes, source IDs, and contact destinations remain unchanged.

## Release process (requires Junjie)

1. Junjie checks all sensitive Chinese candidate texts, provenance, official source meaning and the bilingual contract with Guanyu, and records a clear approval in #111. Junjie (not Zheng) commits `backend/locales/task24_review_approval.json` with actual reviewer timestamp, package version, and SHA-256 of unchanged entries, following `docs/task24-reviewed-delivery-gate.md`. Require independently approved GitHub code review; a JSON name is not independently verifiable identity.
2. Merge this PR after tests/review. Verify the **real production service** is running reviewed commit on `main`, with durable source/quarantine state and existing safety requirements satisfied. Do not repoint the old demo service as a substitute.
3. On the **owner-controlled** `sg-navi-api-junjie` production service, set `SG_NAVI_TASK24_REVIEWED_LOCALE=1` and deploy the approved main commit. The endpoint is not intended to be toggled before the approval commit exists. Keep `SG_NAVI_CORS_ORIGINS=https://chu-junjie.github.io`; do not use wildcard CORS.
4. After deploy, check `GET /api/health`, `GET /api/version`, `OPTIONS /api/action-plan/zh-hans-reviewed` (Origin: `https://chu-junjie.github.io`, Access-Control-Request-Method: POST, Access-Control-Request-Headers: content-type), and `POST` with synthetic English `interpret` and confirmed `plan` requests. Verify `canonical` vs English 1.0, `display` Chinese after review, exact source quotation bytes, URLs, revision IDs and request IDs. Record HTTP status, deployment SHA, JSON excerpt and actual review reference in #111.
5. Send the real URL + contract/example to Guanyu for Task23 frontend consumption, followed by Pages→Render two-scenario browser acceptance (restaurant overcharge and rental deposit / work-pass context). Distinguish "reviewed Chinese explanation" from official translation. Do not claim Chinese free-text intake.

### Real example request to use only after approval and deploy

```json
{
  "action_plan_version": "1.0",
  "request_id": "task24-public-12345",
  "operation": "interpret",
  "description": "I bought a faulty product and want a refund."
}
```

Expected high-level *schema*, not a claimed network result:

```json
{
  "overlay_version": "task24-reviewed-1.0",
  "locale": "zh-Hans",
  "translation_status": "approved_explanation",
  "is_official_translation": false,
  "canonical": {"action_plan_version": "1.0", "state": "CONFIRM"},
  "display": {"context_summary": "您表示购买的商品发生纠纷。 您希望请求返还款项。"}
}
```

The exact response contains further fields and must be captured from the actual deployed service before being posted as evidence. **Do not copy the illustrative values as a successful real response.**

## Regression commands

```bash
python -m pytest tests/backend/test_task24_production_cors.py tests/backend/test_task24_reviewed_delivery.py -q
python -m pytest tests/contracts tests/backend tests/rag tests/integration -q
```

Judge the final branch SHA from GitHub Actions, not older historical runs. Issue #111 remains Open until full reviewed API and real deployment evidence is posted.
