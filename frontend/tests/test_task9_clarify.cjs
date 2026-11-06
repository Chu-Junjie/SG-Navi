"use strict";
const {test} = require("node:test");
const assert = require("node:assert/strict");
const {parseAnswer,kindOf,validateResponse,filterUnresolved} = require("../js/task9-clarify.js");

const string = {anyOf:[{type:"string"},{const:"unknown"},{type:"null"}]};
const number = {anyOf:[{type:"number",minimum:0},{const:"unknown"},{type:"null"}]};
const bool = {anyOf:[{type:"boolean"},{const:"unknown"},{type:"null"}]};
const date = {anyOf:[{type:"string",format:"date"},{const:"unknown"},{type:"null"}]};
const schema = {properties:{claim_amount_sgd:number,respondent_in_singapore:bool,dispute_with:string,purchase_date:date}};
test("schema types are selected by actual definitions",()=>{
  assert.equal(kindOf(number),"number");
  assert.equal(kindOf(bool),"boolean");
  assert.equal(kindOf(date),"date");
  assert.equal(kindOf(string),"string");
});
test("unknown, not provided, false and missing remain distinct",()=>{
  assert.deepEqual(parseAnswer("ignored",bool,"unknown"),{value:"unknown"});
  assert.deepEqual(parseAnswer("ignored",bool,"null"),{value:null});
  assert.deepEqual(parseAnswer("false",bool),{value:false});
  assert.deepEqual(parseAnswer("true",bool),{value:true});
  assert.equal(Object.hasOwn({}, "respondent_in_singapore"),false);
});
test("SGD amount, empty inputs and calendar dates are validated",()=>{
  assert.deepEqual(parseAnswer("2000",number),{value:2000});
  assert.deepEqual(parseAnswer("0",number),{value:0});
  assert.match(parseAnswer("-9",number).error,/valid/i);
  assert.match(parseAnswer("abc",number).error,/valid/i);
  assert.match(parseAnswer("",string).error,/Enter an answer/);
  assert.deepEqual(parseAnswer("2026-10-31",date),{value:"2026-10-31"});
  assert.match(parseAnswer("2026-02-30",date).error,/calendar/i);
});
test("only actual backend-reported questions can drive the flow",()=>{
  const base={api_version:"1.0",rule_version:"mock-1",source_version:"kb-v1",
    questions:[{id:"claim_amount_sgd",label:"What amount?",input_type:"number",required:true}],
    warnings:[],evidence:[],action_card:null,status:"NEED_CLARIFICATION"};
  assert.equal(validateResponse(base,schema).status,"NEED_CLARIFICATION");
  assert.throws(()=>validateResponse({...base,questions:[{id:"invented_eligibility",label:"?",input_type:"text"}]},schema),/Unknown/);
  assert.throws(()=>validateResponse({...base,questions:[]},schema),/Unknown/);
});
test("only unanswered (not previously set unknown/null/false) questions recur",()=>{
  const q=[{id:"claim_amount_sgd"},{id:"respondent_in_singapore"},{id:"dispute_with"}];
  assert.deepEqual(filterUnresolved(q,{claim_amount_sgd:2000,respondent_in_singapore:false}).map(x=>x.id),["dispute_with"]);
  assert.deepEqual(filterUnresolved(q,{claim_amount_sgd:"unknown",respondent_in_singapore:null}).map(x=>x.id),["dispute_with"]);
});
