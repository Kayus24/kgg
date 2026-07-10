# KGG Source Chunk 054

- Source: `kgg-update/index.html`
- Lines: 22681-23100

```html
  }
  function currentLocalGeminiKey(){return localGeminiKeys()[0]||'';}

  /* ========================================================================
     KGG v308 QR STRUCTURED OUTPUT + CURRENT-LAYOUT CONTACT-SHEET SCAN START
     Integrationskandidat aus v306: TPL-BASIS-A-CLASSIC-L6-v2, EX1-EX6,
     T1-Zeilen-Crops -> Contact-Sheet -> ein Gemini-Call -> lokale Zuordnung.
     Später entfernbar/isolierbar, aber KEINE zweite KGGScan-Engine.
     ======================================================================== */
  const KGG_CURRENT_LAYOUT_ID='TPL-BASIS-A-CLASSIC-L6-v2';
  const KGG_CURRENT_LAYOUT_BOXES=[
    {ex:1,name:'Adduktion Maschine',x:.027,y:.134,w:.470,h:.225,measure:'Wdh'},
    {ex:2,name:'Ein-Beinpresse',x:.503,y:.134,w:.470,h:.225,measure:'Wdh'},
    {ex:3,name:'Ein-Beinpresse',x:.027,y:.385,w:.470,h:.225,measure:'Wdh'},
    {ex:4,name:'Ein-Beinpresse',x:.503,y:.385,w:.470,h:.225,measure:'Wdh'},
    {ex:5,name:'Copenhagen Plank',x:.027,y:.637,w:.470,h:.318,measure:'Sek.'},
    {ex:6,name:'Beinpresse',x:.503,y:.637,w:.470,h:.318,measure:'Wdh'}
  ];
  function kggClampRect(rect,w,h){
    const x=Math.max(0,Math.min(w-1,Math.round(rect.x)));
    const y=Math.max(0,Math.min(h-1,Math.round(rect.y)));
    const rw=Math.max(1,Math.min(w-x,Math.round(rect.w)));
    const rh=Math.max(1,Math.min(h-y,Math.round(rect.h)));
    return {x,y,w:rw,h:rh};
  }
  function kggCropCanvas(src,rect){
    const r=kggClampRect(rect,src.width,src.height);
    const c=document.createElement('canvas');
    c.width=r.w; c.height=r.h;
    const x=c.getContext('2d',{willReadFrequently:true});
    x.fillStyle='#fff'; x.fillRect(0,0,c.width,c.height);
    x.drawImage(src,r.x,r.y,r.w,r.h,0,0,r.w,r.h);
    return c;
  }
  function kggCurrentLayoutRowStripRect(box,imgW,imgH,wide){
    const bx=box.x*imgW, by=box.y*imgH, bw=box.w*imgW, bh=box.h*imgH;
    const valueLeft=bx+bw*.110;
    const valueRight=bx+bw*.858;
    const cy=by+(box.ex<=4?bh*.595:bh*.485);
    const stripH=wide?Math.max(54,bh*.19):Math.max(42,bh*.15);
    return {x:valueLeft,y:cy-stripH*.55,w:valueRight-valueLeft,h:stripH};
  }
  function kggNormalizeCanvasForCurrentLayout(src){
    const canvas=scanCloneCanvas(src);
    const ctx=canvas.getContext('2d',{willReadFrequently:true});
    ctx.save();
    ctx.filter='contrast(1.18) brightness(1.03) saturate(.92)';
    ctx.drawImage(src,0,0);
    ctx.restore();
    canvas.dataset.kggLayout=KGG_CURRENT_LAYOUT_ID;
    return canvas;
  }
  function kggBuildCurrentLayoutT1Strips(srcCanvas){
    const src=kggNormalizeCanvasForCurrentLayout(srcCanvas);
    return KGG_CURRENT_LAYOUT_BOXES.map(box=>{
      const rect=kggCurrentLayoutRowStripRect(box,src.width,src.height,true);
      return {ex:box.ex,name:box.name,measure:box.measure,rect,canvas:kggCropCanvas(src,rect)};
    });
  }
  function kggBuildCurrentLayoutContactSheet(strips){
    const list=strips||[];
    if(!list.length)throw new Error('Keine T1-Zeilen-Crops erzeugt.');
    const scale=1.5;
    const labelW=180;
    const rowH=92;
    const maxW=Math.max.apply(null,list.map(s=>s.canvas.width));
    const c=document.createElement('canvas');
    c.width=Math.round(labelW+maxW*scale+40);
    c.height=36+list.length*rowH+24;
    const x=c.getContext('2d',{willReadFrequently:true});
    x.fillStyle='#fff'; x.fillRect(0,0,c.width,c.height);
    x.fillStyle='#071027'; x.font='bold 24px Arial';
    x.fillText('KGG T1 Contact-Sheet · aktuelles Layout EX1-EX6',20,28);
    list.forEach((s,i)=>{
      const y=46+i*rowH;
      x.fillStyle='#eef6ff'; x.fillRect(16,y-8,c.width-32,rowH-8);
      x.strokeStyle='#dce3eb'; x.strokeRect(16,y-8,c.width-32,rowH-8);
      x.fillStyle='#071027'; x.font='bold 28px Arial'; x.fillText('EX'+s.ex,26,y+36);
      x.font='bold 16px Arial'; x.fillText(s.name,78,y+26);
      x.font='12px Arial'; x.fillStyle='#657386'; x.fillText(s.measure==='Sek.'?'Zeit/Sekunden':'kg/Wdh links nach rechts',78,y+46);
      x.drawImage(s.canvas,labelW,y-2,s.canvas.width*scale,s.canvas.height*scale);
    });
    c.dataset.kggContactSheet='current-layout-t1-v307';
    return c;
  }
  function kggCurrentLayoutPrompt(){
    return [
      'Lies das KGG Contact-Sheet. Es zeigt EX1 bis EX6, jeweils nur die handschriftlich ausgefüllte T1-Zeile aus dem Layout '+KGG_CURRENT_LAYOUT_ID+'.',
      'Gib ausschließlich gültiges JSON aus. Schema: {"groups":[[...EX1 Zahlen...],[...EX2 Zahlen...],[...EX3 Zahlen...],[...EX4 Zahlen...],[...EX5 Zahlen...],[...EX6 Zahlen...]],"warnings":[]}.',
      'Jede Gruppe enthält nur die sichtbaren handschriftlichen Zahlen der jeweiligen EX-Zeile in Leserichtung von links nach rechts.',
      'Keine Übungsnamen raten. Keine leeren Tabellenwerte ergänzen. Keine Erklärungen. Keine Markdown-Codeblöcke.'
    ].join('\n');
  }
  function kggNormalizeGroupsFromJson(json){
    if(!json)return [];
    if(Array.isArray(json.groups))return json.groups.map(g=>Array.isArray(g)?g.map(Number).filter(Number.isFinite):[]);
    if(Array.isArray(json.exercises))return json.exercises.map(ex=>(ex.numbers||ex.values||[]).map(Number).filter(Number.isFinite));
    if(Array.isArray(json))return json.map(g=>Array.isArray(g)?g.map(Number).filter(Number.isFinite):[]);
    return [];
  }
  function kggCurrentLayoutGroupsQuality(groups){
    const warnings=[];
    const normalized=KGG_CURRENT_LAYOUT_BOXES.map((box,i)=>({ex:box.ex,name:box.name,measure:box.measure,numbers:Array.isArray(groups&&groups[i])?groups[i].map(Number).filter(Number.isFinite):[]}));
    if(normalized.length!==6)warnings.push('6 EX-Gruppen erwartet');
    normalized.forEach(item=>{
      if(!item.numbers.length)warnings.push('EX'+item.ex+' leer');
      if(item.numbers.length!==6)warnings.push('EX'+item.ex+' hat '+item.numbers.length+' statt 6 Werte');
      if(item.numbers.length>10)warnings.push('EX'+item.ex+' zu viele Zahlen');
    });
    const totalFound=normalized.reduce((sum,item)=>sum+item.numbers.length,0);
    const completeBoxes=normalized.filter(item=>item.numbers.length===6).length;
    return {ok:!warnings.length,layout:KGG_CURRENT_LAYOUT_ID,exerciseCount:normalized.length,numberCount:totalFound,completeBoxes,warnings,normalized};
  }
  function kggCurrentLayoutGroupToText(box,values){
    const nums=(values||[]).map(v=>String(v).trim()).filter(Boolean);
    if(box.measure==='Sek.'){
      const s1=nums.length>=6?nums[1]:(nums[0]||'');
      const s2=nums.length>=6?nums[3]:(nums[1]||'');
      const s3=nums.length>=6?nums[5]:(nums[2]||'');
      return [box.name,'Satz 1: '+(s1||'')+' Sek.','Satz 2: '+(s2||'')+' Sek.','Satz 3: '+(s3||'')+' Sek.'].join('\n');
    }
    const kg1=nums[0]||'', w1=nums[1]||'';
    const kg2=nums[2]||'', w2=nums[3]||'';
    const kg3=nums[4]||'', w3=nums[5]||'';
    return [box.name,'Satz 1: '+w1+' wdh @ '+kg1+' kg','Satz 2: '+w2+' wdh @ '+kg2+' kg','Satz 3: '+w3+' wdh @ '+kg3+' kg'].join('\n');
  }
  function kggCurrentLayoutGroupsToPlanText(groups){
    return KGG_CURRENT_LAYOUT_BOXES.map((box,i)=>kggCurrentLayoutGroupToText(box,groups&&groups[i]||[])).join('\n\n').trim();
  }
  async function callGeminiCurrentLayoutContactSheet(file){
    const keys=localGeminiKeys();
    if(!keys.length)throw new Error('Kein QR. OCR braucht Admin-Konfig.');
    const imageCanvas=await scanImageCanvasFromFile(file,1900);
    const redacted=redactScanCanvasForExternalOcr(imageCanvas);
    const strips=kggBuildCurrentLayoutT1Strips(redacted);
    const contact=kggBuildCurrentLayoutContactSheet(strips);
    const inline=canvasToGeminiInlineData(contact);
    const models=['gemini-2.5-flash-lite',GEMINI_SCAN_MODEL,'gemini-2.5-flash'].filter((v,i,a)=>v&&a.indexOf(v)===i);
    let lastError=null;
    for(const model of models){
      for(const key of keys){
        const controller=new AbortController();
        const timer=setTimeout(()=>controller.abort(),18000);
        try{
          const body={
            contents:[{role:'user',parts:[{text:kggCurrentLayoutPrompt()},{inline_data:inline}]}],
            generationConfig:{temperature:0,responseMimeType:'application/json',maxOutputTokens:1000}
          };
          const response=await fetch('https://generativelanguage.googleapis.com/v1beta/models/'+encodeURIComponent(model)+':generateContent',{
            method:'POST',
            headers:{'Content-Type':'application/json','x-goog-api-key':key},
            body:JSON.stringify(body),
            signal:controller.signal
          });
          const json=await response.json().catch(()=>({}));
          if(!response.ok)throw new Error((json&&json.error&&json.error.message)||('Gemini OCR HTTP '+response.status));
          const rawText=geminiScanResponseText(json);
          const parsed=parseLooseJson(rawText);
          if(!parsed.ok)throw new Error('Contact-Sheet JSON nicht parsebar.');
          const groups=kggNormalizeGroupsFromJson(parsed.json);
          const quality=kggCurrentLayoutGroupsQuality(groups);
          const planText=kggCurrentLayoutGroupsToPlanText(groups);
          if(!planText)throw new Error('Contact-Sheet OCR hat keinen Plantext erzeugt.');
          return {
            type:'paper-current-layout-contactsheet',
            planText,
            rawText,
            model,
            json:parsed.json,
            jsonRepaired:!!parsed.repaired,
            groups,
            quality,
            applyText:KGG_CURRENT_LAYOUT_BOXES.map(box=>box.name).join(', '),
            redactedBeforeExternalOcr:true,
            contactSheet:true,
            layout:KGG_CURRENT_LAYOUT_ID
          };
        }catch(err){
          lastError=err;
        }finally{clearTimeout(timer);}
      }
    }
    throw lastError||new Error('Current-layout Contact-Sheet-OCR fehlgeschlagen.');
  }
  async function callGeminiPaperFallback(file){
    try{
      const result=await callGeminiCurrentLayoutContactSheet(file);
      if(result&&result.planText)return result;
    }catch(err){
      console.warn('v307 Contact-Sheet-OCR fehlgeschlagen, Legacy-Fallback wird versucht:',err);
    }
    return callGeminiLegacyPaperFallback(file);
  }
  /* ========================================================================
     KGG v308 QR STRUCTURED OUTPUT + CURRENT-LAYOUT CONTACT-SHEET SCAN ENDE
     ======================================================================== */
  async function callGeminiLegacyPaperFallback(file){
    const keys=localGeminiKeys();
    if(!keys.length)throw new Error('Kein QR. OCR braucht Admin-Konfig.');
    const canvas=redactScanCanvasForExternalOcr(createScanReadingCanvas(await scanImageCanvasFromFile(file,1500)));
    const inline=canvasToGeminiInlineData(canvas);
    const models=['gemini-2.5-flash-lite',GEMINI_SCAN_MODEL,'gemini-2.5-flash'].filter((v,i,a)=>v&&a.indexOf(v)===i);
    let lastError=null;
    for(const model of models){
      for(const key of keys){
        const controller=new AbortController();
        const timer=setTimeout(()=>controller.abort(),35000);
        try{
          const body={
            contents:[{role:'user',parts:[{text:geminiScanPrompt()},{inline_data:inline}]}],
            generationConfig:{temperature:0,responseMimeType:'application/json',maxOutputTokens:1400}
          };
          const response=await fetch('https://generativelanguage.googleapis.com/v1beta/models/'+encodeURIComponent(model)+':generateContent',{
            method:'POST',
            headers:{'Content-Type':'application/json','x-goog-api-key':key},
            body:JSON.stringify(body),
            signal:controller.signal
          });
          const json=await response.json().catch(()=>({}));
          if(!response.ok)throw new Error((json&&json.error&&json.error.message)||('Gemini OCR HTTP '+response.status));
          const rawText=geminiScanResponseText(json);
          const parsed=parseLooseJson(rawText);
          const planText=parsed.ok?scanResultToPlanText(parsed.json):cleanGeminiScanText(rawText);
          const quality=scanPaperQuality(planText,parsed.ok?parsed.json:null);
          if(planText)return {type:'paper',planText,rawText,model,quality,json:parsed.ok?parsed.json:null,jsonRepaired:!!parsed.repaired,redactedBeforeExternalOcr:true};
          throw new Error('Gemini OCR hat keinen Übungstext erkannt.');
        }catch(err){
          lastError=err;
        }finally{clearTimeout(timer);}
      }
    }
    throw lastError||new Error('Papierplan-OCR fehlgeschlagen.');
  }
  function qrParsedToScanResult(parsed){
    const json=parsed&&parsed.json;
    let payload=json;
    if(parsed&&parsed.type==='KGGH2')payload=convertKggH2PayloadToPatientPayload(json);
    const exercises=scanPayloadExercises(payload);
    const planText=scanResultToPlanText(payload);
    const applyText=exercises.length?exercises.map(scanExerciseToDocText).filter(Boolean).join('\n\n'):'';
    const warnings=[];
    if(!planText)warnings.push('QR erkannt, aber kein strukturierter Übungstext erzeugt.');
    return {type:'qr',qrType:parsed&&parsed.type||'QR',planText,applyText,rawText:planText||'QR erkannt.',json:payload,quality:{ok:warnings.length===0,warnings}};
  }
  const scanState={next:'page',activeIndex:0,jobs:[],decision:false,busy:false,lastError:'',lastInputKind:'camera'};
  window.scanJobsState=scanState.jobs;
  function scanNewJob(type){
    const job={id:'scan_'+Date.now()+'_'+Math.random().toString(36).slice(2,7),label:'Plan '+(scanState.jobs.length+1),short:'',type:type||'paper',pages:[],result:null,createdAt:new Date().toISOString(),status:'new',warnings:[]};
    scanState.jobs.push(job);
    scanState.activeIndex=scanState.jobs.length-1;
    return job;
  }
  function scanCurrentJob(){
    if(!scanState.jobs.length)return scanNewJob('paper');
    return scanState.jobs[Math.max(0,Math.min(scanState.activeIndex,scanState.jobs.length-1))]||scanNewJob('paper');
  }
  function scanFileMeta(file){return {name:file&&file.name||'Kamera-Foto',size:file&&file.size||0,type:file&&file.type||'image',addedAt:new Date().toISOString(),file:file||null};}
  // v313 Scan-Popup Repeat-Source-Modul:
  // Merkt sich, ob der letzte Bildweg Kamera oder Galerie/Datei war.
  // Weitere Seite / weiterer Plan verwenden danach automatisch denselben Weg.
  function normalizeScanInputKind(kind){return kind==='file'?'file':'camera';}
  function rememberScanInputKind(kind){
    const normalized=normalizeScanInputKind(kind);
    scanState.lastInputKind=normalized;
    try{localStorage.setItem('kgg_scan_last_input_kind_v1',normalized);}catch(err){}
    return normalized;
  }
  function lastScanInputKind(){
    if(scanState.lastInputKind==='file'||scanState.lastInputKind==='camera')return scanState.lastInputKind;
    try{const stored=localStorage.getItem('kgg_scan_last_input_kind_v1'); if(stored==='file'||stored==='camera')return stored;}catch(err){}
    return 'camera';
  }
  function patientShortGuess(){
    const value=String(state.patient&&state.patient.name||$('patientName')&&$('patientName').value||'').trim();
    if(!value)return '';
    const parts=value.split(/\s+/).filter(Boolean);
    if(parts.length>=2)return parts[0]+' '+parts[1].charAt(0)+'.';
    return value.slice(0,16);
  }
  async function scanAcceptFile(file,kind){
    const forceNew=scanState.next==='plan'||!scanState.jobs.length;
    let job=forceNew?scanNewJob('paper'):scanCurrentJob();
    const qr=await scanQrFromImageFile(file);
    if(qr.raw){
      setScanStatus('QR erkannt: Inhalt wird gelesen ...');
      try{
        const parsed=parseScannedQrRaw(qr.raw);
        if(parsed&&(parsed.type==='KGGCFG1'||parsed.type==='KGGCFG2')){
          setScanStatus(parsed.type==='KGGCFG2'?'QR erkannt: verschluesselter API-Key / Konfig-Transfer. Transfer-Code wird abgefragt ...':'QR erkannt: API-Key / Konfig-Transfer wird lokal gespeichert ...');
          const idx=scanState.jobs.indexOf(job);
          if(idx>=0&&!job.pages.length&&!job.result&&job.status==='new'){
            scanState.jobs.splice(idx,1);
            scanState.activeIndex=Math.max(0,Math.min(scanState.activeIndex,scanState.jobs.length-1));
          }
          const ok=await applyKggConfigTransferParsed(parsed);
          return {type:ok?'configTransfer':'configTransferCancelled',json:parsed.json};
        }
        if(parsed&&(parsed.type==='KGGSYNC1'||parsed.type==='KGGSYNC2')){
          setScanStatus(parsed.type==='KGGSYNC2'?'QR erkannt: Sync-Verbindung mit Daten wird gelesen ...':'QR erkannt: Sync-Kopplung wird gespeichert ...');
          const idx=scanState.jobs.indexOf(job);
          if(idx>=0&&!job.pages.length&&!job.result&&job.status==='new'){
            scanState.jobs.splice(idx,1);
            scanState.activeIndex=Math.max(0,Math.min(scanState.activeIndex,scanState.jobs.length-1));
          }
          if(parsed.type==='KGGSYNC2'){
            await applyNativeSyncBundle(parsed.json);
            return {type:'syncBundle',json:parsed.json};
          }
          applyNativeSyncInvite(parsed.json);
          return {type:'syncInvite',json:parsed.json};
        }
        if(job.pages.length||job.result){job=scanNewJob('qr');}
        setScanStatus('QR erkannt: Patientenplan wird gelesen ...');
        job.type='qr';
        job.pages.push(scanFileMeta(file));
        job.result=qrParsedToScanResult(parsed);
        job.result.qrHit=qr.hit||null;
        job.status='ready';
        job.short=job.short||patientShortGuess();
        scanState.next='plan';
        return job;
      }catch(err){
        setScanStatus('QR erkannt, aber Format nicht lesbar: '+(err&&err.message||err));
        if(job.pages.length||job.result){job=scanNewJob('paper');}
        job.type='paper';
        job.pages.push(scanFileMeta(file));
        job.warnings.push('QR erkannt, aber nicht parsebar: '+(err&&err.message||err));
        scanState.next='page';
        return job;
      }
    }
    if(forceNew||job.type==='qr'||job.result){job=forceNew?job:scanNewJob('paper');}
    job.type='paper';
    job.pages.push(scanFileMeta(file));
    if(kind==='file'&&qr&&!qr.raw){
      const qrWarn='QR-Foto-Import: '+(qr.reason||'Kein QR im Bild erkannt.');
      job.warnings.push(qrWarn);
      try{console.warn(qrWarn,qr.debug||{});}catch(err){}
    }
    job.status='queued';
    job.short=job.short||patientShortGuess();
    scanState.next='page';
    return job;
  }
  function scanStateSnapshot(){
    return {next:scanState.next,activeIndex:scanState.activeIndex,busy:scanState.busy,jobs:scanState.jobs.map(job=>({id:job.id,label:job.label,short:job.short,type:job.type,status:job.status,pages:job.pages.map(page=>({name:page.name,size:page.size,type:page.type})),hasResult:!!job.result,warnings:job.warnings||[]}))};
  }
  function setScanStatus(text){const el=$('scanStatus'); if(el){el.classList.remove('hidden'); el.textContent=text||'Bereit.';}}
  function ensureScanV295Styles(){
    if(document.getElementById('kggV295ScanCss'))return;
    const style=document.createElement('style');
    style.id='kggV295ScanCss';
    style.textContent='.kggScanV295{display:grid;gap:10px}.kggScanV295 .scanDecisionBackdrop{position:fixed;inset:0;z-index:99980;background:rgba(7,16,39,.34);backdrop-filter:blur(7px);-webkit-backdrop-filter:blur(7px)}.kggScanV295 .scanDecision{position:fixed;left:50%;top:50%;transform:translate(-50%,-50%);z-index:99990;width:min(92vw,500px);background:#fff;border:2px solid #1b2230;border-radius:22px;padding:14px;box-shadow:0 18px 55px rgba(7,16,39,.22)}.kggScanV295 .scanDecision h3{font-size:22px;margin:0 0 6px}.kggScanV295 .scanDecisionBtns{display:grid;gap:10px;margin-top:10px}.kggScanV295 .scanDecisionBtns.scanDecisionRepeatSource{grid-template-columns:1fr 1fr}.kggScanV295 .scanDecisionBtns.scanDecisionRepeatSource .scanRepeatBtn{min-height:58px;border:2px solid #1b2230;background:#fff;color:#071027;border-radius:16px;font-weight:1000;box-shadow:0 3px 10px rgba(7,16,39,.08)}.kggScanV295 .scanDecisionBtns.scanDecisionRepeatSource .scanFinishBtn{grid-column:1/-1;min-height:64px;border-radius:18px;font-size:20px;box-shadow:0 8px 22px rgba(7,16,39,.22)}.kggScanV295 .scanJobCard{background:#fff;border:1px solid var(--line);border-radius:18px;padding:12px;box-shadow:var(--shadow)}.kggScanV295 .scanJobCard.warn{border-color:#f2d38a;background:#fff8e8}.kggScanV295 .scanJobCard.good{border-color:#93d8a0;background:#f4fff6}.kggScanV295 .scanJobHead{display:flex;justify-content:space-between;gap:8px;align-items:center}.kggScanV295 .scanFileList{font-size:12px;color:var(--muted);font-weight:850;margin-top:6px}.kggScanV295 .scanResultText{width:100%;min-height:118px;border:1px solid var(--line);border-radius:14px;padding:10px;font-size:13px;line-height:1.35;margin-top:8px}.kggScanV295 .scanCardActions{display:grid;grid-template-columns:1fr 1fr;gap:8px;margin-top:8px}.kggScanV295 .scanCardActionsCompact{grid-template-columns:1fr 1.15fr}.kggScanV295 input.scanShort{width:100%;border:1px solid var(--line);border-radius:12px;padding:9px;font-size:14px;margin-top:8px}.kggScanV295 .scanWarning{font-size:12px;color:#8a5a00;font-weight:850;margin-top:6px}.kggScanV295 .scanJobCard.collapsed{padding:9px 12px;background:#f7fff8;border-color:#93d8a0}.kggScanV295 .scanJobCard.collapsed .scanCollapsedHint{display:block;font-size:12px;color:#54715a;font-weight:900;margin-top:2px}.kggScanV295 .scanJobTopActions{display:flex;align-items:center;gap:6px;flex:0 0 auto}.kggScanV295 .scanMiniBtn{border:1px solid var(--line);background:#fff;border-radius:999px;min-width:32px;height:32px;padding:0 8px;font-weight:1000;line-height:1;color:#071027}.kggScanV295 .scanRemoveBtn{border:1px solid rgba(226,59,84,.32);background:#fff5f7;color:#e23b54;border-radius:999px;width:34px;height:34px;padding:0;font-size:20px;font-weight:1000;line-height:1}.kggScanV295 .scanJobHeadMain{min-width:0;display:grid;gap:2px}.kggScanV295 .scanJobHeadMain b,.kggScanV295 .scanJobHeadMain small{overflow:hidden;text-overflow:ellipsis;white-space:nowrap}@media(max-width:520px){.kggScanV295 .scanCardActions{grid-template-columns:1fr}.kggScanV295 .scanDecisionBtns{grid-template-columns:1fr}.kggScanV295 .scanDecisionBtns.scanDecisionRepeatSource{grid-template-columns:1fr}}';
    document.head.appendChild(style);
  }
  function renderScanDecisionOverlay(){
    const id='kggScanDecisionOverlay';
    let layer=document.getElementById(id);
    if(!scanState.decision){if(layer)layer.remove();return;}
    if(!layer){
      layer=document.createElement('div');
      layer.id=id;
      layer.className='kggScanV295';
      document.body.appendChild(layer);
    }
    layer.innerHTML='<div class="scanDecisionBackdrop" aria-hidden="true"></div><div class="scanDecision" role="dialog" aria-modal="true"><h3>Foto hinzugef&uuml;gt</h3><p class="notice">Was kommt als N&auml;chstes?</p><div class="scanDecisionBtns scanDecisionRepeatSource"><button type="button" class="scanRepeatBtn" onclick="window.KGGScan.repeatSource(\'page\')">+ weitere Seite zu diesem Plan</button><button type="button" class="scanRepeatBtn" onclick="window.KGGScan.repeatSource(\'plan\')">+ weiterer Plan / Patient</button><button type="button" class="primary scanFinishBtn" onclick="window.KGGScan.start()">Fertig</button></div></div>';
  }
  function renderScanPreview(){
    ensureScanV295Styles();
    renderScanDecisionOverlay();
    const preview=$('scanPreview');
    if(!preview)return;
    const useInbox=!!$('scannedPlansBlock');
    const hasContent=(useInbox?(scanState.busy||scanState.lastError):(scanState.jobs.length||scanState.busy||scanState.lastError));
    preview.classList.toggle('hidden',!hasContent);
    if(!hasContent){preview.innerHTML='';return;}
    const jobsHtml=useInbox?'':scanState.jobs.map((job,index)=>{
      const resultText=scanResultToCopyText(job);
      const quality=job.result&&job.result.quality||{};
      const warn=[...(job.warnings||[]),...((quality.warnings)||[])];
      const cls=job.result?(quality.ok===false?'warn':'good'):(warn.length?'warn':'');
      const collapsed=!!job.collapsed;
      const typeLabel=job.type==='qr'?'QR-Plan':'Papierplan';
      const title=escapeHtml(job.short||job.label);
      const meta=escapeHtml(typeLabel+' · '+job.pages.length+' Bild(er)');
      const head='<div class="scanJobHead"><div class="scanJobHeadMain"><b>'+title+'</b><small>'+meta+'</small>'+(collapsed?'<span class="scanCollapsedHint">eingeklappt · antippen zum Öffnen</span>':'')+'</div><div class="scanJobTopActions"><button type="button" class="scanMiniBtn" onclick="window.KGGScan.toggleCollapse('+index+')" aria-label="Scankarte '+(collapsed?'ausklappen':'einklappen')+'">'+(collapsed?'▾':'▴')+'</button><button type="button" class="scanRemoveBtn" onclick="window.KGGScan.removeJob('+index+')" aria-label="Scankarte entfernen">×</button></div></div>';
      if(collapsed){
        return '<div class="scanJobCard '+cls+' collapsed">'+head+'</div>';
      }
      return '<div class="scanJobCard '+cls+'">'+
        head+
        '<input class="scanShort" value="'+escapeHtml(job.short||'')+'" placeholder="lokales Kürzel, z. B. Max M." oninput="window.KGGScan.setShort('+index+',this.value)">'+
        '<div class="scanFileList">'+escapeHtml(job.pages.map(p=>p.name).join(' · ')||'Noch kein Bild')+'</div>'+
        (warn.length?'<div class="scanWarning">Prüfen: '+escapeHtml(warn.join(' · '))+'</div>':'')+
        '<textarea id="kggScanCopyField'+index+'" class="scanResultText" readonly>'+escapeHtml(resultText||'Noch nicht ausgelesen.')+'</textarea>'+
        '<div class="scanCardActions scanCardActionsCompact">'+
          '<button type="button" class="mutedBtn" onclick="window.KGGScan.copyResult('+index+')">kopieren</button>'+
          '<button type="button" class="primary" onclick="window.KGGScan.applyResult('+index+')">weiter bearbeiten</button>'+
        '</div></div>';
    }).join('');
    const decisionHtml='';
    preview.innerHTML='<div class="kggScanV295">'+decisionHtml+(scanState.busy?'<div class="notice"><b>Scan läuft …</b></div>':'')+(scanState.lastError?'<div class="notice danger">'+escapeHtml(scanState.lastError)+'</div>':'')+jobsHtml+'</div>';
  }
  function collapseScanCards(reason){
    if(shouldIgnorePhoneScrollToggle())return scanStateSnapshot();
    let changed=false;
    (scanState.jobs||[]).forEach(job=>{if(job&&!job.collapsed){job.collapsed=true; changed=true;}});
    if(changed){scanState.lastCollapseReason=reason||'ui'; renderScanPreview();}
    return scanStateSnapshot();
  }
  function removeScanJob(index){
    const i=Number(index)||0;
    if(i>=0&&i<scanState.jobs.length){scanState.jobs.splice(i,1);}
    if(scanState.activeIndex>=scanState.jobs.length)scanState.activeIndex=Math.max(0,scanState.jobs.length-1);
    if(!scanState.jobs.length){scanState.decision=false; state.scanPanelOpen='plan';}
    renderScanPreview();
    render();
    return scanStateSnapshot();
  }
  function toggleScanJobCollapse(index){
```
