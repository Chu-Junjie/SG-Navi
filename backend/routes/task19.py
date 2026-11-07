"""Task 19: bounded HTTP transport for Task 16 action-plan protocol."""
from flask import Blueprint, jsonify, request
from jsonschema import ValidationError

from backend.action_plan_service import process_action_plan, envelope
from shared.validate_action_plan import validate_action_plan

action_plan_api = Blueprint("task19_action_plan", __name__)
MAX_BODY_BYTES = 8192


def _error(message, status):
    # An invalid request has no trustworthy request identifier. Keep the error
    # outside the successful response schema and never echo untrusted text.
    return jsonify({"error": "invalid_request" if status != 503 else "service_unavailable",
                    "message": message}), status


@action_plan_api.post("/api/action-plan")
def post_action_plan():
    if not request.is_json:
        return _error("JSON Content-Type required.", 415)
    if request.content_length is not None and request.content_length > MAX_BODY_BYTES:
        return _error("Request too large.", 413)
    if len(request.get_data(cache=True)) > MAX_BODY_BYTES:
        return _error("Request too large.", 413)
    body = request.get_json(silent=True)
    if not isinstance(body, dict):
        return _error("Invalid JSON request.", 400)
    try:
        validate_action_plan(body, "request")
        reply = process_action_plan(body)
    except (ValueError, ValidationError, TypeError, KeyError):
        return _error("Invalid request or unsupported input.", 400)
    except (OSError, RuntimeError):
        # Once the request has been validated, transport failures retain the
        # versioned UNAVAILABLE response shape and request correlation.
        reply = envelope(body["request_id"], "UNAVAILABLE", "service_unavailable",
                         "Service is temporarily unavailable. Please retry.")
        return jsonify(reply), 503
    return jsonify(reply), 200
