# Task 5 acceptance — integrated source-context flows

Decision: **PASS for the technical integration stage.** The closeout PR records
acceptance and closes Issue #5 on merge after another developer's review.

Audited main: `913304e48dd3164d7369d38c1767ac915d644e6b`, 2026-11-02.
Automated audit performed through Codex on Windows, Python 3.14.6, Node 24.18.0
and headless Microsoft Edge. Only synthetic facts were used. This record is not
a claim that the three members each installed or manually tested the project.

## Acceptance evidence

| Gate | Actual evidence | Result |
| --- | --- | --- |
| Task 4 prerequisite | Independent modules #23-25 and closeout #26 merged; [Task 4 record](task4-checklist.md) | Pass |
| Backend + real RAG | `python -m integration.checks`: both case types call the real retrieval function once, return FOUND and preserve exact synthetic facts; direct corpus/citation checks also pass | Pass |
| Source-version agreement | GET version, navigation and RAG agree on `kb-2026-11-01.1`; `rule_version: mock-1` accurately identifies the still-disabled rule implementation | Pass |
| Rental browser → API → RAG source context | Blank facts → questions → focus correct field → completed request → safe referral with 2 Evidence records → edited amount resubmitted; 3 real POSTs, no Mock responses | Pass |
| Consumer browser → API → RAG source context | Same sequence, with its own schema and 2 real Evidence records; 3 real POSTs | Pass |
| Source presentation | Both actual pages expose links matching the returned source URLs; referral keeps null legal Action Card and seven card sections | Pass |
| Unknown and scope handling | Supplemental real-browser run preserves unknown and false distinctly; unknown prompts clarification, false registration and business purpose refer without invented evidence | Pass |
| Missing, invalid or unavailable evidence | Backend and RAG regression tests exercise NO_RESULTS/ERROR, malformed records, wrong versions/citations, quarantine and exceptions; frontend Node tests reject unsafe/mixed source metadata | Pass |
| Transport failure and editing | Real-browser request blocking produces Service unavailable, clears stale links and preserves answers; removing the block permits a successful retry. Editing clears earlier sources immediately | Pass |
| Mobile source context | Real Edge at 390 px: visible source links, no horizontal page overflow; full-page capture visually inspected | Pass |
| Regression | UTF-8-mode full suite: 346 passed, 7 subtests passed in 33.46s | Pass with documented Windows run configuration |

The browser check observes real HTTP requests and never supplies fixture API
responses. RAG invocation is additionally observed in-process by a delegating
call observer, while backend tests check real corpus validation. These are
complementary checks, not a distributed trace of each browser request.

## Owner fixes and review

| Work | Merged PR | Verified peer approvals | Successful CI |
| --- | --- | --- | --- |
| Version reporting, resolves #29 | [#34](https://github.com/Chu-Junjie/SG-Navi/pull/34) | Chu-Junjie, Guanyu-Lu | [41425885823](https://github.com/Chu-Junjie/SG-Navi/actions/runs/41425885823) |
| Frontend source context, part of #30 | [#36](https://github.com/Chu-Junjie/SG-Navi/pull/36) | Chu-Junjie, ZhengZaikun | [41428357920](https://github.com/Chu-Junjie/SG-Navi/actions/runs/41428357920) |
| Backend source exposure, completes #30 | [#37](https://github.com/Chu-Junjie/SG-Navi/pull/37) | Chu-Junjie, Guanyu-Lu | [41429175319](https://github.com/Chu-Junjie/SG-Navi/actions/runs/41429175319) |

Original module integration #27/#28 and coordinator #33 are merged. Superseded
backend #35 is not used in the accepted main. Issues #29, #30 and the historical
test conflict #31 are closed. The formerly failing diagnostics were rerun on the
merged code; closed Issue labels alone were not treated as proof of a fix.

## Exact commands and results

Run from the repository root in the existing environment:

