"""SG Navi Task 2 API stubs. No legal decisions or official evidence."""
from flask import Blueprint, jsonify, request
from jsonschema.exceptions import ValidationError
from shared.validate_contracts import validate

api = Blueprint("task2", __name__)
VERSION = "1.0"
MOCK = "mock-1"
CASE_TYPES = ["rental_deposit", "consumer_complaint"]

def response(status, questions=None, warnings=None):
    return {
        "api_version": VERSION,
        "rule_version": MOCK,
        "source_version": MOCK,
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
    return send({"api_version": VERSION, "rule_version": MOCK, "source_version": MOCK}, "version_response")

@api.post("/api/navigate")
def navigate():
    if not request.is_json:
        return send(response("ERROR", warnings=["Content-Type must be application/json."]), code=415)
    payload = request.get_json(silent=True)
    if payload is None:
        return send(response("ERROR", warnings=["Request body must contain valid JSON."]), code=400)
    try:
        validate(payload, "navigate_request")
    except ValidationError:
        return send(response("ERROR", warnings=["Invalid request: check api_version, case_type and answers."]), code=400)
    question = {
        "id": "claim_amount_sgd",
        "label": "What is the disputed amount in SGD?",
        "input_type": "number",
        "required": True,
    }
    if payload["answers"].get("claim_amount_sgd") in (None, "unknown"):
        return send(response("NEED_CLARIFICATION", questions=[question]))
    return send(response("REFER_TO_OFFICIAL", warnings=[
        "Task 2 mock only; no eligibility or official evidence has been verified."
    ]))
