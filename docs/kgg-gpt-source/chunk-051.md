# KGG Source Chunk 051

- Source: `kgg-update/index.html`
- Lines: 21421-21840

```html
        createdAt:new Date().toISOString(),
        media:mediaMeta||{expected:false,count:0,ready:0,status:'none'}
      }
    };
  }
  function buildKggH2PayloadFromInternalPayload(payload){
    const p=payload||{};
    const meta=p.meta||{};
    const plan={id:meta.planId||p.id||'',title:meta.title||'KGG Trainingsplan',days:meta.days||6};
    return buildKggH2PayloadFromPlan(plan,Array.isArray(p.plan)?p.plan:[],p.patient||{},meta.media||null);
  }
  function makeKggH2ShareUrl(baseUrl,publicPayload){
    const base=String(baseUrl||'').split('#')[0].split('?')[0];
    return base+'?plan='+encodeURIComponent('KGGH2:'+encodeKggJsonBase64Url(publicPayload));
  }
  function expandKggH2Exercise(item){
    const e=Array.isArray(item)?item:[];
    const media=Array.isArray(e[7])?e[7]:(e[7]?[e[7]]:[]);
    const loadUnit=e[3]||'kg';
    const metricUnit=e[4]||'Wdh';
    return {
      name:e[0]||'Übung',
      sets:Number(e[1])||3,
      side:normalizeSideMode(e[2]||'BI'),
      weightUnit:loadUnit,
      loadUnit,
      unit:metricUnit,
      metricUnit,
      startLoad:e[5]||'',
      startMetric:e[6]||'',
      media:media.map(entry=>typeof entry==='string'?{id:entry,type:'image',bundleRef:true}:ensureMediaShape(entry)),
      videoUrl:e[8]||'',
      videoLabel:e[9]||'Video öffnen'
    };
  }
  function convertKggH2PayloadToPatientPayload(raw){
    const data=raw||{};
    return {
      kind:'kgg-patient-plan',
      version:2,
      createdAt:data.m&&data.m.createdAt||new Date().toISOString(),
      patient:data.patient||data.p||{},
      plan:Array.isArray(data.e)?data.e.map(expandKggH2Exercise):[],
      meta:{planId:data.i||'',title:data.t||'KGG Trainingsplan',source:'KGGH2',media:data.m&&data.m.media||null}
    };
  }
  function buildPatientShareFromCurrentPlan(planOverride,options){
    if(!planOverride)savePendingToBank('ui_make_patient_payload');
    const plan=planOverride||getCurrentPlanForOutput('ui_make_patient_payload');
    const rawExercises=Array.isArray(plan.exercises)?plan.exercises:[];
    const exercises=rawExercises.map(buildPatientExercisePayload);
    const patient=plan.patient||state.patient||{};
    const ttlSeconds=Number(options&&options.ttlSeconds)||currentMediaShareTtlSeconds();
    const mediaMeta=buildPlanMediaMeta(rawExercises,ttlSeconds);
    const payload=(window.KGGQrCore&&typeof window.KGGQrCore.makePatientPayload==='function')?window.KGGQrCore.makePatientPayload(exercises,patient,{planId:plan.id||'',updatedAt:plan.updatedAt||'',source:'current-plan-state',media:mediaMeta}):{kind:'kgg-patient-plan',version:1,createdAt:new Date().toISOString(),patient,plan:exercises,meta:{planId:plan.id||'',updatedAt:plan.updatedAt||'',source:'current-plan-state',media:mediaMeta}};
    payload.meta={...(payload.meta||{}),media:mediaMeta};
    const publicPayload=buildKggH2PayloadFromPlan(plan,exercises,patient,mediaMeta);
    const debugBase=String(location.href||'').split('#')[0];
    const debugUrl=debugBase+'#kgg='+encodePatientPayload(payload);
    const shareable=isShareablePatientBaseUrl(patientBaseUrl);
    const patientUrl=shareable?makeKggH2ShareUrl(patientBaseUrl,publicPayload):'';
    return {url:patientUrl,debugUrl,payload,publicPayload,plan,shareable};
  }
  function tryRenderQrCode(url){const box=$('patientQrBox'), status=$('patientQrStatus'); if(!box||!status)return; box.innerHTML=''; status.textContent=''; try{let imgData=''; if(window.KGGQrCore&&typeof window.KGGQrCore.renderQrToImg==='function'){imgData=window.KGGQrCore.renderQrToImg(url,{cellSize:10,margin:4});} else if(typeof window.qrcode==='function'){const qr=window.qrcode(0,'L'); qr.addData(url); qr.make(); imgData=qr.createDataURL(10,4);} if(imgData){const img=document.createElement('img'); img.alt='QR-Code zur Patienten-App'; img.src=imgData; box.appendChild(img); return;}}catch(err){console.warn('QR konnte nicht gerendert werden:',err);} box.innerHTML='<span class="qrStatus">QR fehlgeschlagen. Link nutzen.</span>'; status.textContent='Link nutzen.';}
  function cloneSharePlan(plan){return plan?JSON.parse(JSON.stringify(plan)):null;}
  function planHasMedia(plan){
    const exercises=plan&&Array.isArray(plan.exercises)?plan.exercises:[];
    return exercises.some(ex=>ensureExerciseMediaList(ex).length>0);
  }
  function currentPatientLinkUrl(){
    const link=$('patientAppLink');
    return link&&link.href&&link.href!=='#'?link.href:'';
  }
  function setPatientCopyButtonLabel(){
    const btn=$('copyPatientLink');
    if(btn)btn.textContent=currentMediaShareTtlSeconds()>=MEDIA_UPLOAD_LONG_TTL_SECONDS?'24h-Link kopieren':'Link kopieren';
  }
  function setManualPatientLinkField(value,visible,selectText){
    const field=$('patientLinkCopyField');
    if(!field)return;
    field.value=value||'';
    field.classList.toggle('hidden',!visible);
    if(visible&&selectText){
      try{field.focus({preventScroll:true});}catch(err){try{field.focus();}catch(innerErr){}}
      try{field.select();}catch(err){}
      try{field.setSelectionRange(0,field.value.length);}catch(err){}
    }
  }
  async function copyTextValue(value){
    if(!value)return false;
    if(navigator.clipboard&&window.isSecureContext){
      try{await navigator.clipboard.writeText(value);return true;}catch(err){console.warn('Clipboard API blockiert:',err);}
    }
    const field=$('patientLinkCopyField');
    if(!field||!document.execCommand)return false;
    setManualPatientLinkField(value,true,true);
    try{return !!document.execCommand('copy');}catch(err){console.warn('execCommand copy blockiert:',err);return false;}
  }
  async function copyPatientLink(){
    if(Date.now()<copyPatientLinkSuppressClickUntil)return;
    const status=$('patientQrStatus');
    const url=currentPatientLinkUrl();
    if(!url){if(status)status.textContent='Kein Link.';return;}
    try{
      const ok=await copyTextValue(url);
      if(ok){
        setManualPatientLinkField(url,false,false);
        if(status)status.textContent=currentMediaShareTtlSeconds()>=MEDIA_UPLOAD_LONG_TTL_SECONDS?'24h-Link kopiert.':'Link kopiert.';
      }else{
        setManualPatientLinkField(url,true,true);
        if(status)status.textContent='Kopieren blockiert. Link ist markiert.';
      }
    }catch(err){
      console.warn('Patienten-Link konnte nicht kopiert werden:',err);
      setManualPatientLinkField(url,true,true);
      if(status)status.textContent='Kopieren blockiert. Link ist markiert.';
    }
  }
  async function enableLongMediaShare(){
    const btn=$('copyPatientLink'), status=$('patientQrStatus');
    if(!lastPatientSharePlanSnapshot){if(status)status.textContent='Erst Patienten-Link erzeugen.';return;}
    if(!planHasMedia(lastPatientSharePlanSnapshot)){if(status)status.textContent='Keine Bilder im Plan.';return;}
    patientShareTtlSeconds=MEDIA_UPLOAD_LONG_TTL_SECONDS;
    if(btn)btn.textContent='24h-Link wird erstellt ...';
    try{
      const url=await renderPatientShareOutput({plan:lastPatientSharePlanSnapshot,ttlSeconds:MEDIA_UPLOAD_LONG_TTL_SECONDS,force:true});
      setManualPatientLinkField(url,!!url,true);
      if(status)status.textContent=url?'24h-Link bereit und markiert.':'24h-Link fehlgeschlagen.';
    }finally{
      setPatientCopyButtonLabel();
    }
  }
  function openLongMediaConfirmModal(){
    const status=$('patientQrStatus');
    if(!lastPatientSharePlanSnapshot){if(status)status.textContent='Erst Patienten-Link erzeugen.';return;}
    if(!planHasMedia(lastPatientSharePlanSnapshot)){if(status)status.textContent='Keine Bilder im Plan.';return;}
    $('longMediaConfirmModal').classList.add('open');
  }
  function closeLongMediaConfirmModal(){$('longMediaConfirmModal').classList.remove('open');}
  function confirmLongMediaShare(){closeLongMediaConfirmModal(); enableLongMediaShare();}
  function setupPatientLinkCopyLongPress(){
    const btn=$('copyPatientLink');
    if(!btn||btn.dataset.longPressBound)return;
    btn.dataset.longPressBound='1';
    let timer=null;
    let holding=false;
    const reset=()=>{if(timer){clearTimeout(timer);timer=null;} if(holding){holding=false;setPatientCopyButtonLabel();}};
    btn.addEventListener('pointerdown',()=>{
      if(!lastPatientSharePlanSnapshot)return;
      holding=true;
      btn.textContent='5 Sek. halten für 24h';
      timer=setTimeout(()=>{
        timer=null;
        holding=false;
        copyPatientLinkSuppressClickUntil=Date.now()+700;
        openLongMediaConfirmModal();
      },MEDIA_LONG_PRESS_MS);
    });
    btn.addEventListener('pointerup',reset);
    btn.addEventListener('pointerleave',reset);
    btn.addEventListener('pointercancel',reset);
    btn.onclick=copyPatientLink;
  }
  async function renderPatientShareOutput(options){
    const output=$('patientOutputBox'), choices=$('finishChoices'), close=$('closeShare'), finishNotice=$('finishNotice');
    const planOverride=options&&options.plan;
    const ttlSeconds=Number(options&&options.ttlSeconds)||currentMediaShareTtlSeconds();
    if(finishNotice)finishNotice.textContent='Ausgabe wird vorbereitet ...';
    const mediaPrep=await prepareMediaUploadsForPatientShare({plan:planOverride,ttlSeconds,force:!!(options&&options.force)});
    if(!mediaPrep.ok){
      if(output)output.classList.add('hidden');
      if(choices)choices.classList.remove('hidden');
      if(close)close.classList.add('hidden');
      if(finishNotice)finishNotice.textContent=mediaPrep.message||'Medien fehlgeschlagen. Plan bleibt offen.';
      return '';
    }
    const share=buildPatientShareFromCurrentPlan(planOverride,{ttlSeconds});
    lastPatientSharePlanSnapshot=cloneSharePlan(share.plan);
    if(output)output.classList.remove('hidden');
    if(choices)choices.classList.add('hidden');
    if(close)close.classList.remove('hidden');
    if(finishNotice)finishNotice.textContent='';
    const link=$('patientAppLink'), notice=$('patientShareNotice'), box=$('patientQrBox'), status=$('patientQrStatus'), copyBtn=$('copyPatientLink');
    $('shareText').value='INTERNE DEBUG-TESTAUSGABE – nicht an Patient:innen weitergeben\n\nLokaler Testlink:\n'+share.debugUrl+'\n\nPayload JSON:\n'+JSON.stringify(share.payload,null,2);
    const dbg=$('debugPayloadBox'); if(dbg)dbg.open=false;
    if(!share.shareable){
      if(notice)notice.textContent='Lokaler Test.';
      if(link){link.classList.remove('hidden'); link.href=share.debugUrl; link.textContent='Patienten-Test öffnen';}
      if(copyBtn){copyBtn.classList.remove('hidden'); setPatientCopyButtonLabel();}
      setManualPatientLinkField(share.debugUrl,false,false);
      setupPatientLinkCopyLongPress();
      if(box)box.innerHTML='<span class="qrStatus">Lokaler Test.</span>';
      if(status)status.textContent='Testlink bereit.';
      return share.debugUrl;
    }
    if(notice){
      const mediaInfo=share.payload&&share.payload.meta&&share.payload.meta.media;
      const longInfo=ttlSeconds>=MEDIA_UPLOAD_LONG_TTL_SECONDS?' 24h aktiv.':'';
      notice.textContent='Patient:innen-Link bereit.'+(mediaInfo&&mediaInfo.expected?' Bilder bereit.':'')+longInfo;
    }
    if(link){link.classList.remove('hidden'); link.href=share.url;}
    if(copyBtn){copyBtn.classList.remove('hidden'); setPatientCopyButtonLabel();}
    setManualPatientLinkField(share.url,false,false);
    setupPatientLinkCopyLongPress();
    tryRenderQrCode(share.url);
    return share.url;
  }
  function makeShare(){return buildPatientShareFromCurrentPlan().url;}

  function resetFinishModal(){
    const choices=$('finishChoices'), output=$('patientOutputBox'), close=$('closeShare'), notice=$('finishNotice'), dbg=$('debugPayloadBox'), copyBtn=$('copyPatientLink');
    if(choices)choices.classList.remove('hidden');
    if(output)output.classList.add('hidden');
    if(close)close.classList.add('hidden');
    if(notice)notice.textContent='';
    if(dbg)dbg.open=false;
    patientShareTtlSeconds=MEDIA_UPLOAD_TTL_SECONDS;
    lastPatientSharePlanSnapshot=null;
    if(copyBtn)copyBtn.textContent='Link kopieren';
    setManualPatientLinkField('',false,false);
  }
  function openFinishModal(){resetFinishModal(); $('shareModal').classList.add('open');}
  function closeFinishModal(){$('shareModal').classList.remove('open');}
  function openLargePdfModal(){$('largePdfModal').classList.add('open');}
  function closeLargePdfModal(){$('largePdfModal').classList.remove('open');}
  function archiveAndCloseCurrentPlan(reason){
    const plan=getCurrentPlanForOutput(reason||'ui_finish_archive');
    const exercises=Array.isArray(plan.exercises)?plan.exercises:[];
    if(exercises.length){
      const patient=plan.patient||{};
      const title=patient.name||plan.title||'KGG Plan';
      const entry={id:plan.id||makeLocalId(),name:title,date:new Date().toISOString(),patient:{...patient},exercises:exercises.map(ex=>({...ex})),source:reason||'finished'};
      state.recent=[entry].concat(state.recent||[]).slice(0,20);
    }
    state.plan=[];
    state.liveDraftId=null;
    state.bankOpen=false;
    state.planText='';
    if($('exerciseInput'))$('exerciseInput').value='';
    syncStatePlanToStore(reason||'ui_finish_close_current_plan');
    save();
    render();
  }
  async function finishWithPdf(options){
    const notice=$('finishNotice');
    const hasModeOverride=!!(options&&Object.prototype.hasOwnProperty.call(options,'large'));
    const previousLargeMode=state.largePdfMode;
    if(hasModeOverride){state.largePdfMode=!!options.large; applyLargePdfMode();}
    if(notice)notice.textContent='PDF wird erstellt ...';
    try{
      const pdfResult=await buildPdfFromCurrentPlan();
      if(hasModeOverride){state.largePdfMode=previousLargeMode; applyLargePdfMode();}
      archiveAndCloseCurrentPlan('ui_finish_pdf');
      closeFinishModal();
      openPdfPreview(pdfResult);
    }catch(err){
      if(hasModeOverride){state.largePdfMode=previousLargeMode; applyLargePdfMode(); save();}
      console.warn('PDF konnte nicht erzeugt werden:',err);
      if(notice)notice.textContent='PDF fehlgeschlagen. Plan bleibt offen.';
    }
  }
  async function finishWithPatientApp(){
    const notice=$('finishNotice');
    try{
      const url=await renderPatientShareOutput();
      if(!url)return;
      archiveAndCloseCurrentPlan('ui_finish_patient_app');
    }catch(err){
      console.warn('Patienten-Ausgabe konnte nicht erzeugt werden:',err);
      if(notice)notice.textContent='Ausgabe fehlgeschlagen. Plan bleibt offen.';
    }
  }

  function decodePatientPayloadFromHash(){
    const hash=String(location.hash||'');
    const publicMatch=hash.match(/^#KGGH2:(.+)$/i);
    if(publicMatch){
      try{return convertKggH2PayloadToPatientPayload(decodeKggJsonBase64Url(publicMatch[1]));}
      catch(err){console.warn('KGGH2 Patienten-Link konnte nicht gelesen werden:',err); return {error:true};}
    }
    const match=hash.match(/^#kgg=(.+)$/);
    if(!match)return null;
    try{
      const encoded=decodeURIComponent(match[1]).replace(/-/g,'+').replace(/_/g,'/');
      const padded=encoded+'='.repeat((4-encoded.length%4)%4);
      return JSON.parse(decodeURIComponent(escape(atob(padded))));
    }catch(err){
      console.warn('Patienten-Link konnte nicht gelesen werden:',err);
      return {error:true};
    }
  }
  function base64UrlToBytes(value){
    const text=String(value||'').replace(/-/g,'+').replace(/_/g,'/');
    const padded=text+'='.repeat((4-text.length%4)%4);
    const binary=atob(padded);
    const bytes=new Uint8Array(binary.length);
    for(let i=0;i<binary.length;i++)bytes[i]=binary.charCodeAt(i);
    return bytes;
  }
  function patientMediaDb(){
    return new Promise((resolve,reject)=>{
      if(!('indexedDB' in window)){reject(new Error('IndexedDB nicht verfuegbar'));return;}
      const req=indexedDB.open('kgg_patient_media_v1',1);
      req.onupgradeneeded=()=>{const db=req.result; if(!db.objectStoreNames.contains('images'))db.createObjectStore('images',{keyPath:'id'});};
      req.onsuccess=()=>resolve(req.result);
      req.onerror=()=>reject(req.error||new Error('Patienten-Medien-Speicher nicht verfuegbar'));
    });
  }
  async function patientGetCachedMedia(id){
    const db=await patientMediaDb();
    return new Promise(resolve=>{
      const tx=db.transaction('images','readonly');
      const req=tx.objectStore('images').get(id);
      req.onsuccess=()=>resolve(req.result||null);
      req.onerror=()=>resolve(null);
    });
  }
  async function patientPutCachedMedia(record){
    const db=await patientMediaDb();
    return new Promise((resolve,reject)=>{
      const tx=db.transaction('images','readwrite');
      tx.objectStore('images').put(record);
      tx.oncomplete=()=>resolve(record);
      tx.onerror=()=>reject(tx.error||new Error('Bild konnte nicht lokal gespeichert werden'));
    });
  }
  async function patientFetchEncryptedMedia(media){
    if(window.KGGPatientMediaFetchAdapter&&typeof window.KGGPatientMediaFetchAdapter.fetch==='function')return window.KGGPatientMediaFetchAdapter.fetch(media);
    if(!media.downloadUrl)throw new Error('Bild ist noch nicht bereit');
    const res=await fetch(media.downloadUrl,{cache:'no-store'});
    if(!res.ok)throw new Error('Bild konnte nicht geladen werden');
    return res.blob();
  }
  async function patientDecryptMedia(media,encryptedBlob){
    if(!window.crypto||!crypto.subtle)throw new Error('Web Crypto nicht verfuegbar');
    const info=media.crypto||{};
    if(!info.key||!info.iv)throw new Error('Medienschluessel fehlt');
    const key=await crypto.subtle.importKey('raw',base64UrlToBytes(info.key),{name:'AES-GCM'},false,['decrypt']);
    const encrypted=await encryptedBlob.arrayBuffer();
    const plain=await crypto.subtle.decrypt({name:'AES-GCM',iv:base64UrlToBytes(info.iv)},key,encrypted);
    return new Blob([plain],{type:media.mime||'image/jpeg'});
  }
  function updatePatientMediaBox(id,html,kind){
    const selector='[data-patient-media-id="'+String(id).replace(/"/g,'\\"')+'"]';
    const box=document.querySelector(selector);
    if(!box)return;
    box.className='patientMedia patientMedia_'+(kind||'loading');
    box.innerHTML=html;
  }
  async function loadPatientMediaItem(media){
    const id=String(media&&media.id||'');
    if(!id)return false;
    const cached=await patientGetCachedMedia(id);
    if(cached&&cached.blob){
      const url=URL.createObjectURL(cached.blob);
      updatePatientMediaBox(id,'<img src="'+url+'" alt="Uebungsbild"><small>Bild lokal gespeichert.</small>','ready');
      return true;
    }
    const encrypted=await patientFetchEncryptedMedia(media);
    const imageBlob=await patientDecryptMedia(media,encrypted);
    await patientPutCachedMedia({id,blob:imageBlob,mime:media.mime||'image/jpeg',savedAt:new Date().toISOString()});
    const url=URL.createObjectURL(imageBlob);
    updatePatientMediaBox(id,'<img src="'+url+'" alt="Uebungsbild"><small>Bild lokal gespeichert.</small>','ready');
    return true;
  }
  function retryPatientMediaItem(media){
    const id=String(media&&media.id||'');
    if(!id)return;
    const retryMs=Math.max(10,Number(media.retrySeconds)||MEDIA_RETRY_SECONDS)*1000;
    const until=Date.now()+retryMs;
    const tick=async()=>{
      try{
        await loadPatientMediaItem(media);
      }catch(err){
        if(Date.now()<until){
          updatePatientMediaBox(id,'<span>Bild wird geladen ...</span><small>Die App versucht es automatisch erneut.</small>','loading');
          setTimeout(tick,4000);
        }else{
          updatePatientMediaBox(id,'<span>Bild konnte nicht geladen werden.</span><small>Der Plan bleibt ohne Bild nutzbar. Bitte bei Bedarf neuen QR-Code erstellen lassen.</small>','error');
        }
      }
    };
    tick();
  }
  function patientMediaMarkup(ex){
    const media=ensureExerciseMediaList(ex).filter(item=>item.type==='image');
    if(!media.length)return '';
    return '<div class="patientMediaList">'+media.map(item=>'<div class="patientMedia patientMedia_loading" data-patient-media-id="'+escapeHtml(item.id)+'"><span>Bild wird geladen ...</span><small>Verschluesselte Datei wird geholt und lokal gespeichert.</small></div>').join('')+'</div>';
  }
  function initPatientMediaDownloads(exercises){
    (exercises||[]).forEach(ex=>ensureExerciseMediaList(ex).filter(item=>item.type==='image').forEach(retryPatientMediaItem));
  }

  function patientExerciseLine(ex,index){
    const name=escapeHtml(ex&&ex.name||'Übung '+(index+1));
    const sets=escapeHtml(ex&&ex.sets||3);
    const metric=escapeHtml(ex&&ex.startMetric||ex&&ex.metric||'');
    const metricUnit=escapeHtml(ex&&ex.unit||ex&&ex.metricUnit||'Wdh');
    const load=escapeHtml(ex&&ex.startLoad||ex&&ex.load||ex&&ex.weight||'');
    const loadUnit=escapeHtml(ex&&ex.weightUnit||ex&&ex.loadUnit||'kg');
    const side=sideModeLabel(ex&&ex.side||ex&&ex.laterality||'BI');
    const details=[sets+' Sätze'];
    if(metric)details.push(metric+' '+metricUnit);
    if(load)details.push(load+' '+loadUnit);
    details.push(side);
    return '<article class="patientExercise"><b>'+(index+1)+'. '+name+'</b><small>'+details.map(escapeHtml).join(' · ')+'</small>'+patientMediaMarkup(ex)+'</article>';
  }

  function renderPatientHashView(){
    const payload=decodePatientPayloadFromHash();
    if(!payload)return false;
    const plan=Array.isArray(payload.plan)?payload.plan:(Array.isArray(payload.exercises)?payload.exercises:[]);
    const patient=payload.patient||{};
    const displayName=escapeHtml(patient.name||patient.initials||patient.id||'Patient/in');
    const date=escapeHtml(patient.date||patient.startDate||'');
    const exercises=plan.filter(Boolean);
    document.body.innerHTML='<main class="patientAppView">'+
      '<header><h1>KGG Trainingsplan</h1><p>'+displayName+(date?' · '+date:'')+'</p></header>'+
      (payload.error?'<section class="patientNotice">Dieser Patienten-Link konnte nicht gelesen werden.</section>':'')+
      '<section class="patientExercises">'+
```
