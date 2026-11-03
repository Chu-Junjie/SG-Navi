"""Gunicorn WSGI entry point for SG Navi's limited public referral API.

The production app deliberately does not serve the GitHub Pages frontend.
Import fails closed when the Render persistent disk or current corpus is absent.
"""
import os
from pathlib import Path

from backend.app import create_app
from backend.cors import configure_cors
from rag.repository import EvidenceRepository, DEFAULT_STATE


def create_production_app():
    if os.environ.get("SG_NAVI_REQUIRE_PERSISTENCE") == "1":
        expected = Path(__file__).resolve().parents[1] / "instance"
        if DEFAULT_STATE.parent.resolve() != expected:
            raise RuntimeError("RAG quarantine state path is not the configured instance directory")
        if not expected.is_mount():
            raise RuntimeError(
                "Required persistent disk is not mounted at instance/. "
                "Do not run the public API with ephemeral quarantine state."
            )
        if not os.access(expected, os.W_OK | os.X_OK):
            raise RuntimeError("Persistent quarantine directory is not writable")
        # Validate the five canonical files and any historical quarantine events.
        # Never remove or reset the state file to recover from an invalid snapshot.
        EvidenceRepository().snapshot()

    app = create_app()
    app.debug = False
    app.config["TESTING"] = False
    configure_cors(app)
    return app


app = create_production_app()
