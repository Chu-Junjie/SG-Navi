"""Actual public Task 15 synthetic HTTP checks; no state mutations or secrets."""
import argparse
import hashlib
import json
import time
from datetime import datetime, timezone
from pathlib import Path
from urllib.request import Request, urlopen

from backend.smoke_public import _request, ORIGIN
from shared.validate_guidance import validate_guidance

BASE="https://sg-navi-api-junjie.onrender.com"
PAGES="https://chu-junjie.github.io/SG-Navi/"
ROOT=Path(__file__).resolve().parents[1]


def wait_for_public(seconds):
    deadline=time.monotonic()+seconds
    expected=(ROOT/"frontend/js/task15-flow.js").read_text().replace("\r\n","\n").encode()
    while True:
        try:
            with urlopen(Request(PAGES+"frontend/js/task15-flow.js",headers={"Cache-Control":"no-cache"}),timeout=25) as response:
                actual=response.read().replace(b"\r\n",b"\n")
                assert response.status==200 and actual==expected
            code,_,raw=_request(BASE,"/api/guidance",method="POST",payload={},headers={"Origin":ORIGIN})
            assert code==400 and json.loads(raw)["guidance_version"]=="1.0"
            return
        except Exception:
            if time.monotonic()>=deadline:raise RuntimeError("Published frontend bytes / guidance API not ready before deadline") from None
            time.sleep(5)


def run():
    checks=[]
    samples=[]
    passages={p["evidence_id"]:p for p in (json.loads(line) for line in (ROOT/"rag/knowledge_base/passages.jsonl").read_text().splitlines())}
    def check(name,fn):
        try:checks.append({"name":name,"passed":True,"actual":fn()})
        except Exception as exc:checks.append({"name":name,"passed":False,"error":type(exc).__name__+": "+str(exc)[:200]})
    def post(path,body,status=200):
        code,headers,raw=_request(BASE,path,method="POST",payload=body,headers={"Origin":ORIGIN})
        assert code==status,(path,code,status)
        assert headers.get("access-control-allow-origin")==ORIGIN
        assert not headers.get("access-control-allow-credentials")
        return json.loads(raw)
    def health():
        code,headers,_=_request(BASE,"/api/health",headers={"Origin":ORIGIN})
        assert code==200 and headers.get("x-sg-navi-deployment-mode")=="postgres-backed-free-demo"
        return {"http":code,"deployment_mode":headers["x-sg-navi-deployment-mode"]}
    check("Actual Neon-backed service health",health)
    fixtures=[("rental_deposit","My landlord refuses to return my SGD 2000 deposit.",{"dispute_with":"landlord","premises_type":"residential","claim_amount_sgd":2000}),
              ("consumer_complaint","I bought a faulty product but the seller refuses to refund me.",{"purchase_type":"goods","purchase_purpose":"personal","supplier_registered_in_sg":True,"claim_amount_sgd":140})]
    for case,prompt,facts in fixtures:
        def journey(case=case,prompt=prompt,facts=facts):
            intake=post("/api/intake",{"intake_version":"1.0","description":prompt})
            assert intake["suggested_case_type"]==case
            confirmed=post("/api/intake/confirm",{"intake_version":"1.0","confirmed":True,"case_type":case,"confirmed_answers":facts})
            request={"guidance_version":"1.0","confirmed":True,"case_type":case,"confirmed_answers":facts,"confirmation_revision":confirmed["revision"],"query":prompt}
            result=post("/api/guidance",request);validate_guidance(result)
            assert result["guidance_status"]=="GUIDANCE_ONLY" and result["rule_version"]=="mock-1" and result["action_card"] is None
            for row in result["display_evidence"]:
                expected=passages[row["evidence_id"]]
                assert row["verbatim_excerpt"]==expected["text"] and row["url"]==expected["url"]
                assert hashlib.sha256(row["verbatim_excerpt"].encode()).hexdigest()==expected["excerpt_sha256"]
            samples.append({"sample_kind":"selected_fields_from_actual_response","request":request,"response":{k:result[k] for k in ("guidance_version","rule_version","source_version","context_version","confirmation_revision","result_id","guidance_status","matched_evidence_ids","action_card")},"evidence_ids":[r["evidence_id"] for r in result["display_evidence"]],"response_canonical_json_sha256":hashlib.sha256(json.dumps(result,sort_keys=True,separators=(",",":")).encode()).hexdigest()})
            stale={**request,"confirmation_revision":"0"*20}
            assert post("/api/guidance",stale,400)["guidance_status"]=="ERROR"
            return {"intake":intake["intake_status"],"guidance":result["guidance_status"],"evidence_count":len(result["display_evidence"]),"stale_revision_http":400}
        check(case+" real intake -> confirm -> guidance and stale rejection",journey)
    def unconfirmed():
        result=post("/api/guidance",{"guidance_version":"1.0","confirmed":False},400)
        assert result["display_evidence"]==[] and result["action_card"] is None
        return {"http":400,"empty_evidence":True}
    check("Unconfirmed input rejected",unconfirmed)
    def forbidden():
        code,headers,_=_request(BASE,"/api/guidance",method="OPTIONS",headers={"Origin":"https://unapproved.example","Access-Control-Request-Method":"POST"})
        assert code==403 and not headers.get("access-control-allow-origin")
        return {"http":code}
    check("Unapproved CORS origin rejected",forbidden)
    return {"scope":"actual_public_task15_synthetic_wire","executed_at_utc":datetime.now(timezone.utc).isoformat(),"base_url":BASE,"passed":all(c["passed"] for c in checks),"checks":checks,"samples":samples,"production_state_writes":0,"limits":["No forced production quarantine or database writes","Procedural research, not legal eligibility or filing authorization"]}


def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument("--output",required=True);parser.add_argument("--wait-seconds",type=int,default=0);args=parser.parse_args()
    if args.wait_seconds:wait_for_public(args.wait_seconds)
    report=run();target=Path(args.output);target.parent.mkdir(parents=True,exist_ok=True);target.write_text(json.dumps(report,indent=2)+"\n",encoding="utf-8")
    print(json.dumps({"passed":report["passed"],"checks":report["checks"],"output":str(target)}))
    return 0 if report["passed"] else 1


if __name__=="__main__":raise SystemExit(main())
