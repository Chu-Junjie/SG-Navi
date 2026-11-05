// Optional transport diagnostic: Node 22+ and a Chromium browser, no npm install.
// node frontend/tests/task7_candidate_demo.mjs [base-url] [browser-executable]
// Uses a real page and HTTP service; never intercepts or supplies API responses.
import assert from 'node:assert/strict';
import fs from 'node:fs/promises';
import path from 'node:path';
import {spawn} from 'node:child_process';

const base = new URL(process.argv[2] || 'http://127.0.0.1:5000');
if (!['127.0.0.1', 'localhost', '[::1]'].includes(base.hostname)) {
  throw Error('Use a loopback development service with synthetic data only.');
}
const executable = process.argv[3] || (process.platform === 'win32' ? 'C:\\Program Files (x86)\\Microsoft\\Edge\\Application\\msedge.exe' : '/usr/bin/google-chrome');
const artifacts = path.resolve('instance/task7-candidate-browser');
await fs.mkdir(artifacts, {recursive: true});
const profile = await fs.mkdtemp(path.join(artifacts, 'profile-'));
const browser = spawn(executable, [
  '--headless=new', '--no-sandbox', '--disable-gpu', '--disable-background-networking', '--disable-sync',
  '--no-first-run', '--no-default-browser-check', '--remote-debugging-port=0',
  `--user-data-dir=${profile}`, 'about:blank',
], {windowsHide: true, stdio: ['ignore', 'pipe', 'pipe']});
let browserLog = '', launchError;
browser.on('error', error => {launchError = error;});
for (const stream of [browser.stdout, browser.stderr]) {
  stream.on('data', data => {browserLog = (browserLog + data.toString()).slice(-2000);});
}
const delay = ms => new Promise(resolve => setTimeout(resolve, ms));
let ws, session, serial = 0;
const pending = new Map(), requests = [], responses = new Map(), exceptions = [];
function command(method, params = {}, attached = true) {
  const id = ++serial;
  return new Promise((resolve, reject) => {
    const timeout = setTimeout(() => {pending.delete(id); reject(Error('CDP timeout: ' + method));}, 6000);
    pending.set(id, {resolve, reject, timeout});
    ws.send(JSON.stringify({id, method, params, ...(attached && session ? {sessionId: session} : {})}));
  });
}
async function evaluate(expression) {
  const result = await command('Runtime.evaluate', {expression, returnByValue: true, awaitPromise: true});
  if (result.exceptionDetails) throw Error(JSON.stringify(result.exceptionDetails));
  return result.result.value;
}
async function until(expression) {
  for (let i = 0; i < 120; i++) {
    if (await evaluate(expression)) return;
    await delay(50);
  }
  throw Error('Timed out waiting for page: ' + expression);
}
const fixtures = JSON.parse(await fs.readFile(new URL('../../integration/fixtures.json', import.meta.url), 'utf8'));
async function submit() {
  const start = requests.length;
  await evaluate("document.getElementById('submit').click()");
  await until("!document.getElementById('submit').disabled");
  const captured = requests.slice(start);
  assert.equal(captured.filter(r => new URL(r.url).pathname.startsWith('/mocks/')).length, 0,
    'Submission must not load a Mock response');
  const navigation = captured.filter(r => new URL(r.url).pathname === '/api/navigate' && r.method === 'POST');
  assert.equal(navigation.length, 1, 'Exactly one real POST /api/navigate is required');
  const request = JSON.parse(navigation[0].body);
  assert.deepEqual(Object.keys(request).sort(), ['answers', 'api_version', 'case_type']);
  assert.equal(request.api_version, '1.0');
  assert.equal(responses.get(navigation[0].requestId), 200);
  const response = JSON.parse((await command('Network.getResponseBody', {requestId: navigation[0].requestId})).body);
  assert.equal(await evaluate("document.getElementById('status').textContent"), response.status);
  assert.equal(await evaluate("document.querySelectorAll('#card .card-section').length"), 7);
  return {request, response};
}
async function fill(field, value) {
  await evaluate(`(()=>{const select=document.getElementById(${JSON.stringify('input-' + field)});
    select.value=${JSON.stringify(typeof value === 'boolean' ? String(value) : '__value__')};
    select.dispatchEvent(new Event('change',{bubbles:true}));
    const detail=document.getElementById(${JSON.stringify('detail-' + field)});
    if(detail){detail.value=${JSON.stringify(String(value))};detail.dispatchEvent(new Event('input',{bubbles:true}));}})()`);
}

