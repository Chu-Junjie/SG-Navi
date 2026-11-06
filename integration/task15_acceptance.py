"""Frozen 40-case engineering acceptance, not external users or a legal benchmark.

The routing set was committed before integration changes. Expected facts are
permitted extraction bounds; confirmed answers are independent synthetic user
inputs. Provenance/checklist scoring uses frozen approved corpus templates,
not unrestricted generated legal assertions. Initial and later runs are distinct.
"""
import argparse
import hashlib
import json
import re
import shutil
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import patch

from backend.app import create_app
from rag.import_knowledge_base import DEFAULT_KB, load_knowledge_base
from rag.repository import EvidenceRepository, RepositoryError
from shared.validate_guidance import validate_guidance

ROOT = Path(__file__).resolve().parents[1]
CASES = ROOT / "tests/integration/task15_cases.json"
SCORING_VERSION = "task15-provenance-routing-1"


def sanitize_query(text):
    text = text.replace("S$", "SGD ")
    return " ".join(re.sub(r"[^a-zA-Z0-9 ,.!?'-]", " ", text).split())[:300] or None


def _expected_templates(case):
    facts = case.get("user_confirmed_answers", {})
    if case.get("expected_guidance_status") != "GUIDANCE_ONLY":
        return []
    if case["expected_case_type"] == "consumer_complaint":
        return ["consumer-case-review", "consumer-sct-review"]
    if facts.get("dispute_with") == "agent":
        return ["agent-conduct-complaint"] if "conduct" in case["description"] else ["agency-contract-review"]
    return ["rental-sct-review"]


def _support(output, bundle):
    rows = output.get("display_evidence", [])
    by_id = {r["evidence_id"]: r for r in rows}
    valid = len(by_id) == len(rows)
    for eid, row in by_id.items():
        p = bundle["passages"].get(eid, {})
        source = bundle["sources"].get(p.get("source_id"), {})
        valid = valid and bool(p) and row["verbatim_excerpt"] == p["text"] and row["url"] == p["url"] == source["url"]
        valid = valid and row["source_version"] == bundle["source_version"] and row["reviewed_at"] == source["reviewed_at"]
        valid = valid and row["excerpt_sha256"] == hashlib.sha256(row["verbatim_excerpt"].encode()).hexdigest() == p["excerpt_sha256"]
        valid = valid and row["display_state"] == "verified_snapshot" and row["preview"] is None
    allowed = set()
    for template in bundle["templates"].values():
        if template["review_status"] != "verified":
            continue
        ids = {eid for s in ("conditions", "steps", "document_checklist", "limitations") for item in template[s] for eid in item["evidence_ids"]}
        allowed.add(("potential_channels", template["channel"] + " (conditional official source to check; not eligibility)", tuple(sorted(ids))))
        for section in ("conditions", "steps", "document_checklist"):
            allowed.update((section, item["text"], tuple(sorted(item["evidence_ids"]))) for item in template[section])
    assertions = output.get("claim_citations", [])
    supported = sum(bool(valid and set(c["evidence_ids"]) <= set(by_id) and
                    (c["section"], c["text"], tuple(sorted(c["evidence_ids"]))) in allowed) for c in assertions)
    return len(assertions), supported, bool(valid)


