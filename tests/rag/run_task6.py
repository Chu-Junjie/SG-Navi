"""Run all RAG tests once and record RAG-01..12 from actual pytest JUnit results.

Run from repository root: python -X utf8 tests/rag/run_task6.py
No live network or publisher review is performed. Temporary audit files stay in
ignored instance/; an explicit --output may publish the resulting synthetic log.
"""
import argparse
import hashlib
import json
import platform
import subprocess
import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path
from xml.etree import ElementTree as ET

ROOT = Path(__file__).resolve().parents[2]
MATRIX = Path(__file__).with_name("task6_matrix.json")
KB = ROOT / "rag" / "knowledge_base"


def digests(paths):
    return {str(path.relative_to(ROOT)).replace("\\", "/"): hashlib.sha256(path.read_bytes()).hexdigest()
            for path in sorted(paths)}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=ROOT / "instance" / "task6-rag-results.json")
    args = parser.parse_args()
    args.output = args.output.resolve()
    if args.output.suffix != ".json" or not any(args.output.is_relative_to(directory.resolve())
                                               for directory in (ROOT / "instance", ROOT / "docs/test-results")):
        parser.error("--output must be a JSON report under instance/ or docs/test-results/")
    matrix = json.loads(MATRIX.read_text(encoding="utf-8"))
    expected_ids = [f"RAG-{i:02}" for i in range(1, 13)]
    if [case["test_id"] for case in matrix["cases"]] != expected_ids:
        raise ValueError("The RAG matrix must define exactly RAG-01 through RAG-12 in order")
    started = datetime.now(timezone.utc).isoformat(timespec="seconds")
    canonical_before = digests(KB.iterdir())
    audit_files = [*ROOT.joinpath("rag").glob("*.py"), *ROOT.joinpath("tests/rag").glob("*.py"), MATRIX]
    code_hashes = digests(audit_files)
    commit = subprocess.run(["git", "rev-parse", "HEAD"], cwd=ROOT, check=True,
                            capture_output=True, text=True, encoding="utf-8").stdout.strip()
    artifact_dir = ROOT / "instance" / "task6-rag" / uuid.uuid4().hex
    artifact_dir.mkdir(parents=True)
    xml = artifact_dir / "pytest.xml"
    command = [sys.executable, "-X", "utf8", "-m", "pytest", "tests/rag", "-q", "--junitxml", str(xml)]
    run = subprocess.run(command, cwd=ROOT, capture_output=True, text=True,
                         encoding="utf-8", timeout=240, check=False)
    (artifact_dir / "pytest-output.txt").write_text(run.stdout + "\n" + run.stderr, encoding="utf-8")
    canonical_after = digests(KB.iterdir())
    cases = []
    if xml.exists():
        for case in ET.parse(xml).iter("testcase"):
            module = case.get("classname", "").replace(".", "/").split("tests/rag/")[-1]
            node = module + ".py::" + case.get("name", "")
            status = "FAIL" if case.find("failure") is not None or case.find("error") is not None else (
                "NOT_RUN" if case.find("skipped") is not None else "PASS")
            cases.append({"node": node, "status": status})
    results = []
    for group in matrix["cases"]:
        selected = []
        missing = []
        for selector in group["pytest_nodes"]:
            matched = [case for case in cases if case["node"] == selector or (
                "[" not in selector and case["node"].split("[", 1)[0] == selector)]
            if not matched:
                missing.append(selector)
            selected.extend(case for case in matched if case not in selected)
        status = "FAIL" if any(case["status"] == "FAIL" for case in selected) else (
            "NOT_RUN" if missing or not selected or any(case["status"] == "NOT_RUN" for case in selected) else "PASS")
        results.append({**group, "status": status, "actual": {
            "passed": sum(case["status"] == "PASS" for case in selected),
            "failed": sum(case["status"] == "FAIL" for case in selected),
            "not_run": sum(case["status"] == "NOT_RUN" for case in selected),
            "missing_selectors": missing, "executed_testcases": selected},
            "code_commit": commit, "tester": "Codex automated pytest execution", "executed_at": started})
    passed = run.returncode == 0 and canonical_before == canonical_after and all(g["status"] == "PASS" for g in results)
    report = {"status": "PASS" if passed else "FAIL", "matrix_definition": matrix["definition"],
              "started_at": started, "finished_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
              "code_commit": commit,
              "code_state": "Working tree derived from code_commit; audited_file_sha256 identifies the exact tested files",
              "source_version": json.loads((KB / "rule_evidence_map.json").read_text(encoding="utf-8"))["source_version"],
              "audited_file_sha256": code_hashes,
              "environment": {"python": platform.python_version(), "platform": platform.system()},
              "command": ["python", "-X", "utf8", "-m", "pytest", "tests/rag", "-q", "--junitxml", str(xml.relative_to(ROOT)).replace("\\", "/")],
              "pytest_exit_code": run.returncode, "pytest_summary": run.stdout.strip().splitlines()[-1:] or [run.stderr.strip()],
              "canonical_unchanged": canonical_before == canonical_after, "canonical_sha256": canonical_after,
              "suite_counts": {"passed": sum(c["status"] == "PASS" for c in cases),
                               "failed": sum(c["status"] == "FAIL" for c in cases),
                               "not_run": sum(c["status"] == "NOT_RUN" for c in cases)},
              "network": "No publisher requests; network/state damage tests use isolated synthetic fixtures",
              "results": results}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    for result in results:
        print(f"{result['test_id']} {result['status']}: {result['title']}")
    print(f"Overall {report['status']}; pytest exit {run.returncode}; output {args.output}")
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
