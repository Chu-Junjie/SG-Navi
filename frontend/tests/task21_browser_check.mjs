// Actual keyboard/DOM -> real HTTP APIs. No API interception or supplied replies.
import assert from 'node:assert/strict';
import fs from 'node:fs/promises';
import path from 'node:path';
import {spawn} from 'node:child_process';
import {createHash,webcrypto} from 'node:crypto';
import {createRequire} from 'node:module';

const {verifyResponse,reviewedDisplay,summaryForContext}=createRequire(import.meta.url)('../js/task21-live.js');

const base=new URL(process.argv[2]||'http://127.0.0.1:5000/');
const publicRun=base.protocol==='https:';
assert.ok(publicRun?base.href==='https://chu-junjie.github.io/SG-Navi/':base.hostname==='127.0.0.1'&&base.protocol==='http:');
const apiOrigin=publicRun?'https://sg-navi-api-junjie.onrender.com':base.origin;
const extended=process.argv.includes('--extended');
const isActionPlan=request=>request.method==='POST'&&new URL(request.url).origin===apiOrigin&&
 ['/api/action-plan','/api/action-plan/zh-hans-reviewed'].includes(new URL(request.url).pathname);
const executable=process.argv[3]||(process.platform==='win32'?'C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe':'/usr/bin/google-chrome');
const artifacts=path.resolve('instance/task21-browser-'+(publicRun?'public':'local'));
await fs.mkdir(artifacts,{recursive:true});
const profile=await fs.mkdtemp(path.join(artifacts,'profile-'));
const browser=spawn(executable,['--headless=new','--no-sandbox','--disable-gpu','--disable-dev-shm-usage','--disable-background-networking','--disable-sync','--no-first-run','--no-default-browser-check','--remote-debugging-port=0',`--user-data-dir=${profile}`,'about:blank'],{windowsHide:true,stdio:['ignore','pipe','pipe']});
let browserLog='',launchError,ws,session,serial=0;
browser.on('error',e=>{launchError=e;});for(const stream of [browser.stdout,browser.stderr])stream.on('data',d=>{browserLog=(browserLog+d.toString()).slice(-1800);});
const pending=new Map(),requests=[],responses=new Map(),finished=new Set(),exceptions=[];
const networkFailures=[];
const delay=ms=>new Promise(r=>setTimeout(r,ms));
function command(method,params={},attached=true){const id=++serial;return new Promise((resolve,reject)=>{const timeout=setTimeout(()=>{pending.delete(id);reject(Error('CDP timeout '+method));},30000);pending.set(id,{resolve,reject,timeout});ws.send(JSON.stringify({id,method,params,...(attached&&session?{sessionId:session}:{})}));});}
async function evaluate(expression){const r=await command('Runtime.evaluate',{expression,returnByValue:true,awaitPromise:true});if(r.exceptionDetails)throw Error(JSON.stringify(r.exceptionDetails));return r.result.value;}
async function until(expression,seconds=60){for(let n=0;n<seconds*10;n++){if(await evaluate(expression))return;await delay(100);}throw Error('Timed out: '+expression);}
async function enter(id){await evaluate(`document.getElementById(${JSON.stringify(id)}).focus()`);await command('Input.dispatchKeyEvent',{type:'keyDown',key:'Enter',code:'Enter',text:'\r',unmodifiedText:'\r',windowsVirtualKeyCode:13,nativeVirtualKeyCode:13});await command('Input.dispatchKeyEvent',{type:'keyUp',key:'Enter',code:'Enter',windowsVirtualKeyCode:13,nativeVirtualKeyCode:13});}

const report={scope:publicRun?"task21_actual_published_browser":"task21_actual_local_browser",
 extended,passed:false,cases:[],screenshots:[],matrix:[],wire:[],errors:[],started:new Date().toISOString()};
