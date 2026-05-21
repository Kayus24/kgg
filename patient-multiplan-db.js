(()=>{
  const ADDON_VERSION='v1_buttons_only';
  const LANG_KEY='kggPatientLang';
  const $=id=>document.getElementById(id);
  const isEn=()=>localStorage.getItem(LANG_KEY)==='en';
  const t=(de,en)=>isEn()?en:de;

  function ensureStyle(){
    if($('kggMultiPlanDbStyle'))return;
    const s=document.createElement('style');
    s.id='kggMultiPlanDbStyle';
    s.textContent=`
      .kggPatientMiniBtn{min-height:38px;border-radius:999px;border:1px solid #cbd5e1;background:#fff;color:#111827;padding:6px 10px;font-size:13px;font-weight:950;white-space:nowrap;touch-action:manipulation}
      .kggPatientMiniBtn:active{transform:scale(.96);background:#f8fafc}
      #kggPatientDbBtn{background:#f8fafc}
      #kggPatientAddPlanBtn{background:#eff6ff;border-color:#bfdbfe}
      @media(max-width:430px){.kggPatientMiniBtn{font-size:12px;padding:6px 9px}}
    `;
    document.head.appendChild(s);
  }

  function ensureButtons(){
    const row=$('installSmall');
    if(!row)return;
    ensureStyle();
    row.classList.remove('hide');
    row.style.flexWrap='wrap';

    let db=$('kggPatientDbBtn');
    if(!db){
      db=document.createElement('button');
      db.id='kggPatientDbBtn';
      db.type='button';
      db.className='kggPatientMiniBtn';
      db.onclick=e=>{
        e.preventDefault();
        e.stopPropagation();
        alert(t('Übungsdatenbank kommt als nächster Schritt.','Exercise database is the next step.'));
      };
      row.appendChild(db);
    }
    db.textContent=t('Übungsdatenbank','Database');

    let add=$('kggPatientAddPlanBtn');
    if(!add){
      add=document.createElement('button');
      add.id='kggPatientAddPlanBtn';
      add.type='button';
      add.className='kggPatientMiniBtn';
      add.onclick=e=>{
        e.preventDefault();
        e.stopPropagation();
        const scan=$('kggPlanScanBtn');
        if(scan)scan.click();
        else alert(t('QR-Scan noch nicht geladen.','QR scan not loaded yet.'));
      };
      row.appendChild(add);
    }
    add.textContent=t('2. Plan +','2nd plan +');
  }

  function patchRender(){
    if(window.__kggPatientMultiPlanDbRenderPatch)return;
    window.__kggPatientMultiPlanDbRenderPatch=true;
    if(typeof render==='function'){
      const old=render;
      window.render=function(){
        const r=old.apply(this,arguments);
        setTimeout(ensureButtons,0);
        return r;
      };
    }
  }

  function init(){
    window.__kggPatientMultiPlanDbAddon=ADDON_VERSION;
    patchRender();
    ensureButtons();
    setTimeout(ensureButtons,300);
    setTimeout(ensureButtons,1000);
  }

  document.readyState==='loading'?document.addEventListener('DOMContentLoaded',init):init();
})();
