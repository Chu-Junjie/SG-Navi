"use strict";
// The standalone user-visible health widget was intentionally retired by Task20.
// Readiness now means actual guarded intake+guidance requests; do not show a
// cosmetic ready signal without a successful request.
const {test}=require("node:test");
const assert=require("node:assert/strict");
const fs=require("node:fs");
const path=require("node:path");
const {verifyResult}=require("../js/task15-flow.js");

for(const page of ["index.html","frontend/index.html"]){
 test(page+" does not claim service ready without a completed guidance call", async()=>{
   const html=fs.readFileSync(path.resolve(__dirname,"../..",page),"utf8");
   const flow=fs.readFileSync(path.resolve(__dirname,"../js/task15-flow.js"),"utf8");
   assert.ok(html.includes('id="problem-submit"'));
   assert.ok(!html.includes('id="api-status"'));
   assert.ok(!html.includes("Online · Ready to use"));
   assert.ok(flow.includes('await post("/api/intake"'));
   assert.ok(flow.includes('await post("/api/guidance"'));
   assert.ok(flow.includes('if(!response.ok)throw Error("Service unavailable")'));
   assert.ok(flow.includes("showFailure(perform)"));
   await assert.rejects(verifyResult({guidance_status:"GUIDANCE_ONLY"},null),/Invalid guidance/);
 });
}
