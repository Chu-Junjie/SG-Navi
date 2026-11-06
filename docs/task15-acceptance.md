# Task 15: integrated conditional research MVP

Issue [#75](https://github.com/Chu-Junjie/SG-Navi/issues/75). Coordinator: Chu Junjie.
Tasks 13 and 14 are merged in #82 and #84; Zheng's Task 14 backend is merged in #83.
Guanyu's Task 10 continuation #85 was separately approved by Chu-Junjie, passed
both CI workflows and merged at `bb540ebdd9d00ff9313b9b3504b5589f6aeda1bf`.
Its existing Task 9 result/source viewer is retained alongside the new home-page
workflow. The shared API allowlist merge retains all endpoints from both changes.
The owner authorized cross-module implementation and merging without waiting for
peer approval. Reviewer requests remain part of the PR record; no automated run
or owner waiver is described as a teammate's human approval.

## Accepted scope and version boundary

The new home-page workflow uses real `/api/intake`, `/api/intake/confirm`, and
`POST /api/guidance`. The frozen additive contract is
[`shared/guidance_contract.json`](../shared/guidance_contract.json), version 1.0.
It composes actual Task 11 interpretation, Task 12 approved templates, Task 13
query-aware ranking and Task 14 final display/citation checks. The original v1
`/api/navigate`, old guided-form links, six-field Evidence and null Action Card
remain compatible. No legal rule was enabled: `rule_version: mock-1`, all 25
backend legal checks disabled and all 26 RAG mappings disabled.

`GUIDANCE_ONLY` means conditional official-source research and preparation. It
does not establish eligibility, a deadline, a fee payable, entitlement to file,
legal correctness for a real dispute, or production authorization. Unknown/null
answers stay unresolved. Business/non-SG/unsupported situations safely refer;
quarantined, unavailable or changed evidence cannot retain a verified result.

The UI requires explicit category/fact confirmation, asks only missing relevant
questions, and invalidates old results on edits. Every procedural item selects
its exact supporting quote/publisher/review identity/source link. SG Navi
explanations and source locators are labelled separately. Available surrounding
context is visible; no publisher screenshot or text anchor is fabricated.
Matched references are prioritized without truncating complete support records
(nine rental records, twelve consumer records in the standard examples).

## Frozen forty-case engineering acceptance

Inputs were committed **before integration execution or implementation changes**
at `512ef295e1fee158d7f40a1e035179516dfbc75b`. The LF-normalized fixture digest is
`1e118a331a3766a9f97f35a1005832daff9f50087a041eb6e1e6e65b73e50d29`.
No intake classifier was fitted to these cases. Scoring is
`task15-provenance-routing-1`, fixture version `task15-heldout-1`.

| Initial measure | Actual | Required |
| --- | --- | --- |
| Rental routing | 14/15 | >=14/15 |
| Consumer routing | 15/15 | >=14/15 |
| Boundaries | 10/10 | 10/10 |
| Overall routing | 39/40 | >=38/40 |
| Procedural assertion provenance | 206/206 | >=95%, consequential 100% |
| Mean mandatory checklist, rental / consumer | 93.33% / 100% | >=90% each |
| Observed critical failures | 0 | 0 |

[The immutable initial report](test-results/task15-heldout-initial.json) retains
per-case inputs, expectations, actual outcomes/response hashes, Evidence IDs,
scoring version and defect IDs. [Independent source-family audit](test-results/task15-initial-source-family-audit.json)
checks actual IDs against the frozen expected family. Later CI executions are
regressions on the same cases, not fresh held-out evaluations.

The retained miss R12 contains `estate-agent` with a hyphen; existing intake
safely returns `cannot_determine` instead of forcing a category. It counts as
failed routing and zero checklist coverage. Actual browser testing additionally
demonstrates explicit manual correction to Rental Deposit + agent, followed by
CEA-only conduct guidance. This recovery does not change the initial score.

Support scoring verifies identity with approved editorial templates and current
exact quote hashes. It is not independent expert legal-entailment validation.
No free-form generated legal assertions or enabled eligibility decisions are
evaluated. Legal/production acceptance remains **LIMITED** even when every
engineering gate passes. No external user research or physical-phone test is
claimed.

## Executed validation and evidence

The initial suite ran at `2026-11-06T12:50:57Z`. Five official pages were checked
again read-only at `2026-11-06T13:25:15Z`: five HTTP 200 responses, all recorded
body hashes and all 26 excerpts matched. [Actual report](test-results/task15-live-source-check.json).
This does not erase the earlier cloud CASE 403 or guarantee future availability.
Source version remains `kb-2026-11-01.1`; display context version remains
`display-context-2026-11-06.1`. No review timestamps/hashes were promoted.

Actual Edge tests exercise 18 main-case steps and five additional boundaries:
manual correction, real 27-second transport latency versus the app's 25-second
timeout, late-request cancellation on edit, unsupported topic and executable
markup treated as literal text. Offline retry preserves answers. Four real
1440/390-pixel captures are saved; 320-pixel overflow is checked. No intercepted
API replies are used. No JavaScript exceptions were observed. Mobile tests use
browser emulation; external publisher tabs were not opened.

The first browser run failed in the CDP keyboard driver before submitting a
request; Enter dispatch and listener readiness were corrected. The first full
regression reported 686 passed, four skipped and two homepage subtest failures
because a brittle string assertion omitted the new initial `disabled` attribute.
That assertion now requires the privacy-preserving initial disabled state.
These failures are retained, not described as passing runs.

Final combined local regression after #85: **689 passed, four skipped, 15
subtests passed in 121.92 seconds**, using the full command above. The earlier
pre-#85 pass was 686/four/15 in 115.14 seconds. Three skips require disposable
PostgreSQL; the fourth is the older opt-in public browser test. They are not
counted as passes. All twelve shared v1 examples and `pip check` passed.
The actual application delivery is [PR #86](https://github.com/Chu-Junjie/SG-Navi/pull/86).
Tested combined head `ab17ed1807395def24d0116aafd99ff5d0ca3fee` passed
[ordinary CI](https://github.com/Chu-Junjie/SG-Navi/actions/runs/42227170134)
(634 passed/three skipped, frontend 56 tests/one skipped) and
[isolated PostgreSQL CI](https://github.com/Chu-Junjie/SG-Navi/actions/runs/42227170029).
The final merged application commit is `c30b1209ef2f92bd06066818dae6b06e9f18e38c`;
its tree exactly matches the tested combined tree
`3b744ddf1adc7c6af0840ebe5d37161f9ab6b2fb`. Its
[main ordinary CI](https://github.com/Chu-Junjie/SG-Navi/actions/runs/42227462585),
[PG CI](https://github.com/Chu-Junjie/SG-Navi/actions/runs/42227462518),
[legacy HTTPS smoke](https://github.com/Chu-Junjie/SG-Navi/actions/runs/42227462589)
and [Pages publication](https://github.com/Chu-Junjie/SG-Navi/actions/runs/42227461928)
all succeeded.

### Actual published acceptance and retained checker failure

Render provider deploy `dep-dbmthq6c6qcc73bhpi20` reached **live** at
`2026-11-06T13:41:45Z` on that exact merged application commit, health path
`/api/health`, existing Free service, existing Neon-backed mode. No cloud setting,
database state or secret was changed. The published Task 15 frontend bytes
matched the checked file (LF SHA-256
`48a789f100a4a438e53f7377787ebd7469da5b702ee7b19601c6597887333097`).

[Actual public HTTP checks and selected request/response samples](test-results/task15-public-http.json)
passed five checks at `2026-11-06T13:44:35Z`, including both real intake/confirm/
guidance paths, nine/twelve exact quote records, stale revision rejection,
unconfirmed rejection, Neon-backed mode and CORS. Samples are explicitly selected
fields from actual responses with a full canonical-response digest.

The [first public CI run](https://github.com/Chu-Junjie/SG-Navi/actions/runs/42227462719)
**failed** after seven rental steps because the test driver incorrectly required
every captured request to be POST. The same-origin local suite did not expose
the browser's normal cross-origin OPTIONS preflight. Its genuine artifact
`13506212895` and [workstation failure report](test-results/task15-public-first-failure.json)
are preserved. This failure was not called an application or CORS success.

The checker now separately validates data-bearing POSTs and empty-body OPTIONS
preflights, with the same required API origin and no query parameters. It still
rejects every other method/origin and requires three or more actual data calls.
No application behavior, score, fixture or API reply was changed to pass it.
The corrected driver passed the real same-origin regression again (one test in
40.20 seconds).

[Corrected actual public Edge report](test-results/task15-public-browser.json)
passed at `2026-11-06T13:49:48Z`: **18 main journey steps, five boundaries,
four actual desktop/mobile captures, zero JavaScript exceptions**. It includes
real offline/25-second-timeout recovery, late-request cancellation, explicit
unknown handling and exact selected-source verification. The report identifies
the driver content hash and honestly labels the not-yet-committed harness as a
working tree derived from the accepted application commit. All application bytes
were already published. This is separate evidence from the failed CI run.

The closeout PR publishes that tested harness correction and these reports;
ordinary, disposable-PG and published-browser CI re-execute on its final commit.
[Issue #75](https://github.com/Chu-Junjie/SG-Navi/issues/75) records their actual
final run IDs, provider reconciliation and completion after those executions.
Workflow artifacts contain the actual screenshots (public retention 30 days);
their content hashes also remain in the committed reports. Local originals are
under ignored `instance/task15-browser-public/`. No physical-phone test or
outgoing publisher-tab navigation is claimed.

Health=200 alone is insufficient. The public workflow waits for
the exact checked frontend bytes and the new API before real browser testing.
Its SHA identifies the test checkout; the Render provider record separately
identifies the deployed server commit.

## Reproduce and operate

From an installed environment (Task 15 reused the audited environment; it is
not another teammate's independent fresh installation):

```powershell
python -m pip install -r tests/contracts/requirements.txt
python -m shared.validate_contracts
python -X utf8 -m pytest tests/contracts tests/backend frontend/tests tests/rag tests/integration -q -rs
python -m flask --app integration.app run --host 127.0.0.1 --port 5000
```

The install command uses the existing manifest; this iteration ran `pip check`
successfully instead of claiming a fresh install. Actual local Flask HTTP is
started by the browser test. Open `/`, enter a made-up English issue, confirm
the proposed facts, answer remaining questions, then select a step. Old topic
buttons still open the conservative v1 form. Real local and public browser
scripts require Node 22+ (CI pins 24) and Edge/Chrome/Chromium.

```powershell
python -m backend.smoke_guidance --output instance/task15-public-http.json
node frontend/tests/task15_browser_check.mjs https://chu-junjie.github.io/SG-Navi/ "C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe"
```

These public checks send synthetic facts to the actual existing Render API.
They never mutate production quarantine or insert disputes into Neon. API
responses and screenshots are workflow artifacts; no credentials or full
publisher captures are committed. Failure injection uses isolated local state;
the existing durability workflow uses disposable CI PostgreSQL. No new paid
resource, database branch or service is required.

Render is Free and may sleep. Retry after warm-up; source state failures must
be investigated rather than bypassed. The application's structured answers and
problem text stay in tab memory, never local/session storage or URL query
parameters. Requests necessarily transmit the synthetic input to the API;
this is not a promise about provider-level operational logging. Do not submit
real dispute details. The old candidate tag `v0.9.0-rc1` stays unchanged.
