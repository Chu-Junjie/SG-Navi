"use strict";
const assert = require("node:assert/strict");
const { test } = require("node:test");
const { selectVerifiedSources, renderReferralSources, safeUrl } = require("../js/verified-sources.js");
const record = (overrides = {}) => ({
  evidence_id: "ID-1", source_id: "SOURCE-1", rule_ids: ["RULE-1"],
  source_version: "kb-2026-11-01.1", review_status: "verified",
  url: "https://www.judiciary.gov.sg/", ...overrides
});
const referral = (records = [record()]) => ({
  api_version: "1.0", rule_version: "mock-1", source_version: "kb-2026-11-01.1",
  status: "REFER_TO_OFFICIAL", questions: [], action_card: null,
  evidence: records, warnings: ["Check the original source, no legal eligibility assessed."]
});
test("valid referral metadata becomes source context without an Action Card", () => {
  const res = selectVerifiedSources(referral());
  assert.equal(res.length, 1);
  assert.equal(res[0].evidence_id, "ID-1");
  assert.equal(res[0].review_status, "verified");
});
test("both independent verified sources survive with preserved IDs", () => {
  const records = [record(), record({ evidence_id: "ID-2", source_id: "SOURCE-2",
    url: "https://www.case.org.sg/" })];
  assert.deepEqual(selectVerifiedSources(referral(records)).map(r => r.evidence_id), ["ID-1", "ID-2"]);
});
test("missing and unsafe source references fail closed", () => {
  const bad = [
    record({ url: "javascript:alert(1)" }), record({ url: "https://example.invalid/" }),
    record({ url: "http://localhost/" }), record({ url: "http://127.0.0.1/" }),
    record({ url: "https://example.com" }), record({ url: "https://user:pass@example.org" }),
    record({ review_status: "quarantined" }), record({ review_status: "unreviewed" }),
    record({ source_version: "outdated" }), record({ evidence_id: "" }),
    record({ source_id: null }), record({ rule_ids: [] })
  ];
  assert.equal(selectVerifiedSources(referral([])), null);
  for (const item of bad) assert.equal(selectVerifiedSources(referral([item])), null);
  assert.equal(selectVerifiedSources(referral([record(), record({evidence_id:"ID-1"})])), null);
  assert.equal(selectVerifiedSources(referral([record(),bad[0]])), null);
  assert.equal(selectVerifiedSources(referral({status:"SUPPORTED_PATH"})), null);
  assert.equal(selectVerifiedSources(referral({source_version:"mock-1"})), null);
  assert.equal(selectVerifiedSources(referral({action_card:{citations:["ID-1"]}})), null);
  assert.equal(safeUrl("data:text/html;base64,xxx"), null);
});
test("supported path citations are matched by ID, not inferred by order", () => {
  const res = referral([record(), record({evidence_id:"ID-2",source_id:"SOURCE-2"})]);
  res.status = "SUPPORTED_PATH";
  res.action_card = { citations: ["ID-2", "ID-1"] };
  assert.deepEqual(selectVerifiedSources(res).map(x=>x.evidence_id), ["ID-2","ID-1"]);
  res.action_card.citations = ["ID-NOT-FOUND"];
  assert.equal(selectVerifiedSources(res),null);
});
test("DOM renderer uses safe links, metadata, disclaimer; clears previous content", () => {
  class Element {
    constructor(tag) { this.tag=tag;this.children=[];this.textContent="";this.href=""; }
    appendChild(el) { this.children.push(el);return el; }
    replaceChildren() { this.children=[]; }
  }
  const doc={createElement: tag=>new Element(tag)}, container=new Element("div");
  assert.equal(renderReferralSources(container, referral(), doc),true);
  const link=container.children[0].children[0].children[0];
  assert.equal(link.tag,"a");assert.equal(link.target,"_blank");
  assert.equal(link.rel,"noopener noreferrer");
  assert.equal(link.href,"https://www.judiciary.gov.sg/");
  assert.match(container.children[0].children[0].children[1].textContent,/official website/);
  assert.equal(renderReferralSources(container, referral([]),doc),false);
  assert.equal(container.children.length,1);
  assert.match(container.children[0].textContent,/Needs verification/);
});
