# KGG Source Chunk 055

- Source: `kgg-update/index.html`
- Lines: 23101-23520

```html
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
      .map(visibleRect)
      .filter(Boolean)
      .filter(r=>r.left>=rect.left-4&&r.right<=rect.right+4);
    const measuredLeftEdge=leftRects.length?Math.max(...leftRects.map(r=>r.right)):null;
    const cssLeft=gridFirstCol();
    const storedLeft=parseFloat(String(tabletLayoutState.leftCol||'').replace('px',''));
    const fallbackLeft=Number.isFinite(cssLeft)?cssLeft:(Number.isFinite(storedLeft)?storedLeft:Math.min(Math.max(rect.width*.42,360),660));
    const leftEdge=Number.isFinite(measuredLeftEdge)?measuredLeftEdge:rect.left+fallbackLeft;
    const rightRects=[$('rightPlanStack'),$('currentPlanBlock'),$('baseToggle'),$('recentToggle'),$('packageLayoutSlot')]
      .map(visibleRect)
      .filter(Boolean)
      .filter(r=>r.left>=leftEdge-12&&r.left<=rect.right+4);
    const rightEdge=rightRects.length?Math.min(...rightRects.map(r=>r.left)):Math.min(rect.right,rect.left+fallbackLeft+gap);
    const handleWidth=handle.getBoundingClientRect().width||58;
    const center=(rightEdge>leftEdge+2)?((leftEdge+rightEdge)/2):leftEdge+Math.max(0,gap/2);
    handle.style.left=Math.round(center-(handleWidth/2))+'px';
    handle.style.top=Math.round(rect.top+8)+'px';
    handle.style.height=Math.max(160,Math.round(rect.height-16))+'px';
  }
  function updateTabletLayoutAdaptiveClasses(){
    const app=document.querySelector('.app');
    const active=isTabletLayout()&&app&&document.body.classList.contains('tabletLayoutCustom');
    let left=0, rightSlot=0, recentW=0, planW=0;
    if(active){
      const rect=app.getBoundingClientRect();
      const fallback=Math.min(Math.max(rect.width*.42,360),660);
      const leftEl=$('bankArea')||$('inputWrap')||document.querySelector('.scanHub');
      left=leftEl?leftEl.getBoundingClientRect().width:(parseFloat(String(tabletLayoutState.leftCol||'').replace('px',''))||fallback);
      const slot=$('packageLayoutSlot')||$('packageToggle');
      rightSlot=slot?slot.getBoundingClientRect().width:0;
      recentW=$('recentToggle')?$('recentToggle').getBoundingClientRect().width:0;
      planW=$('currentPlanBlock')?$('currentPlanBlock').getBoundingClientRect().width:0;
    }
    document.body.classList.toggle('tabletLayoutLeftSlim',!!active&&left<320);
    document.body.classList.toggle('tabletLayoutLeftTiny',!!active&&left<190);
    document.body.classList.toggle('tabletLayoutRightSlim',!!active&&((rightSlot>0&&rightSlot<270)||(recentW>0&&recentW<250)||(planW>0&&planW<360)));
    document.body.classList.toggle('tabletLayoutRightTiny',!!active&&((rightSlot>0&&rightSlot<150)||(recentW>0&&recentW<135)));
    document.body.classList.toggle('tabletLayoutScaleHuge',!!active&&tabletLayoutState.scale>1.35);
  }
  function getTabletLayoutRect(el){
    if(!el)return null;
    const style=getComputedStyle(el);
    if(style.display==='none'||style.visibility==='hidden'||style.opacity==='0')return null;
    const rect=el.getBoundingClientRect();
    if(rect.width<2||rect.height<2)return null;
    return rect;
  }
  function tabletRectsCollide(a,b,gap){
    return !(a.right+gap<=b.left||b.right+gap<=a.left||a.bottom+gap<=b.top||b.bottom+gap<=a.top);
  }
  function updateTabletLayoutCollisionGuard(){
    const active=isTabletLayout()&&document.body.classList.contains('tabletLayoutCustom');
    if(!active){
      document.body.classList.remove('tabletLayoutCollisionTight');
      document.documentElement.style.setProperty('--kgg-tablet-collision-gap','14px');
      return;
    }
    const scale=Number(tabletLayoutState.scale)||1;
    const safetyGap=Math.max(10,Math.min(28,Math.round(12+(scale-1)*18)));
    document.documentElement.style.setProperty('--kgg-tablet-collision-gap',safetyGap+'px');
    const selectors=['.scanHub .scanBtn','.scanHub .scanMeta','.scanHub .adminConfigBtn','.scanHub .sharedBankBtn','#baseToggle','#inputWrap','#bankArea','#rightPlanStack','#recentToggle','#packageLayoutSlot'];
    const rects=selectors.flatMap(sel=>[...document.querySelectorAll(sel)]).map(getTabletLayoutRect).filter(Boolean);
    let collision=false;
    for(let i=0;i<rects.length&&!collision;i++){
      for(let j=i+1;j<rects.length;j++){
        if(tabletRectsCollide(rects[i],rects[j],safetyGap)){collision=true;break;}
      }
    }
    document.body.classList.toggle('tabletLayoutCollisionTight',collision);
  }
  function applyTabletLayoutSettings(){
    const tabletActive=isTabletLayout();
    document.body.classList.toggle('tabletLayoutUnlocked',!tabletLayoutState.locked);
    document.body.classList.toggle('tabletLayoutCustom',tabletActive);
    document.documentElement.style.setProperty('--kgg-tablet-ui-scale',String(tabletLayoutState.scale));
    if(tabletLayoutState.leftCol)document.documentElement.style.setProperty('--kgg-tablet-left-col',tabletLayoutState.leftCol);
    else document.documentElement.style.removeProperty('--kgg-tablet-left-col');
    const btn=$('tabletLayoutLockBtn'), value=$('tabletScaleValue'), splitValue=$('tabletSplitScaleValue');
    if(btn){
      btn.setAttribute('aria-pressed',tabletLayoutState.locked?'true':'false');
      btn.setAttribute('aria-label',tabletLayoutState.locked?'Layout fixiert':'Layout frei verschiebbar');
      const icon=btn.querySelector('.tabletLockIcon');
      const text=btn.querySelector('.tabletLockText');
      if(icon)icon.textContent=String.fromCodePoint(tabletLayoutState.locked?128274:128275);
      if(text)text.textContent=tabletLayoutState.locked?'Fix':'Frei';
    }
    const scaleLabel=Math.round(tabletLayoutState.scale*100)+'%';
    if(value)value.textContent=scaleLabel;
    if(splitValue)splitValue.textContent=scaleLabel;
    updateTabletLayoutAdaptiveClasses();
    requestAnimationFrame(()=>{updateTabletLayoutHandle();updateTabletLayoutCollisionGuard();});
  }
  function setTabletLayoutLocked(locked){
```
