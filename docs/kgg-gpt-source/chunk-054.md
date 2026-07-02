# KGG Source Chunk 054

- Source: `kgg-update/index.html`
- Lines: 22681-23100

```html
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
    if(shouldIgnorePhoneScrollToggle())return scanStateSnapshot();
    const job=scanState.jobs[Number(index)||0];
    if(job){job.collapsed=!job.collapsed; renderScanPreview();}
    return scanStateSnapshot();
  }
  function initScanAutoCollapseOnUiOpen(){
    if(window.__kggScanAutoCollapseBound)return;
    window.__kggScanAutoCollapseBound=true;
    const watchedIds=['editorModal','packageSaveModal','bankDeleteModal','shareModal','largePdfModal','longMediaConfirmModal','installPromptModal','adminSecretsModal','sharedBankModal','pdfPreviewModal','recentList','packageList','baseFields','bankContent'];
    const visible=function(el){
      if(!el)return false;
      if(el.classList.contains('open'))return true;
      if(el.id==='recentList'||el.id==='packageList'||el.id==='baseFields'||el.id==='bankContent')return !el.classList.contains('hidden');
      return false;
    };
    const previous=new Map();
    watchedIds.forEach(id=>{const el=$(id); if(el)previous.set(id,visible(el));});
    const check=function(id,el){
      if(shouldIgnorePhoneScrollToggle())return;
      const now=visible(el);
      const before=previous.get(id)||false;
      previous.set(id,now);
      if(now&&!before)collapseScanCards('auto_'+id);
    };
    const observer=new MutationObserver(records=>{
      records.forEach(record=>{const el=record.target; if(el&&el.id)check(el.id,el);});
    });
    watchedIds.forEach(id=>{
      const el=$(id);
      if(el)observer.observe(el,{attributes:true,attributeFilter:['class','style','open']});
    });
    document.addEventListener('click',ev=>{
      if(shouldIgnorePhoneScrollToggle())return;
      const target=ev.target&&ev.target.closest?ev.target.closest('button,.drawerBtn,.baseCard,.dbTitle,.modal,.sheet'):null;
      if(!target)return;
      if(target.closest&&target.closest('#scanPreview'))return;
      const opensOtherUi=target.id==='baseToggle'||target.id==='recentToggle'||target.id==='packageToggle'||target.id==='bankToggle'||target.id==='dbTitle'||target.id==='finishBtn'||target.closest('.modal');
      if(opensOtherUi)setTimeout(()=>collapseScanCards('click_'+(target.id||'ui')),0);
    },true);
  }
  async function processPaperJob(job){
    if(job.result&&job.type==='qr')return job.result;
    if(!job.pages.length)throw new Error(job.label+': keine Bilder.');
    const texts=[]; const raw=[]; const warnings=[];
    for(let i=0;i<job.pages.length;i++){
      const page=job.pages[i];
      if(!page.file){warnings.push('Bilddatei nicht mehr im Speicher: '+page.name); continue;}
      setScanStatus(job.label+': Seite '+(i+1)+' wird ausgelesen …');
      const result=await callGeminiPaperFallback(page.file);
      if(result.planText)texts.push(result.planText);
      raw.push(result.rawText||'');
      if(result.quality&&result.quality.warnings)warnings.push(...result.quality.warnings);
    }
    const planText=texts.join(', ').replace(/(?:,\s*){2,}/g,', ').trim();
    const quality=scanPaperQuality(planText,{raw});
    quality.warnings=[...new Set([...(quality.warnings||[]),...warnings])];
    quality.ok=!quality.warnings.length;
    job.result={type:'paper',planText,rawText:raw.join('\n---\n'),quality};
    job.status='ready';
    return job.result;
  }
  async function copyTextWithFallback(text,fieldId){
    const field=$(fieldId);
    let ok=false;
    try{if(navigator.clipboard&&window.isSecureContext){await navigator.clipboard.writeText(text);ok=true;}}catch(err){}
    if(!ok&&field){
      try{field.focus({preventScroll:true});field.select();field.setSelectionRange(0,field.value.length);ok=document.execCommand('copy');}catch(err){}
    }
    return ok;
  }
  function scanValueToString(value){
    if(value==null||value==='')return '';
    const n=Number(value);
    if(Number.isFinite(n))return String(Math.round(n*100)/100).replace('.',',');
    return String(value).trim();
  }
  function scanSetsFromNumberSequence(nums,source){
    const values=(nums||[]).map(Number).filter(Number.isFinite);
    const side=normalizeSideMode(source&&source.side||source&&source.side_mode||source&&source.laterality||source&&source.seite||'BI');
    const metricUnit=scanUnitLabel(source&&source.unit||source&&source.metricUnit||source&&source.metric_unit,(source&&source.measure)==='Sek.'?'Sek.':'Wdh');
    const loadUnit=scanUnitLabel(source&&source.weightUnit||source&&source.loadUnit||source&&source.weight_unit,/sek|zeit|time/i.test(metricUnit)?'keine':'kg');
    const isTime=/zeit|sek|sec|min|time/i.test(metricUnit)||/keine/i.test(loadUnit);
    const pains=scanFindPainValues(source||{});
    const sets=[];
    if(side==='LR'&&values.length>=12){
      for(let i=0;i<3;i++){
        const b=i*4;
        sets.push({
          li:{load:scanValueToString(values[b]),metric:scanValueToString(values[b+1])},
          re:{load:scanValueToString(values[b+2]),metric:scanValueToString(values[b+3])},
          pain:scanValueToString(pains[i]||values[12+i]||'')
        });
      }
      return sets;
    }
    if(isTime){
      for(let i=0;i<3;i++){
        const idx=values.length>=6?i*2+1:i;
        const metric=scanValueToString(values[idx]);
        if(metric)sets.push({metric,pain:scanValueToString(pains[i]||'')});
      }
      return sets;
    }
    if(values.length>=9){
      for(let i=0;i<3;i++){
        const b=i*3;
        sets.push({load:scanValueToString(values[b]),metric:scanValueToString(values[b+1]),pain:scanValueToString(values[b+2]||pains[i]||'')});
      }
      return sets;
    }
    if(values.length>=6){
      for(let i=0;i<3;i++){
        sets.push({load:scanValueToString(values[i*2]),metric:scanValueToString(values[i*2+1]),pain:scanValueToString(pains[i]||'')});
      }
      return sets;
    }
    return [];
  }
  function scanPlanExerciseFromNumbers(name,numbers,source){
    const cleanName=stripScanExerciseName(name||scanExerciseName(source));
```
