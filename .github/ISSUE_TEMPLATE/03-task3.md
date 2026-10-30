---
name: Task 3 - Verified sources and mappings
about: Build the official-source knowledge base and traceable rule skeleton
title: 'Task 3 — Verified knowledge base and rule mapping'
---

Prerequisite: Task 2 accepted.

## Responsibilities

- @Chu-Junjie: rag/knowledge_base/ sources.csv, passages.jsonl, rule_evidence_map.json, action_templates.json and source_review_log.csv; import validation.
- @ZhengZaikun: Rental, Consumer and Boundary rule configuration with unverified thresholds disabled; basic tests.
- @Guanyu-Lu: map both cases' inputs and seven Action Card sections, including citations and unresolved conditions.

Register and verify the five guide sources: Courts SCT eligibility, Courts filing, CEA dispute resolution, CEA complaints and CASE complaints. The guide's topic list is not verified law.

## Acceptance

- [ ] All five sources registered with truthful review status, dates and reviewer evidence.
- [ ] Unique Evidence IDs, nonempty URLs and Rule ID → Evidence ID → URL mappings.
- [ ] Unverified or missing evidence cannot be marked usable or verified.
- [ ] Two case types and seven Action Card sections mapped.
- [ ] Import validation and relevant tests actually executed.

Evidence: reviewed passages, source versions, PRs and test output. Do not fabricate quotations, dates or thresholds.
