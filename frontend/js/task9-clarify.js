"use strict";
/* Task 9: server-driven clarification only. The server decides what is relevant.
   Never infer legal eligibility or invent required questions in this module. */
(function (root, factory) {
  const api = factory();
  if (typeof module === "object" && module.exports) module.exports = api;
  if (root) root.SGNaviTask9 = api;
  if (root && root.document && typeof root.document.getElementById === "function") {
    api.init(root.document, root);
  }
})(typeof globalThis !== "undefined" ? globalThis : this, function () {
  const CASES = Object.freeze(["rental_deposit", "consumer_complaint"]);
  const SCHEMAS = Object.freeze({
    rental_deposit: "./schemas/rental_deposit_input.schema.json",
    consumer_complaint: "./schemas/consumer_complaint_input.schema.json"
  });
  const LABELS = Object.freeze({
    dispute_with: "Who is the dispute with?",
    premises_type: "What type of property are you renting?",
    tenancy_duration_months: "How many months is your tenancy?",
    claim_amount_sgd: "What amount is involved?",
    relevant_event_date: "When did the relevant event happen?",
    respondent_in_singapore: "Is the other party in Singapore?",
    agency_agreement_signed: "Have you signed an agency agreement?",
    resolution_attempted: "Have you tried resolving this with the other party?",
    documents_available: "Do you have relevant documents?",
    purchase_type: "What goods or services did you buy?",
    purchase_purpose: "Was the purchase for personal or business use?",
    supplier_registered_in_sg: "Is the seller registered in Singapore?",
    supplier_location: "Where is the seller located?",
    problem_type: "What went wrong with the product or service?",
    purchase_date: "When did you buy it?"
  });
  const DESCRIPTIONS = Object.freeze({
    claim_amount_sgd: "Enter the SGD amount, or choose Not sure / Not provided.",
    tenancy_duration_months: "Enter the duration in months, if known.",
    relevant_event_date: "Use the date from your own records; do not guess.",
    purchase_date: "Use the purchase date, if known.",
    dispute_with: "For example, landlord or property agent.",
    premises_type: "For example, residential apartment or room.",
    purchase_type: "For example, a phone, household item or service.",
    purchase_purpose: "For example, personal use or business use.",
    supplier_location: "Enter a location only if you know it.",
    problem_type: "For example, faulty item, missing delivery or service concern."
  });
  const own = (object, key) => Object.prototype.hasOwnProperty.call(object, key);
  const nullish = value => value === null || value === "unknown" || value === undefined;
  function kindOf(definition) {
    const variants = Array.isArray(definition?.anyOf) ? definition.anyOf : [definition];
    if (variants.some(v => v.type === "boolean")) return "boolean";
    if (variants.some(v => v.type === "number")) return "number";
    if (variants.some(v => v.format === "date")) return "date";
    return "string";
  }
  function parseAnswer(raw, definition, mode = "value") {
    if (mode === "null") return {value: null};
    if (mode === "unknown") return {value: "unknown"};
    if (mode !== "value") return {error: "Select an answer."};
    if (typeof raw !== "string" || !raw.trim()) return {error: "Enter an answer or choose Not sure / Not provided."};
    const kind = kindOf(definition);
    if (kind === "boolean") {
      if (raw === "true") return {value: true};
      if (raw === "false") return {value: false};
      return {error: "Choose Yes, No or Not sure."};
    }
    if (kind === "number") {
      if (!/^\d+(?:\.\d+)?$/.test(raw.trim())) return {error: "Enter a valid non-negative number."};
      const number = Number(raw);
      const variants = definition.anyOf || [definition];
      const minimum = variants.find(v => v.type === "number")?.minimum;
      if (!Number.isFinite(number) || (minimum !== undefined && number < minimum))
        return {error: "Enter a number within the allowed range."};
      return {value: number};
    }
    if (kind === "date") {
      if (!/^\d{4}-\d{2}-\d{2}$/.test(raw)) return {error: "Use YYYY-MM-DD."};
      const date = new Date(raw + "T00:00:00Z");
      if (!Number.isFinite(date.getTime()) || date.toISOString().slice(0, 10) !== raw)
        return {error: "Enter a valid calendar date."};
    }
    return {value: raw.trim()};
  }
  function validateResponse(payload, schema) {
    if (!payload || typeof payload !== "object" || Array.isArray(payload) ||
        payload.api_version !== "1.0" ||
        !["NEED_CLARIFICATION", "REFER_TO_OFFICIAL", "SUPPORTED_PATH", "ERROR"].includes(payload.status) ||
        !Array.isArray(payload.questions) || !Array.isArray(payload.warnings) ||
        !Array.isArray(payload.evidence) || typeof payload.source_version !== "string" ||
        typeof payload.rule_version !== "string") throw new Error("Invalid response");
    if (payload.status === "NEED_CLARIFICATION") {
      if (payload.action_card !== null || !payload.questions.length ||
          payload.questions.some(q => !q || typeof q.id !== "string" ||
            !own(schema.properties, q.id) || typeof q.label !== "string" ||
            !["text","number","select","date","boolean"].includes(q.input_type))) {
        throw new Error("Unknown or invalid follow-up question");
      }
    }
    if (payload.status === "ERROR" && (!payload.warnings.length || payload.action_card !== null))
      throw new Error("Invalid error response");
    return payload;
  }
  function filterUnresolved(questions, answers) {
    // Explicit unknown/null may remain unresolved for the backend. Do not repeatedly
    // require users to re-enter the same uncertain value in this UI.
    return questions.filter(q => !own(answers, q.id));
  }
  function safeQuestions(questions, schema) {
    const seen = new Set();
    return questions.filter(q => {
      if (!q || !own(schema.properties, q.id) || seen.has(q.id)) return false;
      seen.add(q.id);
      return true;
    });
  }
  function init(doc, win) {
    const byId = id => doc.getElementById(id);
    const topic = byId("case-type");
    if (!topic || !byId("answer-form")) return null;
    const area = byId("question-area"), heading = byId("current-question");
    const answerControls = byId("answer-controls"), error = byId("answer-error");
    const feedback = byId("flow-feedback"), retry = byId("retry");
    const progress = byId("progress"), facts = byId("confirmed-facts");
    const result = byId("result"), message = byId("result-message");
    const warnings = byId("result-warnings"), sources = byId("verified-source-list");
    const continueButton = byId("question-continue");
    const state = {
      schemas: {}, answers: {}, pending: null, revision: 0,
      questionQueue: [], cursor: 0, current: null, busy: false
    };
    const setText = (element, text) => { element.textContent = String(text); };
    const element = (tag, text, cls) => {
      const node = doc.createElement(tag);
      if (text !== undefined) setText(node, text);
      if (cls) node.className = cls;
      return node;
    };
    function setFeedback(text) {
      setText(feedback, text);
      feedback.hidden = !text;
    }
    function invalidate() {
      ++state.revision;
      state.pending?.abort();
      state.pending = null;
      state.busy = false;
      continueButton.disabled = false;
      retry.hidden = true;
      result.hidden = true;
      if (win.SGNaviTask10) win.SGNaviTask10.clear(doc);
      warnings.replaceChildren();
      sources.replaceChildren();
      state.questionQueue = [];
      state.cursor = 0;
      state.current = null;
      area.hidden = true;
    }
    function displayAnswer(value) {
      if (value === null) return "Not provided";
      if (value === "unknown") return "Not sure";
      if (value === true) return "Yes";
      if (value === false) return "No";
      return String(value);
    }
    function renderFacts() {
      facts.replaceChildren();
      const entries = Object.entries(state.answers);
      if (!entries.length) { facts.appendChild(element("p", "No answers yet.", "empty")); return; }
      for (const [field, value] of entries) {
        const card = element("div", undefined, "fact-row");
        card.appendChild(element("p", LABELS[field] || field, "fact-key"));
        card.appendChild(element("p", displayAnswer(value), "fact-value"));
        const edit = element("button", "Edit answer", "fact-edit");
        edit.type = "button";
        edit.setAttribute("aria-label", "Edit " + (LABELS[field] || field));
        edit.addEventListener("click", () => {
          invalidate();
          // Any prior backend result is no longer reliable after a correction.
          delete state.answers[field];
          renderFacts();
          state.questionQueue = [{id:field,label:LABELS[field] || field,input_type:kindOf(state.schemas[topic.value].properties[field])}];
          state.cursor = 0;
          setText(progress, "Editing a previous answer. Further questions will be checked again.");
          showCurrent();
        });
        card.appendChild(edit);
        facts.appendChild(card);
      }
    }
    function addRadio(parent, name, value, title, checked = false) {
      const label = element("label", undefined, "radio-choice");
      const input = doc.createElement("input");
      input.type = "radio"; input.name = name; input.value = value; input.checked = checked;
      label.append(input, doc.createTextNode(title));
      parent.appendChild(label);
      return input;
    }
    function answerField(question) {
      answerControls.replaceChildren();
      const definition = state.schemas[topic.value].properties[question.id];
      const kind = kindOf(definition);
      if (kind === "boolean") {
        addRadio(answerControls, "answer-mode", "true", "Yes");
        addRadio(answerControls, "answer-mode", "false", "No");
        addRadio(answerControls, "answer-mode", "unknown", "Not sure");
        addRadio(answerControls, "answer-mode", "null", "Not provided");
        return;
      }
      const label = element("label", kind === "number" ?
        (question.id === "claim_amount_sgd" ? "Amount (SGD)" : "Number of months") : "Your answer", "answer-label");
      label.htmlFor = "answer-value";
      const line = element("div", undefined, kind === "number" && question.id === "claim_amount_sgd" ? "number-wrap" : "");
      if (kind === "number" && question.id === "claim_amount_sgd")
        line.appendChild(element("span", "S$", "number-unit"));
      const input = doc.createElement("input");
      input.className = "answer-input"; input.id = "answer-value"; input.name = "answer-value";
      input.type = kind === "number" ? "number" : kind === "date" ? "date" : "text";
      input.maxLength = 200;
      if (kind === "number") { input.min = "0"; input.step = "any"; }
      input.autocomplete = "off";
      line.appendChild(input);
      answerControls.append(label, line);
      const options = element("div", undefined, "answer-option-list");
      addRadio(options, "answer-mode", "value", "Use the value above", true);
      addRadio(options, "answer-mode", "unknown", "Not sure / Unknown");
      addRadio(options, "answer-mode", "null", "Not provided");
      answerControls.appendChild(options);
      options.addEventListener("change", () => {
        const selected = options.querySelector('input[name="answer-mode"]:checked')?.value;
        input.disabled = selected !== "value";
      });
    }
    function showCurrent() {
      const q = state.questionQueue[state.cursor];
      if (!q) { area.hidden = true; return; }
      state.current = q;
      area.hidden = false;
      setText(byId("question-count"), "Question " + (state.cursor + 1) + " of " + state.questionQueue.length + " requested by the service");
      setText(heading, LABELS[q.id] || q.label);
      setText(byId("question-hint"), DESCRIPTIONS[q.id] || "Choose an answer or Not sure. No eligibility decision is made here.");
      answerField(q);
      setText(error, "");
      byId("question-back").disabled = state.cursor === 0 && Object.keys(state.answers).length === 0;
      heading.focus();
    }
    async function loadSchema(selected) {
      if (state.schemas[selected]) return state.schemas[selected];
      const response = await win.fetch(SCHEMAS[selected], {cache:"no-store",headers:{Accept:"application/json"}});
      if (!response.ok) throw Error("Could not load questions");
      const schema = await response.json();
      if (!schema || !schema.properties || typeof schema.properties !== "object") throw Error("Invalid question schema");
      state.schemas[selected] = schema;
      return schema;
    }
    // Task 12 is additive. A preview failure never promotes a legacy referral
    // into a supported result. The unchanged v1 workflow remains available.
    async function fetchGuidancePreview(caseType,answers,revision) {
      const endpoint=win.SGNaviApiConfig.resolve("/api/results/preview",win.location);
      if (!endpoint) return null;
      const controller=new AbortController();
      state.pending=controller;
      const timer=setTimeout(()=>controller.abort(),10000);
      try {
        const response=await win.fetch(endpoint,{
          method:"POST",
          headers:{"Content-Type":"application/json",Accept:"application/json"},
          body:JSON.stringify({
            results_version:"0.1",confirmed:true,
            case_type:caseType,confirmed_answers:{...answers}
          }),
          signal:controller.signal
        });
        if (revision !== state.revision || !response.ok ||
            !(response.headers.get("content-type") || "").toLowerCase().includes("application/json")) return null;
        const payload=await response.json();
        return revision === state.revision ? payload : null;
      } catch (_) {
        return null;
      } finally {
        clearTimeout(timer);
        if (state.pending === controller) state.pending=null;
      }
    }
    async function check() {
      const selected = topic.value;
      if (!CASES.includes(selected)) return;
      invalidate();
      const rev = state.revision;
      setText(progress, "Checking which details are still needed…");
      setFeedback("");
      try {
        const schema = await loadSchema(selected);
        if (rev !== state.revision) return;
        const endpoint = win.SGNaviApiConfig.resolve("/api/navigate", win.location);
        if (!endpoint) throw Error("Service unavailable");
        const controller = new AbortController();
        state.pending = controller;
        state.busy = true;
        const timer = setTimeout(() => controller.abort(), 10000);
        let payload;
        try {
          const response = await win.fetch(endpoint, {
            method:"POST",
            headers:{"Content-Type":"application/json",Accept:"application/json"},
            body:JSON.stringify({api_version:"1.0",case_type:selected,answers:{...state.answers}}),
            signal:controller.signal
          });
          if (!(response.headers.get("content-type") || "").toLowerCase().includes("application/json"))
            throw Error("Invalid service response");
          payload = validateResponse(await response.json(), schema);
          if (!response.ok && payload.status !== "ERROR") throw Error("Service unavailable");
        } finally {
          clearTimeout(timer);
        }
        if (rev !== state.revision) return;
        if (payload.status === "NEED_CLARIFICATION") {
          const questions = filterUnresolved(safeQuestions(payload.questions,schema), state.answers);
          if (!questions.length) {
            setText(progress, "More information is still needed.");
            setFeedback("You marked all remaining details as Unknown or Not provided. We cannot determine a supported path. Edit an answer if you learn more, or consult official information.");
            retry.hidden = true;
          } else {
            state.questionQueue = questions;
            state.cursor = 0;
            setText(progress, "A few more details are needed. Questions come from the SG Navi service.");
            showCurrent();
          }
        } else {
          setText(progress, payload.status === "ERROR" ? "Checking is unavailable" : "Review your information");
          setText(message, payload.status === "ERROR"
            ? "The service could not complete the check. Your answers remain on this page."
            : "Only available official reference information is shown. We cannot confirm a legal process or eligibility.");
          result.hidden = false;
          for (const warning of payload.warnings) {
            if (typeof warning === "string") warnings.appendChild(element("p", warning));
          }
          // Only a real v1 referral may request the separately versioned
          // Task 12 research preview. Do not treat v1 SUPPORTED_PATH as verified.
          // Unavailable, malformed or limited guidance never produces made-up
          // eligibility, quotations, or approved legal Action Cards.
          let inspection=null;
          if (payload.status === "REFER_TO_OFFICIAL" && payload.action_card === null &&
              win.SGNaviTask10Guidance) {
            const preview=await fetchGuidancePreview(selected,{...state.answers},rev);
            if (rev !== state.revision) return;
            if (preview) {
              const model=win.SGNaviTask10Guidance.inspectPreview(preview);
              if (model.kind === "guidance" || model.kind === "limited") {
                inspection=win.SGNaviTask10Guidance.render(preview,doc,{...state.answers});
                setText(message,model.kind === "guidance"
                  ? "Based on the details you provided, here is conditional research and preparation information. Confirm everything on the original official websites."
                  : "There is not enough checked information for detailed preparation guidance. Please check the official websites.");
              }
            }
          }
          if (!inspection) {
            const selector=win.SGNaviVerifiedSources?.selectVerifiedSources;
            inspection=win.SGNaviTask10?.render(payload,doc,{...state.answers},selector) || null;
            if (payload.status === "REFER_TO_OFFICIAL") {
              setText(message,"Only official reference information is available. More detailed guidance could not be checked right now.");
            }
          }
          setText(byId("task10-result-status"), inspection?.kind === "guidance"
            ? "Research guidance · not legal advice"
            : inspection?.kind === "referral"
              ? "Official references · not legal advice"
              : inspection?.kind === "limited"
                ? "Limited information · check official sources"
                : "No verified action available");
          if (payload.status === "ERROR") retry.hidden = false;
          byId("result-title").focus();
        }
      } catch (_) {
        if (rev !== state.revision) return;
        setText(progress, "The service is temporarily unavailable.");
        setFeedback("Your answers are still here. Check your connection and try again.");
        retry.hidden = false;
      } finally {
        if (rev === state.revision) {
          state.pending = null;
          state.busy = false;
          continueButton.disabled = false;
        }
      }
    }
    byId("answer-form").addEventListener("submit", event => {
      event.preventDefault();
      if (!state.current || state.busy) return;
      const question = state.current;
      const selected = answerControls.querySelector('input[name="answer-mode"]:checked')?.value;
      const definition = state.schemas[topic.value].properties[question.id];
      const type = kindOf(definition);
      const mode = type === "boolean" && (selected === "true" || selected === "false") ? "value" : selected;
      const raw = type === "boolean" ? selected : answerControls.querySelector("#answer-value")?.value;
      const parsed = parseAnswer(raw, definition, mode);
      if (parsed.error) {setText(error, parsed.error);return;}
      state.answers[question.id] = parsed.value;
      renderFacts();
      setText(error, "");
      if (state.cursor + 1 < state.questionQueue.length) {
        state.cursor += 1;
        showCurrent();
      } else {
        void check();
      }
    });
    byId("question-back").addEventListener("click", () => {
      if (state.cursor > 0) {
        state.cursor -= 1;
        const q=state.questionQueue[state.cursor];
        delete state.answers[q.id];
        renderFacts();
        showCurrent();
      } else {
        const last = Object.keys(state.answers).at(-1);
        if (last) {
          invalidate();
          delete state.answers[last];
          renderFacts();
          state.questionQueue = [{id:last,label:LABELS[last] || last,input_type:kindOf(state.schemas[topic.value].properties[last])}];
          showCurrent();
        }
      }
    });
    retry.addEventListener("click", () => { void check(); });
    byId("task10-retry").addEventListener("click", () => { void check(); });
    byId("task10-refine").addEventListener("click", () => {
      // Invalidate immediately. The previous result must never survive an edit.
      invalidate();
      setText(progress, "Results cleared. Review or change your answers, then check again.");
      setFeedback("Choose Edit answer on the right to correct a detail, or Check again to rerun the service.");
      renderFacts();
      const firstEdit = facts.querySelector(".fact-edit");
      if (firstEdit) firstEdit.focus();
      else topic.focus();
      retry.hidden = false;
    });
    topic.addEventListener("change", () => {
      invalidate();
      state.answers = {};
      renderFacts();
      if (CASES.includes(topic.value)) void check();
      else setText(progress, "Choose a topic to begin.");
    });
    const requested = new URLSearchParams(win.location.search).get("case_type");
    if (CASES.includes(requested)) {
      topic.value = requested;
      void check();
    } else {
      setText(progress, "Choose Rental Deposit or Consumer Complaint to begin.");
    }
    return {getAnswers: () => ({...state.answers}),check};
  }
  return Object.freeze({parseAnswer,kindOf,validateResponse,filterUnresolved,init});
});
