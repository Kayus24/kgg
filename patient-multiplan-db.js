(()=>{
  const ADDON_VERSION='v6_vertical_camera_bubbles';
  const LANG_KEY='kggPatientLang';
  const MULTI_KEY='kggPatientMultiPlansV1';
  const CURRENT_KEY='kggCurrentPlanV1';
  const $=id=>document.getElementById(id);
  const isEn=()=>localStorage.getItem(LANG_KEY)==='en';
  const t=(de,en)=>isEn()?en:de;
  const safe=f=>{try{return f()}catch(e){return null}};

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
      #kggActionBubbles[hidden]{display:none!important}.kggBubble{min-height:42px;border-radius:999px;border:1px solid #cbd5e1;background:#fff;color:#111827;padding:8px 13px;font-size:14px;font-weight:950;box-shadow:0 10px 28px rgba(15,23,42,.16);touch-action:manipulation;pointer-events:auto;animation:kggBubbleUp .20s cubic-bezier(.16,.84,.44,1) both;white-space:nowrap}.kggBubble.primary{background:#111827;color:#fff;border-color:#111827}.kggBubble:active{transform:scale(.96)}.kggBubble:nth-child(1){animation-delay:.02s}.kggBubble:nth-child(2){animation-delay:.065s}
      @keyframes kggBubbleUp{from{opacity:0;transform:translateY(14px) scale(.94)}to{opacity:1;transform:translateY(0) scale(1)}}
      @media(max-width:430px){#kggActionFab{width:52px;height:52px;left:12px;bottom:12px;font-size:23px}#kggActionBubbles{left:12px;bottom:72px}.kggBubble{font-size:13px;min-height:40px;padding:8px 11px}}
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

  function ensureSourceButtons(){
    const row=$('installSmall'); if(!row)return; row.classList.remove('hide');
    let db=$('kggPatientDbBtn');
    if(!db){db=document.createElement('button');db.id='kggPatientDbBtn';db.type='button';db.onclick=e=>{e.preventDefault();e.stopPropagation();alert(t('Übungsdatenbank kommt als nächster Schritt.','Exercise database is the next step.'))};row.appendChild(db)}
    db.textContent=t('📚 Übungsdatenbank','📚 Database');
    let add=$('kggPatientAddPlanBtn');
    if(!add){add=document.createElement('button');add.id='kggPatientAddPlanBtn';add.type='button';add.onclick=e=>{e.preventDefault();e.stopPropagation();const scan=$('kggPlanScanBtn');if(scan)scan.click();else alert(t('QR-Scan noch nicht geladen.','QR scan not loaded yet.'))};row.appendChild(add)}
    add.textContent=t('2. Plan +','2nd plan +');
  }
  function closeBubbles(){const b=$('kggActionBubbles'),fab=$('kggActionFab');if(b)b.hidden=true;if(fab)fab.classList.remove('open')}
  function toggleBubbles(){const b=$('kggActionBubbles'),fab=$('kggActionFab');if(!b)return;const open=b.hidden;b.hidden=!open;if(fab)fab.classList.toggle('open',open)}
  function clickSource(id){closeBubbles();const el=$(id);if(el)el.click();else alert(t('Funktion noch nicht geladen.','Function not loaded yet.'))}
  function ensureActionBubbles(){
    ensureStyle(); ensureSourceButtons(); ensureState();
    let box=$('kggActionBubbles'); if(!box){box=document.createElement('div');box.id='kggActionBubbles';box.hidden=true;document.body.appendChild(box)}
    box.innerHTML=`<button type="button" class="kggBubble primary" id="kggBubbleScan">📷 ${t('Aktualisieren','Update')}</button><button type="button" class="kggBubble" id="kggBubbleAdd">➕ ${t('2. Plan','2nd plan')}</button>`;
    $('kggBubbleScan').onclick=()=>clickSource('kggPlanScanBtn');
    $('kggBubbleAdd').onclick=()=>clickSource('kggPatientAddPlanBtn');
    let fab=$('kggActionFab'); if(!fab){fab=document.createElement('button');fab.id='kggActionFab';fab.type='button';fab.textContent='📷';fab.title=t('Planaktionen','Plan actions');fab.onclick=e=>{e.preventDefault();e.stopPropagation();toggleBubbles()};document.body.appendChild(fab)}
    fab.textContent='📷';fab.title=t('Planaktionen','Plan actions');fab.onclick=e=>{e.preventDefault();e.stopPropagation();toggleBubbles()};
  }
  function patchRender(){if(window.__kggPatientMultiPlanDbRenderPatch)return;window.__kggPatientMultiPlanDbRenderPatch=true;if(typeof render==='function'){const old=render;window.render=function(){const r=old.apply(this,arguments);setTimeout(ensureActionBubbles,0);return r}}}
  function init(){window.__kggPatientMultiPlanDbAddon=ADDON_VERSION;window.KGGPatientMultiPlan={switchTo,ensureState,saveCurrentSlot};patchRender();ensureActionBubbles();setTimeout(ensureActionBubbles,300);setTimeout(ensureActionBubbles,1000)}
  document.readyState==='loading'?document.addEventListener('DOMContentLoaded',init):init();
})();
