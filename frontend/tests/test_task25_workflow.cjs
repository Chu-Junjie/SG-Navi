"use strict";
const {test}=require("node:test"),assert=require("node:assert/strict");
const {readFileSync}=require("node:fs"),{resolve}=require("node:path");
const flow=require("../js/task25-workflow.js"),locale=require("../js/task23-locale.js");
const packageData=JSON.parse(readFileSync(resolve(__dirname,"../../rag/action_evidence/package.json"),"utf8"));
const c=f=>({case_type:"consumer_complaint",issue_subtype:"goods_dispute",facts:{merchant_location:"singapore",purchase_purpose:"personal",...f}});
const r=(s,f)=>({case_type:"rental_deposit",issue_subtype:s,facts:f});
const links=(...ids)=>new Map(ids.map(id=>[id,{id}]));
test("workflow reference URLs match signed Task17 records or are explicitly pending review",()=>{
 assert.equal(packageData.profiles.length,13);
 const actual=new Map(packageData.records.map(x=>[x.id,x.evidence.url]));
 for(const x of Object.values(flow.SOURCES)){
  const u=new URL(x.url);assert.equal(u.protocol,"https:");
  assert.ok(["www.case.org.sg","www.cea.gov.sg","www.judiciary.gov.sg"].includes(u.hostname));
  if(x.status==="task17")assert.equal(actual.get(x.id),x.url);
  else{assert.equal(x.status,"pending_review");assert.equal(x.id,null);}
 }
});
test("consumer support does not equate enquiry or visitor status to filing eligibility",()=>{
 assert.deepEqual(flow.buildRoutes(c({}),{},links()).map(x=>x.id),["case","sct"]);
 assert.match(flow.buildRoutes(c({}),{},links("case-phone"))[0].reason,/enquiry/);
 assert.match(flow.buildRoutes(c({consumer_context:"visitor"}),{},links("case-form"))[0].reason,/Visitor/);
 assert.match(flow.buildRoutes(c({consumer_context:"local_consumer"}),{},links("case-form"))[0].reason,/form is verified/);
 assert.deepEqual(flow.buildRoutes(c({purchase_purpose:"business"}),{},links()).map(x=>x.id),["sct"]);
 assert.deepEqual(flow.buildRoutes(c({merchant_location:"outside_singapore"}),{},links()).map(x=>x.id),[]);
});
test("residential SCT gate never includes known commercial or industrial landlord cases",()=>{
 for(const kind of ["commercial","industrial"])assert.deepEqual(flow.buildRoutes(r("deposit_return",{dispute_with:"landlord",premises_type:kind}),{},links()),[]);
 for(const kind of ["private_residential","hdb"]){
  const route=flow.buildRoutes(r("deposit_return",{dispute_with:"landlord",premises_type:kind}),{},links());
  assert.deepEqual(route.map(x=>x.id),["sct"]);assert.match(route[0].reason,/no more than two years/);
 }
});
test("CEA misconduct and contract disputes are separate; missing signature cannot imply approval",()=>{
 assert.deepEqual(flow.buildRoutes(r("agent_conduct",{dispute_with:"agent"}),{},links()).map(x=>x.id),["ceaConduct"]);
 const unknown=flow.buildRoutes(r("agency_agreement",{dispute_with:"agent",agency_agreement_signed:"unknown"}),{},links());
 assert.match(unknown[0].reason,/not been confirmed/);
 const signed=flow.buildRoutes(r("agency_agreement",{dispute_with:"agent",agency_agreement_signed:true}),{},links());
 assert.match(signed[0].reason,/signed agency agreement was reported/i);
 assert.deepEqual(flow.buildRoutes(r("deposit_return",{dispute_with:"agent"}),{},links()),[]);
});
test("every official stage has a reference and every new static phrase has a Chinese UI translation",()=>{
 for(const t of Object.values(flow.TEMPLATES)){
  assert.ok(t.stages.length>=4);
  for(const s of t.stages)assert.ok(flow.SOURCES[s.source]);
 }
 for(const phrase of flow.COPY)assert.ok(locale.chineseCopy(phrase),"Missing zh-Hans static copy: "+phrase);
 assert.deepEqual(flow.buildRoutes(null,{},links()),[]);
 assert.deepEqual(flow.buildRoutes(c({}),{},null),[]);
});
