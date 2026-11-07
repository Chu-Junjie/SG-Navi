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
