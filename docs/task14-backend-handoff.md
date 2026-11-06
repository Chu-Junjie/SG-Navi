# Task 14 — backend Evidence Viewer projection handoff

Issue [#74](https://github.com/Chu-Junjie/SG-Navi/issues/74). This change is **Zheng's backend API-integration portion**, not Junjie's source curation or Guanyu's UI delivery. The canonical six-field Evidence v1 remains unchanged. No source data or review state was modified.

## Projection contract (proposed display extension)

The existing `POST /api/results/preview` response retains `results_version: 0.1`, `GUIDANCE_ONLY` / `LIMITED_REFERRAL`, null legal Action Card and all previously published display fields. Each `display_evidence` object additionally contains:

```json
{
  "display_version": "1.0",
  "display_state": "verified_snapshot",
  "preview": null
}
```

Its existing fields remain `evidence_id`, `source_id`, `rule_ids`, `url`, `review_status`, `source_version`, `publisher`, `title`, `verbatim_excerpt`, `source_locator`, `reviewed_at`, `summary`, and `excerpt_sha256`. `verbatim_excerpt` is the **exact currently recorded source passage**; `summary` is **SG Navi-authored explanatory text** and must be labeled separately by the viewer. `verified_snapshot` is a verified repository review record, NOT an assertion that the publisher's website was reachable or unchanged at this instant. No screenshot, page, HTML anchor or official endorsement is supplied.

### Two trace examples from existing reviewed records

1. Rental `SCT-ELIG-RESIDENTIAL` — exact existing quote: `residential premises not exceeding 2 years`. Original: `https://www.judiciary.gov.sg/civil/cases-eligible-small-claim`. Locator: `tenancy scope paragraph`. This passage can accompany a **conditional research** check of residential tenancy scope; it does not decide eligibility.
2. Consumer `CASE-PERSONAL` — retrieve the **current canonical excerpt** from the existing five-file knowledge bundle and display its recorded publisher/locator/date. Do not substitute the editorial summary for the quote or invent a larger surrounding quote. The integration test checks its presence in a personal-use consumer scenario.

## Final validation boundary

`backend.evidence_projection.project_display_evidence` performs a **fresh repository snapshot** before projection and checks:
- requested corpus version, source/case scope, current verified source review, operational quarantine;
- official HTTPS allowlisted URL and unchanged source-to-passage URL;
- original passage SHA-256 and exact passage digest listed in the current source review record;
- individually attributed guidance conditions, channels, steps and document checklist with unique Evidence IDs;
- optional comparison against the earlier assembly snapshot: ID set, URL, review timestamp, source version, original excerpt, digest and metadata.

When any check fails, the existing Task 12 result assembly returns `LIMITED_REFERRAL` with null guidance and **no display evidence**. Nothing is partially marked verified. Existing `/api/navigate` v1 continues to return only the canonical six-field Evidence data.

## Ownership and pending acceptance

- **Junjie:** approve the display extension and verify the original 26 short quotations are sufficient for the UI. Any expanded quotation, official-source snapshot, page locator or added provenance MUST undergo actual source review with the existing audit/digest protocol. Task 13 ranking is already delivered; source curation remains independent.
- **Guanyu:** safely render `verbatim_excerpt` and explicitly distinguish `summary`; hide preview while null. Clicking a citation/step must show its exact `evidence_id`, not just a generic publisher URL.
- **Zheng:** backend projection + tests done in this PR, subject to review and actual CI. No claim of source live fetch, external screenshots, actual filing, or legal eligibility. Task 15 still owns final cross-component wiring/acceptance.

## Verification commands

```bash
python -m pytest tests/backend/test_task14_projection.py -q
python -m pytest tests/contracts tests/backend tests/rag tests/integration -q
```

Actual pass/fail counts must be taken from the corresponding GitHub Actions run, not assumed here. The tests use the repository's currently reviewed records and controlled tampering/quarantine fixtures; they do not access or alter live source websites or production quarantine state.
