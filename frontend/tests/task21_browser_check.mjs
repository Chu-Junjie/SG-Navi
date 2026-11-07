// Actual keyboard/DOM -> real HTTP APIs. No API interception or supplied replies.
import assert from 'node:assert/strict';
import fs from 'node:fs/promises';
import path from 'node:path';
import {spawn} from 'node:child_process';
import {createHash} from 'node:crypto';

const base=new URL(process.argv[2]||'http://127.0.0.1:5000/');
const publicRun=base.protocol==='https:';
assert.ok(publicRun?base.href==='https://chu-junjie.github.io/SG-Navi/':base.hostname==='127.0.0.1'&&base.protocol==='http:');
const apiOrigin=publicRun?'https://sg-navi-api-junjie.onrender.com':base.origin;
const executable=process.argv[3]||(process.platform==='win32'?'C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe':'/usr/bin/google-chrome');
const artifacts=path.resolve('instance/task21-browser-'+(publicRun?'public':'local'));
await fs.mkdir(artifacts,{recursive:true});
const profile=await fs.mkdtemp(path.join(artifacts,'profile-'));
const browser=spawn(executable,['--headless=new','--no-sandbox','--disable-gpu','--disable-dev-shm-usage','--disable-background-networking','--disable-sync','--no-first-run','--no-default-browser-check','--remote-debugging-port=0',`--user-data-dir=${profile}`,'about:blank'],{windowsHide:true,stdio:['ignore','pipe','pipe']});
let browserLog='',launchError,ws,session,serial=0;
browser.on('error',e=>{launchError=e;});for(const stream of [browser.stdout,browser.stderr])stream.on('data',d=>{browserLog=(browserLog+d.toString()).slice(-1800);});
const pending=new Map(),requests=[],responses=new Map(),finished=new Set(),exceptions=[];
const delay=ms=>new Promise(r=>setTimeout(r,ms));
function command(method,params={},attached=true){const id=++serial;return new Promise((resolve,reject)=>{const timeout=setTimeout(()=>{pending.delete(id);reject(Error('CDP timeout '+method));},30000);pending.set(id,{resolve,reject,timeout});ws.send(JSON.stringify({id,method,params,...(attached&&session?{sessionId:session}:{})}));});}
async function evaluate(expression){const r=await command('Runtime.evaluate',{expression,returnByValue:true,awaitPromise:true});if(r.exceptionDetails)throw Error(JSON.stringify(r.exceptionDetails));return r.result.value;}
async function until(expression,seconds=60){for(let n=0;n<seconds*10;n++){if(await evaluate(expression))return;await delay(100);}throw Error('Timed out: '+expression);}
async function enter(id){await evaluate(`document.getElementById(${JSON.stringify(id)}).focus()`);await command('Input.dispatchKeyEvent',{type:'keyDown',key:'Enter',code:'Enter',text:'\r',unmodifiedText:'\r',windowsVirtualKeyCode:13,nativeVirtualKeyCode:13});await command('Input.dispatchKeyEvent',{type:'keyUp',key:'Enter',code:'Enter',windowsVirtualKeyCode:13,nativeVirtualKeyCode:13});}

