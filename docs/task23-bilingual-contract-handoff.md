# Task 23 — Bilingual result and process source handoff

**Status:** proposed contract extension, NOT agreed, reviewed or deployed. Frontend: Guanyu-Lu. API protocol owner: ZhengZaikun. Source/legal reviewer and coordinator: Chu-Junjie.

## Already implemented safely in draft PR #107

- User-facing static layout, English/Chinese labels and slogan; actual source records are unchanged.
- Main verified action and in-memory progress steps are rendered only from existing Action Plan 1.0 `plan.primary_action` and `plan.checklist`. This is **View available steps**, not a certified full court/CASE timeline.
- Original official English legal quote, SHA-256, source URL, legal edition and captured/reviewed times remain immutable. No external translation API or user-data storage.
- Current dynamic English case-specific source text is explicitly marked **unreviewed/untranslated** in Chinese mode, so full bilingual acceptance is not claimed.

## Contract extension proposal (source-owner approval required)

Expose optional versioned `localized_text` for user-facing fields, scoped to a source-reviewed `zh-Hans` locale. The server response must carry a bilingual approval version/digest, and its action/evidence IDs must match the English result exactly. Do not accept an arbitrary client-provided translation or preserve an old Chinese translation after the confirmed context revision changes.

Suggested source-owned fields:

| Action Plan field (existing English) | Proposed accompanying zh-Hans field | Review owner |
| --- | --- | --- |
| `message`, `context.summary` | `localized_text.zh-Hans.message/summary` | Zheng; Junjie |
| `question.prompt/reason/options[].label` | ID/value-matched question labels/reason and options | Zheng |
| `plan.headline/assessment.text/primary_action.text/label` | matched result heading, assessment, exact next action/label | Zheng; Junjie |
| `plan.checklist[].text`, `plan.details[].items[].text` | ID-matched checklist and condition text | Junjie |
| `plan.contacts[].institution/purpose/note` | ID-matched display descriptions only; do **not** translate contact URLs, phone numbers or email addresses | Junjie |
| `plan.draft.title/subject/body/slots[].label` | coordinator-reviewed Chinese draft variant with **identical safe slot IDs** | Zheng; Junjie |
| `plan.legal_basis[]`, `plan.evidence[]` | optional *separate* clearly unofficial Chinese explanation, identified by exact evidence ID and review version | Junjie |

**Forbidden transformations:** modifying `evidence.quote`, `quote_sha256`, `source_sha256`, `url`, `provision`, `captured_at`, `reviewed_at`, `request_id`, `revision`, or any verified route/contact. A Chinese explanation is never itself an original legal quote or proof of eligibility. Do not infer legal filing process branches from translated copy.

A response is **fully bilingual-capable** only if the complete visible state (CONFIRM/ASK/READY/LIMITED/UNAVAILABLE and error states) has reviewed coverage. Otherwise the English experience remains the authoritative default with a clear Chinese limitation warning; do not silently advertise full translation.

## Future reviewed full process

Action Plan 1.0 provides a prioritized next action and a short preparation checklist, **not necessarily an end-to-end legal filing sequence**. To display an official complete timeline, a source-reviewed versioned extension should supply unique `step_id`, `text_en`, `text_zh_Hans`, `kind` (required/optional/conditional), `prerequisite_ids`, `evidence_ids`, `contact_id` (where supported), `reviewed_source_version` and stage ordering. Frontend checks personal ticks only; it must never report official acceptance or submission. Unsupported, stale, quarantined or missing evidence must fail closed.

## Required acceptance evidence

- Deterministic translation validation against reviewed source and contract version, two scenarios plus limited/error/unknown states.
- Switch language mid-question, mid-result, mid-draft, and inside process drawer with no new HTTP request, loss of answers, source drift or loss of checkbox state.
- Actual Pages→Render 1366×768 / 1440×900 / 320px / 390px, 200% zoom and keyboard/ESC/focus/draft/edit/offline acceptance; screenshots, source quote identity and request logs.
- Separate coordinator text/source review and honest technical/usability/legal dispositions. Keep Issues #93, #94 and #106 open until their own evidence gates are met.
