# Task 7 — internal candidate release and handover

**Technical acceptance: PASS WITH LIMITS. Publication: PENDING post-merge checks.**

On 2026-11-05 the owner delegated the remaining backend, frontend, integration
and release work to the coordinator and authorized merging without waiting for
another approval. This is a single-operator internal-candidate handover. The
original all-three-personal-environments criterion is not fully evidenced;
Zheng's missing personal results remain unfilled rather than invented.

## Identity and actual evidence

- Implementation: `2d14ed5a612d35e35e1f6b9cb0a5fca0c6333d87`, [PR #66](https://github.com/Chu-Junjie/SG-Navi/pull/66).
- Fresh clone and isolated Windows venv: install/pip check exit 0; **481 passed,
  4 skipped, 13 subtests in 51.12s**. Actual Flask CLI startup, five GETs and
  both synthetic navigation POSTs passed. [Machine record](test-results/task7-final-candidate-20261105.json).
- Separate actual disposable PostgreSQL CI: [42014879380](https://github.com/Chu-Junjie/SG-Navi/actions/runs/42014879380), **3 passed in 4.93s**.
- Actual local browser: Rental and Consumer, **18/18 technical steps**, four
  desktop/mobile screenshots, zero JS exceptions. Final public execution is
  recorded separately after deployment.
- Five official URLs and all 26 excerpts/current full-page hashes matched the
  recorded independent snapshot. Separate requests can still time out; previous
  runner CASE 403 is a known access limitation. Failed checks remain failures.
- API **1.0**, rule **mock-1**, source **kb-2026-11-01.1**; five corpus files,
  five sources, 26 passages/mappings, five templates, nine review rows. No legal
  rule is enabled, normal `action_card` is null.
- Intended immutable tag: **v0.9.0-rc1**, created only after merge and final
  public verification. The actual tag/release metadata pins the merge commit;
  a checked-in document cannot contain its own future merge SHA.

## Reproduce after the candidate tag is published

These commands use the existing verified installation/start interface. The exact
executed fresh-checkout commands and results are in the machine record above.

```powershell
git clone https://github.com/Chu-Junjie/SG-Navi.git
cd SG-Navi
git checkout --detach v0.9.0-rc1
git rev-parse HEAD
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r tests/contracts/requirements.txt
.\.venv\Scripts\python.exe -m pip check
.\.venv\Scripts\python.exe -m shared.validate_contracts
.\.venv\Scripts\python.exe -m rag.import_knowledge_base
.\.venv\Scripts\python.exe -m integration.checks
.\.venv\Scripts\python.exe -X utf8 -m pytest tests/contracts tests/backend frontend/tests tests/rag tests/integration -q -rs
.\.venv\Scripts\python.exe -m flask --app integration.app run --host 127.0.0.1 --port 5000
```

Open `http://127.0.0.1:5000/`. Python 3.12+, Node 22+ and an installed
Chromium/Edge/Chrome are required to run the full browser coverage. On Linux,
use `.venv/bin/python` instead of the Windows executable. Local development
needs no API key, `.env` or production database credential. Requirements use
ranges; the actual resolved versions are recorded, not a cross-platform lockfile.

## Public deployment and operator recovery

- [Public Pages](https://chu-junjie.github.io/SG-Navi/) uses
  [the Render API](https://sg-navi-api-junjie.onrender.com).
- Existing Render service: `srv-dbluspoae00c73fqp4v0`, Free, Singapore, main
  auto-deploy enabled, health check **/api/health** (actual configuration read back).
- Source/state dependency failure returns **503/unavailable**. The homepage
  only reports Ready when it receives exact valid `status: ok`.
- [Active Render + Neon runbook](task7-junjie-render-neon-integration.md) describes
  current configuration. Do not sync historical paid/ephemeral Blueprints to
  the existing service.
- [Verified persistence and encrypted recovery](task7-state-recovery.md) gives
  the actual isolated hosted redeploy/export/restore drill and safe operator
  commands. Keys and credentials stay outside Git; the production database was
  not used for synthetic recovery writes.
- Roll back application code by manually deploying the previously recorded
  known-good commit in Render and verifying `/api/health`, `/api/version` and
  both synthetic scenarios. Revert Pages through a new PR if frontend rollback
  is needed. This is an operator procedure, not a claim that a production
  rollback was performed. Database state is recovered separately through the
  guarded archive procedure; never reset production to test a rollback.

## Known limits accepted for this internal candidate

1. Legal eligibility and populated supported legal Action Cards remain
   unavailable. Seven-section layout tests do not prove a real legal route.
2. The original three-person final clean-environment gate is incompletely
   evidenced. This delivery uses the owner's explicit single-operator scope;
   neither CI nor coordinator runs are renamed as Zheng's personal tests.
3. Official sources can time out or reject a GitHub runner (CASE 403). The
   read-only monitor keeps strict hash/excerpt checks and fails on uncertainty;
   it does not auto-renew evidence or suppress failed results. The independently
   verified source snapshot supports the limited source-context demo only.
4. Mobile emulation is not a physical-phone audit. Official publisher URLs and
   safe link attributes were checked; external publisher tabs were not audited.
5. Free services can sleep or be unavailable. The recovery drill is a tested
   snapshot procedure, not scheduled backups, off-machine key escrow or a
   provider disaster-recovery guarantee. Isolated Free test resources remain
   separate; no paid resource was created.

The earlier local-only preparation document is retained in Git history. Current
acceptance is in [integration_acceptance.md](../integration_acceptance.md);
release metadata and final public artifacts provide the actual delivery SHA.
