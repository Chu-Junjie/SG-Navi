"""Task 24 experimental reviewer preview. Default CLOSED, not an approved API.

Only a local test/development Flask config switch can expose this route.
Production /api/action-plan stays untouched and English Action Plan 1.0.
"""
from flask import Blueprint, current_app, jsonify, request
from jsonschema import ValidationError

from backend.action_plan_service import process_action_plan
from backend.task24_bilingual import preview_zh_hans
from backend.task24_delivery import reviewed_overlay, ChineseTranslationNotApproved
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


@task24_preview.post("/api/action-plan/zh-hans-reviewed")
def reviewed_chinese():
    """Opt-in reviewed sidecar, explicitly unavailable without owner signoff.

    The canonical English API is unaffected. Do NOT enable production until
    the contract and UI approval is recorded and frontend consumes it safely.
    """
    if current_app.config.get("TASK24_ENABLE_REVIEWED_LOCALE") is not True:
        return "", 404
    if not request.is_json:
        return jsonify({"error": "invalid_request"}), 415
    if (request.content_length is not None and request.content_length > MAX_BYTES
            or len(request.get_data(cache=True)) > MAX_BYTES):
        return jsonify({"error": "request_too_large"}), 413
    body = request.get_json(silent=True)
    if not isinstance(body, dict):
        return jsonify({"error": "invalid_request"}), 400
    try:
        validate_action_plan(body, "request")
    except (ValidationError, ValueError, KeyError, TypeError):
        return jsonify({"error": "invalid_request"}), 400
    try:
        canonical = process_action_plan(body)
        overlay = reviewed_overlay(canonical)
    except ChineseTranslationNotApproved:
        return jsonify({
            "error": "translation_not_approved",
            "message": "Reviewed Chinese content is not available; use the canonical English API.",
        }), 503
    except (OSError, RuntimeError):
        return jsonify({"error": "service_unavailable"}), 503
    return jsonify(overlay), 200
