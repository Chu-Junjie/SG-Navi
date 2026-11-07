"use strict";
/* Task 8 problem-first interface. No production intake endpoint exists until Task 11 is approved. */
(function (root, factory) {
  const api = factory();
  if (typeof module === "object" && module.exports) module.exports = api;
  if (root) root.SGNaviTask8 = api;
  if (root && root.document && typeof root.document.getElementById === "function") {
    api.init(root.document, root);
  }
})(typeof globalThis !== "undefined" ? globalThis : this, function () {
  const MAX_LENGTH = 1200;
  const CATEGORIES = Object.freeze(["rental_deposit", "consumer_complaint"]);
  const FACT_LABELS = Object.freeze({
    amount_sgd: "Amount mentioned (SGD)",
    purchase_amount_sgd: "Purchase amount mentioned (SGD)",
    other_party: "Other party mentioned",
    item_or_service: "Item or service mentioned"
  });
  function validateProblem(raw) {
    if (typeof raw !== "string" || !raw.trim()) return "Please describe your situation before continuing.";
    if (raw.trim().length > MAX_LENGTH) return "Please shorten your description to 1,200 characters.";
    return "";
  }
  function normaliseSuggestion(payload) {
    if (!payload || typeof payload !== "object" || Array.isArray(payload)) {
      throw new Error("Invalid intake response");
    }
    // Frontend presentation shape only. Task 11 must approve and map its response separately.
    const category = CATEGORIES.includes(payload.category) ? payload.category : null;
    const status = ["suggested", "ambiguous", "out_of_scope", "cannot_determine"].includes(payload.status)
      ? payload.status : "cannot_determine";
    const source = payload.candidateFacts;
    const facts = {};
    if (source && typeof source === "object" && !Array.isArray(source)) {
      for (const key of Object.keys(FACT_LABELS)) {
        const value = source[key];
        if (typeof value === "string" && value.trim()) facts[key] = value.slice(0, 160);
        else if (typeof value === "number" && Number.isFinite(value)) facts[key] = String(value);
        else if (typeof value === "boolean") facts[key] = String(value);
      }
    }
    return {status, category: status === "suggested" ? category : null, candidateFacts: facts};
  }
  async function runIntakeRequest(request, text, timeoutMs = 10000) {
    if (typeof request !== "function") throw new Error("Intake is not configured");
    const error = validateProblem(text);
    if (error) throw new Error(error);
    const controller = new AbortController();
    let timer;
    try {
      const response = await Promise.race([
        Promise.resolve().then(() => request(text.trim(), {signal: controller.signal})),
        new Promise((_, reject) => {
          timer = setTimeout(() => {
            controller.abort();
            reject(new Error("TIMEOUT"));
          }, timeoutMs);
        })
      ]);
      return normaliseSuggestion(response);
    } finally {
      clearTimeout(timer);
    }
  }
  function init(doc, win, options = {}) {
    if (win.SGNaviTask21 && options.legacy !== true && win.__SGNaviLegacyRegression !== true) return win.SGNaviTask21.init(doc, win);
    if (win.SGNaviTask15 && options.legacy !== true) return win.SGNaviTask15.init(doc, win);
    const get = id => doc.getElementById(id);
    const form = get("problem-form"), input = get("problem-text"), review = get("problem-review");
    if (!form || !input || !review) return null;
    const error = get("problem-validation"), reviewError = get("review-validation");
    const reviewNote = get("interpretation-note"), reviewSummary = get("review-summary");
    const reviewTitle = get("review-title"), continueButton = get("review-continue");
    const reviewOutcome = get("review-outcome"), factsPanel = get("candidate-facts");
    const factList = get("candidate-list"), submit = get("problem-submit"), count = get("problem-count");
    const formPath = get("problem-intake").getAttribute("data-form-path");
    const isAllowedFormPath = formPath === "./task5-flow.html" ||
      formPath === "./frontend/task5-flow.html";
    let revision = 0;
    const setText = (element, value) => { element.textContent = value; };
    function showFacts(facts) {
      factList.replaceChildren();
      for (const key of Object.keys(facts)) {
        const label = doc.createElement("label");
        label.className = "candidate-item";
        setText(label, FACT_LABELS[key]);
        const field = doc.createElement("input");
        field.className = "candidate-value";
        field.type = "text";
        field.maxLength = 160;
        field.value = facts[key];
        field.setAttribute("data-candidate-fact", key);
        field.setAttribute("aria-label", FACT_LABELS[key] + " (unconfirmed)");
        label.appendChild(field);
        factList.appendChild(label);
      }
      factsPanel.hidden = !Object.keys(facts).length;
    }
    function showReview(problem, suggestion = null) {
      setText(reviewSummary, problem);
      setText(reviewError, "");
      setText(reviewOutcome, "");
      form.querySelectorAll("input[name='review-topic']").forEach(radio => { radio.checked = false; });
      review.querySelectorAll("input[name='review-topic']").forEach(radio => { radio.checked = false; });
      if (suggestion && suggestion.status === "suggested" && suggestion.category) {
        const name = suggestion.category === "rental_deposit" ? "Rental Deposit" : "Consumer Complaint";
        setText(reviewNote, "Suggested topic: " + name +
          " (not confirmed). Please check every detail and choose the appropriate topic yourself.");
        showFacts(suggestion.candidateFacts);
      } else {
        showFacts({});
        const msg = suggestion && suggestion.status === "out_of_scope" ?
          "This description appears outside the two topics covered by this demonstration. No route has been selected. Use official services for other concerns." :
          suggestion && suggestion.status === "ambiguous" ?
          "We could not identify a single supported topic. Please check the options below; no category has been selected." :
          "Automatic problem understanding is not available yet. We have not analysed or extracted any facts. Please choose a topic yourself, or select Not sure / Another topic.";
        setText(reviewNote, msg);
      }
      review.hidden = false;
      reviewTitle.focus();
    }
    function resetReview() {
      revision += 1;
      review.hidden = true;
      setText(error, "");
      setText(reviewError, "");
      setText(reviewOutcome, "");
    }
    input.addEventListener("input", () => {
      setText(count, String(input.value.length) + " / 1,200");
      setText(error, "");
      if (!review.hidden) resetReview();
    });
    doc.querySelectorAll("[data-example-question]").forEach(button => {
      button.addEventListener("click", () => {
        input.value = button.getAttribute("data-example-question");
        input.dispatchEvent(new Event("input", {bubbles: true}));
        input.focus();
      });
    });
    form.addEventListener("submit", async event => {
      event.preventDefault();
      const problem = input.value.trim();
      const validation = validateProblem(problem);
      if (validation) { setText(error, validation); input.focus(); return; }
      const currentRevision = ++revision;
      const request = typeof options.request === "function" ? options.request : null;
      if (!request) { showReview(problem); return; } // Task 11 contract not yet approved.
      submit.disabled = true;
      setText(error, "Checking your description…");
      try {
        const suggestion = await runIntakeRequest(request, problem, options.timeoutMs || 10000);
        if (currentRevision === revision) { setText(error, ""); showReview(problem, suggestion); }
      } catch (caught) {
        if (currentRevision !== revision) return;
        setText(error, caught && caught.message === "TIMEOUT"
          ? "The check took too long. Your text is still here. Please try Find Guidance again."
          : "We could not check your description. Your text is still here. Please try again or use a topic below.");
      } finally {
        if (currentRevision === revision) submit.disabled = false;
      }
    });
    get("review-back").addEventListener("click", () => { resetReview(); input.focus(); });
    continueButton.addEventListener("click", () => {
      setText(reviewError, "");
      const checked = review.querySelector('input[name="review-topic"]:checked');
      if (!checked) { setText(reviewError, "Please choose a topic, Not sure, or Another topic."); return; }
      const topic = checked.value;
      if (!CATEGORIES.includes(topic)) {
        setText(reviewOutcome, topic === "unsure"
          ? "We cannot determine a topic from this description. You can edit it or use the quick-start topics when ready."
          : "This demonstration only supports rental deposits and consumer complaints in Singapore. Please look for an appropriate official service for other concerns.");
        return;
      }
      if (!isAllowedFormPath) { setText(reviewError, "The next step is not available."); return; }
      // Legacy /api/navigate workflow intentionally starts fresh; no raw dispute details are persisted.
      // Task 9 uses the existing approved backend's question list; original form
      // remains accessible from the guided questions screen.
      const guidedPath = formPath.replace("task5-flow.html", "task9-clarify.html");
      win.location.assign(guidedPath + "?case_type=" + topic);
    });
    submit.disabled = false;
    return {showReview, resetReview};
  }
  return Object.freeze({MAX_LENGTH, validateProblem, normaliseSuggestion, runIntakeRequest, init});
});
