"use strict";
const {test} = require("node:test");
const assert = require("node:assert/strict");
const {
  validateProblem, normaliseSuggestion, runIntakeRequest, MAX_LENGTH
} = require("../js/task8-home.js");

test("empty input, whitespace and excessive input are rejected safely", () => {
  assert.match(validateProblem("  "), /describe your situation/i);
  assert.match(validateProblem(""), /describe your situation/i);
  assert.match(validateProblem("x".repeat(MAX_LENGTH + 1)), /shorten/i);
  assert.equal(validateProblem("I bought a faulty item."), "");
});
test("unsupported and ambiguous classification never guesses a case type", () => {
  const unsupported = normaliseSuggestion({status: "out_of_scope", category: "rental_deposit"});
  const ambiguous = normaliseSuggestion({status: "ambiguous", category: "consumer_complaint"});
  assert.equal(unsupported.category, null);
  assert.equal(ambiguous.category, null);
  assert.equal(normaliseSuggestion({status: "suggested", category: "employment"}).category, null);
});
test("candidate facts include only a fixed safe presentation allowlist", () => {
  const value = normaliseSuggestion({
    status: "suggested", category: "rental_deposit",
    candidateFacts: {amount_sgd: 2000, other_party: "<img src=x>", malicious: "not displayed"}
  });
  assert.equal(value.category, "rental_deposit");
  assert.equal(value.candidateFacts.amount_sgd, "2000");
  assert.equal(value.candidateFacts.other_party, "<img src=x>");
  assert.equal(Object.hasOwn(value.candidateFacts, "malicious"), false);
});
test("invalid intake response is not silently accepted", () => {
  assert.throws(() => normaliseSuggestion(null), /Invalid intake response/);
  assert.throws(() => normaliseSuggestion([]), /Invalid intake response/);
});
test("request returns a candidate only; user must still confirm separately", async () => {
  const result = await runIntakeRequest(async () => ({
    status: "suggested", category: "consumer_complaint",
    candidateFacts: {item_or_service: "faulty phone"}
  }), "My new phone is faulty.");
  assert.equal(result.category, "consumer_complaint");
  assert.equal(result.candidateFacts.item_or_service, "faulty phone");
});
test("backend error does not create a successful interpretation", async () => {
  await assert.rejects(
    runIntakeRequest(async () => { throw new Error("HTTP 503"); }, "My landlord kept my deposit."),
    /HTTP 503/
  );
});
test("timeouts reject without converting to a case type", async () => {
  await assert.rejects(
    runIntakeRequest(() => new Promise(() => {}), "My landlord kept my deposit.", 10),
    /TIMEOUT/
  );
});
