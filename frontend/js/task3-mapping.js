"use strict";
// Task 3 display-only mapping: no local routing, thresholds, or legal rules.
const CASES = {
  rental_deposit: "./mocks/rental_deposit_request.json",
  consumer_complaint: "./mocks/consumer_complaint_request.json"
};
const SECTIONS = ["case_summary","potential_channels","conditions","steps","document_checklist","unresolved_questions","citations"];
const STATUSES = new Set(["NEED_CLARIFICATION","SUPPORTED_PATH","REFER_TO_OFFICIAL","ERROR"]);
const el = id => document.getElementById(id);
const line = (parent,tag,value) => { const n=document.createElement(tag);n.textContent=String(value);parent.append(n);return n; };
const empty = node => node.replaceChildren();
const known = (value, exists) => !exists ? "Missing" : value===null ? "Not provided (null)" : value==="unknown" ? "Unknown" : value===false ? "No" : value===true ? "Yes" : value==="" ? "Empty" : typeof value==="string"||typeof value==="number" ? String(value) : "Unavailable";
async function getJSON(url,options) { const r=await fetch(url,options); if(!r.ok) throw Error("HTTP "+r.status); return r.json(); }
let labels, input, sequence=0;
function renderInputs() {
  const target=el("fields");empty(target);
  const fields=labels?.[el("case").value] || {};
  for(const [name,label] of Object.entries(fields)) {
    line(target,"dt",label);
    const present=input?.answers && Object.prototype.hasOwnProperty.call(input.answers,name);
    line(target,"dd",known(input?.answers?.[name],present));
  }
}
function verifiedRecords(response) {
  // Evidence metadata is necessary, never sufficient for actual official verification.
  if(response?.status!=="SUPPORTED_PATH" || !response.action_card ||
    !Array.isArray(response.evidence) || !Array.isArray(response.action_card.citations) ||
    !response.action_card.citations.length || !response.source_version ||
    response.source_version.startsWith("mock")) return null;
  const records=new Map();
  response.evidence.forEach(item=>{
    if(item?.review_status!=="verified" || item.source_version!==response.source_version) return;
    try {
      const u=new URL(item.url);
      if(!["http:","https:"].includes(u.protocol)||u.hostname.endsWith(".invalid")||u.username||u.password) return;
      records.set(item.evidence_id,{...item,href:u.href});
    } catch (_) {}
  });
  const matched=response.action_card.citations.map(id=>records.get(id));
  return matched.every(Boolean)?matched:null;
}
function render(response) {
  const target=el("sections");empty(target);
  empty(el("questions"));empty(el("warnings"));
  const status=STATUSES.has(response?.status)?response.status:"UNAVAILABLE";
  el("status").textContent=status;
  const records=verifiedRecords(response);
  el("verification").textContent=records
    ?"Evidence metadata supplied by backend; independently confirm official sources before relying on it."
    :"Needs verification — verified supporting evidence or a complete Action Card is unavailable.";
  if(status==="NEED_CLARIFICATION" && Array.isArray(response.questions))
    response.questions.forEach(q=>{if(typeof q?.label==="string")line(el("questions"),"p",q.label);});
  if(Array.isArray(response?.warnings))
    response.warnings.forEach(w=>{if(typeof w==="string")line(el("warnings"),"p",w);});
  for(const key of SECTIONS) {
    const section=document.createElement("section");section.className="section";
    line(section,"h3",labels?.action_card?.[key]||key);
    const value=response?.action_card?.[key];
    const factual=["case_summary","potential_channels","conditions","steps","document_checklist","citations"].includes(key);
    if(factual&&!records) line(section,"p","Needs verification — no supported data to display.");
    else if(value===null||value===undefined||value===""||(Array.isArray(value)&&!value.length))
      line(section,"p","Not provided by backend.");
    else if(key==="citations") {
      const list=document.createElement("ul");
      (records||[]).forEach(record=>{
        const li=document.createElement("li"),a=document.createElement("a");
        a.textContent=record.source_id+" ("+record.evidence_id+")";a.href=record.href;
        a.target="_blank";a.rel="noopener noreferrer";li.append(a);list.append(li);
      });section.append(list);
    } else if(Array.isArray(value)) {
      const list=document.createElement("ul");
      value.filter(v=>typeof v==="string").forEach(v=>line(list,"li",v));
      if(!list.children.length)line(section,"p","Not provided by backend.");
      else section.append(list);
    } else if(typeof value==="string")line(section,"p",value);
    else line(section,"p","Unsupported value — needs verification.");
    target.append(section);
  }
}
async function changeCase() {
  const token=++sequence;input=null;renderInputs();render(null);
  try {
    labels ||= await getJSON("./mappings/task3_display_map.json");
    const c=el("case").value;
    const payload=await getJSON(CASES[c]);
    if(token!==sequence)return;
    if(payload.case_type!==c||payload.api_version!=="1.0"||!payload.answers)throw Error("Invalid fixture");
    input=payload;renderInputs();el("message").textContent="Synthetic input fixture loaded.";
  } catch (_) {if(token===sequence)el("message").textContent="Input fixture unavailable. Serve frontend/ using HTTP."; }
}
async function requestServer() {
  if(!input){el("message").textContent="Input unavailable; cannot request backend.";return;}
  const token=sequence,button=el("request");
  button.disabled=true;el("status").textContent="LOADING";
  const abort=new AbortController(),timeout=setTimeout(()=>abort.abort(),8000);
  try {
    const response=await getJSON("/api/navigate",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify(input),signal:abort.signal});
    if(token===sequence)render(response);
  } catch (_) {if(token===sequence){render(null);el("message").textContent="Backend unavailable or response invalid; confirm using official sources.";}}
  finally {clearTimeout(timeout);button.disabled=false;}
}
el("case").addEventListener("change",changeCase);
el("request").addEventListener("click",requestServer);
changeCase();
