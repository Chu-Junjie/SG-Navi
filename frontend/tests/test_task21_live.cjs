"use strict";
const {test}=require("node:test");
const assert=require("node:assert/strict");
const {webcrypto,createHash}=require("node:crypto");
const ui=require("../js/task21-live.js");
const sha=s=>createHash("sha256").update(s).digest("hex");
const context={
  case_type:"consumer_complaint",issue_subtype:"restaurant_overcharge",goal:"complain",
  facts:{resolution_attempted:true,merchant_location:"singapore",purchase_purpose:"personal"},
  summary:"You reported an extra restaurant charge."
};
function record(){
 const quote="A relevant quoted passage from a recorded official source.";
 return {id:"e-1",source_id:"case-record",kind:"statute",publisher:"Official legislation",
 title:"Consumer Protection (Fair Trading) Act",url:"https://sso.agc.gov.sg/Act/CPFTA2003",
 locator:"section 4",quote,quote_sha256:sha(quote),source_sha256:"b".repeat(64),
 captured_at:"2026-11-01T00:00:00Z",reviewed_at:"2026-11-07T00:00:00Z",reviewed_by:"reviewer",
 review_method:"live_excerpt_check",review_status:"verified",provision:"section 4",edition:"2026"};
}
const claim=(id,text)=>({id,text,evidence_ids:["e-1"]});
async function ready(){
 const primary={...claim("action-1","Review the official assistance process."),label:"Open official form",kind:"complaint_intake",contact_id:"case-form"};
 return {action_plan_version:"1.0",request_id:"req-12345678",state:"READY",
  reason:"verified_action",message:"An official next step is available.",
  context,revision:await ui.revisionOf(context,webcrypto),question:null,
  plan:{headline:"What you can do next",assessment:claim("assessment-1","A local contact may provide assistance."),
    primary_action:primary,checklist:[claim("check-1","Keep your receipt and messages.")],
    contacts:[{id:"case-form",institution:"CASE",purpose:"complaint_intake",
      kind:"web",value:"https://www.case.org.sg/submit-a-complaint/",evidence_ids:["e-1"]}],
    details:[],draft:null,legal_basis:[{claim_id:"action-1",evidence_id:"e-1"}],
    source_version:"action-kb-2026-11-07.1",evidence:[record()]}}
}
function req(){return {action_plan_version:"1.0",request_id:"req-12345678",operation:"plan",confirmed:true,context};}
test("three-step consumer process uses verified action and scoped contacts",()=>{
 const p={primary_action:{id:"next",kind:"prepare",text:"Keep the purchase receipt.",evidence_ids:["ev-1"]},
  checklist:[claim("records","Keep the receipt and seller messages.")],draft:{title:"Draft"}};
 const ctx={case_type:"consumer_complaint",issue_subtype:"goods_dispute",goal:"complain",
  facts:{purchase_purpose:"personal",resolution_attempted:false}};
 const noContacts=ui.buildProcessSteps(ctx,p,new Map());
 assert.deepEqual(noContacts.map(step=>step.id),["prepare","communicate","official"]);
 assert.equal(noContacts.length,3);
 assert.equal(noContacts[0].text,p.primary_action.text);
 assert.deepEqual(noContacts[0].evidence_ids,["ev-1"]);
 assert.match(noContacts[1].text,/Describe the problem to the business/);
 assert.deepEqual(noContacts[1].evidence_ids,[]);
 assert.equal(noContacts[2].hasContacts,false);
 assert.deepEqual(noContacts[2].evidence_ids,[]);
 assert.match(noContacts[2].text,/No verified official contact/);
 const approved={id:"case-phone",evidence_ids:["ev-phone"],purpose:"consumer_assistance"};
 const available=ui.buildProcessSteps({...ctx,facts:{...ctx.facts,resolution_attempted:true}},
   p,new Map([["case-phone",approved]]));
 assert.match(available[1].text,/Review your earlier request/);
 assert.equal(available[2].hasContacts,true);
 assert.deepEqual(available[2].evidence_ids,["ev-phone"]);
});
test("three-step rental guide distinguishes agent and never invents external contacts",()=>{
 const p={primary_action:{id:"next",kind:"prepare",text:"Check the signed tenancy terms.",
  evidence_ids:["ev-lease"]},checklist:[claim("records","Keep payment records."),claim("terms","Check the agreement.")],
  draft:null};
 const ctx={case_type:"rental_deposit",issue_subtype:"deposit_deduction",goal:"seek_refund",
  facts:{dispute_with:"agent"}};
 const steps=ui.buildProcessSteps(ctx,p,new Map());
 assert.match(steps[0].title,/rental records/);
 assert.match(steps[1].text,/estate agent/);
 assert.equal(steps[0].extra.length,2);
 assert.equal(steps[2].hasContacts,false);
 assert.deepEqual(steps[2].evidence_ids,[]);
 const landlord=ui.buildProcessSteps({...ctx,facts:{dispute_with:"landlord"}},p,new Map());
 assert.match(landlord[1].text,/relevant party/);
});

