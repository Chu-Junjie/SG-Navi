"use strict";
const {test} = require("node:test");
const assert = require("node:assert/strict");
const {safeLink,chooseFixture,FIXTURE_QUESTIONS} = require("../js/task20-concept.js");

test("fixture selection is explicit or based on demo-only descriptions",()=>{
  assert.equal(chooseFixture("A restaurant charged extra",null),"restaurant");
  assert.equal(chooseFixture("My landlord kept the deposit",null),"rental");
  assert.equal(chooseFixture("An unrelated question",null),null);
  assert.equal(chooseFixture("An unrelated question","restaurant"),"restaurant");
});
test("only HTTPS URLs at precise reviewed-domain candidates may be shown",()=>{
  assert.equal(safeLink("javascript:alert(1)"),null);
  assert.equal(safeLink("http://www.case.org.sg/submit-a-complaint/"),null);
  assert.equal(safeLink("https://user:pass@www.case.org.sg/submit-a-complaint/"),null);
  assert.equal(safeLink("https://www.case.org.sg.evil.example/"),null);
  assert.equal(safeLink("https://www.judiciary.gov.sg/#fragment"),null);
  assert.equal(safeLink("https://www.judiciary.gov.sg:8080/"),null);
  assert.match(safeLink("https://www.case.org.sg/submit-a-complaint/"),/^https:\/\//);
});
test("each fixture question has Not sure and no personal-data fields",()=>{
  for(const scenario of ["restaurant","rental"]){
    assert.ok(FIXTURE_QUESTIONS[scenario].length >= 1);
    for(const q of FIXTURE_QUESTIONS[scenario]){
      assert.ok(q.options.some(x=>x.toLowerCase().includes("not sure")));
      assert.ok(q.prompt.length>10);
      assert.doesNotMatch(q.prompt,/passport|FIN number|NRIC|full name|phone number/i);
    }
  }
});