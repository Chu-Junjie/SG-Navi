# Task 4: dynamic case forms + mock API display

Only `frontend/` is changed. Task 3 acceptance was recorded under Issue #3.

## Open the preview

From the repository root:

```powershell
python -m http.server 8000 --directory frontend
```

Open **http://127.0.0.1:8000/forms.html**.

The standalone page is deliberately not linked into the root-level `index.html`,
which is outside the requested `frontend/` change scope. That integration can
be approved separately. The preview also does not depend on the Flask backend.

## Implementation boundary

- **Input controls** are generated from exactly the existing
  `schemas/rental_deposit_input.schema.json` and
  `schemas/consumer_complaint_input.schema.json` properties. Display labels
  come from the existing `mappings/task3_display_map.json`.
- Per-field choices are Skip (omit), Provide answer, Unknown (string `unknown`),
  and Not provided (`null`). Boolean `false` is stored as false; it is never
  inferred from missing/unknown. Numeric/date/text validation is structural
  and uses schema types/formats/minima, **not legal thresholds**.
- Both case drafts remain editable while the page is open. Changing answers
  invalidates the previous displayed result. No personal data is saved to
  localStorage, sent to the backend or committed to the repository.
- Submit creates the unchanged API 1.0 envelope:
  `{ "api_version": "1.0", "case_type": "...", "answers": {...} }`.
- **Mock API** is a frontend-local transport that fetches the four existing
  `frontend/mocks/*_response.json` synthetic fixtures. A selector allows all
  four navigation statuses to be demonstrated independently of answers.
  It does not call `/api/navigate`, and does not simulate legal eligibility.
- The seven result headings are derived from
  `schemas/action_card.schema.json`; questions/warnings come from the response.
  Placeholder evidence `example.invalid` and mock versions cannot become
  clickable official citations or supported legal paths. Without genuine
  evidence metadata, channel/condition/step sections explicitly show
  **Needs verification**.

## Tests

With contract-test dependencies installed:

```powershell
python -m pip install -r tests/contracts/requirements.txt
python -m unittest discover -s frontend/tests -v
```

Optional real browser smoke tests (separate from GitHub's Python CI):

```powershell
python -m pip install playwright
python -m playwright install chromium
python frontend/tests/browser_task4.py
```

The smoke script runs real Chromium with a controlled in-page Mock API (no network
requests), exercising 2 cases x 4 statuses at desktop, phone and narrow phone
widths, negative numeric input, editing/unknown, overflow, and JS errors.

## Next stage

Integrating real backend `/api/navigate`, verified retrieved passages, actual
case logic, and root homepage navigation is **not** claimed in Task 4.
