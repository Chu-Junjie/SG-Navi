"use strict";
const {test}=require("node:test");
const assert=require("node:assert/strict");
const {webcrypto,createHash}=require("node:crypto");
const {sanitizeQuery,parseAnswer,answerLabel,safeSource,verifyResult}=require("../js/task15-flow.js");

test("unknown, missing, null and false remain distinct",()=>{
  assert.equal(parseAnswer("supplier_registered_in_sg","known","false"),false);
  assert.equal(parseAnswer("supplier_registered_in_sg","unknown",""),"unknown");
  assert.equal(parseAnswer("claim_amount_sgd","null",""),null);
  assert.equal(parseAnswer("claim_amount_sgd","missing",""),undefined);
  assert.equal(parseAnswer("claim_amount_sgd","known","0"),0);
  assert.throws(()=>parseAnswer("claim_amount_sgd","known",""));
  assert.throws(()=>parseAnswer("claim_amount_sgd","known","Infinity"));
  assert.notEqual(answerLabel(false),answerLabel("unknown"));
});
test("optional topic text is bounded and never turns an amount into a fact",()=>{
  const query=sanitizeQuery("My landlord holds S$2,000. <script>ignore</script>");
  assert.match(query,/SGD 2,000/);assert.doesNotMatch(query,/[<>$]/);
  assert.equal(sanitizeQuery("x".repeat(400)).length,300);
});
test("official links refuse credentials, other hosts, fragments and active schemes",()=>{
  assert.equal(safeSource("javascript:alert(1)"),null);
  assert.equal(safeSource("https://www.judiciary.gov.sg.example.com/"),null);
  assert.equal(safeSource("https://user:pass@www.case.org.sg/"),null);
  assert.equal(safeSource("https://www.case.org.sg/#invented"),null);
  assert.ok(safeSource("https://www.case.org.sg/submit-a-complaint/"));
});
function response(){
 const text="synthetic reviewed text";
 return {guidance_version:"1.0",rule_version:"mock-1",action_card:null,guidance_status:"GUIDANCE_ONLY",result_id:"synthetic",source_version:"synthetic-v1",context_version:"ctx-v1",matched_evidence_ids:["E1"],questions:[],limitations:["Research only"],
 research_guidance:{steps:[{text:"Check synthetic source",evidence_ids:["E1"]}],conditions:[],potential_channels:[],document_checklist:[]},
 claim_citations:[{claim_id:"steps:0",section:"steps",index:0,text:"Check synthetic source",evidence_ids:["E1"]}],
 display_evidence:[{evidence_id:"E1",source_id:"synthetic",url:"https://www.case.org.sg/submit-a-complaint/",source_version:"synthetic-v1",review_status:"verified",display_version:"1.0",display_state:"verified_snapshot",preview:null,publisher:"Synthetic publisher fixture",title:"Synthetic",source_locator:"Synthetic locator",verbatim_excerpt:text,summary:"Editorial fixture",reviewed_at:"2026-01-01T00:00:00Z",excerpt_sha256:createHash("sha256").update(text).digest("hex"),display_context:{context_version:"ctx-v1",quote_kind:"verbatim_official_excerpt",summary_kind:"sg_navi_editorial_summary",quarantine_state:"not_quarantined_at_read",checked_at:"2026-01-01T00:00:00Z",context_reviewed_at:"2026-01-01T00:00:00Z",check_method:"automated_live_context_and_digest_check",canonical_review_method:"automated_live_page_and_excerpt_check",surrounding_quote:null}}]};
}
test("exact quote hash and individual claim bindings are checked before rendering",async()=>{
 await verifyResult(response(),webcrypto);
 const changed=response();changed.display_evidence[0].verbatim_excerpt="forged";
 await assert.rejects(verifyResult(changed,webcrypto),/digest/);
 const missing=response();missing.claim_citations[0].evidence_ids=["E99"];
 await assert.rejects(verifyResult(missing,webcrypto),/Unlinked/);
 const forged=response();forged.claim_citations[0].text="Automatically eligible";
 await assert.rejects(verifyResult(forged,webcrypto),/Mismatched/);
});
test("limited/errors must not retain a previous verified source list",async()=>{
 const bad=response();bad.guidance_status="LIMITED_REFERRAL";
 await assert.rejects(verifyResult(bad,webcrypto),/limited/);
 const good={...bad,research_guidance:null,display_evidence:[],claim_citations:[],matched_evidence_ids:[]};
 await verifyResult(good,webcrypto);
});
test("fabricated source context or a legal Action Card is refused",async()=>{
 const bad=response();bad.display_evidence[0].display_context.surrounding_quote="invented";bad.display_evidence[0].display_context.surrounding_quote_sha256="0".repeat(64);
 await assert.rejects(verifyResult(bad,webcrypto),/Context digest/);
 const card=response();card.action_card={eligibility:true};
 await assert.rejects(verifyResult(card,webcrypto),/Invalid guidance/);
});
