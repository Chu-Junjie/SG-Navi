---
name: Task 5 - Integration
about: Connect backend to real RAG before connecting frontend
title: 'Task 5 — Integrate backend, RAG and frontend'
---

Prerequisite: Task 4 accepted.

## Responsibilities

- @Chu-Junjie: coordinate integration, identify contract mismatches and assign reproducible bugs to owners.
- @ZhengZaikun: replace Mock Evidence with retrieve_evidence(case_type, rule_ids, facts); handle empty, invalid and failed retrieval.
- @Guanyu-Lu: replace Mock API with /api/navigate; handle follow-up questions, edits, referrals, errors and citations.

## Acceptance

- [ ] Validate Backend + Mock Evidence, then Backend + real RAG, then Frontend + Backend in that order.
- [ ] Rental and Consumer run from real page through real API and RAG.
- [ ] Unknown facts, out-of-scope input, bad citations, absent evidence and service failures handled without fabricated conclusions.
- [ ] Real integration tests recorded; major mismatches resolved before Task 6.

Evidence: both end-to-end reproduction steps, commit, logs, PRs and Bug Issues. Cross-module changes require the owner's confirmation.
