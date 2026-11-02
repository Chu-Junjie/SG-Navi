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
const executable = process.argv[3] || 'C:\\Program Files (x86)\\Microsoft\\Edge\\Application\\msedge.exe';
const artifacts = path.resolve('instance/task5-browser');
await fs.mkdir(artifacts, {recursive: true});
const profile = await fs.mkdtemp(path.join(artifacts, 'profile-'));
const browser = spawn(executable, [
  '--headless=new', '--disable-gpu', '--disable-background-networking', '--disable-sync',
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
const fixtures = JSON.parse(await fs.readFile(new URL('./fixtures.json', import.meta.url), 'utf8'));
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
  scope: 'real_browser_api_rag_referral_flow', synthetic_facts: true,
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
  for (const caseType of ['rental_deposit', 'consumer_complaint']) {
    const check = {case_type: caseType, passed: false};
    try {
      await evaluate(`(()=>{const select=document.getElementById('case-type');select.value=${JSON.stringify(caseType)};select.dispatchEvent(new Event('change',{bubbles:true}));})()`);
      const blank = await submit();
      assert.equal(blank.request.case_type, caseType);
      assert.equal(blank.response.status, 'NEED_CLARIFICATION');
      assert.equal(blank.response.action_card, null);
      check.clarification = true;
      const firstQuestion = blank.response.questions[0].id;
      await evaluate("document.querySelector('#questions button').click()");
      assert.equal(await evaluate('document.activeElement.id'), 'input-' + firstQuestion);
      check.followup_focus = true;
      for (const [field, value] of Object.entries(fixtures[caseType].answers)) await fill(field, value);
      const completed = await submit();
      assert.deepEqual(completed.request.answers, fixtures[caseType].answers);
      assert.equal(completed.response.status, 'REFER_TO_OFFICIAL');
      assert.equal(completed.response.action_card, null);
      check.referral = true;
      check.evidence_count = completed.response.evidence.length;
      assert.ok(!completed.response.source_version.startsWith('mock'));
      check.source_version = completed.response.source_version;
      await fill('claim_amount_sgd', 456);
      const edited = await submit();
      assert.equal(edited.request.answers.claim_amount_sgd, 456);
      check.edit_resubmitted = true;
      check.api_posts = 3;
      check.transport_passed = true;
      assert.ok(check.evidence_count > 0, 'Referral does not expose verified source context for UI display');
      const links = await evaluate("Array.from(document.querySelectorAll('main a[href]'),a=>a.href)");
      const expectedURLs = [...new Set(completed.response.evidence.map(record => new URL(record.url).href))];
      check.context_sources_visible = expectedURLs.every(url => links.includes(url));
      assert.ok(check.context_sources_visible, 'Verified referral sources returned by RAG must be accessible in the UI');
      check.passed = true;
    } catch (error) {check.error = error.message;}
    result.checks.push(check);
  }
  result.javascript_exceptions = exceptions.length;
  result.passed = result.checks.every(check => check.passed) && exceptions.length === 0;
} catch (error) {result.error = error.message;}
finally {
  if (ws?.readyState === WebSocket.OPEN) {
    try {await command('Browser.close', {}, false);} catch {}
    ws.close();
  } else {browser.kill();}
}
console.log(JSON.stringify(result, null, 2));
process.exitCode = result.passed ? 0 : 1;
