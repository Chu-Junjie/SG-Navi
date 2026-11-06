# Task 14 — reviewed display evidence and claim-level source context

Issue [#74](https://github.com/Chu-Junjie/SG-Navi/issues/74). Source/shared owner:
Chu Junjie. This completes the source-owner portion on top of Zheng's reviewed
backend projection [PR #83](https://github.com/Chu-Junjie/SG-Navi/pull/83).

## Approved additive contract

[`shared/display_evidence_contract.json`](../shared/display_evidence_contract.json)
approves `display_version: 1.0` and the backend's existing 16 display fields.
Canonical six-field Evidence, `/api/navigate`, rule activation and API 1.0 are
unchanged. The context enrichment is an optional, separately versioned nested
extension; it is validated locally without fetching schema URLs.

- `verbatim_excerpt` is the exact current recorded official short quotation.
- `summary` is SG Navi editorial text. `display_context` labels it explicitly;
  it must not be rendered as an official quotation.
- `source_locator` is the existing editorial textual description, not an
  invented official heading, paragraph number or HTML anchor.
- `reviewed_at` remains the actual canonical source-review time. The new
  `checked_at` and `context_reviewed_at` are separate capture/context-check times;
  canonical reviewer/method and operational quarantine state are explicit.
- `verified_snapshot` means checked repository provenance at projection time.
  It never means live website availability, official approval or eligibility.
- `preview` is **null**. No real official-page screenshot, PDF page or deep-link
  capture was supplied. A future extension needs an actual capture, original
  source URL, timestamp, digest and correct excerpt position before schema approval.

## Actual context curation

[`display_contexts.json`](display_contexts.json) is outside the exactly-five-file
canonical corpus. Its independent `context_version` binds **all 26** original
passages to five actual HTTP-200 captures on **2026-11-06**, their current
reviewed full-page hashes, excerpt/summary/locator digests, and exact positions
in whitespace-normalized visible text. This is automated source/context checking
by Codex, not human or official approval. Canonical review logs/dates, excerpts,
source version and legal thresholds were not altered.

Three inspected short-context additions clarify the event-time fragment,
respondent service location and the antecedent of CASE's ambiguous fee fragment.
Only bounded exact original wording is stored; it is separately hashed and tied
to the same page capture/review proof. The remaining fragments retain the
existing clearly labeled editorial explanation and official source link. Every
record is marked `short_fragment_requires_official_context`; none becomes a
complete legal rule. Positions refer to normalized **text**, not an HTML anchor
or screenshot crop. Full public-page captures remain ignored local review files.

## Final source-owner verification boundary

`rag.display_context.enrich_display_evidence(case_type, guidance, display_records,
expected_source_version=..., repository=..., freshness_report=...)` consumes the
actual `backend.evidence_projection.project_display_evidence` output:

1. Independently verify every baseline display field against a new authoritative
   repository snapshot: case, source, URL, exact quote/digest, original summary,
   locator, source version, current review identity and quarantine state.
2. Bind **every channel, condition, ordered step and checklist item** to the
   exact approved template text and its complete Evidence ID set. Extra same-case
   citations, omitted/reordered steps, arbitrary prose with a valid ID and partial
   multi-passage mappings fail. This is template/provenance validation, not a new
   determination that a legal process applies to the user.
3. Verify the separate context review, page hash, immutable record binding,
   current excerpt/summary/locator digests, time order and normalized text span.
4. If a trusted read-only freshness report is provided, any required source's
   403/timeout/drift/missing excerpt is `SOURCE_PENDING`; no badge is produced.
   Without a report the output claims only the dated reviewed snapshot. Existing
   source quarantine must still be applied by the established operator protocol;
   this helper never writes review or operational state.
5. Reuse `validate_citations` for complete canonical rule/source coverage and a
   fresh state read. Compare the full snapshot fingerprint and context file again
   immediately before returning; changed data cannot inherit an earlier badge.

Any failure raises `DisplayContextUnavailable` with a fixed diagnostic code.
The caller must discard all tentative display records and return the limited/
referral result. Never catch an error and publish the earlier input records.
There is no query/model/network call or case-data persistence on this path.

The returned `claim_citations` uses stable section/index IDs such as `steps:0`;
each selected step resolves to specific display Evidence IDs, never only a
publisher URL. The original quote, editorial explanation, review state and
source link remain separate fields for the Evidence Viewer.

## Real examples and commands

- [Rental source trace](examples/display_rental_trace.json) binds an actual
  approved condition to the recorded Courts passage and source metadata.
- [Consumer source trace](examples/display_consumer_trace.json) binds an actual
  personal-purchase/supplier condition to the exact recorded CASE passages.
- [Synthetic backend projection input](examples/display_projection_input.json)
  is generated by the actual merged backend assembler, not a fabricated API.

From an installed repository root (Python 3.12+):

```powershell
python -m pip install -r tests/contracts/requirements.txt
python -m rag.display_context --case-type rental_deposit --input rag/examples/display_projection_input.json --source-version kb-2026-11-01.1
python -m pytest tests/rag/test_display_context.py tests/backend/test_task14_projection.py -q
```

CLI exit 0 means checked enriched data; exit 1 prints only unavailable/empty data.
Use the actual current source version in integration code. Installation commands
are existing repository instructions; this task reused the installed environment
and verified `pip check`, rather than claiming a new install/member machine.

[Actual tests, captures, hashes and limitations](../docs/test-results/task14-rag-20261106.json)
are recorded separately. Current successful independent captures do not repair
or erase historical runner CASE 403/timeouts. No physical-device or publisher-tab
acceptance is inferred from these data checks.

## Task 15 handoff

The approved baseline projection is already available through Task 12 preview.
Task 15 must call the enrichment at the final preview boundary, safely render
original/summary/context labels, and connect selected claims to exact records.
It must verify the actual Pages → Render browser workflow. This task supplies the
source-owner contract, genuine context, final validator, examples and backend
composition tests; it does not claim that the full new UI is already integrated.
