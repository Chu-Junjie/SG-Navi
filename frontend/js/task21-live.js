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
  function init(doc,win){
    const get=id=>doc.getElementById(id),host=get("problem-intake"),form=get("problem-form"),input=get("problem-text");
    if(!host||!form||!input)return null;
    const add=(tag,content,cls)=>{
      const el=doc.createElement(tag);if(content!==undefined)el.textContent=String(content);
      if(cls)el.className=cls;return el;
    };
    const btn=(label,fn,cls="intake-secondary")=>{
      const b=add("button",label,cls);b.type="button";b.addEventListener("click",fn);return b;
    };
    let serial=0,controller=null,context=null,description="",stage="input",lastFocus=null,pending=false;
    let previousContexts=[],reply=null;
    const overlay=add("div",undefined,"task20-overlay");overlay.hidden=true;overlay.id="task21-overlay";
    const dialog=add("section",undefined,"task20-dialog");dialog.setAttribute("role","dialog");dialog.setAttribute("aria-modal","true");
    dialog.setAttribute("aria-label","SG Navi question and details");
    const heading=add("div",undefined,"task20-dialog-head");
    heading.appendChild(add("strong","SG Navi"));
    const close=btn("×",()=>hideDialog(),"task20-close");close.setAttribute("aria-label","Close dialog");heading.appendChild(close);
    const body=add("div",undefined,"task20-dialog-content");
    dialog.append(heading,body);overlay.appendChild(dialog);doc.body.appendChild(overlay);
    const result=add("section",undefined,"task15-flow task21-result");result.id="task21-result";result.hidden=true;host.appendChild(result);
    function reset(){
      serial++;if(controller)controller.abort();controller=null;pending=false;reply=null;
      result.hidden=true;result.replaceChildren();host.dataset.flowStage="input";
    }
    function hideDialog(){
      overlay.hidden=true;doc.body.classList.remove("task20-modal-open");
      if(lastFocus?.isConnected)lastFocus.focus();
    }
    function showDialog(){
      if(overlay.hidden)lastFocus=doc.activeElement;
      overlay.hidden=false;doc.body.classList.add("task20-modal-open");
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
      get("problem-validation").textContent=text;
      get("problem-validation").setAttribute("role",isError?"alert":"status");
    }
    const call=async(operation,token,payload)=>{
      const path=win.SGNaviApiConfig?.resolve("/api/action-plan",win.location);
      if(!path)throw Error("The checking service is not configured.");
      const request={action_plan_version:"1.0",request_id:"req-"+win.crypto.randomUUID(),operation,...payload};
      controller=new AbortController();const timeout=setTimeout(()=>controller.abort(),25000);
      try{
        const res=await win.fetch(path,{method:"POST",headers:{"Content-Type":"application/json",Accept:"application/json"},
          body:JSON.stringify(request),signal:controller.signal,credentials:"omit",cache:"no-store"});
        if(token!==serial)return null;
        if(!res.ok&&res.status!==503)throw Error("The checking service could not complete this request.");
        if(!(res.headers.get("content-type")||"").toLowerCase().includes("application/json"))
          throw Error("Unexpected checking service response.");
        const data=await verifyResponse(await res.json(),request,win.crypto);
        return token===serial?data:null;
      }finally{clearTimeout(timeout);if(token===serial)controller=null;}
    };
    async function interpret(){
      reset();stage="interpreting";description=input.value.trim();const token=serial;
      if(!description||description.length>1200){message("Describe the problem in 1 to 1,200 characters.",true);return;}
      message("Checking what happened…");get("problem-submit").disabled=true;
      try{
        const data=await call("interpret",token,{description});
        if(!data||token!==serial)return;
        message("");
        if(data.state==="CONFIRM"){context=data.context;previousContexts=[];showConfirm();}
        else showLimited(data.message,data.state==="UNAVAILABLE");
      }catch(_){if(token===serial)showLimited("The service could not check your description. Please try again.",true);}
      finally{if(token===serial)get("problem-submit").disabled=false;}
    }
    function select(label,items,value,onChange){
      const wrap=add("label",label,"task21-field");
      const sel=add("select");for(const item of items){
        const o=add("option",LABEL(item));o.value=item;if(item===value)o.selected=true;sel.appendChild(o);
      }
      sel.addEventListener("change",()=>onChange(sel.value));wrap.appendChild(sel);return wrap;
    }
    function showConfirm(){
      if(!context)return;
      body.replaceChildren();
      body.appendChild(add("p","Does this describe your situation?","task21-eyebrow"));
      body.appendChild(add("h2","Confirm the main details"));
      body.appendChild(add("p",context.summary));
      const copy={...context,facts:{...context.facts}};
      body.appendChild(select("Topic",Object.keys(SUBTYPES),copy.case_type,value=>{
        copy.case_type=value;copy.issue_subtype="unspecified";copy.facts={};
        context=copy;showConfirm();
      }));
      body.appendChild(select("Type of concern",SUBTYPES[copy.case_type],copy.issue_subtype,value=>{copy.issue_subtype=value;}));
      body.appendChild(select("What you want help with",GOALS,copy.goal,value=>{copy.goal=value;}));
      const actions=add("div",undefined,"task21-modal-actions");
      actions.append(btn("Edit description",()=>{hideDialog();input.focus();},"intake-secondary"));
      actions.append(btn("Confirm and continue →",()=>{
        context=copy;hideDialog();previousContexts=[];plan();
      },"intake-primary"));
      body.appendChild(actions);showDialog();stage="confirm";
    }
    async function plan(){
      reset();stage="checking";const token=serial;
      message("Checking the next step…");get("problem-submit").disabled=true;
      try{
        const data=await call("plan",token,{confirmed:true,context});
        if(!data||token!==serial)return;
        message("");
        if(data.state==="ASK"){context=data.context;showQuestion(data.question);}
        else if(data.state==="READY"){context=data.context;reply=data;showResult(data);}
        else showLimited(data.message,data.state==="UNAVAILABLE");
      }catch(_){if(token===serial)showLimited("We could not check the next step. Your answers remain here; please retry.",true);}
      finally{if(token===serial)get("problem-submit").disabled=false;}
    }
    function showQuestion(question){
      if(!question||!context||Object.hasOwn(context.facts,question.field)){showLimited("We could not safely show the next question.",true);return;}
      stage="question";body.replaceChildren();
      body.appendChild(add("p","ONE QUICK DETAIL","task21-eyebrow"));
      body.appendChild(add("h2",question.prompt));
      body.appendChild(add("p",question.reason));
      const choices=add("div",undefined,"task20-answers");
      let selected=null;
      for(const option of question.options){
        const optionBtn=btn(option.label,()=>{
          selected=option.value;
          for(const b of choices.children)b.setAttribute("aria-pressed",String(b===optionBtn));
        },"task20-answer");
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
        if(selected===null&&question.options.some(x=>x.value===null)===false){
          error.textContent="Choose an option, including Not sure.";return;
        }
        previousContexts.push(context);
        context={...context,facts:{...context.facts,[question.field]:selected}};
        hideDialog();plan();
      },"intake-primary"));
      body.appendChild(actions);showDialog();
    }
    function showLimited(text,unavailable=false){
      reset();stage="limited";result.hidden=false;host.dataset.flowStage="limited";
      result.appendChild(add("h3",unavailable?"Service temporarily unavailable":"More information is needed"));
      result.appendChild(add("p",text));
      result.appendChild(btn("Check again",()=>{if(context)plan();else interpret();},"intake-primary"));
      result.appendChild(btn("Edit description",()=>{result.hidden=true;input.focus();}));
    }
    function showResult(data){
      result.replaceChildren();result.hidden=false;stage="ready";host.dataset.flowStage="results";
      const p=data.plan,sources=data.verifiedSources,contacts=data.verifiedContacts;
      const title=add("h3",p.headline);title.id="task21-result-heading";result.appendChild(title);
      result.appendChild(add("p",p.assessment.text,"task20-situation"));
      result.appendChild(add("p","An official help or preparation option is available; this does not decide legal eligibility or guarantee a result.","task15-notice"));
      const two=add("div",undefined,"task20-first-grid"),left=add("div",undefined,"task20-first-left"),right=add("aside",undefined,"task20-first-right");
      const primary=add("section",undefined,"task20-primary");primary.appendChild(add("span","YOUR NEXT STEP","task20-label"));
      primary.appendChild(add("h4",p.primary_action.text));
      const selected=p.primary_action.contact_id?contacts.get(p.primary_action.contact_id):null;
      if(selected){
        const link=add("a",p.primary_action.label+" ↗","intake-primary task21-link");
        link.href=selected.href;
        if(selected.external){link.target="_blank";link.rel="noopener noreferrer";}
        primary.appendChild(link);
      }else primary.appendChild(btn(p.primary_action.label,()=>showDetails("preparation"),"intake-primary"));
      left.appendChild(primary);
      const prep=add("section",undefined,"task20-checklist");prep.appendChild(add("h4","Before you continue"));
      const steps=add("ol");
      for(const item of p.checklist)steps.appendChild(add("li",item.text));
      prep.appendChild(steps);left.appendChild(prep);
      right.appendChild(add("h4","Get help with the next part"));
      for(const [label,part] of [["Official contacts","contacts"],["Write a request","draft"],
        ["Documents to prepare","documents"],["What to watch out for","pitfalls"],
        ["If it isn't resolved","alternatives"],["Why this advice?","evidence"]]){
        if(part==="draft"&&!p.draft||["documents","pitfalls","alternatives"].includes(part)&&!p.details.some(x=>x.kind===part))continue;
        right.appendChild(btn(label+"  ›",()=>showDetails(part),"task20-secondary-option"));
      }
      two.append(left,right);result.appendChild(two);
      const basis=p.legal_basis.map(row=>sources.get(row.evidence_id)).filter(Boolean);
      if(basis.length){
        const legal=add("section",undefined,"task21-legal");
        legal.appendChild(add("strong","Relevant legal wording"));
        const e=basis[0];legal.appendChild(add("blockquote",e.quote));
        legal.appendChild(add("p",e.title+(e.provision?" · "+e.provision:"")));
        legal.appendChild(btn("Read wording and context",()=>showDetails("evidence")));
        result.appendChild(legal);
      }
      const controls=add("div",undefined,"task21-bottom-actions");
      controls.append(btn("Edit situation",()=>{reset();showConfirm();}));
      controls.append(btn("Check again",()=>plan()));
      result.appendChild(controls);
      function showDetails(part){
        body.replaceChildren();
        body.appendChild(add("h2",({
          contacts:"Official ways to get help",draft:"Write a request",documents:"What to prepare",
          pitfalls:"What to watch out for",alternatives:"If it isn't resolved",
          evidence:"Verified wording and sources",preparation:"Your preparation steps"
        })[part]||"More information"));
        if(part==="contacts"){
          if(!contacts.size)body.appendChild(add("p","No currently verified contact is available for this route."));
          for(const c of contacts.values()){
            const row=add("div",undefined,"task21-contact");row.appendChild(add("strong",c.institution));
            row.appendChild(add("p",LABEL(c.purpose)+(c.note?" · "+c.note:"")));
            const link=add("a",c.kind==="phone"?"Call "+c.value:c.kind==="email"?"Email "+c.value:"Open official website ↗","task21-link");
            link.href=c.href;if(c.external){link.target="_blank";link.rel="noopener noreferrer";}
            row.appendChild(link);body.appendChild(row);
          }
        }else if(part==="draft"&&p.draft){
          body.appendChild(add("p","Edit this draft before copying. Nothing will be sent automatically."));
          body.appendChild(add("h3",p.draft.title));
          const editors=new Map();
          for(const slot of p.draft.slots){
            const label=add("label",slot.label,"task21-field"),field=add("input");
            field.type="text";field.maxLength=140;field.placeholder="Add your own confirmed details";
            label.appendChild(field);editors.set(slot.id,field);body.appendChild(label);
          }
          const preview=add("textarea",undefined,"task21-draft");preview.rows=9;preview.value=p.draft.subject+"\n\n"+p.draft.body;
          const refresh=()=>{let src=p.draft.subject+"\n\n"+p.draft.body;for(const [id,field] of editors)src=src.split("{"+id+"}").join(field.value.trim()||"["+id+": to fill in]");
            preview.value=src;};
          editors.forEach(x=>x.addEventListener("input",refresh));refresh();
          body.appendChild(preview);
          const copy=btn("Copy draft",async()=>{
            try{await win.navigator.clipboard.writeText(preview.value);copy.textContent="Copied — review before sending";}
            catch(_){copy.textContent="Select the draft text to copy";preview.select();}
          },"intake-primary");body.appendChild(copy);
        }else if(part==="evidence"){
          for(const e of sources.values()){
            const article=add("article",undefined,"task21-evidence");article.appendChild(add("strong",e.publisher+" · "+e.title));
            article.appendChild(add("p",e.kind==="statute"?"Statutory excerpt":e.kind==="contract_template"?"Model contract wording (not a law)":"Official procedural information"));
            article.appendChild(add("blockquote",e.quote));
            article.appendChild(add("p",(e.provision?e.provision+" · ":"")+"Reviewed "+e.reviewed_at));
            const link=add("a","Read full original ↗","task21-link");link.href=safeURL(e.url,true);
            link.target="_blank";link.rel="noopener noreferrer";article.appendChild(link);
            body.appendChild(article);
          }
        }else{
          const items=part==="preparation"?p.checklist:p.details.filter(x=>x.kind===part).flatMap(x=>x.items);
          const list=add("ul");for(const c of items||[])list.appendChild(add("li",c.text));
          body.appendChild(list);
          body.appendChild(btn("View supporting sources",()=>showDetails("evidence")));
        }
        body.appendChild(btn("Back to next step",hideDialog,"intake-secondary"));
        showDialog();
      }
      title.tabIndex=-1;title.focus();
    }
    form.addEventListener("submit",e=>{e.preventDefault();interpret();});
    input.addEventListener("input",()=>{
      reset();context=null;get("problem-count").textContent=input.value.length+" / 1,200";
      get("problem-submit").disabled=false;message("");
    });
    for(const b of doc.querySelectorAll("[data-example-question]"))b.addEventListener("click",()=>{
      input.value=b.getAttribute("data-example-question");input.dispatchEvent(new Event("input",{bubbles:true}));input.focus();
    });
    host.dataset.task21Ready="true";get("problem-submit").disabled=false;
    return Object.freeze({interpret,reset});
  }
  return Object.freeze({init,safeURL,safeContact,verifyResponse,revisionOf,canonical});
});