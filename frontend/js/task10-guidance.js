"use strict";
/* Task 10: viewer for Task 12 research guidance and Task 14 checked display records.
   Backend/source owners, not this browser, validate citations against current
   source digests and quarantine state. A verified snapshot is never legal advice. */
(function (root, factory) {
  const api = factory();
  if (typeof module === "object" && module.exports) module.exports = api;
  if (root) root.SGNaviTask10Guidance = api;
})(typeof globalThis !== "undefined" ? globalThis : this, function () {
  const SECTIONS = Object.freeze([
    ["potential_channels", "Official services to explore"],
    ["conditions", "Things to check"],
    ["steps", "Preparation steps"],
    ["document_checklist", "Documents to prepare"]
  ]);
  const NAMES = Object.freeze({
    dispute_with:"Dispute with", premises_type:"Property type",
    tenancy_duration_months:"Tenancy duration", claim_amount_sgd:"Amount (SGD)",
    relevant_event_date:"Relevant date", respondent_in_singapore:"Other party in Singapore",
    agency_agreement_signed:"Agency agreement", resolution_attempted:"Tried resolving the issue",
    documents_available:"Documents available", purchase_type:"Goods or services",
    purchase_purpose:"Purchase purpose", supplier_registered_in_sg:"Seller registered in Singapore",
    supplier_location:"Seller location", problem_type:"Problem", purchase_date:"Purchase date"
  });
  const OFFICIAL_HOSTS = new Set(["www.judiciary.gov.sg","www.case.org.sg","www.cea.gov.sg"]);
  const own = (obj,key) => Object.prototype.hasOwnProperty.call(obj,key);
  const object = x => x !== null && typeof x === "object" && !Array.isArray(x);
  const nonempty = x => typeof x === "string" && x.trim().length > 0 && x.length <= 3000;
  const failed = reason => ({kind:"unverified",notice:reason || "This information could not be checked safely.",sources:[]});
  const uniqueStrings = value => Array.isArray(value) && value.length >= 1 && value.length <= 64 &&
    value.every(nonempty) && new Set(value).size === value.length;
  function safeOfficialURL(value) {
    if (typeof value !== "string") return null;
    try {
      const u = new URL(value);
      if (u.protocol !== "https:" || u.username || u.password || u.port ||
          !OFFICIAL_HOSTS.has(u.hostname.toLowerCase())) return null;
      return u.href;
    } catch (_) { return null; }
  }
  function inspectPreview(data) {
    if (!object(data) || data.results_version !== "0.1" ||
        typeof data.result_id !== "string" || !/^[a-f0-9]{24}$/.test(data.result_id) ||
        !nonempty(data.source_version) ||
        !["GUIDANCE_ONLY","LIMITED_REFERRAL"].includes(data.guidance_status) ||
        !Array.isArray(data.limitations) ||
        data.limitations.some(x=>!nonempty(x)) ||
        !Array.isArray(data.display_evidence)) {
      return failed("The checking service returned an unsupported result. Please use official sources.");
    }
    if (data.guidance_status === "LIMITED_REFERRAL") {
      if (data.research_guidance !== null || data.display_evidence.length !== 0) {
        return failed("The limited result contained information we cannot verify.");
      }
      return {kind:"limited",sources:[],limitations:data.limitations,
        notice:"There is not enough checked information to show preparation steps. Please check official guidance."};
    }
    const guide = data.research_guidance;
    if (!object(guide) || !nonempty(guide.case_summary) ||
        !Array.isArray(guide.unresolved_questions) || guide.unresolved_questions.length > 64 ||
        guide.unresolved_questions.some(q=>!object(q) || !nonempty(q.field) || !nonempty(q.text)) ||
        !uniqueStrings(guide.citations) ||
        !data.display_evidence.length || data.display_evidence.length > 64) {
      return failed("Some guidance or source references are missing.");
    }
    const sources = new Map();
    for (const rec of data.display_evidence) {
      if (!object(rec) || !nonempty(rec.evidence_id) || sources.has(rec.evidence_id) ||
          !nonempty(rec.source_id) || !nonempty(rec.publisher) || !nonempty(rec.title) ||
          !nonempty(rec.verbatim_excerpt) || !nonempty(rec.summary) ||
          !nonempty(rec.source_locator) || !nonempty(rec.reviewed_at) ||
          !Number.isFinite(Date.parse(rec.reviewed_at)) ||
          rec.source_version !== data.source_version || rec.review_status !== "verified" ||
          rec.display_version !== "1.0" || rec.display_state !== "verified_snapshot" ||
          rec.preview !== null || !Array.isArray(rec.rule_ids) ||
          !/^[0-9a-f]{64}$/.test(rec.excerpt_sha256 || "") ||
          !safeOfficialURL(rec.url)) {
        return failed("An official reference is incomplete, outdated, or unsafe to display.");
      }
      // Task 14 context is optional until the final backend enrichment is wired.
      // Never represent absent context as a missing screenshot or a live check.
      if (own(rec,"display_context")) {
        const ctx=rec.display_context;
        if (!object(ctx) || ctx.quarantine_state !== "not_quarantined_at_read" ||
            ctx.quote_kind !== "verbatim_official_excerpt" ||
            ctx.summary_kind !== "sg_navi_editorial_summary" ||
            ctx.locator_kind !== "sg_navi_textual_description" ||
            ctx.quote_completeness !== "short_fragment_requires_official_context" ||
            !(ctx.surrounding_quote === null || nonempty(ctx.surrounding_quote))) {
          return failed("The official excerpt context could not be checked.");
        }
      }
      sources.set(rec.evidence_id,{...rec,href:safeOfficialURL(rec.url)});
    }
    if (sources.size !== guide.citations.length ||
        guide.citations.some(id=>!sources.has(id))) {
      return failed("The result and its official citations do not match.");
    }
    const claims = [];
    for (const [section] of SECTIONS) {
      const items=guide[section];
      if (!Array.isArray(items) || items.length > 64) return failed("A guidance section is incomplete.");
      for (let i=0;i<items.length;i++) {
        const item=items[i];
        if (!object(item) || !nonempty(item.text) || !uniqueStrings(item.evidence_ids) ||
            item.evidence_ids.some(id=>!sources.has(id))) {
          return failed("A preparation step has no valid supporting source.");
        }
        claims.push({section,index:i,text:item.text,evidenceIds:item.evidence_ids});
      }
    }
    if (!claims.length) return failed("No checked preparation steps are available.");
    // A future Task 14 response can additionally project the authoritative
    // claim-citation mapping. It must agree exactly with the source-backed
    // template item mapping before the browser can render either.
    if (own(data,"claim_citations")) {
      if (!Array.isArray(data.claim_citations) || data.claim_citations.length !== claims.length) {
        return failed("Claim-to-source references do not match the displayed steps.");
      }
      const mapped=new Map();
      for (const entry of data.claim_citations) {
        if (!object(entry) || !nonempty(entry.claim_id) || mapped.has(entry.claim_id)) {
          return failed("Duplicate or invalid claim references were supplied.");
        }
        mapped.set(entry.claim_id,entry);
      }
      for (const item of claims) {
        const key=item.section+":"+item.index, mappedItem=mapped.get(key);
        if (!mappedItem || mappedItem.section !== item.section ||
            mappedItem.index !== item.index || mappedItem.text !== item.text ||
            mappedItem.text_kind !== "sg_navi_reviewed_template_text" ||
            !uniqueStrings(mappedItem.evidence_ids) ||
            mappedItem.evidence_ids.length !== item.evidenceIds.length ||
            item.evidenceIds.some(x=>!mappedItem.evidence_ids.includes(x))) {
          return failed("A displayed claim could not be linked to its exact sources.");
        }
      }
    }
    return {kind:"guidance",guide,claims,sources,limitations:data.limitations,
      sourceVersion:data.source_version,resultId:data.result_id,
      notice:"Research and preparation information only. This is not a legal eligibility decision or a filing service."};
  }
  function create(doc,tag,text,className) {
    const el=doc.createElement(tag);
    if (text !== undefined) el.textContent=String(text);
    if (className) el.className=className;
    return el;
  }
  function addFactSummary(doc,node,answers) {
    const section=create(doc,"section",undefined,"reported-facts");
    section.appendChild(create(doc,"h3","Your answers (not independently verified)"));
    const dl=create(doc,"dl",undefined,"fact-grid");
    for (const [field,value] of Object.entries(object(answers)?answers:{})) {
      if (!own(NAMES,field) || !(value === null || value === "unknown" ||
            typeof value === "boolean" || typeof value === "number" || typeof value === "string")) continue;
      const label=value === null ? "Not provided" : value === "unknown" ? "Not sure" :
        value === false ? "No" : value === true ? "Yes" : String(value);
      dl.append(create(doc,"dt",NAMES[field]),create(doc,"dd",label));
    }
    if (dl.children.length) section.appendChild(dl);
    else section.appendChild(create(doc,"p","No answers have been entered.","muted"));
    node.appendChild(section);
  }
  function clear(doc) {
    for (const id of ["task10-fact-summary","task10-source-list","task10-evidence-viewer"]) {
      const el=doc.getElementById(id);
      if (el) el.replaceChildren();
    }
    const details=doc.getElementById("task10-evidence-details");
    if (details) details.open=false;
  }
  function render(data,doc,answers={}) {
    const list=doc.getElementById("task10-source-list"),
      viewer=doc.getElementById("task10-evidence-viewer"),
      summary=doc.getElementById("task10-fact-summary"),
      details=doc.getElementById("task10-evidence-details"),
      status=doc.getElementById("task10-evidence-state");
    if (!list || !viewer || !summary || !details || !status) return null;
    clear(doc);
    const model=inspectPreview(data);
    addFactSummary(doc,summary,answers);
    list.appendChild(create(doc,"p",model.notice,"evidence-notice"));
    status.textContent=model.kind === "guidance"
      ? "Official source records checked against the reviewed snapshot — not live website verification"
      : "No source-backed preparation steps available";
    if (model.kind !== "guidance") {
      for (const reason of model.limitations || []) list.appendChild(create(doc,"p",reason,"muted"));
      viewer.appendChild(create(doc,"p","No verified original excerpt is available for this result. Please consult official sources directly.","muted"));
      details.open=true;
      return model;
    }
    const {guide,sources,claims}=model;
    list.appendChild(create(doc,"h3","Your situation"));
    list.appendChild(create(doc,"p",guide.case_summary,"guidance-summary"));
    const controls=[];
    function showEvidence(ids,focus) {
      viewer.replaceChildren();
      for (const id of ids) {
        const source=sources.get(id);
        const section=create(doc,"section",undefined,"matched-evidence");
        section.appendChild(create(doc,"p","Reviewed source record · not a legal decision","evidence-eyebrow"));
        const title=create(doc,"h3",source.title,"evidence-publisher");
        title.tabIndex=-1;
        section.appendChild(title);
        section.appendChild(create(doc,"p","Official publisher: "+source.publisher));
        const block=create(doc,"blockquote",source.verbatim_excerpt,"source-excerpt");
        section.appendChild(create(doc,"h4","Original wording from the recorded official source"));
        section.appendChild(block);
        if (source.display_context && source.display_context.surrounding_quote) {
          section.appendChild(create(doc,"h4","Additional recorded original context"));
          section.appendChild(create(doc,"blockquote",source.display_context.surrounding_quote,"source-excerpt"));
        }
        section.appendChild(create(doc,"h4","SG Navi explanation (not an official quotation)"));
        section.appendChild(create(doc,"p",source.summary));
        const meta=create(doc,"dl",undefined,"source-metadata");
        for (const [label,value] of [
          ["Source description (not a page anchor)",source.source_locator],
          ["Recorded source review date",source.reviewed_at],
          ["Recorded review status",source.review_status],
          ["Source version",source.source_version],
          ["Evidence reference",source.evidence_id]
        ]) meta.append(create(doc,"dt",label),create(doc,"dd",value));
        section.appendChild(meta);
        const link=create(doc,"a","Open Original Source ↗","original-link");
        link.href=source.href; link.target="_blank"; link.rel="noopener noreferrer";
        section.appendChild(link);
        section.appendChild(create(doc,"p","Short extracts can omit important conditions. Read the full official page before acting.","evidence-disclaimer"));
        viewer.appendChild(section);
      }
      details.open=true;
      if(focus) viewer.querySelector("h3")?.focus();
    }
    function refButton(ids,text) {
      const button=create(doc,"button",text,"claim-reference");
      button.type="button";
      button.setAttribute("aria-pressed","false");
      button.addEventListener("click",()=>{
        for(const el of controls) el.setAttribute("aria-pressed",String(el===button));
        showEvidence(ids,true);
      });
      controls.push(button);
      return button;
    }
    for (const [section,label] of SECTIONS) {
      const group=claims.filter(x=>x.section===section);
      if (!group.length) continue;
      list.appendChild(create(doc,"h3",label));
      const ol=create(doc,section==="steps"?"ol":"ul",undefined,"guidance-items");
      for (const item of group) {
        const li=create(doc,"li");
        if (section === "document_checklist") {
          const tick=create(doc,"label",undefined,"preparation-check");
          const box=doc.createElement("input");
          box.type="checkbox"; box.setAttribute("aria-label","Mark for personal preparation: "+item.text);
          tick.append(box,doc.createTextNode(item.text));
          li.appendChild(tick);
        } else li.appendChild(create(doc,"p",item.text));
        li.appendChild(refButton(item.evidenceIds,item.evidenceIds.length===1
          ? "Read supporting source" : "Read "+item.evidenceIds.length+" supporting sources"));
        ol.appendChild(li);
      }
      list.appendChild(ol);
    }
    if (guide.document_checklist.length) list.appendChild(create(doc,"p",
      "Checklist ticks are only for personal planning on this page. They do not file a case.","muted"));
    if (guide.unresolved_questions.length) {
      list.appendChild(create(doc,"h3","Questions still to check"));
      const ul=create(doc,"ul");
      for(const q of guide.unresolved_questions) ul.appendChild(create(doc,"li",q.text));
      list.appendChild(ul);
    }
    list.appendChild(create(doc,"h3","Official references"));
    const ul=create(doc,"ul",undefined,"guidance-citations");
    for(const id of guide.citations) {
      const source=sources.get(id);
      const li=create(doc,"li");
      li.appendChild(refButton([id],source.publisher+" — "+source.title));
      ul.appendChild(li);
    }
    list.appendChild(ul);
    for(const reason of model.limitations) list.appendChild(create(doc,"p",reason,"muted"));
    showEvidence(claims[0].evidenceIds,false);
    controls[0]?.setAttribute("aria-pressed","true");
    return model;
  }
  return Object.freeze({inspectPreview,render,clear,safeOfficialURL});
});