const report={scope:"task21_actual_local_browser",passed:false,cases:[],screenshots:[],errors:[],started:new Date().toISOString()};
async function click(selector,text){
 const expr="(()=>{const b=[...document.querySelectorAll("+JSON.stringify(selector)+")].find(x=>x.textContent.includes("+JSON.stringify(text)+"));if(!b)return false;b.click();return true;})()";
 assert.ok(await evaluate(expr),"Missing button: "+text);
}
async function lastResponse(){
 const req=requests.filter(x=>new URL(x.url).pathname==="/api/action-plan"&&x.method==="POST").at(-1);
 assert.ok(req,"Actual Action Plan POST required");
 for(let n=0;n<120&&!finished.has(req.id);n++)await delay(50);
 assert.equal(responses.get(req.id),200);
 return JSON.parse((await command("Network.getResponseBody",{requestId:req.id})).body);
}
async function screenshot(name,width){
 await command("Emulation.setDeviceMetricsOverride",{width,height:850,deviceScaleFactor:1,mobile:width<700});
 await delay(150);
 const sizes=await evaluate("({w:document.documentElement.clientWidth,s:document.documentElement.scrollWidth,h:document.documentElement.scrollHeight})");
 assert.ok(sizes.s<=sizes.w+1,"Mobile horizontal overflow");
 const pic=await command("Page.captureScreenshot",{format:"jpeg",quality:68,
   captureBeyondViewport:true,clip:{x:0,y:0,width:sizes.w,height:Math.min(sizes.h,1500),scale:1}});
 const bytes=Buffer.from(pic.data,"base64"),file=name+"-"+width+".jpg";
 await fs.writeFile(path.join(artifacts,file),bytes);
 report.screenshots.push({file,width,bytes:bytes.length,digest:createHash("sha256").update(bytes).digest("hex")});
}
try{
 let active;
 for(let n=0;n<450;n++){
   if(launchError)throw launchError;
   try{active=(await fs.readFile(path.join(profile,"DevToolsActivePort"),"utf8")).trim().split(/\r?\n/);break;}catch{}
   if(browser.exitCode!==null)throw Error(browserLog);
   await delay(50);
 }
 assert.ok(active,"Chrome debugger unavailable: "+browserLog);
 ws=new WebSocket("ws://127.0.0.1:"+active[0]+active[1]);
 await new Promise((resolve,reject)=>{ws.onopen=resolve;ws.onerror=reject;});
 ws.onmessage=e=>{
   const d=JSON.parse(e.data);
   if(d.id){const p=pending.get(d.id);if(p){clearTimeout(p.timeout);pending.delete(d.id);
     d.error?p.reject(Error(JSON.stringify(d.error))):p.resolve(d.result||{});}return;}
   const x=d.params||{};
   if(d.method==="Network.requestWillBeSent")requests.push({id:x.requestId,url:x.request.url,method:x.request.method,body:x.request.postData||""});
   if(d.method==="Network.responseReceived")responses.set(x.requestId,x.response.status);
   if(d.method==="Network.loadingFinished")finished.add(x.requestId);
 };
 const targets=await command("Target.getTargets",{},false);
 session=(await command("Target.attachToTarget",{targetId:targets.targetInfos.find(t=>t.type==="page").targetId,flatten:true},false)).sessionId;
 for(const m of ["Page.enable","Runtime.enable","Network.enable"])await command(m);
 for(const scenario of [
  {name:"restaurant",description:"The restaurant in Singapore charged me SGD 20 extra and refuses to refund it.",type:"consumer_complaint",subtype:"restaurant_overcharge",goal:"complain"},
  {name:"rental_pass",description:"My work pass was cancelled and I must leave my private rental early. My landlord will not refund my deposit.",type:"rental_deposit",subtype:"pass_related_exit",goal:"seek_refund"}
 ]){
   const trace={name:scenario.name,states:[],passed:false};report.cases.push(trace);
   await command("Emulation.setDeviceMetricsOverride",{width:1440,height:850,deviceScaleFactor:1,mobile:false});
   await command("Page.navigate",{url:base.href});
   await until("document.querySelector('#problem-intake')?.dataset.task21Ready==='true'");
   await evaluate("document.getElementById('problem-text').focus()");
   await command("Input.insertText",{text:scenario.description});
   await enter("problem-submit");
   await until("document.querySelector('#problem-intake')?.dataset.flowStage==='review'");
   let response=await lastResponse();
   assert.equal(response.state,"CONFIRM");trace.states.push("CONFIRM");
   const choice="(()=>{const a=[...document.querySelectorAll('#task21-overlay select')];"+
     "if(a.length!==3)return false;"+
     "for(const [i,v] of [[0,"+JSON.stringify(scenario.type)+"],[1,"+JSON.stringify(scenario.subtype)+"],[2,"+JSON.stringify(scenario.goal)+"]])"+
     "{a[i].value=v;a[i].dispatchEvent(new Event('change',{bubbles:true}));}return true;})()";
   assert.ok(await evaluate(choice));
   await click("#task21-overlay button","Confirm and continue");
   const preferred={merchant_location:"singapore",purchase_purpose:"personal",
     consumer_context:"local_consumer",resolution_attempted:true,
     dispute_with:"landlord",premises_type:"private_residential",
     pass_event:"cancelled",break_clause_present:"unknown",lease_ended:false};
   for(let n=0;n<9;n++){
     await until("['questions','results','limited'].includes(document.querySelector('#problem-intake')?.dataset.flowStage)");
     const stage=await evaluate("document.querySelector('#problem-intake').dataset.flowStage");
     if(stage==="results")break;
     assert.equal(stage,"questions","A verified route should be available");
     response=await lastResponse();assert.equal(response.state,"ASK");
     const q=response.question;trace.states.push("ASK:"+q.field);
     let k=q.options.findIndex(x=>x.value===preferred[q.field]);
     if(k<0)k=q.options.findIndex(x=>x.value==="unknown");
     assert.ok(k>=0,"Not sure required");
     await evaluate("document.querySelectorAll('.task20-answer')["+k+"].click()");
     await click("#task21-overlay button","Continue");
   }
   assert.equal(await evaluate("document.querySelector('#problem-intake').dataset.flowStage"),"results");
   response=await lastResponse();assert.equal(response.state,"READY");
   trace.states.push("READY");
   assert.ok(response.plan?.evidence?.length);
   assert.ok(await evaluate("!!document.querySelector('.task20-first-grid')"));
   await screenshot(scenario.name,1440);await screenshot(scenario.name,390);
   await command("Emulation.setDeviceMetricsOverride",{width:320,height:850,deviceScaleFactor:1,mobile:true});
   assert.ok(await evaluate("document.documentElement.scrollWidth<=document.documentElement.clientWidth+1"));
   await click(".task20-first-right button","Official contacts");
   assert.ok(await evaluate("!document.getElementById('task21-overlay').hidden"));
   await click("#task21-overlay button","Back to next step");
   await click(".task20-first-right button","Why this advice?");
   assert.ok(await evaluate("document.querySelectorAll('#task21-overlay .task21-evidence blockquote').length>0"));
   await click("#task21-overlay button","Back to next step");
   await evaluate("document.getElementById('problem-text').dispatchEvent(new Event('input',{bubbles:true}))");
   assert.ok(await evaluate("document.getElementById('task21-result').hidden"));
   trace.passed=true;
 }
 report.passed=report.cases.every(x=>x.passed)&&report.screenshots.length===4;
}catch(error){report.errors.push(String(error.stack||error));process.exitCode=1;}
finally{
 report.finished=new Date().toISOString();
 await fs.writeFile(path.join(artifacts,"report.json"),JSON.stringify(report,null,2)+"\n");
 process.stdout.write("SGNAVI_TASK21_BROWSER_JSON="+JSON.stringify(report)+"\n");
 if(ws&&ws.readyState===WebSocket.OPEN){try{await command("Browser.close",{},false)}catch{}ws.close();}
 for(const p of pending.values()){clearTimeout(p.timeout);p.reject(Error("Browser finished"));}
 browser.kill();
}
