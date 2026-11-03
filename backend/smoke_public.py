"""Task 7 REAL HTTPS smoke audit for a deployed SG Navi API.

After provider deploy, run:
python -m backend.smoke_public --base-url https://ACTUAL-SERVICE.onrender.com

Fails if HTTPS/CORS/schema/real RAG referral behavior does not match contract.
Uses synthetic case facts only. Does not inject failures or prove external link
navigation, persistent-disk restart, or supported legal eligibility.
"""
import argparse
import json
from datetime import datetime, timezone
from urllib.error import HTTPError, URLError
from urllib.parse import urlsplit
from urllib.request import Request, urlopen

from shared.validate_contracts import validate

ORIGIN = "https://chu-junjie.github.io"
CASES = {
    "rental_deposit": {
        "dispute_with": "landlord", "premises_type": "residential",
        "claim_amount_sgd": 123,
    },
    "consumer_complaint": {
        "purchase_type": "goods", "purchase_purpose": "personal",
        "supplier_registered_in_sg": True, "claim_amount_sgd": 123,
    },
}


def _request(base, path, *, method="GET", payload=None, headers=None):
    wire = json.dumps(payload).encode("utf-8") if payload is not None else None
    h = dict(headers or {})
    if payload is not None:
        h["Content-Type"] = "application/json"
    request = Request(base + path, data=wire, headers=h, method=method)
    try:
        with urlopen(request, timeout=25) as response:
            return response.status, dict(response.headers.items()), response.read()
    except HTTPError as error:
        return error.code, dict(error.headers.items()), error.read()


def run(base):
    parsed = urlsplit(base)
    if (parsed.scheme != "https" or not parsed.hostname or parsed.username
            or parsed.password or parsed.query or parsed.fragment or parsed.path not in ("", "/")):
        raise ValueError("A deployed HTTPS origin (without path/query) is required")
    base = base.rstrip("/")
    checks = []

    def attempt(name, task):
        try:
            details = task()
            checks.append({"name": name, "passed": True, "actual": details})
        except Exception as error:
            checks.append({"name": name, "passed": False, "error": str(error)})

    def decode(code, headers, body, expected_code, definition):
        if code != expected_code:
            raise ValueError(f"Expected HTTP {expected_code}, got {code}")
        data = json.loads(body)
        validate(data, definition)
        if headers.get("Access-Control-Allow-Origin") != ORIGIN:
            raise ValueError("Required GitHub Pages CORS origin missing")
        return data

    def check_version():
        code, headers, body = _request(base, "/api/version", headers={"Origin": ORIGIN})
        d = decode(code, headers, body, 200, "version_response")
        if d["api_version"] != "1.0" or d["rule_version"] != "mock-1":
            raise ValueError("Unexpected API or rule version")
        if not d["source_version"].startswith("kb-"):
            raise ValueError("Unverified source version")
        return d

    version = {}
    def get_version():
        v = check_version()
        version.update(v)
        return v

    attempt("GET /api/version", get_version)

    def health():
        code, headers, body = _request(base, "/api/health", headers={"Origin": ORIGIN})
        d = decode(code, headers, body, 200, "health_response")
        assert d["status"] == "ok"
        return {"http": code, "body": d}

    attempt("GET /api/health", health)

    def case_types():
        code, headers, body = _request(base, "/api/case-types", headers={"Origin": ORIGIN})
        d = decode(code, headers, body, 200, "case_types_response")
        assert set(d["case_types"]) == set(CASES)
        return d

    attempt("GET /api/case-types", case_types)

    for case_type, facts in CASES.items():
        def preflight(case=case_type):
            code, headers, _ = _request(base, "/api/navigate", method="OPTIONS",
                headers={"Origin": ORIGIN, "Access-Control-Request-Method": "POST",
                         "Access-Control-Request-Headers": "content-type"})
            if code != 204 or headers.get("Access-Control-Allow-Origin") != ORIGIN:
                raise ValueError(f"CORS preflight failed ({code})")
            if "POST" not in headers.get("Access-Control-Allow-Methods", ""):
                raise ValueError("POST not in allow-methods")
            if "content-type" not in headers.get("Access-Control-Allow-Headers", "").lower():
                raise ValueError("Content-Type missing from allow-headers")
            return {"http": code, "origin": headers["Access-Control-Allow-Origin"]}

        attempt(case_type + ": OPTIONS preflight", preflight)

        def navigate(case=case_type, answers=facts):
            code, headers, body = _request(base, "/api/navigate", method="POST",
                payload={"api_version": "1.0", "case_type": case, "answers": answers},
                headers={"Origin": ORIGIN})
            d = decode(code, headers, body, 200, "navigate_response")
            if d["status"] != "REFER_TO_OFFICIAL" or d["action_card"] is not None:
                raise ValueError("Unexpected legal recommendation/status")
            if not d["evidence"] or any(e["review_status"] != "verified" for e in d["evidence"]):
                raise ValueError("No verified contextual evidence")
            if version and d["source_version"] != version["source_version"]:
                raise ValueError("Version mismatch between version endpoint and navigation")
            return {"http": code, "status": d["status"], "source_version": d["source_version"],
                    "evidence_ids": [e["evidence_id"] for e in d["evidence"]],
                    "action_card_is_null": True}

        attempt(case_type + ": POST real source referral", navigate)

    def missing():
        code, headers, body = _request(base, "/api/navigate", method="POST",
            payload={"api_version": "1.0", "case_type": "rental_deposit", "answers": {}},
            headers={"Origin": ORIGIN})
        d = decode(code, headers, body, 200, "navigate_response")
        assert d["status"] == "NEED_CLARIFICATION" and d["questions"] and not d["evidence"]
        return {"status": d["status"], "questions": [q["id"] for q in d["questions"]]}

    attempt("POST missing facts safely clarify", missing)

    def malformed():
        code, headers, body = _request(base, "/api/navigate", method="POST",
            payload={"api_version": "1.0", "case_type": "rental_deposit", "answers": []},
            headers={"Origin": ORIGIN})
        d = decode(code, headers, body, 400, "navigate_response")
        assert d["status"] == "ERROR" and not d["evidence"] and d["action_card"] is None
        return {"http": code, "status": d["status"]}

    attempt("POST invalid contract safely rejected", malformed)

    def forbidden_origin():
        code, headers, _ = _request(base, "/api/navigate", method="OPTIONS",
            headers={"Origin": "https://other.example.org",
                     "Access-Control-Request-Method": "POST"})
        if code != 403 or headers.get("Access-Control-Allow-Origin"):
            raise ValueError("Unapproved Origin can preflight the public service")
        return {"http": code, "origin_allowed": False}

    attempt("OPTIONS unauthorized Origin rejected", forbidden_origin)
    return {"scope": "real_remote_https_wire_smoke", "base_url": base,
            "executed_at": datetime.now(timezone.utc).isoformat(),
            "synthetic_facts": True, "passed": all(c["passed"] for c in checks),
            "checks": checks, "limits": [
                "No forced RAG/source failure injection against the public service",
                "Persistent-disk restart and rollback require separate provider evidence",
                "No browser UI/outgoing source tab acceptance or legal supported Action Card",
            ]}


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--base-url", required=True, help="Actual provider HTTPS origin")
    args = p.parse_args()
    try:
        record = run(args.base_url)
    except (ValueError, URLError, OSError) as error:
        record = {"passed": False, "error": str(error)}
    print(json.dumps(record, indent=2))
    return 0 if record["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
