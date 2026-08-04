# KGG Patient Source Chunk 003

- Source file: `update-recovery.html`
- Characters: 1-5778
- Full source SHA-256: `8522669c2cdb796b87733f5d183a7994c0515c55779e5f6aef2e732e4adaea48`

```
<!doctype html>
<html lang="de">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width,initial-scale=1">
  <meta name="robots" content="noindex">
  <meta http-equiv="Cache-Control" content="no-store, no-cache, must-revalidate">
  <title>KGG Update reparieren</title>
  <style>
    *{box-sizing:border-box}body{margin:0;background:#f4f7fb;color:#111827;font-family:system-ui,-apple-system,Segoe UI,Roboto,Arial,sans-serif}main{max-width:560px;margin:auto;padding:18px}.card{margin-top:10vh;background:#fff;border:1px solid #dbe3ef;border-radius:20px;padding:18px;box-shadow:0 14px 40px #0f172a14}h1{font-size:24px;margin:0 0 8px}.muted{color:#64748b;line-height:1.45}.status{margin-top:14px;padding:12px;border:1px solid #dbe3ef;border-radius:14px;background:#f8fafc;font-weight:750}.status.ok{background:#ecfdf5;border-color:#bbf7d0;color:#166534}.status.err{background:#fff1f2;border-color:#fecaca;color:#b91c1c}.actions{display:grid;gap:10px;margin-top:14px}button,a{min-height:48px;border-radius:14px;font-size:16px;font-weight:900;display:flex;align-items:center;justify-content:center;text-decoration:none}button{border:1px solid #111827;background:#111827;color:#fff}button:disabled{opacity:.58}a{border:1px solid #cbd5e1;background:#fff;color:#111827}.note{margin-top:12px;font-size:13px;color:#64748b}
  </style>
</head>
<body>
  <main>
    <section class="card">
      <h1>KGG Update reparieren</h1>
      <p class="muted">Trainingsdaten, Pläne, Historien und Bilder bleiben erhalten. Erneuert werden nur der KGG-Service-Worker und dessen App-Cache.</p>
      <div id="status" class="status" role="status" aria-live="polite">Bereit.</div>
      <div class="actions">
        <button id="run" type="button">Update jetzt reparieren</button>
        <a href="./">Abbrechen</a>
      </div>
      <div class="note">Diese Seite löscht weder Websitedaten noch lokale Trainingsdaten.</div>
    </section>
  </main>
  <script>
  (()=>{
    const RELEASE='73';
    const CACHE_PREFIX='kgg-handyplan-';
    const statusEl=document.getElementById('status');
    const runButton=document.getElementById('run');
    const sleep=ms=>new Promise(resolve=>setTimeout(resolve,ms));
    const setStatus=(text,kind='')=>{statusEl.textContent=text;statusEl.className='status'+(kind?' '+kind:'')};
    const appScope=()=>new URL('./',location.href).href;
    const isOwnRegistration=registration=>Boolean(registration&&registration.scope&&registration.scope.startsWith(appScope()));

    async function unregisterAppWorkers(){
      const registrations=await navigator.serviceWorker.getRegistrations();
      const own=registrations.filter(isOwnRegistration);
      for(const registration of own){
        [registration.installing,registration.waiting,registration.active].filter(Boolean).forEach(worker=>{try{worker.postMessage({type:'SKIP_WAITING'})}catch(e){}});
        await registration.unregister();
      }
      return own.length;
    }

    async function clearAppCaches(){
      if(!('caches' in window))return 0;
      const keys=await caches.keys();
      const own=keys.filter(key=>key.startsWith(CACHE_PREFIX));
      await Promise.all(own.map(key=>caches.delete(key)));
      return own.length;
    }

    async function waitForActiveWorker(registration){
      for(let attempt=0;attempt<60;attempt++){
        if(registration.waiting){try{registration.waiting.postMessage({type:'SKIP_WAITING'})}catch(e){}}
        if(registration.active&&registration.active.state==='activated')return registration.active;
        await sleep(250);
      }
      throw new Error('Der neue Service Worker wurde nicht rechtzeitig aktiviert.');
    }

    function readWorkerInfo(worker){
      return new Promise((resolve,reject)=>{
        if(!worker||typeof MessageChannel==='undefined'){reject(new Error('Worker-Diagnose nicht verfügbar.'));return}
        const channel=new MessageChannel();
        const timer=setTimeout(()=>reject(new Error('Der neue Worker antwortet nicht.')),2500);
        channel.port1.onmessage=event=>{clearTimeout(timer);resolve(event.data||{})};
        try{worker.postMessage({type:'GET_UPDATE_DIAGNOSTICS'},[channel.port2])}catch(error){clearTimeout(timer);reject(error)}
      });
    }

    async function registerFreshWorker(){
      const script='./service-worker.js?recovery='+RELEASE+'&t='+Date.now();
      const registration=await navigator.serviceWorker.register(script,{scope:'./',updateViaCache:'none'});
      try{await registration.update()}catch(e){}
      const worker=await waitForActiveWorker(registration);
      const info=await readWorkerInfo(worker);
      if(String(info.version||'')!==RELEASE)throw new Error('Geladen wurde v'+String(info.version||'?')+' statt v'+RELEASE+'.');
      await navigator.serviceWorker.ready;
      return info;
    }

    async function recover(){
      if(!('serviceWorker' in navigator)){setStatus('Dieser Browser unterstützt keine Service Worker.','err');return}
      runButton.disabled=true;
      try{
        setStatus('Alten KGG-Service-Worker lösen …');
        await unregisterAppWorkers();
        setStatus('Nur den KGG-App-Cache erneuern …');
        await clearAppCaches();
        setStatus('Aktuelle KGG-Version laden …');
        await registerFreshWorker();
        setStatus('Update repariert. Die App wird neu geöffnet.','ok');
        await sleep(650);
        location.replace('./?recovered='+RELEASE+'&t='+Date.now());
      }catch(error){
        setStatus('Reparatur fehlgeschlagen: '+String(error&&error.message||error),'err');
        runButton.disabled=false;
      }
    }

    runButton.addEventListener('click',recover);
    if(new URLSearchParams(location.search).get('auto')==='1')setTimeout(recover,120);
  })();
  </script>
</body>
</html>
```
