# KGG Source Chunk 051

- Source: `kgg-update/src` modular source
- Lines: 21421-21840

```html
    const frame=$('pdfPreviewFrame');
    const useMobileBridge=shouldUsePdfMobileBridge();
    setPdfPreviewFallbackVisible(false);
    setPdfMobileBridgeVisible(useMobileBridge);
    if(frame){frame.src=useMobileBridge?'about:blank':url;frame.onerror=()=>setPdfPreviewFallbackVisible(true);}
    const notice=$('pdfPreviewNotice');
    if(notice)notice.textContent=useMobileBridge?'PDF bereit. Öffnen oder herunterladen.':'PDF bereit. Drucken oder herunterladen.';
    $('pdfPreviewModal').classList.add('open');
    if(!useMobileBridge){
      pdfPreviewFallbackTimer=setTimeout(()=>{
        if(currentPdfPreview)setPdfPreviewFallbackVisible(true);
      },1200);
    }
  }
  function closePdfPreview(){
    if(pdfPreviewFallbackTimer)clearTimeout(pdfPreviewFallbackTimer);
    pdfPreviewFallbackTimer=null;
    $('pdfPreviewModal').classList.remove('open');
    const frame=$('pdfPreviewFrame');
    if(frame)frame.src='about:blank';
    setPdfPreviewFallbackVisible(false);
    setPdfMobileBridgeVisible(false);
    if(currentPdfPreview&&currentPdfPreview.url)URL.revokeObjectURL(currentPdfPreview.url);
    currentPdfPreview=null;
  }
  async function printCurrentPdfPreview(){
    if(await sendPdfToNative('print'))return;
    if(shouldUsePdfMobileBridge()){
      openCurrentPdfPreviewTab();
      return;
    }
    const frame=$('pdfPreviewFrame');
    try{
      if(frame&&frame.contentWindow){frame.contentWindow.focus();frame.contentWindow.print();return;}
    }catch(e){}
    if(currentPdfPreview&&currentPdfPreview.url){
      const win=window.open(currentPdfPreview.url,'_blank');
      if(win)setTimeout(()=>{try{win.focus();win.print();}catch(e){}},600);
    }
  }
  async function downloadCurrentPdfPreview(){
    if(await sendPdfToNative('download'))return;
    if(currentPdfPreview)downloadPdfBlob(currentPdfPreview.blob,currentPdfPreview.filename);
  }
  function openPdfUrlCrossBrowser(url){
    if(!url)return false;
    try{
      const win=window.open('','_blank');
      if(win){
        try{win.opener=null;}catch(e){}
        win.location.href=url;
        return true;
      }
    }catch(e){}
    try{
      const a=document.createElement('a');
      a.href=url;
      a.target='_blank';
      a.rel='noopener';
      document.body.appendChild(a);
      a.click();
      setTimeout(()=>a.remove(),1000);
      return true;
    }catch(e){}
    return false;
  }
  async function openCurrentPdfPreviewTab(){
    if(!currentPdfPreview||!currentPdfPreview.url)return;
    if(await sendPdfToNative('open'))return;
    if(!openPdfUrlCrossBrowser(currentPdfPreview.url)){
      downloadPdfBlob(currentPdfPreview.blob,currentPdfPreview.filename);
    }
  }

  async function buildPdfFromCurrentPlan(){
    savePendingToBank('ui_make_pdf');
    const plan=getCurrentPlanForOutput('ui_make_pdf');
    const snapshot=buildKggPdfSnapshot(plan,state.largePdfMode?{layout:'large-single-row'}:null);
    await attachKggPdfExerciseThumbnails(snapshot,plan);
    window.KGGLatestPdfSnapshot=snapshot;
    let JsPdfCtor=null;
    try{JsPdfCtor=await ensureJsPdfForPdfTest();}catch(e){console.warn('KGG jsPDF Testloader:',e);}
    if(!JsPdfCtor){
      alert('jsPDF-Testeinbindung konnte nicht geladen werden. PDF wird lokal im Browser erzeugt, sobald jsPDF verfuegbar ist. Der aktuelle Plan-Snapshot wurde nur intern vorbereitet.');
      console.info('KGG PDF Snapshot Adapter:',snapshot);
      return snapshot;
    }
    const pdfMode=state.largePdfMode?'grossdruck':'standard';
    const doc=new JsPdfCtor({orientation:state.largePdfMode?'portrait':'landscape',unit:'mm',format:'a4'});
    const patientName=snapshot.patient&&snapshot.patient.displayName||snapshot.patient&&snapshot.patient.name||'patient';
    const safeName=String(patientName).replace(/[^a-z0-9äöüß_-]+/ig,'_').replace(/^_+|_+$/g,'')||'patient';
    const stamp=new Date().toISOString().replace(/[-:]/g,'').replace(/\..+$/,'').replace('T','_');
    try{doc.setProperties({title:'KGG Trainingsplan '+safeName,subject:PDF_RUNTIME_FINGERPRINT+' '+pdfMode,creator:VERSION});}catch(e){}
    drawKggPdfLayoutV1(doc,snapshot);
    const filename='kgg_trainingsplan_'+safeName+'_'+VERSION+'_'+pdfMode+'_'+stamp+'.pdf';
    const blob=pdfBlobFromDoc(doc);
    if(!blob)doc.save(filename);
    return {snapshot,blob,filename,pdfMode};
  }

  function encodePatientPayload(payload){return (window.KGGQrCore&&typeof window.KGGQrCore.encodePayload==='function')?window.KGGQrCore.encodePayload(payload):btoa(unescape(encodeURIComponent(JSON.stringify(payload))));}
  function isShareablePatientBaseUrl(url){
    const raw=String(url||'').trim();
    if(!raw)return false;
    if(/^(content|file|blob|data|about):/i.test(raw))return false;
    if(!/^https?:\/\//i.test(raw))return false;
    try{const parsed=new URL(raw); const host=parsed.hostname.toLowerCase(); if(host==='localhost'||host==='127.0.0.1'||host==='0.0.0.0'||host.endsWith('.local'))return false;}catch(e){return false;}
    return true;
  }
  function makeUrlWithPayload(baseUrl,payload){
    const base=String(baseUrl||'').split('#')[0].split('?')[0];
    const publicPayload=payload&&Array.isArray(payload.e)?payload:buildKggH2PayloadFromInternalPayload(payload);
    return base+'?plan='+encodeURIComponent('KGGH2:'+encodeKggJsonBase64Url(publicPayload));
  }
  function buildExerciseMediaManifestForPatient(ex){
    return ensureExerciseMediaList(ex).filter(item=>item.type==='image').map(item=>({
      id:item.id,
      type:'image',
      mime:item.mime,
      name:item.name,
      width:item.width,
      height:item.height,
      bytes:item.encryptedSize||0,
      encrypted:true,
      status:item.downloadUrl?'ready':'upload-pending',
      downloadUrl:item.downloadUrl||'',
      expiresInSeconds:item.ttlSeconds||MEDIA_UPLOAD_TTL_SECONDS,
      retrySeconds:item.retrySeconds||MEDIA_RETRY_SECONDS,
      crypto:item.crypto||null
    }));
  }
  function buildExerciseMediaRefsForPatient(ex){
    const ids=ensureExerciseMediaList(ex).filter(item=>item.type==='image'&&item.id).map(item=>item.id);
    return ids.length?ids:'';
  }
  function compactMediaBundleForQr(bundle){
    if(!bundle||!bundle.downloadUrl||!bundle.crypto)return null;
    return {
      u:bundle.downloadUrl,
      k:bundle.crypto.key,
      i:bundle.crypto.iv,
      c:Number(bundle.count)||0,
      t:Number(bundle.expiresInSeconds)||MEDIA_UPLOAD_TTL_SECONDS,
      r:Number(bundle.retrySeconds)||MEDIA_RETRY_SECONDS
    };
  }
  function buildPatientExercisePayload(ex){
    const copy={...ex};
    const media=buildExerciseMediaManifestForPatient(ex);
    if(media.length)copy.media=media; else delete copy.media;
    return copy;
  }
  function buildPlanMediaMeta(rawExercises,ttlSeconds){
    const items=(rawExercises||[]).flatMap(ensureExerciseMediaList);
    const count=items.length;
    const bundle=compactMediaBundleForQr(lastPatientMediaBundleManifest);
    const ready=bundle?count:items.filter(item=>item.downloadUrl&&item.status==='ready').length;
    const meta={expected:count>0,count,ready,ttlSeconds:Number(ttlSeconds)||currentMediaShareTtlSeconds(),retrySeconds:MEDIA_RETRY_SECONDS,status:count?(ready===count?'ready':'upload-pending'):'none'};
    if(bundle)meta.b=bundle;
    return meta;
  }
  function encodeKggJsonBase64Url(value){
    return btoa(unescape(encodeURIComponent(JSON.stringify(value||{})))).replace(/\+/g,'-').replace(/\//g,'_').replace(/=+$/,'');
  }
  function decodeKggJsonBase64Url(value){
    const encoded=String(value||'').replace(/-/g,'+').replace(/_/g,'/');
    const padded=encoded+'='.repeat((4-encoded.length%4)%4);
    return JSON.parse(decodeURIComponent(escape(atob(padded))));
  }
  function compactKggH2Exercise(ex){
    const media=lastPatientMediaBundleManifest?buildExerciseMediaRefsForPatient(ex):buildExerciseMediaManifestForPatient(ex);
    const loadUnit=ex&&ex.weightUnit||ex&&ex.loadUnit||'kg';
    const metricUnit=ex&&ex.unit||ex&&ex.metricUnit||'Wdh';
    return [
      ex&&ex.name||'Übung',
      normalizeSetCount(ex&&ex.sets),
      normalizeSideMode(ex&&ex.side||ex&&ex.laterality||'BI'),
      loadUnit,
      metricUnit,
      ex&&ex.startLoad||ex&&ex.load||ex&&ex.weight||'',
      ex&&ex.startMetric||ex&&ex.metric||ex&&ex.reps||'',
      media&&media.length?media:'',
      ex&&ex.videoUrl||'',
      ex&&ex.videoLabel||'Video öffnen'
    ];
  }
  function buildKggH2PayloadFromPlan(plan,exercises,patient,mediaMeta){
    const sourcePlan=plan||{};
    const sourcePatient=patient||{};
    return {
      v:2,
      i:String(sourcePlan.id||sourcePlan.planId||'plan_'+Date.now()),
      t:String(sourcePlan.title||'KGG Trainingsplan'),
      d:Number(sourcePlan.days)||6,
      extendDays:true,
      stepDays:6,
      e:(exercises||[]).map(compactKggH2Exercise),
      patient:{
        name:sourcePatient.name||sourcePatient.displayName||'',
        date:sourcePatient.date||sourcePatient.startDate||'',
        therapist:sourcePatient.therapist||'',
        notes:sourcePatient.notes||''
      },
      m:{
        source:'kgg-therapist-app',
        schema:'KGGH2',
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
```
