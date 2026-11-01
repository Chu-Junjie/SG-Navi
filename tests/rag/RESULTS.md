# Task 3 source preparation validation

Executed on 2026-11-01 in the owner's local Windows workspace, based on main commit `0840522121be8f5ef31e1a45cba62768adbc4a03`. Environment: Python 3.14.6, pytest 9.1.1, jsonschema 4.26.0 and referencing 0.37.0.

| Check | Actual result |
| --- | --- |
| `python -m pytest tests/contracts tests/backend frontend/tests tests/rag -q` | **169 passed in 10.46 seconds**: 44 new ingestion tests plus 125 existing checks |
| `python -m rag.import_knowledge_base` | Passed: 5 sources, 26 passages, 26 rule mappings, 5 templates |
| `python -m rag.import_knowledge_base --verify-live` | All 5 pages HTTP 200; 6/5/5/4/6 excerpts matched their source pages and the recorded page fingerprints |
| `python -m rag.import_knowledge_base --output instance/task3-kb-final.json` | New validated snapshot created successfully; instance/ export is ignored by Git |

The five source files contain actual capture/review times and fingerprints. Reviewer identity is explicitly Codex's automated page and excerpt check, not a human or official approval. All 26 runtime rule activation flags remain false. Summaries are editorial; only the short text excerpts are original quotations.

Negative tests verify rejection of missing files, duplicate IDs, absent/untrusted URLs, bad references, inconsistent cases/versions, invalid review dates, failed HTTP review results, forged excerpt edits using old review digests, unreviewed/quarantined evidence on usable mappings/templates and changed live content. Export tests confirm that invalid bundles create no output and existing output is preserved.

Tests and live checks do not establish legal eligibility, validate a real dispute, execute the future Rule Engine, retrieve evidence for an API call or perform the teammates' Task 3 work. Existing CI does not run tests/rag/ yet; these 44 new tests are local results. The CI owner should add the documented RAG test command.
