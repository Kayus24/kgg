# KGG Source Chunk 042

- Source: `kgg-update/index.html`
- Lines: 17641-18060

```html
    if(['zeit','time','dauer','sek','sek.','sec','s'].includes(raw))return 'zeit';
    return 'wdh';
  }
  function measureUnitLabel(measure){return normalizeMeasureMode(measure)==='zeit'?'Sek.':'Wdh';}
  function cleanFreeUnitLabel(value){
    return String(value||'').trim().replace(/\s*\/\s*/g,'/').replace(/\s+/g,' ').replace(/^[.@:;,\-\s]+|[.@:;,\-\s]+$/g,'');
  }
  function normalizeLoadUnitInfo(value,fallback){
    const fallbackUnit=fallback||'kg';
    const raw=cleanFreeUnitLabel(value);
    if(!raw)return {unit:fallbackUnit,custom:false,explicit:false};
    const lower=raw.toLowerCase().replace(/\./g,'').replace(/\s+/g,' ');
    const compact=lower.replace(/\s+/g,'');
    if(['kg','kgs','kilo','kilos','kilogramm','kilogram'].includes(lower))return {unit:'kg',custom:false,explicit:true};
    if(['bw','bodyweight','body weight','koerpergewicht','körpergewicht','eigengewicht'].includes(lower)||compact==='bodyweight')return {unit:'BW',custom:false,explicit:true};
    if(['hub','huebe','hübe'].includes(lower))return {unit:'Hub',custom:false,explicit:true};
    if(['stufe'].includes(lower))return {unit:'Stufe',custom:false,explicit:true};
    if(['watt','w'].includes(lower))return {unit:'Watt',custom:false,explicit:true};
    if(['stufe/watt','stufe watt','stufe+watt','stufewatt'].includes(lower)||compact==='stufe/watt')return {unit:'Stufe/Watt',custom:false,explicit:true};
    if(['bar'].includes(lower))return {unit:'bar',custom:false,explicit:true};
    if(['keine','kein','none','ohne'].includes(lower))return {unit:'keine',custom:false,explicit:true};
    return {unit:raw,custom:true,explicit:true};
  }
  function normalizeLoadUnit(value){
    return normalizeLoadUnitInfo(value,'kg').unit;
  }
  function structuredNumberPattern(){return '-?\\d+(?:[,.]\\d+)?';}
  function structuredUnitPattern(){return '[A-Za-zÄÖÜäöüß%°/._-]+(?:\\s*/\\s*[A-Za-zÄÖÜäöüß%°/._-]+)?';}
  function normalizeStructuredNumber(value){return String(value||'').replace(',','.').trim();}
  function normalizeMetricToken(token){
    const raw=String(token||'').trim().replace('.','');
    const lower=raw.toLowerCase();
    if(['wdh','wh','rep','reps'].includes(lower))return {unit:'Wdh',metricUnit:'Wdh',time:false,label:'Wdh'};
    if(['min','minute','minutes','minuten','sek','sec','secs','s','zeit','time','dauer'].includes(lower))return {unit:'Zeit',metricUnit:'Zeit',time:true,label:raw||'Zeit'};
    return {unit:raw||'Wdh',metricUnit:raw||'Wdh',time:false,label:raw||'Wdh',custom:true};
  }
  function parseExerciseQuantityText(text){
    const body=String(text||'');
    const n=structuredNumberPattern(), u=structuredUnitPattern();
    const freeU='([^\\s\\d@,:;]+(?:\\s*/\\s*[^\\s\\d@,:;]+)?)';
    const out={startMetric:'',unit:'',metricUnit:'',startLoad:'',weightUnit:'',loadUnit:'',customLoadUnit:false,needsReview:false};
    const loadBeforeMetric=body.match(new RegExp('('+n+')\\s*'+freeU+'\\s*@\\s*('+n+')\\s*(wdh|wh|rep|reps)\\b','i'));
    if(loadBeforeMetric){
      const loadUnitInfo=normalizeLoadUnitInfo(loadBeforeMetric[2]||'kg','kg');
      out.startLoad=normalizeStructuredNumber(loadBeforeMetric[1]);
      out.weightUnit=loadUnitInfo.unit;
      out.loadUnit=loadUnitInfo.unit;
      out.customLoadUnit=!!loadUnitInfo.custom;
      out.startMetric=normalizeStructuredNumber(loadBeforeMetric[3]);
      out.unit='Wdh'; out.metricUnit='Wdh';
      if(loadUnitInfo.custom)out.needsReview=true;
      return out;
    }
    const compact=body.match(new RegExp('('+n+')\\s*x\\s*('+n+')(?:\\s*('+u+'))?','i'));
    const rep=body.match(new RegExp('('+n+')\\s*(wdh|wh|rep|reps)\\b','i'));
    const time=body.match(new RegExp('('+n+')\\s*(min|minute|minutes|minuten|sek\\.?|sec|secs|s|zeit|time|dauer)\\b','i'));
    if(rep){
      out.startMetric=normalizeStructuredNumber(rep[1]);
      out.unit='Wdh'; out.metricUnit='Wdh';
    }else if(time){
      const mt=normalizeMetricToken(time[2]);
      out.startMetric=normalizeStructuredNumber(time[1])+' '+mt.label;
      out.unit=mt.unit; out.metricUnit=mt.metricUnit;
    }else if(compact){
      out.startMetric=normalizeStructuredNumber(compact[1]);
      out.unit='Wdh'; out.metricUnit='Wdh';
    }
    let loadUnitInfo=null, loadMatch=null;
    loadMatch=body.match(new RegExp('@\\s*('+n+')\\s*('+u+')?','i'));
    if(loadMatch){
      out.startLoad=normalizeStructuredNumber(loadMatch[1]);
      loadUnitInfo=normalizeLoadUnitInfo(loadMatch[2]||'kg','kg');
    }else{
      loadMatch=body.match(new RegExp('@\\s*('+u+')\\s*('+n+')','i'));
      if(loadMatch){
        out.startLoad=normalizeStructuredNumber(loadMatch[2]);
        loadUnitInfo=normalizeLoadUnitInfo(loadMatch[1],'kg');
      }else{
        loadMatch=body.match(new RegExp('@\\s*('+u+')\\b','i'));
        if(loadMatch)loadUnitInfo=normalizeLoadUnitInfo(loadMatch[1],'kg');
      }
    }
    if(!loadUnitInfo&&compact){
      out.startLoad=normalizeStructuredNumber(compact[2]);
      loadUnitInfo=normalizeLoadUnitInfo(compact[3]||'kg','kg');
    }
    if(!loadUnitInfo){
      let rest=body;
      [compact,rep,time].forEach(m=>{if(m)rest=rest.replace(m[0],' ');});
      rest=rest.replace(new RegExp('@\\s*(?:'+n+'\\s*'+u+'?|'+u+'\\s*'+n+'|'+u+')','ig'),' ');
      loadMatch=rest.match(new RegExp('('+n+')\\s*('+u+')\\b','i'));
      if(loadMatch){
        out.startLoad=normalizeStructuredNumber(loadMatch[1]);
        loadUnitInfo=normalizeLoadUnitInfo(loadMatch[2],'kg');
      }else{
        loadMatch=rest.match(new RegExp('('+u+')\\s*('+n+')\\b','i'));
        if(loadMatch){
          out.startLoad=normalizeStructuredNumber(loadMatch[2]);
          loadUnitInfo=normalizeLoadUnitInfo(loadMatch[1],'kg');
        }
      }
    }
    if(loadUnitInfo&&loadUnitInfo.explicit){
      out.weightUnit=loadUnitInfo.unit;
      out.loadUnit=loadUnitInfo.unit;
      out.customLoadUnit=!!loadUnitInfo.custom;
      if(loadUnitInfo.custom)out.needsReview=true;
    }
    return out;
  }
  function parseSideModeFromText(text){
    const raw=' '+String(text||'').toLowerCase().replace(/[.,;:]+/g,' ')+' ';
    if(/\b(lr|l\/r|li\/re|links\/rechts|li|re|links|rechts)\b/.test(raw))return 'LR';
    return 'BI';
  }
  function ensureKGGDataStore(){
    if(window.KGGDataStore && typeof window.KGGDataStore.getCurrentPlan==='function')return window.KGGDataStore;
    const store={currentPlan:{id:'plan_'+Date.now(),title:'KGG Plan',createdAt:new Date().toISOString(),updatedAt:new Date().toISOString(),patient:{},exercises:[],source:'ui'}};
    window.KGGDataStore={
      init(meta){store.meta={...(store.meta||{}),...(meta||{})};return this;},
      setCurrentPlan(plan,reason){store.currentPlan={...(store.currentPlan||{}),...(plan||{}),updatedAt:new Date().toISOString(),lastReason:reason||''};return store.currentPlan;},
      getCurrentPlan(){return JSON.parse(JSON.stringify(store.currentPlan||{exercises:[]}));},
      getState(){return JSON.parse(JSON.stringify(store));}
    };
    return window.KGGDataStore;
  }
  function ensureUiExerciseShape(ex){
    const localId=ex.localId||ex.uiLocalId||(String(ex.id||'').startsWith('p_')?ex.id:makeLocalId());
    return {...ex, id:localId, localId, side:normalizeSideMode(ex.side||ex.sides||ex.laterality||'BI'), media:ensureExerciseMediaList(ex), sourceId:ex.sourceId||ex.bankId||(!String(ex.id||'').startsWith('p_')?ex.id:''), bankId:ex.bankId||(!String(ex.id||'').startsWith('p_')?ex.id:'')};
  }
  function currentPatientData(){return {name:state.patient&&state.patient.name||'',date:$('planDate')&&$('planDate').value||'',therapist:state.patient&&state.patient.therapist||'',notes:state.patient&&state.patient.notes||''};}
  function syncStatePlanToStore(reason){
    const ds=ensureKGGDataStore();
    state.plan=Array.isArray(state.plan)?state.plan.map(ensureUiExerciseShape):[];
    ds.setCurrentPlan({
      id:state.planId||'plan_'+(state.createdAt||Date.now()),
      title:state.planTitle||'KGG Plan',
      patient:{...(state.patient||{}),...currentPatientData()},
      exercises:state.plan.map(ex=>({...ex})),
      source:'ui-shell'
    },reason||'sync_state_to_store');
    return ds.getCurrentPlan();
  }
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
```
