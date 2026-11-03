"""Read-only HTTPS public deployment probe with synthetic SG Navi facts.

Usage:
  python -m backend.public_probe --base-url https://<actual-hostname>.onrender.com

No requests to a paid service occur unless the operator supplies the real URL.
This probes the deployed service, not just Flask's in-process test client.
"""
import argparse
import json
from urllib.error import HTTPError
from urllib.parse import urlsplit
from urllib.request import Request, urlopen

from rag.import_knowledge_base import load_knowledge_base
from shared.validate_contracts import validate

ORIGIN = "https://chu-junjie.github.io"
INPUTS = {
    "rental_deposit": {
        "dispute_with": "landlord",
        "premises_type": "residential",
        "claim_amount_sgd": 123,
    },
    "consumer_complaint": {
        "purchase_type": "goods",
        "purchase_purpose": "personal",
        "supplier_registered_in_sg": True,
        "claim_amount_sgd": 123,
    },
}


def call(base, path, method="GET", payload=None, headers=None):
    body = None if payload is None else json.dumps(payload).encode("utf-8")
    req = Request(base + path, data=body, method=method,
                  headers=headers or {})
    try:
        with urlopen(req, timeout=20) as resp:
            return resp.status, dict(resp.headers), resp.read()
    except HTTPError as error:
        return error.code, dict(error.headers), error.read()


def probe(base):
    parsed = urlsplit(base)
    if (parsed.scheme != "https" or not parsed.hostname or parsed.username or parsed.password
            or parsed.path not in ("", "/") or parsed.query or parsed.fragment):
        raise ValueError("Pass the actual HTTPS API origin, not a path or an HTTP URL")
    base = base.rstrip("/")
    report = {"base_url": base, "checks": [], "passed": False}

    def check(name, action):
        try:
            outcome = action()
            report["checks"].append({"check": name, "status": "PASS", "detail": outcome})
        except Exception as error:
            report["checks"].append({"check": name, "status": "FAIL", "error": str(error)})

    def check_endpoint(path, definition):
        code, headers, body = call(base, path, headers={"Origin": ORIGIN})
        data = json.loads(body)
        validate(data, definition)
        assert code == 200, f"HTTP {code}"
        assert headers.get("Access-Control-Allow-Origin") == ORIGIN
        return data

    check("health", lambda: check_endpoint("/api/health", "health_response"))
    check("case_types", lambda: check_endpoint("/api/case-types", "case_types_response"))

    def version():
        data = check_endpoint("/api/version", "version_response")
        assert data["source_version"] == load_knowledge_base()["source_version"]
        assert data["rule_version"] == "mock-1"
        assert data["api_version"] == "1.0"
        return data
    check("version_and_local_corpus", version)

    def preflight(method):
        code, headers, _ = call(base, "/api/navigate" if method == "POST" else "/api/version",
                                method="OPTIONS", headers={
                                    "Origin": ORIGIN,
                                    "Access-Control-Request-Method": method,
                                    "Access-Control-Request-Headers": "content-type",
                                })
        assert code == 204
        assert headers.get("Access-Control-Allow-Origin") == ORIGIN
        assert method in headers.get("Access-Control-Allow-Methods", "")
        assert "content-type" in headers.get("Access-Control-Allow-Headers", "").lower()
        assert not headers.get("Access-Control-Allow-Credentials")
        return {"http_status": code, "method": method}
    check("cors_options_get", lambda: preflight("GET"))
    check("cors_options_post", lambda: preflight("POST"))

    def navigate(case, facts, expected):
        request = {"api_version": "1.0", "case_type": case, "answers": facts}
        validate(request, "navigate_request")
        code, headers, raw = call(base, "/api/navigate", method="POST", payload=request,
                                   headers={"Origin": ORIGIN, "Content-Type": "application/json"})
        data = json.loads(raw)
        validate(data, "navigate_response")
        assert code == 200
        assert headers.get("Access-Control-Allow-Origin") == ORIGIN
        assert data["status"] == expected
        assert data["action_card"] is None
        assert data["source_version"] == load_knowledge_base()["source_version"]
        if expected == "REFER_TO_OFFICIAL":
            assert data["evidence"], "Official source context must not be empty"
            assert all(r["review_status"] == "verified"
                       and r["source_version"] == data["source_version"]
                       for r in data["evidence"])
        else:
            assert data["questions"] and data["evidence"] == []
        return {"http_status": code, "status": data["status"],
                "evidence_ids": [x["evidence_id"] for x in data["evidence"]],
                "questions": [x["id"] for x in data["questions"]]}

    for case, facts in INPUTS.items():
        check(case + "_complete", lambda case=case, facts=facts: navigate(
            case, facts, "REFER_TO_OFFICIAL"))
        check(case + "_missing", lambda case=case: navigate(
            case, {}, "NEED_CLARIFICATION"))

    def reject_bad_request():
        code, headers, body = call(base, "/api/navigate", method="POST",
            payload={"api_version": "1.0", "case_type": "rental_deposit", "answers": {},
                     "simulate_supported": True},
            headers={"Origin": ORIGIN, "Content-Type": "application/json"})
        validate(json.loads(body), "navigate_response")
        assert code == 400 and json.loads(body)["status"] == "ERROR"
        return {"http_status": code}
    check("synthetic_supported_override_rejected", reject_bad_request)

    def reject_foreign_origin():
        code, headers, _ = call(base, "/api/navigate", method="OPTIONS",
                                headers={"Origin": "https://invalid.example",
                                         "Access-Control-Request-Method": "POST"})
        assert code == 403
        assert not headers.get("Access-Control-Allow-Origin")
        return {"http_status": code}
    check("foreign_origin_preflight", reject_foreign_origin)

    report["passed"] = all(item["status"] == "PASS" for item in report["checks"])
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base-url", required=True)
    args = parser.parse_args()
    result = probe(args.base_url)
    print(json.dumps(result, indent=2))
    return 0 if result["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
