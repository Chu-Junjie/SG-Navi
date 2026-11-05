"use strict";
const {test} = require("node:test");
const assert = require("node:assert/strict");
const {resolve, normalisePublicOrigin, isGitHubPages, isPublicConfigured} = require("../js/api-config.js");

const pages = {protocol:"https:", hostname:"chu-junjie.github.io",pathname:"/SG-Navi/frontend/task5-flow.html"};
const local = {protocol:"http:",hostname:"127.0.0.1",pathname:"/task5-flow.html"};

test("new Render service origin is used on GitHub Pages, never the Pages hostname",()=>{
 assert.equal(isGitHubPages(pages),true);
 assert.equal(isPublicConfigured(),true);
 for(const path of ["/api/navigate","/api/health","/api/version","/api/case-types"])
   assert.equal(resolve(path,pages),"https://sg-navi-api-junjie.onrender.com"+path);
 assert.equal(resolve("/api/navigate",pages,""),null);
});
test("local Flask same-origin routes are preserved unchanged",()=>{
 assert.equal(isGitHubPages(local),false);
 assert.equal(resolve("/api/navigate",local),"/api/navigate");
 assert.equal(resolve("/api/health",local),"/api/health");
});
test("valid confirmed public origin selects cross-origin routes",()=>{
 assert.equal(resolve("/api/navigate",pages,"https://sgnavi-api.onrender.com"),"https://sgnavi-api.onrender.com/api/navigate");
 assert.equal(resolve("/api/health",pages,"https://sgnavi-api.onrender.com"),"https://sgnavi-api.onrender.com/api/health");
});
test("reject credential, URL path, insecure, local, mock and placeholder addresses",()=>{
 for(const raw of [
   "", "http://sgnavi-api.onrender.com","https://localhost",
   "https://127.0.0.1","https://example.com","https://example.invalid",
   "https://api.example.com", "https://api.onrender.com/api",
   "https://user:pass@api.onrender.com","https://api.onrender.com/?token=secret",
   "https://api.onrender.com/#a","https://api.onrender.com:8443/endpoint",
   " https://api.onrender.com", "https://192.168.1.7"
 ])assert.equal(normalisePublicOrigin(raw),null,raw);
});
test("reject unsupported endpoints; no arbitrary URL forwarding",()=>{
 assert.throws(()=>resolve("/admin",pages,"https://foo.onrender.com"),/Unrecognised/);
});
test("Pages root and nested paths recognized without identifying unrelated gh pages",()=>{
 assert.equal(isGitHubPages({hostname:"chu-junjie.github.io",pathname:"/SG-Navi/"}),true);
 assert.equal(isGitHubPages({hostname:"evil.github.io",pathname:"/other/"}),false);
});