```powershell
python -X utf8 -m pytest tests/contracts tests/backend frontend/tests tests/rag tests/integration -q
python -m shared.validate_contracts
python -m rag.import_knowledge_base
python -m integration.checks
```

Results: **346 passed, 7 subtests passed in 33.46s**; all 11 shared examples passed;
5 sources, 26 passages, 26 rule mappings and 5 templates passed offline import;
all five real-RAG/version diagnostic checks passed with exit 0.

Start the actual local integration origin, then run the browser check in another
terminal (the audit used port 5055):

```powershell
python -m flask --app integration.app run --host 127.0.0.1 --port 5055
node integration/browser_check.mjs http://127.0.0.1:5055
```

Open http://127.0.0.1:5055/task5-flow.html. Both browser scenarios passed with exit
0 and zero JavaScript exceptions. The supplemental local browser script also
passed all seven extra checks; its reproducible interactions are recorded below.
The installed dependency file remains `tests/contracts/requirements.txt`:
`python -m pip install -r tests/contracts/requirements.txt`. Installation was not
rerun and no dependency or CI configuration was changed for this closeout.

Machine-readable results:

- [Audit commands, environment and initial failure](test-results/task5-closeout-audit.json)
- [Backend/RAG and versions](test-results/task5-closeout-backend-rag.json)
- [Two browser flows](test-results/task5-closeout-browser.json)
- [Supplemental browser results](test-results/task5-closeout-browser-extra.json)

## Supplemental browser reproduction

After the standard Consumer flow has returned its real source context:

1. Use a 390 px viewport. Confirm the source panel and both links are visible and
   the page does not scroll horizontally. This capture was visually inspected.
2. Set supplier registration to Unknown. Confirm earlier links clear immediately;
   submit and inspect the real request's `unknown` value and clarification response.
3. Select No and resubmit. Confirm false is preserved, the backend returns a safe
   referral and no Evidence. Select Yes, set purchase purpose to business and
   confirm another evidence-free scope referral.
4. Restore personal purpose and submit. Edit amount to 789. Block the browser's
   request to `/api/navigate` and submit; confirm Service unavailable, no stale
   links and retained answers. This simulates transport failure, not a stopped
   backend process or a fabricated API error response.
5. Remove request blocking and submit again. Confirm the real request still has
   amount 789 and the actual response restores two verified source records.

The extra script was derived locally from the existing browser harness and kept
under ignored `instance/`; the interactions above allow independent reproduction.
No frontend/backend production code was edited during this audit.

## Boundaries and remaining work

- The first plain `python -m pytest ...` run failed in the frontend Node-output
  reader: Windows GBK could not decode UTF-8 Node output. Actual outcome was
  1 failed, 345 passed, 1 warning and 7 subtests passed in 37.29s. Running Python
  with `-X utf8` resolves this configuration issue without editing owner files.
  Windows test commands now document that mode; the reader's default-encoding
  portability is tracked in [#38](https://github.com/Chu-Junjie/SG-Navi/issues/38)
  for its frontend owner. This does not block the documented UTF-8 configuration.
- Normal flows remain clarification/referral with reviewed source context.
  `FOUND` is not legal eligibility; runtime legal rules stay disabled. No real
  SUPPORTED_PATH, legal recommendation or filing was claimed. All seven sections
  render, with unavailable advice still marked Needs verification.
- Automated source review is not official or human legal approval. No new live
  publisher capture or external source-link click-through was performed here.
- Existing CI covers backend/RAG/contracts and frontend tests, but still omits
  `tests/integration` and the Edge diagnostics; these were run locally for this
  acceptance. Workflow changes remain with the CI owner.
- Task 6's complete formal test matrix, clean-environment member runs, deployment
  and candidate handover are not completed by this Task 5 record.

All required Task 5 integration connections and the two recorded blocking
mismatches now pass. This acceptance keeps the limitations above explicit and
does not start Task 6 automatically.