async function click(selector,text){
 const expr="(()=>{const b=[...document.querySelectorAll("+JSON.stringify(selector)+")].find(x=>x.textContent.includes("+JSON.stringify(text)+"));if(!b)return false;b.focus();b.click();return true;})()";
 assert.ok(await evaluate(expr),"Missing button: "+text);
}
// Exercise locale/state invariants without adding another switch inside the modal.
// Users choose their language on the homepage before opening a dialog.
async function dialogLanguage(language){
 assert.equal(await evaluate("document.querySelectorAll('#task21-overlay [data-task23-language]').length"),0,
   "Dialogs must not duplicate the homepage language controls");
 await evaluate(`window.SGNaviLocale.setLanguage(${JSON.stringify(language)})`);
}
async function lastResponse(){
 const req=requests.filter(isActionPlan).at(-1);
 assert.ok(req,"Actual Action Plan POST required");
 for(let n=0;n<120&&!finished.has(req.id);n++)await delay(50);
 assert.equal(responses.get(req.id),200);
 const wire=await command("Network.getResponseBody",{requestId:req.id});
 const envelope=JSON.parse(wire.base64Encoded?Buffer.from(wire.body,"base64").toString():wire.body);
 const reviewed=new URL(req.url).pathname.endsWith('zh-hans-reviewed');
 const data=reviewed?envelope.canonical:envelope;
 await verifyResponse(data,JSON.parse(req.body),webcrypto);
 if(reviewed)assert.ok(reviewedDisplay(envelope),'Actual reviewed response must pass identity/coverage checks');
 if(!report.wire.some(row=>row.requestId===data.request_id))report.wire.push({
   path:new URL(req.url).pathname,http:200,state:data.state,requestId:data.request_id,
   revision:data.revision,reviewed,sourceVersion:data.plan?.source_version??null,
   evidence:data.plan?.evidence.map(({id,url,quote_sha256})=>({id,url,quote_sha256}))??[]
 });
 return data;
}
async function screenshot(name,width,height=850){
 await command("Emulation.setDeviceMetricsOverride",{width,height,deviceScaleFactor:1,mobile:width<700});
 await delay(150);
 const sizes=await evaluate("({w:document.documentElement.clientWidth,s:document.documentElement.scrollWidth,h:document.documentElement.scrollHeight})");
 assert.ok(sizes.s<=sizes.w+1,"Mobile horizontal overflow");
 const pic=await command("Page.captureScreenshot",{format:"jpeg",quality:68,
   captureBeyondViewport:true,clip:{x:0,y:0,width:sizes.w,height:Math.min(sizes.h,1500),scale:1}});
 const bytes=Buffer.from(pic.data,"base64"),file=name+"-"+width+".jpg";
 await fs.writeFile(path.join(artifacts,file),bytes);
 report.screenshots.push({file,width,height,bytes:bytes.length,digest:createHash("sha256").update(bytes).digest("hex")});
}
async function key(name,modifiers=0){
 const codes={Tab:9,Escape:27};
 for(const type of ['keyDown','keyUp'])await command('Input.dispatchKeyEvent',{
   type,key:name,code:name,modifiers,windowsVirtualKeyCode:codes[name],nativeVirtualKeyCode:codes[name]
 });
}
async function layoutMatrix(name,resultView){
 for(const language of ['en','zh']){
   await evaluate(`document.querySelector('.site-header [data-task23-language="${language}"]').click()`);
   for(const [width,height] of [[1366,768],[1440,900],[320,850],[390,850],[683,384]]){
     if(resultView)await evaluate("document.getElementById('task21-result').scrollTop=0");
     const capture=`${name}-${language}-${width===683?'zoom-layout-200':'layout'}`;
     await screenshot(capture,width,height);
     const metrics=await evaluate(`(()=>{
       const root=document.documentElement;
       const button=document.querySelector(${JSON.stringify(resultView?'.task20-primary .intake-primary':'#problem-submit')});
       const rect=button.getBoundingClientRect();
       return {width:root.clientWidth,height:innerHeight,scrollWidth:root.scrollWidth,
         scrollHeight:root.scrollHeight,action:{top:rect.top,bottom:rect.bottom,left:rect.left,right:rect.right},
         language:root.lang};
     })()`);
     assert.ok(metrics.scrollWidth<=metrics.width+1,'Horizontal overflow in '+capture);
     assert.ok(metrics.action.left>=0&&metrics.action.right<=metrics.width+1,'Clipped action in '+capture);
     if(width>700){
       assert.ok(metrics.action.top>=0&&metrics.action.bottom<=height,'Desktop action needs scrolling in '+capture);
       assert.ok(metrics.scrollHeight<=height+1,'Desktop outer-page scroll in '+capture);
     }
     report.matrix.push({name,language,width,height,...metrics,
       zoom:width===683?'200% equivalent layout at half CSS viewport; native browser zoom NOT RUN':'100%'});
   }
 }
 await command('Emulation.setDeviceMetricsOverride',{width:1440,height:900,deviceScaleFactor:1,mobile:false});
 await evaluate("document.querySelector('.site-header [data-task23-language=en]').click()");
}
async function keyboardDialog(){
 const controls="[...document.querySelector('#task21-overlay [role=dialog]').querySelectorAll('button:not([disabled]),input:not([disabled]),select:not([disabled]),textarea:not([disabled]),a[href]')].filter(el=>el.getClientRects().length)";
 await evaluate(`(${controls}).at(-1).focus()`);
 await key('Tab');
 assert.ok(await evaluate(`document.activeElement===(${controls})[0]`),'Tab must stay inside dialog');
 await key('Tab',8);
 assert.ok(await evaluate(`document.activeElement===(${controls}).at(-1)`),'Shift+Tab must stay inside dialog');
 await key('Escape');
 assert.ok(await evaluate("document.getElementById('task21-overlay').hidden"),'Escape closes dialog');
 assert.ok(await evaluate("document.activeElement.classList.contains('task23-process-trigger')"),'Escape returns focus');
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
   if(d.method==="Network.loadingFailed")networkFailures.push({id:x.requestId,error:x.errorText});
   if(d.method==="Runtime.exceptionThrown")exceptions.push(x.exceptionDetails?.text||'JavaScript exception');
 };
 const targets=await command("Target.getTargets",{},false);
 session=(await command("Target.attachToTarget",{targetId:targets.targetInfos.find(t=>t.type==="page").targetId,flatten:true},false)).sessionId;
 for(const m of ["Page.enable","Runtime.enable","Network.enable"])await command(m);
 for(const scenario of [
  {name:"restaurant",description:"The restaurant in Singapore charged me SGD 20 extra and refuses to refund it.",type:"consumer_complaint",subtype:"restaurant_overcharge",goal:"complain"},
  {name:"rental_pass",description:"My work pass was cancelled and I must leave my private condo early. My landlord will not refund my rental deposit.",type:"rental_deposit",subtype:"pass_related_exit",goal:"seek_refund"}
 ]){
   const trace={name:scenario.name,states:[],passed:false};report.cases.push(trace);
   await command("Emulation.setDeviceMetricsOverride",{width:1440,height:850,deviceScaleFactor:1,mobile:false});
   await command("Page.navigate",{url:base.href});
   await until("document.querySelector('#problem-intake')?.dataset.task21Ready==='true'");
   if(extended&&scenario.name==='restaurant')await layoutMatrix('homepage',false);
   await evaluate("document.getElementById('problem-text').focus()");
   await command("Input.insertText",{text:scenario.description});
   await enter("problem-submit");
   await until("document.querySelector('#problem-intake')?.dataset.flowStage==='review'");
   let response=await lastResponse();
   assert.equal(response.state,"CONFIRM");trace.states.push("CONFIRM");
   const choice="(()=>{const a=[...document.querySelectorAll('#task21-overlay select')];"+
     "if(a.length<3)return false;"+
     "for(const [i,v] of [[0,"+JSON.stringify(scenario.type)+"],[1,"+JSON.stringify(scenario.subtype)+"],[2,"+JSON.stringify(scenario.goal)+"]])"+
     "{const el=document.querySelectorAll('#task21-overlay select')[i];if(!el)return false;"+
     "if(el.value!==v){el.value=v;el.dispatchEvent(new Event('change',{bubbles:true}));}}return true;})()";
   assert.ok(await evaluate(choice));
   const values="[...document.querySelectorAll('#task21-overlay select')].map(select=>select.value)";
   const actionRequestCount=()=>requests.filter(isActionPlan).length;
   const selected=await evaluate(values),requestCount=actionRequestCount();
   await dialogLanguage("zh");
   assert.equal(await evaluate("document.documentElement.lang"),"zh-Hans");
   assert.deepEqual(await evaluate(values),selected);
   assert.ok(await evaluate("document.querySelector('#task21-overlay select').selectedOptions[0].textContent.includes('纠纷')"));
   const confirmedSummary=summaryForContext({case_type:scenario.type,issue_subtype:scenario.subtype,goal:scenario.goal});
   const summaryText=`[...document.querySelectorAll('#task21-overlay p')].find(el=>el.dataset.task23Original===${JSON.stringify(confirmedSummary)})?.textContent`;
   assert.match(await evaluate(summaryText),/\p{Script=Han}/u,"Known confirmation summary should display in Chinese");
   assert.equal(await evaluate("!!document.querySelector('#task23-dialog-translation-notice:not([hidden])')"),false);
   await dialogLanguage("en");
   assert.equal(await evaluate(summaryText),confirmedSummary);
   assert.deepEqual(await evaluate(values),selected);
   assert.equal(actionRequestCount(),requestCount,"Changing the display language must not send a request");
   await click("#task21-overlay button","Confirm and continue");
   const preferred={merchant_location:"singapore",purchase_purpose:"personal",
     consumer_context:"local_consumer",resolution_attempted:true,
     dispute_with:"landlord",premises_type:"private_residential",
     pass_event:"cancelled",break_clause_present:"unknown",lease_ended:false};
   for(let n=0;n<9;n++){
     await until("['questions','results','limited'].includes(document.querySelector('#problem-intake')?.dataset.flowStage)");
     const stage=await evaluate("document.querySelector('#problem-intake').dataset.flowStage");
     if(stage==="results")break;
     if(stage!=="questions"){
       const last=await lastResponse();
       trace.diagnostic={state:stage,apiState:last.state,reason:last.reason,apiMessage:last.message,
         ui:await evaluate("document.getElementById('task21-result')?.textContent.slice(0,700)")};
       throw Error("Action Plan stopped for "+scenario.name+" at "+JSON.stringify(trace.diagnostic));
     }
     response=await lastResponse();assert.equal(response.state,"ASK");
     const q=response.question;trace.states.push("ASK:"+q.field);
     let k=q.options.findIndex(x=>x.value===preferred[q.field]);
     if(k<0)k=q.options.findIndex(x=>x.value==="unknown");
     assert.ok(k>=0,"Not sure required");
     await evaluate("document.querySelectorAll('.task20-answer')["+k+"].click()");
     await dialogLanguage("zh");
     assert.equal(await evaluate("document.querySelectorAll('.task20-answer')["+k+"].getAttribute('aria-pressed')"),"true");
     assert.match(await evaluate("document.querySelector('#task21-overlay h2').textContent"),/\p{Script=Han}/u);
     await dialogLanguage("en");
     await click("#task21-overlay button","Continue");
   }
   assert.equal(await evaluate("document.querySelector('#problem-intake').dataset.flowStage"),"results");
   response=await lastResponse();assert.equal(response.state,"READY");
   trace.states.push("READY");
   assert.ok(response.plan?.evidence?.length);
   assert.ok(await evaluate("!!document.querySelector('.task20-first-grid')"));
   await screenshot(scenario.name,1440);await screenshot(scenario.name,390);
   if(extended)await layoutMatrix(scenario.name,true);
   await command("Emulation.setDeviceMetricsOverride",{width:320,height:850,deviceScaleFactor:1,mobile:true});
   assert.ok(await evaluate("document.documentElement.scrollWidth<=document.documentElement.clientWidth+1"));
   await click(".task20-first-right button","Official contacts");
   assert.ok(await evaluate("!document.getElementById('task21-overlay').hidden"));
   await click("#task21-overlay button","Continue to next step");
   await evaluate("document.querySelector('.task20-primary button').click()");
   assert.equal(await evaluate("[...document.querySelectorAll('#task21-overlay button')].filter(b=>b.textContent==='View supporting sources').length"),1,
     "Preparation dialog should have one supporting-sources entry");
   await click("#task21-overlay button","View supporting sources");
   assert.ok(await evaluate("document.querySelectorAll('#task21-overlay .task21-evidence blockquote').length>0"));
   await click("#task21-overlay button","Continue to next step");
   await click(".task20-first-right button","View available steps");
   if(extended){
     await keyboardDialog();
     await click(".task20-first-right button","View available steps");
     trace.keyboardFocusAndEscape=true;
   }
   assert.ok(await evaluate("document.querySelectorAll('#task21-overlay .task23-step input[type=checkbox]').length>0"));
   await evaluate("document.querySelector('#task21-overlay .task23-step input[type=checkbox]').click()");
   assert.ok(await evaluate("document.querySelector('.task23-progress').textContent.includes('1 /')"));
   await click("#task21-overlay button","Continue to next step");
   await click(".task20-first-right button","View available steps");
   assert.ok(await evaluate("document.querySelector('#task21-overlay .task23-step input[type=checkbox]').checked"));
   await dialogLanguage("zh");
   assert.equal(await evaluate("document.documentElement.lang"),"zh-Hans");
   assert.ok(await evaluate("document.querySelector('#task21-overlay .task23-step input[type=checkbox]').checked"));
   await dialogLanguage("en");
   assert.equal(await evaluate("document.documentElement.lang"),"en");
   await click("#task21-overlay button","Continue to next step");
   await click(".task20-first-right button","Why this advice?");
   assert.ok(await evaluate("document.querySelectorAll('#task21-overlay .task21-evidence blockquote').length>0"));
   const excerpts="[...document.querySelectorAll('#task21-overlay .task21-evidence')].map(el=>[el.querySelector('blockquote').textContent,el.querySelector('a').href])";
   const original=await evaluate(excerpts);
   await dialogLanguage("zh");
   assert.deepEqual(await evaluate(excerpts),original);
   await dialogLanguage("en");
   await click("#task21-overlay button","Continue to next step");
   if(extended&&response.plan.draft){
     await click('.task20-first-right button','Write a request');
     const edited='Synthetic editable draft for '+scenario.name;
     await evaluate(`(()=>{const field=document.querySelector('.task21-draft');field.value=${JSON.stringify(edited)};field.dispatchEvent(new Event('input',{bubbles:true}));})()`);
     await dialogLanguage('zh');
     assert.equal(await evaluate("document.querySelector('.task21-draft').value"),edited);
     await dialogLanguage('en');
     assert.equal(await evaluate("document.querySelector('.task21-draft').value"),edited);
     await click('#task21-overlay button','Continue to next step');
     trace.editedDraftPreserved=true;
   }
   if(extended){
     const facts=response.context.facts;
     await command('Network.emulateNetworkConditions',{offline:true,latency:0,downloadThroughput:-1,uploadThroughput:-1});
     await click('#task21-result button','Check again');
     await until("document.querySelector('#problem-intake').dataset.flowStage==='limited'");
     assert.match(await evaluate("document.getElementById('task21-result').textContent"),/retry|unavailable/i);
     await command('Network.emulateNetworkConditions',{offline:false,latency:0,downloadThroughput:-1,uploadThroughput:-1});
     await click('#task21-result button','Check again');
     await until("document.querySelector('#problem-intake').dataset.flowStage==='results'");
     const recovered=await lastResponse();
     assert.deepEqual(recovered.context.facts,facts,'Offline retry must preserve typed answers');
     trace.offlineRetryPreservedAnswers=true;
   }
   await evaluate("document.getElementById('problem-text').dispatchEvent(new Event('input',{bubbles:true}))");
   assert.ok(await evaluate("document.getElementById('task21-result').hidden"));
   if(extended){
     await command('Network.emulateNetworkConditions',{offline:false,latency:1000,downloadThroughput:-1,uploadThroughput:-1});
     const beforeAbort=actionRequestCount();
     await enter('problem-submit');
     for(let n=0;n<30&&actionRequestCount()===beforeAbort;n++)await delay(50);
     assert.ok(actionRequestCount()>beforeAbort,'Slow request started');
     await evaluate("(()=>{const field=document.getElementById('problem-text');field.value='A new synthetic description.';field.dispatchEvent(new Event('input',{bubbles:true}));})()");
     await delay(1200);
     assert.ok(await evaluate("document.getElementById('task21-result').hidden&&document.getElementById('task21-overlay').hidden&&document.getElementById('problem-intake').dataset.flowStage==='input'"),'Late response must not restore the old case');
     await command('Network.emulateNetworkConditions',{offline:false,latency:0,downloadThroughput:-1,uploadThroughput:-1});
     trace.slowRequestEditInvalidation=true;
     assert.ok(await evaluate("localStorage.length===0&&sessionStorage.length===0"),'No dispute storage');
     assert.ok(requests.every(request=>!request.url.includes(encodeURIComponent(scenario.description))),'No dispute in URLs');
     trace.noBrowserStorageOrDescriptionInUrls=true;
     const history=await command('Page.getNavigationHistory');
     const previous=history.entries[history.currentIndex];
     await command('Page.navigate',{url:base.href+'?acceptance-navigation=1'});
     await until("document.querySelector('#problem-intake')?.dataset.task21Ready==='true'");
     await command('Page.navigateToHistoryEntry',{entryId:previous.id});
     await until(`location.href===${JSON.stringify(previous.url)}&&document.querySelector('#problem-intake')?.dataset.task21Ready==='true'`);
     trace.browserHistoryBack=true;
   }
   trace.passed=true;
 }
 report.passed=report.cases.every(x=>x.passed)&&report.screenshots.length===(extended?34:4)&&exceptions.length===0;
 assert.ok(report.passed,'Browser acceptance incomplete');
}catch(error){
 report.errors.push(String(error.stack||error));process.exitCode=1;
 try{report.failurePage=await evaluate("({url:location.href,title:document.title,text:document.body?.innerText.slice(0,1500)})");}catch{}
}
finally{
 report.javascriptExceptions=exceptions;report.networkFailures=networkFailures;
 report.finished=new Date().toISOString();
 await fs.writeFile(path.join(artifacts,"report.json"),JSON.stringify(report,null,2)+"\n");
 process.stdout.write("SGNAVI_TASK21_BROWSER_JSON="+JSON.stringify(report)+"\n");
 if(ws&&ws.readyState===WebSocket.OPEN){try{await command("Browser.close",{},false)}catch{}ws.close();}
 for(const p of pending.values()){clearTimeout(p.timeout);p.reject(Error("Browser finished"));}
 browser.kill();
}
