"""Read the active, validated RAG source version without treating mock data as live.

The returned version identifies the checked source bundle, not legal eligibility
or rule activation. Read fresh on each request so updates and corrupt source
state do not silently inherit a stale version.
"""
from rag.repository import EvidenceRepository

UNAVAILABLE_SOURCE_VERSION = "unavailable"


class SourceVersionUnavailable(RuntimeError):
    """The source bundle or operational quarantine state cannot be trusted."""


def validated_source_bundle():
    """Return a fresh checked bundle, including validation of quarantine state."""
    try:
        bundle, _blocked = EvidenceRepository().snapshot()
        version = bundle["source_version"]
        if not isinstance(version, str) or not version.strip() or version.startswith("mock"):
            raise ValueError("Unexpected source version")
        return bundle
    except Exception as exc:
        raise SourceVersionUnavailable(
            "Validated source-bundle version cannot be determined"
        ) from exc


def current_source_version():
    """Report only a real source version; never substitute mock-1 on failure."""
    return validated_source_bundle()["source_version"]
