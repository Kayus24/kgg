# KGG Source Chunk 042

- Source: `kgg-update/index.html`
- Lines: 17641-18060

```html
  function syncStoreToStatePlan(reason){
    const ds=ensureKGGDataStore();
    const plan=ds.getCurrentPlan()||{};
    state.patient={...(state.patient||{}),...(plan.patient||{})};
    state.plan=Array.isArray(plan.exercises)?plan.exercises.map(ensureUiExerciseShape):[];
    return state.plan;
  }
  function getCurrentPlanForOutput(reason){
    syncStatePlanToStore(reason||'get_current_plan_for_output');
    return ensureKGGDataStore().getCurrentPlan();
  }
  function load(){try{const raw=localStorage.getItem(storageKey); if(raw) state={...state,...JSON.parse(raw)};}catch(e){console.warn(e)} loadCustomBank(); if(!$('planDate').value) $('planDate').value=new Date().toISOString().slice(0,10);}
  function save(){try{localStorage.setItem(storageKey,JSON.stringify(state));}catch(e){console.warn(e)}}
  function cleanSecret(value){return String(value||'').trim();}
  function loadAdminSecrets(){
    try{
      const raw=localStorage.getItem(adminSecretsKey);
      const parsed=raw?JSON.parse(raw):{};
      adminSecrets={geminiKeys:Array.isArray(parsed.geminiKeys)?parsed.geminiKeys.map(cleanSecret).filter(Boolean):[],mediaDropzoneEndpoint:cleanSecret(parsed.mediaDropzoneEndpoint),mediaDropzoneUploadToken:cleanSecret(parsed.mediaDropzoneUploadToken),updatedAt:parsed.updatedAt||''};
    }catch(err){console.warn('Admin-Secrets konnten nicht gelesen werden:',err); adminSecrets={geminiKeys:[],mediaDropzoneEndpoint:'',mediaDropzoneUploadToken:'',updatedAt:''};}
    return adminSecrets;
  }
  function persistAdminSecrets(){
    const data={version:2,updatedAt:new Date().toISOString(),geminiKeys:(adminSecrets.geminiKeys||[]).map(cleanSecret).filter(Boolean),mediaDropzoneEndpoint:cleanSecret(adminSecrets.mediaDropzoneEndpoint),mediaDropzoneUploadToken:cleanSecret(adminSecrets.mediaDropzoneUploadToken)};
    localStorage.setItem(adminSecretsKey,JSON.stringify(data));
    try{
      if(data.mediaDropzoneEndpoint)localStorage.setItem('kggMediaDropzoneEndpoint',data.mediaDropzoneEndpoint); else localStorage.removeItem('kggMediaDropzoneEndpoint');
      if(data.mediaDropzoneUploadToken)localStorage.setItem('kggMediaDropzoneUploadToken',data.mediaDropzoneUploadToken); else localStorage.removeItem('kggMediaDropzoneUploadToken');
    }catch(e){}
    adminSecrets={geminiKeys:data.geminiKeys,mediaDropzoneEndpoint:data.mediaDropzoneEndpoint,mediaDropzoneUploadToken:data.mediaDropzoneUploadToken,updatedAt:data.updatedAt};
    try{initMediaDropzoneUploadAdapter();}catch(e){console.warn('Medien-Adapter konnte nach Admin-Safe-Import nicht neu starten:',e);}
    renderAdminSecretStatus();
  }
  function clearLocalAdminSecrets(){adminSecrets={geminiKeys:[],mediaDropzoneEndpoint:'',mediaDropzoneUploadToken:'',updatedAt:''}; localStorage.removeItem(adminSecretsKey); try{localStorage.removeItem('kggMediaDropzoneEndpoint');localStorage.removeItem('kggMediaDropzoneUploadToken');}catch(e){} renderAdminSecretStatus();}
  function maskSecret(value){const text=cleanSecret(value); return text?('•••• '+text.slice(-4)):'';}
  function renderAdminSecretStatus(){
    const status=$('adminSecretStatus');
    if(status){const parts=[]; if(adminSecrets.geminiKeys.length)parts.push('Gemini: '+adminSecrets.geminiKeys.map(maskSecret).join(', ')); if(adminSecrets.mediaDropzoneEndpoint)parts.push('Medien: verbunden'+(adminSecrets.mediaDropzoneUploadToken?' '+maskSecret(adminSecrets.mediaDropzoneUploadToken):'')); status.textContent=parts.length?('Lokal gespeichert: '+parts.join(' · ')):'Keine lokalen Codes gespeichert.';}
  }
  function openAdminSecretsModal(){
    loadAdminSecrets();
    const k=adminSecrets.geminiKeys||[];
    if($('adminGeminiKey1'))$('adminGeminiKey1').value=k[0]||'';
    if($('adminGeminiKey2'))$('adminGeminiKey2').value=k[1]||'';
    if($('adminMediaDropzoneEndpoint'))$('adminMediaDropzoneEndpoint').value=adminSecrets.mediaDropzoneEndpoint||'';
    if($('adminMediaDropzoneUploadToken'))$('adminMediaDropzoneUploadToken').value=adminSecrets.mediaDropzoneUploadToken||'';
    renderAdminSecretStatus();
    $('adminSecretsModal').classList.add('open');
  }
  function closeAdminSecretsModal(){$('adminSecretsModal').classList.remove('open');}
  function saveAdminSecretsFromModal(){
    adminSecrets.geminiKeys=[cleanSecret($('adminGeminiKey1').value),cleanSecret($('adminGeminiKey2').value)].filter(Boolean);
    adminSecrets.mediaDropzoneEndpoint=cleanSecret($('adminMediaDropzoneEndpoint')&&$('adminMediaDropzoneEndpoint').value);
    adminSecrets.mediaDropzoneUploadToken=cleanSecret($('adminMediaDropzoneUploadToken')&&$('adminMediaDropzoneUploadToken').value);
    persistAdminSecrets();
    closeAdminSecretsModal();
  }
  function encodeAdminCodePackage(data){
    const json=JSON.stringify({kind:'kgg-admin-codes-v1',version:1,...data});
    return 'KGG_ADMIN_CODES_V1:'+btoa(unescape(encodeURIComponent(json))).replace(/\+/g,'-').replace(/\//g,'_').replace(/=+$/,'');
  }
  function decodeAdminCodePackage(text){
    let raw=cleanSecret(text).replace(/^\uFEFF/,'');
    const embedded=raw.match(/KGG_ADMIN_CODES_V1\s*:\s*[A-Za-z0-9_-]+/);
    if(embedded)raw=embedded[0];
    raw=raw.replace(/^KGG_ADMIN_CODES_V1\s*:\s*/,'').trim();
    const dataUrl=raw.match(/^data:[^,]+,([A-Za-z0-9+/=_-]+)$/i);
    if(dataUrl)raw=dataUrl[1];
    let data=null;
    if(raw.startsWith('{')){
      data=JSON.parse(raw);
    }else{
      const compact=raw.split(/\s+/).filter(Boolean).join('');
      const base64=compact.replace(/-/g,'+').replace(/_/g,'/');
      const padded=base64+'='.repeat((4-base64.length%4)%4);
      data=JSON.parse(decodeURIComponent(escape(atob(padded))));
    }
    if(!data||data.kind!=='kgg-admin-codes-v1')throw new Error('Kein KGG Admin-Code-Paket.');
    return data;
  }
  function applyAdminCodePackageData(data){
    adminSecrets.geminiKeys=(Array.isArray(data.geminiKeys)?data.geminiKeys:[]).map(cleanSecret).filter(Boolean).slice(0,4);
    adminSecrets.mediaDropzoneEndpoint=cleanSecret(data.mediaDropzoneEndpoint);
    adminSecrets.mediaDropzoneUploadToken=cleanSecret(data.mediaDropzoneUploadToken);
    persistAdminSecrets();
    return adminSecrets;
  }
  async function importAdminCodePackageFromClipboard(){
    let text='';
    try{text=await navigator.clipboard.readText();}catch(err){}
    if(!text)text=prompt('KGG Admin-Code-Paket einfuegen')||'';
    if(!text)return;
    applyAdminCodePackageData(decodeAdminCodePackage(text));
    openAdminSecretsModal();
  }
  async function exportAdminCodePackageToClipboard(){
    loadAdminSecrets();
    const pack=encodeAdminCodePackage({
      geminiKeys:(adminSecrets.geminiKeys||[]).map(cleanSecret).filter(Boolean),
      mediaDropzoneEndpoint:cleanSecret(adminSecrets.mediaDropzoneEndpoint),
      mediaDropzoneUploadToken:cleanSecret(adminSecrets.mediaDropzoneUploadToken),
      exportedAt:new Date().toISOString()
    });
    try{await navigator.clipboard.writeText(pack);}catch(err){prompt('KGG Admin-Code-Paket kopieren',pack);}
    renderAdminSecretStatus();
  }
  async function importAdminSafeFile(file){
    if(!file)return;
    const text=await file.text();
    applyAdminCodePackageData(decodeAdminCodePackage(text));
    openAdminSecretsModal();
  }
  function downloadAdminSafeFile(){
    loadAdminSecrets();
    const pack=encodeAdminCodePackage({
      geminiKeys:(adminSecrets.geminiKeys||[]).map(cleanSecret).filter(Boolean),
      mediaDropzoneEndpoint:cleanSecret(adminSecrets.mediaDropzoneEndpoint),
      mediaDropzoneUploadToken:cleanSecret(adminSecrets.mediaDropzoneUploadToken),
      exportedAt:new Date().toISOString()
    });
    const body=[
      'KGG ADMIN SAFE FILE v1',
      'DO NOT UPLOAD TO GITHUB',
      'DO NOT SEND TO PATIENTS',
      '',
      pack,
      ''
    ].join('\n');
    const blob=new Blob([body],{type:'text/plain;charset=utf-8'});
    const url=URL.createObjectURL(blob);
    const a=document.createElement('a');
    a.href=url;
    a.download='KGG_PRIVATE_ADMIN_SAFE_v1_DO_NOT_UPLOAD.kggsafe';
    a.click();
    setTimeout(()=>URL.revokeObjectURL(url),1000);
  }
  function exposeAdminSecretApi(){
    window.KGGAdmin=window.KGGAdmin||{};
    window.KGGAdmin.openConfig=openAdminSecretsModal;
    window.KGGAdmin.importCodePackage=text=>{applyAdminCodePackageData(decodeAdminCodePackage(text)); return window.KGGAdmin.getSecretStatus();};
    window.KGGAdmin.exportCodePackage=()=>{loadAdminSecrets(); return encodeAdminCodePackage({geminiKeys:(adminSecrets.geminiKeys||[]).map(cleanSecret).filter(Boolean),mediaDropzoneEndpoint:cleanSecret(adminSecrets.mediaDropzoneEndpoint),mediaDropzoneUploadToken:cleanSecret(adminSecrets.mediaDropzoneUploadToken),exportedAt:new Date().toISOString()});};
    window.KGGAdmin.getSecretStatus=()=>({geminiKeys:(adminSecrets.geminiKeys||[]).map(maskSecret),mediaDropzoneEndpoint:adminSecrets.mediaDropzoneEndpoint||'',mediaDropzoneUploadToken:maskSecret(adminSecrets.mediaDropzoneUploadToken),updatedAt:adminSecrets.updatedAt||''});
    window.KGGAdmin.setGeminiKeys=keys=>{adminSecrets.geminiKeys=(Array.isArray(keys)?keys:[keys]).map(cleanSecret).filter(Boolean); persistAdminSecrets(); return window.KGGAdmin.getSecretStatus();};
    window.KGGAdmin.setMediaDropzone=(endpoint,token)=>{adminSecrets.mediaDropzoneEndpoint=cleanSecret(endpoint); adminSecrets.mediaDropzoneUploadToken=cleanSecret(token); persistAdminSecrets(); return window.KGGAdmin.getSecretStatus();};
    window.KGGAdmin.getGeminiKeyForLocalUse=()=>((adminSecrets.geminiKeys||[]).find(Boolean)||'');
    window.KGGAdmin.getGeminiKeysForLocalUse=()=>((adminSecrets.geminiKeys||[]).map(cleanSecret).filter(Boolean));
  }
  function canUsePwaRuntime(){return location.protocol==='https:'||location.hostname==='localhost'||location.hostname==='127.0.0.1';}
  function isLocalHtmlTestRuntime(){return location.protocol==='file:'||location.hostname==='localhost'||location.hostname==='127.0.0.1';}
  function isStandalonePwa(){return window.matchMedia&&window.matchMedia('(display-mode: standalone)').matches||window.navigator.standalone===true;}
  async function initStoragePersistence(){
    if(!navigator.storage||!navigator.storage.persist)return;
    try{await navigator.storage.persist();}catch(err){console.warn('Persistenter Speicher nicht bestätigt:',err);}
  }

  function kggVersionNumber(value){
    const match=String(value||'').match(/v(\d+)/i);
    return match?parseInt(match[1],10):0;
  }
  function currentRolloutProfile(){
    return (window.KGG_ROLLOUT_PROFILE||'colleague').toLowerCase()==='admin'?'admin':'colleague';
  }
  function githubUpdateTargetFromManifest(manifest){
    const profile=currentRolloutProfile();
    const latestVersion=profile==='admin'?(manifest.latestAdminVersion||manifest.latestVersion):(manifest.latestColleagueVersion||manifest.latestVersion);
    const latestUrl=profile==='admin'?(manifest.adminUrl||manifest.latestUrl):(manifest.colleagueUrl||manifest.latestUrl);
    if(!latestVersion||!latestUrl)return null;
    if(kggVersionNumber(latestVersion)<=kggVersionNumber(VERSION))return null;
    return {version:latestVersion,url:latestUrl,notes:manifest.releaseNotes||''};
  }
  function isNativeAndroidShell(){
    return !!(window.KGGAndroidApp||window.KGGAndroidSync||window.KGGNativeSync);
  }
  function nativeAppUpdateStatus(){
    try{
      if(window.KGGNativeAppUpdate&&typeof window.KGGNativeAppUpdate.status==='function')return window.KGGNativeAppUpdate.status()||{};
      if(window.KGGAndroidApp&&typeof window.KGGAndroidApp.updateStatus==='function')return JSON.parse(window.KGGAndroidApp.updateStatus()||'{}');
    }catch(err){}
    return {};
  }
  function requestNativeAppUpdateCheck(){
    try{
      if(window.KGGNativeAppUpdate&&typeof window.KGGNativeAppUpdate.checkNow==='function')return !!window.KGGNativeAppUpdate.checkNow();
      if(window.KGGAndroidApp&&typeof window.KGGAndroidApp.checkForAppUpdate==='function')return !!window.KGGAndroidApp.checkForAppUpdate();
    }catch(err){}
    return false;
  }
  function androidApkUpdateTargetFromManifest(manifest){
    if(!isNativeAndroidShell())return null;
    const profile=currentRolloutProfile();
    const latestVersion=manifest.latestAndroidShellVersion||manifest.latestWebVersion||'';
    const latestUrl=profile==='admin'
      ?(manifest.latestAdminAndroidApkUrl||manifest.adminAndroidApkUrl||manifest.latestAndroidApkUrl)
      :(manifest.latestColleagueAndroidApkUrl||manifest.colleagueAndroidApkUrl||manifest.latestAndroidApkUrl);
    const latestSha=profile==='admin'
      ?(manifest.latestAdminAndroidApkSha256||manifest.adminAndroidApkSha256||manifest.latestAndroidApkSha256)
      :(manifest.latestColleagueAndroidApkSha256||manifest.colleagueAndroidApkSha256||manifest.latestAndroidApkSha256);
    if(!latestVersion||!latestUrl)return null;
    const nativeStatus=nativeAppUpdateStatus();
    const currentShell=Number(nativeStatus.currentShellVersion||0);
    if(currentShell&&kggVersionNumber(latestVersion)<=currentShell)return null;
    return {version:latestVersion,url:latestUrl,sha256:latestSha||'',notes:manifest.releaseNotes||manifest.notes||''};
  }
  function isKggLocalContentNoRedirectRuntime(){
    const protocol=String(location.protocol||'').toLowerCase();
    const href=String(location.href||'').toLowerCase();
    return protocol==='content:'||
      protocol==='capacitor:'||
      protocol==='android-app:'||
      href.indexOf('/media/external/file/')!==-1||
      href.indexOf('content://')===0||
      href.indexOf('file://')===0;
  }
  const kggNoAutoReleaseNavigationMarker='kgg-no-auto-release-navigation-v32';
  function stageManualRemoteWebUpdate(target){
    if(!target||!target.url)return false;
    window.KGGRemoteUpdateUrl=target.url;
    window.KGGPendingRemoteUpdateVersion=target.version;
    window.KGGPendingRemoteUpdateNotes=target.notes;
    showInstallPrompt('remoteUpdate');
    return true;
  }
  function autoApplyRemoteWebUpdate(target){
    // v32: Beim Booten niemals automatisch auf GitHub-Pages/Release-HTML navigieren.
    // ChatGPT-/Android-/Datei-Viewer fangen solche Redirects als externen Link ab.
    // Updates duerfen nur noch nach bewusstem Tippen auf den sichtbaren Button oeffnen.
    void target;
    return false;
  }
  async function checkGithubAppUpdate(){
    if(!window.fetch||isLocalHtmlTestRuntime())return;
    try{
      const res=await fetch(kggUpdateManifestUrl,{cache:'no-store'});
      if(!res.ok)return;
      const manifest=await res.json();
      if(!manifest||manifest.kind!=='kgg_app_update_manifest')return;
      const webTarget=githubUpdateTargetFromManifest(manifest);
      const apkTarget=androidApkUpdateTargetFromManifest(manifest);
      if(isNativeAndroidShell()){
        if(apkTarget){
          window.KGGAndroidApkUpdateUrl=apkTarget.url;
          window.KGGAndroidApkUpdateVersion=apkTarget.version;
          window.KGGAndroidApkUpdateSha256=apkTarget.sha256;
        }
        return;
      }
      if(!webTarget)return;
      stageManualRemoteWebUpdate(webTarget);
    }catch(err){
      console.warn('GitHub-Update-Pruefung nicht verfuegbar:',err);
    }
  }
  function closeInstallPrompt(){const modal=$('installPromptModal'); if(modal)modal.classList.remove('open');}
  function showInstallPrompt(mode){
    if(mode!=='update'&&mode!=='remoteUpdate'&&mode!=='androidApkUpdate'&&isStandalonePwa())return;
    if(localStorage.getItem(pwaInstallPromptSeenKey)&&mode!=='update'&&mode!=='remoteUpdate'&&mode!=='androidApkUpdate')return;
    const title=$('installPromptTitle'), text=$('installPromptText'), accept=$('acceptInstallPrompt');
    if(mode==='androidApkUpdate'){
      if(title)title.textContent='Android-App-Update verfuegbar';
      if(text)text.textContent='Neue Android-Version '+(window.KGGAndroidApkUpdateVersion||'')+' ist bereit. Android fragt vor der Installation noch einmal nach.';
      if(accept)accept.textContent='APK installieren';
    }else if(mode==='remoteUpdate'){
      if(title)title.textContent='GitHub-Update verfuegbar';
      if(text)text.textContent='Neue Version '+(window.KGGPendingRemoteUpdateVersion||'')+' ist online. Lokale Daten bleiben auf diesem Geraet erhalten.';
      if(accept)accept.textContent='Update oeffnen';
    }else if(mode==='update'){
      if(title)title.textContent='Update bereit';
      if(text)text.textContent='Update bereit. Lokale Daten bleiben erhalten.';
      if(accept)accept.textContent='Aktualisieren';
    }else{
      if(title)title.textContent='App installieren?';
      if(text)text.textContent='Installieren und lokale Daten über Updates behalten.';
      if(accept)accept.textContent='Installieren';
    }
    const modal=$('installPromptModal'); if(modal)modal.classList.add('open');
  }
  async function acceptInstallPrompt(){
    if(window.KGGAndroidApkUpdateUrl){
      const target=window.KGGAndroidApkUpdateUrl;
      window.KGGAndroidApkUpdateUrl='';
      closeInstallPrompt();
      try{const opened=window.open(target,'_blank','noopener'); if(!opened)location.href=target;}catch(err){location.href=target;}
      return;
    }
    if(window.KGGRemoteUpdateUrl){
      const target=window.KGGRemoteUpdateUrl;
      window.KGGRemoteUpdateUrl='';
      closeInstallPrompt();
      try{const opened=window.open(target,'_blank','noopener'); if(!opened)location.href=target;}catch(err){location.href=target;}
      return;
    }
    localStorage.setItem(pwaInstallPromptSeenKey,new Date().toISOString());
    const waiting=window.KGGWaitingServiceWorker;
    if(waiting){waiting.postMessage({type:'SKIP_WAITING'}); closeInstallPrompt(); return;}
    if(deferredInstallPrompt){
      const prompt=deferredInstallPrompt;
      deferredInstallPrompt=null;
      try{prompt.prompt(); await prompt.userChoice;}catch(err){console.warn('Install-Prompt blockiert:',err);}
    }
    closeInstallPrompt();
  }
  function initPwaAndUpdates(){
    initStoragePersistence();
    setTimeout(checkGithubAppUpdate,900);
    setInterval(checkGithubAppUpdate,kggAutoUpdateCheckMs);
    document.addEventListener('visibilitychange',()=>{if(document.visibilityState==='visible')checkGithubAppUpdate();});
    window.addEventListener('beforeinstallprompt',ev=>{
      ev.preventDefault();
      deferredInstallPrompt=ev;
      showInstallPrompt('install');
    });
    window.addEventListener('appinstalled',()=>localStorage.setItem(pwaInstallPromptSeenKey,new Date().toISOString()));
    if(!canUsePwaRuntime()||isLocalHtmlTestRuntime()||!('serviceWorker' in navigator))return;
    navigator.serviceWorker.register(pwaServiceWorkerUrl).then(reg=>{
      reg.update().catch(()=>{});
      reg.addEventListener('updatefound',()=>{
        const worker=reg.installing;
        if(!worker)return;
        worker.addEventListener('statechange',()=>{
          if(worker.state==='installed'&&navigator.serviceWorker.controller){
            window.KGGWaitingServiceWorker=worker;
            worker.postMessage({type:'SKIP_WAITING'});
          }
        });
      });
    }).catch(err=>console.warn('Service Worker konnte nicht registriert werden:',err));
    navigator.serviceWorker.addEventListener('controllerchange',()=>{if(!window.KGGPwaReloading){window.KGGPwaReloading=true; location.reload();}});
  }
  function initAdminModeAccess(){
    loadAdminSecrets();
    exposeAdminSecretApi();
    document.body.classList.add('adminMode');
    if(!(adminSecrets.geminiKeys&&adminSecrets.geminiKeys.length)){
      setTimeout(()=>{try{openAdminSecretsModal();}catch(e){}},700);
    }
  }
  function applyLargePdfMode(){
    const enabled=!!state.largePdfMode;
    const btn=$('visionBtn');
    if(btn){btn.textContent=enabled?'PDF A-':'PDF A+'; btn.setAttribute('aria-pressed',enabled?'true':'false'); btn.title=enabled?'Standard-PDF':'Großdruck-PDF';}
  }
  function setLargePdfMode(enabled){state.largePdfMode=!!enabled; applyLargePdfMode(); save();}
  function initLargePdfMode(){if(/[?&](grosspdf|largepdf)=1\b/i.test(location.search))state.largePdfMode=true; applyLargePdfMode();}
  function loadDeletedBankIds(){try{const raw=localStorage.getItem(deletedBankKey); const ids=raw?JSON.parse(raw):[]; deletedBankIds=new Set(Array.isArray(ids)?ids.map(String):[]);}catch(e){console.warn(e); deletedBankIds=new Set();}}
  function persistDeletedBankIds(){try{localStorage.setItem(deletedBankKey,JSON.stringify([...deletedBankIds]));}catch(e){console.warn(e)}}
  function loadCustomBank(){loadDeletedBankIds(); try{const raw=localStorage.getItem(customBankKey); const items=raw?JSON.parse(raw):[]; if(Array.isArray(items))items.forEach(ex=>{if(ex&&ex.name){const existing=bank.find(b=>compact(b.name)===compact(ex.name)); if(existing)Object.assign(existing,{...ex,id:existing.id||ex.id,custom:true}); else bank.push({...ex,custom:true});}});}catch(e){console.warn(e)} for(let i=bank.length-1;i>=0;i--){if(deletedBankIds.has(String(bank[i]&&bank[i].id)))bank.splice(i,1);}}
  function persistCustomBank(){try{localStorage.setItem(customBankKey,JSON.stringify(bank.filter(ex=>ex.custom||ex.createdFromPlan)));}catch(e){console.warn(e)} queueNativeExerciseBankSync('exercise_bank_changed');}
  function openBankDeleteModal(id){
    const ex=bank.find(item=>String(item.id)===String(id));
    if(!ex)return;
    pendingBankDeleteId=String(id);
    const name=$('bankDeleteName');
    if(name)name.textContent=ex.name||'';
    $('bankDeleteModal').classList.add('open');
  }
  function closeBankDeleteModal(){pendingBankDeleteId=null; $('bankDeleteModal').classList.remove('open');}
  function deleteBankExercise(id){
    const sid=String(id||'');
    const idx=bank.findIndex(ex=>String(ex&&ex.id)===sid);
    if(idx<0)return;
    deletedBankIds.add(sid);
    bank.splice(idx,1);
    persistDeletedBankIds();
    persistCustomBank();
    render();
  }
  function confirmBankDelete(){if(pendingBankDeleteId)deleteBankExercise(pendingBankDeleteId); closeBankDeleteModal();}
  function exerciseBankFieldsFromPlan(ex,name){
    return {
      name:name||ex.name||stripExerciseName(ex.rawText)||'',
      aliases:ex.aliases||name||ex.name||'',
      sets:normalizeSetCount(ex.sets),
      unit:ex.unit||ex.metricUnit||'Wdh',
      weightUnit:ex.weightUnit||ex.loadUnit||'kg',
      loadUnit:ex.weightUnit||ex.loadUnit||'kg',
      metricUnit:ex.unit||ex.metricUnit||'Wdh',
      measure:normalizeMeasureMode(ex.measure||(String(ex.unit||'').toLowerCase().includes('zeit')?'zeit':'wdh')),
      side:normalizeSideMode(ex.side||'BI'),
      startMetric:ex.startMetric||'',
      startLoad:ex.startLoad||'',
      videoUrl:ex.videoUrl||'',
      videoLabel:ex.videoLabel||'Video öffnen',
      media:ensureExerciseMediaList(ex)
    };
  }
  function upsertPlanExerciseToBank(ex,reason){
    const name=ex&&ex.name||stripExerciseName(ex&&ex.rawText)||'';
    if(!name)return null;
    let existing=bank.find(b=>compact(b.name)===compact(name));
    const fields=exerciseBankFieldsFromPlan(ex,name);
    if(existing){
      Object.assign(existing,fields,{custom:true,updatedFromPlan:true,updatedAt:new Date().toISOString(),dbSyncReason:reason||'plan_save'});
    }else{
      existing={id:'custom_'+Date.now()+'_'+Math.random().toString(36).slice(2,6),...fields,custom:true,createdFromPlan:true,createdAt:new Date().toISOString(),dbSyncReason:reason||'plan_save'};
      bank.push(existing);
    }
    return existing;
  }
  function savePendingToBank(reason){
    state.plan=(state.plan||[]).map(ex=>{
      const copy={...ex};
      if(copy.pendingNew||copy.changedByLiveText||copy.needsReview){
        const saved=upsertPlanExerciseToBank(copy,reason||'before_output');
        if(saved){
          copy.pendingNew=false;
          copy.dbSynced=true;
          copy.dbSyncedAt=new Date().toISOString();
          copy.dbSyncReason=reason||'before_output';
          copy.sourceId=saved.id;
          copy.bankId=saved.id;
        }
      }
      return copy;
    });
    persistCustomBank();
    syncStatePlanToStore(reason||'save_pending_to_bank');
    save();
  }
  function score(q,ex){const cq=compact(q), cn=compact(ex.name), al=String(ex.aliases||'').split(/[,;]/).map(compact); if(!cq)return 0; if(cq===cn)return 120; if(al.indexOf(cq)>-1)return 115; if(cn.includes(cq)||cq.includes(cn))return 94; if(al.some(a=>a.length>2&&(a.includes(cq)||cq.includes(a))))return 90; return norm(q).split(' ').reduce((r,t)=>r+(t.length>2&&norm(ex.name+' '+ex.aliases).includes(t)?10:0),0)}
  function scoredSearch(q,limit){return bank.map(ex=>({ex,score:score(q,ex)})).filter(x=>x.score>0).sort((a,b)=>b.score-a.score).slice(0,limit||8)}
```
