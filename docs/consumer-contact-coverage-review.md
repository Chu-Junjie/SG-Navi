# Consumer complaint Official contacts coverage — review required

## Why this branch exists

The published `goods_dispute` and `services_dispute` preparation profiles deliberately contained `contact_ids: []`, so the frontend correctly displayed "No currently verified contact is available for this route." The existing Task 17 CASE registry already holds official telephone, assistance email and complaint form actions with evidence and source guards; **the problem is selection coverage, not a rendering defect**.

## Proposed bounded change

- Personal-use purchases in Singapore can display the reviewed CASE *assistance enquiry* telephone and email for all five concrete consumer subtypes. These remain preparation actions; the result does not promise CASE acceptance, a refund or formal claim eligibility.
- For goods/services where a local-consumer status and a prior attempt with the merchant are both confirmed, also display the reviewed CASE complaint-form link. Do not promote a preparation action to complaint submission or auto-submit anything.
- Unknown personal/business purpose stays without CASE contacts; business purchases, confirmed unregistered suppliers and transactions outside Singapore remain outside this reviewed route. A tourist may still see a general assistance enquiry, but not the confirmed local-consumer complaint-form route.
- All contact destinations, claim text, evidence records, legal text and Chinese translation strings remain **byte-for-byte unchanged** from the source package. New profile selectors only reuse reviewed fields. Existing fallback semantics remain intact.

## Release gate — do not merge until approved

The proposed package version is `action-kb-2026-11-12.1`; CASE evidence capture timestamps from 7 November are not misrepresented as a new capture/review. `package.sha256` is updated to match the exact package bytes.

The Task 24 reviewed Chinese catalog and approval **still refer to `action-kb-2026-11-07.1`**. This is intentional: do not silently rewrite the previous human approval to cover a new package revision. A source owner must review the expanded CASE route applicability, reconcile the unchanged catalog against the new source version, explicitly record a new approval, and confirm production reviewed delivery and bilingual tests before marking this PR ready or merging. The current production branch is not affected.

Run `python -X utf8 -m pytest tests/contracts tests/rag tests/backend/test_task19_action_plan.py tests/backend/test_task24_reviewed_delivery.py -q --tb=short` and `python -X utf8 -m pytest tests/backend/test_task24_bilingual.py -q --tb=short` after the reviewed-delivery gate has been reconciled. Confirm that local buyer goods and services show CASE assistance, confirmed after-dispute goods/services include the online form, and unknown/business cases do not imply eligibility.
