# KGG Source Chunk 055

- Source: `kgg-update/index.html`
- Lines: 23101-23520

```html
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
        if(!jobs.length)throw new Error('Bitte zuerst mindestens ein Foto hinzufügen.');
        for(const job of jobs){
          if(!job.result||job.type==='paper')await processPaperJob(job);
        }
        state.scanPanelOpen='scanned';
        save();
        render();
        setScanStatus('Scan fertig: '+jobs.length+' Plan/Pläne.');
      }catch(err){
        scanState.lastError='Scan fehlgeschlagen: '+(err&&err.message||err);
        setScanStatus(scanState.lastError);
      }finally{
        scanState.busy=false;
        renderScanPreview();
      }
      return scanStateSnapshot();
    },
    repeatSource(mode){
      const nextMode=mode==='plan'?'plan':'page';
      this.setNext(nextMode);
      return this.pick(lastScanInputKind());
    },
    setNext(mode){
      scanState.next=mode==='plan'?'plan':'page';
      if(mode==='plan')scanState.activeIndex=scanState.jobs.length;
      scanState.decision=false;
      setScanStatus(scanState.next==='plan'?'Nächstes Foto wird neuer Plan.':'Nächstes Foto wird weitere Seite.');
      renderScanPreview();
      return scanStateSnapshot();
    },
    removePage(jobIndex,pageIndex){
      const job=scanState.jobs[Number(jobIndex)||0];
      if(job&&job.pages){job.pages.splice(Number(pageIndex)||0,1); if(job.type==='paper')job.result=null; if(!job.pages.length&&!job.result)scanState.jobs.splice(Number(jobIndex)||0,1);}
      if(scanState.activeIndex>=scanState.jobs.length)scanState.activeIndex=Math.max(0,scanState.jobs.length-1);
      renderScanPreview();
      return scanStateSnapshot();
    },
    setActive(index){
      scanState.activeIndex=Math.max(0,Math.min(Number(index)||0,scanState.jobs.length-1));
      scanState.next='page';
      setScanStatus((scanState.jobs[scanState.activeIndex]&&scanState.jobs[scanState.activeIndex].label||'Plan')+' aktiv.');
      renderScanPreview();
      return scanStateSnapshot();
    },
    setShort(index,value){
      const job=scanState.jobs[Number(index)||0];
      if(job)job.short=String(value||'').trim();
      const field=$('kggScanCopyField'+index);
      if(field&&job)field.value=scanResultToCopyText(job)||field.value;
      return scanStateSnapshot();
    },
    toggleCollapse(index){return toggleScanJobCollapse(index);},
    removeJob(index){return removeScanJob(index);},
    collapseAll(reason){return collapseScanCards(reason);},
    closeDecision(){scanState.decision=false;renderScanPreview();return scanStateSnapshot();},
    async copyResult(index){
      const job=scanState.jobs[Number(index)||0];
      if(!job)return false;
      const text=scanResultToCopyText(job);
      const fieldId=$('kggScanCopyField'+index)?'kggScanCopyField'+index:'kggScanInboxField'+index;
      const ok=await copyTextWithFallback(text,fieldId);
      setScanStatus(ok?'Kopiert.':'Text markiert - bitte manuell kopieren.');
      return ok;
    },
    applyResult(index){
      const job=scanState.jobs[Number(index)||0];
      if(!job)return false;
      const ok=applyScanResultToCurrentPlan(job.result,'scan_v319_continue_edit_job_'+index); if(ok){state.scanPanelOpen='plan'; save(); render();} return ok;
    },
    getState:scanStateSnapshot
  };

  /* v316 Tablet Anchor Overlay Manager: ein Nebenfenster aktiv, aber am jeweiligen Button verankert. */
  const tabletLayoutKeys={
    locked:'kgg_tablet_layout_locked',
    left:'kgg_tablet_left_col_width',
    scale:'kgg_tablet_ui_scale'
  };
  const tabletLayoutState={locked:true,leftCol:'',scale:1,dragging:false};
  function clampTabletScale(value){const n=Number(value)||1; return Math.max(.01,Math.min(2,n));}
  function loadTabletLayoutSettings(){
    try{
      tabletLayoutState.locked=localStorage.getItem(tabletLayoutKeys.locked)!=='false';
      tabletLayoutState.leftCol=localStorage.getItem(tabletLayoutKeys.left)||'';
      tabletLayoutState.scale=clampTabletScale(localStorage.getItem(tabletLayoutKeys.scale)||1);
    }catch(err){tabletLayoutState.locked=true;tabletLayoutState.leftCol='';tabletLayoutState.scale=1;}
  }
  function saveTabletLayoutSettings(){
    try{
      localStorage.setItem(tabletLayoutKeys.locked,tabletLayoutState.locked?'true':'false');
      if(tabletLayoutState.leftCol)localStorage.setItem(tabletLayoutKeys.left,tabletLayoutState.leftCol); else localStorage.removeItem(tabletLayoutKeys.left);
      localStorage.setItem(tabletLayoutKeys.scale,String(tabletLayoutState.scale));
    }catch(err){}
  }
  function updateTabletLayoutHandle(){
    const handle=$('tabletLayoutResizeHandle'), app=document.querySelector('.app');
    if(!handle||!app||!isTabletLayout()){return;}
    const rect=app.getBoundingClientRect();
    const appStyle=getComputedStyle(app);
    const gap=parseFloat(appStyle.columnGap)||0;
    const visibleRect=el=>{
      if(!el)return null;
      const style=getComputedStyle(el);
      if(style.display==='none'||style.visibility==='hidden'||style.opacity==='0')return null;
      const r=el.getBoundingClientRect();
      return (r.width>2&&r.height>2)?r:null;
    };
    const gridFirstCol=()=>{
      const first=String(appStyle.gridTemplateColumns||'').trim().split(/\s+/)[0]||'';
      const px=parseFloat(first);
      return Number.isFinite(px)&&px>2?px:null;
    };
    const leftRects=[$('bankArea'),$('inputWrap'),$('scanHub'),document.querySelector('.scanHub')]
```
