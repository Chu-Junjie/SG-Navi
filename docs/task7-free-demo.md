# Task 7 — Render Free API demonstration (NOT the release candidate)

**Purpose:** a temporary HTTPS backend to let Guanyu connect the existing GitHub Pages frontend, with **zero paid Render web-service plan charges**. This is NOT the durable-state backend required for final Task 7 acceptance.

## Scope and explicit limitation

- Free deployment entry: `backend.free_demo:app` with Gunicorn, `debug=False`, 32 KiB request body limit, checked real RAG corpus and unchanged API schemas.
- Free hosting does **not** preserve `instance/rag_quarantine.json` across replacement/redeployment. The startup setting `SG_NAVI_FREE_DEMO_ACK=1` means temporary state loss is **known and accepted for demonstration only**. `SG_NAVI_REQUIRE_PERSISTENCE=1` forbids starting this demo.
- Do **not** change the existing `render.yaml` or `backend.production`. Those remain the proposed durable paid production configuration. The isolated `render-free.yaml` is a reviewable no-disk Blueprint option.
- No eligibility rules are enabled. Real complete synthetic cases should return `REFER_TO_OFFICIAL`, contextual Evidence and `action_card: null`, never a legally supported Action Card. **Never enter real dispute/private data** in a free public demonstration.
- Render free instances can suspend and have ephemeral files. Keep RAG quarantine changes and backup/restart tests **NOT RUN / NOT SATISFIED** for final release until an external persistence architecture or paid disk has been implemented and genuinely tested.

## Repository and deployment details

GitHub: https://github.com/Chu-Junjie/SG-Navi

Branch: `feat/task7-free-public-api-demo` (start from merged PR #50 main `ffb503f9f0de4fd4fbb4cf8dcf3d2a6f653b5892`). **Record actual deployed commit from Render; it must not be inferred from branch name.**

Proposed free Render Web Service settings:

| Field | Value |
| --- | --- |
| Name | sg-navi-api-free-demo |
| Region | Singapore |
| Plan | Free (NOT Starter or paid) |
| Repository | https://github.com/Chu-Junjie/SG-Navi |
| Branch | feat/task7-free-public-api-demo (review then merge or pin final approved main) |
| Build | `pip install -r requirements.txt && python -m rag.import_knowledge_base` |
| Start | `gunicorn --bind 0.0.0.0:$PORT --workers 1 --threads 2 --timeout 30 backend.free_demo:app` |
| SG_NAVI_FREE_DEMO_ACK | `1` |
| SG_NAVI_REQUIRE_PERSISTENCE | `0` |
| SG_NAVI_CORS_ORIGINS | `https://chu-junjie.github.io` |
| PYTHON_VERSION | `3.12.9` |
| Disk | **None.** Free service has no persistent disk. |
| Auto Deploy | Disabled to avoid accidental unreviewed changes |

The **whole repo** is the build context, including `shared/`, five `rag/knowledge_base` files, and `frontend/schemas`; do not deploy just `backend/`.

## Live public verification (after a real hostname exists)

Use a real `https://...onrender.com` URL returned by Render (never guess the hostname):

```powershell
python -m backend.smoke_public --base-url https://ACTUAL-RENDER-SERVICE.onrender.com
```

This read-only/synthetic smoke check sends real remote HTTPS GET health/version, OPTIONS from Pages origin, POST both synthetic cases, missing facts, invalid answers, and refused origins. Save its timestamped JSON and actual Render deploy commit and dependencies. A green GitHub CI is **not** a substitute for this live check.

The owner Guanyu must integrate the actual Base URL into `https://chu-junjie.github.io/SG-Navi/` in a frontend-only PR and rerun full browser flows. Current Pages `/api/health` returning 404 is expected without such integration. Backend does **not** modify Guanyu's `frontend/`.

## Release gate and future migration

Before the `v0.9.0-rc1` tag, replace this temporary service with a durable quarantine store (the existing paid Render disk plan, or a properly implemented and tested external persistent store). Verify state survives a **real service restart**, genuine backup/restore and rollback; run full BE/RAG/FE/E2E suite, both Pages-origin cases, actual source-version check and coordinator approval. The free ephemeral demo itself **does not** satisfy these final gates.

Operational notes: do not purge unknown existing quarantines to make tests pass; quarantine actions need legitimate operator/source review; no credentials or user data should be added to Git or Render public logs.