test("approved HTTPS contacts, local phone and email only",()=>{
 assert.ok(ui.safeURL("https://www.case.org.sg/submit-a-complaint/"));
 for(const x of ["javascript:alert(1)","http://www.case.org.sg","https://case.org.sg.evil.com/",
   "https://www.case.org.sg/?email=private","https://person@www.case.org.sg/"])
   assert.equal(ui.safeURL(x),null);
 assert.equal(ui.safeContact({id:"c",institution:"CASE",kind:"phone",value:"+6562775100",evidence_ids:["e-1"]}).href,"tel:+6562775100");
 assert.equal(ui.safeContact({id:"c",institution:"CASE",kind:"email",value:"help@example.com",evidence_ids:["e-1"]}).href,"mailto:help@example.com");
 assert.equal(ui.safeContact({id:"c",institution:"CASE",kind:"phone",value:"123-unsafe",evidence_ids:["e-1"]}),null);
});
test("real result contract requires same request, revision, quoted digest and support",async()=>{
 const data=await ready(); const verified=await ui.verifyResponse(data,req(),webcrypto);
 assert.equal(verified.verifiedContacts.size,1);
 assert.equal(verified.verifiedSources.size,1);
 data.plan.evidence[0].quote="Altered quote";
 await assert.rejects(ui.verifyResponse(data,req(),webcrypto),/verification/);
});
test("stale context, altered contacts and unrelated legal citations fail closed",async()=>{
 let r=await ready();r.revision="0".repeat(24);await assert.rejects(ui.verifyResponse(r,req(),webcrypto),/Stale/);
 r=await ready();r.plan.contacts[0].value="https://evil.example/contact";
 await assert.rejects(ui.verifyResponse(r,req(),webcrypto),/Invalid contact/);
 r=await ready();r.plan.legal_basis[0].claim_id="not-a-real-claim";
 await assert.rejects(ui.verifyResponse(r,req(),webcrypto),/Unrelated/);
 r=await ready();r.plan.primary_action.contact_id="missing";
 await assert.rejects(ui.verifyResponse(r,req(),webcrypto),/Unverified action/);
});
test("preparation-only actions never invent contacts",async()=>{
 const r=await ready();r.plan.primary_action.kind="prepare";r.plan.primary_action.contact_id=null;
 assert.equal((await ui.verifyResponse(r,req(),webcrypto)).state,"READY");
 r.plan.primary_action.contact_id="case-form";
 await assert.rejects(ui.verifyResponse(r,req(),webcrypto),/Unexpected external action/);
});
test("ASK allows one relevant question but no fabricated legal plan",async()=>{
 const id="req-12345678",revision=await ui.revisionOf(context,webcrypto);
 const asked={action_plan_version:"1.0",request_id:id,state:"ASK",reason:"missing_decisive_fact",
  message:"One detail changes the appropriate next step.",context,revision,plan:null,
  question:{id:"decide_consumer_context",field:"consumer_context",prompt:"Are you a local consumer or visitor?",
    reason:"Assistance audience matters.",options:[{value:"local_consumer",label:"Local consumer"},
      {value:"visitor",label:"Visitor"},{value:"unknown",label:"Not sure"}]}};
 assert.equal((await ui.verifyResponse(asked,req(),webcrypto)).state,"ASK");
 asked.question.field="resolution_attempted";
 await assert.rejects(ui.verifyResponse(asked,req(),webcrypto),/Invalid follow-up/);
});
test("canonical facts do not depend on insertion order",async()=>{
 const copy={...context,facts:{purchase_purpose:"personal",merchant_location:"singapore",resolution_attempted:true}};
 assert.equal(await ui.revisionOf(copy,webcrypto),await ui.revisionOf(context,webcrypto));
});

function approved(canonical,display){
 return {overlay_version:"task24-reviewed-1.0",locale:"zh-Hans",
  translation_status:"approved_explanation",is_official_translation:false,
  reviewed_by:"Chu-Junjie",reviewed_at:"2026-11-10T00:00:00Z",entries_sha256:"c".repeat(64),
  disclaimer:"测试用中文说明",canonical,display};
}
function displayFor(data,fields={}){
 return {message:"测试提示",context_summary:data.context?"测试摘要":null,question:null,plan:null,...fields};
}

