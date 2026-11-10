"use strict";
/* Task23 bilingual UI shell. Dynamic legal/action wording must be sourced from
   an approved bilingual backend contract; never machine-translate evidence. */
(function(root,factory){
  const api=factory();
  if(typeof module==="object"&&module.exports)module.exports=api;
  if(root)root.SGNaviLocale=api;
})(typeof globalThis!=="undefined"?globalThis:this,function(){
  const EN_ZH=Object.freeze({
    "What happened?":"发生了什么？",
    "Don't feel lost, just find me.":"别迷茫，让我帮你找到方向。",
    "RENTAL DEPOSITS & CONSUMER COMPLAINTS":"租房押金与消费者投诉",
    "Tell us the problem. We’ll help you find official information to check your next step.":"告诉我们遇到的问题，我们会帮你查找官方信息，了解下一步。",
    "Describe your concern":"描述问题",
    "English · Singapore":"中文 · 新加坡",
    "Tell us what happened":"告诉我们发生了什么",
    "We currently help with rental deposit and consumer complaint questions in Singapore.":"目前我们主要协助查询新加坡租房押金与消费投诉相关信息。",
    "Describe your problem":"描述遇到的问题",
    "Try a made-up example:":"试试虚构示例：",
    "Rental deposit":"租房押金",
    "Consumer complaint":"消费者投诉",
    "Find my next step":"找到下一步",
    "Use made-up details only. Do not include names, contact details or private documents.":"请只使用虚构信息，不要填写姓名、联系方式或私人文件。",
    "For demonstration only · Not legal advice · Does not submit cases":"仅供演示 · 不构成法律建议 · 不会代为提交案件",
    "SG Navi · Student demonstration · Not legal advice":"SG Navi · 学生项目演示 · 不构成法律建议",
    "Confirm your situation":"确认情况",
    "Is this your situation?":"这是你的情况吗？",
    "Please confirm the topic. Your answers stay in this browser tab and are not saved to browser storage.":"请确认问题类型。答案只保留在当前页面，不会写入浏览器存储。",
    "Which topic best matches your concern?":"你的问题更接近哪种类型？",
    "Correct any important details (optional)":"核对重要信息（选填）",
    "Not specified":"未说明",
    "Topic":"问题类别",
    "Type of concern":"问题类型",
    "What you want help with":"希望获得的帮助",
    "Does this describe your situation?":"这是否符合你的情况？",
    "Confirm the main details":"确认主要信息",
    "Edit description":"修改描述",
    "Confirm and continue →":"确认并继续 →",
    "Continue →":"继续 →",
    "Back":"返回",
    "Close dialog":"关闭弹窗",
    "SG Navi question and details":"SG Navi 问题与详情",
    "ONE QUICK DETAIL":"还需要确认一项信息",
    "Not sure":"不确定",
    "Yes":"是",
    "No":"否",
    "Singapore":"新加坡",
    "Outside Singapore":"新加坡境外",
    "Personal use":"个人用途",
    "Business use":"商业用途",
    "Private home or condo":"私人住宅或公寓",
    "Landlord":"房东",
    "Estate agent":"房产中介",
    "Not yet":"尚未",
    "Choose an option, including Not sure.":"请选择一个选项，包括“不确定”。",
    "Checking what happened…":"正在了解情况……",
    "Checking the next step…":"正在核对下一步……",
    "Describe the problem in 1 to 1,200 characters.":"请用 1 至 1,200 个字符描述问题。",
    "The checking service is not configured.":"查询服务尚未配置。",
    "The checking service could not complete this request.":"查询服务暂时无法完成请求。",
    "Unexpected checking service response.":"查询服务返回了无法识别的内容。",
    "The service could not check your description. Please try again.":"暂时无法检查你的描述，请重试。",
    "We could not check the next step. Your answers remain here; please retry.":"暂时无法核对下一步，已保留你的答案，请重试。",
    "We could not safely show the next question.":"暂时无法安全显示下一项问题。",
    "Service temporarily unavailable":"服务暂时不可用",
    "More information is needed":"还需要更多信息",
    "Check again":"重新核对",
    "An official help or preparation option is available; this does not decide legal eligibility or guarantee a result.":"以下仅为官方信息查询及准备建议，不代表法律资格判定，也不保证结果。",
    "YOUR NEXT STEP":"建议的下一步",
    "Before you continue":"继续之前",
    "Get help with the next part":"查看后续帮助",
    "Official contacts":"官方联系方式",
    "Write a request":"撰写请求",
    "Documents to prepare":"准备材料",
    "What to watch out for":"注意事项",
    "If it isn't resolved":"如果仍未解决",
    "Why this advice?":"建议依据",
    "Relevant legal wording":"相关法律原文",
    "Read wording and context":"查看原文及上下文",
    "Edit situation":"修改情况",
    "Official ways to get help":"官方求助方式",
    "No currently verified contact is available for this route.":"目前没有经过核验的适用联系方式。",
    "Edit this draft before copying. Nothing will be sent automatically.":"复制前请核对并修改草稿；系统不会自动发送。",
    "Add your own confirmed details":"补充已确认的详情",
    "Copy draft":"复制草稿",
    "Copied — review before sending":"已复制，请发送前再次检查",
    "Select the draft text to copy":"请选择草稿文本后复制",
    "Verified wording and sources":"已核验原文及来源",
    "Statutory excerpt":"法律原文摘录",
    "Model contract wording (not a law)":"合同示例文字（不是法律条文）",
    "Official procedural information":"官方流程信息",
    "Read full original ↗":"查看官方原文 ↗",
    "View supporting sources":"查看依据来源",
    "Continue to next step":"继续下一步",
    "View available steps":"查看可用步骤",
    "Now":"现在",
    "Next":"接下来",
    "Later":"之后",
    "Further steps depend on your case.":"后续步骤取决于你的具体情况。",
    "Personal checklist only — not a filed case or official status.":"仅供个人记录，不代表已提交申诉或获得官方处理状态。",
    "Your preparation steps":"准备步骤",
    "No currently verified process sequence is available.":"目前没有经过核验的完整流程。",
    "Original official English source (not translated)":"官方英文原文（未翻译）",
    "No reviewed Chinese translation of this result is available. Please switch to EN to read the complete verified text.":"此结果暂无经审核的完整中文译文。请切换 EN 查看经过核验的完整英文内容。"
  });
  const STATIC=Object.freeze([
    ["#hero-heading","What happened?"],
    ["#task23-slogan","Don't feel lost, just find me."],
    [".hero > .shell > .eyebrow","RENTAL DEPOSITS & CONSUMER COMPLAINTS"],
    [".hero-copy","Tell us the problem. We’ll help you find official information to check your next step."],
    [".intake-step","Describe your concern"],
    [".intake-language","English · Singapore"],
    ["#intake-heading","Tell us what happened"],
    [".intake-privacy","Use made-up details only. Do not include names, contact details or private documents."],
    [".intake-examples .example-question:first-of-type","Rental deposit"],
    [".intake-examples .example-question:last-of-type","Consumer complaint"],
    ["#problem-review .intake-step","Confirm your situation"],
    ["#review-title","Is this your situation?"],
    ["#review-back","Edit description"],
    [".review-help","Please confirm the topic. Your answers stay in this browser tab and are not saved to browser storage."],
    ["#task23-language-warning","No reviewed Chinese translation of this result is available. Please switch to EN to read the complete verified text."],
    [".intake-description","We currently help with rental deposit and consumer complaint questions in Singapore."],
    ["label[for=problem-text]","Describe your problem"],
    [".intake-examples > span","Try a made-up example:"],
    [".hero-note","For demonstration only · Not legal advice · Does not submit cases"],
    [".site-footer","SG Navi · Student demonstration · Not legal advice"]
  ]);
  let lang="en",doc=null,warning=null;
  function translate(text){return lang==="zh" ? EN_ZH[text]||null : text;}
  function label(text){return translate(String(text))||String(text);}
  function applyDynamicElement(el){
    if(!el || !el.dataset || !el.dataset.task23Original)return;
    const original=el.dataset.task23Original;
    if(lang==="en"){el.textContent=original;return;}
    const translated=translate(original);
    if(translated){el.textContent=translated;return;}
    if(el.tagName==="BLOCKQUOTE"||el.dataset.task23Source==="true"){
      el.textContent=original;el.setAttribute("lang","en");return;
    }
    // No unreviewed automatic paraphrasing of legal conclusions or routes.
    el.textContent="英文原文（暂无审核译文）："+original;
  }
  function apply(){
    if(!doc)return;
    doc.documentElement.lang=lang==="zh"?"zh-Hans":"en";
    for(const [sel,original]of STATIC){
      const el=doc.querySelector(sel);
      if(el)el.textContent=label(original);
    }
    const input=doc.getElementById("problem-text");
    if(input)input.placeholder=lang==="zh"
      ?"例如：房东没有退还我 2,000 新元押金，我该先核对什么？"
      :"For example: My landlord has not returned my S$2,000 deposit. What should I check?";
    const primary=doc.getElementById("problem-submit");
    if(primary){
      const span=primary.querySelector("span");
      // Keep the actual button node and listeners; only replace its first text node.
      if(primary.firstChild && primary.firstChild.nodeType===3)
        primary.firstChild.textContent=label("Find my next step")+" ";
      if(span)span.setAttribute("aria-hidden","true");
    }
    for(const el of doc.querySelectorAll("[data-task23-original]"))applyDynamicElement(el);
    for(const btn of doc.querySelectorAll("[data-task23-language]"))
      btn.setAttribute("aria-pressed",String(btn.dataset.task23Language===lang));
    if(warning)warning.hidden=lang==="en" || !doc.getElementById("problem-intake") ||
       !["review","questions","results","limited"].includes(doc.getElementById("problem-intake").dataset.flowStage);
  }
  function setLanguage(next){
    if(next!=="zh"&&next!=="en")return false;
    lang=next;apply();
    if(doc)doc.dispatchEvent(new CustomEvent("sgnavi:languagechange",{detail:{language:lang}}));
    return true;
  }
  function observeText(el,original,source=false){
    if(!el)return el;
    el.dataset.task23Original=String(original);
    if(source)el.dataset.task23Source="true";
    applyDynamicElement(el);
    return el;
  }
  function init(documentRef){
    doc=documentRef;
    warning=doc.getElementById("task23-language-warning");
    for(const btn of doc.querySelectorAll("[data-task23-language]"))
      btn.addEventListener("click",()=>setLanguage(btn.dataset.task23Language));
    apply();
    return {setLanguage,apply};
  }
  if(typeof document!=="undefined"){
    if(document.readyState==="loading")document.addEventListener("DOMContentLoaded",()=>init(document));
    else init(document);
  }
  return Object.freeze({init,setLanguage,translate,label,observeText,getLanguage:()=>lang});
});
