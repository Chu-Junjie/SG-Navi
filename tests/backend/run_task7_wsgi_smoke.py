"""Real Gunicorn-on-loopback smoke for CI (not a public deployment test).

Run: python tests/backend/run_task7_wsgi_smoke.py
Requires gunicorn and dependencies from requirements.txt on Linux/macOS.
"""
import json
import os
import socket
import subprocess
import sys
import time
from urllib.error import URLError
from urllib.request import Request, urlopen

ORIGIN = "https://chu-junjie.github.io"


def call(base, path, *, method="GET", data=None, extra=None):
    headers = {"Origin": ORIGIN}
    headers.update(extra or {})
    payload = None if data is None else json.dumps(data).encode()
    req = Request(base + path, headers=headers, method=method, data=payload)
    with urlopen(req, timeout=5) as result:
        return result.status, result.headers, result.read()


def main():
    if os.name == "nt":
        print("Gunicorn process smoke requires POSIX; this command is for GitHub Ubuntu CI.")
        return 2

    with socket.socket() as listener:
        listener.bind(("127.0.0.1", 0))
        port = listener.getsockname()[1]

    env = dict(os.environ)
    env.pop("RENDER", None)
    env["SG_NAVI_REQUIRE_PERSISTENCE"] = "0"
    command = [
        sys.executable, "-m", "gunicorn", "--bind", f"127.0.0.1:{port}",
        "--workers", "1", "--threads", "2", "--timeout", "30",
        "backend.production:app",
    ]
    process = subprocess.Popen(command, env=env, stdout=subprocess.DEVNULL,
                               stderr=subprocess.PIPE, text=True)
    base = f"http://127.0.0.1:{port}"
    try:
        for _ in range(80):
            if process.poll() is not None:
                raise RuntimeError("Gunicorn failed at startup: " + process.stderr.read()[-1000:])
            try:
                code, headers, body = call(base, "/api/health")
                if code == 200 and json.loads(body) == {"status": "ok"}:
                    break
            except (URLError, TimeoutError, OSError):
                time.sleep(0.1)
        else:
            raise RuntimeError("Gunicorn did not become healthy on loopback")

        assert headers.get("Access-Control-Allow-Origin") == ORIGIN
        code, _, body = call(base, "/api/version")
        version = json.loads(body)
        assert code == 200 and version["source_version"].startswith("kb-")
        assert version["rule_version"] == "mock-1"

        code, headers, _ = call(base, "/api/navigate", method="OPTIONS", extra={
            "Access-Control-Request-Method": "POST",
            "Access-Control-Request-Headers": "content-type"
        })
        assert code == 204 and headers.get("Access-Control-Allow-Origin") == ORIGIN

        inputs = {
            "rental_deposit": {"dispute_with": "landlord", "premises_type": "residential",
                               "claim_amount_sgd": 123},
            "consumer_complaint": {"purchase_type": "goods",
                                   "purchase_purpose": "personal",
                                   "supplier_registered_in_sg": True,
                                   "claim_amount_sgd": 123},
        }
        for case, answers in inputs.items():
            code, headers, body = call(base, "/api/navigate", method="POST", data={
                "api_version": "1.0", "case_type": case, "answers": answers
            }, extra={"Content-Type": "application/json"})
            result = json.loads(body)
            assert code == 200 and result["status"] == "REFER_TO_OFFICIAL"
            assert result["evidence"] and result["action_card"] is None
            assert headers.get("Access-Control-Allow-Origin") == ORIGIN
        print("PASS real local Gunicorn health/version/CORS/OPTIONS/Rental/Consumer")
        return 0
    finally:
        process.terminate()
        try:
            process.communicate(timeout=5)
        except subprocess.TimeoutExpired:
            process.kill()
            process.communicate(timeout=5)


if __name__ == "__main__":
    raise SystemExit(main())
