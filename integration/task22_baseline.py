"""Record legacy intake observations before the action-plan service is available."""

import argparse
import hashlib
import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

from backend.app import create_app
from shared.validate_action_plan import context_revision

CASES = Path(__file__).resolve().parents[1] / "tests/integration/task22_cases.json"


def load_frozen_cases():
    raw = CASES.read_text(encoding="utf-8").encode("utf-8")
    digest = hashlib.sha256(raw).hexdigest()
    expected = CASES.with_suffix(".sha256").read_text(encoding="ascii").strip()
    if digest != expected:
        raise ValueError("Task 22 frozen fixture digest changed")
    suite = json.loads(raw)
    cases = suite["cases"]
    if Counter(c["group"] for c in cases) != {"rental": 15, "consumer": 15, "boundary": 10}:
        raise ValueError("Invalid frozen case distribution")
    if len({c["id"] for c in cases}) != 40 or len({c["description"] for c in cases}) != 40:
        raise ValueError("Duplicate frozen case")
    for row in cases:
        expectation = row["expected"]
        if expectation["case_type"] is None:
            if row["confirmed_facts"]:
                raise ValueError("Unsupported input cannot have confirmed case facts")
            continue
        context_revision({
            "case_type": expectation["case_type"], "issue_subtype": expectation["issue_subtype"],
            "goal": expectation["goal"], "facts": row["confirmed_facts"],
            "summary": "Synthetic fixture validation",
        })
        if expectation.get("question_field") in row["confirmed_facts"]:
            raise ValueError("Expected question repeats a confirmed fact")
    return suite, digest


def run_baseline():
    suite, digest = load_frozen_cases()
    client = create_app().test_client()
    probe = client.post("/api/action-plan", json={
        "action_plan_version": "1.0", "request_id": "task22-baseline",
        "operation": "interpret", "description": "I received an unexplained restaurant charge.",
    })
    if probe.status_code != 404:
        raise RuntimeError("Action-plan readiness has changed. Use the integrated acceptance procedure.")
    observations = []
    hits = Counter()
    for case in suite["cases"]:
        response = client.post("/api/intake", json={
            "intake_version": "1.0", "description": case["description"],
        })
        data = response.get_json()
        if response.status_code != 200 or not isinstance(data, dict):
            raise RuntimeError("Unexpected legacy intake response for " + case["id"])
        suggested = data.get("suggested_case_type")
        match = suggested == case["expected"]["case_type"] if case["group"] != "boundary" else None
        if match:
            hits[case["group"]] += 1
        observations.append({
            "id": case["id"], "group": case["group"], "legacy_http": response.status_code,
            "intake_status": data["intake_status"], "suggested_case_type": suggested,
            "expected_case_type": case["expected"]["case_type"], "legacy_core_case_match": match,
            "response_sha256": hashlib.sha256(response.data).hexdigest(),
        })
    return {
        "scope": "Real local legacy intake responses. Only core case recognition is counted.",
        "executed_at_utc": datetime.now(timezone.utc).isoformat(),
        "fixture_version": suite["fixture_version"], "fixture_sha256": digest,
        "scoring_version": suite["scoring_version"], "planned_endpoint_http": probe.status_code,
        "legacy_core_case_matches": {group: hits[group] for group in ("rental", "consumer")},
        "observations": observations,
        "new_action_acceptance": "NOT_RUN", "public_browser_acceptance": "NOT_RUN",
        "human_comprehension": "NOT_RUN",
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    report = run_baseline()
    with args.output.open("x", encoding="utf-8") as stream:
        json.dump(report, stream, indent=2)
        stream.write("\n")
    print(json.dumps({
        "cases": len(report["observations"]), "planned_endpoint_http": report["planned_endpoint_http"],
        "legacy_core_case_matches": report["legacy_core_case_matches"],
    }))


if __name__ == "__main__":
    main()
