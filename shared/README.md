# Shared API contract for Task 2

`api_contract.json` is the single canonical JSON Schema for the API 1.0 wire envelope. `schemas/evidence_schema.json` is its shared Evidence definition. No endpoint, form, retrieval algorithm or legal rule is implemented here.

`query_retrieval_contract.json` defines the **separate internal query-RAG 1.0**
protocol added in [Task 13](../rag/TASK13.md). It reuses the existing case input
schemas and six-field Evidence contract using local-only resolution. It is not
a new `/api/navigate` version, endpoint or legal decision status. Validate its
output with `rag.query_retriever.validate_query_result`; the old validator and
12-example manifest remain unchanged.

`display_evidence_contract.json` approves the additive Task 14 backend display
record and optional source-owner context extension. It keeps exact official
quotation separate from SG Navi summary and descriptive locator, and requires
`preview: null` until a genuine official-source capture exists. Structural
validation alone does not establish provenance: use the [Task 14 final source
boundary](../rag/TASK14.md) before publishing an enriched viewer result.

## Install and validate

Run from the repository root with Python 3.12 or newer:

```powershell
python -m pip install -r tests/contracts/requirements.txt
python -m shared.validate_contracts
python -m pytest tests/contracts -v
```

The first validation command checks all examples in `examples/manifest.json`. To check another file:

```powershell
python -m shared.validate_contracts shared/examples/rental_deposit_request.json --definition navigate_request
```

Other modules can reuse the exact same validators:

```python
from shared.validate_contracts import validate

validate(request_payload, "navigate_request")
validate(response_payload, "navigate_response")
validate(evidence_record, "evidence")
```

Validators raise `jsonschema.ValidationError` without mutating or coercing the payload. All schema references resolve from local files; `.invalid` schema IDs are identifiers, not websites to fetch. Format checking is enabled by the helper. Other JSON Schema implementations must enable URI format assertions too.

## Endpoint mapping

| Endpoint or boundary | Named definition in api_contract.json |
| --- | --- |
| POST /api/navigate request | navigate_request |
| POST /api/navigate response | navigate_response (also the root default) |
| GET /api/health response | health_response |
| GET /api/case-types response | case_types_response |
| GET /api/version response | version_response |
| retrieve_evidence(case_type, rule_ids, facts) arguments | retrieval_request |
| retrieve_evidence return value | retrieval_response |

Health keeps Task 1's existing `{"status":"ok"}` shape. Case types return `api_version` and the two case-type strings. Version returns `api_version`, `rule_version`, `source_version`. The backend owner implements these endpoints against the contract; only health exists in the current baseline.

## Fixed navigation envelope

- Request fields: `api_version`, `case_type`, `answers` only. `api_version` is the string `"1.0"`. Case type is `rental_deposit` or `consumer_complaint`.
- Response fields: `api_version`, `rule_version`, `source_version`, `status`, `questions`, `action_card`, `evidence`, `warnings` only. Rule/source versions are nonblank strings, independent of the API version.
- Each question has `id`, `label`, `input_type`, `required`. `input_type` is a nonblank string; the frontend owner confirms supported controls in the input schemas. Warnings are plain English strings.
- Unknown facts remain absent, `null`, or a schema-defined `unknown`; never turn unknown into `false`. `answers` and RAG `facts` remain objects whose field validation belongs to the two case-specific schemas. The envelope validator deliberately does not assess their legal meaning or validate individual answer types.

| Navigation status | Required behavior of the payload |
| --- | --- |
| NEED_CLARIFICATION | At least one question; action_card is null |
| SUPPORTED_PATH | No questions; seven-section card; at least one verified Evidence record |
| REFER_TO_OFFICIAL | No questions; at least one warning; nullable card |
| ERROR | No questions; at least one warning; action_card is null |

Any nonnull card, including a referral card, needs at least one verified Evidence record. No fifth navigation status is permitted. `retrieval_status` is a separate nonblank string whose vocabulary is left for RAG confirmation; it must not be copied into navigation `status`.

## Evidence and mock data

Every Evidence record requires exactly `evidence_id`, `source_id`, `rule_ids`, `url`, `review_status`, `source_version`. IDs and versions must be nonblank, rule IDs are a nonempty unique list, and URLs must be absolute HTTP(S) URIs. Review states are `unreviewed`, `verified`, `quarantined`; these are application review states, not government approval.

All examples are synthetic. `mock-*` IDs and versions, reserved `example.invalid` URLs and the mock `verified` value exercise validation branches only. They are not official passages, source reviews, usable citations or eligibility decisions. Do not import them into a production knowledge base. Schema validation cannot prove a source was really reviewed, that Evidence IDs are unique across a dataset, that versions agree across modules, or that citations match rules; those checks belong to the later evidence validator.

## Readiness status (Task 7)

`GET /api/health` validates the same checked source bundle and operational state
used by navigation. It returns HTTP 200 with `{"status":"ok"}` when ready,
or HTTP 503 with `{"status":"unavailable"}` when critical state cannot be
validated. Both payloads use `health_response`; the two examples are in the
manifest. No connection details or source-state contents appear in the response.
Clients must require a successful HTTP status and the exact `ok` value before
showing that submissions are available. API version 1.0 and the successful
health payload are unchanged.

## Historical Task 2 handoff

Lu Guanyu owns the two input schemas and detailed Action Card schema. The shared envelope fixes the seven card names (`case_summary`, `potential_channels`, `conditions`, `steps`, `document_checklist`, `unresolved_questions`, `citations`); section contents are intentionally unconstrained until his schema is agreed. This PR does not claim full Action Card content validation. Refine or reference those schemas here after agreement instead of maintaining a second conflicting contract.

Zheng Zaikun owns the backend and CI. `tests/contracts/requirements.txt` layers
validator dependencies on the root requirements. Current CI installs them and
validates the shared examples before the backend/RAG/frontend tests.

The original Task 2 implementation/acceptance is historical. Current source,
deployment and release decisions are recorded in the root
`integration_acceptance.md`; these mock examples do not grant legal approval.
# Task 15 integration envelope

`guidance_contract.json` freezes additive `guidance_version: 1.0` for `POST /api/guidance`.
The request requires explicit confirmation, supported case facts and the exact revision
returned by `/api/intake/confirm`. Answers edited since confirmation are rejected.
The response distinguishes clarification, conditional research, limited referral and
error; only `GUIDANCE_ONLY` can contain the complete Task 14 display records and
claim citations. v1 `/api/navigate` is unchanged. No legal Action Card is activated.
See [integration acceptance](../docs/task15-acceptance.md) and `validate_guidance.py`.

## Task 16 action plan

[`action_plan_contract.json`](action_plan_contract.json) specifies the additive
action plan 1.0 request, confirmation, question, result and evidence envelopes.
See the [design and handoff](../docs/task16-action-first-design.md), the labelled
[wire examples](examples/task16_action_plan.json) and `validate_action_plan.py`.
The service implementation and live transition are tracked separately.
