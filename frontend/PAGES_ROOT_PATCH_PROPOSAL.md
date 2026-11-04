# Pages root homepage — coordinated change proposal (NOT APPLIED)

**Action required from Junjie/owner:** authorize Guanyu to modify the ROOT index.html in a separate PR or have Junjie apply it. This file is outside frontend/ and was not touched here.

The published Pages home at https://chu-junjie.github.io/SG-Navi/ serves root index.html. It is still the Task 1 version and displays two "Flow coming soon" placeholders, even though frontend/index.html already has working form links. The integrated Flask home is separate and does not prove the Pages root works.

Minimal root change after permission, retaining skyline/brand/logo:
1. Change both choice-label strings from "Flow coming soon" to "Open guided form"; change "Both flows are being developed" to appropriate prototype wording.
2. Before root homepage inline script, load: <script src="./frontend/js/api-config.js"></script>
3. Resolve health URL with SGNaviApiConfig.resolve("/api/health",window.location); when missing, show a not-configured offline message and send no request; keep the existing try/finally for re-enabling Refresh.
4. On Rental click, navigate to "./frontend/task5-flow.html?case_type=rental_deposit"; on Consumer click to "./frontend/task5-flow.html?case_type=consumer_complaint". The /frontend/ path segment is essential on Pages ROOT; do not copy the frontend/index.html relative link unmodified.
5. Publish and verify the actual root URL and deployed revision; check both routes, form schema and JS files, and once a verified backend is supplied, the exact HTTPS origin and CORS.

Expected public paths AFTER owner-approved root patch and verified deployment:
- https://chu-junjie.github.io/SG-Navi/
- https://chu-junjie.github.io/SG-Navi/frontend/task5-flow.html?case_type=rental_deposit
- https://chu-junjie.github.io/SG-Navi/frontend/task5-flow.html?case_type=consumer_complaint

This is an implementation proposal, NOT evidence of approval, deployment or public browser pass.
