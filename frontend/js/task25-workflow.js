"use strict";
/* Task25: read-only pathway research. Not official eligibility or filing status. */
(function(root,factory){
 const api=factory();
 if(typeof module==="object"&&module.exports)module.exports=api;
 if(root)root.SGNaviTask25=api;
})(typeof globalThis!=="undefined"?globalThis:this,function(){
 const SOURCES=Object.freeze({
  caseScope:{id:"CASE-SCOPE",url:"https://www.case.org.sg/submit-a-complaint/",status:"task17"},
  caseAssessment:{id:"CASE-ASSESS",url:"https://www.case.org.sg/submit-a-complaint/",status:"task17"},
  caseFees:{id:"CASE-FEES",url:"https://www.case.org.sg/submit-a-complaint/",status:"task17"},
  sctCriteria:{id:"COURTS-RESIDENTIAL",url:"https://www.judiciary.gov.sg/civil/cases-eligible-small-claim",status:"task17"},
  sctFiling:{id:"COURTS-RECORDS",url:"https://www.judiciary.gov.sg/civil/how-to-file-serve-small-claim",status:"task17"},
  sctOverview:{id:null,url:"https://www.judiciary.gov.sg/civil/file-small-claim",status:"pending_review"},
  ceaConduct:{id:"CEA-CONDUCT-ROUTE",url:"https://www.cea.gov.sg/submit-complaint/",status:"task17"},
  ceaAgreement:{id:"CEA-AGREEMENT-ROUTE",url:"https://www.cea.gov.sg/consumers/engaging-a-property-agent/dispute-resolution/",status:"task17"}
 });
 const TEMPLATES=Object.freeze({
  case:{id:"case",title:"CASE — Consumer assistance",stages:[
   {title:"Confirm the consumer-to-business scope",description:"Check whether CASE handles this consumer purchase dispute.",source:"caseScope"},
   {title:"Submit a complaint for consultation, if appropriate",description:"CASE officers assess submitted complaints and advise the next steps.",source:"caseAssessment"},
   {title:"Consider assistance or case filing",description:"After consultation, CASE may offer an assisted scheme or case service; fees can apply.",source:"caseFees"},
   {title:"Explore mediation or another route if unresolved",description:"CASE may discuss mediation or other recourse, including SCT, depending on the dispute.",source:"caseScope"}]},
  sct:{id:"sct",title:"SCT — Small Claims Tribunals",stages:[
   {title:"Check claim eligibility before filing",description:"Check claim type, amount, time limit, respondent location and any residential tenancy term.",source:"sctCriteria"},
   {title:"Complete the CJTS pre-filing assessment",description:"The pre-filing assessment helps you assess the claim; it is not a final eligibility decision.",source:"sctCriteria"},
   {title:"File, serve and confirm service if eligible",description:"The Courts describe filing, fees, service and the Declaration of Service on CJTS.",source:"sctFiling"},
   {title:"Consider settlement, consultation or a hearing",description:"Filed cases may involve online resolution, consultation and possibly a hearing.",source:"sctOverview"},
   {title:"Check available post-order steps where necessary",description:"If the tribunal makes an order, check the current Courts guidance on enforcement or review.",source:"sctOverview"}]},
  ceaConduct:{id:"ceaConduct",title:"CEA — Agent-conduct complaint",stages:[
   {title:"Check whether the concern is estate agency misconduct",description:"CEA investigates estate agency work, not every landlord-tenant payment dispute.",source:"ceaConduct"},
   {title:"Prepare information and submit a complaint",description:"CEA asks for a chronology, agent details, supporting documents and contact information.",source:"ceaConduct"},
   {title:"CEA assesses the case and may investigate",description:"If within its remit, CEA may seek statements or investigate the agency or agent.",source:"ceaConduct"},
   {title:"Check the regulatory outcome",description:"Regulatory action is possible, but compensation is not guaranteed.",source:"ceaConduct"}]},
  ceaAgreement:{id:"ceaAgreement",title:"CEA — Agency agreement dispute",stages:[
   {title:"Approach the property agency about the dispute",description:"Describe the agreement issue to the agency and retain the communication.",source:"ceaAgreement"},
   {title:"Check the signed agreement and scheme scope",description:"CEA's scheme covers disputes arising from a relevant signed agency agreement.",source:"ceaAgreement"},
   {title:"Explore mediation or arbitration",description:"The scheme offers mediation and arbitration through approved independent centres.",source:"ceaAgreement"},
   {title:"Review arbitration if mediation does not resolve it",description:"Further arbitration may be an option; check current conditions and deadlines.",source:"ceaAgreement"}]}
 });
 const REASONS=Object.freeze({
  caseForm:"A CASE complaint form is verified for this result. Consultation still determines later options.",
  caseEnquiry:"CASE enquiry contacts are available; this does not confirm eligibility to file.",
  caseVisitor:"Visitor circumstances may need a different channel; check CASE guidance before attempting a complaint.",
  caseUnknown:"Check CASE's consumer-to-business scope before taking formal action.",
  sctConsumer:"SCT may cover certain consumer disputes. Claim amount, timing and jurisdiction still need checking.",
  sctRental:"SCT may cover residential tenancies of no more than two years. Term, amount and other rules need checking.",
  ceaConduct:"CEA handles estate agency conduct, not an automatic landlord deposit refund.",
  ceaSigned:"A signed agency agreement was reported; check that the dispute arises from its terms.",
  ceaUnknown:"A qualifying signed agency agreement has not been confirmed. Check the agreement first."
 });
 const UI=Object.freeze([
  "Potential official routes to review",
  "These are official reference pathways, not a decision that you may file a claim.",
  "Explore the possible stages",
  "Read official process page",
  "View verified supporting source",
  "This is background guidance, not a verified filing channel for this result.",
  "This new reference is pending independent source-owner review.",
  "Only contacts returned and verified for your case are actionable in SG Navi."
 ]);
 function buildRoutes(ctx,plan,contacts){
  if(!ctx||!ctx.facts||!plan||!contacts||typeof contacts.has!=="function")return [];
  const f=ctx.facts,result=[];
  const add=(id,reason)=>{
   const t=TEMPLATES[id];result.push({id:t.id,title:t.title,reason,
    stages:t.stages.map(s=>({...s}))});
  };
  if(ctx.case_type==="consumer_complaint"){
   if(f.merchant_location==="singapore"&&f.purchase_purpose!=="business"){
    let message=REASONS.caseUnknown;
    if(f.consumer_context==="visitor")message=REASONS.caseVisitor;
    else if(contacts.has("case-form"))message=REASONS.caseForm;
    else if(contacts.has("case-phone")||contacts.has("case-email"))message=REASONS.caseEnquiry;
    add("case",message);
   }
   if(f.merchant_location!=="outside_singapore")add("sct",REASONS.sctConsumer);
  }else if(ctx.case_type==="rental_deposit"){
   if(f.dispute_with==="landlord"&&!["commercial","industrial"].includes(f.premises_type))
    add("sct",REASONS.sctRental);
   if(f.dispute_with==="agent"&&ctx.issue_subtype==="agent_conduct")
    add("ceaConduct",REASONS.ceaConduct);
   if(f.dispute_with==="agent"&&ctx.issue_subtype==="agency_agreement")
    add("ceaAgreement",f.agency_agreement_signed===true?REASONS.ceaSigned:REASONS.ceaUnknown);
  }
  return result;
 }
 const COPY=Object.freeze([...Object.values(TEMPLATES).flatMap(t=>[t.title,...t.stages.flatMap(s=>[s.title,s.description])]),...Object.values(REASONS),...UI]);
 return Object.freeze({SOURCES,TEMPLATES,REASONS,UI,COPY,buildRoutes});
});
