# Guanyu frontend acceptance evidence, 11 November 2026

Related issues #93, #106, #111 and the frontend contribution to #94. Related PR #131.

## Delivered correction

Changing a confirmed topic, subtype or goal now updates the existing Task18 product-written English summary template. A stale summary previously caused the reviewed endpoint to return 503 after a valid correction. `selector-summary-regression.json` preserves actual isolated Flask responses showing stale 503 and corrected 200. A regression checks 13 corrected selector combinations against the existing backend translation catalog. This formats the user's confirmed selectors and makes no legal route decision.

A desktop result with the English-fallback notice now keeps its main action inside the viewport, using the existing internally scrollable result. The browser runner accepts and verifies either canonical English responses or the actual reviewed envelope.

## Executed frontend checks

- `PATH="/tmp/sg-acceptance-bin:$PATH" ../logo-venv/bin/python -m unittest discover -s frontend/tests -v` completed with **78 tests, 1 skipped, zero failures** on the source commit `d4760ff6c1daa6caa28bd8c44ba1aa23cf23ea6c`. The local Chromium wrapper adds `--single-process --no-zygote` for the execution sandbox. No certificate verification was disabled.
- The real local Flask/Chromium browser runner passed **both** scenarios with reviewed delivery enabled. It also passed both with delivery disabled, exercising the real 404-to-English fallback. Each run produced **34 screenshots and 30 layout records**. `local-reviewed-browser.json` and `local-fallback-browser.json` preserve the actual results, wire identities, quote hashes and screenshot SHA-256 values. The reviewed report is from the full-suite run. One additional fallback-banner sizing rule was then verified in the fallback run. `source-snapshot.json` records the exact application/test file hashes.
- Normal-scale layouts cover **1366×768, 1440×900, 320×850 and 390×850**, in English and Chinese, on the homepage and both result scenarios. Desktop primary actions were visible without outer scrolling. No horizontal overflow was observed.
- Both scenarios passed Tab/Shift+Tab focus containment, Escape/focus return, checklist reopening and language state, edited draft retention, offline retry retaining typed answers, cancellation after editing a slow request, ordinary browser history Back, and no description in browser storage or request URLs. Network failures recorded during these checks are deliberately induced client-offline/cancellation cases.
- The half-CSS-viewport captures are explicitly labelled **200% equivalent layout**, not native browser zoom. Separately, actual Chrome UI zoom was set to **200%** on the published site for both scenarios. The browser UI, `devicePixelRatio=2`, no-horizontal-overflow measurements and open-step-dialog captures are in `public-native-zoom.json` and the `public-native-200-*.png` files. Native zoom was restored to 100% afterward. Those public captures use the already deployed PR130 frontend, before the PR131 correction.
- Actual earlier published functional walkthroughs and API verification are recorded in PR130. `public-reviewed-api.json` contains the actual Render HTTP200 reviewed responses for restaurant overcharge, rental/pass exit and deposit deduction, plus actual Pages-origin OPTIONS204/POST CORS headers. It includes full canonical/display examples with synthetic inputs only.

Only representative screenshots are committed here. The complete screenshot set is generated under `instance/task21-browser-local/` and preserved by the existing CI `task21-local-action-first-evidence` artifact. Public runner command after deployment is `node frontend/tests/task21_browser_check.mjs https://chu-junjie.github.io/SG-Navi/ /path/to/chrome --extended`. Local checks are not labelled as a published candidate pass.

## Task22 machine observations

`task22-machine-observations.json` preserves exact-field observations for **38 of the frozen 40 cases**, without changing the fixture, expected answers or backend. B09 and B10 require separate coordinator-controlled fault fixtures and are marked NOT RUN.

| Group | Observed | Case-type matches | Exact case/subtype/goal matches | Exact state/action/contact matches |
| --- | --- | --- | --- | --- |
| Rental | 15 | 15 | 3 | 5 |
| Consumer | 15 | 8 | 2 | 6 |
| Boundary | 8 | 4 | 2 | 4 |

These are machine comparisons, not completed independent acceptance. Some cases currently ask additional facts or use different contact IDs. Other descriptions are not recognised. Junjie and Zaikun must review the per-case differences against the frozen expectations. There was no backend tuning against the held-out set. Semantic legal/source support and checklist completeness were not scored. The current evidence does not meet Task22's final acceptance gates.

## Remaining team gates

1. Review and merge PR131, then rerun the corrected **published** consumer/rental journeys and extended public browser matrix. The local command here does not prove a new Pages deployment.
2. Confirm the actual Render deployment SHA through the provider. The public `/api/version` response currently reports legacy version fields and exposes no deployed SHA.
3. Resolve/reconcile Task22 frozen-case differences and run B09/B10 in isolated failure fixtures. Production source/quarantine data was not altered.
4. Record genuine human walkthroughs. For each participant, capture an anonymised identifier and role, scenario, device/viewport, actual time to identify the next action/organisation, clicks, questions, errors and permitted feedback. **Human comprehension, usability timings and semantic legal/source scoring remain NOT RUN.**

Keep the issues open for their remaining gates. This evidence supplies Guanyu's tested frontend corrections, reproducible technical checks and the actual observed limitations.
