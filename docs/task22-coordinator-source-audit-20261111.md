# SG Navi — Junjie source/evidence and release audit (11 November 2026)

**Owner:** Chu Junjie — AI & RAG Retrieval Lead / source reviewer / Task 22 coordinator  
**Scope:** Read-only evidence integrity, first-party source meaning, frozen evaluation gaps, published bilingual release identity  
**Disposition:** **SOURCE-INTEGRITY CHECKS PASS; SOURCE-FRESHNESS/LITERAL LAW REVIEW CONDITIONAL; TASK 22 FINAL ACCEPTANCE NOT YET PASSED.** This is an independent technical/source audit, **not** a legal opinion or a fabricated human usability study.

## 1. Current release and what was actually inspected

- GitHub `main`: `a9cc8cc85ac356482c711bd68c3039e39cee1b7a` (merged frontend correction PR #131). Frontend `REVIEWED_ACTION_PLAN_ENABLED=true`.
- Correct owner-managed Render `sg-navi-api-junjie`: deploy `dep-dbpsn4u0tbcc73fj2va0`, `status=live`, exact same commit `a9cc8cc85ac356482c711bd68c3039e39cee1b7a`, finished 2026-11-11 01:58:29 UTC. This is a direct GitHub/Render metadata comparison, **not** an HTTP probe from the current auditor.
- Review-gated API approval: `backend/locales/task24_review_approval.json`, `task24-reviewed-1.0`, `zh-Hans`, owner `Chu-Junjie`, reviewed at `2026-11-10T14:38:32+00:00`. Independently recomputed approved `catalog["entries"]` SHA-256 **`d9aa17280c9691388c4ed1c410cad5274594930bc61fb2ce7208f84e4f010ca3`** = checked-in approval digest. Catalog still has 155/155 nonempty candidate rows deliberately tagged `pending_review` (the **separate approval file** is what authorizes delivery; do not change row statuses).
- Inspected `rag/action_evidence/package.json` `action-kb-2026-11-07.1` (13 profiles, six contacts, **18** evidence records), the approved catalog, and Guanyu's actual [public reviewed API capture](../frontend/tests/evidence/task23-20261111/public-reviewed-api.json). No user dispute was transmitted for this review.

## 2. Reproducible integrity checks

| Independently checked item | Observation | Interpretation |
| --- | --- | --- |
| Every Task 17 `evidence.quote` against its own `quote_sha256` | **18/18 match** (literal UTF-8 SHA-256) | Checked-in excerpt bytes have not diverged from their recorded quote digests |
| Three archived public `READY` `canonical` + `display` envelopes (consumer overcharge, rental/pass exit, rental deposit deduction) | **3/3** have `task24-reviewed-1.0`, reviewer identity and matching catalog entries digest | Archived public requests prove those three examples, **not** every possible case |
| Every returned public evidence record's `quote`, quote/source digest, source ID, URL, kind, reviewer timestamp and review status vs Task 17 package | **No mismatch found** | Archived citations preserved their authoritative package metadata |
| Evidence IDs in archived visible checklist and legal-basis claims vs 18-item evidence register | **No unknown ID found** | These claim pointers resolve to the frozen source package |
| Archived public contact destinations vs reviewed Chinese `display` contact destinations | **No destination mismatch found** | Translation did not alter phone/email/portal routing in the checked examples |
| Public CORS/transport evidence | Stored POST **HTTP 200**, OPTIONS **204**, exact `access-control-allow-origin: https://chu-junjie.github.io` | This evidence was captured 2026-11-11 01:12 UTC, **before** PR #131 merge; do not call it a new live POST against final `a9cc8cc...` |
| Latest release deploy SHA | GitHub main and Render live commit **match** | Resolves the previously missing provider-deployed SHA in a metadata-based way; public `/api/version` still does not disclose it |

**Important distinction:** These are deterministic **in-repository integrity** and archived-response comparisons. The audit did **not** reconstruct the new HTTP byte-level `source_sha256` for each webpage or issue a fresh POST/OPTIONS from the final deployed browser.

## 3. Source meaning / currency spot-checks (11 November 2026)

The original frozen package was reviewed **7 November 2026**. Public first-party pages were visited anew and their relevant wording/context checked, **without overwriting the package's frozen page hashes or claiming identical live HTML bytes**.

| Source / mapped evidence | Verified meaning / caveat |
| --- | --- |
| [CASE contact](https://www.case.org.sg/contact-us/) — `CASE-PORTAL`, `CASE-PHONE` | Complaint URL `https://complaints.case.org.sg/`, telephone `+(65) 6277 5100`, general hotline Mon–Fri 09:00–17:00 excluding holidays |
| [CASE complaint process](https://www.case.org.sg/submit-a-complaint/) — `CASE-SCOPE`, `CASE-FEES`, `CASE-ASSESS` | Personal/domestic consumer-to-business scope; officers assess before giving next steps; fees may apply. Landlord/tenant claims are specifically excluded from CASE assistance. Tourist appointment details are **not** the same as general telephone operating hours |
| [CCS consumer protection FAQ](https://www.ccs.gov.sg/resources/faqs/consumer-protection/) — `CASE-EMAIL`, `CCS-RECORDS`, `CPFTA-4A` | Supports `admin@case.org.sg`, evidence-document preparation, CPFTA s4 misleading-practice excerpt. CCS distinguishes consumer redress via CASE/STB from its own supplier enforcement |
| [Singapore Courts SCT eligibility](https://www.judiciary.gov.sg/civil/cases-eligible-small-claim) — `COURTS-RESIDENTIAL` | Residential tenancy scope not exceeding 2 years; claim amount/time limits and disallowed commercial/industrial premises remain conditional. The site does not promise a deposit refund |
| [Singapore Courts filing](https://www.judiciary.gov.sg/civil/how-to-file-serve-small-claim) — `COURTS-RECORDS` | Invoices, receipts, contracts and tenancy agreements are suggested documents; formal filing eligibility requires assessment |
| [CEA dispute resolution](https://www.cea.gov.sg/consumers/engaging-a-property-agent/dispute-resolution/) — `CEA-AGREEMENT-ROUTE` | Scheme depends on a **signed estate agency agreement** and a dispute **about that agreement**, not an ordinary landlord deposit conflict |
| [CEA agent complaint](https://www.cea.gov.sg/submit-complaint/) — `CEA-CONDUCT-ROUTE` | Agency/agent conduct jurisdiction, complaint evidence and disclosure limitations. Not a general landlord/tenant deposit referee |
| [CEA private-rental overview](https://www.cea.gov.sg/consumers/transacting-on-your-own/renting-or-renting-out-a-private-residential-property/) and [20-page DPTWG private-tenancy template](https://isomer-user-content.by.gov.sg/71/60052678-1592-4904-b443-3269a655e0de/Tenancy%20Agreement%20Template%20for%20Private%20Residential%20Property.pdf) — `CEA-TEMPLATE-*` | Template version 1.3; explicitly **not mandatory**. The document shows optional diplomatic/break, notice and security-deposit clauses. An actual signed lease—not the sample template—controls a user's terms |
| [MOM Employment Pass cancellation](https://www.mom.gov.sg/passes-and-permits/employment-pass/cancel-a-pass) — `MOM-EP-CANCELLATION` | An EP status/cancellation rule, not a determination of a tenant's contractual rights or deposit entitlement |
| [Singapore SCT grounds of decision (2026 SGSCT 8)](https://www.elitigation.sg/gd/s/2026_SGSCT_8) — `SCTA-SCHEDULE-1C` | Published decision reproduces the jurisdictional residential-tenancy context. Its **judgment reproduction** is not a direct live retrieval of the SSO statute |
| [Singapore Statutes Online CPFTA](https://sso.agc.gov.sg/Act/CPFTA2003) and [SCTA](https://sso.agc.gov.sg/Act/SCTA1984) | **Direct retrieval returned HTTP 403** in this audit, consistent with earlier source-check metadata. Cross-referenced CCS/court reproduction, but **do not certify direct current statutory wording or page digest**. Human source owner should inspect statutory version/effective date if unqualified legal citation is required |

No supported source indicates an automatic right to refund, a guaranteed agency outcome, a universal work-pass termination entitlement or a mandatory CEA template. The app should not imply these.

## 4. Task 22: frozen 40-case observations are a real open acceptance risk

The team's [existing actual machine observations](../frontend/tests/evidence/task23-20261111/task22-machine-observations.json) were recorded **2026-11-11 01:49 UTC**, on `d4760ff6c1daa6caa28bd8c44ba1aa23cf23ea6c`, **before** final PR #131 `a9cc8cc...`. They are labelled **machine observations only**, not a scored comprehension/source-audit verdict.

| Frozen group | Case-type matched | Full interpretation matched | Expected state/action/contact matched |
| --- | ---: | ---: | ---: |
| Rental (15) | 15/15 | 3/15 | 5/15 |
| Consumer (15) | 8/15 | 2/15 | 6/15 |
| Boundary (10) | 4/10 | 2/10 | 4/10 |
| **Overall (40)** | **27/40** | **7/40** | **15/40** |

These numbers are **not** the acceptance score: the machine probe may omit decisive confirmed facts and may expect a `READY` action where the product correctly asks a follow-up. An `ASK` or safe `LIMITED` must **not** be counted as a hallucination or critical failure without case-level adjudication. Nevertheless, the observed routing/first-action mismatch is substantial relative to the frozen targets in [docs/task22-evaluation.md](task22-evaluation.md): >=14/15 correct routing **per core group**, 10/10 boundary, >=38/40 overall, >=95% source support, 100% consequential legal/contact support, >=90% mandatory checklist coverage per core group, zero critical inventions.

**Required independent follow-up (not completed by this document):**
1. @ZhengZaikun: rerun and adjudicate all 40 frozen cases on **final main**, preserving IDs, each initial actual response and the two intentionally injected failure cases. Test prescribed facts/confirmation paths, question necessity and correct next action; version any test-fixture correction, do not quietly change expected outcomes.
2. @Chu-Junjie: for each final claim/checklist/route, assess the actual supporting evidence IDs and official sources. Record 100% consequential-claim support and document any missing/ambiguous quote, contact or source-freshness case. Never equate presence of an evidence ID with semantic claim support.
3. @Guanyu-Lu / PM: if asserting actual user comprehension, record real participants and first-action/route identification time. Automated screenshots, native 200% zoom and keyboard tests are technical usability checks, **not** human comprehension measurements. Otherwise label human comprehension **NOT RUN**.
4. For a final `a9cc8cc...` public release claim, retain a new genuine published Pages-origin walkthrough/response (earlier three examples predate the PR #131 correction). Capture version, response, source IDs, exact official quote, CORS, and no stale state.

## 5. Separation of release decisions

- **Frontend merged and initial production tests:** PASS for the recorded published examples, with latest GitHub Actions and Render showing the same commit.
- **Internal quote/source-pointer integrity:** PASS for the 18 frozen evidence records and archived three `READY` examples.
- **Full current online source freshness and direct statutory version proof:** CONDITIONAL; SSO 403 and no new byte-level page re-capture. Do not mutate operational source state based on a read-only audit.
- **Task 22 route/goal/checklist/evidence evaluation of the complete 40-case frozen set:** **NOT ACCEPTED / NEEDS INDEPENDENT ADJUDICATION**.
- **Human response-time/comprehension:** NOT RUN from the available record.
- **Task 22 #94:** KEEP OPEN pending real frozen-case scoring and final coordination decision. Do not claim the whole proposal is complete merely because PR #131 and Pages CI are green.

### Evidence references

- [#111 Task 24](https://github.com/Chu-Junjie/SG-Navi/issues/111), [#106 Task 23](https://github.com/Chu-Junjie/SG-Navi/issues/106), [#94 Task 22](https://github.com/Chu-Junjie/SG-Navi/issues/94)
- [Public reviewed API capture](../frontend/tests/evidence/task23-20261111/public-reviewed-api.json), [frontend acceptance README](../frontend/tests/evidence/task23-20261111/README.md), [machine observations](../frontend/tests/evidence/task23-20261111/task22-machine-observations.json)
- [Source package](../rag/action_evidence/package.json), [source capture record](../rag/action_evidence/source-checks.json), [Task 24 traceability map](task24-source-traceability.json), [approved entries digest](../backend/locales/task24_review_approval.json)
