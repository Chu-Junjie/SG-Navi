"""SG Navi Task 2 API stubs. No legal decisions or official evidence."""
import json
from functools import lru_cache
from pathlib import Path

from flask import Blueprint, jsonify, request
from jsonschema import Draft202012Validator, FormatChecker
from jsonschema.exceptions import ValidationError
from shared.validate_contracts import validate
from backend.rules.engine import evaluate
from backend.versioning import current_source_version, SourceVersionUnavailable, UNAVAILABLE_SOURCE_VERSION

api = Blueprint("task2", __name__)
VERSION = "1.0"
MOCK = "mock-1"
CASE_TYPES = ["rental_deposit", "consumer_complaint"]
SCHEMA_DIR = Path(__file__).resolve().parents[2] / "frontend" / "schemas"

@lru_cache(maxsize=2)
def answers_validator(case_type):
    schema_path = SCHEMA_DIR / f"{case_type}_input.schema.json"
    schema = json.loads(schema_path.read_text(encoding="utf-8"))
    Draft202012Validator.check_schema(schema)
    return Draft202012Validator(schema, format_checker=FormatChecker())

def response(status, questions=None, warnings=None, source_version=None):
    return {
        "api_version": VERSION,
        "rule_version": MOCK,
        "source_version": source_version or UNAVAILABLE_SOURCE_VERSION,
        "status": status,
        "questions": questions or [],
        "action_card": None,
        "evidence": [],
        "warnings": warnings or [],
    }

def send(payload, definition="navigate_response", code=200):
    validate(payload, definition)
    return jsonify(payload), code

@api.get("/api/case-types")
def case_types():
    return send({"api_version": VERSION, "case_types": CASE_TYPES}, "case_types_response")

@api.get("/api/version")
def version():
    try:
        source_version = current_source_version()
    except SourceVersionUnavailable:
        return send({"api_version": VERSION, "rule_version": MOCK,
                     "source_version": UNAVAILABLE_SOURCE_VERSION}, "version_response", 503)
    return send({"api_version": VERSION, "rule_version": MOCK,
                 "source_version": source_version}, "version_response")

@api.post("/api/navigate")
def navigate():
    try:
        source_version = current_source_version()
    except SourceVersionUnavailable:
        return send(response("ERROR", warnings=[
            "Verified source data is unavailable. No decision can be made."
        ], source_version=UNAVAILABLE_SOURCE_VERSION), code=503)

    if not request.is_json:
        return send(response("ERROR", warnings=["Content-Type must be application/json."], source_version=source_version), code=415)
    payload = request.get_json(silent=True)
    if payload is None:
        return send(response("ERROR", warnings=["Request body must contain valid JSON."], source_version=source_version), code=400)
    try:
        validate(payload, "navigate_request")
    except ValidationError:
        return send(response("ERROR", warnings=["Invalid request: check api_version, case_type and answers."]), code=400)
    if not answers_validator(payload["case_type"]).is_valid(payload["answers"]):
        return send(response("ERROR", warnings=["Invalid answers for the selected case type."]), code=400)
    try:
        return send(evaluate(payload["case_type"], payload["answers"]))
    except (ValueError, OSError, KeyError):
        return send(response("ERROR", warnings=[
            "Backend rule configuration is unavailable; no conclusion can be made."
        ], source_version=UNAVAILABLE_SOURCE_VERSION), code=503)
