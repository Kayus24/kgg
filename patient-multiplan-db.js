(()=>{
  const ADDON_VERSION='v7_local_exercise_db_big_bubbles';
  const LANG_KEY='kggPatientLang';
  const MULTI_KEY='kggPatientMultiPlansV1';
  const CURRENT_KEY='kggCurrentPlanV1';
  const $=id=>document.getElementById(id);
  const isEn=()=>localStorage.getItem(LANG_KEY)==='en';
  const t=(de,en)=>isEn()?en:de;
  const safe=f=>{try{return f()}catch(e){return null}};
  const norm=s=>String(s||'').toLowerCase().normalize('NFD').replace(/[\u0300-\u036f]/g,'').replace(/[^a-z0-9äöüß]+/g,' ').replace(/\s+/g,' ').trim();
  const esc=s=>String(s??'').replace(/[&<>"']/g,m=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[m]));

  function ensureStyle(){
    const old=$('kggMultiPlanDbStyle'); if(old)old.remove();
    const s=document.createElement('style'); s.id='kggMultiPlanDbStyle';
    s.textContent=`
      #installSmall{display:grid!important;grid-template-columns:auto 1fr auto!important;align-items:center!important;gap:8px!important;margin-top:10px!important}
      #installSmall .muted,#kggPlanScanBtn,#kggPatientAddPlanBtn{display:none!important}
      #installSmall .btnSmall:not(#kggLangSwitch):not(#kggPatientDbBtn){display:none!important}
      #kggLangSwitch{grid-column:1!important;display:inline-flex!important;align-items:center;justify-content:center;min-height:38px;border-radius:999px;border:1px solid #cbd5e1;background:#fff;color:#111827;padding:6px 10px;font-size:13px;font-weight:950;white-space:nowrap}
      #kggPatientDbBtn{grid-column:3!important;display:inline-flex!important;align-items:center;justify-content:center;min-height:38px;border-radius:999px;border:1px solid #cbd5e1;background:#fff;color:#111827;padding:6px 12px;font-size:13px;font-weight:950;white-space:nowrap;touch-action:manipulation}
      #kggPatientDbBtn:active,#kggLangSwitch:active{transform:scale(.96);background:#f8fafc}
      #kggActionFab{position:fixed;left:14px;bottom:calc(14px + env(safe-area-inset-bottom));z-index:2600;width:56px;height:56px;border-radius:999px;border:1px solid #1d4ed8;background:#2563eb;color:white;box-shadow:0 12px 34px rgba(37,99,235,.30);font-size:25px;font-weight:950;display:flex;align-items:center;justify-content:center;touch-action:manipulation;transition:transform .12s ease,background .16s ease}
      #kggActionFab:active{transform:scale(.92)}#kggActionFab.open{background:#111827;border-color:#111827}
      #kggActionBackdrop,#kggActionSheet{display:none!important}
      #kggActionBubbles{position:fixed;left:14px;bottom:calc(78px + env(safe-area-inset-bottom));z-index:2601;display:flex;flex-direction:column;gap:8px;align-items:flex-start;pointer-events:none}
      #kggActionBubbles[hidden]{display:none!important}.kggBubble{min-height:56px;min-width:56px;border-radius:999px;border:1px solid #cbd5e1;background:#fff;color:#111827;padding:10px 16px;font-size:15px;font-weight:950;box-shadow:0 10px 28px rgba(15,23,42,.16);touch-action:manipulation;pointer-events:auto;animation:kggBubbleUp .20s cubic-bezier(.16,.84,.44,1) both;white-space:nowrap;display:flex;align-items:center;justify-content:center}.kggBubble.primary{background:#111827;color:#fff;border-color:#111827}.kggBubble:active{transform:scale(.96)}.kggBubble:nth-child(1){animation-delay:.02s}.kggBubble:nth-child(2){animation-delay:.065s}
      @keyframes kggBubbleUp{from{opacity:0;transform:translateY(14px) scale(.94)}to{opacity:1;transform:translateY(0) scale(1)}}
      #kggDbBackdrop{position:fixed;inset:0;z-index:2680;background:rgba(15,23,42,.12);backdrop-filter:blur(1px);animation:kggDbFade .14s ease both}#kggDbBackdrop[hidden]{display:none!important}
      #kggDbPanel{position:fixed;z-index:2681;right:12px;top:96px;width:min(430px,calc(100vw - 24px));max-height:calc(100dvh - 126px);overflow:auto;-webkit-overflow-scrolling:touch;background:rgba(255,255,255,.98);border:1px solid #dbe3ef;border-radius:20px;padding:12px;box-shadow:0 22px 70px rgba(15,23,42,.22);animation:kggDbIn .18s cubic-bezier(.16,.84,.44,1) both}#kggDbPanel[hidden]{display:none!important}
      .kggDbHead{display:flex;align-items:center;justify-content:space-between;gap:10px;margin-bottom:10px}.kggDbHead h3{margin:0;font-size:18px}.kggDbClose{width:38px;height:38px;border-radius:999px;border:1px solid #cbd5e1;background:#fff;font-size:22px;font-weight:950}.kggDbSearch{width:100%;min-height:42px;border-radius:14px;border:1px solid #cbd5e1;padding:8px 11px;font-size:15px;margin-bottom:10px}.kggDbList{display:grid;gap:8px}.kggDbCard{border:1px solid #dbe3ef;border-radius:15px;background:#fff;padding:9px 10px;text-align:left;width:100%;touch-action:manipulation}.kggDbCard:active{transform:scale(.99);background:#eff6ff}.kggDbCard b{font-size:15px}.kggDbMeta{font-size:12px;color:#64748b;margin-top:3px}.kggDbAdd{margin-top:7px;border-radius:999px;border:1px solid #bbf7d0;background:#ecfdf5;color:#166534;padding:6px 9px;font-size:12px;font-weight:950;display:inline-flex}.kggDbAlready{margin-top:7px;border-radius:999px;border:1px solid #cbd5e1;background:#f8fafc;color:#64748b;padding:6px 9px;font-size:12px;font-weight:950;display:inline-flex}.kggDbEmpty{font-size:13px;color:#64748b;text-align:center;padding:18px 8px}
      @keyframes kggDbIn{from{opacity:0;transform:translateY(-8px) scale(.985)}to{opacity:1;transform:translateY(0) scale(1)}}@keyframes kggDbFade{from{opacity:0}to{opacity:1}}
      @media(max-width:430px){#kggActionFab{width:52px;height:52px;left:12px;bottom:12px;font-size:23px}#kggActionBubbles{left:12px;bottom:72px}.kggBubble{min-height:52px;min-width:52px;font-size:14px;padding:9px 13px}#kggDbPanel{left:10px;right:10px;top:88px;width:auto;max-height:calc(100dvh - 112px)}}
    `;
    document.head.appendChild(s);
  }

  function exObj(e){if(!Array.isArray(e))e=[];return{n:e[0]||'Übung',sets:Number(e[1])||3,side:e[2]||'LR',u:e[3]||'kg',m:e[4]||'Wdh',sl:e[5]||'',sm:e[6]||'',media:e[7]||'',videoUrl:e[8]||'',videoLabel:e[9]||'Video öffnen',painMode:e[10]||'exercise'}}
  function exRaw(e){return[e.n,e.sets,e.side,e.u,e.m,e.sl||'',e.sm||'',e.media||'',e.videoUrl||'',e.videoLabel||'Video öffnen',e.painMode||'exercise']}
  function rawFromRuntime(){return{i:p?.id||'plan',t:p?.title||'KGG Trainingsplan',v:p?.version||1,d:p?.days||6,extendDays:p?p.extendDays!==false:true,stepDays:p?.stepDays||6,e:Array.isArray(p?.ex)?p.ex.map(exRaw):[]}}
  function runtimeFromRaw(raw){return{id:raw.i||'plan',title:raw.t||'KGG Trainingsplan',version:+raw.v||1,days:+raw.d||6,extendDays:raw.extendDays!==false,stepDays:+raw.stepDays||6,ex:(raw.e||[]).map(exObj)}}
  function readState(){try{return JSON.parse(localStorage.getItem(MULTI_KEY)||'null')}catch(e){return null}}
  function writeState(s){s.updatedAt=new Date().toISOString();localStorage.setItem(MULTI_KEY,JSON.stringify(s))}
  function ensureState(){let s=readState();if(!s||!Array.isArray(s.plans))s={version:1,plans:[],active:0,day:{}};if(!s.plans.length&&safe(()=>p))s.plans.push(rawFromRuntime());s.day=s.day||{};if(typeof s.active!=='number')s.active=0;writeState(s);return s}
  function saveCurrentSlot(){const s=ensureState();const i=Math.max(0,Math.min(Number(s.active)||0,s.plans.length-1));safe(()=>safeSave());s.plans[i]=rawFromRuntime();writeState(s);localStorage.setItem(CURRENT_KEY,JSON.stringify({plan:s.plans[i],importedAt:new Date().toISOString()}))}
  function loadValuesForPlan(){safe(()=>{v=read(sk(),'{}')});safe(()=>{done=read(dk(),'[]').map(Number).filter(n=>n>=1&&n<=p.days)})}
  function switchTo(idx){const s=ensureState();if(!s.plans[idx])return false;if(Number(s.active)===idx)return true;saveCurrentSlot();s.active=idx;writeState(s);p=runtimeFromRaw(s.plans[idx]);localStorage.setItem(CURRENT_KEY,JSON.stringify({plan:s.plans[idx],importedAt:new Date().toISOString()}));loadValuesForPlan();safe(()=>save());safe(()=>render());safe(()=>setStatus(t('Plan gewechselt. Werte bleiben erhalten.','Plan switched. Values kept.'),'ok'));return true}

  function currentHas(name){const key=norm(name);return Array.isArray(p?.ex)&&p.ex.some(ex=>norm(ex.n)===key)}
  function collectDb(){
    const s=ensureState();const map=new Map();
    const add=(ex,source)=>{const o=Array.isArray(ex)?exObj(ex):ex;if(!o||!o.n)return;const key=norm(o.n);if(!key)return;if(!map.has(key))map.set(key,{...o,source});};
    (s.plans||[]).forEach((pl,pi)=>(pl.e||[]).forEach(ex=>add(ex,pl.t||t('Plan ','Plan ')+(pi+1))));
    safe(()=>p.ex.forEach(ex=>add(ex,t('aktueller Plan','current plan'))));
    return [...map.values()].sort((a,b)=>String(a.n).localeCompare(String(b.n),'de'));
  }
  function ensureDbDom(){
    if(!$('kggDbBackdrop')){const bd=document.createElement('div');bd.id='kggDbBackdrop';bd.hidden=true;bd.onclick=closeDb;document.body.appendChild(bd)}
    if(!$('kggDbPanel')){const pn=document.createElement('div');pn.id='kggDbPanel';pn.hidden=true;pn.onclick=e=>e.stopPropagation();document.body.appendChild(pn)}
  }
  function closeDb(){const bd=$('kggDbBackdrop'),pn=$('kggDbPanel');if(bd)bd.hidden=true;if(pn)pn.hidden=true}
  function openDb(){ensureStyle();ensureDbDom();renderDb('');$('kggDbBackdrop').hidden=false;$('kggDbPanel').hidden=false;setTimeout(()=>{const s=$('kggDbSearch');if(s)s.focus({preventScroll:true})},80)}
  function renderDb(filter){
    const pn=$('kggDbPanel');if(!pn)return;
    const q=norm(filter);const all=collectDb();const list=q?all.filter(ex=>norm(ex.n+' '+ex.u+' '+ex.m).includes(q)):all;
    pn.innerHTML=`<div class="kggDbHead"><h3>${t('📚 Übungsdatenbank','📚 Exercise database')}</h3><button class="kggDbClose" id="kggDbClose" type="button">×</button></div><input id="kggDbSearch" class="kggDbSearch" value="${esc(filter||'')}" placeholder="${t('Übung suchen','Search exercise')}"><div class="kggDbList">${list.length?list.map((ex,i)=>dbCard(ex,i)).join(''):`<div class="kggDbEmpty">${t('Noch keine lokalen Übungen gespeichert.','No local exercises saved yet.')}</div>`}</div>`;
    $('kggDbClose').onclick=closeDb;
    $('kggDbSearch').oninput=e=>renderDb(e.target.value);
    pn.querySelectorAll('.kggDbCard').forEach(card=>card.onclick=()=>addExerciseFromDb(list[Number(card.dataset.i)]));
  }
  function dbCard(ex,i){
    const already=currentHas(ex.n);
    return `<button type="button" class="kggDbCard" data-i="${i}"><b>${esc(ex.n)}</b><div class="kggDbMeta">${esc(String(ex.sets||3))} · ${ex.side==='LR'?t('links/rechts','left/right'):t('beidseitig','bilateral')} · ${esc(ex.u||'kg')} / ${esc(ex.m||'Wdh')}<br>${esc(ex.source||'')}</div><span class="${already?'kggDbAlready':'kggDbAdd'}">${already?t('schon im Plan','already in plan'):t('+ in Plan holen','+ add to plan')}</span></button>`;
  }
  function addExerciseFromDb(ex){
    if(!ex||currentHas(ex.n)){closeDb();return}
    saveCurrentSlot();
    p.ex=p.ex||[];p.ex.push({...ex});
    const s=ensureState();const i=Math.max(0,Math.min(Number(s.active)||0,s.plans.length-1));
    s.plans[i]=rawFromRuntime();writeState(s);localStorage.setItem(CURRENT_KEY,JSON.stringify({plan:s.plans[i],importedAt:new Date().toISOString()}));
    safe(()=>save());safe(()=>render());safe(()=>setStatus(t('Übung aus Datenbank hinzugefügt.','Exercise added from database.'),'ok'));
    closeDb();
  }

  function ensureSourceButtons(){
    const row=$('installSmall'); if(!row)return; row.classList.remove('hide');
    let db=$('kggPatientDbBtn');
    if(!db){db=document.createElement('button');db.id='kggPatientDbBtn';db.type='button';row.appendChild(db)}
    db.onclick=e=>{e.preventDefault();e.stopPropagation();openDb()};
    db.textContent=t('📚 Übungsdatenbank','📚 Database');
    let add=$('kggPatientAddPlanBtn');
    if(!add){add=document.createElement('button');add.id='kggPatientAddPlanBtn';add.type='button';add.onclick=e=>{e.preventDefault();e.stopPropagation();const scan=$('kggPlanScanBtn');if(scan)scan.click();else alert(t('QR-Scan noch nicht geladen.','QR scan not loaded yet.'))};row.appendChild(add)}
    add.textContent=t('2. Plan +','2nd plan +');
  }
  function closeBubbles(){const b=$('kggActionBubbles'),fab=$('kggActionFab');if(b)b.hidden=true;if(fab)fab.classList.remove('open')}
  function toggleBubbles(){const b=$('kggActionBubbles'),fab=$('kggActionFab');if(!b)return;const open=b.hidden;b.hidden=!open;if(fab)fab.classList.toggle('open',open)}
  function clickSource(id){closeBubbles();const el=$(id);if(el)el.click();else alert(t('Funktion noch nicht geladen.','Function not loaded yet.'))}
  function ensureActionBubbles(){
    ensureStyle(); ensureSourceButtons(); ensureState(); ensureDbDom();
    let box=$('kggActionBubbles'); if(!box){box=document.createElement('div');box.id='kggActionBubbles';box.hidden=true;document.body.appendChild(box)}
    box.innerHTML=`<button type="button" class="kggBubble primary" id="kggBubbleScan">📷 ${t('Aktualisieren','Update')}</button><button type="button" class="kggBubble" id="kggBubbleAdd">➕ ${t('2. Plan','2nd plan')}</button>`;
    $('kggBubbleScan').onclick=()=>clickSource('kggPlanScanBtn');
    $('kggBubbleAdd').onclick=()=>clickSource('kggPatientAddPlanBtn');
    let fab=$('kggActionFab'); if(!fab){fab=document.createElement('button');fab.id='kggActionFab';fab.type='button';fab.textContent='📷';fab.title=t('Planaktionen','Plan actions');document.body.appendChild(fab)}
    fab.textContent='📷';fab.title=t('Planaktionen','Plan actions');fab.onclick=e=>{e.preventDefault();e.stopPropagation();toggleBubbles()};
  }
  function patchRender(){if(window.__kggPatientMultiPlanDbRenderPatch)return;window.__kggPatientMultiPlanDbRenderPatch=true;if(typeof render==='function'){const old=render;window.render=function(){const r=old.apply(this,arguments);setTimeout(ensureActionBubbles,0);return r}}}
  function init(){window.__kggPatientMultiPlanDbAddon=ADDON_VERSION;window.KGGPatientMultiPlan={switchTo,ensureState,saveCurrentSlot};patchRender();ensureActionBubbles();setTimeout(ensureActionBubbles,300);setTimeout(ensureActionBubbles,1000)}
  document.readyState==='loading'?document.addEventListener('DOMContentLoaded',init):init();
})();
