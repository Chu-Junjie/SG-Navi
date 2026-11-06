"""Additive confirmed-guidance 1.0 API; legacy endpoints keep their contracts."""
import re

from flask import Blueprint, current_app, jsonify, request

from backend.guidance import empty, generate
from rag.import_knowledge_base import read_json
from rag.repository import RepositoryError
from shared.validate_guidance import validate_guidance
from jsonschema.exceptions import ValidationError

guidance_api = Blueprint("task15_guidance", __name__)
MAX_BYTES = 8192


def error(message, code):
    return jsonify(empty("ERROR", message)), code


@guidance_api.post("/api/guidance")
def guidance():
    if not request.is_json:
        return error("JSON Content-Type is required.", 415)
    if request.content_length is not None and request.content_length > MAX_BYTES:
        return error("Request exceeds the permitted size.", 413)
    raw = request.stream.read(MAX_BYTES + 1)
    if len(raw) > MAX_BYTES:
        return error("Request exceeds the permitted size.", 413)
    try:
        body = read_json(raw.decode("utf-8"))
        validate_guidance(body, "request")
        if (not isinstance(body, dict) or set(body) != {"guidance_version", "confirmed", "case_type", "confirmed_answers", "confirmation_revision", "query"}
                or body["guidance_version"] != "1.0" or body["confirmed"] is not True
                or body["case_type"] not in ("rental_deposit", "consumer_complaint")
                or not isinstance(body["confirmed_answers"], dict)
                or not isinstance(body["confirmation_revision"], str)
                or not re.fullmatch(r"[0-9a-f]{20}", body["confirmation_revision"])):
            return error("Confirm a supported case and its current structured facts first.", 400)
        factory = current_app.config.get("SG_NAVI_REPOSITORY_FACTORY")
        repo = factory() if factory is not None else None
        audit = current_app.config.get("SG_NAVI_FRESHNESS_REPORT")
        result = generate(body["case_type"], body["confirmed_answers"],
                          confirmation_revision=body["confirmation_revision"], query=body["query"],
                          repository=repo, freshness_report=audit)
        validate_guidance(result)
        return jsonify(result), 200
    except (RepositoryError, OSError, RuntimeError):
        return error("Verified source records are unavailable. Please retry; no decision was made.", 503)
    except (ValidationError, ValueError, KeyError, TypeError):
        return error("Invalid or stale confirmed facts. Confirm the current answers again.", 400)
