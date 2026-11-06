"""Frozen engineering targets. Does not assert a legal eligibility capability."""
from integration.task15_acceptance import run_suite, audit_source_families
import json
from pathlib import Path


def test_frozen_forty_case_engineering_targets_with_current_real_modules():
    report=run_suite()
    report["run_kind"]="regression_on_previously_executed_frozen_cases"
    target=Path(__file__).resolve().parents[2]/"instance/task15-ci-regression.json"
    target.parent.mkdir(exist_ok=True)
    target.write_text(json.dumps(report,indent=2)+"\n",encoding="utf-8")
    assert report["engineering_gates_passed"], report["gates"]
    assert audit_source_families(report)["all_passed"]
    assert not report["legal_eligibility_assessed"]
    assert report["production_state_writes"]==0
