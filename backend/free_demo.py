"""Intentionally ephemeral Render Free demo entry point.

This is a temporary, stateless *referral* demo, not a candidate release.
Any quarantine changes stored in the local instance/ directory are disposable
when Render suspends/redeploys the free instance. Never use this entry point
when durable source isolation is a release requirement.
"""
import os

from backend.app import create_app
from rag.repository import EvidenceRepository


def create_free_demo_app():
    if os.environ.get("SG_NAVI_FREE_DEMO_ACK") != "1":
        raise RuntimeError(
            "Free demo requires SG_NAVI_FREE_DEMO_ACK=1: RAG quarantine state "
            "is ephemeral and must not be trusted across restarts"
        )
    if os.environ.get("SG_NAVI_REQUIRE_PERSISTENCE") == "1":
        raise RuntimeError("Cannot enable free demo and persistent-state requirement together")
    # Fail closed on a malformed canonical source bundle or local quarantine
    # record (if a transient record exists); never replace one with an empty file.
    EvidenceRepository().snapshot()
    app = create_app()
    app.debug = False
    app.config["TESTING"] = False
    app.config["MAX_CONTENT_LENGTH"] = 32768
    return app


app = create_free_demo_app()