const result = {
  scope: "task7_candidate_real_browser", synthetic_facts: true,
  verified_official_path_claimed: false, is_production_release: false,
  run_started_at_utc: new Date().toISOString(),
  executed_commit: process.env.SG_NAVI_TEST_SHA || "unspecified",
  cases: [], screenshots: [], javascript_exceptions: 0,
  passed: false
};
try {
  let address;
  for (let i = 0; i < 200; i++) {
    if (launchError) throw launchError;
    try {address = (await fs.readFile(path.join(profile, 'DevToolsActivePort'), 'utf8')).trim().split(/\r?\n/); break;} catch {}
    if (browser.exitCode !== null && browser.exitCode !== 0) throw Error('Browser launch failed: ' + browserLog);
    await delay(50);
  }
  assert.ok(address, 'Browser DevTools endpoint available');
  ws = new WebSocket(`ws://127.0.0.1:${address[0]}${address[1]}`);
  await new Promise((resolve, reject) => {
    ws.addEventListener('open', resolve, {once: true});
    ws.addEventListener('error', reject, {once: true});
  });
  ws.addEventListener('message', event => {
    const message = JSON.parse(event.data);
    if (message.id && pending.has(message.id)) {
      const call = pending.get(message.id); pending.delete(message.id); clearTimeout(call.timeout);
      if (message.error) call.reject(Error(JSON.stringify(message.error))); else call.resolve(message.result);
    } else if (message.method === 'Network.requestWillBeSent') {
      const {requestId, request} = message.params;
      requests.push({requestId, url: request.url, method: request.method, body: request.postData});
    } else if (message.method === 'Network.responseReceived') {
      responses.set(message.params.requestId, message.params.response.status);
    } else if (message.method === 'Runtime.exceptionThrown') exceptions.push(message.params);
  });
  const target = await command('Target.createTarget', {url: 'about:blank'}, false);
  session = (await command('Target.attachToTarget', {targetId: target.targetId, flatten: true}, false)).sessionId;
  await command('Page.enable'); await command('Runtime.enable'); await command('Network.enable');
  await command('Page.navigate', {url: new URL('/', base).href});
  await until("document.querySelectorAll('[data-case]').length===2");


  async function untilReady() {
    await until("document.querySelectorAll('#dynamic-fields select').length === 9 && document.getElementById('submit').disabled === false");
  }
  async function clickHomeTopic(caseType) {
    const label = caseType === 'rental_deposit' ? "Rental Deposit" : "Consumer Complaint";
    await command('Page.navigate',{url:new URL('/',base).href});
    await until("document.querySelectorAll('[data-case]').length === 2");
    await until("document.getElementById('status-text').textContent.includes('Online')");
    const before = await evaluate("({path:location.pathname, label:document.querySelector('.choice-label').textContent.trim()})");
    await evaluate("document.querySelector('[data-case="+JSON.stringify(label)+"]').click()");
    await until("location.pathname === '/task5-flow.html' && document.querySelectorAll('#dynamic-fields select').length === 9");
    const chosen = await evaluate("({caseType:document.getElementById('case-type').value, path:location.pathname})");
    assert.equal(chosen.caseType,caseType,'Home card must select the correct case form');
    return {health:'Online',before,after:chosen};
  }
  async function submitReal() {
    const start = requests.length;
    await evaluate("document.getElementById('submit').click()");
    await until("!document.getElementById('submit').disabled");
    const captured = requests.slice(start);
    assert.equal(captured.filter(x=>new URL(x.url).pathname.startsWith('/mocks/')).length,0);
    const api = captured.filter(x=>new URL(x.url).pathname==='/api/navigate' && x.method==='POST');
    assert.equal(api.length,1,'Exactly one real backend API request must be sent');
    assert.equal(responses.get(api[0].requestId),200,'HTTP 200 expected for submitted synthetic data');
    const sent=JSON.parse(api[0].body);
    assert.deepEqual(Object.keys(sent).sort(),['answers','api_version','case_type']);
    const response=JSON.parse((await command('Network.getResponseBody',{requestId:api[0].requestId})).body);
    assert.equal(await evaluate("document.getElementById('status').textContent"),response.status);
    assert.equal(await evaluate("document.querySelectorAll('#card .card-section').length"),7);
    return {request:sent,response};
  }
  async function fillAnswer(field,value) {
    await evaluate('(()=>{const s=document.getElementById('+JSON.stringify('input-'+field)+');'
      +'if(!s)throw Error("Missing form field "+'+JSON.stringify(field)+');'
      +'s.value='+JSON.stringify(value===null?'__null__':value==='unknown'?'__unknown__':typeof value==='boolean'?String(value):'__value__')+';'
      +'s.dispatchEvent(new Event("change",{bubbles:true}));'
      +'const detail=document.getElementById('+JSON.stringify('detail-'+field)+');'
      +(value!==null&&value!=='unknown'&&typeof value!=='boolean'?'if(detail){detail.value='+JSON.stringify(String(value))+';detail.dispatchEvent(new Event("input",{bubbles:true}));}':'')
      +'})()');
  }
  async function addStep(trace,id,action,expected,runner) {
    const entry={id,action,expected,result:'FAIL'};
    trace.steps.push(entry);
    try {
      entry.actual=await runner();
      entry.result='PASS';
      console.log("TASK7_STEP "+trace.case_type+" "+id+" PASS "+JSON.stringify(entry.actual));
    } catch(error) {
      entry.error=error.stack || String(error);
      console.log("TASK7_STEP "+trace.case_type+" "+id+" FAIL "+String(error));
      throw error;
    }
  }
  async function screenshot(caseType,viewport) {
    const suffix=viewport==='desktop'?'desktop-1440':'mobile-390';
    const name=caseType+"-"+suffix+".jpg";
    if(viewport==='mobile'){
      await command('Emulation.setDeviceMetricsOverride',{width:390,height:844,deviceScaleFactor:1,mobile:true});
    } else await command('Emulation.setDeviceMetricsOverride',{width:1440,height:900,deviceScaleFactor:1,mobile:false});
    await delay(180);
    const metrics=await evaluate("({viewport:window.innerWidth,scrollWidth:document.documentElement.scrollWidth,clientWidth:document.documentElement.clientWidth,bodyHeight:document.body.scrollHeight,sourceVisible:!document.getElementById('verified-source-context').hidden})");
    assert.ok(metrics.scrollWidth<=metrics.clientWidth+1,JSON.stringify(metrics));
    assert.equal(metrics.sourceVisible,true);
    const shot=await command('Page.captureScreenshot',{format:'jpeg',quality:62,captureBeyondViewport:true,fromSurface:true});
    const bytes=Buffer.from(shot.data,'base64');
    assert.ok(bytes.length>6500,'Screenshot image too small or empty');
    await fs.writeFile(path.join(artifacts,name),bytes);
    result.screenshots.push({name,bytes:bytes.length,case_type:caseType,viewport,metrics});
    if(process.env.SG_NAVI_EXPORT_SCREENSHOTS==='1'){
      const chunkSize=3200,total=Math.ceil(shot.data.length/chunkSize);
      console.log("SGNAVI_SHOT_START "+name+" "+total+" "+bytes.length);
      for(let n=0;n<total;n++){
        console.log("SGNAVI_SHOT_CHUNK "+name+" "+(n+1)+"/"+total+" "+shot.data.slice(n*chunkSize,(n+1)*chunkSize));
      }
      console.log("SGNAVI_SHOT_END "+name);
    }
    return {name,bytes:bytes.length,...metrics};
  }
  async function checkSourceContext(response) {
    assert.equal(response.status,'REFER_TO_OFFICIAL');
    assert.equal(response.action_card,null);
    assert.ok(response.evidence.length>0,'Real RAG must supply reviewed source context');
    assert.ok(response.evidence.every(e=>e.review_status==='verified'&&e.source_version===response.source_version));
    const links=await evaluate("Array.from(document.querySelectorAll('#verified-source-list a[href]'),e=>({href:e.href,target:e.target,rel:e.rel,text:e.textContent}))");
    assert.equal(links.length,response.evidence.length);
    for(const evidence of response.evidence){
      assert.ok(links.some(x=>x.href===new URL(evidence.url).href&&x.text.includes('official website')),evidence.evidence_id);
    }
    assert.ok(links.every(x=>x.target==='_blank'&&x.rel.includes('noopener')&&x.rel.includes('noreferrer')));
    const disclaimer=await evaluate("document.querySelector('#verified-source-context .source-note').textContent");
    assert.ok(disclaimer.includes('do not establish legal eligibility'));
    const cards=await evaluate("Array.from(document.querySelectorAll('#card .card-section'),x=>({name:x.querySelector('h3')?.textContent,text:x.textContent}))");
    assert.equal(cards.length,7);
    assert.ok(cards.some(x=>x.text.includes('Needs verification')),'Incomplete legal guidance must be marked');
    return {status:response.status,rule_version:response.rule_version,source_version:response.source_version,evidence:response.evidence.map(e=>({evidence_id:e.evidence_id,source_id:e.source_id,review_status:e.review_status,source_version:e.source_version,url:e.url})),clickable_links:links,card_sections:cards.map(x=>x.name),disclaimer};
  }

  for(const kind of ['rental_deposit','consumer_complaint']){
    const trace={case_type:kind,steps:[],passed:false};
    result.cases.push(trace);
    try{
      await addStep(trace,'01','Start on candidate homepage; select topic','Real health online; card opens correct real form',async()=>clickHomeTopic(kind));
      const first=await addStep(trace,'02','Submit all Not provided','Real NEED_CLARIFICATION; 9 schema fields; seven unavailable sections',async()=>{
        const r=await submitReal();
        assert.equal(r.response.status,'NEED_CLARIFICATION');
        assert.equal(Object.keys(r.request.answers).length,9);
        assert.equal(r.response.action_card,null);
        return {request_case:r.request.case_type,status:r.response.status,question_ids:r.response.questions.map(q=>q.id),seven_sections:7};
      });
      await addStep(trace,'03','Follow backend questions, enter nine synthetic case facts','Question jumps to matching input; backend gets actual edited fields',async()=>{
        const qid=await evaluate("document.querySelector('#questions button')?.closest('.question')?.querySelector('span')?.textContent");
        assert.ok(qid);
        await evaluate("document.querySelector('#questions button').click()");
        const focus=await evaluate("document.activeElement.id");
        assert.ok(focus.startsWith('input-'));
        for(const [field,value] of Object.entries(fixtures[kind].answers))await fillAnswer(field,value);
        const values=await evaluate("Array.from(document.querySelectorAll('#dynamic-fields select'),e=>e.name)");
        assert.equal(values.length,9);
        return {first_question_label:qid,focused_field:focus,entered_synthetic_fields:values};
      });
      let referral;
      await addStep(trace,'04','Submit complete facts to actual backend and RAG','REFER_TO_OFFICIAL; seven sections; reviewed source links; not legal eligibility',async()=>{
        const r=await submitReal();
        assert.equal(r.request.case_type,kind);
        assert.deepEqual(r.request.answers,fixtures[kind].answers);
        referral=await checkSourceContext(r.response);
        return referral;
      });
      await addStep(trace,'05','Capture actual desktop screenshot','1440px browser screenshot including evidence and seven blocks',async()=>screenshot(kind,'desktop'));
      await addStep(trace,'06','Check mobile and capture screenshot','390px screenshot and 320px no horizontal overflow',async()=>{
        const mobile=await screenshot(kind,'mobile');
        await command('Emulation.setDeviceMetricsOverride',{width:320,height:780,deviceScaleFactor:1,mobile:true});
        const width=await evaluate("({width:innerWidth,scroll:document.documentElement.scrollWidth,client:document.documentElement.clientWidth})");
        assert.ok(width.scroll<=width.client+1,JSON.stringify(width));
        await command('Emulation.clearDeviceMetricsOverride');
        return {mobile,small_phone:width};
      });
      await addStep(trace,'07','Edit answer and re-submit','Old evidence disappears until fresh backend response; changed amount sent',async()=>{
        await fillAnswer('claim_amount_sgd',456);
        assert.equal(await evaluate("document.querySelectorAll('#verified-source-list a[href]').length"),0);
        const r=await submitReal();
        assert.equal(r.request.answers.claim_amount_sgd,456);
        assert.equal(r.response.status,'REFER_TO_OFFICIAL');
        return {edited_amount:r.request.answers.claim_amount_sgd,status:r.response.status,source_count:r.response.evidence.length};
      });
      await addStep(trace,'08','Block backend call then restore','Service unavailable; stale links removed; answer retained; retry successful',async()=>{
        await command('Network.setBlockedURLs',{urls:['*api/navigate*']});
        try{
          await evaluate("document.getElementById('submit').click()");
          await until("document.getElementById('status').textContent==='Service unavailable'");
          assert.equal(await evaluate("document.querySelectorAll('#verified-source-list a[href]').length"),0);
          assert.equal(await evaluate("document.getElementById('detail-claim_amount_sgd').value"),'456');
        }finally{await command('Network.setBlockedURLs',{urls:[]});}
        const r=await submitReal();
        assert.equal(r.request.answers.claim_amount_sgd,456);
        assert.equal(r.response.status,'REFER_TO_OFFICIAL');
        return {offline:'Service unavailable',preserved_amount:456,retry_status:r.response.status};
      });
      await addStep(trace,'09','Click header return to homepage','Candidate form return link reaches actual homepage',async()=>{
        await evaluate("document.querySelector('.head a').click()");
        await until("location.pathname==='/' && document.querySelectorAll('[data-case]').length===2");
        return {pathname:await evaluate("location.pathname")};
      });
      trace.passed=trace.steps.length===9 && trace.steps.every(x=>x.result==='PASS');
    }catch(error){trace.error=error.stack||String(error);}
  }
  result.javascript_exceptions=exceptions.length;
  result.passed=result.cases.length===2 && result.cases.every(c=>c.passed) && !result.javascript_exceptions;
} catch(error){result.error=error.stack||String(error);}
finally{
  if(ws?.readyState===WebSocket.OPEN){try{await command('Browser.close',{},false);}catch{}ws.close();}
  else browser.kill();
}
console.log("SGNAVI_TASK7_JSON="+JSON.stringify(result));
process.exitCode=result.passed?0:1;
