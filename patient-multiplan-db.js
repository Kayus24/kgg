(()=>{
  const ADDON_VERSION='v2_action_fab';
  const LANG_KEY='kggPatientLang';
  const $=id=>document.getElementById(id);
  const isEn=()=>localStorage.getItem(LANG_KEY)==='en';
  const t=(de,en)=>isEn()?en:de;

  function ensureStyle(){
    if($('kggMultiPlanDbStyle'))return;
    const s=document.createElement('style');
    s.id='kggMultiPlanDbStyle';
    s.textContent=`
      #installSmall{display:flex!important;align-items:center!important;gap:8px!important;flex-wrap:wrap!important}
      #installSmall .muted,#kggPlanScanBtn,#kggPatientDbBtn,#kggPatientAddPlanBtn{display:none!important}
      #installSmall .btnSmall:not(#kggLangSwitch):not(#kggActionHomeBtn){display:none!important}
      #kggLangSwitch{display:inline-flex!important;align-items:center;justify-content:center;min-height:38px;border-radius:999px;border:1px solid #cbd5e1;background:#fff;color:#111827;padding:6px 10px;font-size:13px;font-weight:950;white-space:nowrap}
      #kggActionFab{position:fixed;right:14px;bottom:calc(14px + env(safe-area-inset-bottom));z-index:2600;width:56px;height:56px;border-radius:999px;border:1px solid #1d4ed8;background:#2563eb;color:white;box-shadow:0 12px 34px rgba(37,99,235,.30);font-size:25px;font-weight:950;display:flex;align-items:center;justify-content:center;touch-action:manipulation;transition:transform .12s ease,background .16s ease}
      #kggActionFab:active{transform:scale(.92)}#kggActionFab.open{background:#111827;border-color:#111827}
      #kggActionSheet{position:fixed;left:12px;right:12px;bottom:calc(82px + env(safe-area-inset-bottom));z-index:2599;max-width:520px;margin:0 auto;background:#fff;border:1px solid #dbe3ef;border-radius:22px;padding:12px;box-shadow:0 22px 70px rgba(15,23,42,.24);transform-origin:bottom center;animation:kggSheetIn .18s ease both}
      #kggActionSheet[hidden]{display:none!important}
      #kggActionSheet h3{margin:2px 4px 10px;font-size:18px;line-height:1.15}
      .kggActionItem{width:100%;min-height:52px;border-radius:16px;border:1px solid #cbd5e1;background:#fff;color:#111827;margin-top:8px;font-size:16px;font-weight:950;text-align:left;padding:10px 12px;display:flex;align-items:center;gap:10px;justify-content:flex-start;touch-action:manipulation}
      .kggActionItem.primary{background:#111827;color:#fff;border-color:#111827}.kggActionItem.blue{background:#eff6ff;border-color:#bfdbfe}.kggActionItem:active{transform:scale(.985);filter:brightness(.98)}
      .kggSheetBackdrop{position:fixed;inset:0;z-index:2598;background:rgba(15,23,42,.20);animation:kggFadeIn .16s ease both}.kggSheetBackdrop[hidden]{display:none!important}
      @keyframes kggSheetIn{from{opacity:0;transform:translateY(12px) scale(.98)}to{opacity:1;transform:translateY(0) scale(1)}}@keyframes kggFadeIn{from{opacity:0}to{opacity:1}}
      @media(max-width:430px){#kggActionFab{width:52px;height:52px;right:12px;bottom:12px;font-size:23px}#kggActionSheet{bottom:76px}.kggActionItem{min-height:50px;font-size:15px}#kggLangSwitch{font-size:12px;padding:6px 9px}}
    `;
    document.head.appendChild(s);
  }

  function ensureHiddenSourceButtons(){
    const row=$('installSmall');
    if(!row)return;
    row.classList.remove('hide');
    row.style.flexWrap='wrap';

    let db=$('kggPatientDbBtn');
    if(!db){
      db=document.createElement('button');
      db.id='kggPatientDbBtn';
      db.type='button';
      db.onclick=e=>{e.preventDefault();e.stopPropagation();alert(t('Übungsdatenbank kommt als nächster Schritt.','Exercise database is the next step.'));};
      row.appendChild(db);
    }
    db.textContent=t('Übungsdatenbank','Database');

    let add=$('kggPatientAddPlanBtn');
    if(!add){
      add=document.createElement('button');
      add.id='kggPatientAddPlanBtn';
      add.type='button';
      add.onclick=e=>{e.preventDefault();e.stopPropagation();const scan=$('kggPlanScanBtn');if(scan)scan.click();else alert(t('QR-Scan noch nicht geladen.','QR scan not loaded yet.'));};
      row.appendChild(add);
    }
    add.textContent=t('2. Plan +','2nd plan +');
  }

  function closeSheet(){
    const sh=$('kggActionSheet'),bd=$('kggActionBackdrop'),fab=$('kggActionFab');
    if(sh)sh.hidden=true;if(bd)bd.hidden=true;if(fab)fab.classList.remove('open');
  }
  function toggleSheet(){
    const sh=$('kggActionSheet'),bd=$('kggActionBackdrop'),fab=$('kggActionFab');
    if(!sh||!bd)return;
    const open=sh.hidden;
    sh.hidden=!open;bd.hidden=!open;if(fab)fab.classList.toggle('open',open);
  }
  function clickSource(id){
    closeSheet();
    const el=$(id);
    if(el)el.click();
    else alert(t('Funktion noch nicht geladen.','Function not loaded yet.'));
  }
  function clickHome(){
    closeSheet();
    const row=$('installSmall');
    const btn=row?[...row.querySelectorAll('button')].find(b=>!['kggLangSwitch','kggPlanScanBtn','kggPatientDbBtn','kggPatientAddPlanBtn','kggActionHomeBtn'].includes(b.id)):null;
    if(btn)btn.click();
    else alert(t('Startbildschirm-Hilfe noch nicht geladen.','Home screen help not loaded yet.'));
  }

  function ensureActionMenu(){
    ensureStyle();
    ensureHiddenSourceButtons();
    if(!$('kggActionBackdrop')){
      const bd=document.createElement('div');bd.id='kggActionBackdrop';bd.className='kggSheetBackdrop';bd.hidden=true;bd.onclick=closeSheet;document.body.appendChild(bd);
    }
    let sh=$('kggActionSheet');
    if(!sh){
      sh=document.createElement('div');sh.id='kggActionSheet';sh.hidden=true;document.body.appendChild(sh);
    }
    sh.innerHTML=`
      <h3>${t('Planaktionen','Plan actions')}</h3>
      <button type="button" class="kggActionItem primary" id="kggActionScan">📷 ${t('Plan scannen / aktualisieren','Scan / update plan')}</button>
      <button type="button" class="kggActionItem blue" id="kggActionAddPlan">➕ ${t('2. Plan hinzufügen','Add 2nd plan')}</button>
      <button type="button" class="kggActionItem" id="kggActionDb">📚 ${t('Übungsdatenbank','Exercise database')}</button>
      <button type="button" class="kggActionItem" id="kggActionHome">🏠 ${t('Startbildschirm','Home screen')}</button>`;
    $('kggActionScan').onclick=()=>clickSource('kggPlanScanBtn');
    $('kggActionAddPlan').onclick=()=>clickSource('kggPatientAddPlanBtn');
    $('kggActionDb').onclick=()=>clickSource('kggPatientDbBtn');
    $('kggActionHome').onclick=clickHome;

    let fab=$('kggActionFab');
    if(!fab){
      fab=document.createElement('button');fab.id='kggActionFab';fab.type='button';fab.textContent='📷';fab.title=t('Planaktionen','Plan actions');fab.onclick=e=>{e.preventDefault();e.stopPropagation();toggleSheet();};document.body.appendChild(fab);
    }
    fab.title=t('Planaktionen','Plan actions');
  }

  function patchRender(){
    if(window.__kggPatientMultiPlanDbRenderPatch)return;
    window.__kggPatientMultiPlanDbRenderPatch=true;
    if(typeof render==='function'){
      const old=render;
      window.render=function(){
        const r=old.apply(this,arguments);
        setTimeout(ensureActionMenu,0);
        return r;
      };
    }
  }

  function init(){
    window.__kggPatientMultiPlanDbAddon=ADDON_VERSION;
    patchRender();
    ensureActionMenu();
    setTimeout(ensureActionMenu,300);
    setTimeout(ensureActionMenu,1000);
  }

  document.readyState==='loading'?document.addEventListener('DOMContentLoaded',init):init();
})();