def run_suite():
    raw = CASES.read_text(encoding="utf-8").encode()
    frozen_hash = (CASES.with_suffix(".sha256")).read_text().strip()
    assert hashlib.sha256(raw).hexdigest() == frozen_hash, "Acceptance inputs changed after freeze"
    data = json.loads(raw)
    assert len(data["cases"]) == 40
    bundle = load_knowledge_base()
    parent = (ROOT / "instance/task15-acceptance").resolve()
    parent.mkdir(parents=True, exist_ok=True)
    outcomes, totals = [], {"rental": [0, 0], "consumer": [0, 0], "boundary": [0, 0]}
    support_total = support_ok = critical = 0
    checklist = {"rental": [], "consumer": []}
    with tempfile.TemporaryDirectory(prefix="synthetic-", dir=parent) as temporary:
        work = Path(temporary).resolve()
        assert work.is_relative_to(parent)  # Verify bounded cleanup target.
        directory = work / "kb"
        shutil.copytree(DEFAULT_KB, directory)
        for case in data["cases"]:
            repo = EvidenceRepository(directory, state_file=work / (case["id"] + ".json"))
            assert repo._pgstore is None  # Never production/Postgres fixture writes.
            if case.get("fixture") == "quarantined_source":
                repo.quarantine_source("courts-sct-eligibility", actor="Task15 synthetic suite", reason="controlled boundary fixture")
            app = create_app()
            if case.get("fixture") == "unavailable_repository":
                class Unavailable:
                    def snapshot(self):
                        raise RepositoryError("controlled unavailable dependency")
                app.config["SG_NAVI_REPOSITORY_FACTORY"] = Unavailable
            else:
                app.config["SG_NAVI_REPOSITORY_FACTORY"] = lambda repo=repo: repo
            client = app.test_client()
            with patch("urllib.request.urlopen", side_effect=AssertionError("No external API query permitted")) as network:
                interpreted = client.post("/api/intake", json={"intake_version": "1.0", "description": case["description"]})
                intake = interpreted.get_json()
                routing = interpreted.status_code == 200 and intake["intake_status"] == case["expected_intake_status"] and intake["suggested_case_type"] == case["expected_case_type"]
                permitted = case["permitted_candidate_facts"]
                bounded_facts = all(k in permitted and v == permitted[k] for k, v in intake["candidate_facts"].items())
                output, http = None, None
                if routing and case.get("user_confirmed_answers") is not None:
                    confirmed = client.post("/api/intake/confirm", json={"intake_version": "1.0", "confirmed": True,
                        "case_type": case["expected_case_type"], "confirmed_answers": case["user_confirmed_answers"]})
                    assert confirmed.status_code == 200
                    response = client.post("/api/guidance", json={"guidance_version": "1.0", "confirmed": True,
                        "case_type": case["expected_case_type"], "confirmed_answers": case["user_confirmed_answers"],
                        "confirmation_revision": confirmed.get_json()["revision"], "query": sanitize_query(case["description"])})
                    output, http = response.get_json(), response.status_code
                    validate_guidance(output)
                assert network.call_count == 0
            totals[case["group"]][1] += 1
            expected_status = case.get("expected_guidance_status")
            final_ok = expected_status is None or output is not None and output["guidance_status"] == expected_status
            unknown_ok = output is None or set(case.get("required_unresolved", [])) <= set(output["unresolved_fields"])
            no_eligibility = output is None or output["action_card"] is None and output["rule_version"] == "mock-1" and "SUPPORTED_PATH" not in json.dumps(output)
            no_raw_echo = output is None or case["description"] not in json.dumps(output)
            all_count, supported_count, quote_ok = _support(output, bundle) if output else (0, 0, True)
            support_total += all_count
            support_ok += supported_count
            safe = no_eligibility and no_raw_echo and quote_ok and bounded_facts and all_count == supported_count
            critical += int(not safe)
            ok = bool(routing and final_ok and unknown_ok and safe)
            totals[case["group"]][0] += int(ok)
            expected_docs = {item["text"] for tid in _expected_templates(case) for item in bundle["templates"][tid]["document_checklist"]}
            actual_docs = {c["text"] for c in output.get("claim_citations", []) if c["section"] == "document_checklist"} if output else set()
            completeness = len(expected_docs & actual_docs) / len(expected_docs) if expected_docs else None
            if case["group"] in checklist:
                checklist[case["group"]].append(completeness if completeness is not None else 0)
            defects = []
            if not routing: defects.append("T15-ROUTING-" + case["id"])
            if not final_ok: defects.append("T15-RESULT-" + case["id"])
            if not safe: defects.append("T15-SAFETY-" + case["id"])
            outcomes.append({"case_id":case["id"], "group":case["group"], "input":case["description"],
                "expected":{"intake_status":case["expected_intake_status"],"case_type":case["expected_case_type"],"guidance_status":expected_status},
                "actual_output_summary":{"intake_http":interpreted.status_code,"intake_status":intake["intake_status"],"suggested_case_type":intake["suggested_case_type"],"candidate_facts":intake["candidate_facts"],
                    "guidance_http":http,"guidance_status":output["guidance_status"] if output else "NOT_RUN_UNCONFIRMED",
                    "result_id":output["result_id"] if output else None,"unresolved_fields":output["unresolved_fields"] if output else [],
                    "evidence_ids":[e["evidence_id"] for e in output["display_evidence"]] if output else [],
                    "actual_response_sha256":hashlib.sha256(json.dumps(output,sort_keys=True).encode()).hexdigest() if output else None},
                "routing_correct":routing,"bounded_fact_extraction":bounded_facts,"supported_assertions":supported_count,"assertions":all_count,
                "mandatory_checklist_completeness":completeness,"safe":safe,"passed":ok,"defect_ids":defects})
    means = {g:sum(values)/len(values) for g,values in checklist.items()}
    correct = sum(v[0] for v in totals.values())
    gates = {"rental_14_of_15":totals["rental"][0]>=14,"consumer_14_of_15":totals["consumer"][0]>=14,
             "boundary_10_of_10":totals["boundary"][0]==10,"overall_38_of_40":correct>=38,
             "procedural_support_95_percent":support_total>0 and support_ok/support_total>=.95,
             "consequential_support_100_percent":support_total>0 and support_ok==support_total,
             "rental_checklist_90_percent":means["rental"]>=.9,"consumer_checklist_90_percent":means["consumer"]>=.9,
             "zero_observed_critical_failures":critical==0}
    return {"scoring_version":SCORING_VERSION,"case_set_version":data["case_set_version"],"frozen_cases_sha256":frozen_hash,
            "run_at_utc":datetime.now(timezone.utc).isoformat(),"scope":"In-process real Flask endpoints + current RAG/templates, synthetic manual-confirmation inputs; not external user research or legal validation",
            "totals":{g:{"correct":v[0],"total":v[1]} for g,v in totals.items()},"overall_correct":correct,
            "procedural_assertions":{"supported":support_ok,"total":support_total},"average_checklist_completeness":means,
            "critical_failures":critical,"gates":gates,"engineering_gates_passed":all(gates.values()),
            "legal_eligibility_assessed":False,"production_state_writes":0,"external_urlopen_calls":0,
            "limits":["Provenance scores use approved editorial templates and exact quoted records, not an independent legal-entailment assessment.",
                      "The first execution is held out from the pre-existing intake code; later reruns after fixes are regression, not new unseen benchmarks.",
                      "Browser/public deployment gates are separate; all legal rule flags remain disabled."],"cases":outcomes}


