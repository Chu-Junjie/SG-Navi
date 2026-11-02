/* SG Navi Task 4 — schema-driven UI + synthetic mock transport only.
   No client-side legal rules, official channel selection, or eligibility decisions. */
"use strict";
(() => {
  const CASE_TYPES = Object.freeze({
    rental_deposit: "./schemas/rental_deposit_input.schema.json",
    consumer_complaint: "./schemas/consumer_complaint_input.schema.json"
  });
  const MOCK_RESPONSE_FILES = Object.freeze({
    NEED_CLARIFICATION: "./mocks/need_clarification_response.json",
    SUPPORTED_PATH: "./mocks/supported_path_response.json",
    REFER_TO_OFFICIAL: "./mocks/refer_to_official_response.json",
    ERROR: "./mocks/error_response.json"
  });
  const RESPONSE_FIELDS = Object.freeze([
    "api_version", "rule_version", "source_version", "status",
    "questions", "action_card", "evidence", "warnings"
  ]);
  const $ = id => document.getElementById(id);
  const state = { inputs: Object.create(null), actionCard: null,
    labels: null, drafts: Object.create(null), generation: 0 };
  const addText = (parent, tag, value, cls) => {
    const node = document.createElement(tag);
    node.textContent = String(value);
    if (cls) node.className = cls;
    parent.appendChild(node);
    return node;
  };
  const clear = node => node.replaceChildren();
  const own = (obj, name) => Object.prototype.hasOwnProperty.call(obj, name);

  async function getJSON(path) {
    const result = await fetch(path, { cache: "no-store", headers: { Accept: "application/json" } });
    if (!result.ok) throw new Error("Could not load fixture: " + result.status);
    return result.json();
  }

  function descriptor(definition) {
    const types = Array.isArray(definition.anyOf) ? definition.anyOf : [definition];
    const typed = types.find(branch => branch && ["number", "boolean", "string"].includes(branch.type));
    if (!typed) throw new Error("Input schema contains an unsupported type");
    return { type: typed.type, format: typed.format || null, minimum: typed.minimum };
  }

  function caseDraft(kind, key) {
    if (!state.drafts[kind]) state.drafts[kind] = Object.create(null);
    if (!state.drafts[kind][key]) state.drafts[kind][key] = { mode: "omit", raw: "" };
    return state.drafts[kind][key];
  }

  function invalidateResult() {
    state.generation++;
    $("result-status").textContent = "ANSWERS CHANGED";
    $("result-message").textContent = "Submit again to preview the edited answers.";
    $("evidence-alert").textContent = "Needs verification — previous mock response is no longer current.";
    $("question-panel").replaceChildren();
    $("warning-panel").replaceChildren();
    renderCard(null, null);
  }

  function makeValueControl(typeInfo, id, draft, onEdit) {
    let input;
    if (typeInfo.type === "boolean") {
      input = document.createElement("select");
      for (const [value, label] of [["", "Select Yes or No"], ["true", "Yes"], ["false", "No"]]) {
        const option = document.createElement("option");
        option.value = value; option.textContent = label; input.appendChild(option);
      }
    } else {
      input = document.createElement("input");
      input.type = typeInfo.type === "number" ? "number" : typeInfo.format === "date" ? "date" : "text";
      if (typeInfo.type === "number") {
        input.step = "any";
        if (typeof typeInfo.minimum === "number") input.min = String(typeInfo.minimum);
      }
      if (input.type === "text") input.placeholder = "Enter an answer";
    }
    input.id = id;
    input.name = id;
    input.value = draft.raw;
    input.autocomplete = "off";
    const update = () => { draft.raw = input.value; onEdit(); };
    input.addEventListener("input", update);
    input.addEventListener("change", update);
    return input;
  }

  function renderForm() {
    const kind = $("case-type").value;
    const schema = state.inputs[kind];
    if (!schema || !schema.properties || !state.labels?.[kind]) return;
    const root = $("dynamic-fields");
    clear(root); $("form-summary").textContent = "";
    for (const [key, property] of Object.entries(schema.properties)) {
      const draft = caseDraft(kind, key), info = descriptor(property);
      const wrap = document.createElement("div"); wrap.className = "field";
      wrap.dataset.field = key;
      const row = addText(wrap, "div", "", "field-row");
      const titleArea = document.createElement("div");
      const title = addText(titleArea, "label", state.labels[kind][key] || key, "field-label");
      const typeDescription = info.type === "number" ? "Number" : info.type === "boolean" ? "Yes / No" : info.format === "date" ? "Date" : "Text";
      addText(title, "small", typeDescription + " · " + key);
      row.appendChild(titleArea);
      const stateArea = document.createElement("div"); stateArea.className = "field-state";
      const stateId = "mode-" + key;
      const stateLabel = addText(stateArea, "label", "Answer state");
      stateLabel.htmlFor = stateId;
      const stateSelect = document.createElement("select"); stateSelect.id = stateId;
      stateSelect.setAttribute("aria-label", "Answer state for " + (state.labels[kind][key] || key));
      for (const [value, name] of [["omit", "Skip field"], ["value", "Provide answer"], ["unknown", "Unknown"], ["null", "Not provided (null)"]]) {
        const opt = document.createElement("option"); opt.value = value; opt.textContent = name; stateSelect.appendChild(opt);
      }
      stateSelect.value = draft.mode;
      stateArea.appendChild(stateSelect); row.appendChild(stateArea);
      const valueArea = document.createElement("div"); valueArea.className = "field-value";
      const controlId = "value-" + key;
      const valueLabel = addText(valueArea, "label", "Your answer"); valueLabel.htmlFor = controlId;
      const control = makeValueControl(info, controlId, draft, () => { clearFieldError(); invalidateResult(); });
      valueArea.appendChild(control);
      valueArea.hidden = draft.mode !== "value";
      wrap.appendChild(valueArea);
      const error = addText(wrap, "p", "", "field-error");
      error.id = "error-" + key; control.setAttribute("aria-describedby", error.id);
      function clearFieldError() { error.textContent = ""; control.removeAttribute("aria-invalid"); }
      stateSelect.addEventListener("change", () => {
        draft.mode = stateSelect.value;
        valueArea.hidden = draft.mode !== "value";
        clearFieldError(); invalidateResult();
        if (draft.mode === "value") control.focus();
      });
      title.htmlFor = stateId;
      root.appendChild(wrap);
    }
  }

  function dateIsReal(raw) {
    if (!/^\d{4}-\d{2}-\d{2}$/.test(raw)) return false;
    const [year, month, day] = raw.split("-").map(Number);
    const result = new Date(0);
    result.setUTCFullYear(year, month - 1, day);
    return result.getUTCFullYear() === year && result.getUTCMonth() === month - 1 && result.getUTCDate() === day;
  }

  function parseAnswer(raw, info) {
    if (info.type === "boolean") {
      if (raw === "true") return { value: true };
      if (raw === "false") return { value: false };
      return { error: "Please choose Yes or No, or select Unknown." };
    }
    if (info.type === "number") {
      if (raw.trim() === "" || !/^[+-]?(?:\d+\.?\d*|\.\d+)$/.test(raw.trim()))
        return { error: "Enter a valid number, or select Unknown." };
      const number = Number(raw);
      if (!Number.isFinite(number) || (typeof info.minimum === "number" && number < info.minimum))
        return { error: "Enter a finite number within the schema minimum, or select Unknown." };
      return { value: number };
    }
    if (info.format === "date") {
      if (!dateIsReal(raw)) return { error: "Enter a valid date (YYYY-MM-DD), or select Unknown." };
      return { value: raw };
    }
    if (raw.trim() === "") return { error: "Enter some text, or select Unknown." };
    return { value: raw.trim() };
  }

  function buildRequest() {
    const kind = $("case-type").value, schema = state.inputs[kind];
    const answers = {}, errors = [];
    for (const [key, definition] of Object.entries(schema.properties)) {
      const draft = caseDraft(kind, key);
      const control = $("value-" + key), error = $("error-" + key);
      error.textContent = ""; control.removeAttribute("aria-invalid");
      if (draft.mode === "omit") continue;
      if (draft.mode === "unknown") { answers[key] = "unknown"; continue; }
      if (draft.mode === "null") { answers[key] = null; continue; }
      const parsed = parseAnswer(draft.raw, descriptor(definition));
      if (own(parsed, "error")) {
        errors.push({ control, error, message: parsed.error });
        control.setAttribute("aria-invalid", "true"); error.textContent = parsed.error;
      } else answers[key] = parsed.value;
    }
    for (const key of schema.required || []) {
      if (!own(answers, key) && !errors.some(e => e.control.id === "value-" + key))
        errors.push({ control: $("mode-" + key), error: $("error-" + key), message: "This schema requires a value." });
    }
    if (errors.length) {
      $("form-summary").textContent = errors.length + " answer(s) need correction before this mock request can be sent.";
      errors[0].control.focus();
      return null;
    }
    $("form-summary").textContent = "";
    return { api_version: "1.0", case_type: kind, answers };
  }

  // Mock transport: fetch only existing synthetic response JSON, never /api/navigate.
  async function mockNavigate(request, chosenStatus) {
    if (request.api_version !== "1.0" || !own(CASE_TYPES, request.case_type))
      throw new Error("Invalid request envelope");
    if (!own(MOCK_RESPONSE_FILES, chosenStatus)) throw new Error("Unknown mock status");
    const response = await getJSON(MOCK_RESPONSE_FILES[chosenStatus]);
    if (!response || response.api_version !== "1.0" || response.status !== chosenStatus ||
        RESPONSE_FIELDS.some(field => !own(response, field))) throw new Error("Unexpected mock response");
    return response;
  }

  function describeEvidence(record, sourceVersion) {
    if (!record || record.review_status !== "verified" || record.source_version !== sourceVersion ||
        typeof record.evidence_id !== "string" || typeof record.url !== "string") return null;
    try {
      const url = new URL(record.url);
      if (!["http:", "https:"].includes(url.protocol) || url.username || url.password ||
          !url.hostname || url.hostname.endsWith(".invalid") || sourceVersion.startsWith("mock")) return null;
      return { id: record.evidence_id, name: String(record.source_id), url: url.href };
    } catch (_) { return null; }
  }

  function verifiedCitations(response) {
    if (!Array.isArray(response?.evidence) || !Array.isArray(response?.action_card?.citations) ||
        !response.action_card.citations.length || typeof response.source_version !== "string") return null;
    const byId = new Map();
    response.evidence.forEach(entry => {
      const value = describeEvidence(entry, response.source_version);
      if (value) byId.set(value.id, value);
    });
    const matches = response.action_card.citations.map(id => byId.get(id));
    return matches.every(Boolean) ? matches : null;
  }

  function renderCard(card, response) {
    const root = $("card-sections"); clear(root);
    const fields = state.actionCard?.properties || {};
    const citations = verifiedCitations(response);
    for (const key of Object.keys(fields)) {
      const section = document.createElement("section"); section.className = "result-section";
      addText(section, "h3", state.labels?.action_card?.[key] || key);
      const value = card && own(card, key) ? card[key] : null;
      // Mock data (including its fake 'verified' record) is never shown as an official pathway.
      const sensitive = ["potential_channels", "conditions", "steps", "document_checklist", "citations"].includes(key);
      if (sensitive && card && !citations) {
        addText(section, "p", "Needs verification — no genuine supporting evidence was supplied.");
      } else if (value === null || value === undefined || value === "" || (Array.isArray(value) && value.length === 0)) {
        addText(section, "p", "Not provided by mock response.");
      } else if (key === "citations") {
        const list = document.createElement("ul");
        for (const item of citations || []) {
          const li = document.createElement("li"), a = document.createElement("a");
          a.href = item.url; a.target = "_blank"; a.rel = "noopener noreferrer";
          a.textContent = item.name + " (" + item.id + ")"; li.appendChild(a); list.appendChild(li);
        }
        section.appendChild(list);
      } else if (typeof value === "string") {
        addText(section, "p", value);
      } else if (Array.isArray(value)) {
        const list = document.createElement("ul");
        value.filter(v => typeof v === "string").forEach(item => addText(list, "li", item));
        if (!list.children.length) addText(section, "p", "Not provided by mock response.");
        else section.appendChild(list);
      } else addText(section, "p", "Unsupported result value — needs verification.");
      root.appendChild(section);
    }
  }

  function renderLines(rootId, title, items) {
    const root = $(rootId); clear(root);
    if (!Array.isArray(items) || !items.length) return;
    addText(root, "h3", title);
    for (const item of items) if (typeof item === "string") addText(root, "p", item);
  }

  function renderResult(response) {
    $("result-status").textContent = response.status;
    $("result-message").textContent = "Synthetic fixture returned by the Mock API.";
    $("evidence-alert").textContent =
      "Needs verification — these fixtures cannot establish eligibility, official evidence, or any genuine filing route.";
    renderLines("question-panel", "Backend questions (synthetic)",
      response.status === "NEED_CLARIFICATION" && Array.isArray(response.questions)
        ? response.questions.map(q => q && q.label).filter(v => typeof v === "string") : []);
    renderLines("warning-panel", "Response warnings", response.warnings);
    renderCard(response.action_card, response);
  }

  async function submit(event) {
    event.preventDefault();
    const request = buildRequest();
    if (!request) return;
    const ticket = ++state.generation;
    const button = $("submit-form"); button.disabled = true;
    $("result-status").textContent = "LOADING";
    try {
      const response = await mockNavigate(request, $("mock-status").value);
      if (ticket === state.generation) renderResult(response);
    } catch (_) {
      if (ticket === state.generation) {
        $("result-status").textContent = "UNAVAILABLE";
        $("result-message").textContent = "Mock API fixture could not be loaded.";
        $("evidence-alert").textContent = "Needs verification — no valid response available.";
        clear($("question-panel")); clear($("warning-panel")); renderCard(null, null);
      }
    } finally { button.disabled = false; }
  }

  async function initialise() {
    try {
      const [rental, consumer, actionCard, labels] = await Promise.all([
        getJSON(CASE_TYPES.rental_deposit), getJSON(CASE_TYPES.consumer_complaint),
        getJSON("./schemas/action_card.schema.json"), getJSON("./mappings/task3_display_map.json")
      ]);
      state.inputs.rental_deposit = rental;
      state.inputs.consumer_complaint = consumer;
      state.actionCard = actionCard;
      state.labels = labels;
      for (const kind of Object.keys(CASE_TYPES)) {
        if (!state.inputs[kind]?.properties) throw new Error("Invalid input schema");
        if (Object.keys(state.inputs[kind].properties).some(key => !own(state.labels[kind] || {}, key)))
          throw new Error("Field-label map does not match input schema");
      }
      if (!state.actionCard?.properties || Object.keys(state.actionCard.properties).length !== 7 ||
          Object.keys(state.actionCard.properties).some(key => !own(state.labels.action_card || {}, key)))
        throw new Error("Invalid Action Card schema");
      renderForm(); renderCard(null, null);
      $("case-type").addEventListener("change", () => { invalidateResult(); renderForm(); });
      $("mock-status").addEventListener("change", invalidateResult);
      $("case-form").addEventListener("submit", submit);
    } catch (_) {
      $("form-summary").textContent = "Cannot load approved schemas. Serve frontend/ from a local HTTP server.";
      $("submit-form").disabled = true;
      $("result-status").textContent = "UNAVAILABLE";
      $("result-message").textContent = "No mock data loaded.";
    }
  }
  initialise();
})();
