"""Production WSGI entrypoint.

The public free demo can remain explicitly ephemeral for synthetic connectivity
tests, or use an independently hosted PostgreSQL state database with audited
quarantine transactions. Durable state is fail-closed: there is no fallback to
ephemeral files if the configured database is unavailable.
"""
import os
from pathlib import Path

from backend.app import create_app
from rag.repository import EvidenceRepository, DEFAULT_STATE


def create_production_app():
    setting = os.environ.get("SG_NAVI_REQUIRE_PERSISTENCE")
    free = os.environ.get("SG_NAVI_FREE_DEMO")
    if setting not in (None, "0", "1"):
        raise RuntimeError("SG_NAVI_REQUIRE_PERSISTENCE must be 0 or 1")
    if free not in (None, "0", "1"):
        raise RuntimeError("SG_NAVI_FREE_DEMO must be 0 or 1")

    is_free_demo = free == "1"
    state_dsn = os.environ.get("SG_NAVI_STATE_DATABASE_URL")
    has_database = bool(state_dsn and state_dsn.strip())

    if is_free_demo and setting == "1" and not has_database:
        raise RuntimeError("Free demo with mandatory persistence needs a real state database")

    if has_database:
        from rag.postgres_state import PostgresStateStore
        # Prepare tables and validate existing source-history before exposing API.
        # Database faults terminate startup rather than using local temp state.
        PostgresStateStore(state_dsn).prepare()
        EvidenceRepository().snapshot()
    elif os.environ.get("RENDER") == "true" and not is_free_demo or setting == "1":
        expected = Path(__file__).resolve().parents[1] / "instance"
        if DEFAULT_STATE.parent.resolve() != expected:
            raise RuntimeError("RAG quarantine state path is not the configured instance directory")
        if not expected.is_mount():
            raise RuntimeError(
                "Required persistent disk is not mounted at instance/. "
                "Do not run the persistent public API with ephemeral quarantine state."
            )
        if not os.access(expected, os.W_OK | os.X_OK):
            raise RuntimeError("Persistent quarantine directory is not writable")
        EvidenceRepository().snapshot()
    elif is_free_demo:
        # Explicitly nonpersistent mode: synthetic transport demo only.
        EvidenceRepository().snapshot()

    app = create_app()
    app.debug = False
    app.config["TESTING"] = False

    if is_free_demo:
        @app.after_request
        def free_mode_disclosure(response):
            response.headers["X-SG-Navi-Deployment-Mode"] = (
                "postgres-backed-free-demo" if has_database else "ephemeral-free-demo"
            )
            return response

    return app


app = create_production_app()
