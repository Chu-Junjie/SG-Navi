"use strict";
/* Task 5: request/response presentation only. Backend owns routing and all legal content. */
(() => {
  const CASES = Object.freeze({
    rental_deposit: "Rental Deposit",
    consumer_complaint: "Consumer Complaint"
  });
  const STATUSES = new Set(["NEED_CLARIFICATION", "SUPPORTED_PATH", "REFER_TO_OFFICIAL", "ERROR"]);
  const SECTIONS = Object.freeze([
    "case_summary", "potential_channels", "conditions", "steps",
    "document_checklist", "unresolved_questions", "citations"
  ]);
  const FACT_SECTIONS = new Set([
    "case_summary", "potential_channels", "conditions", "steps", "document_checklist", "citations"
  ]);
  const $ = id => document.getElementById(id);
  const add = (parent, tag, content, cls = "") => {
    const node = document.createElement(tag);
    node.textContent = String(content);
    if (cls) node.className = cls;
    parent.appendChild(node);
    return node;
  };
  const clear = node => node.replaceChildren();
  const owns = (object, key) => Object.prototype.hasOwnProperty.call(object, key);
  const state = { schemas: {}, labels: null, card: null, drafts: Object.create(null), revision: 0, pending: null };
  const CASE_SCHEMA = {
    rental_deposit: "./schemas/rental_deposit_input.schema.json",
    consumer_complaint: "./schemas/consumer_complaint_input.schema.json"
  };

  async function loadJSON(path) {
    const result = await fetch(path, { cache: "no-store", headers: { Accept: "application/json" } });
    if (!result.ok) throw new Error("HTTP " + result.status);
    return result.json();
  }
  function dataType(definition) {
    const options = Array.isArray(definition.anyOf) ? definition.anyOf : [definition];
    if (options.some(o => o.type === "boolean")) return "boolean";
    if (options.some(o => o.type === "number")) return "number";
    if (options.some(o => o.format === "date")) return "date";
    return "string";
  }
  function decode(raw, definition) {
    if (raw === "__unknown__") return { value: "unknown" };
    if (raw === "__null__") return { value: null };
    const type = dataType(definition);
    if (type === "boolean") {
      if (raw === "true") return { value: true };
      if (raw === "false") return { value: false };
      return { error: "Select Yes, No or Unknown." };
    }
    if (raw === "") return { error: "Enter a value or select Unknown / Not provided." };
    if (type === "number") {
      const number = Number(raw);
      const minimum = (definition.anyOf || []).find(part => part.type === "number")?.minimum;
      if (!Number.isFinite(number)) return { error: "Enter a valid number." };
      if (minimum !== undefined && number < minimum) return { error: "Enter a number within the allowed range." };
      return { value: number };
    }
    if (type === "date") {
      if (!/^\d{4}-\d{2}-\d{2}$/.test(raw)) return { error: "Use YYYY-MM-DD." };
      const date = new Date(raw + "T00:00:00Z");
      if (!Number.isFinite(date.getTime()) || date.toISOString().slice(0, 10) !== raw) {
        return { error: "Enter a valid calendar date." };
      }
    }
    return { value: raw };
  }
  function labelOf(field) {
    return state.labels?.[$("case-type").value]?.[field] || field;
  }
  function cancelStale() {
    ++state.revision;
    if (state.pending) state.pending.abort();
    state.pending = null;
    $("submit").disabled = false;
  }
  function clearResult(message = "Edit answers and select Check case to request another response.") {
    $("status").textContent = "No current result";
    $("verification").textContent = message;
    ["questions", "warnings", "card", "verified-source-list"].forEach(id => clear($(id)));
    $("verified-source-context").hidden = true;
  }
  function edited() {
    cancelStale();
    store(false);
    clearResult("Answers changed. Submit again to receive an updated backend response.");
  }
  function buildControl(field, definition, initial) {
    const parent = document.createElement("div");
    parent.className = "field";
    const label = add(parent, "label", labelOf(field));
    const id = "input-" + field;
    label.htmlFor = id;
    const select = document.createElement("select");
    select.id = id;
    select.name = field;
    const choices = [["__null__", "Not provided"], ["__unknown__", "Unknown / not sure"]];
    const type = dataType(definition);
    if (type === "boolean") choices.push(["true", "Yes"], ["false", "No"]);
    else choices.push(["__value__", "Enter a value"]);
    for (const [value, title] of choices) {
      const option = document.createElement("option");
      option.value = value;
      option.textContent = title;
      select.appendChild(option);
    }
    const known = initial !== undefined && initial !== null && initial !== "unknown";
    select.value = initial === "unknown" ? "__unknown__" :
      !known ? "__null__" : type === "boolean" ? String(initial) : "__value__";
    parent.appendChild(select);
    let detail = null;
    if (type !== "boolean") {
      detail = document.createElement("input");
      detail.id = "detail-" + field;
      detail.dataset.answerFor = field;
      detail.type = type === "date" ? "date" : type === "number" ? "number" : "text";
      if (type === "number") {
        const minimum = (definition.anyOf || []).find(part => part.type === "number")?.minimum;
        if (minimum !== undefined) detail.min = String(minimum);
        detail.step = "any";
      }
      detail.value = known ? String(initial) : "";
      detail.hidden = select.value !== "__value__";
      detail.disabled = detail.hidden;
      detail.setAttribute("aria-label", labelOf(field) + " value");
      parent.appendChild(detail);
    }
    const error = add(parent, "span", "", "field-error");
    error.id = "error-" + field;
    error.setAttribute("role", "status");
    select.setAttribute("aria-describedby", error.id);
    select.addEventListener("change", () => {
      if (detail) {
        detail.hidden = select.value !== "__value__";
        detail.disabled = detail.hidden;
      }
      edited();
    });
    if (detail) detail.addEventListener("input", edited);
    return parent;
  }
  function renderForm() {
    const kind = $("case-type").value;
    const fields = state.schemas[kind]?.properties || {};
    clear($("dynamic-fields"));
    const saved = state.drafts[kind] || {};
    for (const [field, definition] of Object.entries(fields)) {
      $("dynamic-fields").appendChild(buildControl(field, definition, saved[field]));
    }
  }
  function store(showErrors) {
    const kind = $("case-type").value;
    const fields = state.schemas[kind]?.properties || {};
    const prior = state.drafts[kind] || {};
    const next = { ...prior };
    let failures = 0;
    for (const [field, definition] of Object.entries(fields)) {
      const option = $("input-" + field);
      const detail = $("detail-" + field);
      if (!option) continue;
      const raw = option.value === "__value__" ? (detail?.value ?? "") : option.value;
      const parsed = decode(raw, definition);
      $("error-" + field).textContent = showErrors ? parsed.error || "" : "";
      if (parsed.error) failures++;
      else next[field] = parsed.value;
    }
    state.drafts[kind] = next;
    $("validation").textContent = showErrors && failures
      ? failures + " answer(s) need correction before submitting." : "";
    return failures === 0;
  }
  function focusField(id) {
    if (!owns(state.schemas[$("case-type").value]?.properties || {}, id)) return;
    const select = $("input-" + id);
    if (!select) return;
    select.scrollIntoView({ behavior: "smooth", block: "center" });
    select.focus();
    select.closest(".field")?.classList.add("highlight");
    window.setTimeout(() => select.closest(".field")?.classList.remove("highlight"), 1800);
  }
  function evidenceFor(response) {
    if (response.status !== "SUPPORTED_PATH" || !response.action_card) return null;
    const records = SGNaviVerifiedSources.selectVerifiedSources(response);
    if (!records) return null;
    const map = new Map(records.map(source => [
      source.evidence_id,
      { record: { source_id: source.source_id, evidence_id: source.evidence_id }, href: source.href }
    ]));
    const matched = response.action_card.citations.map(id => map.get(id));
    return matched.every(Boolean) ? matched : null;
  }
  function renderSection(key, value, evidence) {
    const section = document.createElement("section");
    section.className = "card-section";
    add(section, "h3", state.labels?.action_card?.[key] || key);
    if (FACT_SECTIONS.has(key) && !evidence) {
      add(section, "p", "Needs verification — supporting evidence was not supplied.");
    } else if (value === null || value === undefined || value === "" ||
               (Array.isArray(value) && value.length === 0)) {
      add(section, "p", "Not provided by backend.");
    } else if (key === "citations") {
      const list = document.createElement("ul");
      for (const entry of evidence || []) {
        const item = document.createElement("li");
        const link = document.createElement("a");
        link.href = entry.href;
        link.target = "_blank";
        link.rel = "noopener noreferrer";
        link.textContent = entry.record.source_id + " (" + entry.record.evidence_id + ")";
        item.appendChild(link);
        list.appendChild(item);
      }
      section.appendChild(list);
    } else if (Array.isArray(value)) {
      const list = document.createElement("ul");
      for (const entry of value) if (typeof entry === "string") add(list, "li", entry);
      if (list.children.length) section.appendChild(list);
      else add(section, "p", "Not provided by backend.");
    } else if (typeof value === "string") {
      add(section, "p", value);
    } else {
      add(section, "p", "Unsupported response content — needs verification.");
    }
    $("card").appendChild(section);
  }
  function isEnvelope(response) {
    if (!response || typeof response !== "object" || Array.isArray(response) ||
        response.api_version !== "1.0" || !STATUSES.has(response.status) ||
        !Array.isArray(response.questions) || !Array.isArray(response.warnings) ||
        !Array.isArray(response.evidence) || typeof response.rule_version !== "string" ||
        typeof response.source_version !== "string") return false;
    if (response.status === "NEED_CLARIFICATION")
      return response.questions.length > 0 && response.action_card === null;
    if (response.status === "SUPPORTED_PATH")
      return response.action_card && typeof response.action_card === "object" &&
        SECTIONS.every(key => owns(response.action_card, key));
    if (response.status === "ERROR") return response.action_card === null && response.warnings.length > 0;
    return response.warnings.length > 0;
  }
  function renderResponse(response) {
    ["questions", "warnings", "card", "verified-source-list"].forEach(id => clear($(id)));
    $("verified-source-context").hidden = true;
    $("status").textContent = response.status;
    const evidence = evidenceFor(response);
    $("verification").textContent = evidence
      ? "Backend supplied linked evidence metadata. Verify original sources before relying on a procedure."
      : "Needs verification — no sufficient source-backed guidance is available.";
    if (response.status === "NEED_CLARIFICATION") {
      add($("questions"), "h3", "Please continue answering");
      for (const question of response.questions) {
        if (!question || typeof question.label !== "string") continue;
        const row = document.createElement("div");
        row.className = "question";
        add(row, "span", question.label);
        if (owns(state.schemas[$("case-type").value]?.properties || {}, question.id)) {
          const button = add(row, "button", "Answer / edit", "text-button");
          button.type = "button";
          button.addEventListener("click", () => focusField(question.id));
        } else {
          add(row, "span", "This question is not in the agreed form; please verify the contract.");
        }
        $("questions").appendChild(row);
      }
    }
    if (Array.isArray(response.warnings) && response.warnings.length) {
      add($("warnings"), "h3", "Backend messages");
      for (const warning of response.warnings) if (typeof warning === "string") add($("warnings"), "p", warning);
    }
    if (response.status === "REFER_TO_OFFICIAL") {
      $("verified-source-context").hidden = false;
      const hasSources = SGNaviVerifiedSources.renderReferralSources(
        $("verified-source-list"), response, document
      );
      $("verification").textContent = hasSources
        ? "Verified source context is available for independent checking, not a legal eligibility decision or a recommended route."
        : "Needs verification — no valid referral source links were supplied by the backend.";
      add($("questions"), "p", "The backend could not confirm a supported path. You can edit your answers and check again.");
    }
    if (response.status === "ERROR") {
      add($("questions"), "p", "The request could not be completed. Your answers remain editable; try again or seek official confirmation.");
    }
    const card = response.action_card || {};
    for (const section of SECTIONS) renderSection(section, card[section], evidence);
  }
  async function submit() {
    if (!store(true)) {
      clearResult("Correct the highlighted fields. No request was sent.");
      $("status").textContent = "Input validation";
      return;
    }
    const request = {
      api_version: "1.0",
      case_type: $("case-type").value,
      answers: { ...state.drafts[$("case-type").value] }
    };
    const sequence = ++state.revision;
    if (state.pending) state.pending.abort();
    const controller = new AbortController();
    state.pending = controller;
    $("submit").disabled = true;
    clearResult("Checking the latest answers with the backend…");
    $("status").textContent = "Checking…";
    $("verification").textContent = "Sending answers to the same-origin backend.";
    const timeout = setTimeout(() => controller.abort(), 10000);
    try {
      const response = await fetch("/api/navigate", {
        method: "POST",
        headers: { "Content-Type": "application/json", Accept: "application/json" },
        body: JSON.stringify(request),
        signal: controller.signal
      });
      const contentType = response.headers.get("content-type") || "";
      if (!contentType.includes("application/json")) throw Error("Expected JSON");
      const payload = await response.json();
      if (!isEnvelope(payload)) throw Error("Invalid response contract");
      if (!response.ok && payload.status !== "ERROR") throw Error("Unexpected HTTP response");
      if (sequence !== state.revision) return;
      renderResponse(payload);
      $("request-preview").textContent = JSON.stringify(request, null, 2);
    } catch (_) {
      if (sequence !== state.revision) return;
      clearResult("Service unavailable or invalid API response. Your answers are preserved. Please retry.");
      $("status").textContent = "Service unavailable";
    } finally {
      clearTimeout(timeout);
      if (sequence === state.revision) { state.pending = null; $("submit").disabled = false; }
    }
  }
  function switchCase() {
    cancelStale();
    renderForm();
    clearResult("Choose or edit answers, then check the case using the backend.");
    $("validation").textContent = "";
  }
  async function initialize() {
    try {
      const [rental, consumer, labels, card] = await Promise.all([
        loadJSON(CASE_SCHEMA.rental_deposit),
        loadJSON(CASE_SCHEMA.consumer_complaint),
        loadJSON("./mappings/task3_display_map.json"),
        loadJSON("./schemas/action_card.schema.json")
      ]);
      state.schemas = { rental_deposit: rental, consumer_complaint: consumer };
      state.labels = labels;
      state.card = card;
      for (const kind of Object.keys(CASES)) {
        const properties = state.schemas[kind]?.properties;
        if (!properties || Object.keys(properties).some(key => !owns(labels[kind] || {}, key))) throw Error("Schema mismatch");
        state.drafts[kind] = Object.fromEntries(Object.keys(properties).map(key => [key, null]));
      }
      if (!SECTIONS.every(key => owns(card.properties || {}, key) && owns(labels.action_card || {}, key)))
        throw Error("Card schema mismatch");
      switchCase();
      $("notice").textContent = "Ready. Responses come from the real /api/navigate endpoint.";
    } catch (_) {
      $("notice").textContent = "Unable to load input schemas or mapping files. Use the frontend integration server.";
      $("submit").disabled = true;
    }
  }
  $("case-type").addEventListener("change", switchCase);
  $("submit").addEventListener("click", submit);
  $("edit-answers").addEventListener("click", () => {
    $("dynamic-fields").querySelector("select")?.focus();
    $("dynamic-fields").scrollIntoView({ behavior: "smooth", block: "start" });
  });
  initialize();
})();
