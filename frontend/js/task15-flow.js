"use strict";
/* Approved integrated research workflow. State stays in this tab's memory. */
(function(root,factory){const api=factory();if(typeof module==="object"&&module.exports)module.exports=api;if(root)root.SGNaviTask15=api;})(typeof globalThis!=="undefined"?globalThis:this,function(){
  const CASES=["rental_deposit","consumer_complaint"];
  const LABELS={dispute_with:"Dispute with",premises_type:"Property type",claim_amount_sgd:"Amount (SGD)",tenancy_duration_months:"Tenancy duration (months)",relevant_event_date:"Relevant event date",respondent_in_singapore:"Other party in Singapore",agency_agreement_signed:"Agency agreement signed",purchase_type:"Goods or services",purchase_purpose:"Purchase purpose",supplier_registered_in_sg:"Seller registered in Singapore",supplier_location:"Seller location",problem_type:"Problem type",purchase_date:"Purchase date",resolution_attempted:"Resolution attempted",documents_available:"Documents available"};
  const FIELDS={rental_deposit:["dispute_with","premises_type","claim_amount_sgd","tenancy_duration_months","relevant_event_date","respondent_in_singapore","agency_agreement_signed","resolution_attempted","documents_available"],consumer_complaint:["purchase_type","purchase_purpose","supplier_registered_in_sg","claim_amount_sgd","supplier_location","problem_type","purchase_date","resolution_attempted","documents_available"]};
  const BOOL=new Set(["respondent_in_singapore","agency_agreement_signed","supplier_registered_in_sg","resolution_attempted","documents_available"]);
  const NUMBER=new Set(["claim_amount_sgd","tenancy_duration_months"]);
  const OPTIONS={dispute_with:[["landlord","Landlord"],["agent","Property agent / agency"]],premises_type:[["residential","Residential"],["commercial","Commercial"],["industrial","Industrial"]],purchase_type:[["goods","Goods"],["services","Services"]],purchase_purpose:[["personal","Personal / household use"],["business","Business use"]],supplier_location:[["singapore","Singapore"],["overseas","Outside Singapore"]]};
  const HOSTS=new Set(["www.judiciary.gov.sg","www.cea.gov.sg","www.case.org.sg"]);
  const SECTIONS={potential_channels:"Official channels to check",conditions:"Conditions to confirm",steps:"Preparation steps",document_checklist:"Documents to prepare"};
  const instances=new WeakMap();
  function sanitizeQuery(text){return String(text).replace(/S\$/g,"SGD ").replace(/[^a-zA-Z0-9 ,.!?'\-]/g," ").replace(/\s+/g," ").trim().slice(0,300)||null;}
  function answerLabel(value){return value===null?"Not provided":value==="unknown"?"Not sure":value===true?"Yes":value===false?"No":String(value);}
  function safeSource(raw){try{const u=new URL(raw);return u.protocol==="https:"&&HOSTS.has(u.hostname)&&!u.username&&!u.password&&!u.hash&&(!u.port||u.port==="443")?u.href:null;}catch(_){return null;}}
  function parseAnswer(field,mode,raw){
    if(mode==="missing")return undefined;if(mode==="unknown")return "unknown";if(mode==="null")return null;
    if(BOOL.has(field)){if(raw!=="true"&&raw!=="false")throw Error("Choose Yes, No, or Not sure.");return raw==="true";}
    if(NUMBER.has(field)){if(!String(raw).trim()||!Number.isFinite(Number(raw))||Number(raw)<0)throw Error("Enter a non-negative number, or choose Not sure.");return Number(raw);}
    if(typeof raw!=="string"||!raw.trim()||raw.length>200||/[\x00-\x1f\x7f]/.test(raw))throw Error("Enter a short value, or choose Not sure.");
    return raw.trim();
  }
  async function verifyResult(data,cryptoApi){
    if(!data||data.guidance_version!=="1.0"||data.rule_version!=="mock-1"||data.action_card!==null||!Array.isArray(data.display_evidence)||!Array.isArray(data.claim_citations)||!Array.isArray(data.questions)||!Array.isArray(data.limitations))throw Error("Invalid guidance format");
    if(!["GUIDANCE_ONLY","LIMITED_REFERRAL","CLARIFICATION_REQUIRED","ERROR"].includes(data.guidance_status))throw Error("Invalid guidance status");
    if(data.guidance_status!=="GUIDANCE_ONLY"){
      if(data.display_evidence.length||data.claim_citations.length||data.research_guidance!==null||!Array.isArray(data.matched_evidence_ids)||data.matched_evidence_ids.length)throw Error("Invalid limited result");return data;
    }
    if(!data.research_guidance||!data.result_id||typeof data.source_version!=="string"||!data.source_version||typeof data.context_version!=="string"||!data.context_version||!data.display_evidence.length||!data.claim_citations.length||!Array.isArray(data.matched_evidence_ids)||!cryptoApi||!cryptoApi.subtle)throw Error("Source verification unavailable");
    async function hashOf(text){const bytes=await cryptoApi.subtle.digest("SHA-256",new TextEncoder().encode(text));return Array.from(new Uint8Array(bytes),v=>v.toString(16).padStart(2,"0")).join("");}
    const ids=new Set(), claims=new Set();
    for(const r of data.display_evidence){
      const ctx=r.display_context;
      if(!r.evidence_id||ids.has(r.evidence_id)||r.source_version!==data.source_version||r.review_status!=="verified"||r.display_version!=="1.0"||r.display_state!=="verified_snapshot"||r.preview!==null||!safeSource(r.url)||typeof r.verbatim_excerpt!=="string"||!r.verbatim_excerpt||typeof r.summary!=="string"||!r.publisher||!r.title||!r.source_locator||!Number.isFinite(Date.parse(r.reviewed_at))||!ctx||ctx.context_version!==data.context_version||ctx.quote_kind!=="verbatim_official_excerpt"||ctx.summary_kind!=="sg_navi_editorial_summary"||ctx.quarantine_state!=="not_quarantined_at_read")throw Error("Unverifiable source record");
      if(!Number.isFinite(Date.parse(ctx.checked_at))||!Number.isFinite(Date.parse(ctx.context_reviewed_at))||ctx.check_method!=="automated_live_context_and_digest_check"||ctx.canonical_review_method!=="automated_live_page_and_excerpt_check")throw Error("Missing review identity");
      if(await hashOf(r.verbatim_excerpt)!==r.excerpt_sha256)throw Error("Quote digest mismatch");
      if(ctx.surrounding_quote!==null&&(typeof ctx.surrounding_quote!=="string"||await hashOf(ctx.surrounding_quote)!==ctx.surrounding_quote_sha256))throw Error("Context digest mismatch");
      ids.add(r.evidence_id);
    }
    if(new Set(data.matched_evidence_ids).size!==data.matched_evidence_ids.length||data.matched_evidence_ids.some(id=>!ids.has(id)))throw Error("Invalid matched evidence");
    for(const c of data.claim_citations){
      if(!Object.hasOwn(SECTIONS,c.section)||c.claim_id!==c.section+":"+c.index||claims.has(c.claim_id)||!Array.isArray(c.evidence_ids)||!c.evidence_ids.length||new Set(c.evidence_ids).size!==c.evidence_ids.length||c.evidence_ids.some(id=>!ids.has(id)))throw Error("Unlinked guidance item");
      const item=data.research_guidance[c.section]&&data.research_guidance[c.section][c.index];
      if(!item||item.text!==c.text||JSON.stringify(item.evidence_ids)!==JSON.stringify(c.evidence_ids))throw Error("Mismatched guidance item");
      claims.add(c.claim_id);
    }
    for(const key of Object.keys(SECTIONS))if(!Array.isArray(data.research_guidance[key])||data.research_guidance[key].some((_,index)=>!claims.has(key+":"+index)))throw Error("Incomplete guidance citations");
    return data;
  }
  function init(doc,win){
    if(instances.has(doc))return instances.get(doc);
    const get=id=>doc.getElementById(id), container=get("problem-intake"), form=get("problem-form"), input=get("problem-text"), review=get("problem-review");
    if(!container||!form||!input||!review)return null;
    const make=(tag,text,cls)=>{const n=doc.createElement(tag);if(text!==undefined)n.textContent=String(text);if(cls)n.className=cls;return n;};
    const button=(text,fn,cls="intake-secondary")=>{const b=make("button",text,cls);b.type="button";b.addEventListener("click",fn);return b;};
    const focus=n=>{if(n){n.tabIndex=-1;n.focus();}};
    const flow=make("section",undefined,"task15-flow");flow.id="task15-flow";flow.hidden=true;flow.setAttribute("aria-live","polite");container.appendChild(flow);
    let revision=0,pending=null,currentResult=null,caseType=null,facts={},description="",reviewFields=new Map();
    const cancel=()=>{revision++;if(pending)pending.abort();pending=null;currentResult=null;flow.replaceChildren();flow.hidden=true;container.dataset.flowStage="input";};
    const clearError=()=>{get("problem-validation").textContent="";get("review-validation").textContent="";get("review-outcome").textContent="";};
    async function post(path,payload,token){
      const url=win.SGNaviApiConfig&&win.SGNaviApiConfig.resolve(path,win.location);if(!url)throw Error("API unavailable");
      const controller=new AbortController();pending=controller;const timer=setTimeout(()=>controller.abort(),25000);
      try{const response=await win.fetch(url,{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify(payload),signal:controller.signal,credentials:"omit",cache:"no-store"});if(!response.ok)throw Error("Service unavailable");const data=await response.json();if(token!==revision)throw Error("STALE");return data;}finally{clearTimeout(timer);if(pending===controller)pending=null;}
    }
    function fieldEditor(field,value,allowMissing=false){
      const box=make("label",undefined,"task15-field");box.appendChild(make("span",LABELS[field]||field));
      const mode=make("select");mode.id="task15-mode-"+field;mode.setAttribute("aria-label",(LABELS[field]||field)+" answer state");
      for(const [v,t] of [["known","Enter / choose a value"],["unknown","Not sure"],["null","Not provided"],...(allowMissing?[["missing","Remove this answer"]]:[])]){const o=make("option",t);o.value=v;mode.appendChild(o);}
      let detail;
      const options=BOOL.has(field)?[["true","Yes"],["false","No"]]:OPTIONS[field];
      if(options){detail=make("select");const blank=make("option","Choose a value");blank.value="";detail.appendChild(blank);for(const [v,t] of options){const o=make("option",t);o.value=v;detail.appendChild(o);}}
      else{detail=make("input");detail.type=NUMBER.has(field)?"number":field.endsWith("_date")?"date":"text";detail.maxLength=200;if(NUMBER.has(field)){detail.min="0";detail.step="any";}}
      detail.id="task15-value-"+field;detail.setAttribute("aria-label",LABELS[field]||field);detail.value=value===null||value==="unknown"||value===undefined?"":String(value);
      mode.value=value===null?"null":value==="unknown"?"unknown":"known";
      const visibility=()=>{detail.hidden=mode.value!=="known";};visibility();mode.addEventListener("change",visibility);
      box.append(mode,detail);
      return {node:box,detail,read:()=>parseAnswer(field,mode.value,detail.value)};
    }
    function showReview(){
      review.hidden=false;flow.hidden=true;container.dataset.flowStage="review";get("review-summary").textContent=description;
      const list=get("candidate-list");list.replaceChildren();reviewFields=new Map();
      for(const field of FIELDS[caseType]||[]){if(!Object.hasOwn(facts,field))continue;const e=fieldEditor(field,facts[field],true);reviewFields.set(field,e);list.appendChild(e.node);}
      const missing=(FIELDS[caseType]||[]).filter(f=>!reviewFields.has(f));
      if(missing.length){const add=make("select");add.id="task15-add-field";add.setAttribute("aria-label","Add an optional detail");const blank=make("option","Add another detail (optional)");blank.value="";add.appendChild(blank);for(const f of missing){const o=make("option",LABELS[f]);o.value=f;add.appendChild(o);}add.addEventListener("change",()=>{if(add.value){const f=add.value;facts[f]="unknown";showReview();reviewFields.get(f).detail.focus();}});list.appendChild(add);}
      get("candidate-facts").hidden=!caseType;get("review-continue").textContent="Confirm details and continue";focus(get("review-title"));
    }
    function showFailure(retry){
      flow.hidden=false;flow.replaceChildren();const h=make("h3","The service is unavailable");h.id="task15-error-title";flow.append(h,make("p","Your answers are still here. Retry when the connection is available; no guidance has been confirmed."));
      flow.append(button("Retry",retry,"intake-primary"),button("Edit answers",editAnswers));focus(h);
    }
    function editAnswers(){cancel();clearError();get("interpretation-note").textContent="Review and correct your answers, then confirm again. Previous results have been cleared.";showReview();}
    function showQuestion(data,token){
      const question=data.questions.find(q=>!Object.hasOwn(facts,q.id));
      if(!question){showLimited({limitations:["These details remain uncertain. Edit your answers or check directly with the appropriate official service."]});return;}
      if(!(FIELDS[caseType]||[]).includes(question.id)||typeof question.label!=="string")throw Error("Unexpected question");
      flow.hidden=false;flow.replaceChildren();container.dataset.flowStage="questions";const h=make("h3","A detail to confirm");h.id="task15-question-title";
      const qform=make("form");qform.id="task15-question-form";qform.noValidate=true;const prompt=make("p",question.label);prompt.id="task15-question-label";
      const editor=fieldEditor(question.id,undefined);editor.node.setAttribute("aria-describedby",prompt.id);const error=make("p","","problem-error");error.id="task15-question-error";error.setAttribute("role","alert");
      const save=make("button","Save and continue","intake-primary");save.type="submit";save.id="task15-save-answer";qform.append(prompt,editor.node,error,save,button("Edit answers",editAnswers));
      qform.addEventListener("submit",event=>{event.preventDefault();if(token!==revision)return;try{facts[question.id]=editor.read();perform();}catch(e){error.textContent=e.message;editor.detail.focus();}});
      flow.append(h,qform);focus(h);editor.detail.focus();
    }
    function showLimited(data){
      flow.hidden=false;flow.replaceChildren();container.dataset.flowStage="limited";const h=make("h3","More confirmation is needed");h.id="task15-limited-title";
      flow.appendChild(h);for(const line of data.limitations||[])flow.appendChild(make("p",line));flow.appendChild(button("Edit answers",editAnswers));focus(h);
    }
    function renderResult(data){
      currentResult=data;flow.hidden=false;flow.replaceChildren();container.dataset.flowStage="results";const h=make("h3","Your guidance");h.id="task15-result-title";
      flow.append(h,make("p","Official research and preparation information — eligibility is not assessed.","task15-notice"));
      const factList=make("dl",undefined,"task15-fact-summary");for(const [field,value]of Object.entries(facts)){factList.append(make("dt",LABELS[field]||field),make("dd",answerLabel(value)));}flow.appendChild(factList);
      const grid=make("div",undefined,"task15-result-grid"), cards=make("div"), viewer=make("aside",undefined,"task15-viewer");viewer.id="task15-evidence-viewer";grid.append(cards,viewer);flow.appendChild(grid);
      const records=new Map(data.display_evidence.map(r=>[r.evidence_id,r]));
      function showRecord(record,claim){
        viewer.replaceChildren();const title=make("h4",record.title);title.id="task15-source-title";viewer.append(make("p",record.publisher,"task15-publisher"),title);
        if(claim)viewer.appendChild(make("p","Evidence for: "+claim.text,"task15-selected-claim"));
        viewer.append(make("p","Recorded official wording","task15-source-label"));const quote=make("blockquote",record.verbatim_excerpt);quote.id="task15-original-quote";viewer.appendChild(quote);
        viewer.append(make("p","SG Navi explanation","task15-source-label"),make("p",record.summary));
        const ctx=record.display_context;if(ctx.surrounding_quote){const details=make("details");details.open=true;details.append(make("summary","Recorded surrounding context"),make("blockquote",ctx.surrounding_quote));viewer.appendChild(details);}
        viewer.append(make("p","Where to look: "+record.source_locator),make("p","Recorded automated review: "+new Date(record.reviewed_at).toLocaleDateString("en-SG")),make("p","Source context checked: "+new Date(ctx.checked_at).toLocaleDateString("en-SG")),make("p","Evidence ID: "+record.evidence_id,"task15-evidence-id"));
        const link=make("a","Open original source");link.id="task15-open-original";link.href=safeSource(record.url);link.target="_blank";link.rel="noopener noreferrer";viewer.appendChild(link);
      }
      function selectClaim(claim){
        viewer.replaceChildren();const choices=make("div",undefined,"task15-source-choices");for(const eid of claim.evidence_ids){const r=records.get(eid);const b=button(r.publisher+" · "+eid,()=>{showRecord(r,claim);viewer.prepend(choices);focus(get("task15-source-title"));});b.dataset.evidenceId=eid;choices.appendChild(b);}showRecord(records.get(claim.evidence_ids[0]),claim);viewer.prepend(choices);focus(get("task15-source-title"));
      }
      const summary=make("section",undefined,"task15-card-section");summary.dataset.cardSection="case_summary";summary.append(make("h4","Your situation"),make("p",data.research_guidance.case_summary));cards.appendChild(summary);
      for(const [key,label] of Object.entries(SECTIONS)){
        const section=make("section",undefined,"task15-card-section");section.dataset.cardSection=key;section.appendChild(make("h4",label));
        for(const c of data.claim_citations.filter(c=>c.section===key)){const b=button(c.text,()=>selectClaim(c),"task15-claim");b.dataset.claimId=c.claim_id;section.appendChild(b);}cards.appendChild(section);
      }
      const unresolved=make("section",undefined,"task15-card-section");unresolved.dataset.cardSection="unresolved_questions";unresolved.appendChild(make("h4","Questions still open"));
      for(const q of data.research_guidance.unresolved_questions||[])unresolved.appendChild(make("p",q.text));if(!(data.research_guidance.unresolved_questions||[]).length)unresolved.appendChild(make("p","Check the full official conditions before acting."));cards.appendChild(unresolved);
      const references=make("section",undefined,"task15-card-section");references.dataset.cardSection="citations";references.appendChild(make("h4","References matched to your question"));
      const referenceButton=r=>{const b=button(r.publisher+" · "+r.evidence_id,()=>{showRecord(r,null);focus(get("task15-source-title"));},"task15-reference");b.dataset.referenceId=r.evidence_id;return b;};
      for(const eid of data.matched_evidence_ids)references.appendChild(referenceButton(records.get(eid)));
      if(!data.matched_evidence_ids.length)references.appendChild(make("p","Select a preparation item to inspect its supporting records."));
      const all=make("details");all.appendChild(make("summary","All references supporting these checks"));for(const r of data.display_evidence)all.appendChild(referenceButton(r));references.appendChild(all);cards.appendChild(references);
      const limits=make("details",undefined,"task15-limits");limits.appendChild(make("summary","Scope and unresolved conditions"));for(const line of data.limitations)limits.appendChild(make("p",line));flow.appendChild(limits);
      const edit=button("Edit answers",editAnswers);edit.id="task15-edit-answers";flow.append(edit,button("Check again",perform));
      const first=data.claim_citations.find(c=>c.section==="steps")||data.claim_citations[0];selectClaim(first);focus(h);
    }
    async function perform(){
      cancel();clearError();review.hidden=true;flow.hidden=false;flow.appendChild(make("p","Checking your confirmed details and source records…"));const token=revision;
      try{
        const confirmation=await post("/api/intake/confirm",{intake_version:"1.0",confirmed:true,case_type:caseType,confirmed_answers:{...facts}},token);
        if(confirmation.intake_version!=="1.0"||confirmation.intake_status!=="confirmed"||confirmation.needs_confirmation!==false||typeof confirmation.revision!=="string")throw Error("Invalid confirmation");
        const data=await post("/api/guidance",{guidance_version:"1.0",confirmed:true,case_type:caseType,confirmed_answers:{...facts},confirmation_revision:confirmation.revision,query:sanitizeQuery(description)},token);
        await verifyResult(data,win.crypto);if(token!==revision)return;if(data.confirmation_revision!==confirmation.revision)throw Error("Confirmation revision mismatch");
        if(data.guidance_status==="CLARIFICATION_REQUIRED")showQuestion(data,token);else if(data.guidance_status==="GUIDANCE_ONLY")renderResult(data);else if(data.guidance_status==="ERROR")showFailure(perform);else showLimited(data);
      }catch(e){if(token===revision)showFailure(perform);}
    }
    form.addEventListener("submit",async event=>{
      event.preventDefault();const text=input.value.trim();if(!text||text.length>1200){get("problem-validation").textContent="Describe your situation in 1 to 1,200 characters.";input.focus();return;}
      cancel();clearError();review.hidden=true;description=text;facts={};caseType=null;const token=revision;get("problem-submit").disabled=true;get("problem-validation").textContent="Checking your description…";
      try{const data=await post("/api/intake",{intake_version:"1.0",description:text},token);if(data.intake_version!=="1.0"||data.needs_confirmation!==true||!data.candidate_facts||typeof data.candidate_facts!=="object"||!["suggested","ambiguous","out_of_scope","cannot_determine"].includes(data.intake_status))throw Error("Invalid intake");
        caseType=data.intake_status==="suggested"&&CASES.includes(data.suggested_case_type)?data.suggested_case_type:null;facts=caseType?{...data.candidate_facts}:{};
        doc.querySelectorAll('input[name="review-topic"]').forEach(r=>{r.checked=r.value===caseType;});
        get("interpretation-note").textContent=caseType?"Suggested topic and facts are unconfirmed. Correct them, then explicitly confirm below.":data.intake_status==="out_of_scope"?"This description is outside the supported topics. No route has been selected.":"A single supported topic could not be determined. Choose the correct topic yourself or edit your description.";
        clearError();showReview();
      }catch(e){if(token===revision){get("problem-validation").textContent="We could not check the description. Your text is still here; try Find Guidance again.";}}
      finally{if(token===revision)get("problem-submit").disabled=false;}
    });
    doc.querySelectorAll('input[name="review-topic"]').forEach(r=>r.addEventListener("change",()=>{if(r.checked){cancel();caseType=CASES.includes(r.value)?r.value:null;facts={};showReview();}}));
    get("review-continue").addEventListener("click",()=>{
      clearError();const chosen=review.querySelector('input[name="review-topic"]:checked');if(!chosen){get("review-validation").textContent="Choose a topic, Not sure, or Another topic.";return;}
      if(!CASES.includes(chosen.value)){cancel();get("review-outcome").textContent="No supported topic is confirmed. Edit the description or check with an appropriate official service.";return;}
      caseType=chosen.value;
      try{const next={};for(const [field,editor] of reviewFields){const value=editor.read();if(value!==undefined)next[field]=value;}facts=next;perform();}catch(e){get("review-validation").textContent=e.message;}
    });
    get("review-back").addEventListener("click",()=>{cancel();clearError();review.hidden=true;input.focus();});
    input.addEventListener("input",()=>{cancel();review.hidden=true;get("problem-submit").disabled=false;get("problem-count").textContent=input.value.length+" / 1,200";clearError();});
    doc.querySelectorAll("[data-example-question]").forEach(b=>b.addEventListener("click",()=>{input.value=b.getAttribute("data-example-question");input.dispatchEvent(new Event("input",{bubbles:true}));input.focus();}));
    const control=Object.freeze({cancel});instances.set(doc,control);container.dataset.task15Ready="true";get("problem-submit").disabled=false;return control;
  }
  return Object.freeze({sanitizeQuery,answerLabel,safeSource,parseAnswer,verifyResult,init});
});
