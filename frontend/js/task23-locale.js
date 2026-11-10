"use strict";
/* Task23 bilingual UI shell. Dynamic legal/action wording must be sourced from
   an approved bilingual backend contract; never machine-translate evidence. */
(function(root,factory){
  const api=factory();
  if(typeof module==="object"&&module.exports)module.exports=api;
  if(root)root.SGNaviLocale=api;
})(typeof globalThis!=="undefined"?globalThis:this,function(){
  const RENTAL_EXAMPLE="My landlord has not returned my S$2,000 deposit. What should I check?";
  const EXAMPLES=Object.freeze({
    [RENTAL_EXAMPLE]:"房东没有退还我 2,000 新元押金，我该先核对什么？",
    "I bought a faulty product for personal use, but the seller will not refund me.":"我买了一件自用的商品，商品有故障，但卖家不肯退款。"
  });
  const EN_ZH=Object.freeze({
    "What happened?":"发生了什么？",
    "SG Navi | Start Here":"SG Navi｜从这里开始",
    "Language / 语言":"语言",
    "Call":"拨打电话",
    "Email":"发送邮件至",
    "Reviewed":"审核时间",
    "Please describe your situation in English.":"请用英文输入你的情况。",
    "Is this about goods or a service?":"这涉及商品还是服务？",
    "The type of purchase changes which help may be relevant.":"购买的是商品还是服务，会影响适合你的求助方式。",
    "Goods":"商品",
    "Service":"服务",
    "Was this for personal or business use?":"这是个人用途还是商业用途？",
    "Consumer assistance may depend on the purpose of the purchase.":"适用的消费纠纷帮助可能取决于购买用途。",
    "Is this dispute with your landlord or an agent?":"这起纠纷涉及你的房东还是房产中介？",
    "Landlord deposit disputes and agent-conduct issues use different routes.":"与房东的押金纠纷和涉及中介行为的问题，可能适用不同的处理方式。",
    "Have you already ended the tenancy?":"你的租约已经结束了吗？",
    "The immediate step differs for a planned exit and a completed exit.":"计划退租和已经退租的情况，下一步有所不同。",
    "Does your signed lease include a break or diplomatic clause?":"你签署的租约中有提前解约条款或外交条款吗？",
    "Only the signed lease can establish your particular early-exit terms.":"请核对已签署的租约，确认其中具体的提前退租条款。",
    "Did you sign an agreement with the estate agency?":"你是否与房产中介公司签署了协议？",
    "A signed agency agreement changes the potential dispute-resolution route.":"是否签署中介协议，可能影响可考虑的纠纷处理方式。",
    "Was the purchase or bill in Singapore?":"这笔购买或账单是否发生在新加坡？",
    "The official local assistance route depends on where the transaction took place.":"交易地点会影响可查询的本地求助方式。",
    "Are you seeking help as a local consumer or a visitor?":"你是以本地消费者还是访客的身份寻求帮助？",
    "The reviewed complaint-contact profile distinguishes its service audience.":"确认你的身份，有助于核对相关求助渠道的服务对象。",
    "Is your concern with the landlord or estate agent?":"你的问题涉及房东还是房产中介？",
    "This determines which agency or dispute procedure should be explored.":"了解纠纷涉及哪一方，有助于核对相关机构和处理方式。",
    "More than one unrelated dispute is described. Select one issue to continue.":"描述中包含多个不同的纠纷，请选一个问题继续。",
    "This situation is outside the currently supported assistance scope. Check the relevant institution's official guidance.":"这类情况超出目前的协助范围。请查看相关机构的官方指引。",
    "Describe the disputed payment, purchase or rental deposit and what happened.":"请描述有争议的付款、购买或租房押金，并说明发生了什么。",
    "Please confirm this understanding or correct the details before proceeding.":"继续之前，请确认以上理解或修改相关细节。",
    "One detail may change the appropriate next step.":"还有一项信息可能影响下一步。",
    "The confirmed details do not yet establish a reviewed next-step profile. Check the disputed transaction or signed tenancy records and correct any uncertain details before choosing a formal route.":"根据已确认的信息，目前还无法给出经过核验的下一步建议。请先核对有争议的交易或已签署的租约，并补正不确定的信息。",
    "A reviewed preparation or assistance step is available. This does not establish eligibility or guarantee an outcome.":"有经过核验的准备步骤或求助方式可供参考。此信息不判定资格，也不保证结果。",
    "The current evidence or contact could not be verified. No source-backed action can be displayed; review the applicable official guidance.":"目前无法核验相关依据或联系方式，暂时无法显示有依据的行动建议。请查看适用的官方指引。",
    "Service is temporarily unavailable. Please retry.":"服务暂时不可用，请重试。",
    "Consumer Complaint":"消费者纠纷",
    "Rental Deposit":"租房押金纠纷",
    "Restaurant Overcharge":"餐厅多收费",
    "Duplicate Charge":"重复扣款",
    "Unclear Charge":"收费不明确",
    "Goods Dispute":"商品纠纷",
    "Services Dispute":"服务纠纷",
    "Deposit Return":"押金退还",
    "Deposit Deduction":"押金扣除",
    "Early Exit":"提前退租",
    "Pass Related Exit":"准证相关退租",
    "Agent Conduct":"房产经纪行为",
    "Agency Agreement":"房地产代理协议",
    "Unspecified":"尚未确定",
    "Complain":"提出投诉",
    "Seek Refund":"请求退款",
    "Prepare Claim":"准备索偿",
    "Understand Options":"了解处理方式",
    "Contact Provider":"联系相关机构",
    "SG Navi · One quick detail":"SG Navi · 还需要确认一项信息",
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
    "Where did the purchase happen?":"你在哪里购买的？",
    "Was it for personal use?":"是个人使用的吗？",
    "Have you asked the seller to resolve it?":"你是否已联系卖家处理？",
    "Are you a local consumer or a visitor?":"你是本地消费者还是访客？",
    "Local consumer":"本地消费者",
    "Visitor":"访客",
    "Who is the dispute with?":"纠纷涉及哪一方？",
    "What type of premises?":"租赁场所属于哪一类？",
    "HDB":"组屋（HDB）",
    "Commercial":"商业场所",
    "Industrial":"工业场所",
    "Have you already left or ended the tenancy?":"你是否已搬离或结束租约？",
    "Does your signed agreement contain a break clause?":"你签署的租约是否包含提前解约条款？",
    "Not yet":"尚未",
    "Choose an option, including Not sure.":"请选择一个选项，包括“不确定”。",
    "Checking what happened…":"正在了解情况……",
    "Checking the next step…":"正在核对下一步……",
    "Describe the problem in 1 to 1,200 characters.":"请用 1 至 1,200 个字符描述问题。",
    "Please write your own description in English, or use one of the examples above.":"请用英文描述你的情况，或直接使用上方的示例。",
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
    "What to prepare":"准备哪些材料",
    "More information":"更多信息",
    "Open official website ↗":"打开官方网站 ↗",
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
    "Now: ":"现在：",
    " personal preparation steps checked":" 项个人准备事项已勾选",
    "This is the current suggested action, not a completed official step.":"这是当前建议采取的行动。勾选仅供个人记录。",
    "Next":"接下来",
    "Later":"之后",
    "Further steps depend on your case.":"后续步骤取决于你的具体情况。",
    "Personal checklist only — not a filed case or official status.":"仅供个人记录，不代表已提交申诉或获得官方处理状态。",
    "Your preparation steps":"准备步骤",
    "No currently verified process sequence is available.":"目前没有经过核验的完整流程。",
    "Original official English source (not translated)":"官方英文原文（未翻译）",
    "No reviewed Chinese translation of this result is available. Please switch to EN to read the complete verified text.":"此结果暂无经审核的完整中文译文。请切换 EN 查看经过核验的完整英文内容。"
  });
  // Exact product-written interpretation templates. Unrecognised summaries stay canonical.
  const SUMMARY_START=Object.freeze({
    "You reported a restaurant billing overcharge.":"你反映餐厅账单多收费。",
    "You reported being charged twice for a transaction.":"你反映一笔交易被重复扣款。",
    "You reported a disputed restaurant bill or charge.":"你反映对餐厅账单或收费有争议。",
    "You reported a dispute about purchased goods.":"你反映购买的商品发生了纠纷。",
    "You reported a dispute about a purchased service.":"你反映购买的服务发生了纠纷。",
    "You reported a dispute about returning a rental deposit.":"你反映租房押金退还发生了纠纷。",
    "You reported disputed deductions from a rental deposit.":"你反映对租房押金扣款有争议。",
    "You reported a rental dispute involving an early tenancy exit.":"你反映租房纠纷涉及提前退租。",
    "You reported a rental issue involving a work-pass event.":"你反映租房问题涉及工作准证的变化。",
    "You reported a concern about an estate agent's conduct.":"你反映对房产中介的行为有疑问。",
    "You reported an estate agency agreement dispute.":"你反映房产中介协议发生了纠纷。",
    "You reported a dispute that needs a little more context.":"你反映了一项需要补充信息的纠纷。"
  });
  const SUMMARY_GOAL=Object.freeze({
    "make a complaint.":"你希望提出投诉。",
    "seek repayment.":"你希望请求退款。",
    "explore preparing a formal claim.":"你希望了解如何准备正式索偿。",
    "contact the relevant organisation.":"你希望联系相关机构。",
    "understand your available options.":"你希望了解有哪些处理方式。"
  });
  const STATIC=Object.freeze([
    ["#hero-heading","What happened?"],
    ["#task23-slogan","Don't feel lost, just find me."],
    [".hero > .shell > .eyebrow","RENTAL DEPOSITS & CONSUMER COMPLAINTS"],
    [".hero-copy","Tell us the problem. We’ll help you find official information to check your next step."],
    [".intake-step","Describe your concern"],
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
    [".hero-note","For demonstration only · Not legal advice · Does not submit cases"]
  ]);
  const reviewedText=new WeakMap();
  let lang="en",doc=null,warning=null;
  function chineseCopy(text){return Object.hasOwn(EN_ZH,text)?EN_ZH[text]:null;}
  function translate(text){return lang==="zh"?chineseCopy(text):text;}
  function chineseSummary(text){
    const parts=text.split(" You want to ");
    if(parts.length!==2||!Object.hasOwn(SUMMARY_START,parts[0])||!Object.hasOwn(SUMMARY_GOAL,parts[1]))return null;
    return SUMMARY_START[parts[0]]+SUMMARY_GOAL[parts[1]];
  }
  function label(text){return translate(String(text))||String(text);}
  function exampleLabel(text){return lang==="zh" && Object.hasOwn(EXAMPLES,text) ? EXAMPLES[text] : text;}
  function canonicalExample(text){return Object.keys(EXAMPLES).find(english=>EXAMPLES[english]===text)??text;}
  function applyDynamicElement(el){
    if(!el || !el.dataset || !el.dataset.task23Original)return;
    const original=el.dataset.task23Original;
    if(el.dataset.task23Source==="true"){el.textContent=original;el.setAttribute("lang","en");return;}
    if(lang==="en"){el.textContent=original;el.removeAttribute("lang");return;}
    const translated=reviewedText.has(el)?reviewedText.get(el):translate(original);
    if(translated){el.textContent=translated;el.removeAttribute("lang");return;}
    // Do not add a bulky warning to *every* label, option and dialog title.
    // Keep dynamic backend/source text unchanged and correctly language-tagged.
    // A single notice in the dialog explains the reviewed-translation limit.
    el.textContent=original;el.setAttribute("lang","en");
  }
  function apply(){
    if(!doc)return;
    doc.documentElement.lang=lang==="zh"?"zh-Hans":"en";
    doc.title=label("SG Navi | Start Here");
    for(const [sel,original]of STATIC){
      const el=doc.querySelector(sel);
      if(el)el.textContent=label(original);
    }
    const input=doc.getElementById("problem-text");
    const inputHelp=doc.getElementById("problem-language-help");
    if(input&&inputHelp){
      inputHelp.hidden=lang!=="zh";
      input.placeholder=inputHelp.hidden?"For example: "+RENTAL_EXAMPLE:chineseCopy("Please describe your situation in English.");
      input.setAttribute("aria-describedby",inputHelp.hidden?"problem-helper":"problem-language-help problem-helper");
    }
    const primary=doc.getElementById("problem-submit");
    if(primary){
      const span=primary.querySelector("span");
      // Keep the actual button node and listeners; only replace its first text node.
      if(primary.firstChild && primary.firstChild.nodeType===3)
        primary.firstChild.textContent=label("Find my next step")+" ";
      if(span)span.setAttribute("aria-hidden","true");
    }
    for(const el of doc.querySelectorAll("[data-task23-original]"))applyDynamicElement(el);
    for(const group of doc.querySelectorAll(".task23-language"))
      group.setAttribute("aria-label",label("Language / 语言"));
    for(const btn of doc.querySelectorAll("[data-task23-language]")){
      const english=btn.dataset.task23Language==="en";
      btn.setAttribute("aria-pressed",String(btn.dataset.task23Language===lang));
      if(english){
        btn.textContent=lang==="zh"?"英文":"EN";
        btn.setAttribute("lang",lang==="zh"?"zh-Hans":"en");
      }
    }
    syncCoverage();
  }
  function syncCoverage(){
    if(!doc)return;
    for(const notice of doc.querySelectorAll("[data-task24-reviewed-notice]"))notice.hidden=lang!=="zh";
    const needsNotice=container=>lang==="zh" && container?.querySelector('[data-task23-original][lang="en"]:not([data-task23-source])');
    const dialogBody=doc.querySelector(".task20-overlay:not([hidden]) .task20-dialog-content");
    if(dialogBody){
      let note=doc.getElementById("task23-dialog-translation-notice");
      const show=Boolean(needsNotice(dialogBody));
      if(!note&&show){
        note=doc.createElement("p");
        note.id="task23-dialog-translation-notice";
        note.className="task23-dialog-translation-notice";
        note.setAttribute("role","note");
        note.textContent="部分内容尚无经审核的中文译文，以下保留英文原文。";
        dialogBody.prepend(note);
      }
      if(note)note.hidden=!show;
    }
    if(warning)warning.hidden=Boolean(dialogBody)||!needsNotice(doc.querySelector("#task21-result:not([hidden])"));
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
  function observeReviewedText(el,original,reviewed){
    reviewedText.set(el,reviewed);
    return observeText(el,original);
  }
  function init(documentRef){
    doc=documentRef;
    warning=doc.getElementById("task23-language-warning");
    doc.addEventListener("click",event=>{
      const button=event.target.closest?.("[data-task23-language]");
      if(button)setLanguage(button.dataset.task23Language);
    });
    apply();
    return {setLanguage,apply};
  }
  if(typeof document!=="undefined"){
    if(document.readyState==="loading")document.addEventListener("DOMContentLoaded",()=>init(document));
    else init(document);
  }
  return Object.freeze({init,setLanguage,translate,label,exampleLabel,canonicalExample,chineseCopy,chineseSummary,observeText,observeReviewedText,syncCoverage,getLanguage:()=>lang});
});
