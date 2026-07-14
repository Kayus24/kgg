# KGG Source Chunk 055

- Source: `kgg-update/src` modular source
- Lines: 23101-23520

```html
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
    if(!cleanName)return null;
    const metricUnit=scanUnitLabel(source&&source.unit||source&&source.metricUnit||source&&source.metric_unit,(source&&source.measure)==='Sek.'?'Sek.':'Wdh');
    const loadUnit=scanUnitLabel(source&&source.weightUnit||source&&source.loadUnit||source&&source.weight_unit,/sek|zeit|time/i.test(metricUnit)?'keine':'kg');
    const side=normalizeSideMode(source&&source.side||source&&source.side_mode||source&&source.laterality||source&&source.seite||'BI');
    const scanSets=scanSetsFromNumberSequence(numbers, {...(source||{}),unit:metricUnit,metricUnit,weightUnit:loadUnit,loadUnit,side});
    const first=scanSets[0]||{};
    const exact=exactBankExercise(cleanName);
    const id=makeLocalId();
    const isTime=/zeit|sek|sec|min|time/i.test(metricUnit)||/keine/i.test(loadUnit);
    return ensureUiExerciseShape({
      ...(exact||{}),
      id,localId:id,sourceId:exact?exact.id:'',bankId:exact?exact.id:'',
      name:exact?exact.name:cleanName,
      sets:3,side,unit:isTime?'Zeit':'Wdh',metricUnit:isTime?'Sek.':'Wdh',weightUnit:isTime?'keine':loadUnit,loadUnit:isTime?'keine':loadUnit,measure:isTime?'zeit':'wdh',
      startLoad:(first&&first.load)||'',
      startMetric:(first&&first.metric)||'',
      scanSets,scanImported:true,scanSource:'Scan: kg/Wdh übernommen',
      rawText:scanSets.length?kggScanPlanExerciseToText(cleanName,scanSets,{metricUnit:isTime?'Sek.':'Wdh',loadUnit:isTime?'keine':loadUnit,side}):(source&&source.rawText||cleanName),
      pendingNew:!exact,needsReview:!exact
    });
  }
  function kggScanPlanExerciseToText(name,sets,source){
    const metricUnit=source&&source.metricUnit||'Wdh';
    const loadUnit=source&&source.loadUnit||'kg';
    const isTime=/zeit|sek|sec|min|time/i.test(metricUnit)||/keine/i.test(loadUnit);
    const lines=[name];
    (sets||[]).slice(0,3).forEach((set,i)=>{
      if(set&&set.li||set&&set.re){
        const li=set.li||{}, re=set.re||{};
        lines.push('Satz '+(i+1)+':');
        lines.push('  Li: '+(li.metric||'')+' '+metricUnit+(li.load?' @ '+li.load+' '+loadUnit:''));
        lines.push('  Re: '+(re.metric||'')+' '+metricUnit+(re.load?' @ '+re.load+' '+loadUnit:''));
        if(set.pain)lines.push('  Schmerz: '+set.pain+'/10');
      }else if(isTime){
        lines.push('Satz '+(i+1)+': '+(set&&set.metric||'')+' '+metricUnit+(set&&set.pain?' · Schmerz: '+set.pain+'/10':''));
      }else{
        lines.push('Satz '+(i+1)+': '+(set&&set.metric||'')+' '+metricUnit+(set&&set.load?' @ '+set.load+' '+loadUnit:'')+(set&&set.pain?' · Schmerz: '+set.pain+'/10':''));
      }
    });
    return lines.join('\n');
  }
  function scanPlanExerciseFromPayloadItem(item,fallbackBox){
    let source=item;
    if(Array.isArray(item)){try{source=expandKggH2Exercise(item);}catch(err){source={name:item[0]||''};}}
    const name=scanExerciseName(source)||fallbackBox&&fallbackBox.name||'';
    const numbers=scanFindNumberSequence(source);
    return scanPlanExerciseFromNumbers(name,numbers,{...(source||{}),measure:fallbackBox&&fallbackBox.measure});
  }
  function scanPlanExercisesFromDocText(text){
    const lines=String(text||'').split(/\n+/).map(l=>l.trim()).filter(Boolean);
    const out=[];
    let current=null;
    lines.forEach(line=>{
      if(/^Satz\s+\d+\s*:/i.test(line)&&current){
        const m=line.match(/^Satz\s+(\d+)\s*:\s*([\d,.]+)?\s*(wdh|wh|sek\.?|sec|s)?(?:\s*@\s*([\d,.]+)\s*(kg|hub|stufe|watt|bar)?)?/i);
        if(m){
          const metric=scanValueToString(m[2]||'');
          const load=scanValueToString(m[4]||'');
          const metricUnit=/sek|sec|\bs\b/i.test(m[3]||'')?'Sek.':'Wdh';
          current.metricUnit=metricUnit;
          if(metricUnit==='Sek.')current.weightUnit='keine';
          current.scanSets=current.scanSets||[];
          current.scanSets[Number(m[1])-1]={metric,load};
        }
      }else if(!/^Typ:|^Prüfen:/i.test(line)){
        if(current)out.push(current);
        current={name:stripScanExerciseName(line),scanSets:[],sets:3,side:'BI',metricUnit:'Wdh',weightUnit:'kg'};
      }
    });
    if(current)out.push(current);
    return out.filter(ex=>ex.name).map(ex=>{
      const isTime=/Sek\./i.test(ex.metricUnit)||ex.weightUnit==='keine';
      const first=(ex.scanSets||[])[0]||{};
      return scanPlanExerciseFromNumbers(ex.name,(ex.scanSets||[]).flatMap(s=>isTime?[0,s&&s.metric||'']:[s&&s.load||'',s&&s.metric||'']),{unit:isTime?'Sek.':'Wdh',metricUnit:isTime?'Sek.':'Wdh',weightUnit:isTime?'keine':'kg',loadUnit:isTime?'keine':'kg'});
    }).filter(Boolean);
  }
  function scanPlanExercisesFromResult(result){
    if(!result)return [];
    if(Array.isArray(result.groups)&&String(result.layout||'')===KGG_CURRENT_LAYOUT_ID){
      return KGG_CURRENT_LAYOUT_BOXES.map((box,i)=>scanPlanExerciseFromNumbers(box.name,result.groups[i]||[],{measure:box.measure,unit:box.measure,metricUnit:box.measure,weightUnit:box.measure==='Sek.'?'keine':'kg',loadUnit:box.measure==='Sek.'?'keine':'kg'})).filter(Boolean);
    }
    const payloadExercises=scanPayloadExercises(result.json||result);
    if(payloadExercises.length)return payloadExercises.map(scanPlanExerciseFromPayloadItem).filter(Boolean);
    const text=result.planText||result.copyText||result.rawText||'';
    return scanPlanExercisesFromDocText(text);
  }
  function appendScanExercisesToCurrentPlan(exercises,reason){
    const clean=(exercises||[]).filter(ex=>ex&&ex.name);
    if(!clean.length){setScanStatus('Kein Übungstext zum Übernehmen.');return false;}
    const input=$('exerciseInput');
    if(input&&input.value.trim())syncPlanFromTextInput('scan_preserve_existing_text_before_apply');
    state.plan=[...(state.plan||[]),...clean.map(ensureUiExerciseShape)];
    state.bankOpen=false;
    state.liveDraftId=null;
    state.scanPanelOpen='plan';
    syncStatePlanToStore(reason||'scan_apply_structured_exercises');
    syncTextInputFromPlan(reason||'scan_apply_structured_exercises_text');
    save();
    render();
    setScanStatus('Scan-Ergebnis mit kg/Wdh übernommen.');
    return true;
  }
  function applyScanResultToCurrentPlan(result,reason){
    const structured=scanPlanExercisesFromResult(result);
    if(structured.length)return appendScanExercisesToCurrentPlan(structured,reason||'scan_apply_result_structured');
    const text=scanResultToApplyText(result)||scanResultToPlanText(result)||'';
    const fromText=scanPlanExercisesFromDocText(text);
    if(fromText.length)return appendScanExercisesToCurrentPlan(fromText,reason||'scan_apply_result_text_structured');
    return applyScanTextToCurrentPlan(text,reason||'scan_apply_result_fallback');
  }
  function applyScanTextToCurrentPlan(text,reason){
    const clean=String(text||'').replace(/^Typ:.*$/gm,'').replace(/^Prüfen:.*$/gm,'').replace(/\n+/g,', ').replace(/(?:,\s*){2,}/g,', ').trim();
    if(!clean){setScanStatus('Kein Übungstext zum Übernehmen.');return false;}
    const input=$('exerciseInput');
    if(!input)return false;
    const existing=String(input.value||'').trim();
    input.value=existing?withTrailingExerciseComma(existing.replace(/,+$/,'')+', '+clean):withTrailingExerciseComma(clean);
    syncPlanFromTextInput(reason||'scan_v319_apply_result_preserve_text');
    state.bankOpen=false;
    state.scanPanelOpen='plan';
    save();
    render();
    setScanStatus('Scan-Ergebnis übernommen.');
    return true;
  }
  function updateScanQueueInfo(){renderScanPreview();}
  function showAfterPhotoPrompt(){scanState.decision=true;renderScanPreview();}
  window.KGGScanBridge={
    getStatus:()=>({singleEngine:true,hasLocalKey:!!currentLocalGeminiKey(),jobs:scanStateSnapshot().jobs.length}),
    redactCanvasForExternalOcr:redactScanCanvasForExternalOcr,
    createReadingCanvas:createScanReadingCanvas,
    qualityCheck:scanPaperQuality,
    scanResultToPlanText,
    applyText:(text)=>applyScanTextToCurrentPlan(text,'scan_bridge_apply_text')
  };
  function notifyNativeScanPickerMode(kind){
    const normalized=normalizeScanInputKind(kind);
    try{
      if(window.KGGNativeCamera&&typeof window.KGGNativeCamera.setNextPickerMode==='function'){
        window.KGGNativeCamera.setNextPickerMode(normalized);
        return;
      }
      if(window.KGGAndroidApp&&typeof window.KGGAndroidApp.setNextFileChooserMode==='function'){
        window.KGGAndroidApp.setNextFileChooserMode(normalized);
      }
    }catch(err){
      console.warn('Native Kamera-Bridge nicht verfuegbar:',err);
    }
  }
  window.KGGScan={
    pick(kind){
        const normalized=rememberScanInputKind(kind||lastScanInputKind());
        notifyNativeScanPickerMode(normalized);
        const input=normalized==='camera'?$('fileInput'):$('filePickerInput');
        if(input){
          try{input.value='';}catch(_e){}
          if(normalized==='camera'){
            input.accept='image/*';
            input.setAttribute('capture','environment');
            input.removeAttribute('multiple');
          }else{
            input.accept='image/*,.jpg,.jpeg,.png,.webp';
            input.removeAttribute('capture');
            input.setAttribute('multiple','multiple');
          }
          input.click();
        }
      },
    async handleInput(input,kind){
      const normalizedKind=rememberScanInputKind(kind||lastScanInputKind());
      const files=Array.from(input&&input.files||[]).filter(Boolean);
      try{if(input)input.value='';}catch(err){}
      if(!files.length)return scanStateSnapshot();
      scanState.busy=true;
      scanState.lastError='';
      scanState.decision=false;
      setScanStatus(files.length===1?'Prüfe: '+(files[0].name||'Kamera-Foto'):files.length+' Bilder werden vorbereitet …');
      renderScanPreview();
      try{
        let syncCodeCount=0;
        let acceptedCount=0;
        for(const file of files){
          const accepted=await scanAcceptFile(file,normalizedKind);
          if(accepted&&(accepted.type==='syncInvite'||accepted.type==='syncBundle'))syncCodeCount++;
          else if(accepted)acceptedCount++;
        }
        if(syncCodeCount&&!acceptedCount){
          scanState.decision=false;
          state.scanPanelOpen='plan';
          save();
          render();
          return scanStateSnapshot();
        }
        scanState.decision=true;
        state.scanPanelOpen='scanned';
        save();
        render();
        setScanStatus('Foto hinzugefügt. Bitte entscheiden.');
      }catch(err){
        scanState.lastError='Scan fehlgeschlagen: '+(err&&err.message||err);
        setScanStatus(scanState.lastError);
      }finally{
        scanState.busy=false;
        renderScanPreview();
      }
      return scanStateSnapshot();
    },
    async start(){
      scanState.decision=false;
      scanState.busy=true;
      scanState.lastError='';
      renderScanPreview();
      try{
        const jobs=scanState.jobs.filter(job=>job.pages.length||job.result);
```
