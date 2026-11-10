"use strict";
const {test}=require("node:test");
const assert=require("node:assert/strict");
const locale=require("../js/task23-locale.js");
test("English is the default and the approved bilingual slogan is exact",()=>{
  assert.equal(locale.getLanguage(),"en");
  assert.equal(locale.translate("Don't feel lost, just find me."),"Don't feel lost, just find me.");
  assert.equal(locale.setLanguage("zh"),true);
  assert.equal(locale.label("Don't feel lost, just find me."),"别迷茫，让我帮你找到方向。");
  assert.equal(locale.label("View available steps"),"查看可用步骤");
  assert.equal(locale.label("Continue to next step"),"继续下一步");
  assert.equal(locale.label("For demonstration only · Not legal advice · Does not submit cases"),"仅供演示 · 不构成法律建议 · 不会代为提交案件");
  assert.equal(locale.setLanguage("en"),true);
});
test("unreviewed backend sentences have no fabricated dictionary translation",()=>{
  locale.setLanguage("zh");
  assert.equal(locale.translate("A novel legal route with a unique source"),null);
  assert.equal(locale.label("A novel legal route with a unique source"),"A novel legal route with a unique source");
  assert.equal(locale.getLanguage(),"zh");
  assert.equal(locale.setLanguage("garbage"),false);
  assert.equal(locale.getLanguage(),"zh");
  locale.setLanguage("en");
});
test("source quotation is never translated by generic translation module",()=>{
  locale.setLanguage("zh");
  assert.equal(locale.translate("A new official legal source quotation"),null);
  locale.setLanguage("en");
});

test("unknown backend option remains legible English without repeated prefix",()=>{
  locale.setLanguage("zh");
  const attrs={};
  const node={dataset:{},tagName:"OPTION",textContent:"",
    setAttribute(name,value){attrs[name]=value;},
    removeAttribute(name){delete attrs[name];}};
  locale.observeText(node,"Understand Options");
  assert.equal(node.textContent,"Understand Options");
  assert.equal(attrs.lang,"en");
  assert.doesNotMatch(node.textContent,/英文原文|暂无审核译文/);
  locale.setLanguage("en");
  locale.observeText(node,"Understand Options");
  assert.equal(attrs.lang,undefined);
  locale.setLanguage("zh");
  assert.equal(locale.label("SG Navi · One quick detail"),"SG Navi · 还需要确认一项信息");
  locale.setLanguage("en");
});
