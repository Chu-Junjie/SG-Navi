# Task 6 provenance and state integrity

The retrieval and citation APIs in [Task 4 usage](TASK4.md) are unchanged.
Task 5 closeout #39 is merged. Task 6 adds strict current-review binding and
quarantine-history consistency, plus [RAG-01–12 results](../docs/task6-rag-results.md).

## Current review proof

Verified passages and live page fingerprints must match the source's recorded
current `source_id`, version, `reviewed_at` and `reviewed_by`. An old successful
same-version record cannot override the current review. If multiple rows identify
the same current review, their page fingerprint and Evidence-ID/excerpt-digest map
must agree. Contradictory current proof makes the bundle invalid.

Historical rows remain in the log. No review is invented, renewed or promoted by
loading/retrieving evidence. A genuine publisher/content change still needs the
existing review/update workflow. Current source facts and all disabled rule flags
were left unchanged by this fix.

## Quarantine history

The state loader replays recorded quarantine/release events and compares the
resulting complete entries with `blocked_sources`. Release needs a preceding
quarantine. Missing history, missing blocks, inconsistent actor/reason/version/time
or an orphan release is corrupt state. Retrieval returns ERROR with no Evidence;
citation checking rejects previously returned records. State format stays at 1.

The module does not silently repair, reset or release inconsistent state. Preserve
the original state file, identify the actual inconsistency and recover from a
known consistent copy after owner review. Follow the explicit fresh-check release
procedure when a source is genuinely ready. Do not delete state to bypass a block.
This validates internal consistency; it does not authenticate edited audit files
or prove legal correctness of source text.

## Repeat RAG acceptance

```powershell
python -m pip install -r tests/contracts/requirements.txt
python -X utf8 tests/rag/run_task6.py
```

The runner executes all RAG tests once, reads actual pytest JUnit outcomes, and
maps them to [the explicit 12-group manifest](../tests/rag/task6_matrix.json).
It records Input/Expected/Actual/status, the base commit, exact code hashes, tester,
UTC execution time and Bug Issues. Missing/skipped selectors cannot become PASS.
Any suite failure or mutation of the five canonical files fails the overall run.
Default output and raw pytest artifacts stay under ignored `instance/`.

Publish a synthetic result record only when intentionally requested:

```powershell
python -X utf8 tests/rag/run_task6.py --output docs/test-results/task6-rag-results.json
```

Report destinations are restricted to JSON under `instance/` or
`docs/test-results/`. The runner performs no publisher network check; use
`python -m rag.import_knowledge_base --verify-live` separately. Twenty-six passages
still use exact lookup without FTS5/vector storage. Rebuild acceptance covers
validated snapshot export/reload and failed-update preservation.
