"""Read-only WSGI/RAG diagnostics, using synthetic facts and the real corpus.

Print JSON to stdout. Exit 0 means these backend/RAG checks passed; exit 1 means
a failure or missing connection. Browser end-to-end acceptance is separate.
"""
import json
import sys
from contextlib import ExitStack
from copy import deepcopy
from pathlib import Path
from unittest.mock import patch

import rag.retriever as retriever
from rag.citations import validate_citations
from rag.import_knowledge_base import load_knowledge_base
from shared.validate_contracts import validate


# Synthetic integration inputs, not legal eligibility examples or real disputes.
CASES = json.loads(Path(__file__).with_name("fixtures.json").read_text(encoding="utf-8"))


def collect_checks():
    checks = []

    def check(name, operation):
        try:
            details = operation()
            checks.append({"check": name, "passed": True, "details": details})
        except Exception as error:
            checks.append({"check": name, "passed": False, "error": str(error)})

    for case_type, fixture in CASES.items():
        def direct_rag(case_type=case_type, fixture=fixture):
            facts = deepcopy(fixture["answers"])
            result = retriever.retrieve_evidence(case_type, [fixture["rule_id"]], facts)
            validate(result, "retrieval_response")
            if result["retrieval_status"] != "FOUND" or not result["evidence"]:
                raise ValueError("Real corpus lookup did not return complete Evidence")
            if facts != fixture["answers"]:
                raise ValueError("Retrieval mutated the input facts")
            evidence = result["evidence"]
            validate_citations(case_type, [fixture["rule_id"]], evidence,
                               [record["evidence_id"] for record in evidence],
                               expected_source_version=evidence[0]["source_version"])
            return {"retrieval_status": result["retrieval_status"],
                    "evidence_ids": [record["evidence_id"] for record in evidence]}
        check(case_type + ":direct_rag_and_citations", direct_rag)

    # Observe the actual function without replacing its result. Also cover aliases
    # already imported by backend modules (e.g. during pytest collection).
    original = retriever.retrieve_evidence
    calls = []

    def observed(case_type, rule_ids, facts, **kwargs):
        call = {"case_type": case_type, "rule_ids": deepcopy(rule_ids),
                "facts": deepcopy(facts)}
        calls.append(call)
        result = original(case_type, rule_ids, facts, **kwargs)
        call["retrieval_status"] = result.get("retrieval_status")
        return result

    with ExitStack() as stack:
        stack.enter_context(patch.object(retriever, "retrieve_evidence", observed))
        from integration.app import create_app
        app = create_app()
        for name, module in list(sys.modules.items()):
            if name == "backend" or name.startswith("backend."):
                for attribute, value in list(vars(module).items()):
                    if value is original:
                        stack.enter_context(patch.object(module, attribute, observed))
        client = app.test_client()

        for case_type, fixture in CASES.items():
            def backend_rag(case_type=case_type, fixture=fixture):
                start = len(calls)
                request = {"api_version": "1.0", "case_type": case_type,
                           "answers": deepcopy(fixture["answers"])}
                validate(request, "navigate_request")
                response = client.post("/api/navigate", json=request)
                payload = response.get_json()
                validate(payload, "navigate_response")
                if response.status_code != 200:
                    raise ValueError("Navigation HTTP status " + str(response.status_code))
                captured = calls[start:]
                matching = [call for call in captured if call["case_type"] == case_type
                            and call["facts"] == fixture["answers"] and call["rule_ids"]
                            and call.get("retrieval_status") == "FOUND"]
                if not matching:
                    raise ValueError(
                        f"Navigation returned {payload['status']}; real retrieve_evidence "
                        f"calls={len(captured)}. Backend/RAG connection is not demonstrated."
                    )
                return {"navigation_status": payload["status"],
                        "retrieval_status": matching[0]["retrieval_status"],
                        "rag_calls": len(captured)}
            check(case_type + ":backend_to_real_rag", backend_rag)

        def versions():
            response = client.get("/api/version")
            payload = response.get_json()
            validate(payload, "version_response")
            expected = load_knowledge_base()["source_version"]
            if response.status_code != 200 or payload["source_version"] != expected:
                raise ValueError(
                    f"/api/version source_version={payload['source_version']}; "
                    f"current RAG source_version={expected}. Version reporting is inconsistent."
                )
            return {"source_version": expected, "rule_version": payload["rule_version"]}
        check("source_version_consistency", versions)

    return {"mode": "in_process_wsgi_and_real_rag", "synthetic_facts": True,
            "browser_e2e_checked": False, "passed": all(c["passed"] for c in checks),
            "checks": checks}


def main():
    result = collect_checks()
    print(json.dumps(result, indent=2))
    return 0 if result["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
