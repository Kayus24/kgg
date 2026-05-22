(()=>{
  const VERSION='v1_day_history_current_day';
  const STYLE='kggPatientDayHistoryStyle';
  const LANG='kggPatientLang';
  const $=id=>document.getElementById(id);
  const en=()=>localStorage.getItem(LANG)==='en';
  const T=(de,enText)=>en()?enText:de;
  const safe=f=>{try{return f()}catch(e){return null}};

  function ensureStyle(){
    const old=$(STYLE);if(old)old.remove();
    const s=document.createElement('style');s.id=STYLE;s.textContent=`
      #kggActionFab{left:14px!important;bottom:calc(14px + env(safe-area-inset-bottom))!important}
      #kggActionSheet{bottom:calc(82px + env(safe-area-inset-bottom))!important}
      #days{display:none!important}
      #kggDayHub{border:1px solid #dbe3ef;border-radius:18px;background:#f8fafc;padding:10px;margin:10px 0 12px;box-shadow:0 6px 18px rgba(15,23,42,.04)}
      .kggCurrentDay{display:flex;align-items:center;justify-content:space-between;gap:10px;border:1px solid #cbd5e1;border-radius:16px;background:#fff;padding:12px}
      .kggCurrentDayLabel{font-size:12px;color:#64748b;font-weight:900;margin-bottom:2px}.kggCurrentDayBig{font-size:24px;font-weight:950;letter-spacing:-.03em}.kggCurrentDayMeta{font-size:12px;color:#64748b;font-weight:800;margin-top:2px}.kggCurrentDayBadge{border-radius:999px;border:1px solid #bbf7d0;background:#ecfdf5;color:#166534;padding:7px 10px;font-size:12px;font-weight:950;white-space:nowrap}
      #kggHistoryToggle{width:100%;min-height:46px;margin-top:9px;border-radius:14px;border:1px solid #cbd5e1;background:#fff;color:#111827;font-size:15px;font-weight:950;touch-action:manipulation}#kggHistoryToggle:active{transform:scale(.985);background:#f8fafc}
      #kggHistoryList{display:grid;gap:8px;margin-top:9px;animation:kggHistIn .18s ease both}#kggHistoryList[hidden]{display:none!important}
      .kggDayCard{width:100%;text-align:left;border:1px solid #dbe3ef;border-radius:16px;background:#fff;padding:10px 12px;display:grid;grid-template-columns:1fr auto;gap:8px;align-items:center;touch-action:manipulation}.kggDayCard:active{transform:scale(.99);background:#eff6ff}.kggDayCard.done{border-color:#bbf7d0;background:#f0fdf4}.kggDayCard.current{border-color:#111827;box-shadow:0 0 0 2px rgba(17,24,39,.06)}.kggDayCard b{font-size:16px}.kggDayCard .muted{font-size:12px;color:#64748b}.kggDayCardPill{border-radius:999px;border:1px solid #cbd5e1;background:#f8fafc;padding:6px 9px;font-size:12px;font-weight:950;color:#334155}.kggDayCard.done .kggDayCardPill{background:#dcfce7;border-color:#86efac;color:#166534}
      @keyframes kggHistIn{from{opacity:0;transform:translateY(-6px)}to{opacity:1;transform:translateY(0)}}
      @media(max-width:430px){#kggActionFab{left:12px!important;bottom:12px!important}.kggCurrentDayBig{font-size:22px}.kggDayCard{padding:10px}}
    `;document.head.appendChild(s)
  }

  function valueCount(day){
    let count=0,total=0,painMax=0;
    const plan=safe(()=>p); if(!plan)return {count,total,painMax};
    (plan.ex||[]).forEach((ex,ei)=>{
      const sets=Number(ex.sets)||3;
      const sides=ex.side==='LR'?['L','R']:['B'];
      for(let s=1;s<=sets;s++)sides.forEach(side=>['a','b'].forEach(key=>{
        total++;
        const val=safe(()=>v[k(ei,s,side,key,day)])||'';
        if(String(val).trim())count++;
      }));
      for(let s=0;s<=sets;s++){
        const pv=Number(safe(()=>v[k(ei,s,'P','pain',day)])||0);
        if(pv>painMax)painMax=pv;
      }
    });
    return {count,total,painMax};
  }
  function dayDone(day){return Array.isArray(done)&&done.includes(day)}
  function dayLine(day){
    const c=valueCount(day);
    const filled=c.count?`${c.count}/${c.total} ${T('Werte','values')}`:T('noch keine Werte','no values yet');
    const pain=c.painMax>0?` · ${T('Schmerz max.','max pain')} ${c.painMax}/10`:'';
    const doneText=dayDone(day)?` · ${T('abgeschlossen','finished')}`:'';
    return filled+pain+doneText;
  }
  function currentMeta(){
    const c=valueCount(Number(d)||1);
    if(!c.count)return T('Noch keine Einträge an diesem Tag.','No entries for this day yet.');
    return `${c.count}/${c.total} ${T('Werte eingetragen','values entered')}${c.painMax>0?' · '+T('Schmerz max.','max pain')+' '+c.painMax+'/10':''}`;
  }
  function ensureHub(){
    const days=$('days'); if(!days||!days.parentNode||!safe(()=>p))return;
    let hub=$('kggDayHub');
    if(!hub){hub=document.createElement('div');hub.id='kggDayHub';days.parentNode.insertBefore(hub,days)}
    const cur=Number(d)||1;
    const total=Number(safe(()=>p.days))||6;
    const isDone=dayDone(cur);
    hub.innerHTML=`
      <div class="kggCurrentDay">
        <div><div class="kggCurrentDayLabel">${T('Aktueller Trainingstag','Current training day')}</div><div class="kggCurrentDayBig">${T('Tag','Day')} ${cur}</div><div class="kggCurrentDayMeta">${currentMeta()}</div></div>
        <div class="kggCurrentDayBadge">${isDone?T('fertig','finished'):T('offen','open')}</div>
      </div>
      <button id="kggHistoryToggle" type="button">${T('Frühere Trainings anzeigen','Show previous trainings')}</button>
      <div id="kggHistoryList" hidden></div>`;
    $('kggHistoryToggle').onclick=()=>toggleHistory(total,cur);
  }
  function toggleHistory(total,cur){
    const list=$('kggHistoryList'); if(!list)return;
    if(!list.hidden){list.hidden=true;$('kggHistoryToggle').textContent=T('Frühere Trainings anzeigen','Show previous trainings');return}
    renderHistory(total,cur);list.hidden=false;$('kggHistoryToggle').textContent=T('Frühere Trainings ausblenden','Hide previous trainings');
  }
  function renderHistory(total,cur){
    const list=$('kggHistoryList'); if(!list)return;
    const days=[];
    for(let day=1;day<=total;day++){
      if(day===cur)continue;
      const c=valueCount(day);
      if(day<cur||c.count||dayDone(day))days.push(day);
    }
    if(!days.length){list.innerHTML=`<div class="muted">${T('Noch keine früheren Trainings vorhanden.','No previous trainings yet.')}</div>`;return}
    list.innerHTML=days.map(day=>`<button type="button" class="kggDayCard ${dayDone(day)?'done':''}" data-day="${day}"><div><b>${T('Tag','Day')} ${day}</b><div class="muted">${dayLine(day)}</div></div><span class="kggDayCardPill">${T('öffnen','open')}</span></button>`).join('');
    list.querySelectorAll('.kggDayCard').forEach(btn=>btn.onclick=()=>openDay(Number(btn.dataset.day)||1));
  }
  function openDay(day){
    safe(()=>{d=day;save();});
    const list=$('kggHistoryList'); if(list)list.hidden=true;
    safe(()=>render());
    setTimeout(()=>{ensureHub();window.scrollTo({top:0,behavior:'smooth'})},40);
  }
  function patchRender(){if(window.__kggDayHistoryRenderPatch||typeof render!=='function')return;window.__kggDayHistoryRenderPatch=1;const old=render;render=function(){const r=old.apply(this,arguments);setTimeout(apply,0);return r}}
  function apply(){ensureStyle();ensureHub()}
  function init(){window.__kggPatientDayHistory=VERSION;patchRender();apply();setTimeout(apply,300);setTimeout(apply,1000)}
  document.readyState==='loading'?document.addEventListener('DOMContentLoaded',init):init();
})();