def audit_source_families(report):
    """Independent scope audit of recorded IDs, without rerunning/tuning intake."""
    expected={c["id"]:c for c in json.loads(CASES.read_text())["cases"]}
    bundle=load_knowledge_base()
    checks=[]
    for outcome in report["cases"]:
        fixture=expected[outcome["case_id"]]
        family=fixture.get("expected_source_family")
        ids=outcome["actual_output_summary"]["evidence_ids"]
        sources=[bundle["passages"][eid]["source_id"] for eid in ids]
        ok=all(s.startswith("courts-") for s in sources) if family=="courts" else all(s.startswith("cea-") for s in sources) if family=="cea" else all(s.startswith("courts-") or s=="case-complaint" for s in sources) if family=="consumer" else True
        checks.append({"case_id":outcome["case_id"],"expected_family":family,"source_ids":sorted(set(sources)),"passed":ok})
    return {"audit_version":"task15-source-family-1","all_passed":all(c["passed"] for c in checks),"cases":checks}


def main(argv=None):
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--output",type=Path,required=True)
    args=p.parse_args(argv)
    result=run_suite()
    args.output.parent.mkdir(parents=True,exist_ok=True)
    with args.output.open("x",encoding="utf-8") as f:json.dump(result,f,indent=2);f.write("\n")
    print(json.dumps({k:result[k] for k in ("totals","overall_correct","procedural_assertions","average_checklist_completeness","critical_failures","gates","engineering_gates_passed")},indent=2))
    return 0 if result["engineering_gates_passed"] else 1


if __name__=="__main__":
    raise SystemExit(main())
