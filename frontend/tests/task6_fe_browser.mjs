// Optional transport diagnostic: Node 22+ and a Chromium browser, no npm install.
// node integration/browser_check.mjs [base-url] [browser-executable]
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
const artifacts = path.resolve('instance/task6-frontend-browser');
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
  scope: 'task6_fe_01_08_real_chromium', synthetic_facts: true,
  supported_legal_path_checked: false, passed: false, checks: [],
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
  await command('Page.navigate', {url: new URL('/task5-flow.html', base).href});
  await until("document.querySelectorAll('#dynamic-fields select').length===9");

  const check = async (id, name, expected, fn) => {
    const row = {id, name, expected, result: 'FAIL'};
    try {row.actual = await fn(); row.result = 'PASS';}
    catch (error) {row.actual = error.stack || String(error);}
    result.checks.push(row);
    console.log(id + ' ' + row.result + ': ' + (row.result === 'FAIL' ? row.actual.split('\n')[0] : JSON.stringify(row.actual)));
  };
  async function reloadPage() {
    await command('Page.reload', {ignoreCache:true});
    await until("document.querySelectorAll('#dynamic-fields select').length===9 && document.getElementById('submit').disabled===false");
  }
  async function choose(kind) {
    await evaluate('(()=>{const el=document.getElementById("case-type");el.value='+JSON.stringify(kind)+';el.dispatchEvent(new Event("change",{bubbles:true}));})()');
    await until("document.querySelectorAll('#dynamic-fields select').length===9");
  }
  async function answer(field,value) {
    await evaluate('(()=>{const s=document.getElementById('+JSON.stringify('input-'+field)+');'
     +'s.value='+JSON.stringify(value===null?'__null__':value==='unknown'?'__unknown__':typeof value==='boolean'?String(value):'__value__')+';'
     +'s.dispatchEvent(new Event("change",{bubbles:true}));'
     +'const detail=document.getElementById('+JSON.stringify('detail-'+field)+');'
     +(value!==null && value!=='unknown' && typeof value!=='boolean' ? 'if(detail){detail.value='+JSON.stringify(String(value))+';detail.dispatchEvent(new Event("input",{bubbles:true}));}' : '')+'})()');
  }
  async function complete(kind) {
    for(const [field,value] of Object.entries(fixtures[kind].answers))await answer(field,value);
    return submit();
  }

  await check('FE-01','Rental initial form + backend clarification','9 schema controls, real NEED_CLARIFICATION and keyboard-focusable follow-up',async()=>{
    await reloadPage();await choose('rental_deposit');
    const first=await submit();
    assert.equal(first.response.status,'NEED_CLARIFICATION');
    assert.equal(first.response.action_card,null);
    assert.equal(Object.keys(first.request.answers).length,9);
    await evaluate("document.querySelector('#questions button').click()");
    assert.equal(await evaluate("document.activeElement.id"),"input-"+first.response.questions[0].id);
    return {status:first.response.status,fields:9,focus:true};
  });
  await check('FE-02','Consumer initial form + backend clarification','9 consumer controls, real NEED_CLARIFICATION',async()=>{
    await reloadPage();await choose('consumer_complaint');
    const first=await submit();
    assert.equal(first.response.status,'NEED_CLARIFICATION');
    assert.equal(Object.keys(first.request.answers).length,9);
    return {status:first.response.status,fields:9};
  });
  await check('FE-03','Unknown, false and absent amount stay separate','unknown string, false boolean, null amount, clarification instead of a guessed amount',async()=>{
    await reloadPage();await choose('rental_deposit');
    await answer('dispute_with','unknown');
    await answer('resolution_attempted',false);
    await answer('documents_available','unknown');
    const r=await submit();
    assert.equal(r.request.answers.dispute_with,'unknown');
    assert.equal(r.request.answers.resolution_attempted,false);
    assert.equal(r.request.answers.documents_available,'unknown');
    assert.equal(r.request.answers.claim_amount_sgd,null);
    assert.equal(r.response.status,'NEED_CLARIFICATION');
    assert.ok(r.response.questions.some(q=>q.id==='claim_amount_sgd'));
    return {status:r.response.status,amount:r.request.answers.claim_amount_sgd,unknown:r.request.answers.dispute_with,falseValue:r.request.answers.resolution_attempted};
  });
  await check('FE-04','Complete rental + edit, refresh and preserve previous answers','real referral, source stale links removed on edit, revised amount sent, draft survives switch',async()=>{
    await reloadPage();await choose('rental_deposit');
    const r=await complete('rental_deposit');
    assert.equal(r.response.status,'REFER_TO_OFFICIAL');
    assert.equal(r.response.action_card,null);
    const initialLinks=await evaluate("document.querySelectorAll('#verified-source-list a[href]').length");
    assert.ok(initialLinks>0);
    await answer('claim_amount_sgd',456);
    assert.equal(await evaluate("document.querySelectorAll('#verified-source-list a[href]').length"),0);
    const edited=await submit();
    assert.equal(edited.request.answers.claim_amount_sgd,456);
    await choose('consumer_complaint');await choose('rental_deposit');
    const preserved=await evaluate("document.getElementById('detail-claim_amount_sgd').value");
    assert.equal(preserved,'456');
    return {status:edited.response.status,source_links_initial:initialLinks,amount_after_edit:edited.request.answers.claim_amount_sgd,draft_preserved:true};
  });
  await check('FE-05','Number/date basic input validation','invalid or negative inputs block real POST and show validation; correction permits submit',async()=>{
    await reloadPage();await choose('rental_deposit');
    const baseline=requests.length;
    await answer('claim_amount_sgd',-1);
    await evaluate("document.getElementById('submit').click()");
    assert.equal(requests.slice(baseline).filter(r=>r.url.endsWith('/api/navigate')).length,0);
    assert.equal(await evaluate("document.getElementById('status').textContent"),'Input validation');
    assert.ok((await evaluate("document.getElementById('validation').textContent")).includes('1 answer'));
    await answer('claim_amount_sgd',123);
    await answer('relevant_event_date','2026-02-30');
    await evaluate("document.getElementById('submit').click()");
    assert.equal(requests.slice(baseline).filter(r=>r.url.endsWith('/api/navigate')).length,0);
    await answer('relevant_event_date','2026-02-28');
    const fixed=await submit();
    assert.equal(fixed.request.answers.claim_amount_sgd,123);
    assert.equal(fixed.request.answers.relevant_event_date,'2026-02-28');
    return {invalid_requests_sent:0,repaired_status:fixed.response.status};
  });
  await check('FE-06','Consumer real referral, seven card blocks and verified source URLs','backend-linked sources clickable; no invented legal Action Card',async()=>{
    await reloadPage();await choose('consumer_complaint');
    const r=await complete('consumer_complaint');
    assert.equal(r.response.status,'REFER_TO_OFFICIAL');
    assert.equal(r.response.action_card,null);
    assert.equal(await evaluate("document.querySelectorAll('#card .card-section').length"),7);
    const linkData=await evaluate("Array.from(document.querySelectorAll('#verified-source-list a[href]'),x=>({href:x.href,target:x.target,rel:x.rel}))");
    assert.ok(linkData.length>0);
    const expected=r.response.evidence.map(x=>new URL(x.url).href);
    for(const source of expected) assert.ok(linkData.some(x=>x.href===source));
    assert.ok(linkData.every(x=>x.target==='_blank' && x.rel.includes('noopener')));
    const note=await evaluate("document.getElementById('verified-source-context').textContent");
    assert.ok(note.includes('does not establish legal eligibility'));
    return {status:r.response.status,verified_links:linkData.length,seven_sections:7};
  });
  await check('FE-07','Simulated API network failure then recover','blocked request shows safe error and clears stale links; retry preserves answers',async()=>{
    await reloadPage();await choose('rental_deposit');
    const good=await complete('rental_deposit');
    assert.equal(good.response.status,'REFER_TO_OFFICIAL');
    await command('Network.setBlockedURLs',{urls:['*api/navigate*']});
    try {
      await evaluate("document.getElementById('submit').click()");
      await until("document.getElementById('status').textContent==='Service unavailable'");
      assert.equal(await evaluate("document.querySelectorAll('#verified-source-list a[href]').length"),0);
      assert.equal(await evaluate("document.getElementById('detail-claim_amount_sgd').value"),'123');
    } finally {await command('Network.setBlockedURLs',{urls:[]});}
    const again=await submit();
    assert.equal(again.response.status,'REFER_TO_OFFICIAL');
    assert.equal(again.request.answers.claim_amount_sgd,123);
    return {offline:'Service unavailable',retry:again.response.status,answers_preserved:true};
  });
  await check('FE-08','Mobile width and physical keyboard navigation','390px and 320px no horizontal overflow; Tab reaches first form select',async()=>{
    await reloadPage();await choose('rental_deposit');
    const results=[];
    for(const width of [390,320]){
      await command('Emulation.setDeviceMetricsOverride',{width,height:844,deviceScaleFactor:1,mobile:true});
      await delay(150);
      const value=await evaluate("({innerWidth:window.innerWidth,scroll:document.documentElement.scrollWidth,client:document.documentElement.clientWidth,card:document.getElementById('card').clientWidth})");
      assert.ok(value.scroll<=value.client+1,JSON.stringify(value));
      results.push({width,scroll: value.scroll,client:value.client});
    }
    await evaluate("document.getElementById('case-type').focus()");
    await command('Input.dispatchKeyEvent',{type:'keyDown',key:'Tab',code:'Tab',windowsVirtualKeyCode:9});
    await command('Input.dispatchKeyEvent',{type:'keyUp',key:'Tab',code:'Tab',windowsVirtualKeyCode:9});
    const focused=await evaluate("document.activeElement.id");
    assert.equal(focused,'input-dispute_with');
    await command('Emulation.clearDeviceMetricsOverride');
    return {viewports:results,tab_focus:focused};
  });
  result.javascript_exceptions = exceptions.length;
  result.passed = result.checks.length===8 && result.checks.every(check => check.result==='PASS') && exceptions.length === 0;
} catch (error) {result.error = error.message;}
finally {
  if (ws?.readyState === WebSocket.OPEN) {
    try {await command('Browser.close', {}, false);} catch {}
    ws.close();
  } else {browser.kill();}
}
console.log(JSON.stringify(result, null, 2));
process.exitCode = result.passed ? 0 : 1;
