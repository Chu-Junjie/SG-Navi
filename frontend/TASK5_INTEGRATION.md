# Task 5 frontend → real backend integration

Scope: frontend/ only. The page `task5-flow.html` generates fields from the two existing
input schemas. It POSTs the original shared API 1.0 envelope to the **real**
`/api/navigate` endpoint. No rule thresholds, channels, legal decisions, evidence,
or extra request fields are embedded in JavaScript. The previous Task 4 Mock page
is intentionally untouched.

## Start locally (two PowerShell terminals)

From the SG-Navi repository root:

Terminal 1:

```powershell
py -m pip install -r tests/contracts/requirements.txt
py -m flask --app backend.app run --host 127.0.0.1 --port 5000
```

Terminal 2:

```powershell
py frontend/dev_proxy.py --backend http://127.0.0.1:5000 --port 8000
```

Open http://127.0.0.1:8000/task5-flow.html (not port 5000: the Flask
app currently serves only its homepage and assets directly).
The frontend-only development bridge serves the form, schemas, mappings,
and JS, while forwarding the real `POST /api/navigate` to Flask. It binds only
to loopback and does not alter backend code.

**Important current backend limitation:** At the Task 4 baseline, production
HTTP requests cannot activate the synthetic `SUPPORTED_PATH` branch and
no real RAG-backed path is claimed. Rental/Consumer normally demonstrate
`NEED_CLARIFICATION` followed by `REFER_TO_OFFICIAL`.
`ERROR` is possible on backend failures/invalid requests; invalid/unavailable
transport is shown as `Service unavailable` in the page. All four contract
status branches are implemented in the renderer but do **not** fabricate
a `SUPPORTED_PATH` response. Citation links are displayed only for
a supported response where every cited Evidence ID matches a verified,
non-mock source-version-matched HTTP(S) URL. Structural metadata alone
does not establish the correctness of the advice.

## End-to-end example A: Rental Deposit (synthetic only)

1. Select Rental Deposit and leave all answers as **Not provided**;
   click **Check case**.
2. Expect the real backend to return `NEED_CLARIFICATION` with its
   questions about `dispute_with`, `premises_type` and `claim_amount_sgd`.
3. Click the backend question's **Answer / edit** button; it focuses the
   corresponding form control. Enter `landlord`, `residential`, and
   `1200` in those three fields. For the others choose Unknown / not sure
   or leave Not provided. Click **Check case** again.
4. Expect `REFER_TO_OFFICIAL` from the current conservative backend,
   with its own warning and the seven card sections showing
   **Needs verification** where evidence is absent.
5. Change `claim_amount_sgd` to `800`, submit again; the edited amount
   appears in the request preview and the real backend is re-queried.
6. For an error demonstration, stop Flask and submit again. Expect
   **Service unavailable**; all answers remain available for retry.
   Restart Flask before testing the second flow.

## End-to-end example B: Consumer Complaint (synthetic only)

1. Switch to Consumer Complaint. All nine fields come from the existing
   Consumer schema (not the Rental schema). Begin with Not provided and
   click **Check case**.
2. Expect `NEED_CLARIFICATION` questions covering `purchase_type`,
   `purchase_purpose`, `supplier_registered_in_sg`, and
   `claim_amount_sgd`.
3. Click **Answer / edit** for the first question, then enter
   `goods`, `personal`, select **Yes** for the Singapore registration,
   and enter `75` for the disputed amount. Unknown is available for
   any other fact. Submit again.
4. Expect the current backend to return `REFER_TO_OFFICIAL`, with
   server-supplied warning text. No unverified channel or invented
   step is shown.
5. Edit `purchase_purpose` to `business` and submit again. The
   response remains `REFER_TO_OFFICIAL`, now for the scope boundary
   reported by the backend. Switch to Rental and back to verify the
   Consumer answers were retained.
6. To test validation, enter a negative disputed amount using the numeric
   control: the page should display an input warning and **not** make
   another API call. Restore `75` and retry.

## Run automated frontend tests

```powershell
py -m unittest discover -s frontend/tests -v
```

Task 5 tests exercise live HTTP against the existing Flask application through
the frontend-only loopback bridge; they also verify static page/JS safety
conditions. The browser UI, keyboard, and citation-link behavior should be
checked with a real browser before the team's Task 5 acceptance. No mocked
official sources, fake user data, or credentials are committed.

**Citation test constraint:** Current production responses have no supported
Action Card with valid Evidence, so a working official citation link cannot be
demonstrated end-to-end until the backend/RAG owners provide one. The UI
already rejects mismatched IDs, placeholder URLs and mock source versions.
