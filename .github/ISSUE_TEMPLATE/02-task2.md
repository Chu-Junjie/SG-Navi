---
name: Task 2 - Shared contracts
about: Fix shared JSON fields before module implementation
title: 'Task 2 — Shared input and output contracts'
---

Prerequisite: Task 1 accepted. This Issue is planning only until then.

## Responsibilities

- @Chu-Junjie: shared/api_contract.json, Evidence Schema and contract tests.
- @ZhengZaikun: contract-compliant placeholders for /api/navigate, /api/health, /api/case-types and /api/version.
- @Guanyu-Lu: two input schemas, seven-block Action Card schema and Mock JSON coordinated with the shared contract owner.

## Acceptance

- [ ] One shared contract and Mock examples; all three confirm fields.
- [ ] Requests use api_version, case_type, answers; case types remain rental_deposit and consumer_complaint.
- [ ] Responses use api_version, rule_version, source_version, status, questions, action_card, evidence, warnings.
- [ ] Only NEED_CLARIFICATION, SUPPORTED_PATH, REFER_TO_OFFICIAL and ERROR statuses.
- [ ] Unknown values preserved; Evidence has evidence_id, source_id, rule_ids, url, review_status, source_version.
- [ ] Shared contract tests actually pass across module data.

Evidence: PRs, contract version, exact test commands and output. No invented legal conditions.
