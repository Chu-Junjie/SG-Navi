# Task 20 / 21 — action-first interface foundation (UI fixture only)

**Owner:** `Guanyu-Lu` · **Tracked:** [Task 20 #92](https://github.com/Chu-Junjie/SG-Navi/issues/92), [Task 21 #93](https://github.com/Chu-Junjie/SG-Navi/issues/93)

## Purpose

This is the concrete HTML/CSS/JS reference for the approved **direction**, not an accepted implementation of the next release. It follows the user's Concept 01 image: short one-screen text entry, one persistent single-question modal, a visible main next step first, and optional detail panels in an internally scrollable result container. It is intentionally isolated from the published root and preserves the Task 15 implementation until the new protocol and data are reviewed.

**Preview URL after the branch/PR is merged:** `/frontend/task20-concept.html`. If testing directly from the branch, use the GitHub source/checkout and open this HTML locally. It has no service calls, API keys, application state storage or navigation to the retired old UI.

## Implemented interaction for design review

- One description textbox with 1,200-character bound, two labelled synthetic examples, one main CTA.
- One reusable dialog shell for one illustrative question at a time, selectable buttons and `I'm not sure`, Back/Close, Escape, focus trapping and focus return.
- Short initial next-step presentation with a clear main button, an ordered checklist and a single secondary edit option.
- Fixed maximum-height result section with **internal** scrolling. Optional documents and unresolved details are hidden in a disclosure. Original-source information opens a separate single details drawer, not seven oversized cards.
- Responsive styles for desktop/mobile and reduced-motion; content inside the modal and drawer can scroll with zoom/keyboard and never relies on clipped outer content.
- Links use allowlisted official HTTPS destinations as **general reading references only**, not verified route/contact recommendations. No telephone, email, fees, statutory quotations, approved eligibility or refund promises are invented.
- Result/state text declares itself to be a **UI fixture**; no backend requests are made and examples are not passed off as official acceptance evidence.

## Blockers to integrating into the real public homepage

1. [Task 16 #88](https://github.com/Chu-Junjie/SG-Navi/issues/88): product scope, one-question state and versioned contract must be frozen and reviewed; the current fixture assumes no live contract.
2. [Task 18 #90](https://github.com/Chu-Junjie/SG-Navi/issues/90): must return real issue/goal recognition and **only route-changing relevant questions**. The fixture's two questions per sample are not the required logic and must not be used as real production questions.
3. [Task 17 #89](https://github.com/Chu-Junjie/SG-Navi/issues/89) and [Task 19 #91](https://github.com/Chu-Junjie/SG-Navi/issues/91): approved primary action, contact URL/phone/email, claim-level actual source quote, relevant law and editable template slots. Without the API fields, the new Task 21 cannot claim verified actionable contacts.
4. Task 20 deployment gate: coordinate authorized removal of both big legacy cards/service panel and the agreed migration/redirect for old public URLs, and update legacy browser tests against the new approved UX.
5. Task 21 final acceptance: use the real Task 19 API for restaurant-overcharge and rental/pass-related journeys, exact citation/contact checks, desktop and mobile/200% zoom screenshots, keyboard/touch focus, offline retry and deployed Pages→Render verification. No fixture tests count toward this.

## Testing

- `node --check frontend/js/task20-concept.js`
- `node --test frontend/tests/test_task20_concept.cjs`
- `python -m unittest frontend.tests.test_task20_concept`
- Existing CI should run the regression checks when this branch is proposed for review. Passing tests on a static UI fixture **do not** prove real API or live browser acceptance.

**Merge note:** Only merge as a separate, labelled non-production concept if desired. Do not replace root `index.html`, mark #92/#93 complete, tag a release or claim customer usability research based on this fixture.