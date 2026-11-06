"use strict";
const {test} = require("node:test");
const assert = require("node:assert/strict");
const {inspectResult,answerLabel,sourceTitle} = require("../js/task10-results.js");

const evidence={source_id:"source-1",evidence_id:"evidence-1",source_version:"kb-2026-11-01.1",
  review_status:"verified",href:"https://www.judiciary.gov.sg/civil"};
const base={api_version:"1.0",status:"REFER_TO_OFFICIAL",rule_version:"mock-1",
  source_version:"kb-2026-11-01.1",action_card:null,
  evidence:[{...evidence,url:evidence.href,rule_ids:["scope"]}],questions:[],warnings:["Context only."]};
const allow=()=>[evidence];
test("API v1 referral displays metadata, not official quotation or eligibility",()=>{
  const result=inspectResult(base,allow);
  assert.equal(result.kind,"referral");
  assert.equal(result.sources.length,1);
  assert.equal(result.sources[0].publisher,"Singapore Courts");
  assert.equal(Object.hasOwn(result.sources[0],"quote"),false);
  assert.equal(Object.hasOwn(result.sources[0],"screenshot"),false);
});
test("multiple independent reviewed references are allowed but never claim-matched",()=>{
  const second={...evidence,evidence_id:"evidence-2",source_id:"source-2",href:"https://www.case.org.sg/"};
  const data={...base,evidence:[base.evidence[0],{...base.evidence[0],evidence_id:"evidence-2"}]};
  const selected=inspectResult(data,()=>[evidence,second]);
  assert.equal(selected.sources.length,2);
  assert.equal(selected.sources[1].publisher,"Consumers Association of Singapore (CASE)");
});
test("null supported card and synthetic supported card do not become Action Cards",()=>{
  const unsupported=inspectResult({...base,status:"SUPPORTED_PATH",action_card:{steps:["Invented step"]}},allow);
  assert.equal(unsupported.kind,"unsupported_card");
  assert.equal(unsupported.sources.length,0);
});
test("invalid version, no evidence, missing selector and uncertain sources fail closed",()=>{
  assert.equal(inspectResult({...base,api_version:"2.0"},allow).kind,"unsupported");
  assert.equal(inspectResult({...base,evidence:[]},allow).kind,"missing");
  assert.equal(inspectResult(base,null).kind,"unverified");
  assert.equal(inspectResult(base,()=>[]).kind,"unverified");
  assert.equal(inspectResult(base,()=>[{...evidence,review_status:"quarantined"}]).kind,"unverified");
  assert.equal(inspectResult(base,()=>[{...evidence,source_version:"older"}]).kind,"unverified");
  assert.equal(inspectResult(base,()=>[{...evidence,href:"http://www.judiciary.gov.sg"}]).kind,"unverified");
});
test("clarification and service errors never display verified results",()=>{
  assert.equal(inspectResult({...base,status:"NEED_CLARIFICATION"},allow).kind,"clarification");
  assert.equal(inspectResult({...base,status:"ERROR"},allow).kind,"error");
  assert.equal(inspectResult({...base,action_card:{}},allow).kind,"unverified");
});
test("raw reported facts retain false/unknown/null distinctions",()=>{
  assert.equal(answerLabel(false),"No");
  assert.equal(answerLabel(null),"Not provided");
  assert.equal(answerLabel("unknown"),"Not sure");
  assert.equal(answerLabel(2000),"2000");
  assert.equal(sourceTitle("https://www.cea.gov.sg/"),"Council for Estate Agencies (CEA)");
});
