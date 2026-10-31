# Shared API contract for Task 2

`api_contract.json` is the single canonical JSON Schema for the API 1.0 wire envelope. `schemas/evidence_schema.json` is its shared Evidence definition. No endpoint, form, retrieval algorithm or legal rule is implemented here.

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

## Handoff and remaining work

Lu Guanyu owns the two input schemas and detailed Action Card schema. The shared envelope fixes the seven card names (`case_summary`, `potential_channels`, `conditions`, `steps`, `document_checklist`, `unresolved_questions`, `citations`); section contents are intentionally unconstrained until his schema is agreed. This PR does not claim full Action Card content validation. Refine or reference those schemas here after agreement instead of maintaining a second conflicting contract.

Zheng Zaikun owns endpoint stubs and CI. `tests/contracts/requirements.txt` layers validator dependencies on the root requirements without changing his dependency file. The existing Task 1 workflow runs backend and homepage tests only. It does not yet install these extra dependencies or run the contract tests; the CI owner should add the install and validation commands above.

Task 2 remains open until the other module owners use this contract, their corresponding schemas and Mock data pass it, and all three confirm the fields through review. Task 1's outstanding acceptance records are not automatically completed by this Task 2 work.
