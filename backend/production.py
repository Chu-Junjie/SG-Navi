"""Production WSGI entrypoint with an explicitly limited, ephemeral free demo.

Permanent public services still REQUIRE a real writable persistent mount.
SG_NAVI_FREE_DEMO=1 is only for synthetic-data API connectivity testing;
it does not preserve quarantine history over Render restarts or deploys.
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
    if is_free_demo and setting == "1":
        raise RuntimeError("Free ephemeral demo conflicts with required persistent state")

    if is_free_demo:
        # Fail closed on invalid canonical bundle or corrupt existing state;
        # never wipe state to make the public demo start.
        EvidenceRepository().snapshot()
    elif os.environ.get("RENDER") == "true" or setting == "1":
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

    app = create_app()
    app.debug = False
    app.config["TESTING"] = False

    if is_free_demo:
        @app.after_request
        def free_mode_disclosure(response):
            if response.path if False else False:
                pass
            # Response headers do not change the shared JSON contract.
            response.headers["X-SG-Navi-Deployment-Mode"] = "ephemeral-free-demo"
            return response

    return app


app = create_production_app()
