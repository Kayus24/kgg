(()=>{
  const ID='kggAppVersion';
  const RELEASE='62';
  const BANNER_ID='kggUpdateGate';
  const RELOAD_KEY='kgg-sw-reload-v'+RELEASE;
  const UPDATE_TIMEOUT_MS=8000;
  let registration=null;
  let waitingWorker=null;
  let updateRequested=false;
  let reloadDone=false;
  let updateTimer=0;

  function fallbackVersion(){
    try{
      const src=document.currentScript&&document.currentScript.src?document.currentScript.src:'';
      const raw=new URL(src||location.href,location.href).searchParams.get('v')||'';
      return raw?'v'+String(raw).replace(/^v/i,''):'v?';
    }catch(e){
      return 'v?';
    }
  }

  function mount(version){
    let el=document.getElementById(ID);
    if(!el){
      el=document.createElement('div');
      el.id=ID;
      const main=document.querySelector('main');
      if(main) main.insertAdjacentElement('afterend',el);
      else document.body.appendChild(el);
    }
    el.textContent=version;
    el.title='KGG App-Version '+version;
    el.setAttribute('aria-label','KGG App-Version '+version);
    el.style.cssText='max-width:760px;margin:-4px auto 0;padding:0 14px calc(10px + env(safe-area-inset-bottom));text-align:right;font:500 10px/1.2 system-ui,-apple-system,Segoe UI,Roboto,Arial,sans-serif;color:#94a3b8;letter-spacing:.02em;user-select:text;';
  }

  function currentPadIsOpen(){
    const pad=document.getElementById('pad');
    return Boolean(pad&&!pad.classList.contains('hide'));
  }

  function persistCurrentValues(){
    try{
      if(typeof window.safeSave==='function') window.safeSave();
    }catch(e){}
  }

  function setBannerStatus(text,isError){
    const status=document.getElementById(BANNER_ID+'Status');
    if(!status)return;
    status.textContent=text;
    status.style.color=isError?'#b91c1c':'#475569';
  }

  function removeBanner(){
    const banner=document.getElementById(BANNER_ID);
    if(banner) banner.remove();
  }

  function showUpdateBanner(worker){
    if(!worker||!navigator.serviceWorker.controller)return;
    waitingWorker=worker;
    let banner=document.getElementById(BANNER_ID);
    if(banner)return;

    banner=document.createElement('section');
    banner.id=BANNER_ID;
    banner.setAttribute('role','status');
    banner.setAttribute('aria-live','polite');
    banner.style.cssText='position:fixed;left:12px;right:12px;bottom:12px;z-index:9000;max-width:720px;margin:auto;padding:12px 14px;border:1px solid #cbd5e1;border-radius:16px;background:#fff;box-shadow:0 16px 42px #0f172a33;font:500 14px/1.35 system-ui,-apple-system,Segoe UI,Roboto,Arial,sans-serif;color:#111827;';

    const title=document.createElement('strong');
    title.textContent='Neue Version verfügbar';
    title.style.display='block';

    const status=document.createElement('div');
    status.id=BANNER_ID+'Status';
    status.textContent='Bitte jetzt aktualisieren, damit der Plan zuverlässig funktioniert.';
    status.style.cssText='margin-top:3px;color:#475569;';

    const actions=document.createElement('div');
    actions.style.cssText='display:grid;grid-template-columns:1fr 1fr;gap:8px;margin-top:10px;';

    const later=document.createElement('button');
    later.type='button';
    later.textContent='Später';
    later.style.cssText='min-height:44px;border:1px solid #cbd5e1;border-radius:12px;background:#fff;color:#111827;font-weight:800;';
    later.addEventListener('click',removeBanner);

    const update=document.createElement('button');
    update.type='button';
    update.id=BANNER_ID+'Button';
    update.textContent='Jetzt aktualisieren';
    update.style.cssText='min-height:44px;border:1px solid #111827;border-radius:12px;background:#111827;color:#fff;font-weight:900;';
    update.addEventListener('click',applyWaitingUpdate);

    actions.append(later,update);
    banner.append(title,status,actions);
    document.body.appendChild(banner);
  }

  function monitorRegistration(reg){
    if(!reg)return;
    registration=reg;
    if(reg.waiting) showUpdateBanner(reg.waiting);
    reg.addEventListener('updatefound',()=>{
      const worker=reg.installing;
      if(!worker)return;
      worker.addEventListener('statechange',()=>{
        if(worker.state==='installed'&&navigator.serviceWorker.controller){
          showUpdateBanner(reg.waiting||worker);
        }
      });
    });
  }

  function applyWaitingUpdate(){
    if(updateRequested)return;
    if(currentPadIsOpen()){
      setBannerStatus('Bitte die offene Eingabe zuerst mit OK abschließen.',true);
      return;
    }
    const worker=registration&&registration.waiting?registration.waiting:waitingWorker;
    if(!worker){
      setBannerStatus('Das Update ist noch nicht vollständig geladen. Bitte kurz warten.',true);
      return;
    }

    persistCurrentValues();
    updateRequested=true;
    const button=document.getElementById(BANNER_ID+'Button');
    if(button){
      button.disabled=true;
      button.textContent='Aktualisierung läuft…';
    }
    setBannerStatus('Die neue Version wird aktiviert.',false);

    clearTimeout(updateTimer);
    updateTimer=setTimeout(()=>{
      if(reloadDone)return;
      updateRequested=false;
      if(button){
        button.disabled=false;
        button.textContent='Jetzt aktualisieren';
      }
      setBannerStatus('Aktivierung hat nicht geantwortet. Bitte erneut versuchen.',true);
    },UPDATE_TIMEOUT_MS);

    try{
      worker.postMessage({type:'SKIP_WAITING'});
    }catch(e){
      clearTimeout(updateTimer);
      updateRequested=false;
      if(button){
        button.disabled=false;
        button.textContent='Jetzt aktualisieren';
      }
      setBannerStatus('Update konnte nicht gestartet werden.',true);
    }
  }

  function getActiveVersion(fallback){
    return new Promise(resolve=>{
      const controller=navigator.serviceWorker&&navigator.serviceWorker.controller;
      if(!controller||typeof MessageChannel==='undefined'){
        resolve(fallback);
        return;
      }
      const channel=new MessageChannel();
      let finished=false;
      const finish=value=>{
        if(finished)return;
        finished=true;
        resolve(value||fallback);
      };
      const timer=setTimeout(()=>finish(fallback),600);
      channel.port1.onmessage=event=>{
        clearTimeout(timer);
        const version=event.data&&event.data.type==='APP_VERSION'?event.data.version:'';
        finish(version?'v'+String(version).replace(/^v/i,''):fallback);
      };
      try{
        controller.postMessage({type:'GET_APP_VERSION'},[channel.port2]);
      }catch(e){
        clearTimeout(timer);
        finish(fallback);
      }
    });
  }

  async function findRegistration(){
    for(let attempt=0;attempt<8;attempt++){
      try{
        const reg=await navigator.serviceWorker.getRegistration('./');
        if(reg)return reg;
      }catch(e){}
      await new Promise(resolve=>setTimeout(resolve,150));
    }
    return null;
  }

  async function init(){
    const fallback=fallbackVersion();
    mount(fallback);
    if(!('serviceWorker' in navigator))return;

    navigator.serviceWorker.addEventListener('controllerchange',()=>{
      if(!updateRequested||reloadDone)return;
      reloadDone=true;
      clearTimeout(updateTimer);
      if(sessionStorage.getItem(RELOAD_KEY)==='1')return;
      sessionStorage.setItem(RELOAD_KEY,'1');
      location.reload();
    });

    const reg=await findRegistration();
    if(reg){
      monitorRegistration(reg);
      try{await reg.update()}catch(e){}
      if(reg.waiting)showUpdateBanner(reg.waiting);
    }
    mount(await getActiveVersion(fallback));
  }

  if(document.readyState==='loading') document.addEventListener('DOMContentLoaded',init,{once:true});
  else init();
})();
