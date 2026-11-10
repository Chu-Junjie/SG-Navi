"use strict";
/* Action Plan 1.0 frontend: actual Task18/19 API, reviewed Task17 source records.
   No browser persistence, no auto-sending, no legal eligibility inference. */
(function(root,factory){
  const api=factory();
  if(typeof module==="object"&&module.exports)module.exports=api;
  if(root)root.SGNaviTask21=api;
})(typeof globalThis!=="undefined"?globalThis:this,function(){
  const HOSTS=new Set(["www.case.org.sg","complaints.case.org.sg","www.ccs.gov.sg","www.judiciary.gov.sg",
    "cjts.judiciary.gov.sg","www.cea.gov.sg","www.hdb.gov.sg","www.mom.gov.sg",
    "sso.agc.gov.sg","www.elitigation.sg","isomer-user-content.by.gov.sg"]);
  const SUBTYPES={
    rental_deposit:["deposit_return","deposit_deduction","early_exit","pass_related_exit","agent_conduct","agency_agreement","unspecified"],
    consumer_complaint:["restaurant_overcharge","duplicate_charge","unclear_charge","goods_dispute","services_dispute","unspecified"]
  };
  const GOALS=["complain","seek_refund","prepare_claim","understand_options","contact_provider"];
  const LABEL=s=>String(s).replace(/_/g," ").replace(/\b\w/g,c=>c.toUpperCase());
  const object=x=>x!==null&&typeof x==="object"&&!Array.isArray(x);
  const isText=(x,max=500)=>typeof x==="string"&&x.length>0&&x.length<=max;
  const hex=(x,n)=>typeof x==="string"&&new RegExp("^[0-9a-f]{"+n+"}$").test(x);
  function safeURL(raw,source=false){
    if(!isText(raw,600)||/[\s\\]/.test(raw))return null;
    try{
      const u=new URL(raw);
      if(u.protocol!=="https:"||u.username||u.password||u.port||u.hash||!HOSTS.has(u.hostname.toLowerCase())||
        (u.search&&!(source&&u.hostname==="sso.agc.gov.sg")))return null;
      return u.href;
    }catch(_){return null;}
  }
  function safeContact(c){
    if(!object(c)||!isText(c.id,80)||!isText(c.institution,160)||!Array.isArray(c.evidence_ids)||
      !c.evidence_ids.length)return null;
    if(c.kind==="web")return safeURL(c.value)?{href:safeURL(c.value),external:true}:null;
    if(c.kind==="phone"&&typeof c.value==="string"&&/^\+65[0-9]{8}$/.test(c.value))
      return {href:"tel:"+c.value,external:false};
    if(c.kind==="email"&&typeof c.value==="string"&&/^[A-Za-z0-9_.+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$/.test(c.value))
      return {href:"mailto:"+c.value,external:false};
    return null;
  }
  async function digest(text,cryptoApi){
    if(!cryptoApi?.subtle||typeof TextEncoder==="undefined")throw Error("Evidence hashing unavailable");
    const data=new TextEncoder().encode(text),bytes=new Uint8Array(await cryptoApi.subtle.digest("SHA-256",data));
    return [...bytes].map(n=>n.toString(16).padStart(2,"0")).join("");
  }
  function canonical(value){
    if(Array.isArray(value))return "["+value.map(canonical).join(",")+"]";
    if(object(value))return "{"+Object.keys(value).sort().map(k=>JSON.stringify(k)+":"+canonical(value[k])).join(",")+"}";
    return JSON.stringify(value);
  }
  async function revisionOf(ctx,cryptoApi){
    if(!object(ctx)||!object(ctx.facts))throw Error("Invalid context");
    const agreed={case_type:ctx.case_type,issue_subtype:ctx.issue_subtype,goal:ctx.goal,facts:ctx.facts};
    return (await digest(canonical(agreed),cryptoApi)).slice(0,24);
  }
  function validContext(ctx){
    return object(ctx)&&Object.hasOwn(SUBTYPES,ctx.case_type)&&
      SUBTYPES[ctx.case_type].includes(ctx.issue_subtype)&&GOALS.includes(ctx.goal)&&
      object(ctx.facts)&&isText(ctx.summary,280);
  }
  async function verifyResponse(data,request,cryptoApi){
    if(!object(data)||data.action_plan_version!=="1.0"||data.request_id!==request.request_id||
       !["CONFIRM","ASK","READY","LIMITED","UNAVAILABLE"].includes(data.state)||
       !isText(data.message,300)||!Object.hasOwn(data,"context")||
       !Object.hasOwn(data,"revision")||!Object.hasOwn(data,"question")||!Object.hasOwn(data,"plan"))
      throw Error("Unexpected service response");
    if(request.operation==="interpret"&&!(["CONFIRM","LIMITED","UNAVAILABLE"].includes(data.state)))
      throw Error("Unexpected interpretation state");
    if(data.state==="UNAVAILABLE"){
      if(data.context!==null||data.revision!==null||data.plan!==null||data.question!==null)
        throw Error("Invalid unavailable response");
      return data;
    }
    if(data.state==="CONFIRM"){
      if(!validContext(data.context)||data.plan!==null||data.question!==null||data.revision!==null)
        throw Error("Invalid confirmation");
      return data;
    }
    if(request.operation==="plan"&&data.state==="CONFIRM")throw Error("Unexpected repeated confirmation");
    if(data.context!==null){
      if(!validContext(data.context)||!hex(data.revision,24)||
        data.revision!==await revisionOf(data.context,cryptoApi)||
        request.operation==="plan"&&canonical(data.context.facts)!==canonical(request.context.facts)||
        request.operation==="plan"&&data.revision!==await revisionOf(request.context,cryptoApi))
        throw Error("Stale context or changed answers");
    }else if(data.revision!==null)throw Error("Revision without context");
    if(data.state==="ASK"){
      const q=data.question;
      if(!validContext(data.context)||!object(q)||!isText(q.prompt,160)||!isText(q.reason,220)||
        !isText(q.field,80)||Object.hasOwn(data.context.facts,q.field)||
        !Array.isArray(q.options)||q.options.length<2||q.options.length>7||
        q.options.some(x=>!object(x)||!isText(x.label,85)||!Object.hasOwn(x,"value"))||
        !q.options.some(x=>x.value==="unknown")||data.plan!==null)
        throw Error("Invalid follow-up");
      return data;
    }
    if(data.question!==null)throw Error("Unexpected question");
    if(data.state==="LIMITED"){
      if(data.plan!==null)throw Error("Unsupported limited action");
      return data;
    }
    if(!validContext(data.context)||!object(data.plan)||!hex(data.revision,24))
      throw Error("Invalid ready plan");
    const p=data.plan;
    if(!isText(p.headline,120)||!object(p.assessment)||!object(p.primary_action)||
      !Array.isArray(p.checklist)||!p.checklist.length||p.checklist.length>5||
      !Array.isArray(p.contacts)||!Array.isArray(p.details)||!Array.isArray(p.legal_basis)||
      !Array.isArray(p.evidence)||!p.evidence.length||!isText(p.source_version,80))
      throw Error("Incomplete action guidance");
    const sources=new Map();
    for(const e of p.evidence){
      if(!object(e)||!isText(e.id,80)||sources.has(e.id)||!safeURL(e.url,true)||
        e.review_status!=="verified"||!["statute","official_procedure","contract_template"].includes(e.kind)||
        !isText(e.quote,450)||!hex(e.quote_sha256,64)||!hex(e.source_sha256,64)||
        await digest(e.quote,cryptoApi)!==e.quote_sha256||
        !isText(e.publisher,140)||!isText(e.title,200)||!Number.isFinite(Date.parse(e.reviewed_at))||
        e.kind==="statute"&&(!isText(e.provision,160)||!isText(e.edition,160)))
        throw Error("Official evidence does not pass verification");
      sources.set(e.id,e);
    }
    const used=new Set(), claims=new Map();
    function claim(c){
      if(!object(c)||!isText(c.id,80)||claims.has(c.id)||!isText(c.text,380)||
         !Array.isArray(c.evidence_ids)||!c.evidence_ids.length||
         new Set(c.evidence_ids).size!==c.evidence_ids.length||
         c.evidence_ids.some(id=>!sources.has(id)))throw Error("Unlinked claim");
      claims.set(c.id,c);c.evidence_ids.forEach(x=>used.add(x));
    }
    claim(p.assessment);claim(p.primary_action);
    for(const item of p.checklist)claim(item);
    for(const group of p.details){
      if(!object(group)||!["documents","pitfalls","alternatives","conditions"].includes(group.kind)||
        !Array.isArray(group.items))throw Error("Invalid details");
      for(const item of group.items)claim(item);
    }
    const contacts=new Map();
    for(const c of p.contacts){
      const dest=safeContact(c);
      if(!dest||contacts.has(c.id)||c.evidence_ids.some(id=>!sources.has(id)))throw Error("Invalid contact");
      contacts.set(c.id,{...c,...dest});c.evidence_ids.forEach(id=>used.add(id));
    }
    if(used.size!==sources.size)throw Error("Unreferenced source");
    if(p.primary_action.kind==="prepare"){
      if(p.primary_action.contact_id!==null)throw Error("Unexpected external action");
    }else{
      const selected=contacts.get(p.primary_action.contact_id);
      const allowed={consult:["consumer_assistance","agency_agreement_help","procedure_information"],
        complaint_intake:["complaint_intake","agency_conduct"],
        check_criteria:["procedure_information"]}[p.primary_action.kind];
      if(!selected||!allowed?.includes(selected.purpose)||
         selected.evidence_ids.some(id=>!p.primary_action.evidence_ids.includes(id)))
        throw Error("Unverified action route");
    }
    for(const l of p.legal_basis){
      const c=claims.get(l.claim_id),e=sources.get(l.evidence_id);
      if(!c||!e||e.kind!=="statute"||!c.evidence_ids.includes(l.evidence_id))
        throw Error("Unrelated legal quote");
    }
    if(p.draft!==null){
      if(!object(p.draft)||!isText(p.draft.subject,160)||!isText(p.draft.body,1600)||
         !Array.isArray(p.draft.slots)||p.draft.slots.some(s=>!isText(s.id,80)||!isText(s.label,100)))
        throw Error("Invalid editable draft");
      const slots=[...new Set([...p.draft.subject,...p.draft.body].join("").match(/\{[A-Za-z0-9_-]+\}/g)||[])].map(s=>s.slice(1,-1));
      if(slots.length!==p.draft.slots.length||p.draft.slots.some(s=>!slots.includes(s.id)))
        throw Error("Incomplete draft fields");
    }
    return {...data,verifiedSources:sources,verifiedContacts:contacts};
  }
  // Check every value that links the approved display to canonical Action Plan data.
  // Returning null means the entire display falls back to canonical English.
  function reviewedDisplay(envelope){
    const data=envelope?.canonical, display=envelope?.display;
    const text=value=>isText(value,1800)&&Boolean(value.trim());
    const texts=(row,keys)=>object(row)&&keys.every(key=>text(row[key]));
    const matches=(row,original,keys)=>object(row)&&object(original)&&
      keys.every(key=>Object.hasOwn(row,key)&&canonical(row[key])===canonical(original[key]));
    const rows=(translated,original,check)=>Array.isArray(translated)&&translated.length===original.length&&
      translated.every((row,index)=>check(row,original[index]));
    const claim=(row,original)=>texts(row,["text"])&&matches(row,original,["id","evidence_ids"]);
    const slots=draft=>[...new Set((draft.subject+"\n"+draft.body).match(/\{[A-Za-z0-9_-]+\}/g)||[])].sort();
    if(!data||envelope.overlay_version!=="task24-reviewed-1.0"||envelope.locale!=="zh-Hans"||
      envelope.translation_status!=="approved_explanation"||envelope.is_official_translation!==false||
      envelope.reviewed_by!=="Chu-Junjie"||!Number.isFinite(Date.parse(envelope.reviewed_at))||
      !hex(envelope.entries_sha256,64)||!text(envelope.disclaimer)||!texts(display,["message"])||
      (data.context?!text(display.context_summary):display.context_summary!==null))return null;
    const q=display.question, originalQuestion=data.question;
    if(originalQuestion?(!texts(q,["prompt","reason"])||!matches(q,originalQuestion,["id","field"])||
      !rows(q.options,originalQuestion.options,(row,original)=>texts(row,["label"])&&matches(row,original,["value"]))):q!==null)return null;
    const p=display.plan, originalPlan=data.plan;
    if(!originalPlan)return p===null?display:null;
    if(!texts(p,["headline"])||!claim(p.assessment,originalPlan.assessment)||
      !claim(p.primary_action,originalPlan.primary_action)||!text(p.primary_action.label)||
      !matches(p.primary_action,originalPlan.primary_action,["kind","contact_id"])||
      !rows(p.checklist,originalPlan.checklist,claim)||
      !rows(p.details,originalPlan.details,(row,original)=>texts(row,["title"])&&
        matches(row,original,["kind"])&&rows(row.items,original.items,claim))||
      !rows(p.contacts,originalPlan.contacts,(row,original)=>texts(row,["institution","purpose"])&&
        (original.note?text(row.note):row.note===null)&&matches(row,original,["id","kind","value","evidence_ids"])))return null;
    if(originalPlan.draft?(!texts(p.draft,["title","subject","body"])||
      !rows(p.draft.slots,originalPlan.draft.slots,(row,original)=>texts(row,["label"])&&matches(row,original,["id"]))||
      canonical(slots(p.draft))!==canonical(slots(originalPlan.draft))):p.draft!==null)return null;
    return display;
  }
  function init(doc,win){
    const get=id=>doc.getElementById(id),host=get("problem-intake"),form=get("problem-form"),input=get("problem-text");
    if(!host||!form||!input)return null;
    const setText=(el,content,source=false,reviewed)=>{
      el.textContent=String(content);
      if(reviewed!==undefined&&win.SGNaviLocale?.observeReviewedText)win.SGNaviLocale.observeReviewedText(el,content,reviewed);
      else win.SGNaviLocale?.observeText(el,content,source);
    };
    const add=(tag,content,cls,reviewed)=>{
      const el=doc.createElement(tag);
      if(content!==undefined)setText(el,content,tag==="blockquote",reviewed);
      if(cls)el.className=cls;return el;
    };
    const productCopy=(original,reviewed)=>reviewed??win.SGNaviLocale?.chineseCopy?.(original)??null;
    const officialText=(tag,content)=>{
      const el=add(tag);
      setText(el,content,true);
      return el;
    };
    const fieldLabel=(text,reviewed)=>{
      const label=add("label",undefined,"task21-field");
      // Replace only the text span when changing locale; the nested control keeps its state.
      label.appendChild(add("span",text,undefined,reviewed));
      return label;
    };
    const btn=(label,fn,cls="intake-secondary",reviewed)=>{
      const b=add("button",label,cls,reviewed);b.type="button";b.addEventListener("click",fn);return b;
    };
    let serial=0,controller=null,context=null,description="",stage="input",lastFocus=null,pending=false;
    let previousContexts=[],reply=null,checkedProcess=new Set();
    let summaryDisplay=null,refreshOpenDraft=null;
    function appendReviewedNotice(container,disclaimer){
      if(!disclaimer)return;
      const note=add("p",undefined,"task23-unofficial");
      note.dataset.task24ReviewedNotice="true";
      note.textContent=disclaimer;
      note.hidden=win.SGNaviLocale?.getLanguage()!=="zh";
      container.appendChild(note);
    }
    function rememberSummary(data){
      summaryDisplay=data.context&&data.reviewedDisplay?{
        english:data.context.summary,chinese:data.reviewedDisplay.context_summary,disclaimer:data.reviewedDisclaimer
      }:null;
    }
    const overlay=add("div",undefined,"task20-overlay");overlay.hidden=true;overlay.id="task21-overlay";
    const dialog=add("section",undefined,"task20-dialog");dialog.setAttribute("role","dialog");dialog.setAttribute("aria-modal","true");
    const heading=add("div",undefined,"task20-dialog-head");
    heading.appendChild(add("strong","SG Navi"));
    const dialogControls=add("div",undefined,"task23-dialog-controls");
    const close=btn("×",()=>hideDialog(),"task20-close");
    if(win.SGNaviLocale){
      const languages=add("div",undefined,"task23-language");
      languages.setAttribute("role","group");
      languages.setAttribute("aria-label",win.SGNaviLocale.label("Language / 语言"));
      for(const [code,text,tag] of [["en","EN","en"],["zh","中文","zh-Hans"]]){
        const button=add("button");button.type="button";button.textContent=text;
        button.lang=tag;button.dataset.task23Language=code;
        button.setAttribute("aria-pressed",String(win.SGNaviLocale.getLanguage()===code));
        languages.appendChild(button);
      }
      dialogControls.appendChild(languages);
    }
    dialogControls.appendChild(close);heading.appendChild(dialogControls);
    function localizeDialogLabels(){
      dialog.setAttribute("aria-label",win.SGNaviLocale?.label("SG Navi question and details")??"SG Navi question and details");
      close.setAttribute("aria-label",win.SGNaviLocale?.label("Close dialog")??"Close dialog");
    }
    localizeDialogLabels();
    doc.addEventListener("sgnavi:languagechange",()=>{
      localizeDialogLabels();
      if(!overlay.hidden)refreshOpenDraft?.();
    });
    const body=add("div",undefined,"task20-dialog-content");
    dialog.append(heading,body);overlay.appendChild(dialog);doc.body.appendChild(overlay);
    const result=add("section",undefined,"task15-flow task21-result");result.id="task21-result";result.hidden=true;host.appendChild(result);
    function reset(){
      serial++;if(controller)controller.abort();controller=null;pending=false;reply=null;checkedProcess.clear();
      refreshOpenDraft=null;
      result.hidden=true;result.replaceChildren();host.dataset.flowStage="input";
      win.SGNaviLocale?.syncCoverage?.();
    }
    function hideDialog(){
      overlay.hidden=true;doc.body.classList.remove("task20-modal-open");
      win.SGNaviLocale?.syncCoverage?.();
      if(lastFocus?.isConnected)lastFocus.focus();
    }
    function showDialog(){
      if(overlay.hidden)lastFocus=doc.activeElement;
      overlay.hidden=false;doc.body.classList.add("task20-modal-open");
      win.SGNaviLocale?.syncCoverage?.();
      close.focus();
    }
    doc.addEventListener("keydown",e=>{
      if(overlay.hidden)return;
      if(e.key==="Escape"){e.preventDefault();hideDialog();return;}
      if(e.key!=="Tab")return;
      const controls=[...dialog.querySelectorAll("button:not([disabled]),input:not([disabled]),select:not([disabled]),textarea:not([disabled]),a[href]")].filter(x=>x.getClientRects().length>0);
      if(!controls.length)return;
      if(e.shiftKey&&doc.activeElement===controls[0]){e.preventDefault();controls.at(-1).focus();}
      else if(!e.shiftKey&&doc.activeElement===controls.at(-1)){e.preventDefault();controls[0].focus();}
    });
    function message(text,isError=false){
      const validation=get("problem-validation");
      setText(validation,text);
      validation.setAttribute("role",isError?"alert":"status");
    }
    const call=async(operation,token,payload)=>{
      const config=win.SGNaviApiConfig;
      const path=config?.resolve("/api/action-plan",win.location);
      if(!path)throw Error("The checking service is not configured.");
      const reviewedPath=config.resolveReviewedActionPlan?.(win.location);
      const request={action_plan_version:"1.0",request_id:"req-"+win.crypto.randomUUID(),operation,...payload};
      controller=new AbortController();const signal=controller.signal;
      const timeout=setTimeout(()=>controller.abort(),25000);
      const post=(url,requestSignal=signal)=>win.fetch(url,{method:"POST",
        headers:{"Content-Type":"application/json",Accept:"application/json"},
        body:JSON.stringify(request),signal:requestSignal,credentials:"omit",cache:"no-store"});
      const json=res=>{
        if(!(res.headers.get("content-type")||"").toLowerCase().includes("application/json"))
          throw Error("Unexpected checking service response.");
        return res.json();
      };
      try{
        if(reviewedPath){
          try{
            const res=await post(reviewedPath,AbortSignal.any([signal,AbortSignal.timeout(8000)]));
            if(res.ok&&token===serial){
              const envelope=await json(res);
              const data=await verifyResponse(envelope?.canonical,request,win.crypto);
              const display=reviewedDisplay(envelope);
              return token===serial?{...data,reviewedDisplay:display,reviewedDisclaimer:display?envelope.disclaimer:null}:null;
            }
          }catch(_){/* A missing or unusable reviewed response can fall back to the English API. */}
          if(token!==serial)return null;
          if(signal.aborted)throw Error("The checking service could not complete this request.");
        }
        const res=await post(path);
        if(token!==serial)return null;
        if(!res.ok&&res.status!==503)throw Error("The checking service could not complete this request.");
        const data=await verifyResponse(await json(res),request,win.crypto);
        return token===serial?data:null;
      }finally{clearTimeout(timeout);if(token===serial)controller=null;}
    };
    async function interpret(){
      reset();summaryDisplay=null;stage="interpreting";description=input.value.trim();const token=serial;
      if(!description||description.length>1200){message("Describe the problem in 1 to 1,200 characters.",true);return;}
      // Only exact, built-in examples have English equivalents accepted by the API.
      description=win.SGNaviLocale?.canonicalExample?.(description)??description;
      if(/\p{Script=Han}/u.test(description)){
        message("Please write your own description in English, or use one of the examples above.",true);return;
      }
      message("Checking what happened…");get("problem-submit").disabled=true;
      try{
        const data=await call("interpret",token,{description});
        if(!data||token!==serial)return;
        message("");
        if(data.state==="CONFIRM"){context=data.context;rememberSummary(data);previousContexts=[];showConfirm();}
        else showLimited(data.message,data.state==="UNAVAILABLE",data);
      }catch(_){if(token===serial)showLimited("The service could not check your description. Please try again.",true);}
      finally{if(token===serial)get("problem-submit").disabled=false;}
    }
    function select(label,items,value,onChange){
      const wrap=fieldLabel(label);
      const sel=add("select");for(const item of items){
        const o=add("option",LABEL(item));o.value=item;if(item===value)o.selected=true;sel.appendChild(o);
      }
      sel.addEventListener("change",()=>onChange(sel.value));wrap.appendChild(sel);return wrap;
    }
    function showConfirm(){
      if(!context)return;
      refreshOpenDraft=null;
      body.replaceChildren();
      body.appendChild(add("p","Does this describe your situation?","task21-eyebrow"));
      body.appendChild(add("h2","Confirm the main details"));
      const summary=summaryDisplay?.english===context.summary?summaryDisplay:null;
      body.appendChild(add("p",context.summary,undefined,summary?.chinese??win.SGNaviLocale?.chineseSummary?.(context.summary)??null));
      appendReviewedNotice(body,summary?.disclaimer);
      const copy={...context,facts:{...context.facts}};
      body.appendChild(select("Topic",Object.keys(SUBTYPES),copy.case_type,value=>{
        copy.case_type=value;copy.issue_subtype="unspecified";copy.facts={};
        context=copy;showConfirm();
      }));
      body.appendChild(select("Type of concern",SUBTYPES[copy.case_type],copy.issue_subtype,value=>{copy.issue_subtype=value;}));
      body.appendChild(select("What you want help with",GOALS,copy.goal,value=>{copy.goal=value;}));

      // Corrections are optional and collapsed: do not impose a generic survey.
      // These exact Task16 typed facts can change a reviewed action profile.
      const corrections={
        consumer_complaint:[
          ["merchant_location","Where did the purchase happen?",[["singapore","Singapore"],["outside_singapore","Outside Singapore"],["unknown","Not sure"]]],
          ["purchase_purpose","Was it for personal use?",[["personal","Personal use"],["business","Business use"],["unknown","Not sure"]]],
          ["resolution_attempted","Have you asked the seller to resolve it?",[[true,"Yes"],[false,"No"],["unknown","Not sure"]]],
          ["consumer_context","Are you a local consumer or a visitor?",[["local_consumer","Local consumer"],["visitor","Visitor"],["unknown","Not sure"]]]
        ],
        rental_deposit:[
          ["dispute_with","Who is the dispute with?",[["landlord","Landlord"],["agent","Estate agent"],["unknown","Not sure"]]],
          ["premises_type","What type of premises?",[["private_residential","Private home or condo"],["hdb","HDB"],["commercial","Commercial"],["industrial","Industrial"],["unknown","Not sure"]]],
          ["lease_ended","Have you already left or ended the tenancy?",[[true,"Yes"],[false,"Not yet"],["unknown","Not sure"]]],
          ["break_clause_present","Does your signed agreement contain a break clause?",[[true,"Yes"],[false,"No"],["unknown","Not sure"]]]
        ]
      };
      const optional=add("details",undefined,"task21-fact-corrections");
      optional.appendChild(add("summary","Correct any important details (optional)"));
      for(const [field,prompt,items] of corrections[copy.case_type]){
        const row=fieldLabel(prompt),control=add("select");
        const empty=add("option","Not specified");empty.value="";control.appendChild(empty);
        for(const [value,text] of items){
          const option=add("option",text);option.value=JSON.stringify(value);
          if(Object.hasOwn(copy.facts,field)&&copy.facts[field]===value)option.selected=true;
          control.appendChild(option);
        }
        control.addEventListener("change",()=>{
          if(control.value==="")delete copy.facts[field];
          else copy.facts[field]=JSON.parse(control.value);
        });
        row.appendChild(control);optional.appendChild(row);
      }
      body.appendChild(optional);

      const actions=add("div",undefined,"task21-modal-actions");
      actions.append(btn("Edit description",()=>{hideDialog();input.focus();},"intake-secondary"));
      actions.append(btn("Confirm and continue →",()=>{
        context=copy;hideDialog();previousContexts=[];plan();
      },"intake-primary"));
      body.appendChild(actions);host.dataset.flowStage="review";showDialog();stage="confirm";
    }
    async function plan(){
      reset();stage="checking";host.dataset.flowStage="checking";const token=serial;
      message("Checking the next step…");get("problem-submit").disabled=true;
      try{
        const data=await call("plan",token,{confirmed:true,context});
        if(!data||token!==serial)return;
        message("");
        if(data.state==="ASK"){context=data.context;rememberSummary(data);showQuestion(data);}
        else if(data.state==="READY"){context=data.context;rememberSummary(data);reply=data;showResult(data);}
        else showLimited(data.message,data.state==="UNAVAILABLE",data);
      }catch(_){if(token===serial)showLimited("We could not check the next step. Your answers remain here; please retry.",true);}
      finally{if(token===serial)get("problem-submit").disabled=false;}
    }
    function showQuestion(data){
      const question=data.question,reviewed=data.reviewedDisplay?.question;
      refreshOpenDraft=null;
      if(!question||!context||Object.hasOwn(context.facts,question.field)){showLimited("We could not safely show the next question.",true);return;}
      stage="question";host.dataset.flowStage="questions";body.replaceChildren();
      body.appendChild(add("p","ONE QUICK DETAIL","task21-eyebrow"));
      body.appendChild(add("h2",question.prompt,undefined,productCopy(question.prompt,reviewed?.prompt)));
      body.appendChild(add("p",question.reason,undefined,productCopy(question.reason,reviewed?.reason)));
      appendReviewedNotice(body,data.reviewedDisclaimer);
      const choices=add("div",undefined,"task20-answers");
      let selected=null,hasSelection=false;
      for(const [index,option] of question.options.entries()){
        const optionBtn=btn(option.label,()=>{
          selected=option.value;hasSelection=true;
          for(const b of choices.children)b.setAttribute("aria-pressed",String(b===optionBtn));
        },"task20-answer",productCopy(option.label,reviewed?.options[index].label));
        optionBtn.setAttribute("aria-pressed","false");choices.appendChild(optionBtn);
      }
      body.appendChild(choices);
      const error=add("p","","problem-error");error.setAttribute("role","alert");body.appendChild(error);
      const actions=add("div",undefined,"task21-modal-actions");
      actions.append(btn("Back",()=>{
        if(previousContexts.length)context=previousContexts.pop();
        showConfirm();
      }));
      actions.append(btn("Continue →",()=>{
        if(!hasSelection){
          setText(error,"Choose an option, including Not sure.");return;
        }
        previousContexts.push(context);
        context={...context,facts:{...context.facts,[question.field]:selected}};
        hideDialog();plan();
      },"intake-primary"));
      body.appendChild(actions);showDialog();
    }
    function showLimited(text,unavailable=false,data){
      reset();stage="limited";result.hidden=false;host.dataset.flowStage="limited";
      message("");get("problem-submit").disabled=false;
      result.appendChild(add("h3",unavailable?"Service temporarily unavailable":"More information is needed"));
      result.appendChild(add("p",text,undefined,data?productCopy(text,data.reviewedDisplay?.message):undefined));
      appendReviewedNotice(result,data?.reviewedDisclaimer);
      result.appendChild(btn("Check again",()=>{if(context)plan();else interpret();},"intake-primary"));
      result.appendChild(btn("Edit description",()=>{result.hidden=true;win.SGNaviLocale?.syncCoverage?.();input.focus();}));
      win.SGNaviLocale?.syncCoverage?.();
    }
    function showResult(data){
      result.replaceChildren();result.hidden=false;stage="ready";host.dataset.flowStage="results";
      const p=data.plan,sources=data.verifiedSources,contacts=data.verifiedContacts;
      const reviewed=data.reviewedDisplay?.plan;
      const claimText=new Map();
      if(reviewed)for(const item of [...reviewed.checklist,...reviewed.details.flatMap(group=>group.items)])
        claimText.set(item.id,item.text);
      // A process is only the source-backed current action and Task19 checklist,
      // NOT an invented official end-to-end complaint or application status.
      let firstAction=null,activeDetail=null;
      const draftEdits=new Map();
      let manualDraft=null;
      function continueToAction(){
        hideDialog();
        if(firstAction){firstAction.classList.add("task23-current-action");firstAction.focus();}
        else title.focus();
      }
      function statusCount(){
        return checkedProcess.size+" / "+p.checklist.length;
      }
      const title=add("h3",p.headline,undefined,reviewed?.headline??null);title.id="task21-result-heading";result.appendChild(title);
      result.appendChild(add("p",p.assessment.text,"task20-situation",reviewed?.assessment.text??null));
      result.appendChild(add("p","An official help or preparation option is available; this does not decide legal eligibility or guarantee a result.","task15-notice"));
      appendReviewedNotice(result,data.reviewedDisclaimer);
      const two=add("div",undefined,"task20-first-grid"),left=add("div",undefined,"task20-first-left"),right=add("aside",undefined,"task20-first-right");
      const primary=add("section",undefined,"task20-primary");primary.appendChild(add("span","YOUR NEXT STEP","task20-label"));
      primary.appendChild(add("h4",p.primary_action.text,undefined,reviewed?.primary_action.text??null));
      const selected=p.primary_action.contact_id?contacts.get(p.primary_action.contact_id):null;
      if(selected){
        const link=add("a",p.primary_action.label+" ↗","intake-primary task21-link",reviewed?reviewed.primary_action.label+" ↗":null);
        link.href=selected.href;
        if(selected.external){link.target="_blank";link.rel="noopener noreferrer";}
        primary.appendChild(link);firstAction=link;
      }else{
        const actionButton=btn(p.primary_action.label,()=>showDetails("preparation"),"intake-primary",reviewed?.primary_action.label??null);
        primary.appendChild(actionButton);firstAction=actionButton;
      }
      left.appendChild(primary);
      const prep=add("section",undefined,"task20-checklist");prep.appendChild(add("h4","Before you continue"));
      const steps=add("ol");
      for(const item of p.checklist)steps.appendChild(add("li",item.text,undefined,claimText.get(item.id)??null));
      prep.appendChild(steps);left.appendChild(prep);
      right.appendChild(add("h4","Get help with the next part"));
      right.appendChild(btn("View available steps",()=>showDetails("process"),"task20-secondary-option task23-process-trigger"));
      for(const [label,part] of [["Official contacts","contacts"],["Write a request","draft"],
        ["Documents to prepare","documents"],["What to watch out for","pitfalls"],
        ["If it isn't resolved","alternatives"],["Why this advice?","evidence"]]){
        if(part==="draft"&&!p.draft||["documents","pitfalls","alternatives"].includes(part)&&!p.details.some(x=>x.kind===part))continue;
        right.appendChild(btn(label,()=>showDetails(part),"task20-secondary-option"));
      }
      two.append(left,right);result.appendChild(two);
      const basis=p.legal_basis.map(row=>sources.get(row.evidence_id)).filter(Boolean);
      if(basis.length){
        const legal=add("section",undefined,"task21-legal");
        legal.appendChild(add("strong","Relevant legal wording"));
        const e=basis[0];legal.appendChild(add("blockquote",e.quote));
        legal.appendChild(officialText("p",e.title+(e.provision?" · "+e.provision:"")));
        legal.appendChild(btn("Read wording and context",()=>showDetails("evidence")));
        result.appendChild(legal);
      }
      const controls=add("div",undefined,"task21-bottom-actions");
      controls.append(btn("Edit situation",()=>{reset();showConfirm();}));
      controls.append(btn("Check again",()=>plan()));
      result.appendChild(controls);
      win.SGNaviLocale?.syncCoverage?.();
      function showDetails(part,requestedEvidenceIds=null){
        activeDetail=part;
        refreshOpenDraft=null;
        body.replaceChildren();
        body.appendChild(add("h2",({
          contacts:"Official ways to get help",draft:"Write a request",documents:"What to prepare",
          pitfalls:"What to watch out for",alternatives:"If it isn't resolved",
          evidence:"Verified wording and sources",preparation:"Your preparation steps",process:"View available steps"
        })[part]||"More information",undefined,reviewed?.details.find(group=>group.kind===part)?.title));
        if(part!=="evidence")appendReviewedNotice(body,data.reviewedDisclaimer);
        if(part==="process"){
          const processSection=add("section",undefined,"task23-process");
          const progress=add("p",undefined,"task23-progress"),count=add("span");
          count.textContent=statusCount();
          progress.append(count,add("span"," personal preparation steps checked"));
          progress.setAttribute("role","status");processSection.appendChild(progress);
          const list=add("ol");
          const now=add("li",undefined,"task23-step");now.dataset.current="true";
          const current=add("strong");current.append(add("span","Now: "),add("span",p.primary_action.text,undefined,reviewed?.primary_action.text??null));
          now.appendChild(current);
          now.appendChild(add("small","This is the current suggested action, not a completed official step."));
          now.appendChild(btn("View supporting sources",()=>showDetails("evidence",p.primary_action.evidence_ids),"task23-step-source"));
          list.appendChild(now);
          for(let index=0;index<p.checklist.length;index++){
            const item=p.checklist[index],li=add("li",undefined,"task23-step");
            const label=add("label"),tick=doc.createElement("input");tick.type="checkbox";
            tick.checked=checkedProcess.has(item.id);
            tick.addEventListener("change",()=>{
              if(tick.checked)checkedProcess.add(item.id);else checkedProcess.delete(item.id);
              count.textContent=statusCount();
              for(const row of list.querySelectorAll("[data-current]"))row.dataset.current="false";
              const next=list.querySelector('input[type="checkbox"]:not(:checked)');
              if(next)next.closest(".task23-step").dataset.current="true";
              else now.dataset.current="true";
            });
            label.append(tick,add("span",item.text,undefined,claimText.get(item.id)??null));
            li.appendChild(label);
            li.appendChild(btn("View supporting sources",()=>showDetails("evidence",item.evidence_ids),"task23-step-source"));
            li.dataset.current=index===0?"true":"false";
            if(tick.checked)li.dataset.current="false";
            list.appendChild(li);
          }
          processSection.appendChild(list);
          processSection.appendChild(add("p","Further steps depend on your case.","task23-limit"));
          processSection.appendChild(add("p","Personal checklist only — not a filed case or official status.","task23-limit"));
          body.appendChild(processSection);
        }else if(part==="contacts"){
          if(!contacts.size)body.appendChild(add("p","No currently verified contact is available for this route."));
          for(const c of contacts.values()){
            const translated=reviewed?.contacts.find(row=>row.id===c.id);
            const row=add("div",undefined,"task21-contact");
            row.appendChild(add("strong",c.institution,undefined,translated?.institution??null));
            row.appendChild(add("p",LABEL(c.purpose)+(c.note?" · "+c.note:""),undefined,
              translated?translated.purpose+(translated.note?" · "+translated.note:""):null));
            const link=add("a",undefined,"task21-link");
            if(c.kind==="web")setText(link,"Open official website ↗");
            else link.append(add("span",c.kind==="phone"?"Call":"Email"),doc.createTextNode(" "+c.value));
            link.href=c.href;if(c.external){link.target="_blank";link.rel="noopener noreferrer";}
            row.appendChild(link);body.appendChild(row);
          }
        }else if(part==="draft"&&p.draft){
          body.appendChild(add("p","Edit this draft before copying. Nothing will be sent automatically."));
          body.appendChild(add("h3",p.draft.title,undefined,reviewed?.draft?.title??null));
          const editors=new Map();
          for(const [index,slot] of p.draft.slots.entries()){
            const label=fieldLabel(slot.label,reviewed?.draft?.slots[index].label??null),field=add("input");
            field.type="text";field.maxLength=140;
            field.value=draftEdits.get(slot.id)||"";
            field.addEventListener("input",()=>draftEdits.set(slot.id,field.value));
            label.appendChild(field);editors.set(slot.id,field);body.appendChild(label);
          }
          const preview=add("textarea",undefined,"task21-draft");preview.rows=9;
          const refresh=()=>{
            const chinese=win.SGNaviLocale?.getLanguage()==="zh"&&reviewed?.draft;
            const template=chinese||p.draft;
            let text=template.subject+"\n\n"+template.body;
            for(const [index,[id,field]] of [...editors].entries()){
              field.placeholder=win.SGNaviLocale?.label("Add your own confirmed details")??"Add your own confirmed details";
              const empty=chinese?"["+template.slots[index].label+"：待填写]":"["+id+": to fill in]";
              text=text.split("{"+id+"}").join(field.value.trim()||empty);
            }
            preview.value=manualDraft?.text??text;
            preview.lang=manualDraft?.lang??(chinese?"zh-Hans":"en");
          };
          preview.addEventListener("input",()=>{manualDraft={text:preview.value,lang:preview.lang};});
          editors.forEach(field=>field.addEventListener("input",()=>{manualDraft=null;refresh();}));
          refreshOpenDraft=refresh;refresh();
          body.appendChild(preview);
          const copy=btn("Copy draft",async()=>{
            try{await win.navigator.clipboard.writeText(preview.value);setText(copy,"Copied — review before sending");}
            catch(_){setText(copy,"Select the draft text to copy");preview.select();}
          },"intake-primary");body.appendChild(copy);
        }else if(part==="evidence"){
          for(const e of sources.values()){
            if(requestedEvidenceIds && !requestedEvidenceIds.includes(e.id))continue;
            const article=add("article",undefined,"task21-evidence");article.appendChild(officialText("strong",e.publisher+" · "+e.title));
            article.appendChild(add("p",e.kind==="statute"?"Statutory excerpt":e.kind==="contract_template"?"Model contract wording (not a law)":"Official procedural information"));
            article.appendChild(add("p","Original official English source (not translated)","task23-unofficial"));
            article.appendChild(add("blockquote",e.quote));
            const review=add("p");
            if(e.provision)review.appendChild(officialText("span",e.provision+" · "));
            review.append(add("span","Reviewed"),doc.createTextNode(" "+e.reviewed_at));
            article.appendChild(review);
            const link=add("a","Read full original ↗","task21-link");link.href=safeURL(e.url,true);
            link.target="_blank";link.rel="noopener noreferrer";article.appendChild(link);
            body.appendChild(article);
          }
        }else{
          const items=part==="preparation"?p.checklist:p.details.filter(x=>x.kind===part).flatMap(x=>x.items);
          const list=add("ul");for(const c of items||[])list.appendChild(add("li",c.text,undefined,claimText.get(c.id)??null));
          body.appendChild(list);
          body.appendChild(btn("View supporting sources",()=>showDetails("evidence")));
        }
        const buttons=add("div",undefined,"task21-modal-actions");
        buttons.appendChild(btn("Continue to next step",continueToAction,"intake-primary"));
        if(part==="evidence")buttons.appendChild(btn("View available steps",()=>showDetails("process"),"intake-secondary"));
        else if(part==="preparation")buttons.appendChild(btn("View supporting sources",()=>showDetails("evidence"),"intake-secondary"));
        body.appendChild(buttons);
        showDialog();
      }
      title.tabIndex=-1;title.focus();
    }
    form.addEventListener("submit",e=>{e.preventDefault();interpret();});
    input.addEventListener("input",()=>{
      reset();context=null;summaryDisplay=null;get("problem-count").textContent=input.value.length+" / 1,200";
      get("problem-submit").disabled=false;message("");
    });
    for(const b of doc.querySelectorAll("[data-example-question]"))b.addEventListener("click",()=>{
      const example=b.getAttribute("data-example-question");
      input.value=win.SGNaviLocale?.exampleLabel?.(example)??example;
      input.dispatchEvent(new Event("input",{bubbles:true}));input.focus();
    });
    host.dataset.task21Ready="true";get("problem-submit").disabled=false;
    return Object.freeze({interpret,reset});
  }
  return Object.freeze({init,safeURL,safeContact,verifyResponse,reviewedDisplay,revisionOf,canonical});
});
