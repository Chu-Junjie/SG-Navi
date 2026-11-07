# Task 16 action-first product contract

[Task 16 #88](https://github.com/Chu-Junjie/SG-Navi/issues/88) covers the design and shared contract. The owner chose one question per modal screen and a first result that states what help is available for the reported situation. The result should show an actual next action, useful contacts and a short checklist. A complaint draft, pitfalls, escalation and the source context are available on demand. The owner requested specific treatment of work-pass-related deposit disputes and actual relevant legislative wording.

## Three views in the same viewport

The Concept 01 review board uses the restaurant bill example. The [runnable frontend fixture](../frontend/task20-concept.html) illustrates the layout. The published homepage currently uses the earlier intake and guidance API with a compact layout from #97. Its current result and the new contract fixtures are separate from the future action-plan service.

```text
DESCRIBE                         CONFIRM / ASK                    NEXT STEP
┌─────────────────────────┐      ┌────────────────────────┐      ┌──────────────────────────────────┐
│ SG Navi       English   │      │ One quick detail     × │      │ SG Navi            Edit situation│
│ What happened?          │      │ Was this for personal  │      │ There is a route to explore       │
│ [ One description     ]│      │ use?                   │      │ Next action        Optional help │
│ [ Find my next step ]   │  →   │ [ Yes ] [ Business ]  │  →   │ [ Open official form ] [ Draft ]  │
│ Example chips           │      │ [ Not sure ]           │      │ Call / Email        [ Pitfalls ] │
│ Compact privacy note    │      │ Back         Continue │      │ 1–3 useful steps    [ Later ]    │
└─────────────────────────┘      └────────────────────────┘      │ Relevant excerpt   [ Context ]  │
                                                                └──────────────────────────────────┘
```

- Confirm the understood situation in a short sentence. Offer a clear correction path. A candidate is an unconfirmed proposal until the user chooses Continue. Start the modal with confirmation and reuse its shell for a decisive question. Close and Back preserve context. Restore focus to the invoking control and use the same sequence on keyboard, touch and pointer.
- Display the next action above the fold at 1366×768 and 1440×900 at normal zoom. Keep visible text and controls readable at 320 and 390 pixels and at 200% zoom. Allow the modal or detail content to scroll when the viewport or keyboard requires it. Keep the primary action reachable.
- A ready result leads with the route and what that route provides. Keep a material limitation visible with its action. Show secondary contacts only when the reviewed evidence supports that contact and purpose. Contact actions open the specified official destination or the user's call/email app. Drafts stay editable in the tab and require the user to copy or send them.
- Use the ordered checklist for the few immediate tasks. Open optional documents, pitfalls, alternatives, draft and source context in one reusable detail layer. Keep the main action visible on return. Use ordinary interaction feedback for hover, focus, pressed, loading and error states.

## Ask only when the answer changes what can be offered

| Situation | Minimum information for the immediate action | Ask or qualify only when it changes the action |
| --- | --- | --- |
| Restaurant overcharge or duplicate payment | A billing dispute, the user's goal, and where relevant the merchant location and personal purchase context | If the user already sought correction and wants to complain, offer verified consumer assistance with its conditions. Ask personal/business or location only when that distinction changes the recommendation. A verified preparation step can be shown while a contact route is uncertain. |
| Unclear restaurant charge | What is disputed and whether the user wants clarification or a complaint | Start with the bill/menu comparison and an itemised explanation when the charge is unclear. Keep the commercial nature and legal finding unresolved. |
| Deposit return or deduction | A residential rental deposit, the reported issue and the party holding it | Request the signed deposit terms, records and reasons for deductions. A landlord dispute and agent conduct lead to different next actions. |
| Early exit with pass expiry or cancellation | Rental context, reported pass event and whether the lease was ended early or is still active | Ask about the signed break/diplomatic clause if this changes the next step. Explain which contract term and notice/document to check. The pass event alone cannot settle the private refund question. |
| Agent conduct or agency agreement | Party is an agent and the user identifies conduct or a contractual agency issue | Ask whether there is a signed agency agreement only when needed for the agreement route. Evidence for a conduct complaint does not justify sending a landlord dispute to CEA. |
| Formal claim assessment requested | Facts needed by the particular verified procedure | Only then ask about the relevant dates, amount, lease type/duration, and respondent service where applicable. Preserve unknown conditions and distinguish reviewing criteria from filing or qualifying. |
| Outside scope, ambiguous, or source unavailable | Enough to identify the limit or ask one useful question | Allow correction or a verified conditional step when the evidence permits it. A standalone immigration query and a rental question mentioning a pass are different scopes. |

An ordinary path targets zero to three additional questions. A later decisive question needs an explicit reason. A supplied unknown, null or false answer remains distinct from a missing key and should not be asked again automatically. Registration proof, identification numbers, documents and exact monetary values are not prerequisites to viewing basic verified help. When the user volunteers known facts, confirm them together rather than showing a field table.

## Additive API 1.0

The new [action plan schema](../shared/action_plan_contract.json) specifies a proposed endpoint for Tasks 18 and 19, `POST /api/action-plan`. Each request includes a new opaque `request_id`. An `interpret` request sends up to 1,200 characters and returns a candidate context or a scoped explanation. A `plan` request sends an explicitly confirmed context, including case type, issue subtype, goal and typed facts. It carries no original description. Treat the context summary as text and keep the user's description and answers in tab memory.

| State | Contract and presentation |
| --- | --- |
| `CONFIRM` | Candidate context only. Show the short proposed understanding. |
| `ASK` | Confirmed revision and exactly one decisive question. The choices include an explicit unknown value. A separately supported preparation step may be present. |
| `READY` | A verified immediate action, assessment, checklist and evidence. A consultation or a criteria check can be useful while a legal outcome remains uncertain. |
| `LIMITED` | A specific ambiguity, scope, missing-fact or source reason and a short corrective message. |
| `UNAVAILABLE` | Retry the same operation without discarding the current answer state. |

Use integer cents for amounts and integer months for duration. Unanswered optional keys stay absent. A context revision hashes the case, subtype, goal and typed facts. It is a consistency marker. Confirmed facts cannot change silently in a response. The client aborts in-flight work on edits and accepts only the active request and revision. Editing a decisive fact invalidates its downstream guidance and drafts, while unrelated confirmed answers remain available.

Task 18 owns interpretation and choice questions. Task 19 owns the service, live evidence selection and final validation. The shared validator checks shape, state, request linkage, action/contact purpose, exact quote digests, claim links and draft placeholders. A data snapshot must also be checked against the approved, current source package and quarantine state by the service. The schema cannot authorize any legal rule.

Keep the Task 15 endpoint and older versioned clients on their existing contracts during rollout. Task 21 switches the public result to the action plan only after the deployed service and source checks pass. Coordinate legacy HTML redirects with the frontend owner as part of the integrated release. The underlying older API compatibility tests remain useful separately.

## Evidence and presentation

A legal-basis pointer links an individual claim to an exact statutory excerpt. Display the Act title and provision with the excerpt. The full-context action opens its reviewed source. Official procedure and optional agreement templates have their own kinds and wording. The app's explanation and user-reported contract facts remain separate. A template explains what to look for in the signed agreement and cannot establish which terms were signed. A statutory jurisdiction extract cannot establish that a private deposit is owed.

Only a current, reviewed contact record supplies a web link, telephone or email. The front end renders the authorized destination and purpose. Scope and review date are available with the evidence. Keep unsupported contact details absent. Never route a complaint to an accreditation or unrelated regulatory form. Task 17 documents authoritative statute access, context, version and any gaps. The historical source examples in Task 16 are protocol fixtures and do not add newly reviewed legislative or contact records.

## Acceptance targets before implementation

| Measure | Target and observation |
| --- | --- |
| Find the next step | At both desktop reference sizes, the primary action and responsible party are visible without scrolling the outer page. Capture the viewport and measure the element bounds. |
| Act on the result | From the result, one click reaches the selected verified external destination. One click opens the exact selected source context. Record interaction and actual target URLs. |
| Question relevance | Record all asked question IDs, prior facts and action dependency. Ordinary scenarios target no more than three extra questions and zero repeated supplied facts. |
| Human comprehension | Show the result to actual reviewers using both synthetic scenarios. From the initial reveal, target identifying the responsible party and next action within five seconds. Record actual elapsed times, errors and feedback. Report any absent human observation as NOT RUN. |
| Action and evidence accuracy | Apply the frozen Task 22 routing, contact, first-action, mandatory checklist and citation gates. Review each consequential claim against its source and the confirmed facts. Test failure, ambiguity and contract dependence separately. |
| Accessibility and recovery | Capture desktop/mobile/zoom and keyboard paths, focus return, editing, stale replies and real retry. Verify synthetic input and no browser persistence or data-bearing URLs. |

User feedback already recorded in this thread concerns the current page's scanning, scrolling, generic results and legacy detours. The user chose one-question modals and specific actions over a generic legal summary. This design records those decisions. Timed comprehension, actual new API journeys and deployed acceptance belong to Task 22. Actual developer review, waiver and test evidence are recorded on the Task 16 PR.

## Verify the handoff

With the existing dependencies installed from `tests/contracts/requirements.txt`:

```powershell
python -m shared.validate_contracts
python -X utf8 -m pytest tests/contracts -q
```

Open `frontend/task20-concept.html` for a locally runnable fixture. The existing integrated app is started with `python -m flask --app integration.app run --host 127.0.0.1 --port 5000`. The protocol fixtures in `shared/examples/task16_action_plan.json` have explicit origins and exercise both scenarios, a question, scope limitation and service unavailability.
