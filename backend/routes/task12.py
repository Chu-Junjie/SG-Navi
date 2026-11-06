"""Task 12 provisional additive research-guidance API (not v1 Action Card)."""
from flask import Blueprint, jsonify, request
from jsonschema import ValidationError

from backend.results import assemble
from backend.routes.task2 import answers_validator

results_api = Blueprint("task12_results", __name__)
MAX_BODY_BYTES = 8192
CASES = ("rental_deposit", "consumer_complaint")

def _problem(message, status):
    return jsonify({"results_version": "0.1", "guidance_status": "ERROR",
                    "research_guidance": None, "display_evidence": [],
                    "limitations": [message]}), status

@results_api.post("/api/results/preview")
def preview_results():
    if not request.is_json:
        return _problem("JSON Content-Type required.", 415)
    if request.content_length is not None and request.content_length > MAX_BODY_BYTES:
        return _problem("Request is too large.", 413)
    if len(request.get_data(cache=True)) > MAX_BODY_BYTES:
        return _problem("Request is too large.", 413)
    body = request.get_json(silent=True)
    if (not isinstance(body, dict) or set(body) !=
            {"results_version", "confirmed", "case_type", "confirmed_answers"}
            or body.get("results_version") != "0.1"
            or body.get("confirmed") is not True
            or body.get("case_type") not in CASES
            or not isinstance(body.get("confirmed_answers"), dict)):
        return _problem("A supported case with explicitly confirmed structured facts is required.", 400)
    answers = body["confirmed_answers"]
    try:
        if (not answers_validator(body["case_type"]).is_valid(answers)
                or any(isinstance(value, str) and
                       (len(value) > 200 or any(ord(char) < 32 for char in value))
                       for value in answers.values())):
            return _problem("Invalid confirmed answers.", 400)
        result = assemble(body["case_type"], answers)
        return jsonify(result), 200
    except (ValidationError, OSError, ValueError, KeyError, TypeError):
        return _problem("Verified source context is unavailable; no guidance can be confirmed.", 503)
