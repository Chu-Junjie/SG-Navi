"""Task 11 additive endpoints; v1 /api/navigate remains untouched.

Raw descriptions never go to logs, a model provider, the database or responses.
Only synthetic / case-limited English heuristics are used. Schema is a proposal
pending Chu's shared-contract review and Guanyu's frontend integration.
"""
import json
from functools import lru_cache
from pathlib import Path

from flask import Blueprint, jsonify, request
from jsonschema import Draft202012Validator, ValidationError

from backend.intake import confirm, interpret

intake_api = Blueprint("task11_intake", __name__)
CONTRACT = Path(__file__).resolve().parents[1] / "intake_contract.json"
MAX_BODY_BYTES = 8192


@lru_cache(maxsize=1)
def _validators():
    schema = json.loads(CONTRACT.read_text(encoding="utf-8"))
    Draft202012Validator.check_schema(schema)
    return {
        name: Draft202012Validator({"$ref": "#/$defs/" + name}, resolver=None)
        for name in ()
    }, schema


def _validate(payload, definition):
    _, schema = _validators()
    # JSON Schema local fragment reference; no network resolution of $id.
    Draft202012Validator({"$defs": schema["$defs"], "$ref": "#/$defs/" + definition}).validate(payload)


def _send(data, code=200):
    _validate(data, "response")
    return jsonify(data), code


def _error(message, code):
    return _send({
        "intake_version": "1.0", "intake_status": "error",
        "suggested_case_type": None, "candidate_facts": {},
        "needs_confirmation": True, "clarification_questions": [],
        "limitations": [message],
    }, code)


def _payload():
    if not request.is_json:
        return None, _error("Content-Type must be application/json.", 415)
    # Bound both fixed Content-Length and chunked bodies. Do not log contents.
    if request.content_length is not None and request.content_length > MAX_BODY_BYTES:
        return None, _error("Request body exceeds the maximum permitted size.", 413)
    raw = request.get_data(cache=True)
    if len(raw) > MAX_BODY_BYTES:
        return None, _error("Request body exceeds the maximum permitted size.", 413)
    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        return None, _error("Request body must be a valid JSON object.", 400)
    return data, None


@intake_api.post("/api/intake")
def intake():
    data, failure = _payload()
    if failure is not None:
        return failure
    try:
        _validate(data, "request")
        return _send(interpret(data["description"]))
    except (ValidationError, ValueError, KeyError, TypeError):
        return _error("Invalid English problem description or intake version.", 400)
    except (OSError, RuntimeError):
        return _error("Intake is temporarily unavailable. No decision can be made.", 503)


@intake_api.post("/api/intake/confirm")
def confirm_intake():
    data, failure = _payload()
    if failure is not None:
        return failure
    try:
        _validate(data, "confirmation_request")
        return _send(confirm(data["case_type"], data["confirmed_answers"]))
    except (ValidationError, ValueError, KeyError, TypeError):
        return _error("Invalid or unconfirmed case facts. No decision can be made.", 400)
    except (OSError, RuntimeError):
        return _error("Clarification is temporarily unavailable. Please retry.", 503)
