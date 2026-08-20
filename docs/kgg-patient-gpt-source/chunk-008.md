# KGG Patient Source Chunk 008

- Source file: `patient-card-progress.js`
- Characters: 1-5300
- Full source SHA-256: `0addeb089b6d19b3f4d2669bd12c75ecf8e4885250b277db07af8d80e4942b40`

```
(()=>{
  const VERSION='card-progress-v2-complete-fields';
  const STYLE_ID='kgg-card-progress-style';
  const BADGE_CLASS='kggCardProgress';
  if(window.__kggCardProgress===VERSION)return;
  window.__kggCardProgress=VERSION;

  function stateForCount(count,total){
    const filled=Math.max(0,Number(count)||0);
    const expected=Math.max(0,Number(total)||0);
    if(filled===0)return 'open';
    if(expected>0&&filled>=expected)return 'done';
    return 'partial'
  }
  function language(){return localStorage.getItem('kggPatientLang')==='en'?'en':'de'}
  function labelForState(state,lang){
    const en=(lang||language())==='en';
    if(state==='done')return en?'✓ Done':'✓ Bearbeitet';
    if(state==='partial')return en?'◐ Partial':'◐ Teilweise';
    return en?'○ Open':'○ Offen'
  }
  function normalValueInputs(card){
    if(!card||typeof card.querySelectorAll!=='function')return [];
    return [...card.querySelectorAll('.set input.num')]
  }
  function filledCount(card){
    return normalValueInputs(card).filter(input=>String(input&&input.value!=null?input.value:'').trim()!=='').length
  }
  function ensureStyle(){
    if(document.getElementById(STYLE_ID))return;
    const style=document.createElement('style');
    style.id=STYLE_ID;
    style.textContent=`.${BADGE_CLASS}{display:none}body.kggCardsCollapsed .ex:not(.kggOpen) .${BADGE_CLASS},body.kggAlwaysCollapsed .ex:not(.kggOpen) .${BADGE_CLASS}{display:inline-flex!important;align-items:center;width:max-content;max-width:100%;margin:0 0 2px;padding:3px 8px;border:1px solid #cbd5e1;border-radius:999px;background:#f8fafc;color:#64748b;font-size:11px;font-weight:900;line-height:1.2;white-space:nowrap}body.kggCardsCollapsed .ex:not(.kggOpen) .${BADGE_CLASS}.kggProgressPartial,body.kggAlwaysCollapsed .ex:not(.kggOpen) .${BADGE_CLASS}.kggProgressPartial{border-color:#fcd34d;background:#fffbeb;color:#92400e}body.kggCardsCollapsed .ex:not(.kggOpen) .${BADGE_CLASS}.kggProgressDone,body.kggAlwaysCollapsed .ex:not(.kggOpen) .${BADGE_CLASS}.kggProgressDone{border-color:#86efac;background:#ecfdf5;color:#166534}`;
    document.head.appendChild(style)
  }
  function ensureBadge(card){
    let badge=card.querySelector('.'+BADGE_CLASS);
    if(badge)return badge;
    badge=document.createElement('span');
    badge.className=BADGE_CLASS;
    badge.setAttribute('aria-live','polite');
    const title=card.querySelector('h3');
    if(title&&title.insertAdjacentElement)title.insertAdjacentElement('afterend',badge);
    else card.insertBefore(badge,card.firstChild||null);
    return badge
  }
  function updateCard(card){
    if(!card)return;
    const inputs=normalValueInputs(card);
    const count=inputs.filter(input=>String(input&&input.value!=null?input.value:'').trim()!=='').length;
    const state=stateForCount(count,inputs.length);
    const badge=ensureBadge(card);
    badge.className=BADGE_CLASS+' kggProgress'+state.charAt(0).toUpperCase()+state.slice(1);
    badge.textContent=labelForState(state);
    badge.dataset.kggProgress=state;
    badge.dataset.kggFilledCount=String(count);
    badge.dataset.kggExpectedCount=String(inputs.length);
    badge.title=badge.textContent;
    badge.setAttribute('aria-label',badge.textContent)
  }
  function cards(){return [...document.querySelectorAll('#list .ex')]}
  function updateAll(){ensureStyle();cards().forEach(updateCard)}
  let updateTimer=0;
  function scheduleUpdate(delay){
    clearTimeout(updateTimer);
    updateTimer=setTimeout(updateAll,Number(delay)||0)
  }
  function bindEvents(){
    if(window.__kggCardProgressEvents)return;
    window.__kggCardProgressEvents=1;
    document.addEventListener('input',event=>{if(event.target&&event.target.matches&&event.target.matches('#list .set input.num'))scheduleUpdate(0)},true);
    document.addEventListener('change',event=>{if(event.target&&event.target.matches&&event.target.matches('#list .set input.num'))scheduleUpdate(0)},true);
    document.addEventListener('click',event=>{
      if(event.target&&event.target.closest&&event.target.closest('.padOk,.padCancel,.padLast,.padGrid,#days')){
        scheduleUpdate(40);setTimeout(updateAll,180);setTimeout(updateAll,360)
      }
    },true)
  }
  function observeList(){
    const list=document.getElementById('list');
    if(!list||list.dataset.kggCardProgressObserved==='1'||typeof MutationObserver==='undefined')return;
    list.dataset.kggCardProgressObserved='1';
    const observer=new MutationObserver(()=>scheduleUpdate(0));
    observer.observe(list,{childList:true,subtree:true})
  }
  function patchRender(){
    if(window.__kggCardProgressRenderPatched||typeof render!=='function')return;
    window.__kggCardProgressRenderPatched=1;
    const old=render;
    window.render=function(){const result=old.apply(this,arguments);scheduleUpdate(0);setTimeout(updateAll,120);return result}
  }
  function init(){
    ensureStyle();bindEvents();observeList();patchRender();updateAll();
    setTimeout(()=>{observeList();patchRender();updateAll()},300);
    setTimeout(()=>{observeList();patchRender();updateAll()},1000)
  }
  if(window.__KGG_TEST__)window.__kggCardProgressTest={stateForCount,labelForState,filledCount,normalValueInputs};
  document.readyState==='loading'?document.addEventListener('DOMContentLoaded',init,{once:true}):init()
})();
```
