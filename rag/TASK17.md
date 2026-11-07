# Task 17 scenario action evidence

The versioned [action package](action_evidence/package.json) delivers 13 reviewed profiles, 18 evidence records and six verified contact actions for [Task 17 #89](https://github.com/Chu-Junjie/SG-Navi/issues/89). Task 19 consumes the package through the [Task 16 contract](../shared/action_plan_contract.json). The package is separate from the historical knowledge base and its disabled rule flags.

## Source review on 7 November 2026

[The capture register](action_evidence/source-checks.json) retains HTTP outcomes, timestamps and digests. The CASE contact page, CASE complaint procedure, CCS consumer FAQ, Singapore Courts pages, CEA procedure pages, MOM Employment Pass page and State Courts judgment were fetched directly. The official CASE complaint destination returned HTTP 200 and contained the complaint form. This was a read-only GET.

The CASE portal, hotline and published assistance email are distinct contact actions. The hotline hours match the CASE contact page. The email is listed in the CCS consumer guidance for assistance. The CASE intake profile includes the published personal-purchase and registered-business scope, the consultation step and service/cost questions. It asks CASE to assess the reported dispute. If the minimum route facts are incomplete, the profile offers a specific preparation step. Business use, an overseas merchant or a confirmed non-registered supplier exits this reviewed scope.

The legal extracts use two layers of verification. The exact statutory phrases match the authoritative SSO indexed provisions and accessible official reproductions. The response identifies the actual publication supplying the readable quote and context.

| Evidence | Version and authoritative provision | Readable official reproduction |
| --- | --- | --- |
| CPFTA-4A | 2020 Revised Edition, version dated 9 March 2025, listed by SSO as at 7 November 2026. [Section 4(a)](https://sso.agc.gov.sg/Act/CPFTA2003?ProvIds=pr4-%2Cpr5-%2Cpr6-) | [CCS consumer FAQ, question 2](https://www.ccs.gov.sg/resources/faqs/consumer-protection/) |
| SCTA-SCHEDULE-1C | 2020 Revised Edition, version dated 1 October 2025, listed by SSO as at 27 October 2026. [Schedule paragraph 1(c)](https://sso.agc.gov.sg/Act/SCTA1984?ProvIds=Sc-) | [2026 SGSCT 8, paragraph 22](https://www.elitigation.sg/gd/s/2026_SGSCT_8) |

Direct SSO HTML and PDF checks returned 403, including in the ordinary headless browser. The indexed edition dates and direct-capture failures are preserved. The official reproductions support the bounded wording, with their own live capture timestamps. The source review does not extend to a fresh full-body SSO capture, an unseen exception or a conclusion on the user's case. The HDB tenancy page also returned 403. The HDB profile therefore uses general records and procedure context and omits the private property template.

For the private rental and pass scenario, CEA links to the [optional tenancy template, version 1.3](https://isomer-user-content.by.gov.sg/71/60052678-1592-4904-b443-3269a655e0de/Tenancy%20Agreement%20Template%20for%20Private%20Residential%20Property.pdf). The downloaded PDF returned 200. Its bytes were hashed. Text extraction and rendered page inspection located Schedule item 14 on PDF page 3 and deposit clause 2.2 on PDF page 6. The model break clause has applicability choices, contract-dependent timing and notice conditions. The plan directs the user to the signed terms, notices and itemised deduction. It keeps administrative EP information separate and labels the small claims excerpt as jurisdiction context. An ordinary early-exit profile omits the pass-specific item.

The contact mapping differentiates a landlord's deposit dispute, agent conduct and a signed agency agreement. A complaint about a landlord receives records or official criteria guidance. The CEA conduct and agreement contact actions each have their own evidence and conditions.

## Reproduce and use

Install the existing dependencies using `python -m pip install -r tests/contracts/requirements.txt`. The source and contract regression uses:

```powershell
python -X utf8 -m pytest tests/contracts tests/rag -q --tb=short
```

The executed local run returned **380 passed in 48.41 seconds**. It reused the audited Python environment. The [actual local RAG traces](action_evidence/scenario-traces.json) show the restaurant scenario selecting the CASE complaint form, hotline and email. The work-pass-related private rental scenario selects signed-contract review and an optional Courts criteria link. Both identify the exact legal evidence and selected claim by ID. The traces use synthetic confirmed facts and an isolated read-only repository state.

```python
from rag.action_evidence import select_action_plan

plan = select_action_plan(
    confirmed_context,
    expected_version="action-kb-2026-11-07.1",
    repository=existing_evidence_repository,
)
```

The caller supplies a confirmed Task 16 context and renders the returned plan or asks a relevant question when no profile fits. It handles `ActionEvidenceUnavailable` as a source-limited response. The package validates exact contact authorization, case association, claim references, digests and draft slots. Selection checks the LF-normalized package digest, canonical version, relevant source quarantine and a 30-day age bound. It re-reads the package and canonical source state before returning. The snapshot timestamp remains visible in the evidence. The first approved profile with matching case, goal and typed facts supplies the action. Missing and explicitly unknown facts remain distinct.

The runtime reads the existing canonical source state for family quarantine. New evidence IDs are guarded by their related CASE, Courts or CEA source IDs. For a detected change in a new publication, the operator can quarantine the affected family or withdraw the package version, then recapture, review and publish a new version. A live source audit and review are required when replacing the snapshot. Task 19 owns the actual service and Task 21 owns displaying these fields. The existing local server command is `python -m flask --app integration.app run --host 127.0.0.1 --port 5000`.
