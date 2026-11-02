"""Local-only Task 5 frontend static server + same-origin navigate API bridge.

Start the existing Flask backend separately on localhost:5000.
This development tool serves frontend/ and forwards POST /api/navigate only.
It neither changes backend rules nor generates a mock response.
"""
from __future__ import annotations

import argparse
import json
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import urlsplit
from urllib.request import Request, urlopen

FRONTEND = Path(__file__).resolve().parent


class FrontendHandler(SimpleHTTPRequestHandler):
    backend_url = "http://127.0.0.1:5000"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(FRONTEND), **kwargs)

    def do_POST(self):
        if urlsplit(self.path).path != "/api/navigate":
            self.send_error(404, "Endpoint not served by frontend proxy")
            return
        if self.headers.get("Content-Type", "").split(";")[0].strip().lower() != "application/json":
            self.respond_json(415, {"error": "Content-Type must be application/json"})
            return
        try:
            length = int(self.headers.get("Content-Length", "-1"))
        except ValueError:
            length = -1
        if not 0 < length <= 65536:
            self.respond_json(413, {"error": "JSON request must be between 1 and 65536 bytes"})
            return
        body = self.rfile.read(length)
        try:
            json.loads(body)
        except (ValueError, UnicodeDecodeError):
            self.respond_json(400, {"error": "Request JSON was invalid"})
            return
        req = Request(
            self.backend_url.rstrip("/") + "/api/navigate",
            data=body,
            headers={"Content-Type": "application/json", "Accept": "application/json"},
            method="POST",
        )
        try:
            with urlopen(req, timeout=10) as result:
                content = result.read(262144)
                self.respond_bytes(result.status, content, result.headers.get("Content-Type", "application/json"))
        except HTTPError as failure:
            content = failure.read(262144)
            self.respond_bytes(failure.code, content, failure.headers.get("Content-Type", "application/json"))
        except (URLError, TimeoutError, OSError):
            self.respond_json(502, {"error": "Backend service unavailable"})

    def respond_bytes(self, status, content, content_type):
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Cache-Control", "no-store")
        self.send_header("Content-Length", str(len(content)))
        self.end_headers()
        self.wfile.write(content)

    def respond_json(self, status, data):
        self.respond_bytes(status, json.dumps(data).encode("utf-8"), "application/json")


def main():
    parser = argparse.ArgumentParser(description="SG Navi frontend-only Task 5 integration preview")
    parser.add_argument("--port", type=int, default=8000)
    parser.add_argument("--backend", default="http://127.0.0.1:5000")
    options = parser.parse_args()
    target = urlsplit(options.backend)
    if target.scheme != "http" or target.hostname not in {"127.0.0.1", "localhost"}:
        parser.error("--backend must be local HTTP (http://127.0.0.1 or localhost)")
    handler = type("LocalFrontendHandler", (FrontendHandler,), {"backend_url": options.backend})
    server = ThreadingHTTPServer(("127.0.0.1", options.port), handler)
    print(f"Frontend: http://127.0.0.1:{options.port}/task5-flow.html")
    print(f"Real backend: {options.backend}/api/navigate")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