test("reviewed overlay accepts all five states and rejects changed identities",async()=>{
 const common={action_plan_version:"1.0",request_id:"req-12345678",reason:"test",message:"English message",
  context:null,revision:null,question:null,plan:null};
 for(const state of ["CONFIRM","LIMITED","UNAVAILABLE"]){
  const data={...common,state,context:state==="CONFIRM"?context:null};
  const overlay=approved(data,displayFor(data));
  assert.equal(ui.reviewedDisplay(overlay),overlay.display);
  assert.equal(ui.reviewedDisplay({...overlay,translation_status:"pending_review"}),null);
  assert.equal(ui.reviewedDisplay({...overlay,display:{...overlay.display,message:" "}}),null);
 }
 const q={id:"test-question",field:"resolution_attempted",prompt:"Did you contact the seller?",reason:"A fact is needed.",
  options:[{value:false,label:"No"},{value:"unknown",label:"Not sure"}]};
 const ask={...common,state:"ASK",context,question:q};
 const displayQ={id:q.id,field:q.field,prompt:"测试问题",reason:"测试原因",
  options:[{value:false,label:"否"},{value:"unknown",label:"不确定"}]};
 assert.ok(ui.reviewedDisplay(approved(ask,displayFor(ask,{question:displayQ}))));
 for(const field of ["id","field","options"]){
  const changed={...displayQ,[field]:field==="options"?[{value:"false",label:"否"},displayQ.options[1]]:"changed"};
  assert.equal(ui.reviewedDisplay(approved(ask,displayFor(ask,{question:changed}))),null);
 }
 const data=await ready();
 data.plan.details=[{kind:"documents",title:"Documents",items:[claim("doc-1","Keep the bill.")]}];
 data.plan.draft={title:"Draft",subject:"Request",body:"I request {amount}.",slots:[{id:"amount",label:"Amount"}]};
 const p=data.plan;
 const plan={headline:"测试标题",assessment:{...p.assessment,text:"测试评估"},
  primary_action:{...p.primary_action,text:"测试行动",label:"测试链接"},
  checklist:p.checklist.map(x=>({...x,text:"测试清单"})),
  details:[{kind:"documents",title:"测试材料",items:[{...p.details[0].items[0],text:"测试项目"}]}],
  contacts:p.contacts.map(x=>({...x,purpose:"测试用途",note:null})),
  draft:{title:"测试草稿",subject:"测试主题",body:"测试 {amount}。",slots:[{id:"amount",label:"金额"}]}};
 const envelope=approved(data,displayFor(data,{plan}));
 assert.equal(ui.reviewedDisplay(envelope),envelope.display);
 for(const mutate of [
  x=>{x.primary_action.contact_id="other";},
  x=>{x.checklist[0].evidence_ids=["other"];},
  x=>{x.details[0].items[0].id="other";},
  x=>{x.contacts[0].value="https://example.com/";},
  x=>{x.draft.body="无占位符";},
  x=>{x.draft.slots[0].id="other";}
 ]){
  const changed=structuredClone(envelope);
  mutate(changed.display.plan);
  assert.equal(ui.reviewedDisplay(changed),null);
 }
 assert.equal(data.plan.evidence[0].quote,record().quote);
});

test("approved reviewed endpoint resolves on Pages and local Flask",()=>{
 const api=require("../js/api-config.js");
 const pages={hostname:"chu-junjie.github.io",pathname:"/SG-Navi/"};
 const path="/api/action-plan/zh-hans-reviewed";
 assert.equal(api.resolveReviewedActionPlan(pages),"https://sg-navi-api-junjie.onrender.com"+path);
 assert.equal(api.resolve(path,pages),api.resolveReviewedActionPlan(pages));
 assert.equal(api.resolveReviewedActionPlan({hostname:"127.0.0.1",pathname:"/"}),path);
});

test("disabled, 404, 503 and network errors use the unchanged English request",async()=>{
 class Element extends EventTarget {
  dataset={}; setAttribute(){} removeAttribute(){} append(){} appendChild(){} replaceChildren(){} focus(){}
 }
 for(const status of [null,404,503,"network"]){
  const nodes=new Map(["problem-intake","problem-form","problem-text","problem-submit","problem-validation"]
    .map(id=>[id,new Element()]));
  nodes.get("problem-text").value="Synthetic English description.";
  const doc=Object.assign(new EventTarget(),{body:new Element(),getElementById:id=>nodes.get(id),
    createElement:()=>new Element(),querySelectorAll:()=>[]});
  const requests=[];
  const client=ui.init(doc,{
   SGNaviApiConfig:{resolve:()=>"/api/action-plan",resolveReviewedActionPlan:()=>status?"/api/action-plan/zh-hans-reviewed":null},
   crypto:{randomUUID:()=>"12345678"},
   async fetch(path,options){
    requests.push([path,options.body]);
    if(path.endsWith("zh-hans-reviewed")){
     if(status==="network")throw Error("Network");
     return {ok:false,status};
    }
    return new Response(JSON.stringify({action_plan_version:"1.0",request_id:"req-12345678",
     state:"LIMITED",reason:"test",message:"Canonical English",context:null,revision:null,question:null,plan:null}),
     {headers:{"Content-Type":"application/json"}});
   }
  });
  await client.interpret();
  assert.deepEqual(requests.map(x=>x[0]),status?["/api/action-plan/zh-hans-reviewed","/api/action-plan"]:["/api/action-plan"]);
  assert.equal(new Set(requests.map(x=>x[1])).size,1);
  assert.equal(JSON.parse(requests[0][1]).description,nodes.get("problem-text").value);
 }
});
