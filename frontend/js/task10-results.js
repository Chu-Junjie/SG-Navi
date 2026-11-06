"use strict";
/* Task 10 — conservative results presentation for the CURRENT approved API 1.0.
   This version does not fabricate action cards, excerpts, screenshot previews,
   review dates or item-to-citation mappings. Task 12/14 must define and approve
   a new contract before a new structured result can be displayed. */
(function (root, factory) {
  const api = factory();
  if (typeof module === "object" && module.exports) module.exports = api;
  if (root) root.SGNaviTask10 = api;
})(typeof globalThis !== "undefined" ? globalThis : this, function () {
  const STATUSES = Object.freeze({
    REFER_TO_OFFICIAL: "referral",
    NEED_CLARIFICATION: "clarification",
    ERROR: "error",
    SUPPORTED_PATH: "unsupported_card"
  });
  const LABELS = Object.freeze({
    dispute_with: "Dispute with",
    premises_type: "Property type",
    tenancy_duration_months: "Tenancy duration (months)",
    claim_amount_sgd: "Amount (SGD)",
    relevant_event_date: "Relevant date",
    respondent_in_singapore: "Other party in Singapore",
    agency_agreement_signed: "Agency agreement signed",
    resolution_attempted: "Resolution attempted",
    documents_available: "Documents available",
    purchase_type: "Purchased goods or service",
    purchase_purpose: "Purchase purpose",
    supplier_registered_in_sg: "Seller registered in Singapore",
    supplier_location: "Seller location",
    problem_type: "Problem",
    purchase_date: "Purchase date"
  });
  const own = (value, key) => Object.prototype.hasOwnProperty.call(value, key);
  function answerLabel(value) {
    if (value === null) return "Not provided";
    if (value === "unknown") return "Not sure";
    if (value === true) return "Yes";
    if (value === false) return "No";
    return typeof value === "string" || typeof value === "number" ? String(value) : "Not available";
  }
  function sourceTitle(href) {
    try {
      const hostname = new URL(href).hostname.toLowerCase();
      if (hostname === "www.judiciary.gov.sg" || hostname === "judiciary.gov.sg") return "Singapore Courts";
      if (hostname === "www.case.org.sg" || hostname === "case.org.sg") return "Consumers Association of Singapore (CASE)";
      if (hostname === "www.cea.gov.sg" || hostname === "cea.gov.sg") return "Council for Estate Agencies (CEA)";
      return hostname;
    } catch (_) {
      return "Source website";
    }
  }
  function inspectResult(payload, sourceSelector) {
    // Strictly reject unknown versions: no speculative mapping of Task 12/14 fields.
    if (!payload || typeof payload !== "object" || Array.isArray(payload) ||
        payload.api_version !== "1.0" || !own(STATUSES, payload.status) ||
        !Array.isArray(payload.evidence) || typeof payload.source_version !== "string") {
      return {kind: "unsupported", sources: [], notice: "This result format is not yet supported. Please use the original official websites."};
    }
    if (payload.status === "NEED_CLARIFICATION") {
      return {kind:"clarification", sources:[], notice:"Some details are still missing. Answer or correct them before checking again."};
    }
    if (payload.status === "ERROR") {
      return {kind:"error", sources:[], notice:"We could not safely verify the result. Try again, without changing your answers."};
    }
    if (payload.status === "SUPPORTED_PATH") {
      // The current v1 Action Card has no step-level evidence IDs or verified excerpt
      // projection; synthetic mock cards MUST NOT be presented as supported guidance.
      return {kind:"unsupported_card", sources:[], notice:"This result does not include the approved claim-by-claim evidence needed to display an Action Card. No recommended route can be confirmed here."};
    }
    if (payload.action_card !== null) {
      return {kind:"unverified", sources:[], notice:"The result is missing the expected referral safeguards; no source links will be displayed."};
    }
    if (!payload.evidence.length) {
      return {kind:"missing", sources:[], notice:"No verified official reference is available from this response. Please check directly with the relevant public service."};
    }
    if (typeof sourceSelector !== "function") {
      return {kind:"unverified", sources:[], notice:"The source checking component is unavailable. No reference can be verified for display."};
    }
    const picked = sourceSelector(payload);
    if (!Array.isArray(picked) || picked.length !== payload.evidence.length || !picked.length ||
        picked.some(s => !s || typeof s.href !== "string" ||
          !s.href.startsWith("https://") || typeof s.evidence_id !== "string" ||
          typeof s.source_id !== "string" || s.source_version !== payload.source_version ||
          s.review_status !== "verified") ||
        new Set(picked.map(s => s.evidence_id)).size !== picked.length) {
      return {kind:"unverified", sources:[], notice:"Some official references are missing, outdated, changed or not safely verifiable. They are not shown as reviewed evidence."};
    }
    return {kind:"referral", sources:picked.map(s => ({
      evidenceId:s.evidence_id, sourceId:s.source_id, sourceVersion:s.source_version,
      reviewStatus:s.review_status, href:s.href, publisher:sourceTitle(s.href)
    })), notice:"The service supplied official reference metadata for research, not a verified quotation or a legal eligibility decision."};
  }
  function create(doc,tag,content,className) {
    const node = doc.createElement(tag);
    if (content !== undefined) node.textContent = String(content);
    if (className) node.className = className;
    return node;
  }
  let current = null;
  function clear(doc) {
    current = null;
    for (const id of ["task10-source-list","task10-evidence-viewer","task10-fact-summary"]) {
      const target = doc.getElementById(id);
      if (target) target.replaceChildren();
    }
    const evidence = doc.getElementById("task10-evidence-details");
    if (evidence) evidence.open = false;
  }
  function render(payload,doc,answers={},sourceSelector=null) {
    const sourceList = doc.getElementById("task10-source-list");
    const viewer = doc.getElementById("task10-evidence-viewer");
    const summary = doc.getElementById("task10-fact-summary");
    const details = doc.getElementById("task10-evidence-details");
    const state = doc.getElementById("task10-evidence-state");
    if (!sourceList || !viewer || !summary || !details || !state) return null;
    clear(doc);
    const model = inspectResult(payload,sourceSelector);
    current = model;
    const section = create(doc,"section",undefined,"reported-facts");
    section.appendChild(create(doc,"h3","Details you provided (not independently verified)"));
    const entries = Object.entries(answers).filter(([key,value]) => own(LABELS,key) &&
      (value === null || value === "unknown" || typeof value === "boolean" ||
       typeof value === "number" || typeof value === "string"));
    if (!entries.length) section.appendChild(create(doc,"p","No facts were supplied in this session.","muted"));
    else {
      const definition = create(doc,"dl",undefined,"fact-grid");
      for (const [key,value] of entries) {
        definition.appendChild(create(doc,"dt",LABELS[key]));
        definition.appendChild(create(doc,"dd",answerLabel(value)));
      }
      section.appendChild(definition);
    }
    summary.appendChild(section);
    // Omit the seven legal/informational sections when API 1.0 has a null card.
    // The current API does not provide claim-level supported procedure content.
    const info = create(doc,"p",model.notice,"evidence-notice");
    sourceList.appendChild(info);
    state.textContent = model.kind === "referral" ?
      "Service-listed references · source wording not supplied" :
      "Evidence not available for this result";
    function showSource(source,focus) {
      viewer.replaceChildren();
      viewer.appendChild(create(doc,"p","Source reference · not an eligibility finding","evidence-eyebrow"));
      viewer.appendChild(create(doc,"h3",source.publisher,"evidence-publisher"));
      const metadata = create(doc,"dl",undefined,"source-metadata");
      const fields = [
        ["Source reference",source.sourceId],
        ["Evidence ID",source.evidenceId],
        ["Review status in service data",source.reviewStatus],
        ["Source version",source.sourceVersion],
        ["Review date","Not supplied by this API"],
        ["Exact official excerpt","Not supplied by this API"],
        ["Section / page locator","Not supplied by this API"]
      ];
      for (const [label,value] of fields) {
        metadata.append(create(doc,"dt",label),create(doc,"dd",value));
      }
      viewer.appendChild(metadata);
      const note = create(doc,"p","A link and review status do not establish what legal conditions apply. Read the original source to verify its meaning.","evidence-disclaimer");
      viewer.appendChild(note);
      const link = create(doc,"a","Open Original Source ↗","original-link");
      link.href = source.href;
      link.target = "_blank";
      link.rel = "noopener noreferrer";
      viewer.appendChild(link);
      details.open = true;
      if (focus) viewer.querySelector("h3")?.focus();
    }
    if (model.sources.length) {
      sourceList.appendChild(create(doc,"h3","Official websites to check"));
      const list = create(doc,"div",undefined,"source-options");
      let buttons=[];
      for (const source of model.sources) {
        const button = create(doc,"button",undefined,"source-option");
        button.type = "button";
        const title = create(doc,"span",source.publisher,"source-option-title");
        const id = create(doc,"small","Reference " + source.evidenceId,"source-option-id");
        button.append(title,id);
        button.addEventListener("click",() => {
          for (const candidate of buttons) candidate.setAttribute("aria-pressed",String(candidate===button));
          showSource(source,true);
        });
        button.setAttribute("aria-pressed","false");
        buttons.push(button);
        list.appendChild(button);
      }
      sourceList.appendChild(list);
      buttons[0].setAttribute("aria-pressed","true");
      showSource(model.sources[0],false);
    } else {
      viewer.appendChild(create(doc,"p","No source excerpt or approved evidence is available. We cannot verify a recommended next step here.","muted"));
      viewer.appendChild(create(doc,"p","Open a public service website directly or retry the check when the service is available.","muted"));
      details.open = true;
    }
    return model;
  }
  return Object.freeze({inspectResult,answerLabel,sourceTitle,clear,render});
});
