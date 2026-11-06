"use strict";
const {test} = require("node:test");
const assert = require("node:assert/strict");
const {inspectPreview,safeOfficialURL} = require("../js/task10-guidance.js");
const version="kb-2026-11-01.1";
function source(id="SCT-ELIG-RESIDENTIAL") {
  return {
    evidence_id:id,source_id:"courts-sct-eligibility",rule_ids:["rental-sct"],
    url:"https://www.judiciary.gov.sg/civil/cases-eligible-small-claim",
    review_status:"verified",source_version:version,
    publisher:"Singapore Courts",title:"Cases eligible for small claims",
    verbatim_excerpt:"residential premises not exceeding 2 years",
    source_locator:"tenancy scope paragraph",
    reviewed_at:"2026-11-01T02:00:00Z",
    summary:"SG Navi explanation; source wording is separate.",
    excerpt_sha256:"a".repeat(64),display_version:"1.0",
    display_state:"verified_snapshot",preview:null
  };
}
function sample() {
  return {
    results_version:"0.1",result_id:"a".repeat(24),source_version:version,
    guidance_status:"GUIDANCE_ONLY",limitations:["This is not a legal eligibility decision."],
    display_evidence:[source()],
    research_guidance:{
      case_summary:"User-confirmed rental deposit; facts not independently verified.",
      potential_channels:[{text:"Review the official Singapore Courts information",evidence_ids:["SCT-ELIG-RESIDENTIAL"]}],
      conditions:[{text:"Check tenancy scope",evidence_ids:["SCT-ELIG-RESIDENTIAL"]}],
      steps:[{text:"Read the current official rules",evidence_ids:["SCT-ELIG-RESIDENTIAL"]}],
      document_checklist:[{text:"Prepare tenancy documents",evidence_ids:["SCT-ELIG-RESIDENTIAL"]}],
      unresolved_questions:[{field:"tenancy_duration_months",text:"Check your tenancy period"}],
      citations:["SCT-ELIG-RESIDENTIAL"]
    }
  };
}
test("Task12 conditional guidance uses Task14 recorded official wording without eligibility",()=>{
  const model=inspectPreview(sample());
  assert.equal(model.kind,"guidance");
  assert.equal(model.claims.length,4);
  assert.equal(model.sources.get("SCT-ELIG-RESIDENTIAL").verbatim_excerpt,
    "residential premises not exceeding 2 years");
  assert.match(model.notice,/not a legal eligibility decision/);
  assert.equal(model.guide.document_checklist.length,1);
});
test("Optional source context keeps original quote and SG Navi summary distinct",()=>{
  const p=sample();
  p.display_evidence[0].display_context={
    quote_kind:"verbatim_official_excerpt",
    summary_kind:"sg_navi_editorial_summary",
    locator_kind:"sg_navi_textual_description",
    quote_completeness:"short_fragment_requires_official_context",
    quarantine_state:"not_quarantined_at_read",surrounding_quote:null
  };
  assert.equal(inspectPreview(p).kind,"guidance");
  p.display_evidence[0].display_context.quarantine_state="quarantined";
  assert.equal(inspectPreview(p).kind,"unverified");
});
test("Exact per-item citations, duplicate and nonexistent evidence fail closed",()=>{
  let p=sample();p.research_guidance.steps[0].evidence_ids=["NOT-IN-SOURCES"];
  assert.equal(inspectPreview(p).kind,"unverified");
  p=sample();p.display_evidence.push(source());
  assert.equal(inspectPreview(p).kind,"unverified");
  p=sample();p.research_guidance.citations=[];
  assert.equal(inspectPreview(p).kind,"unverified");
  p=sample();p.display_evidence[0].source_version="old";
  assert.equal(inspectPreview(p).kind,"unverified");
  p=sample();p.display_evidence[0].review_status="quarantined";
  assert.equal(inspectPreview(p).kind,"unverified");
});
test("Task14 claim projection must match each guidance item exactly",()=>{
  const p=sample();
  p.claim_citations=[
    ["potential_channels",0],["conditions",0],["steps",0],["document_checklist",0]
  ].map(([section,index])=>({
    claim_id:section+":"+index,section,index,
    text:p.research_guidance[section][index].text,
    text_kind:"sg_navi_reviewed_template_text",
    evidence_ids:["SCT-ELIG-RESIDENTIAL"]
  }));
  assert.equal(inspectPreview(p).kind,"guidance");
  p.claim_citations[2].text="Tampered recommendation";
  assert.equal(inspectPreview(p).kind,"unverified");
});
test("No fabricated screenshots or non-official insecure/external URLs",()=>{
  assert.equal(safeOfficialURL("http://www.judiciary.gov.sg/civil"),null);
  assert.equal(safeOfficialURL("https://evil.example/"),null);
  assert.equal(safeOfficialURL("https://www.judiciary.gov.sg.evil.example/"),null);
  assert.equal(safeOfficialURL("https://www.judiciary.gov.sg:8443/"),null);
  assert.equal(safeOfficialURL("https://www.judiciary.gov.sg/civil").startsWith("https://"),true);
  let p=sample();p.display_evidence[0].preview={url:"https://example.com/image.png"};
  assert.equal(inspectPreview(p).kind,"unverified");
  p=sample();p.display_evidence[0].verbatim_excerpt="";
  assert.equal(inspectPreview(p).kind,"unverified");
  p=sample();p.display_evidence[0].url="javascript:alert(1)";
  assert.equal(inspectPreview(p).kind,"unverified");
});
test("Conservative limited referral never displays source-backed guidance",()=>{
  const p=sample();
  p.guidance_status="LIMITED_REFERRAL";
  p.research_guidance=null;p.display_evidence=[];
  assert.equal(inspectPreview(p).kind,"limited");
  p.research_guidance=sample().research_guidance;
  assert.equal(inspectPreview(p).kind,"unverified");
});
test("Unsupported versions and incomplete response are not accepted",()=>{
  let p=sample();p.results_version="1.0";assert.equal(inspectPreview(p).kind,"unverified");
  p=sample();p.result_id="invalid";assert.equal(inspectPreview(p).kind,"unverified");
  p=sample();p.research_guidance.conditions="not-an-array";assert.equal(inspectPreview(p).kind,"unverified");
});
