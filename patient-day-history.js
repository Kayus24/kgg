(()=>{
  const VERSION='v2_compact_history_plan_switch_ready';
  const STYLE='kggPatientDayHistoryStyle';
  const LANG='kggPatientLang';
  const MULTI_KEY='kggPatientMultiPlansV1';
  const $=id=>document.getElementById(id);
  const en=()=>localStorage.getItem(LANG)==='en';
  const T=(de,enText)=>en()?enText:de;
  const safe=f=>{try{return f()}catch(e){return null}};
  const today=()=>safe(()=>next())||1;

  function readMulti(){try{return JSON.parse(localStorage.getItem(MULTI_KEY)||'null')}catch(e){return null}}
  function multiPlans(){const s=readMulti();return s&&Array.isArray(s.plans)?s.plans:[]}
  function activePlanName(){const s=readMulti(),arr=multiPlans();if(!arr.length)return '';const i=Math.max(0,Math.min(Number(s&&s.active)||0,arr.length-1));return arr[i]&&arr[i].t?arr[i].t:T('Plan ','Plan ')+(i+1)}

  function ensureStyle(){
    const old=$(STYLE);if(old)old.remove();
    const s=document.createElement('style');s.id=STYLE;s.textContent=`
      #kggActionFab{left:14px!important;bottom:calc(14px + env(safe-area-inset-bottom))!important}
      #days{display:none!important}
      #kggDayHub{border:0;border-radius:0;background:transparent;padding:0;margin:6px 0 10px;box-shadow:none}
      #kggHistoryToggle{width:100%;min-height:42px;margin:0 0 8px;border-radius:999px;border:1px solid #cbd5e1;background:#fff;color:#111827;font-size:14px;font-weight:950;touch-action:manipulation;box-shadow:0 4px 12px rgba(15,23,42,.04)}
      #kggHistoryToggle:active{transform:scale(.985);background:#f8fafc}
      .kggCurrentDay{display:flex;align-items:center;justify-content:space-between;gap:8px;border:1px solid #dbe3ef;border-radius:14px;background:#fff;padding:8px 10px;min-height:42px}
      .kggCurrentDayBig{font-size:16px;font-weight:950;letter-spacing:-.02em}.kggCurrentDayMeta{font-size:12px;color:#64748b;font-weight:850;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;max-width:50vw}.kggCurrentDayBadge{border-radius:999px;border:1px solid #cbd5e1;background:#f8fafc;color:#334155;padding:5px 8px;font-size:12px;font-weight:950;white-space:nowrap}.kggCurrentDay.switchable{cursor:pointer}.kggCurrentDay.switchable:active{transform:scale(.99);background:#eff6ff}
      #kggPlanChoiceBar{display:flex;gap:6px;flex-wrap:wrap;margin:8px 0;animation:kggHistIn .18s ease both}#kggPlanChoiceBar[hidden]{display:none!important}.kggPlanChoice{border:1px solid #cbd5e1;border-radius:999px;background:#fff;padding:7px 10px;font-size:12px;font-weight:950}.kggPlanChoice.active{background:#111827;color:#fff;border-color:#111827}
      #kggHistoryList{display:grid;gap:8px;margin:8px 0 10px;animation:kggHistIn .18s ease both}#kggHistoryList[hidden]{display:none!important}
      .kggDayCard{width:100%;text-align:left;border:1px solid #dbe3ef;border-radius:16px;background:#fff;padding:10px 12px;display:block;touch-action:manipulation}.kggDayCard:active{transform:scale(.99);background:#eff6ff}.kggDayCard.done{border-color:#bbf7d0;background:#f0fdf4}.kggDayHead{display:flex;align-items:center;justify-content:space-between;gap:8px;margin-bottom:6px}.kggDayHead b{font-size:16px}.kggDayPill{border-radius:999px;border:1px solid #cbd5e1;background:#f8fafc;padding:5px 8px;font-size:12px;font-weight:950;color:#334155}.kggDayCard.done .kggDayPill{background:#dcfce7;border-color:#86efac;color:#166534}.kggDayExerciseList{display:grid;gap:4px;margin-top:5px}.kggDayExercise{font-size:12px;color:#334155;line-height:1.25;background:rgba(248,250,252,.78);border:1px solid #e2e8f0;border-radius:10px;padding:6px 8px}.kggDayExercise b{font-size:12px}.kggEmptyHist{font-size:12px;color:#64748b;padding:8px;text-align:center}
      @keyframes kggHistIn{from{opacity:0;transform:translateY(-6px)}to{opacity:1;transform:translateY(0)}}
      @media(max-width:430px){#kggActionFab{left:12px!important;bottom:12px!important}.kggCurrentDayBig{font-size:15px}.kggCurrentDayMeta{max-width:44vw}.kggDayCard{padding:9px 10px}}
    `;document.head.appendChild(s)
  }

  function valAt(ei,s,side,key,day){return String(safe(()=>v[k(ei,s,side,key,day)])||'').trim()}
  function painAt(ei,s,day){return Number(safe(()=>v[k(ei,s,'P','pain',day)])||0)}
  function dayDone(day){return Array.isArray(done)&&done.includes(day)}
  function exSummary(day,ei,ex){
    const sets=Number(ex.sets)||3;
    const sides=ex.side==='LR'?['L','R']:['B'];
    let doneSets=0,parts=[],painMax=0;
    for(let s=1;s<=sets;s++){
      let any=false;
      sides.forEach(side=>{
        const a=valAt(ei,s,side,'a',day), b=valAt(ei,s,side,'b',day);
        if(a||b){any=true;parts.push((side==='B'?'':side+': ')+(a||'?')+' '+(ex.u||'')+' × '+(b||'?')+' '+(ex.m||''));}
      });
      if(any)doneSets++;
      const pv=painAt(ei,s,day);if(pv>painMax)painMax=pv;
    }
    const globalPain=painAt(ei,0,day);if(globalPain>painMax)painMax=globalPain;
    if(!doneSets&&!painMax)return '';
    const first=parts.slice(0,2).join(' · ');
    return `<div class="kggDayExercise"><b>${esc(ex.n)}</b><br>${doneSets}/${sets} ${T('Sätze','sets')}${first?' · '+esc(first):''}${painMax?' · '+T('Schmerz','pain')+' '+painMax+'/10':''}</div>`;
  }
  function dayHasData(day){
    if(dayDone(day))return true;
    const plan=safe(()=>p);if(!plan)return false;
    return (plan.ex||[]).some((ex,ei)=>!!exSummary(day,ei,ex));
  }
  function dayCards(day){
    const arr=(safe(()=>p.ex)||[]).map((ex,ei)=>exSummary(day,ei,ex)).filter(Boolean);
    return arr.length?arr.join(''):`<div class="kggDayExercise">${T('Noch keine Werte eingetragen.','No values entered yet.')}</div>`;
  }
  function isToday(){return Number(d)===today()}
  function planMeta(){const arr=multiPlans();if(arr.length<2)return '';return activePlanName()}

  function ensureHub(){
    const days=$('days'); if(!days||!days.parentNode||!safe(()=>p))return;
    let hub=$('kggDayHub');
    if(!hub){hub=document.createElement('div');hub.id='kggDayHub';days.parentNode.insertBefore(hub,days)}
    const cur=Number(d)||1,total=Number(safe(()=>p.days))||6,arr=multiPlans();
    const back=!isToday();
    const mainLabel=back?T('Zum heutigen Training zurückkehren','Return to today’s training'):T('Frühere Trainings anzeigen','Show previous trainings');
    hub.innerHTML=`
      <button id="kggHistoryToggle" type="button">${mainLabel}</button>
      <div id="kggHistoryList" hidden></div>
      <div class="kggCurrentDay ${arr.length>1?'switchable':''}" id="kggCurrentDayBox">
        <div class="kggCurrentDayBig">${T('Tag','Day')} ${cur}</div>
        <div class="kggCurrentDayMeta">${arr.length>1?esc(planMeta()):''}</div>
        <div class="kggCurrentDayBadge">${dayDone(cur)?T('fertig','finished'):T('offen','open')}</div>
      </div>
      <div id="kggPlanChoiceBar" hidden></div>`;
    $('kggHistoryToggle').onclick=()=> back?openDay(today()):toggleHistory(total,cur);
    $('kggCurrentDayBox').onclick=()=>handlePlanSwitch(arr);
  }
  function toggleHistory(total,cur){const list=$('kggHistoryList');if(!list)return;if(!list.hidden){list.hidden=true;$('kggHistoryToggle').textContent=T('Frühere Trainings anzeigen','Show previous trainings');return}renderHistory(total,cur);list.hidden=false;$('kggHistoryToggle').textContent=T('Frühere Trainings ausblenden','Hide previous trainings')}
  function renderHistory(total,cur){
    const list=$('kggHistoryList');if(!list)return;
    const days=[];for(let day=1;day<=total;day++){if(day===cur)continue;if(day<cur||dayHasData(day))days.push(day)}
    if(!days.length){list.innerHTML=`<div class="kggEmptyHist">${T('Noch keine früheren Trainings vorhanden.','No previous trainings yet.')}</div>`;return}
    list.innerHTML=days.map(day=>`<button type="button" class="kggDayCard ${dayDone(day)?'done':''}" data-day="${day}"><div class="kggDayHead"><b>${T('Tag','Day')} ${day}</b><span class="kggDayPill">${T('öffnen','open')}</span></div><div class="kggDayExerciseList">${dayCards(day)}</div></button>`).join('');
    list.querySelectorAll('.kggDayCard').forEach(btn=>btn.onclick=()=>openDay(Number(btn.dataset.day)||1))
  }
  function openDay(day){safe(()=>{d=day;save()});const list=$('kggHistoryList');if(list)list.hidden=true;safe(()=>render());setTimeout(()=>{ensureHub();window.scrollTo({top:0,behavior:'smooth'})},40)}

  function handlePlanSwitch(arr){
    if(arr.length<2)return;
    if(arr.length===2){switchPlan((currentPlanIndex()+1)%2);return}
    const bar=$('kggPlanChoiceBar');if(!bar)return;
    if(!bar.hidden){bar.hidden=true;return}
    renderPlanChoices(arr);bar.hidden=false;
  }
  function currentPlanIndex(){const s=readMulti();return Math.max(0,Math.min(Number(s&&s.active)||0,multiPlans().length-1))}
  function switchPlan(idx){
    const fn=window.KGGPatientMultiPlan&&window.KGGPatientMultiPlan.switchTo;
    if(typeof fn==='function'){fn(idx);setTimeout(()=>safe(()=>render()),40);return}
    const s=readMulti();if(!s||!s.plans||!s.plans[idx])return;
    s.active=idx;localStorage.setItem(MULTI_KEY,JSON.stringify(s));setTimeout(()=>safe(()=>render()),40)
  }
  function renderPlanChoices(arr){const bar=$('kggPlanChoiceBar');if(!bar)return;const active=currentPlanIndex();bar.innerHTML=arr.map((pl,i)=>`<button type="button" class="kggPlanChoice ${i===active?'active':''}" data-i="${i}">${esc(pl.t||T('Plan ','Plan ')+(i+1))}</button>`).join('');bar.querySelectorAll('.kggPlanChoice').forEach(b=>b.onclick=()=>{switchPlan(Number(b.dataset.i)||0);bar.hidden=true})}

  function esc(s){return String(s??'').replace(/[&<>"']/g,m=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[m]))}
  function patchRender(){if(window.__kggDayHistoryRenderPatch||typeof render!=='function')return;window.__kggDayHistoryRenderPatch=1;const old=render;render=function(){const r=old.apply(this,arguments);setTimeout(apply,0);return r}}
  function apply(){ensureStyle();ensureHub()}
  function init(){window.__kggPatientDayHistory=VERSION;patchRender();apply();setTimeout(apply,300);setTimeout(apply,1000)}
  document.readyState==='loading'?document.addEventListener('DOMContentLoaded',init):init();
})();
