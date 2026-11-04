# KGG Patient Source Chunk 017

- Source file: `patient-install-transfer.js`
- Characters: 1-13069
- Full source SHA-256: `e8c6d4a51632b1e39eeedafdc167ad72f151f65ab0f33d9bb96c85a38fb1a6d8`

```
(()=>{
  // Install pop-up + lossless plan/value transfer into the installed web app.
  // Browser tabs may lose localStorage (Safari ITP after 7 days without a visit,
  // Samsung Internet/Chrome best-effort eviction). Installed apps are exempt or
  // far better protected, so patients with a plan are invited to install.
  const VERSION='install-transfer-1';
  if(window.__kggInstallTransfer===VERSION)return;
  window.__kggInstallTransfer=VERSION;

  const SNOOZE_KEY='kggInstallPopupSnoozeUntil';
  const DONE_KEY='kggInstallPopupDone';
  const PERSIST_KEY='kggStoragePersisted';
  const IMPORTED_KEY='kggTransferImported';
  const VERIFIED_KEY='kggInstallVerified';
  const PREFIX='KGGT1:';
  const SNOOZE_MS=3*24*60*60*1000;
  const PROMPT_WAIT_MS=4000;
  const SKIP_KEYS=new Set([SNOOZE_KEY,DONE_KEY,PERSIST_KEY,IMPORTED_KEY,VERIFIED_KEY,'kggInstallAsked']);

  const ua=navigator.userAgent||'';
  const isIOS=/iPad|iPhone|iPod/.test(ua)||(navigator.platform==='MacIntel'&&navigator.maxTouchPoints>1);
  const isAndroid=/Android/i.test(ua);
  const standalone=()=>Boolean((window.matchMedia&&matchMedia('(display-mode: standalone)').matches)||navigator.standalone);
  const T=(de,en)=>{const i18n=window.KGGPatientI18n;if(i18n&&typeof i18n.t==='function')return i18n.t(de,en);try{return localStorage.getItem('kggPatientLang')==='en'?en:de}catch(e){return de}};
  const get=k=>{try{return localStorage.getItem(k)}catch(e){return null}};
  const set=(k,v)=>{try{localStorage.setItem(k,v);return true}catch(e){return false}};

  function hasPlan(){
    try{const cur=JSON.parse(get('kggCurrentPlanV1')||'null');if(cur&&cur.plan)return true}catch(e){}
    try{const multi=JSON.parse(get('kggPatientMultiPlansV1')||'null');if(multi&&Array.isArray(multi.plans)&&multi.plans.length)return true}catch(e){}
    return false;
  }

  // ---- bundle: every kgg* localStorage entry, deflated + base64url ----
  function b64Encode(bytes){let s='';for(let i=0;i<bytes.length;i+=0x8000)s+=String.fromCharCode.apply(null,bytes.subarray(i,i+0x8000));return btoa(s).replace(/\+/g,'-').replace(/\//g,'_').replace(/=+$/,'')}
  function b64Decode(v){const t=String(v||'').replace(/-/g,'+').replace(/_/g,'/'),b=atob(t+'='.repeat((4-t.length%4)%4)),u=new Uint8Array(b.length);for(let i=0;i<b.length;i++)u[i]=b.charCodeAt(i);return u}
  function snapshot(){
    const items={};
    for(let i=0;i<localStorage.length;i++){const k=localStorage.key(i);if(k&&/^kgg/i.test(k)&&!SKIP_KEYS.has(k)){const v=get(k);if(v!==null)items[k]=v}}
    return {v:1,id:Date.now().toString(36)+'-'+Math.random().toString(36).slice(2,8),at:new Date().toISOString(),items};
  }
  function encodeBundle(bundle){
    const json=JSON.stringify(bundle||snapshot());
    if(!window.fflate)throw new Error('fflate missing');
    return PREFIX+b64Encode(window.fflate.deflateSync(window.fflate.strToU8(json),{level:9}));
  }
  function decodeBundle(code){
    const body=String(code||'').replace(/^#?(kggt=)?/i,'');
    if(!body.startsWith(PREFIX))throw new Error('no transfer bundle');
    const bundle=JSON.parse(window.fflate.strFromU8(window.fflate.inflateSync(b64Decode(body.slice(PREFIX.length)))));
    if(!bundle||bundle.v!==1||!bundle.id||!bundle.items||typeof bundle.items!=='object')throw new Error('invalid transfer bundle');
    return bundle;
  }
  // Imports only keys that are missing, once per bundle id: never overwrites
  // data already in the app and never resurrects plans deleted later.
  function importBundle(bundle){
    const done=(get(IMPORTED_KEY)||'').split(',').filter(Boolean);
    if(done.includes(bundle.id))return {imported:0,skipped:true};
    let imported=0;
    Object.keys(bundle.items).forEach(k=>{if(/^kgg/i.test(k)&&!SKIP_KEYS.has(k)&&get(k)===null&&set(k,String(bundle.items[k])))imported++});
    done.push(bundle.id);set(IMPORTED_KEY,done.slice(-10).join(','));
    return {imported,skipped:false};
  }

  function requestPersist(){
    try{
      if(!navigator.storage||typeof navigator.storage.persist!=='function')return Promise.resolve(null);
      return navigator.storage.persist().then(ok=>{set(PERSIST_KEY,ok?'1':'0');return ok}).catch(()=>null);
    }catch(e){return Promise.resolve(null)}
  }

  function iosInstallLink(){
    const dir=location.pathname.replace(/[^\/]*$/,'');
    let planQuery='';
    try{const cur=JSON.parse(get('kggCurrentPlanV1')||'null');if(cur&&cur.plan&&window.KGGPlanFormat&&typeof window.KGGPlanFormat.encodeKggH3==='function')planQuery='&plan='+encodeURIComponent(window.KGGPlanFormat.encodeKggH3(cur.plan))}catch(e){}
    // Bundle goes into the hash: never sent to the server, so no URL length limit there.
    return location.origin+dir+'ios-start.html?install=1'+planQuery+'#kggt='+encodeBundle();
  }

  // ---- UI ----
  function ensureStyle(){
    if(document.getElementById('kggInstallTransferStyle'))return;
    const s=document.createElement('style');s.id='kggInstallTransferStyle';
    s.textContent=`#kggInstallPopupBackdrop{position:fixed;inset:0;z-index:10050;background:rgba(15,23,42,.45);display:flex;align-items:flex-end;justify-content:center;padding:12px;padding-bottom:calc(12px + env(safe-area-inset-bottom))}
