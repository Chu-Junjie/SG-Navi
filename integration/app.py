"""Serve the existing frontend and backend at one local development origin.

Run: python -m flask --app integration.app run --host 127.0.0.1 --port 5000
This configures static delivery only; module owners still implement their transports.
"""
from flask import send_from_directory

from backend.app import FRONTEND_DIR, create_app as create_backend_app


def create_app():
    app = create_backend_app()
    for page in ("task5-flow.html", "task4-forms.html", "task3-mapping.html", "mock-preview.html"):
        app.add_url_rule(
            "/" + page, endpoint="integration_page_" + page,
            view_func=lambda page=page: send_from_directory(FRONTEND_DIR, page),
        )
    for directory in ("js", "schemas", "mappings", "mocks"):
        app.add_url_rule(
            "/" + directory + "/<path:filename>",
            endpoint="integration_static_" + directory,
            view_func=lambda filename, directory=directory: send_from_directory(
                FRONTEND_DIR / directory, filename
            ),
        )
    return app
