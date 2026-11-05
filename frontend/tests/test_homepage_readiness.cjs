"use strict";
const {test} = require("node:test");
const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");
const vm = require("node:vm");

async function check(page, payload, ok = true) {
  const html = fs.readFileSync(path.resolve(__dirname, "../..", page), "utf8");
  const inline = [...html.matchAll(/<script>([\s\S]*?)<\/script>/g)].at(-1)[1];
  const elements = {
    "api-status": {dataset: {}},
    "status-text": {textContent: ""},
    "refresh-api": {disabled: false, addEventListener() {}}
  };
  const context = vm.createContext({
    document: {getElementById: id => elements[id], querySelectorAll: () => []},
    window: {location: {}},
    SGNaviApiConfig: {resolve: () => "https://service.example/api/health"},
    AbortController, setTimeout, clearTimeout,
    fetch: async () => ({ok, status: ok ? 200 : 503,
      headers: {get: () => "application/json"}, json: async () => payload})
  });
  vm.runInContext(inline.replace(/checkApiHealth\(\);\s*$/, "globalThis.run = checkApiHealth();"), context);
  await context.run;
  return {state: elements["api-status"].dataset.state, text: elements["status-text"].textContent,
    disabled: elements["refresh-api"].disabled};
}

for (const page of ["index.html", "frontend/index.html"]) {
  test(page + " only displays ready for a valid successful readiness response", async () => {
    for (const payload of [{}, {status: "unavailable"}, {status: "unexpected"}, []]) {
      assert.equal((await check(page, payload)).state, "offline", JSON.stringify(payload));
    }
    const ready = await check(page, {status: "ok"});
    assert.equal(ready.state, "online");
    assert.equal(ready.disabled, false);
    assert.equal((await check(page, {status: "ok"}, false)).state, "offline");
  });
}