#kggInstallPopup{width:100%;max-width:520px;background:#fff;color:#111827;border-radius:20px;padding:18px;box-shadow:0 20px 50px rgba(15,23,42,.3);font-family:inherit}
#kggInstallPopup h2{margin:0 0 8px;font-size:20px;font-weight:950}#kggInstallPopup p{margin:0 0 10px;color:#334155;font-size:15px;line-height:1.4}
#kggInstallPopup ol{margin:0 0 10px;padding-left:22px;font-size:15px;line-height:1.5}#kggInstallPopup .kggInstallActions{display:flex;flex-direction:column;gap:8px;margin-top:12px}
#kggInstallPopup button{min-height:48px;border-radius:14px;border:1px solid #cbd5e1;background:#fff;color:#111827;font-size:16px;font-weight:900;touch-action:manipulation}
#kggInstallPopup button.primary{background:#111827;border-color:#111827;color:#fff}#kggInstallPopup .ok{color:#166534;font-weight:900}#kggInstallPopup .warn{color:#b45309;font-weight:900}
#kggInstallToast{position:fixed;left:12px;right:12px;bottom:calc(84px + env(safe-area-inset-bottom));z-index:10040;max-width:520px;margin:auto;background:#ecfdf5;border:1px solid #86efac;color:#166534;border-radius:16px;padding:12px 14px;font-weight:900;box-shadow:0 12px 30px rgba(15,23,42,.18)}
#kggInstallToast.warn{background:#fffbeb;border-color:#fcd34d;color:#92400e}`;
    document.head.appendChild(s);
  }
  function close(){const b=document.getElementById('kggInstallPopupBackdrop');if(b)b.remove()}
  function snooze(){set(SNOOZE_KEY,String(Date.now()+SNOOZE_MS))}
  function toast(text,warn){
    ensureStyle();const old=document.getElementById('kggInstallToast');if(old)old.remove();
    const d=document.createElement('div');d.id='kggInstallToast';d.setAttribute('role','status');if(warn)d.className='warn';d.textContent=text;document.body.appendChild(d);
    setTimeout(()=>{if(d.parentNode)d.remove()},warn?9000:5000);
  }
  function el(tag,cls,html){const e=document.createElement(tag);if(cls)e.className=cls;if(html!=null)e.innerHTML=html;return e}
  function button(text,primary,onClick){const b=document.createElement('button');b.type='button';b.textContent=text;if(primary)b.className='primary';b.addEventListener('click',onClick);return b}

  function manualSteps(){
    if(isIOS)return T('<li>Unten auf <b>Weiter zur Installation</b> tippen.</li><li>Auf der nächsten Seite das <b>Teilen</b>-Symbol antippen.</li><li><b>Zum Home-Bildschirm</b> wählen und <b>Hinzufügen</b> tippen.</li><li>Danach die App nur noch über das neue Symbol öffnen.</li>',
      '<li>Tap <b>Continue to install</b> below.</li><li>On the next page, tap the <b>Share</b> icon.</li><li>Choose <b>Add to Home Screen</b> and tap <b>Add</b>.</li><li>From then on, open the app only via the new icon.</li>');
    return '';
  }

  function showPopup(){
    if(document.getElementById('kggInstallPopupBackdrop'))return;
    ensureStyle();
    const prompt=window.__kggInstallPrompt&&typeof window.__kggInstallPrompt.prompt==='function'?window.__kggInstallPrompt:null;
    const backdrop=el('div');backdrop.id='kggInstallPopupBackdrop';backdrop.setAttribute('role','presentation');
    const dialog=el('section');dialog.id='kggInstallPopup';dialog.setAttribute('role','dialog');dialog.setAttribute('aria-modal','true');dialog.setAttribute('aria-labelledby','kggInstallPopupTitle');
    const title=el('h2');title.id='kggInstallPopupTitle';title.textContent=T('KGG als App installieren?','Install KGG as an app?');
    const intro=el('p');intro.textContent=T('Im Browser kann dein Handy den Trainingsplan und deine Werte nach einiger Zeit ohne Nutzung löschen. Als App auf dem Startbildschirm bleiben sie sicher gespeichert. Dein Plan und deine Werte werden übernommen.',
      'In the browser, your phone may delete your training plan and values after some time without use. As an app on your home screen they stay safely stored. Your plan and values are carried over.');
    const status=el('p');status.id='kggInstallPopupStatus';
    const actions=el('div','kggInstallActions');
    dialog.append(title,intro);
    if(prompt){
      actions.append(button(T('Jetzt installieren','Install now'),true,async()=>{
        let choice=null;
        try{window.__kggInstallPrompt=null;await prompt.prompt();choice=prompt.userChoice?await prompt.userChoice:null}catch(e){}
        if(choice&&choice.outcome==='accepted'){
          set(DONE_KEY,'1');requestPersist();['installBox','installOfferText','installOfferBtn'].forEach(id=>{const n=document.getElementById(id);if(n)n.classList.add('hide')});
          status.className='ok';status.textContent=T('Installiert. Dein Plan ist in der App. Bitte ab jetzt die App über das neue Symbol öffnen.','Installed. Your plan is in the app. From now on, please open it via the new icon.');
          actions.innerHTML='';actions.append(button(T('Fertig','Done'),true,close));
        }else{snooze();close()}
      }));
    }else if(isIOS){
      const ol=el('ol',null,manualSteps());dialog.append(ol);
      actions.append(button(T('Weiter zur Installation','Continue to install'),true,()=>{
        try{const link=iosInstallLink();set(DONE_KEY,'1');location.href=link}
        catch(e){status.className='warn';status.textContent=T('Die Installation konnte nicht vorbereitet werden. Bitte später erneut versuchen.','Installation could not be prepared. Please try again later.')}
      }));
    }
    actions.append(button(T('Später','Later'),false,()=>{snooze();close()}));
    dialog.append(status,actions);backdrop.appendChild(dialog);document.body.appendChild(backdrop);
  }

  function busy(){
    const pad=document.getElementById('pad');
    return Boolean((pad&&!pad.classList.contains('hide'))||document.getElementById('kggPlanLinkChoiceBackdrop')||document.getElementById('kggInstallPopupBackdrop'));
  }
  // Pop-up only where installing really works with one tap: the browser must
  // have handed us a real install prompt (Chrome, Edge, Samsung Internet on
  // Android). iPhone has no such prompt; its guided flow stays off until it is
  // proven on a real device and can be enabled for tests with ?iosinstall=1.
  function iosTestEnabled(){try{return isIOS&&new URLSearchParams(location.search).get('iosinstall')==='1'}catch(e){return false}}
  function canInstall(){return Boolean(window.__kggInstallPrompt&&typeof window.__kggInstallPrompt.prompt==='function')||iosTestEnabled()}
  function shouldOffer(){
    if(standalone()||!(isIOS||isAndroid)||!hasPlan()||!canInstall())return false;
    if(get(DONE_KEY)==='1')return false;
    if(Number(get(SNOOZE_KEY)||0)>Date.now())return false;
    return true;
  }
  function maybeOffer(attempt){
    if(!shouldOffer())return;
    if(busy()){if(attempt<20)setTimeout(()=>maybeOffer(attempt+1),3000);return}
    showPopup();
  }

  // Installed app start: protect storage and confirm the plan arrived.
  function verifyInstalled(){
    if(!standalone())return;
    requestPersist();
    if(get(VERIFIED_KEY)==='1')return;
    setTimeout(()=>{
      if(hasPlan()){set(VERIFIED_KEY,'1');toast(T('✓ Trainingsplan in der App übernommen.','✓ Training plan transferred into the app.'),false)}
      else toast(T('Noch kein Plan in der App. Bitte den QR-Code deines Trainingsplans hier in der App scannen.','No plan in the app yet. Please scan your training plan QR code here in the app.'),true);
    },1500);
  }

  window.KGGInstallTransfer={snapshot,encodeBundle,decodeBundle,importBundle,requestPersist,hasPlan,showPopup,shouldOffer};

  // Only the patient app page runs the UI; ios-start.html uses the API above.
  if(window.__KGG_INSTALL_TRANSFER_API_ONLY__)return;
  function init(){
    window.addEventListener('appinstalled',()=>{set(DONE_KEY,'1');requestPersist()});
    window.addEventListener('beforeinstallprompt',()=>setTimeout(()=>maybeOffer(0),1500));
    verifyInstalled();
    setTimeout(()=>maybeOffer(0),isIOS?2500:PROMPT_WAIT_MS);
  }
  document.readyState==='loading'?document.addEventListener('DOMContentLoaded',init,{once:true}):init();
})();
```
