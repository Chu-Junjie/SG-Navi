# Task 25 — Case-specific official-route explorer

The new user interface preserves the three personal planning steps. Step 3 expands into source-linked CASE, SCT, or CEA research paths, conditionally selected from confirmed context. These are informational guides only and do not decide eligibility, file anything, track cases, or bypass existing verified contacts.

## Decision boundaries

- Singapore consumer purchase: CASE pathway if not confirmed business use. Verified CASE form appears only through the existing backend contact gate; visitors see a separate caution and no inferred filing entitlement.
- Consumer purchase: SCT path is a possible research route, with an explicit eligibility check. Transactions confirmed outside Singapore are not surfaced.
- Landlord residential rent/deposit: SCT path for potential residential tenancy disputes; do not show for known commercial or industrial premises.
- Agent conduct: CEA regulatory complaint path, separate from tenant vs landlord money disputes.
- Estate agency agreement dispute: CEA mediation/arbitration scheme path; no eligibility promise if a qualifying signed agreement is unknown.

## Sources and review requirements

The following source identifiers/URLs are already present in the signed Task17 Action Package (version action-kb-2026-11-07.1) and are used as read-only official process references:
- CASE-SCOPE, CASE-ASSESS and CASE-FEES: https://www.case.org.sg/submit-a-complaint/
- COURTS-RESIDENTIAL: https://www.judiciary.gov.sg/civil/cases-eligible-small-claim
- COURTS-RECORDS: https://www.judiciary.gov.sg/civil/how-to-file-serve-small-claim
- CEA-CONDUCT-ROUTE: https://www.cea.gov.sg/submit-complaint/
- CEA-AGREEMENT-ROUTE: https://www.cea.gov.sg/consumers/engaging-a-property-agent/dispute-resolution/

One additional official overview page is pending independent review:
https://www.judiciary.gov.sg/civil/file-small-claim
It documents possible post-filing settlement, consultation, hearing, and post-order processes. It is explicitly flagged as pending_review and is never mistaken for already attested Task17 evidence.

When a workflow stage source exactly matches an evidence record returned by the current verified API result, the UI opens the verified source panel. Otherwise it displays an official informational link with a non-verification warning. Formal filing/assistance buttons remain restricted to existing backend-verified contacts. No signed RAG package, source hash, backend schema, Task24 translation approval, source timestamp, or user data is changed.

## Release gate

The owner must independently confirm the new SCT overview and the route-stage summaries against official pages before merging. The frontend's Chinese phrases are interface explanations, not official translated quotations. Check the separate CASE vs SCT options, landlord vs agent routing, visitor caution, signed-agreement gate, three progress checkboxes, accessibility, responsive modal layout, and existing English/Chinese reviewed action plan.
