# Task 6 — Zheng Zaikun Backend (BE-01–10) and HTTP E2E (E2E-01–08)

**Status:** All 18 owner tests PASS in actual GitHub Actions. **Technical-only acceptance; legal Action Card and browser interaction remain explicitly limited.** Team Task 6 cannot close solely from this owner record.

- Tested commit: `0322d13a23c4461bf53a287ffb92da558de67f04` (branch `feat/task6-backend-e2e-acceptance`).
- Tester: automated GitHub Actions `ubuntu-latest`, Python 3.12, executed **2026-11-02 14:24 UTC**; user/test author: Zheng Zaikun.
- Run: [41461565663](https://github.com/Chu-Junjie/SG-Navi/actions/runs/41461565663). Actual command: `python -m pytest tests/contracts tests/backend tests/rag tests/integration -v`; **348 passed in 3.98s**. Frontend `python -m unittest discover -s frontend/tests -v`: **27 tests OK**. Contract examples `python -m shared.validate_contracts`: **11 PASS**.
- Scope: Backend and **actual loopback HTTP integration** using `werkzeug.make_server`, `urllib.request` and real `integration.app`. E2E tests observe HTML delivery and real Flask + RAG HTTP responses; **they do not drive browser JavaScript, keyboard, layout or click outgoing official links**. Existing Task 5 browser audit remains separate.
- `rule_version` is `mock-1`: all eligibility rules deliberately disabled. Correct normal status is `REFER_TO_OFFICIAL` with source context and `action_card: null`. This does **not** establish a supported legal path. No synthetic real-world user data.

## Backend matrix — real pytest outcomes

| ID | Input | Expected | Actual on run 41461565663 | Result | Bug |
| --- | --- | --- | --- | --- | --- |
| BE-01 | GET health, case types, version | Schema-compliant 200; active source version and disabled rule version | All endpoints validated; version matched checked repository | PASS | — |
| BE-02 | Complete Rental and Consumer synthetic facts | Both use verified source context, not supported eligibility | Both returned `REFER_TO_OFFICIAL`, verified Evidence and null Action Card | PASS | — |
| BE-03 | Bad API version, bad case, non-object answers, unexpected key, invalid JSON/MIME | Reject with contract-valid 400/415 errors | All rejected without legal conclusions | PASS | — |
| BE-04 | Missing, null or unknown Rental/Consumer questions | Clarify; preserve unknown vs false, no RAG | `NEED_CLARIFICATION`, requested missing fields, retrieval not called | PASS | — |
| BE-05 | Commercial/industrial Rental; business Consumer; unregistered supplier | Out of pilot: safe referral, no RAG | All referred with warnings and no source leakage | PASS | — |
| BE-06 | Negative/non-numeric amounts and unknown field | 400 `ERROR`, no inferred amount | All invalid inputs rejected | PASS | — |
| BE-07 | Version cross-check; synthetic unreadable source/quarantine state | Current source version or 503 unavailable, no Evidence | Version agreement and safe 503 confirmed | PASS | — |
| BE-08 | RAG `NO_RESULTS` / `ERROR` / exception (synthetic injected) | Safe referral/error, no fabricated source | Warnings and empty Evidence, no Action Card | PASS | — |
| BE-09 | Malformed retrieval response, unknown RAG status, invalid citation | No invalid citation output | All fail closed | PASS | — |
| BE-10 | All disabled rule checks; attempted HTTP simulation override | No enabled legal path; unsafe override rejected 400 | Both cases remained conservative, override rejected | PASS | — |

## E2E matrix — real loopback HTTP and actual Flask/RAG

| ID | Input / request sequence | Expected | Actual on run 41461565663 | Result | Bug |
| --- | --- | --- | --- | --- | --- |
| E2E-01 | Load Task 5 HTML; Rental empty → complete landlord/residential/123 → amount edit 456 | Clarify, real API/RAG, safe source links in Evidence metadata; no fake advice | HTML 200, questions, real Evidence metadata, referral and edited result | PASS **(legal Action Card NOT IMPLEMENTED; limitation)** | — |
| E2E-02 | Consumer empty → goods/personal/registered/123 → amount edit 456 | Same sequence with real Consumer sources | Questions, validated source records, referral and edit response | PASS **(legal Action Card NOT IMPLEMENTED; limitation)** | — |
| E2E-03 | Rental amount null and `unknown` | Clarify rather than guess | Required amount question, no Evidence or Action Card | PASS | — |
| E2E-04 | Rental dispute_with null and `unknown` | Clarify landlord vs agent before routing | Asked dispute_with, no unsupported route | PASS | — |
| E2E-05 | Consumer purchase_purpose=`business` | Out-of-scope referral | Safe `REFER_TO_OFFICIAL`, no evidence | PASS | — |
| E2E-06 | Consumer supplier_registered_in_sg=`false` | Out-of-pilot referral | Safe referral, source list empty | PASS | — |
| E2E-07 | Injected `INVALID` and `NO_RESULTS` evidence | Do not expose fabricated or unverified sources | No Evidence or Action Card; safe warnings | PASS | — |
| E2E-08 | Injected backend RAG exception; then retry | Safe error and recovery | `ERROR` with no evidence; follow-up request recovered | PASS | — |

## Reproduction / review

```powershell
python -m pip install -r tests/contracts/requirements.txt
python -m shared.validate_contracts
python -m pytest tests/contracts tests/backend tests/rag tests/integration -v
python -m unittest discover -s frontend/tests -v
python -m pytest tests/backend/test_task6_be_matrix.py tests/backend/test_task6_e2e_http.py -v
```

The current GitHub workflow includes `tests/integration` with this PR, not a browser runner. The final team's browser acceptance and outbound official-link checks must be separately recorded by the coordinator; do not infer these passed from the HTTP tests alone.

## Bugs, limitations and disposition

- **New BE/E2E test failures:** none in the successful 2026-11-02 CI run. No backend implementation changes were needed to make those tests pass.
- **Tested supported legal Action Card:** **Not Run / unavailable by design** (all real rule activation disabled), explicitly bounded for E2E-01/02. An Action Card generated only by synthetic direct engine simulation is *not* evidence of a real supported route. The seven existing UI sections and genuine sources can still be presented in the conservative referral.
- **Real browser JavaScript or outgoing URL clicks:** **Not Run in this PR**; previous separate Task 5 browser audit exists and must not be misrepresented as this Task 6 run.
- **CI integration:** `.github/workflows/test.yml` now runs `tests/integration` in addition to backend/contracts/RAG and frontend. Node/Edge browser-based checks and formal Test 6 group owner closeout remain separate.
- Team gate: require Guanyu FE-01–08 and Junjie RAG-01–12 acceptance, peer review of this PR, merged code, and coordinator decision on explicitly accepted legal-path limitations before Task 7.
