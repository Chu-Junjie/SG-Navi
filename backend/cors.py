"""Restricted cross-origin access for SG Navi's public read-only/referral API.

CORS enables requests from the current GitHub Pages origin. It is NOT client
authentication, does not make a legal decision and does not allow cookies.
"""
import os
from urllib.parse import urlsplit

from flask import Response, request

API_METHODS = {
    "/api/health": frozenset({"GET"}),
    "/api/version": frozenset({"GET"}),
    "/api/case-types": frozenset({"GET"}),
    "/api/navigate": frozenset({"POST"}),
    "/api/intake": frozenset({"POST"}),
    "/api/intake/confirm": frozenset({"POST"}),
    "/api/results/preview": frozenset({"POST"}),
    "/api/guidance": frozenset({"POST"}),
    "/api/action-plan": frozenset({"POST"}),
    "/api/action-plan/zh-hans-reviewed": frozenset({"POST"}),
}
DEFAULT_ORIGIN = "https://chu-junjie.github.io"


def _trusted_origins():
    raw = os.environ.get("SG_NAVI_CORS_ORIGINS", DEFAULT_ORIGIN)
    origins = set()
    for item in raw.split(","):
        origin = item.strip()
        parsed = urlsplit(origin)
        if (not origin or parsed.scheme != "https" or not parsed.hostname
                or parsed.username or parsed.password or parsed.path not in ("", "/")
                or parsed.query or parsed.fragment or "*" in origin
                or origin.endswith("/")):
            raise ValueError("SG_NAVI_CORS_ORIGINS must list bare HTTPS origins, not paths or wildcard URLs")
        origins.add(origin)
    return frozenset(origins)


def configure_cors(app):
    """Configure exact-origins, explicit preflight methods and no-store API output."""
    origins = _trusted_origins()

    @app.before_request
    def _preflight():
        methods = API_METHODS.get(request.path)
        if methods is None or request.method != "OPTIONS":
            return None
        method = request.headers.get("Access-Control-Request-Method")
        if not method:
            return None  # Flask's normal non-preflight OPTIONS behavior.
        if request.headers.get("Origin") not in origins:
            return Response(status=403)
        if method not in methods:
            return Response(status=405)
        asked = [h.strip().lower() for h in request.headers.get(
            "Access-Control-Request-Headers", "").split(",") if h.strip()]
        if any(h != "content-type" for h in asked):
            return Response(status=400)
        return Response(status=204)

    @app.after_request
    def _cors_response(response):
        methods = API_METHODS.get(request.path)
        if methods is None:
            return response
        response.headers["Cache-Control"] = "no-store"
        response.vary.add("Origin")
        origin = request.headers.get("Origin")
        if origin in origins:
            response.headers["Access-Control-Allow-Origin"] = origin
            if request.method == "OPTIONS" and request.headers.get("Access-Control-Request-Method"):
                response.headers["Access-Control-Allow-Methods"] = ", ".join(sorted(methods)) + ", OPTIONS"
                response.headers["Access-Control-Allow-Headers"] = "Content-Type"
                response.headers["Access-Control-Max-Age"] = "600"
        return response
