"""Minimal SG Navi Task 1 backend.

Run from the repository root with: python -m flask --app backend.app run
"""
from pathlib import Path

from flask import Flask, jsonify, send_from_directory


FRONTEND_DIR = Path(__file__).resolve().parent.parent / "frontend"


def create_app() -> Flask:
    """Create the minimal web application, without case-routing logic."""
    app = Flask(__name__, static_folder=None)

    @app.get("/api/health")
    def health():
        return jsonify({"status": "ok"}), 200

    @app.get("/")
    def homepage():
        return send_from_directory(FRONTEND_DIR, "index.html")

    @app.get("/assets/<path:filename>")
    def frontend_assets(filename: str):
        return send_from_directory(FRONTEND_DIR / "assets", filename)

    return app


app = create_app()
