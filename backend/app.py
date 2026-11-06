"""Minimal SG Navi Task 1 backend.

Run from the repository root with: python -m flask --app backend.app run
"""
from pathlib import Path

from flask import Flask, jsonify, send_from_directory

from backend.routes.task2 import api as task2_api
from backend.routes.task11 import intake_api
from backend.routes.task12 import results_api
from backend.cors import configure_cors
from backend.versioning import current_source_version, SourceVersionUnavailable


FRONTEND_DIR = Path(__file__).resolve().parent.parent / "frontend"


def create_app() -> Flask:
    """Create the minimal web application, without case-routing logic."""
    app = Flask(__name__, static_folder=None)
    app.register_blueprint(task2_api)
    app.register_blueprint(intake_api)
    app.register_blueprint(results_api)
    configure_cors(app)

    @app.get("/api/health")
    def health():
        # Readiness includes the same validated corpus and durable state used by
        # navigation. A running process alone must not make the homepage say ready.
        try:
            current_source_version()
        except SourceVersionUnavailable:
            return jsonify({"status": "unavailable"}), 503
        return jsonify({"status": "ok"}), 200

    @app.get("/")
    def homepage():
        return send_from_directory(FRONTEND_DIR, "index.html")

    @app.get("/assets/<path:filename>")
    def frontend_assets(filename: str):
        return send_from_directory(FRONTEND_DIR / "assets", filename)

    return app


app = create_app()
