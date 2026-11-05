"""Prevent accidental paid or nonpersistent changes to the current free deployment."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def content(path):
    return (ROOT / path).read_text(encoding="utf-8")


def test_default_blueprint_is_free_neon_backed_and_fail_closed():
    blueprint = content("render.yaml")
    assert "name: sg-navi-api-junjie" in blueprint
    assert "plan: free" in blueprint
    assert "plan: starter" not in blueprint
    assert "disk:" not in blueprint
    assert "branch: main" in blueprint
    assert "healthCheckPath: /api/health" in blueprint
    assert 'SG_NAVI_REQUIRE_PERSISTENCE\n        value: "1"' in blueprint
    assert "SG_NAVI_STATE_DATABASE_URL\n        sync: false" in blueprint
    assert "postgresql://" not in blueprint
    assert "SG_NAVI_CORS_ORIGINS" in blueprint


def test_paid_alternative_is_explicitly_separate():
    paid = content("render.starter.yaml")
    assert "HISTORICAL PAID ALTERNATIVE" in paid
    assert "plan: starter" in paid
    assert "disk:" in paid
    for historical in ("render.free.yaml", "render-free.yaml"):
        legacy = content(historical)
        assert "HISTORICAL NONPERSISTENT DEMO" in legacy


def test_public_origin_is_current_service_and_not_a_secret():
    frontend = content("frontend/js/api-config.js")
    assert 'const HTTPS_API_ORIGIN = "https://sg-navi-api-junjie.onrender.com";' in frontend
    assert "sg-navi-api-free-demo.onrender.com" not in frontend
    assert "SG_NAVI_STATE_DATABASE_URL" not in frontend


def test_public_workflows_include_main_and_independent_browser():
    smoke = content(".github/workflows/task7-junjie-render-neon-https.yml")
    assert "branches: [main, feat/task7-free-hosting-hardening]" in smoke
    assert "github.event_name == 'schedule'" in smoke
    assert "task7_public_pages_check.mjs" in smoke
    assert "postgres-backed-free-demo" in smoke
    assert "github.event_name == 'workflow_dispatch'" in smoke
    assert "https://sg-navi-api-junjie.onrender.com" in smoke


def test_actual_postgres_durability_runs_on_main_without_prod_dsn():
    workflow = content(".github/workflows/task7-postgres-durability.yml")
    assert "branches: [main, feat/task7-free-hosting-hardening]" in workflow
    assert "services:" in workflow
    assert "postgres:18" in workflow
    assert "tests/backend/test_task7_pg_real_durability.py" in workflow
    assert "SG_NAVI_STATE_DATABASE_URL" not in workflow
    assert "damp-scene-05807412" not in workflow


def test_source_freshness_is_readonly_and_requires_review():
    workflow = content(".github/workflows/source-freshness-read-only.yml")
    assert "python -m rag.import_knowledge_base --verify-live" in workflow
    assert "permissions:\n  contents: read" in workflow
    assert "schedule:" in workflow
    assert "source-freshness-audit.log" in workflow
    assert "Never auto-update review timestamps" in workflow
    assert "--output" not in workflow


def test_no_unreviewed_legal_rules_enabled_by_hosting_fix():
    for filename in ("boundary", "rental", "consumer"):
        import json
        rules = json.loads(content(f"backend/rules/{filename}.json"))
        assert rules["checks"]
        assert all(item["runtime_enabled"] is False for item in rules["checks"])
