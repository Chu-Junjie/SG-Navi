/* Task 2: synthetic wire-format preview only. No legal routing or live API calls. */
"use strict";

const CASE_FIXTURES = Object.freeze({
  rental_deposit: "./mocks/rental_deposit_request.json",
  consumer_complaint: "./mocks/consumer_complaint_request.json"
});
const STATUS_FIXTURES = Object.freeze({
  NEED_CLARIFICATION: "./mocks/need_clarification_response.json",
  SUPPORTED_PATH: "./mocks/supported_path_response.json",
  REFER_TO_OFFICIAL: "./mocks/refer_to_official_response.json",
  ERROR: "./mocks/error_response.json"
});
const CARD_SECTIONS = Object.freeze([
  "case_summary", "potential_channels", "conditions", "steps",
  "document_checklist", "unresolved_questions", "citations"
]);
const $ = (id) => document.getElementById(id);
const clean = (node) => node.replaceChildren();

function displayValue(value) {
  if (value === null || value === undefined || value === "unknown") return "Unknown / not provided";
  if (value === true) return "Yes (synthetic)";
  if (value === false) return "No (synthetic)";
  if (value === "") return "Not provided";
  return String(value);
}
function appendText(container, tagName, text, className = "") {
  const el = document.createElement(tagName);
  el.textContent = text;
  if (className) el.className = className;
  container.appendChild(el);
  return el;
}
function renderAnswers(answers) {
  const root = $("answers");
  clean(root);
  if (!answers || typeof answers !== "object" || Array.isArray(answers)) {
    appendText(root, "dd", "No input data available", "empty");
    return;
  }
  for (const [field, value] of Object.entries(answers)) {
    appendText(root, "dt", field);
    const unknown = value === null || value === undefined || value === "unknown";
    appendText(root, "dd", displayValue(value), unknown ? "unknown" : "");
  }
}
function renderList(parent, heading, items) {
  appendText(parent, "h3", heading.replaceAll("_", " "));
  if (items === null || items === undefined || (Array.isArray(items) && items.length === 0)) {
    appendText(parent, "p", "No information provided in mock", "empty");
    return;
  }
  if (Array.isArray(items)) {
    const list = document.createElement("ul");
    items.forEach((item) => appendText(list, "li", displayValue(item)));
    parent.appendChild(list);
    return;
  }
  appendText(parent, "p", displayValue(items));
}
function renderResponse(response) {
  const questions = $("questions"), card = $("card"), warnings = $("warnings"), evidence = $("evidence");
  [questions, card, warnings, evidence].forEach(clean);
  $("mock-status").textContent = response && typeof response.status === "string" ? response.status : "ERROR";
  if (!response || typeof response !== "object") {
    renderList(warnings, "Warnings", ["Missing mock response. No action can be suggested."]);
    return;
  }
  if (response.status === "NEED_CLARIFICATION") {
    renderList(questions, "Questions", (response.questions || []).map(q => q && q.label || "Question unavailable"));
  }
  if (response.action_card && typeof response.action_card === "object") {
    appendText(card, "h3", "Seven-section Action Card (synthetic)");
    for (const name of CARD_SECTIONS) renderList(card, name, response.action_card[name]);
  } else {
    renderList(card, "Action Card", null);
  }
  if (Array.isArray(response.warnings) && response.warnings.length) {
    renderList(warnings, "Warnings", response.warnings);
  }
  if (Array.isArray(response.evidence) && response.evidence.length) {
    renderList(evidence, "Mock evidence IDs (not official sources)",
      response.evidence.map(e => e && e.evidence_id || "Unknown fixture ID"));
  }
}
async function loadJson(path) {
  const result = await fetch(path, {cache: "no-store"});
  if (!result.ok) throw new Error("HTTP " + result.status + " for " + path);
  return result.json();
}
let activeLoad = 0;
async function showFixture() {
  const current = ++activeLoad;
  $("preview-message").textContent = "Loading synthetic fixtures…";
  try {
    const [request, response] = await Promise.all([
      loadJson(CASE_FIXTURES[$("case-select").value]),
      loadJson(STATUS_FIXTURES[$("status-select").value])
    ]);
    if (current !== activeLoad) return;
    renderAnswers(request && request.answers);
    renderResponse(response);
    $("preview-message").textContent = "Synthetic fixtures loaded. Not a live assessment.";
  } catch (error) {
    if (current !== activeLoad) return;
    renderAnswers(null);
    renderResponse(null);
    $("preview-message").textContent = "Could not load mock files. Run from a local HTTP server (not file://).";
  }
}
$("case-select").addEventListener("change", showFixture);
$("status-select").addEventListener("change", showFixture);
showFixture();
