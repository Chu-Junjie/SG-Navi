# Source preparation and evidence retrieval

This package contains the reviewed source bundle, validation/import utilities, Rule ID retrieval, citation validation and source quarantine operations. [Task 4 usage](TASK4.md) documents the runtime evidence boundary and update workflow. A Rule Engine and /api/navigate integration remain with their assigned owners and Tasks.

[Task 13 query-aware retrieval](TASK13.md) adds deterministic passage ranking
from confirmed facts and an optional bounded English query. It uses a separate
internal versioned contract and still enforces complete exact-rule retrieval
and current citation/quarantine checks. It does not activate legal rules or
change the v1 envelope. Task 12/15 runtime and Task 14 display integration remain
separate handoff steps.

[Task 14 display evidence](TASK14.md) approves the separate display schema and
adds genuinely checked short-source context, exact claim-to-Evidence bindings
and a final reread/quarantine boundary. Quote, editorial summary, locator and
review/capture times remain explicitly distinguished; publisher screenshots
and unverified deep links remain unavailable.

[Task 6 integrity checks](TASK6.md) document current-review proof binding, quarantine event replay and the reproducible RAG-01–12 runner. [The actual RAG results](../docs/task6-rag-results.md) include observed failures, fixes and source checks; full team Task 6 acceptance remains separate.

## Run

From the repository root, using Python 3.12 or newer:

```powershell
python -m pip install -r tests/contracts/requirements.txt
python -m rag.import_knowledge_base
python -m rag.import_knowledge_base --verify-live
python -m rag.import_knowledge_base --output instance/task3-kb.json
python -m pytest tests/rag -v
```

Offline checks are the default. `--verify-live` reads the five source URLs, requires unchanged normalized-page fingerprints and checks every original excerpt against the current page. It does not modify review records. `--output` creates a new validated JSON snapshot; it refuses to overwrite an existing file or add files inside knowledge_base/. The example instance/ export is ignored by Git. Combine `--verify-live` and `--output` when an online check must precede export.

## Five source files

| File | Content |
| --- | --- |
| knowledge_base/sources.csv | Source ID, publisher, title, URL, tags, actual review time/reviewer, status and version |
| knowledge_base/passages.jsonl | 26 uniquely identified excerpts, separate summaries, contextual locators, cases, rule IDs, version, URL, status and excerpt digest |
| knowledge_base/rule_evidence_map.json | 26 reciprocal mappings; all runtime_enabled flags are false |
| knowledge_base/action_templates.json | Five conditional templates covering both cases; every condition, step, document item and limitation cites Evidence IDs |
| knowledge_base/source_review_log.csv | Initial live retrieval times, HTTP results, full-text fingerprints, matched excerpt digests and affected rule IDs |

The source directory contains exactly these five files. Version `kb-2026-11-01.1` identifies this checked bundle. It is distinct from Task 2's synthetic mock-1 version. Any reviewed content revision needs an explicit version and review-log update; the importer does not silently renew or promote sources.

A documented recheck showing only site banners or footer changes can append a same-evidence-version review entry with the newly checked page fingerprint. Original excerpt digests and review history must remain intact. Changes to evidence text or its policy context require a content/version review instead. The 2026-11-02 CEA rechecks follow the former procedure; strict fingerprint verification remains enabled.

## Read-only weekly freshness audit

A scheduled GitHub Actions job [source-freshness-read-only.yml](../.github/workflows/source-freshness-read-only.yml)
checks the five official URLs without changing any knowledge records. Local
equivalent (run with network access):

```bash
python -m rag.import_knowledge_base
python -m rag.freshness_report --output instance/source-freshness-report.json
```

The JSON report records current page SHA256, source ID, excerpt matching,
HTTP status and a status per source. It deliberately excludes the full
downloaded page and never copies credentials, claims human review or changes
`source_review_log.csv`.

- `unchanged`: matching recorded fingerprint and all checked literal excerpts.
- `page_changed_excerpts_present`: site content/layout changed, but the
  previously reviewed quotations still appear; **manual contextual review
  needed**, not automatic permission to refresh the fingerprint.
