"use strict";
const {test}=require("node:test");
const assert=require("node:assert/strict");
const {readFileSync}=require("node:fs");
const {resolve}=require("node:path");
const locale=require("../js/task23-locale.js");
const live=require("../js/task21-live.js");
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
  const attrs={};
  const source={dataset:{},setAttribute:(key,value)=>{attrs[key]=value;}};
  locale.observeText(source,"Not sure",true);
  assert.equal(source.textContent,"Not sure");
  assert.equal(attrs.lang,"en");
  locale.setLanguage("en");
});

test("homepage example clicks show Chinese and submit the equivalent English examples",async()=>{
  const examples=path=>[...readFileSync(resolve(__dirname,path),"utf8")
    .matchAll(/data-example-question="([^"]+)"/g)].map(match=>match[1]);
  const english=examples("../../index.html");
  assert.equal(english.length,2);
  assert.deepEqual(examples("../index.html"),english);
  class Element extends EventTarget {
    dataset={};
    setAttribute(){}
    removeAttribute(){}
    append(){}
    appendChild(){}
    replaceChildren(){}
    focus(){}
  }
  const nodes=new Map(["problem-intake","problem-form","problem-text","problem-submit",
    "problem-count","problem-validation"].map(id=>[id,new Element()]));
  const input=nodes.get("problem-text"),validation=nodes.get("problem-validation");
  const buttons=english.map(text=>Object.assign(new Element(),{getAttribute:()=>text}));
  const doc=Object.assign(new EventTarget(),{body:new Element(),getElementById:id=>nodes.get(id),
    createElement:()=>new Element(),querySelectorAll:()=>buttons});
  const submitted=[];
  const app=live.init(doc,{SGNaviLocale:locale,SGNaviApiConfig:{resolve:()=>"/api/action-plan"},
    crypto:{randomUUID:()=>"12345678"},async fetch(_path,{body}){
      assert.equal(validation.textContent,"正在了解情况……");
      submitted.push(JSON.parse(body).description);
      throw new Error("Test service unavailable");
    }});
  locale.setLanguage("zh");
  try{
    for(const [index,button] of buttons.entries()){
      button.dispatchEvent(new Event("click"));
      assert.match(input.value,index===0?/房东.*2,000.*押金/:/自用.*商品.*退款/);
      await app.interpret();
      assert.equal(validation.textContent,"");
      assert.equal(nodes.get("problem-submit").disabled,false);
    }
    assert.deepEqual(submitted,english);
    input.value+="今天。";
    await app.interpret();
    assert.match(validation.textContent,/请用英文/);
    assert.deepEqual(submitted,english);
    locale.setLanguage("en");
    buttons[0].dispatchEvent(new Event("click"));
    assert.equal(input.value,english[0]);
  }finally{locale.setLanguage("en");}
});

test("known non-legal selector labels have Chinese display, unknown content stays English",()=>{
  locale.setLanguage("zh");
  const attrs={};
  const node={dataset:{},tagName:"OPTION",textContent:"",
    setAttribute(name,value){attrs[name]=value;},
    removeAttribute(name){delete attrs[name];}};
  locale.observeText(node,"A novel and unreviewed legal outcome");
  assert.equal(node.textContent,"A novel and unreviewed legal outcome");
  assert.equal(attrs.lang,"en");
  assert.equal(locale.label("Understand Options"),"了解处理方式");
  assert.equal(locale.label("Goods Dispute"),"商品纠纷");
  assert.equal(locale.label("Consumer Complaint"),"消费者纠纷");
  assert.doesNotMatch(node.textContent,/英文原文|暂无审核译文/);
  locale.setLanguage("en");
  locale.observeText(node,"Understand Options");
  assert.equal(attrs.lang,undefined);
  locale.setLanguage("zh");
  assert.equal(locale.label("SG Navi · One quick detail"),"SG Navi · 还需要确认一项信息");
  locale.setLanguage("en");
});

test("Chinese intake shows its English-input requirement before submission",()=>{
  const hint={hidden:true};
  const input={value:"My existing description",placeholder:"English example",attributes:{},
    setAttribute(name,value){this.attributes[name]=value;}};
  const doc=Object.assign(new EventTarget(),{documentElement:{},querySelector:()=>null,
    querySelectorAll:()=>[],getElementById:id=>({"problem-text":input,"problem-language-help":hint})[id]});
  locale.init(doc);
  assert.equal(hint.hidden,true);
  locale.setLanguage("zh");
  assert.equal(hint.hidden,false);
  assert.equal(input.attributes["aria-describedby"],"problem-language-help problem-helper");
  assert.equal(input.placeholder,"English example");
  assert.equal(input.value,"My existing description");
  locale.setLanguage("en");
  assert.equal(hint.hidden,true);
  assert.equal(input.attributes["aria-describedby"],"problem-helper");
});
