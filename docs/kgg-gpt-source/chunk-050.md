# KGG Source Chunk 050

- Source: `kgg-update/index.html`
- Lines: 21001-21420

```html
        doc.rect(thumbX-.45,thumbY-.45,thumbW+.9,thumbH+.9);
        doc.addImage(thumb.dataUrl,'JPEG',thumbX,thumbY,thumbW,thumbH);
      }catch(err){console.warn('PDF-Thumbnail konnte nicht gezeichnet werden:',err);}
      pdfResetInk(doc);
    }
    pdfSetFont(doc,7.1,'bold');
    pdfText(doc,pdfShort((ex.exNo||'EX')+' · '+(ex.name||'Übung'),textMax),x+labelW+2.3,y+5.0);
    const sideLabel=sideModeLabel(ex.side||'BI');
    const startParts=[];
    if(ex.startLoad)startParts.push('Startlast '+ex.startLoad+' '+(ex.loadUnit||'kg'));
    if(ex.startMetric)startParts.push('Startwert '+ex.startMetric+' '+(ex.metricUnit||'Wdh'));
    const meta=[(ex.sets||3)+' Sätze',sideLabel].concat(startParts).concat([(ex.loadUnit||'kg'),(ex.metricUnit==='Wdh'?'Wiederholungen':(ex.metricUnit||'Wdh'))]).join(' · ');
    pdfSetFont(doc,4.55,'normal');
    pdfText(doc,pdfShort(meta,canDrawThumb?64:95),x+labelW+2.3,y+9.1);
    pdfSetFont(doc,3.35,'normal');
    pdfText(doc,pdfShort(ex.machineLine||'',canDrawThumb?82:128),x+labelW+2.3,y+12.5);
    const tableY=y+15.2;
    drawKggTableScaffold(doc,ex,x+1.6,tableY,w-3.2,h-(tableY-y)-1.5);
    pdfResetInk(doc);
  }


  function drawKggPdfLayoutV1(doc,snapshot){
    const size=getPdfPageSize(doc);
    const layout={pageW:size.w,pageH:size.h,margin:5.4,headerH:17.5,gap:2.6};
    const gridTop=layout.margin+layout.headerH+3.1;
    const footerH=3.8;
    const gridH=layout.pageH-gridTop-layout.margin-footerH;
    const target=snapshot.layoutTarget||{};
    const largeSingleRow=target.grid==='1x3';
    const cols=largeSingleRow?1:2,rows=3;
    const slotLimit=cols*rows;
    const boxW=(layout.pageW-(layout.margin*2)-(layout.gap*(cols-1)))/cols;
    const boxH=(gridH-(layout.gap*(rows-1)))/rows;
    const pages=(snapshot.pages&&snapshot.pages.length?snapshot.pages:[{pageNo:1,pageCount:1,slots:[]}]);
    const pageOrientation=(target.orientation||'landscape');
    pages.forEach((page,pageIdx)=>{
      if(pageIdx>0)doc.addPage('a4',pageOrientation);
      pdfResetInk(doc);
      drawKggCornerMarkers(doc,layout);
      drawKggPdfHeader(doc,snapshot,page,layout);
      const slots=(page.slots||page.exercises||[]).slice(0,slotLimit);
      while(slots.length<slotLimit)slots.push({empty:true});
      slots.forEach((slot,slotIdx)=>{
        const col=slotIdx%cols;
        const row=Math.floor(slotIdx/cols);
        const x=layout.margin+col*(boxW+layout.gap);
        const y=gridTop+row*(boxH+layout.gap);
        drawKggExerciseBox(doc,slot,x,y,boxW,boxH);
      });
      pdfResetInk(doc);
      pdfSetFont(doc,3.75,'normal');
      const template=(snapshot.layoutTarget&&snapshot.layoutTarget.templateId)||'TPL-BASIS-A-CLASSIC-L6-v2';
      pdfText(doc,'KGG|'+template+'|'+(page.pageNo||pageIdx+1)+'/'+(snapshot.pageCount||pages.length)+'|#EX-Layout|'+(snapshot.createdAt||'').slice(0,10),layout.pageW-layout.margin,layout.pageH-2.2,{align:'right'});
      pdfSetFont(doc,3.3,'normal');
      pdfText(doc,PDF_RUNTIME_FINGERPRINT,layout.margin,layout.pageH-2.2);
    });
  }

  function createScaledPdfDoc(doc,scale,options){
    const s=Number(scale)||1;
    const opts=options||{};
    const virtualW=Number(opts.virtualW)||297,virtualH=Number(opts.virtualH)||210;
    const pageOrientation=opts.orientation||(virtualW>virtualH?'landscape':'portrait');
    const scaled={
      internal:{pageSize:{width:virtualW,height:virtualH,getWidth:()=>virtualW,getHeight:()=>virtualH}},
      addPage:(_format,orientation)=>{doc.addPage([virtualW*s,virtualH*s],orientation||pageOrientation);return scaled;},
      setFont:(family,style)=>{doc.setFont(family,style);return scaled;},
      setFontSize:size=>{doc.setFontSize(Number(size||0)*s);return scaled;},
      setLineWidth:width=>{doc.setLineWidth(Number(width||0)*s);return scaled;},
      setDrawColor:(...args)=>{doc.setDrawColor(...args);return scaled;},
      setTextColor:(...args)=>{doc.setTextColor(...args);return scaled;},
      setFillColor:(...args)=>{doc.setFillColor(...args);return scaled;},
      rect:(x,y,w,h,style)=>{doc.rect(x*s,y*s,w*s,h*s,style);return scaled;},
      roundedRect:(x,y,w,h,rx,ry,style)=>{try{doc.roundedRect(x*s,y*s,w*s,h*s,(rx||0)*s,(ry||0)*s,style);}catch(e){doc.rect(x*s,y*s,w*s,h*s,style);}return scaled;},
      line:(x1,y1,x2,y2)=>{doc.line(x1*s,y1*s,x2*s,y2*s);return scaled;},
      text:(text,x,y,opts)=>{doc.text(String(text==null?'':text),x*s,y*s,opts||{});return scaled;}
    };
    return scaled;
  }

  function drawKggLargePrintPdfLayout(doc,snapshot){
    const size=getPdfPageSize(doc);
    const layout={pageW:size.w,pageH:size.h,margin:10,gap:7};
    const patient=snapshot.patient||{};
    const exercises=(snapshot.pages||[]).flatMap(page=>(page.slots||page.exercises||[])).filter(ex=>ex&&!ex.empty);
    let pageNo=0,y=0;
    const startPage=()=>{
      if(pageNo>0)doc.addPage('a4','landscape');
      pageNo+=1;
      y=layout.margin;
      pdfResetInk(doc);
      doc.setLineWidth(.45);
      try{doc.roundedRect(layout.margin,y,layout.pageW-layout.margin*2,21,2,2);}catch(e){doc.rect(layout.margin,y,layout.pageW-layout.margin*2,21);}
      pdfSetFont(doc,18,'bold');
      pdfText(doc,'KGG Trainingsplan - Grossdruck',layout.margin+5,y+8.2);
      pdfSetFont(doc,9,'normal');
      const line='Patient/in: '+pdfShort(patient.displayName||patient.name||'Patient/in',42)+'   Start: '+pdfShort(patient.startDate||'-',16);
      pdfText(doc,line,layout.margin+5,y+16.2);
      y+=29;
    };
    const drawCard=(ex,index)=>{
      const cardH=34;
      if(y+cardH>layout.pageH-layout.margin-6)startPage();
      const x=layout.margin,w=layout.pageW-layout.margin*2;
      doc.setLineWidth(.35);
      try{doc.roundedRect(x,y,w,cardH,2,2);}catch(e){doc.rect(x,y,w,cardH);}
      pdfSetFont(doc,15,'bold');
      pdfText(doc,(index+1)+'. '+pdfShort(ex.name||'Uebung',56),x+5,y+8.5);
      const side=sideModeLabel(ex.side||'BI');
      const meta=[];
      meta.push('Saetze: '+(ex.sets||3));
      meta.push('Ausfuehrung: '+side);
      if(ex.startLoad)meta.push('Startlast: '+ex.startLoad+' '+(ex.loadUnit||'kg'));
      if(ex.startMetric)meta.push('Startwert: '+ex.startMetric+' '+(ex.metricUnit||'Wdh'));
      meta.push('Eintragen: kg / Wiederholungen oder Zeit / Schmerz 1-10');
      pdfSetFont(doc,9.6,'normal');
      pdfText(doc,pdfShort(meta.join('  |  '),118),x+5,y+18.3);
      pdfSetFont(doc,8.2,'normal');
      pdfText(doc,'Trainingstage 1 bis 6 - bitte Werte nach jedem Training notieren.',x+5,y+27.2);
      y+=cardH+layout.gap;
    };
    startPage();
    if(!exercises.length){
      pdfSetFont(doc,14,'bold');
      pdfText(doc,'Keine Uebungen im Plan.',layout.margin+5,y+12);
    }else{
      exercises.forEach(drawCard);
    }
    pdfResetInk(doc);
    pdfSetFont(doc,6.5,'normal');
    pdfText(doc,PDF_RUNTIME_FINGERPRINT,layout.margin,layout.pageH-3.2);
  }

  function pdfBytesFromBinaryString(pdf){
    const bytes=new Uint8Array(pdf.length);
    for(let i=0;i<pdf.length;i++)bytes[i]=pdf.charCodeAt(i)&255;
    return bytes;
  }
  function pdfBlobFromDoc(doc){
    if(!doc)return null;
    if(typeof doc.output==='function'){
      try{
        const blob=doc.output('blob');
        if(blob instanceof Blob)return blob;
      }catch(e){}
      try{
        const buffer=doc.output('arraybuffer');
        if(buffer)return new Blob([buffer],{type:'application/pdf'});
      }catch(e){}
      try{
        const text=doc.output();
        if(typeof text==='string')return new Blob([pdfBytesFromBinaryString(text)],{type:'application/pdf'});
      }catch(e){}
    }
    if(typeof doc._buildPdf==='function'){
      try{return new Blob([pdfBytesFromBinaryString(doc._buildPdf())],{type:'application/pdf'});}catch(e){}
    }
    return null;
  }
  function downloadPdfBlob(blob,filename){
    if(!blob)return;
    const url=URL.createObjectURL(blob);
    const a=document.createElement('a');
    a.href=url;
    a.download=filename||'kgg_trainingsplan.pdf';
    document.body.appendChild(a);
    a.click();
    setTimeout(()=>{URL.revokeObjectURL(url);a.remove();},1000);
  }
  function pdfBlobToBase64(blob){
    return new Promise((resolve,reject)=>{
      const reader=new FileReader();
      reader.onload=()=>resolve(String(reader.result||'').split(',')[1]||'');
      reader.onerror=()=>reject(reader.error||new Error('PDF konnte nicht gelesen werden.'));
      reader.readAsDataURL(blob);
    });
  }
  function nativePdfBridge(){
    return window.KGGNativePdf&&window.KGGNativePdf.available?window.KGGNativePdf:null;
  }
  async function sendPdfToNative(action){
    if(!currentPdfPreview||!currentPdfPreview.blob)return false;
    const bridge=nativePdfBridge();
    if(!bridge)return false;
    try{
      const base64=await pdfBlobToBase64(currentPdfPreview.blob);
      if(action==='download'&&typeof bridge.download==='function')return !!bridge.download(currentPdfPreview.filename,base64);
      if(action==='print'&&typeof bridge.print==='function')return !!bridge.print(currentPdfPreview.filename,base64);
      if(typeof bridge.open==='function')return !!bridge.open(currentPdfPreview.filename,base64);
    }catch(err){console.warn('Native PDF-Aktion fehlgeschlagen:',err);}
    return false;
  }
  let currentPdfPreview=null;
  let pdfPreviewFallbackTimer=null;
  function setPdfPreviewFallbackVisible(isVisible){
    const fallback=$('pdfPreviewFallback');
    if(fallback)fallback.classList.toggle('hidden',!isVisible);
  }
  function shouldUsePdfMobileBridge(){
    return !!(window.matchMedia && (window.matchMedia('(pointer: coarse)').matches || window.matchMedia('(max-width: 700px)').matches));
  }
  function setPdfMobileBridgeVisible(isVisible){
    const bridge=$('pdfPreviewMobileBridge');
    const modal=$('pdfPreviewModal');
    if(bridge)bridge.classList.toggle('hidden',!isVisible);
    if(modal)modal.classList.toggle('pdfPreviewModalMobile',isVisible);
  }
  function openPdfPreview(result){
    if(!result||!result.blob)return;
    if(currentPdfPreview&&currentPdfPreview.url)URL.revokeObjectURL(currentPdfPreview.url);
    if(pdfPreviewFallbackTimer)clearTimeout(pdfPreviewFallbackTimer);
    const url=URL.createObjectURL(result.blob);
    currentPdfPreview={url,blob:result.blob,filename:result.filename||'kgg_trainingsplan.pdf'};
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
    const doc=new JsPdfCtor({orientation:state.largePdfMode?'portrait':'landscape',unit:'mm',format:state.largePdfMode?[420,594]:'a4'});
    const patientName=snapshot.patient&&snapshot.patient.displayName||snapshot.patient&&snapshot.patient.name||'patient';
    const safeName=String(patientName).replace(/[^a-z0-9äöüß_-]+/ig,'_').replace(/^_+|_+$/g,'')||'patient';
    const stamp=new Date().toISOString().replace(/[-:]/g,'').replace(/\..+$/,'').replace('T','_');
    try{doc.setProperties({title:'KGG Trainingsplan '+safeName,subject:PDF_RUNTIME_FINGERPRINT+' '+pdfMode,creator:VERSION});}catch(e){}
    if(state.largePdfMode)drawKggPdfLayoutV1(createScaledPdfDoc(doc,2,{orientation:'portrait',virtualW:210,virtualH:297}),snapshot); else drawKggPdfLayoutV1(doc,snapshot);
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
```