- `missing_reviewed_excerpt`: at least one cited quotation has disappeared;
  quarantine/review the affected source before making any eligibility claim.
- `url_or_http_changed` or `fetch_error`: changed URL, response or network;
  investigate without silently marking the source as current.

**Observed 2026-11-05:** a first remote read-only audit reported
`cea-dispute-resolution: content changed; review and version update required`.
This is a *drift signal*, not proof that the law or excerpt changed. The
coordinator must compare the current official content with the archived
reviewed excerpts, record whether the change is material, obtain human review
when appropriate, and only then update the five source records/version by PR.
Until then no new eligibility rules are enabled. See
[Task 7 integration guide](../docs/task7-junjie-render-neon-integration.md).
 
## Source registry

| Source ID | Official-publisher page |
| --- | --- |
| courts-sct-eligibility | [Courts eligibility](https://www.judiciary.gov.sg/civil/cases-eligible-small-claim) |
| courts-sct-filing | [Courts filing](https://www.judiciary.gov.sg/civil/how-to-file-serve-small-claim) |
| cea-dispute-resolution | [CEA dispute resolution](https://www.cea.gov.sg/consumers/engaging-a-property-agent/dispute-resolution/) |
| cea-complaint | [CEA complaints](https://www.cea.gov.sg/submit-complaint/) |
| case-complaint | [CASE complaints](https://www.case.org.sg/submit-a-complaint/) |

All five were fetched directly with HTTP 200 on 2026-11-01. `verified` records identify **Codex automated page and excerpt check** as the reviewer. It means the source was read and the short literal excerpt matched the captured page. It does not claim human approval, official endorsement or a legal determination. Excerpt matching and source fingerprints were also checked by the published importer's live-verification mode.

The `text` field is a short verbatim excerpt, not an entire paragraph. The `summary` field is editorial and must not be presented as an official quotation. Complete pages are not redistributed. Refetch the cited page for context. Sources that cannot be read or checked must remain unreviewed or quarantined rather than receive a successful review record.

## Validation guarantees and boundaries

Import rejects missing files/columns, duplicate IDs, missing or untrusted URLs, broken mappings, mismatched cases/versions, changed excerpt digests, unverifiable review metadata and unsafe activation of unreviewed records. Verified templates and rules cannot cite unreviewed or quarantined passages. A verified passage cannot inherit trust from an unreviewed source. Invalid data produces no exported snapshot.

Stored passages include original-text fields that are not part of the API envelope. Use `api_evidence(passage)` to project exactly the existing six shared Evidence fields before API use; tests validate every projection against the canonical shared schema. No shared contract fields were changed.

Offline review checks establish internal consistency, not the authenticity of a manually edited review ledger. The live check adds current page and quote verification. Full-page fingerprints include navigation and footer text, so an editorial page change can require a review even when the relevant excerpt appears unchanged.

## Handoff and remaining scope

- ZhengZaikun should review the proposed rule IDs with the mappings when defining backend rule configuration. **No runtime rule is enabled by this package.** Missing or ambiguous conditions still require clarification or official referral.
- Guanyu-Lu should use the cited templates to map the two case flows and seven Action Card sections. The templates are content building blocks, not new Action Card API fields.
- Case-specific facts such as prior resolution attempts and document availability are not automatically eligibility conditions. Immigration/criminal boundaries and any other checks lacking indexed evidence remain unverified and disabled until supported. The map contains only checks with actual Evidence IDs.
- Keep landlord tenancy issues, agency contract disputes and agent-conduct complaints separate. CASE's description of overseas partnerships does not make cross-border cases part of SG Navi's project scope.
- Task 4 adds retrieval, citation checks and a separate quarantine state file without altering the five source files or enabling legal rules. FTS5 is unnecessary for the current exact-ID lookup; no search index is maintained.
- Existing CI runs contracts, backend, frontend and tests/rag/. Task 4 tests are included by that existing configuration. Backend/RAG integration remains for Task 5.
