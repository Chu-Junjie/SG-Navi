"""Task 24 experimental reviewer preview. Default CLOSED, not an approved API.

Only a local test/development Flask config switch can expose this route.
Production /api/action-plan stays untouched and English Action Plan 1.0.
"""
from flask import Blueprint, current_app, jsonify, request
from jsonschema import ValidationError

from backend.action_plan_service import process_action_plan
from backend.task24_bilingual import preview_zh_hans
from shared.validate_action_plan import validate_action_plan

task24_preview = Blueprint("task24_preview", __name__)
MAX_BYTES = 8192


@task24_preview.post("/api/action-plan/zh-hans-preview")
def bilingual_preview():
    if current_app.config.get("TASK24_ENABLE_UNREVIEWED_PREVIEW") is not True:
        return "", 404
    if not request.is_json:
        return jsonify({"error": "invalid_request"}), 415
    if (request.content_length is not None and request.content_length > MAX_BYTES
            or len(request.get_data(cache=True)) > MAX_BYTES):
        return jsonify({"error": "request_too_large"}), 413
    req = request.get_json(silent=True)
    if not isinstance(req, dict):
        return jsonify({"error": "invalid_request"}), 400
    try:
        validate_action_plan(req, "request")
        original = process_action_plan(req)
        result = preview_zh_hans(original)
        return jsonify(result), 200
    except (ValidationError, ValueError, TypeError, KeyError):
        return jsonify({"error": "invalid_request"}), 400
    except OSError:
        return jsonify({"error": "preview_unavailable"}), 503
