# Task 4 evidence module

The public entry point is `retrieve_evidence(case_type, rule_ids, facts)`. It uses the same request and Evidence schemas established in Task 2. Retrieval selects source evidence for rule IDs supplied by the backend; it does not decide whether those rules apply to a dispute.

Task 13 adds a separate [query-aware research-context function](TASK13.md) with
its own internal versioned contract. This legacy exact-rule entry point and
its two-field response remain unchanged; it is still the strict coverage gate
used after query ranking.

## Run independently

From the repository root:

```powershell
python -m pip install -r tests/contracts/requirements.txt
python -m rag.retriever rental_deposit --rule-id SCT_RESIDENTIAL_SCOPE --rule-id SCT_CLAIM_AMOUNT
python -m rag.retriever consumer_complaint --rule-id CASE_PERSONAL_PURPOSE
python -m pytest tests/rag -v
```

There is no additional service, API key, database or search index. Twenty-six passages are small enough for exact Rule ID lookup through the validated map. A query without rule IDs does not fall back to keyword search or infer rules from user facts.

## Retrieval contract

The returned object contains exactly `retrieval_status` and `evidence`. The status vocabulary is defined by this RAG implementation and fits the existing shared string field; it does not add navigation statuses.

| retrieval_status | Meaning |
| --- | --- |
| FOUND | Every requested rule has its complete reviewed evidence set for the selected case |
| NO_RESULTS | No rules requested, an unknown/wrong-case rule, or at least one mapping/source is unreviewed or quarantined; evidence is empty |
| ERROR | Invalid input, unreadable/invalid knowledge files or corrupt source state; evidence is empty |

Evidence records have exactly `evidence_id`, `source_id`, `rule_ids`, `url`, `review_status`, `source_version`. Results follow request rule order and map order, with Evidence IDs deduplicated. A shared passage records all requested rules it supports. A mixed successful/failed batch returns no partial evidence. URLs, versions and review status come from the checked bundle, never from the caller.

`facts` must be an object and is neither mutated nor persisted. Missing, null, unknown and false stay distinct. Facts are not a keyword query or a legal classifier. A FOUND result is evidence availability, not SUPPORTED_PATH or eligibility; the backend still owns scope, clarification, rule activation and response assembly.

CLI exit codes are 0 for FOUND, 1 for NO_RESULTS and 2 for ERROR. The Python function returns the wire object for expected failures instead of exposing exceptions or adding diagnostic fields to the shared contract.

## Validate citations before returning a card

```python
from rag.repository import EvidenceRepository
from rag.retriever import retrieve_evidence
from rag.citations import CitationValidationError, validate_citations

repository = EvidenceRepository()
rule_ids = ["SCT_RESIDENTIAL_SCOPE", "SCT_CLAIM_AMOUNT"]
result = retrieve_evidence("rental_deposit", rule_ids, {}, repository=repository)
if result["retrieval_status"] == "FOUND":
    evidence = result["evidence"]
    citation_ids = [entry["evidence_id"] for entry in evidence]
    validate_citations(
        "rental_deposit", rule_ids, evidence, citation_ids,
        expected_source_version=evidence[0]["source_version"],
        repository=repository,
    )
```

`CitationValidator(repository).validate(...)` is the equivalent reusable object API. Success returns None; failure raises `CitationValidationError`. The caller must handle that failure by clarification/referral/error as appropriate, rather than issue a supported result.

The validator reloads current source data and quarantine state, validates the six-field schema, rejects fabricated or duplicate IDs, checks exact source/URL/version/review metadata and reciprocal rule mappings, and requires the full requested Evidence set. Citations must list every supplied Evidence ID exactly once; a URL is not an Evidence ID. Optional expected_source_version pins the caller's response version. Evidence retrieved before a quarantine or source update will fail the later citation check.

These checks establish provenance and coverage of the selected mappings. They do not establish that arbitrary generated prose follows from a source. Use the reviewed source summaries/templates and backend rules when assembling text.

## Source quarantine

Source availability is separate from the immutable review history. Operational blocks live in `instance/rag_quarantine.json`, which is ignored by Git. The five canonical source files are untouched by quarantine, release and live checks.

```powershell
python -m rag.repository state
python -m rag.repository quarantine --source cea-complaint --actor Chu-Junjie --reason "Source requires review"
python -m rag.repository check-live --actor Chu-Junjie
python -m rag.repository release --source cea-complaint --actor Chu-Junjie --reason "Updated review and live match checked"
```

Use `--directory PATH` and `--state-file PATH` to select an isolated corpus or operational state. Actor/reason fields describe real administrative actions; do not put case answers or private dispute details there. Source state must remain outside the five-file directory. Preserve it across service restarts and source versions; deleting it is not the release procedure.

The source check compares current pages with each source's current review record and all its excerpts. A changed, unavailable or unreviewed source is quarantined. Healthy unrelated sources remain usable. Successful subsequent checks do not automatically remove a block. Explicit release requires a fresh live match to the current checked review; file changes during that check prevent release. No operation invents a review or promotes unreviewed source metadata to verified.

State writes use a temporary file and atomic replacement under an exclusive writer lock. Corrupt state fails closed instead of becoming an empty blocklist. Concurrent writes fail explicitly. An abandoned .lock file requires an operator to confirm no writer is active before recovery; the module does not guess that an existing writer is dead.

## Update the reviewed bundle

Prepare all five candidate files in a separate directory and use the Task 3 review/import procedure, including genuine source checks and review records. Policy/evidence content changes need a new source_version. A documented banner/footer recheck may retain the evidence version if passages, mappings and templates are unchanged.

```python
repository = EvidenceRepository()
new_version = repository.update_from("path/to/checked-candidate")
# Keep passing this configured repository instance to retrieval and validation.
```

`update_from` validates the complete candidate and performs live checks by default before switching this instance's source directory. An invalid candidate leaves its previous directory intact and raises `RepositoryError`; it never claims the failed version was installed. Quarantine remains effective across the switch. `verify_live=False` is an explicit offline option for already reviewed data and test fixtures, not a way to assign verified status.

Every retrieval/citation call reads current files instead of retaining a stale evidence cache. If an active directory becomes invalid, retrieval returns ERROR with no old evidence fallback. The default three-argument function always uses the canonical repository directory; a caller choosing another directory must keep passing that configured repository instance. No deployment path is changed globally by this library.

## Task boundary

Only rag/ and related tests change in this PR. The source facts, shared API fields, backend routes and frontend behavior are not edited. All existing knowledge rule activation flags remain unchanged. Connecting these real RAG functions to the backend belongs to Task 5; Task 4 tests run the module independently.
