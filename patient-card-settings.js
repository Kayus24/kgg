(()=>{
  const VERSION='v1_always_collapsed_settings_pain_scale';
  const STYLE='kggPatientCardSettingsStyle';
  const LANG='kggPatientLang';
  const PLAN_KEY='kggCurrentPlanV1';
  const SET_KEY='kggPatientExerciseSettingsV1';
  let openIndex=null;
  const $=id=>document.getElementById(id);
  const en=()=>localStorage.getItem(LANG)==='en';
  const T=(de,enText)=>en()?enText:de;
  const safe=f=>{try{return f()}catch(e){return null}};

  function readSettings(){try{return JSON.parse(localStorage.getItem(SET_KEY)||'{}')||{}}catch(e){return{}}}
  function writeSettings(s){localStorage.setItem(SET_KEY,JSON.stringify(s||{}))}
  function exKey(e){return String((safe(()=>p.id)||'plan')+'|'+(e&&e.n||'exercise')).toLowerCase()}
  function getPainMode(e){const s=readSettings();return s[exKey(e)]&&s[exKey(e)].painMode||e.painMode||'exercise'}
  function setPainMode(e,mode){const s=readSettings(),key=exKey(e);s[key]=s[key]||{};s[key].painMode=mode;writeSettings(s);e.painMode=mode}
  function rawPlan(){return{ i:p.id||'plan', t:p.title||'KGG Trainingsplan', v:p.version||1, d:p.days||6, extendDays:p.extendDays!==false, stepDays:p.stepDays||6, e:(p.ex||[]).map(e=>[e.n,e.sets,e.side,e.u,e.m,e.sl||'',e.sm||'',e.media||'',e.videoUrl||'',e.videoLabel||'Video öffnen',e.painMode||getPainMode(e)])}}
  function storePlan(){safe(()=>localStorage.setItem(PLAN_KEY,JSON.stringify({plan:rawPlan(),importedAt:new Date().toISOString()})))}
  function unit(x){x=String(x||'');const m={Wdh:['Wdh','reps'],wdh:['Wdh','reps'],Reps:['Wdh','reps'],reps:['Wdh','reps'],'Sek.':['Sek.','sec'],Sek:['Sek.','sec'],sec:['Sek.','sec'],'Min.':['Min.','min'],Min:['Min.','min'],min:['Min.','min'],Stufe:['Stufe','level'],level:['Stufe','level'],Level:['Stufe','level']};return m[x]?T(m[x][0],m[x][1]):x}
  function sideText(x){return x==='LR'?T('links/rechts','left/right'):T('beidseitig','bilateral')}
  function st(msg){safe(()=>setStatus(msg,'ok'))}
  function saveAll(){safe(()=>save());storePlan()}

  function ensureStyle(){
    const old=$(STYLE);if(old)old.remove();
    const s=document.createElement('style');s.id=STYLE;s.textContent=`
      #kgg-collapse-toggle{display:none!important}
      body.kggAlwaysCollapsed .ex{position:relative;cursor:pointer;transition:box-shadow .18s ease,transform .16s ease,background .18s ease;padding-right:52px!important}
      body.kggAlwaysCollapsed .ex:not(.kggOpen) .set,body.kggAlwaysCollapsed .ex:not(.kggOpen) .pain{display:none!important}
      body.kggAlwaysCollapsed .ex:not(.kggOpen)::after{content:'Antippen zum Öffnen';display:block;margin-top:8px;color:#64748b;font-size:12px;font-weight:800}
      body.kggLangEn.kggAlwaysCollapsed .ex:not(.kggOpen)::after{content:'Tap to open'}
      body.kggAlwaysCollapsed .ex.kggOpen{box-shadow:0 12px 32px rgba(15,23,42,.12);border-color:#111827;background:#fff}
      .kggCardDots{position:absolute;right:10px;top:10px;width:38px;height:38px;border-radius:999px;border:1px solid #cbd5e1;background:#fff;color:#111827;font-size:22px;font-weight:950;display:flex;align-items:center;justify-content:center;z-index:5;touch-action:manipulation}
      .kggCardDots:active{transform:scale(.94);background:#eff6ff}
      body.kggAlwaysCollapsed .ex:not(.kggOpen) .kggCardDots{display:none!important}
      .kggPainScale{display:grid;grid-template-columns:repeat(11,1fr);gap:4px;width:100%;touch-action:none;user-select:none;-webkit-user-select:none;margin-top:8px}
      .kggPainScale button{min-width:0;min-height:38px;border-radius:12px;border:1px solid #cbd5e1;background:#fff;color:#111827;font-weight:950;font-size:14px;box-shadow:none;touch-action:none}
      .kggPainScale button.on{background:#dbeafe;border-color:#60a5fa;color:#1d4ed8;box-shadow:0 5px 14px rgba(37,99,235,.20);transform:translateY(-2px)}
      .kggPainScale button:active{transform:scale(.94)}
      .kggPainCaption{font-size:12px;color:#64748b;margin-top:5px;font-weight:800;text-align:right}
      .kggSetPain{margin-top:10px;border-top:1px dashed #e2e8f0;padding-top:8px}.kggSetPain b{font-size:14px}
      .kggSettingsBackdrop{position:fixed;inset:0;background:rgba(15,23,42,.22);z-index:2700}.kggSettingsBackdrop[hidden]{display:none!important}
      #kggSettingsSheet{position:fixed;left:12px;right:12px;bottom:calc(12px + env(safe-area-inset-bottom));z-index:2701;max-width:540px;margin:0 auto;background:#fff;border:1px solid #dbe3ef;border-radius:22px;padding:14px;box-shadow:0 22px 70px rgba(15,23,42,.28);animation:kggSettingsIn .18s ease both}
      #kggSettingsSheet[hidden]{display:none!important}#kggSettingsSheet h3{margin:0 0 10px;font-size:19px}.kggSetGrid{display:grid;grid-template-columns:1fr 1fr;gap:8px}.kggSetGrid label{font-size:12px;color:#64748b;font-weight:900}.kggSetGrid input,.kggSetGrid select{width:100%;margin-top:4px;border:1px solid #cbd5e1;border-radius:12px;padding:10px;font-size:15px;background:#fff}.kggSetActions{display:grid;grid-template-columns:1fr 1fr;gap:9px;margin-top:12px}.kggSetActions button{min-height:48px;border-radius:14px;font-size:16px;font-weight:950}.kggSetCancel{background:#fff;border:1px solid #cbd5e1;color:#111827}.kggSetSave{background:#111827;border:1px solid #111827;color:#fff}
      @keyframes kggSettingsIn{from{opacity:0;transform:translateY(14px) scale(.98)}to{opacity:1;transform:translateY(0) scale(1)}}
      @media(max-width:430px){.kggPainScale{gap:3px}.kggPainScale button{min-height:34px;font-size:12px;border-radius:10px}.kggSetGrid{grid-template-columns:1fr}#kggSettingsSheet{border-radius:20px 20px 0 0;left:0;right:0;bottom:0}}
    `;document.head.appendChild(s)
  }

  function cards(){return[...document.querySelectorAll('#list .ex')]}
  function forceCards(){
    document.body.classList.add('kggAlwaysCollapsed');
    document.body.classList.toggle('kggLangEn',en());
    const tgl=$('kgg-collapse-toggle');if(tgl)tgl.style.display='none';
    cards().forEach((card,i)=>{
      card.dataset.kggAlwaysIdx=i;
      card.classList.toggle('kggOpen',openIndex===i);
      addDots(card,i);
      if(!card.dataset.kggAlwaysBound){
        card.dataset.kggAlwaysBound='1';
        card.addEventListener('click',ev=>{
          if(ev.target.closest('input,button,a,select,textarea,.kggPainScale,#kggSettingsSheet'))return;
          openIndex=openIndex===i?null:i;
          apply();
          if(openIndex===i)setTimeout(()=>card.scrollIntoView({behavior:'smooth',block:'start'}),60)
        });
      }
    })
  }
  function addDots(card,i){
    let b=card.querySelector('.kggCardDots');
    if(!b){b=document.createElement('button');b.type='button';b.className='kggCardDots';b.textContent='⋯';b.title=T('Übung anpassen','Edit exercise');b.onclick=e=>{e.preventDefault();e.stopPropagation();openSettings(i)};card.appendChild(b)}
    b.hidden=openIndex!==i;b.title=T('Übung anpassen','Edit exercise')
  }

  function valKey(ei,s){return safe(()=>k(ei,s,'P','pain'))||(`${d}|${ei}|${s}|P|pain`)}
  function painVal(ei,s){return String((safe(()=>v[valKey(ei,s)])||'0')||'0')}
  function setPainVal(ei,s,x){safe(()=>{v[valKey(ei,s)]=String(x);save()});st(T('Automatisch gespeichert.','Automatically saved.'));updatePainScales()}
  function painScale(ei,s){const wrap=document.createElement('div');wrap.className='kggPainScale';wrap.dataset.ei=ei;wrap.dataset.s=s;for(let n=0;n<=10;n++){let b=document.createElement('button');b.type='button';b.textContent=String(n);b.dataset.val=String(n);b.onclick=e=>{e.preventDefault();e.stopPropagation();setPainVal(ei,s,n)};wrap.appendChild(b)}bindDrag(wrap);return wrap}
  function bindDrag(wrap){if(wrap.dataset.dragBound)return;wrap.dataset.dragBound='1';let active=false;const hit=e=>{const el=document.elementFromPoint(e.clientX,e.clientY);const b=el&&el.closest&&el.closest('.kggPainScale button');if(b&&wrap.contains(b))setPainVal(+wrap.dataset.ei,+wrap.dataset.s,+b.dataset.val)};wrap.addEventListener('pointerdown',e=>{active=true;wrap.setPointerCapture&&wrap.setPointerCapture(e.pointerId);hit(e)});wrap.addEventListener('pointermove',e=>{if(active)hit(e)});wrap.addEventListener('pointerup',()=>active=false);wrap.addEventListener('pointercancel',()=>active=false)}
  function paintScale(wrap){const v=painVal(+wrap.dataset.ei,+wrap.dataset.s);wrap.querySelectorAll('button').forEach(b=>b.classList.toggle('on',b.dataset.val===v));let cap=wrap.nextElementSibling;if(cap&&cap.classList.contains('kggPainCaption'))cap.textContent=v+'/10'}
  function updatePainScales(){document.querySelectorAll('.kggPainScale').forEach(paintScale)}
  function renderPain(){
    cards().forEach((card,ei)=>{const e=safe(()=>p.ex[ei]);if(!e)return;const mode=getPainMode(e);
      card.querySelectorAll('.kggSetPain').forEach(x=>x.remove());
      const global=card.querySelector('.pain');
      if(mode==='set'){
        if(global)global.style.display='none';
        card.querySelectorAll('.set').forEach((set,idx)=>{const s=idx+1;let box=document.createElement('div');box.className='kggSetPain';box.innerHTML='<b>'+T('Schmerz Satz ','Pain set ')+s+' · 0–10</b>';box.appendChild(painScale(ei,s));let cap=document.createElement('div');cap.className='kggPainCaption';box.appendChild(cap);set.appendChild(box)})
      }else{
        if(global){global.style.display='';let b=global.querySelector('b');if(b)b.textContent=T('Schmerz 0–10','Pain 0–10');let row=global.querySelector('.painRow');if(row){row.innerHTML='';row.appendChild(painScale(ei,0));let cap=document.createElement('div');cap.className='kggPainCaption';row.appendChild(cap)}}
      }
    });
    updatePainScales()
  }

  function copySideValues(ei,oldSide,newSide){
    if(oldSide===newSide)return;const ex=safe(()=>p.ex[ei]);if(!ex)return;const sets=+ex.sets||3,days=+p.days||6;
    for(let day=1;day<=days;day++)for(let s=1;s<=sets;s++)['a','b'].forEach(key=>{
      if(oldSide!=='LR'&&newSide==='LR'){
        const b=safe(()=>v[k(ei,s,'B',key,day)])||''; if(b){if(!safe(()=>v[k(ei,s,'L',key,day)]))v[k(ei,s,'L',key,day)]=b;if(!safe(()=>v[k(ei,s,'R',key,day)]))v[k(ei,s,'R',key,day)]=b}
      }else if(oldSide==='LR'&&newSide!=='LR'){
        const l=safe(()=>v[k(ei,s,'L',key,day)])||'',r=safe(()=>v[k(ei,s,'R',key,day)])||''; if((l||r)&&!safe(()=>v[k(ei,s,'B',key,day)]))v[k(ei,s,'B',key,day)]=l||r
      }
    });
  }
  function closeSettings(){const b=$('kggSettingsBackdrop'),s=$('kggSettingsSheet');if(b)b.hidden=true;if(s)s.hidden=true}
  function openSettings(i){
    const e=safe(()=>p.ex[i]);if(!e)return;ensureSettingsDom();const sh=$('kggSettingsSheet'),bd=$('kggSettingsBackdrop');
    sh.innerHTML=`<h3>${T('Übung anpassen','Edit exercise')}</h3><div class="kggSetGrid">
      <label>${T('Gewicht / Gerät','Weight / machine')}<input id="kggSetUnitA" value="${esc(e.u||'kg')}"></label>
      <label>${T('Wdh / Zeit','Reps / time')}<input id="kggSetUnitB" value="${esc(e.m||'Wdh')}"></label>
      <label>${T('Seite','Side')}<select id="kggSetSide"><option value="BI">${T('beidseitig','bilateral')}</option><option value="LR">${T('links/rechts getrennt','left/right separate')}</option></select></label>
      <label>${T('Schmerz','Pain')}<select id="kggSetPainMode"><option value="exercise">${T('einmal pro Übung','once per exercise')}</option><option value="set">${T('pro Satz','per set')}</option></select></label>
    </div><div class="kggSetActions"><button class="kggSetCancel" id="kggSetCancel">${T('Abbrechen','Cancel')}</button><button class="kggSetSave" id="kggSetSave">${T('Speichern','Save')}</button></div>`;
    $('kggSetSide').value=e.side==='LR'?'LR':'BI';$('kggSetPainMode').value=getPainMode(e);
    $('kggSetCancel').onclick=closeSettings;
    $('kggSetSave').onclick=()=>{const old=e.side; e.u=$('kggSetUnitA').value.trim()||e.u||'kg'; e.m=$('kggSetUnitB').value.trim()||e.m||'Wdh'; e.side=$('kggSetSide').value; setPainMode(e,$('kggSetPainMode').value); copySideValues(i,old,e.side); saveAll(); closeSettings(); openIndex=i; safe(()=>render()); setTimeout(apply,0); st(T('Übung angepasst.','Exercise updated.'))};
    bd.hidden=false;sh.hidden=false;
  }
  function esc(s){return String(s??'').replace(/[&<>"']/g,m=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[m]))}
  function ensureSettingsDom(){if(!$('kggSettingsBackdrop')){let b=document.createElement('div');b.id='kggSettingsBackdrop';b.className='kggSettingsBackdrop';b.hidden=true;b.onclick=closeSettings;document.body.appendChild(b)}if(!$('kggSettingsSheet')){let s=document.createElement('div');s.id='kggSettingsSheet';s.hidden=true;document.body.appendChild(s)}}

  function i18n(){
    document.documentElement.lang=en()?'en':'de';document.body.classList.toggle('kggLangEn',en());
    const h=document.querySelector('main .card h1');if(h)h.textContent=T('KGG Handyplan','KGG Phone Plan');
    const intro=document.querySelector('main .card p.muted');if(intro)intro.textContent=T('Werte direkt am Handy eintragen. Schmerz 0–10 angeben. Daten bleiben lokal auf diesem Gerät.','Enter values directly on the phone. Pain 0–10. Data stays local on this device.');
    const meta=$('meta');if(meta&&safe(()=>p))meta.textContent=(p.ex?.length||0)+' '+T('Übungen','exercises')+' · '+(p.days||0)+' '+T('Trainingstage','training days');
    document.querySelectorAll('#days button').forEach((b,i)=>b.textContent=T('Tag ','Day ')+(i+1));
    const ex=$('extendBtn');if(ex&&safe(()=>p))ex.textContent=T('+ '+p.stepDays+' weitere Tage hinzufügen','Add '+p.stepDays+' more days');
    const db=$('kggPatientDbBtn');if(db)db.textContent=T('📚 Übungsdatenbank','📚 Database');
    const scan=$('kggActionScan');if(scan)scan.textContent='📷 '+T('Plan scannen / aktualisieren','Scan / update plan');
    const add=$('kggActionAddPlan');if(add)add.textContent='➕ '+T('2. Plan hinzufügen','Add 2nd plan');
    document.querySelectorAll('button').forEach(b=>{const x=b.textContent.trim();const map={'Aktuelle Werte als QR zeigen':'Show current values as QR','Show current values as QR':'Show current values as QR','Training beenden & QR anzeigen':'Finish training & show QR','Finish training & show QR':'Finish training & show QR','Zurück zum Plan':'Back to plan','Back to plan':'Back to plan','Abbrechen':'Cancel','Cancel':'Cancel','OK':'OK'}; if(map[x])b.textContent=en()?map[x]:Object.keys(map).find(k=>map[k]===map[x]&&k!==map[x])||x});
    cards().forEach((card,ei)=>{const e=safe(()=>p.ex[ei]);if(!e)return;let m=card.querySelector(':scope > .muted');if(m)m.textContent=(e.sets||3)+' '+T('Sätze','sets')+' · '+sideText(e.side)+' · '+unit(e.u)+' · '+unit(e.m);card.querySelectorAll('.set > b').forEach((b,i)=>b.textContent=T('Satz ','Set ')+(i+1));card.querySelectorAll('.lr span').forEach(sp=>{if(sp.textContent.trim()==='Li'||sp.textContent.trim()==='L')sp.textContent=T('Li','L');else sp.textContent=T('Re','R')})});
  }

  function patchRows(){if(window.__kggPainRowsPatch||typeof rows!=='function')return;window.__kggPainRowsPatch=1;const old=rows;rows=function(day){const out=old(day);safe(()=>out.forEach((r,ei)=>{const e=p.ex[ei];if(getPainMode(e)==='set'){let a=[];for(let s=1;s<=e.sets;s++){let x=v[k(ei,s,'P','pain',day)]||'0';a.push('S'+s+':'+x)}r[6]=a.join(' ')}}));return out}}
  function patchRender(){if(window.__kggAlwaysCardsRenderPatch||typeof render!=='function')return;window.__kggAlwaysCardsRenderPatch=1;const old=render;render=function(){const r=old.apply(this,arguments);setTimeout(apply,0);return r}}
  function apply(){ensureStyle();ensureSettingsDom();forceCards();renderPain();i18n();patchRows()}
  function init(){window.__kggPatientCardSettings=VERSION;patchRender();apply();setTimeout(apply,300);setTimeout(apply,1000)}
  document.readyState==='loading'?document.addEventListener('DOMContentLoaded',init):init();
})();
