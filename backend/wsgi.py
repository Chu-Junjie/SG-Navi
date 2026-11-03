"""Production WSGI entrypoint: Gunicorn serves backend.wsgi:app.

SG Navi is still an internal, source-context referral candidate; never run the
Flask debug server or claim enabled legal eligibility rules in production.
"""
import os
from pathlib import Path

from backend.app import app
from rag.repository import DEFAULT_STATE


def validate_persistent_state():
    """Fail startup rather than silently lose quarantines on ephemeral hosting."""
    if os.environ.get("SG_NAVI_REQUIRE_PERSISTENT_STATE") != "1":
        return
    directory = Path(DEFAULT_STATE).parent
    if not directory.is_dir() or not directory.is_mount():
        raise RuntimeError(
            "Persistent RAG quarantine disk must be mounted at " + str(directory)
        )
    state = Path(DEFAULT_STATE)
    if state.exists():
        # A corrupt state must fail startup, never be overwritten or reset.
        from rag.repository import EvidenceRepository
        EvidenceRepository().snapshot()
    else:
        # Mount must be writable. Create a harmless short-lived probe only.
        probe = directory / ".sg-navi-mount-probe"
        with probe.open("x", encoding="utf-8") as handle:
            handle.write("ok")
        probe.unlink()


validate_persistent_state()
