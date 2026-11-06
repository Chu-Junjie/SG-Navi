"use strict";
/* Task 20/21 standalone UI fixture. NO live backend, eligibility or contacts.
   Contract and evidence integration remain blocked on Tasks 16–19. */
(function(root,factory){
  const api=factory();
  if(typeof module==="object"&&module.exports)module.exports=api;
  if(root)root.SGNaviConcept=api;
})(typeof globalThis!=="undefined"?globalThis:this,function(){
  const SAMPLES=Object.freeze({
    restaurant:"A restaurant charged me more than the menu price and refuses to refund the difference.",
    rental:"My landlord has not returned the rental deposit, and I want to know what to check."
  });
  // These questions are explicitly illustrative; not inferred or returned by Task 18.
  const FIXTURE_QUESTIONS=Object.freeze({
    restaurant:[
      {prompt:"Was this purchase for personal use?",options:["Yes, for myself","It was for business","I'm not sure"]},
      {prompt:"Have you already asked the restaurant to correct the bill?",options:["Yes","Not yet","I'm not sure"]}
    ],
    rental:[
      {prompt:"Who currently holds your rental deposit?",options:["Landlord","Property agent","I'm not sure"]},
      {prompt:"Have you checked the terms in your signed tenancy agreement?",options:["Yes","Not yet","I'm not sure"]}
    ]
  });
  const FIXTURE_ACTIONS=Object.freeze({
    restaurant:{
      topic:"RESTAURANT BILL · CONSUMER COMPLAINT",
      statement:"For a disputed restaurant charge, start by checking the itemised bill and asking the restaurant to explain or correct it.",
      action:"Review the itemised bill",
      description:"Keep the price shown on the menu, the receipt, and any response from the restaurant.",
      checklist:["Keep your itemised receipt and payment record.","Note the price difference and when it occurred.","Keep a copy of your request and the restaurant's reply."],
      documents:"Itemised receipt, menu/photo if available, payment record and correspondence.",
      uncertainty:"The actual transaction, advertised price and appropriate official complaint route have not been checked.",
      links:[["CASE — consumer complaint information","https://www.case.org.sg/submit-a-complaint/"]]
    },
    rental:{
      topic:"RENTAL DEPOSIT",
      statement:"For a rental deposit disagreement, first check what your signed tenancy agreement says about deductions and returning the deposit.",
      action:"Review the signed agreement",
      description:"Identify the relevant deposit terms and gather payment and move-out records before considering possible official channels.",
      checklist:["Find the signed tenancy agreement and deposit payment record.","List the disputed deductions or missing refund details.","Keep move-out and landlord/agent correspondence."],
      documents:"Signed tenancy terms, payment proof, condition records and written communications.",
      uncertainty:"The signed contract, landlord/agent role, premises type and legal channel have not been verified.",
      links:[["Singapore Courts — small claims information","https://www.judiciary.gov.sg/civil/cases-eligible-small-claim"]]
    }
  });
  const OFFICIAL_HOSTS=new Set(["www.judiciary.gov.sg","www.case.org.sg","www.cea.gov.sg"]);
  function safeLink(raw){
    try {
      const u=new URL(raw);
      if(u.protocol!=="https:"||u.username||u.password||u.hash||
          (u.port&&u.port!=="443")||!OFFICIAL_HOSTS.has(u.hostname.toLowerCase()))return null;
      return u.href;
    } catch(_) {return null;}
  }
  function chooseFixture(text,explicit){
    if(explicit==="restaurant"||explicit==="rental")return explicit;
    const t=String(text).toLowerCase();
    if(/restaurant|menu|dining|meal|bill|overcharg/.test(t))return "restaurant";
    if(/landlord|rental|tenan|deposit|lease/.test(t))return "rental";
    return null;
  }
  function init(doc){
    const $=id=>doc.getElementById(id);
    if(!$("description")||!$("question-overlay")||!$("outcome"))return null;
    const state={scenario:null,explicit:null,step:0,answers:{restaurant:[],rental:[]},
      lastFocus:null,detailsFocus:null};
    const text=(id,value)=>{$(id).textContent=value;};
    const setHidden=(id,value)=>{$(id).hidden=value;};
    function inDialog(rootEl){
      return [...rootEl.querySelectorAll("button:not([disabled]),a[href],input:not([disabled])")]
        .filter(el=>typeof el.getClientRects!=="function"||el.getClientRects().length);
    }
    function closeQuestion(){
      setHidden("question-overlay",true);
      (state.lastFocus||$("start")).focus();
    }
    function closeDetails(){
      setHidden("details-overlay",true);
      (state.detailsFocus||$("show-evidence")).focus();
    }
    function focusTrap(e){
      const current=!$("details-overlay").hidden?$("details-overlay"):
        !$("question-overlay").hidden?$("question-overlay"):null;
      if(!current)return;
      if(e.key==="Escape"){
        e.preventDefault();
        if(current===$("details-overlay"))closeDetails();else closeQuestion();
        return;
      }
      if(e.key!=="Tab")return;
      const items=inDialog(current);
      if(!items.length)return;
      if(e.shiftKey&&doc.activeElement===items[0]){e.preventDefault();items[items.length-1].focus();}
      else if(!e.shiftKey&&doc.activeElement===items[items.length-1]){e.preventDefault();items[0].focus();}
    }
    doc.addEventListener("keydown",focusTrap);
    function renderQuestion(){
      const question=FIXTURE_QUESTIONS[state.scenario][state.step];
      text("dialog-heading",question.prompt);
      const options=$("question-options");
      options.replaceChildren();
      for(const answer of question.options){
        const b=doc.createElement("button");
        b.type="button";b.textContent=answer;
        b.setAttribute("aria-pressed",String(state.answers[state.scenario][state.step]===answer));
        b.addEventListener("click",()=>{
          state.answers[state.scenario][state.step]=answer;
          for(const candidate of options.children)candidate.setAttribute("aria-pressed",String(candidate===b));
        });
        options.appendChild(b);
      }
      text("question-back",state.step?"Previous question":"Close");
      text("question-next",state.step===FIXTURE_QUESTIONS[state.scenario].length-1
        ?"Show next step →":"Continue →");
    }
    function openQuestion(){
      state.lastFocus=doc.activeElement;
      setHidden("question-overlay",false);
      renderQuestion();
      $("close-question").focus();
    }
    function showResult(){
      const model=FIXTURE_ACTIONS[state.scenario];
      closeQuestion();
      text("result-topic",model.topic);
      text("next-step",model.statement);
      text("action-heading",model.action);
      text("action-description",model.description);
      text("documents",model.documents);
      text("uncertainty",model.uncertainty);
      const checklist=$("quick-list");
      checklist.replaceChildren();
      for(const point of model.checklist){
        const item=doc.createElement("li");item.textContent=point;checklist.appendChild(item);
      }
      setHidden("outcome",false);
      $("extra").open=false;
      $("result-heading").focus();
    }
    function openDetails(){
      const model=FIXTURE_ACTIONS[state.scenario];
      state.detailsFocus=doc.activeElement;
      const list=$("official-links");list.replaceChildren();
      for(const [name,url] of model.links){
        const href=safeLink(url);
        if(!href)continue;
        const li=doc.createElement("li"),a=doc.createElement("a");
        a.href=href;a.target="_blank";a.rel="noopener noreferrer";a.textContent=name;
        li.appendChild(a);list.appendChild(li);
      }
      setHidden("details-overlay",false);
      $("close-details").focus();
    }
    function start(){
      const value=$("description").value.trim();
      if(!value){text("message","Please describe the problem first.");$("description").focus();return;}
      if(value.length>1200){text("message","Please shorten your description.");return;}
      state.scenario=chooseFixture(value,state.explicit);
      if(!state.scenario){
        text("message","This preview has only two made-up examples. Choose Restaurant bill or Rental deposit.");
        $("description").focus();return;
      }
      state.step=0;
      setHidden("outcome",true);
      text("message","This is a sample interaction. No data has been submitted.");
      openQuestion();
    }
    $("start").addEventListener("click",start);
    for(const button of doc.querySelectorAll("[data-example]")){
      button.addEventListener("click",()=>{
        state.explicit=button.dataset.example;
        $("description").value=SAMPLES[state.explicit];
        $("description").focus();
        text("message","Sample selected. No data has been sent.");
      });
    }
    $("description").addEventListener("input",()=>{
      state.explicit=null;setHidden("outcome",true);
      text("message","Use made-up examples only. Leave out personal details.");
    });
    $("close-question").addEventListener("click",closeQuestion);
    $("question-back").addEventListener("click",()=>{
      if(state.step){state.step--;renderQuestion();}
      else closeQuestion();
    });
    $("question-next").addEventListener("click",()=>{
      if(!state.answers[state.scenario][state.step]){
        text("question-help","Choose an answer, including ‘I'm not sure’, to continue.");
        $("question-options").querySelector("button")?.focus();
        return;
      }
      text("question-help","This helps us identify which information to check.");
      if(state.step<FIXTURE_QUESTIONS[state.scenario].length-1){
        state.step++;renderQuestion();
      } else showResult();
    });
    $("edit").addEventListener("click",()=>{
      state.step=0;setHidden("outcome",true);openQuestion();
    });
    $("show-evidence").addEventListener("click",openDetails);
    $("close-details").addEventListener("click",closeDetails);
    $("return-details").addEventListener("click",closeDetails);
    return Object.freeze({start,closeQuestion,closeDetails});
  }
  if(typeof document!=="undefined"){
    if(document.readyState==="loading")document.addEventListener("DOMContentLoaded",()=>init(document));
    else init(document);
  }
  return Object.freeze({safeLink,chooseFixture,init,FIXTURE_QUESTIONS});
});