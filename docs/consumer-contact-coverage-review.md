# Consumer complaint Official contacts — bounded selection fix

## Root cause

The existing reviewed Task 17 package has 13 profiles. The goods and services preparation profiles have no contacts configured, so the frontend correctly displays "No currently verified contact is available for this route" even though Task 17 already includes verified CASE phone, email and complaint form actions.

## Fix

This PR preserves the **entire existing signed Task 17 evidence package** (including `package.json`, `package.sha256`, review dates, source version `action-kb-2026-11-07.1`, its 13 source profiles, and all official contact/quote text) rather than creating a new package version. Only the selector's combination of previously verified contact actions changes.

- For a personal purchase in Singapore matching any of the five concrete consumer subtypes, return existing CASE phone/email *assistance enquiry* actions in the preparation plan. This does not claim intake eligibility, a refund or filing success.
- For `goods_dispute` and `services_dispute` with a confirmed local consumer, prior attempt to resolve with merchant, and a suitable complaint/refund/understand goal, also provide the reviewed CASE complaint form under `Official contacts`. The primary next step is still preparation and nothing is submitted automatically.
- For an earlier restaurant complaint route that already explicitly selects CASE form/phone/email, leave that reviewed profile untouched.
- Do not present CASE actions when personal purpose is missing/unknown, the seller is confirmed unregistered, the purchase is business-related or the transaction is outside Singapore. Visitor cases can ask the contact desk for information but do not automatically get the form.
- The additional `consumer_context` question for goods/services asks only when a verified complaint intake route might be relevant. It remains a single Task 18/19 question and has an unknown/visitor option.

## Evidence and approval integrity

No source content, evidence digests, legal quotations, existing review timestamps, approved Chinese translation strings or human sign-off records are changed. All contact actions originate from the existing approved Task 17 registry, and `_materialize` validates their exact evidence associations; runtime quarantine and source freshness checks still apply to the returned contact evidence.

This is a **routing behavior change** even though it does not change the approved source package. Review the decision gates and run the full backend/RAG/Task24 regression suite before merging. Do **not** claim this branch has completed a fresh official-source review or a new human approval. The approved Chinese catalog remains version-compatible because the signed underlying evidence package and its exact English strings have not been replaced.

## Test command

```powershell
python -X utf8 -m pytest tests/contracts tests/rag tests/backend -q --tb=short
```

Verify that a goods complaint now returns relevant CASE assistance; a confirmed after-dispute goods/service complaint shows the CASE form; unknown-purpose and out-of-scope cases do not show unqualified contacts; and Task24 reviewed Chinese delivery remains enabled.
