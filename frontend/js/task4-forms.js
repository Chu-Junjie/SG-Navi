"use strict";
/* Task 4 — rendering only. No legal rules, routing thresholds or official channel constants. */
const CASE_TYPES={rental_deposit:"Rental Deposit",consumer_complaint:"Consumer Complaint"};
const MOCK_FILES={NEED_CLARIFICATION:"need_clarification",SUPPORTED_PATH:"supported_path",REFER_TO_OFFICIAL:"refer_to_official",ERROR:"error"};
const SEVEN=["case_summary","potential_channels","conditions","steps","document_checklist","unresolved_questions","citations"];
const byId=id=>document.getElementById(id);
const put=(parent,tag,value)=>{const e=document.createElement(tag);e.textContent=String(value);parent.append(e);return e;};
const reset=node=>node.replaceChildren();
const json=async path=>{const response=await fetch(path,{cache:"no-store"});if(!response.ok)throw Error("HTTP "+response.status);return response.json();};
let schemas={},labels,cardSchema,answers={rental_deposit:{},consumer_complaint:{}},revision=0;
function kind(schema) {
  const variants=schema.anyOf||[schema];
  if(variants.some(x=>x.type==="boolean"))return "boolean";
  if(variants.some(x=>x.type==="number"))return "number";
  if(variants.some(x=>x.format==="date"))return "date";
  return "string";
}
function parseInput(raw,definition) {
  if(raw==="__unknown__")return {value:"unknown"};
  if(raw==="__null__"||raw==="")return {value:null};
  const type=kind(definition);
  if(type==="boolean")return {value:raw==="true"};
  if(type==="number"){
    const n=Number(raw);
    if(!Number.isFinite(n))return {error:"Enter a valid number or choose Unknown."};
    const lower=(definition.anyOf||[]).find(s=>s.type==="number")?.minimum;
    if(lower!==undefined&&n<lower)return {error:"This value cannot be negative."};
    return {value:n};
  }
  if(type==="date"&&!/^\d{4}-\d{2}-\d{2}$/.test(raw))return {error:"Enter a valid date."};
  if(type==="date"){
    const d=new Date(raw+"T00:00:00Z");
    if(!Number.isFinite(d.getTime())||d.toISOString().slice(0,10)!==raw)return {error:"Enter a valid calendar date."};
  }
  return {value:raw};
}
function controlFor(field,def,current) {
  const container=document.createElement("div");container.className="field";
  const label=put(container,"label",labels[byId("case-type").value]?.[field]||field);
  const id="answer-"+field;label.htmlFor=id;
  const select=document.createElement("select");select.id=id;select.name=field;select.dataset.field=field;
  const type=kind(def);
  const choices=[["__null__","Not provided"],["__unknown__","Unknown / not sure"]];
  if(type==="boolean")choices.push(["true","Yes"],["false","No"]);
  for(const [value,title] of choices){const option=document.createElement("option");option.value=value;option.textContent=title;select.append(option);}
  const currentKnown=current!==undefined&&current!==null&&current!=="unknown";
  let details=null;
  if(type!=="boolean"){
    const item=document.createElement("option");item.value="__value__";item.textContent="Enter a value";select.append(item);
    details=document.createElement("input");details.dataset.valueField=field;
    details.type=type==="date"?"date":type==="number"?"number":"text";
    if(type==="number"){details.min="0";details.step="any";}
    details.placeholder=type==="number"?"Enter a non-negative number":"Enter a value";
    details.value=currentKnown?String(current):"";
    details.hidden=!currentKnown;
    details.disabled=!currentKnown;
  }
  select.value=current===undefined||current===null?"__null__":current==="unknown"?"__unknown__":type==="boolean"?String(current):"__value__";
  select.addEventListener("change",()=>{
    if(details){details.hidden=select.value!=="__value__";details.disabled=select.value!=="__value__";}
    collect(false);
  });
  if(details)details.addEventListener("input",()=>collect(false));
  container.append(select);
  if(details)container.append(details);
  const err=put(container,"span","");err.className="field-error";err.dataset.errorFor=field;
  return container;
}
function renderFields(){
  const caseType=byId("case-type").value,root=byId("dynamic-fields");reset(root);
  const properties=schemas[caseType].properties;
  for(const [key,definition] of Object.entries(properties))root.append(controlFor(key,definition,answers[caseType][key]));
}
function collect(showErrors=true){
  const caseType=byId("case-type").value,properties=schemas[caseType].properties,next={},issues=[];
  for(const [field,def] of Object.entries(properties)){
    const select=byId("answer-"+field),detail=document.querySelector('[data-value-field="'+field+'"]');
    const raw=select.value==="__value__"?detail?.value??"":select.value;
    let result;
    if(select.value==="__value__"&&raw==="")result={error:"Enter a value, or select Not provided / Unknown."};
    else result=parseInput(raw,def);
    const errorNode=document.querySelector('[data-error-for="'+field+'"]');
    const error=result.error||"";
    if(error&&showErrors)issues.push(field+": "+error);
    errorNode.textContent=showErrors?error:"";
    if(error)next[field]=answers[caseType][field]??null;
    else next[field]=result.value;
  }
  answers[caseType]=next;
  byId("validation").textContent=issues.length?issues.length+" field(s) need attention.":"";
  return issues.length===0;
}
function warn(message){byId("verification").textContent=message;}
function evidenceOK(data){
  if(data?.status!=="SUPPORTED_PATH"||!data.action_card||!Array.isArray(data.evidence)||
     !Array.isArray(data.action_card.citations)||!data.action_card.citations.length||
     typeof data.source_version!=="string"||data.source_version.startsWith("mock"))return null;
  const map=new Map();
  for(const e of data.evidence){
    if(e?.review_status!=="verified"||e.source_version!==data.source_version)continue;
    try{const url=new URL(e.url);if(!["https:","http:"].includes(url.protocol)||url.hostname.endsWith(".invalid")||url.username||url.password)continue;
      map.set(e.evidence_id,{...e,url:url.href});}catch(_){}
  }
  const found=data.action_card.citations.map(id=>map.get(id));
  return found.every(Boolean)?found:null;
}
function showResponse(response){
  const root=byId("card"),questions=byId("questions"),warnings=byId("warnings");
  [root,questions,warnings].forEach(reset);
  const status=Object.hasOwn(MOCK_FILES,response?.status)?response.status:"ERROR";
  byId("status").textContent=status;
  const sources=evidenceOK(response);
  warn(sources?"Evidence metadata returned; verify independently before relying on it.":"Needs verification — no usable verified evidence was supplied.");
  if(status==="NEED_CLARIFICATION"&&Array.isArray(response.questions)){
    put(questions,"h3","Questions from response");
    response.questions.forEach(q=>{if(typeof q?.label==="string")put(questions,"p",q.label);});
  }
  if(Array.isArray(response?.warnings)&&response.warnings.length){
    put(warnings,"h3","Warnings");response.warnings.forEach(w=>{if(typeof w==="string")put(warnings,"p",w);});
  }
  for(const key of SEVEN){
    const region=document.createElement("section");region.className="card-section";
    put(region,"h3",labels.action_card[key]||key);
    const value=response?.action_card?.[key];
    const sensitive=["case_summary","potential_channels","conditions","steps","document_checklist","citations"].includes(key);
    if(sensitive&&!sources){put(region,"p","Needs verification — evidence unavailable.");}
    else if(value===undefined||value===null||value===""||(Array.isArray(value)&&!value.length))put(region,"p","Not provided.");
    else if(key==="citations"){
      const ul=document.createElement("ul");
      sources.forEach(e=>{const li=document.createElement("li"),a=document.createElement("a");a.href=e.url;a.target="_blank";a.rel="noopener noreferrer";a.textContent=e.source_id+" ("+e.evidence_id+")";li.append(a);ul.append(li);});
      region.append(ul);
    } else if(Array.isArray(value)){
      const ul=document.createElement("ul");value.filter(x=>typeof x==="string").forEach(v=>put(ul,"li",v));region.append(ul);
    }else if(typeof value==="string")put(region,"p",value);
    else put(region,"p","Unsupported response content.");
    root.append(region);
  }
}
async function mockNavigate(request,status){
  // Transport mock: return the existing, contract-valid JSON fixture; do not infer status from answers.
  if(!Object.hasOwn(CASE_TYPES,request.case_type)||request.api_version!=="1.0")throw Error("Invalid request envelope");
  return json("./mocks/"+MOCK_FILES[status]+"_response.json");
}
async function submit(){
  if(!collect(true)){byId("status").textContent="INPUT ERROR";warn("Correct the highlighted fields before requesting a result.");return;}
  const caseType=byId("case-type").value,request={api_version:"1.0",case_type:caseType,answers:{...answers[caseType]}};
  const attempt=++revision;
  byId("status").textContent="LOADING";
  byId("submit").disabled=true;
  try{
    const response=await mockNavigate(request,byId("mock-status").value);
    if(attempt!==revision)return;
    if(response?.api_version!=="1.0"||!Object.hasOwn(MOCK_FILES,response.status))throw Error("Bad response");
    showResponse(response);
    byId("request-preview").textContent=JSON.stringify(request,null,2);
  }catch(_){if(attempt===revision){showResponse({status:"ERROR",warnings:["Mock API response unavailable or invalid."]});}}
  finally{byId("submit").disabled=false;}
}
async function start(){
  try{
    const [rental,consumer,map,card]=await Promise.all([
      json("./schemas/rental_deposit_input.schema.json"),json("./schemas/consumer_complaint_input.schema.json"),
      json("./mappings/task3_display_map.json"),json("./schemas/action_card.schema.json")]);
    schemas={rental_deposit:rental,consumer_complaint:consumer};labels=map;cardSchema=card;
    if(SEVEN.some(key=>!cardSchema.properties?.[key]))throw Error("Card schema mismatch");
    renderFields();showResponse(null);
    byId("notice").textContent="Schemas loaded. Enter or edit answers and try each synthetic status.";
  }catch(_){byId("notice").textContent="Unable to load schemas. Serve frontend/ over HTTP.";byId("submit").disabled=true;}
}
byId("case-type").addEventListener("change",()=>{if(!labels)return;++revision;renderFields();showResponse(null);});
byId("submit").addEventListener("click",submit);
start();
