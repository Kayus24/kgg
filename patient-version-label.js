(()=>{
  const ID='kggAppVersion';
  const RELEASE='61';
  const RELOAD_KEY='kgg-sw-controller-v'+RELEASE;

  function fallbackVersion(){
    try{
      const src=document.currentScript&&document.currentScript.src?document.currentScript.src:'';
      const raw=new URL(src||location.href,location.href).searchParams.get('v')||'';
      return raw?'v'+String(raw).replace(/^v/i,''):'v?';
    }catch(e){
      return 'v?';
    }
  }

  function refreshManifestLink(){
    try{
      const link=document.querySelector('link[rel~="manifest"]');
      if(!link)return;
      const url=new URL(link.getAttribute('href')||'./manifest.json',location.href);
      url.searchParams.set('v',RELEASE);
      link.href=url.href;
    }catch(e){}
  }

  async function refreshServiceWorker(){
    if(!('serviceWorker' in navigator))return;
    try{
      let reloading=false;
      navigator.serviceWorker.addEventListener('controllerchange',()=>{
        if(reloading||sessionStorage.getItem(RELOAD_KEY)==='1')return;
        reloading=true;
        sessionStorage.setItem(RELOAD_KEY,'1');
        location.reload();
      });
      await navigator.serviceWorker.register('./service-worker.js?v='+RELEASE,{scope:'./',updateViaCache:'none'});
      const registration=await navigator.serviceWorker.getRegistration('./');
      if(registration)await registration.update();
    }catch(e){}
  }

  async function resolveVersion(){
    const fallback=fallbackVersion();
    if(!('caches' in window)) return fallback;
    try{
      const keys=await caches.keys();
      let best=0;
      for(const key of keys){
        const match=String(key).match(/^kgg-handyplan-v(\d+)(?:-|$)/i);
        const n=match?Number(match[1]):0;
        if(n>best) best=n;
      }
      return best?'v'+best:fallback;
    }catch(e){
      return fallback;
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

  async function init(){
    refreshManifestLink();
    await refreshServiceWorker();
    mount(await resolveVersion());
  }

  if(document.readyState==='loading') document.addEventListener('DOMContentLoaded',init,{once:true});
  else init();
})();