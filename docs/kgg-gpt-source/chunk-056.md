# KGG Source Chunk 056

- Source: `kgg-update/src` modular source
- Lines: 23521-23940

```html
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
    const scaleDisplay='Groesse '+scaleLabel;
    if(value)value.textContent=scaleDisplay;
    if(splitValue)splitValue.textContent=scaleDisplay;
    updateTabletLayoutAdaptiveClasses();
    requestAnimationFrame(()=>{updateTabletLayoutHandle();updateTabletLayoutCollisionGuard();});
  }
  function setTabletLayoutLocked(locked){
    tabletLayoutState.locked=!!locked;
    saveTabletLayoutSettings();
    applyTabletLayoutSettings();
  }
  function setTabletLayoutScale(next){
    tabletLayoutState.scale=clampTabletScale(next);
    saveTabletLayoutSettings();
    applyTabletLayoutSettings();
  }
  function adjustTabletLayoutScale(direction){
    if(tabletLayoutState.locked||!isTabletLayout())return;
    setTabletLayoutScale(tabletLayoutState.scale+(direction>0?.05:-.05));
  }
  function adjustTabletSplitLayoutScale(direction){
    if(!isTabletLayout())return;
    setTabletLayoutScale(tabletLayoutState.scale+(direction>0?.05:-.05));
  }
  function resetTabletLayoutDefaults(){
    tabletLayoutState.leftCol='';
    tabletLayoutState.scale=1;
    saveTabletLayoutSettings();
    applyTabletLayoutSettings();
  }
  function initTabletLayoutControls(){
    loadTabletLayoutSettings();
    const btn=$('tabletLayoutLockBtn'), minus=$('tabletScaleMinus'), plus=$('tabletScalePlus'), reset=$('tabletLayoutReset'), handle=$('tabletLayoutResizeHandle'), tools=$('tabletLayoutFreeTools'), splitMinus=$('tabletSplitScaleMinus'), splitPlus=$('tabletSplitScalePlus');
    if(btn)btn.onclick=()=>setTabletLayoutLocked(!tabletLayoutState.locked);
    if(minus)minus.onclick=()=>adjustTabletLayoutScale(-1);
    if(plus)plus.onclick=()=>adjustTabletLayoutScale(1);
    if(reset)reset.onclick=()=>resetTabletLayoutDefaults();
    if(splitMinus)splitMinus.onclick=ev=>{ev.preventDefault();ev.stopPropagation();adjustTabletSplitLayoutScale(-1);};
    if(splitPlus)splitPlus.onclick=ev=>{ev.preventDefault();ev.stopPropagation();adjustTabletSplitLayoutScale(1);};
    if(tools){
      tools.addEventListener('wheel',ev=>{
        if(tabletLayoutState.locked||!isTabletLayout())return;
        ev.preventDefault();
        adjustTabletLayoutScale(ev.deltaY<0?1:-1);
      },{passive:false});
      let scaleDragY=null;
      tools.addEventListener('pointerdown',ev=>{
        if(tabletLayoutState.locked||!isTabletLayout()||ev.target.closest('button'))return;
        scaleDragY=ev.clientY;
        try{tools.setPointerCapture(ev.pointerId);}catch(err){}
      });
      tools.addEventListener('pointermove',ev=>{
        if(scaleDragY===null||tabletLayoutState.locked)return;
        const dy=ev.clientY-scaleDragY;
        if(Math.abs(dy)<18)return;
        adjustTabletLayoutScale(dy<0?1:-1);
        scaleDragY=ev.clientY;
      });
      const endScaleDrag=()=>{scaleDragY=null;};
      tools.addEventListener('pointerup',endScaleDrag);
      tools.addEventListener('pointercancel',endScaleDrag);
    }
    if(handle){
      handle.addEventListener('pointerdown',ev=>{
        if(ev.target&&ev.target.closest&&ev.target.closest('.tabletSplitScaleControl'))return;
        if(tabletLayoutState.locked||!isTabletLayout())return;
        const app=document.querySelector('.app');
        if(!app)return;
        ev.preventDefault();
        tabletLayoutState.dragging=true;
        document.body.classList.add('tabletLayoutDragging');
        try{handle.setPointerCapture(ev.pointerId);}catch(err){}
        const move=moveEv=>{
          if(!tabletLayoutState.dragging)return;
          const rect=app.getBoundingClientRect();
          const min=24;
          const max=Math.max(min,rect.width-48);
          const gap=parseFloat(getComputedStyle(app).columnGap)||0;
          const next=Math.max(min,Math.min(max,moveEv.clientX-rect.left-(gap/2)));
          tabletLayoutState.leftCol=Math.round(next)+'px';
          document.documentElement.style.setProperty('--kgg-tablet-left-col',tabletLayoutState.leftCol);
          updateTabletLayoutAdaptiveClasses();
          updateTabletLayoutHandle();
          updateTabletLayoutCollisionGuard();
        };
        const up=()=>{
          tabletLayoutState.dragging=false;
          document.body.classList.remove('tabletLayoutDragging');
          saveTabletLayoutSettings();
          document.removeEventListener('pointermove',move);
          document.removeEventListener('pointerup',up);
          document.removeEventListener('pointercancel',up);
        };
        document.addEventListener('pointermove',move,{passive:true});
        document.addEventListener('pointerup',up,{once:true});
        document.addEventListener('pointercancel',up,{once:true});
      });
    }
    window.addEventListener('resize',()=>requestAnimationFrame(()=>{updateTabletLayoutAdaptiveClasses();updateTabletLayoutHandle();updateTabletLayoutCollisionGuard();}));
    window.addEventListener('orientationchange',()=>setTimeout(()=>{updateTabletLayoutAdaptiveClasses();updateTabletLayoutHandle();updateTabletLayoutCollisionGuard();},120));
    applyTabletLayoutSettings();
  }
  const tabletOverlayState={kind:null};
  function tabletPanelConfig(kind){
    if(kind==='base')return {kind:'base',panelId:'baseFields',anchorId:'baseToggle',preferred:'below',align:'left',minWidth:420,maxWidth:680};
    if(kind==='recent')return {kind:'recent',panelId:'recentList',anchorId:(document.body.classList.contains('tabletMenuOpen')&&$('tabletMenuRecentBtn'))?'tabletMenuRecentBtn':'recentToggle',preferred:document.body.classList.contains('tabletMenuOpen')?'below':'above',align:'left',minWidth:360,maxWidth:560};
    if(kind==='package')return {kind:'package',panelId:'packageList',anchorId:(document.body.classList.contains('tabletMenuOpen')&&$('tabletMenuPackagesBtn'))?'tabletMenuPackagesBtn':'packageToggle',preferred:document.body.classList.contains('tabletMenuOpen')?'below':'above',align:'left',minWidth:360,maxWidth:620};
    return null;
  }
  function clearTabletOverlayStyles(panel){
    if(!panel)return;
    ['--kgg-overlay-left','--kgg-overlay-top','--kgg-overlay-width','--kgg-overlay-max-height','--kgg-overlay-origin'].forEach(name=>panel.style.removeProperty(name));
  }
  function setTabletOverlayActiveFlag(){
    const active=!!(isTabletLayout()&&(
      ($('baseFields')&&!$('baseFields').classList.contains('hidden'))||
      ($('recentList')&&!$('recentList').classList.contains('hidden'))||
      ($('packageList')&&!$('packageList').classList.contains('hidden'))
    ));
    document.body.classList.toggle('kggTabletOverlayActive',active);
    if(!active)tabletOverlayState.kind=null;
    updateToggleCarets();
    setTabletAnchorActiveClasses();
  }
  function closeTabletFloatingPanelsExcept(except){
    const base=$('baseFields'), recent=$('recentList'), packages=$('packageList');
    if(base&&except!=='base'){base.classList.add('hidden');clearTabletOverlayStyles(base);}
    if(recent&&except!=='recent'){recent.classList.add('hidden');clearTabletOverlayStyles(recent);}
    if(packages&&except!=='package'){packages.classList.add('hidden');clearTabletOverlayStyles(packages);}
    if(!['base','recent','package'].includes(except||''))tabletOverlayState.kind=null;
    let needsRender=false;
    if(except!=='bank'&&state&&state.bankOpen){state.bankOpen=false; needsRender=true;}
    if(window.KGGScan&&typeof window.KGGScan.collapseAll==='function')window.KGGScan.collapseAll('tablet_overlay_'+(except||'none'));
    setTabletOverlayActiveFlag();
    return needsRender;
  }
  function clampNumber(value,min,max){return Math.max(min,Math.min(max,value));}
  function positionTabletAnchoredOverlay(kind){
    if(!isTabletLayout())return false;
    const cfg=tabletPanelConfig(kind);
    if(!cfg)return false;
    const panel=$(cfg.panelId), anchor=$(cfg.anchorId), app=document.querySelector('.app');
    if(!panel||!anchor||!app||panel.classList.contains('hidden'))return false;
    const appRect=app.getBoundingClientRect();
    const anchorRect=anchor.getBoundingClientRect();
    const vv=window.visualViewport||null;
    const viewTop=vv?vv.offsetTop:0;
    const viewHeight=vv?vv.height:window.innerHeight;
    const viewBottom=viewTop+viewHeight;
    const margin=12;
    const availableWidth=Math.max(280,appRect.width-(margin*2));
    const minW=Math.min(cfg.minWidth||360,availableWidth);
    const maxW=Math.min(cfg.maxWidth||620,availableWidth);
    let width=clampNumber(Math.max(anchorRect.width,minW),minW,maxW);
    let left=(cfg.align==='right')?(anchorRect.right-width):anchorRect.left;
    left=clampNumber(left,appRect.left+margin,appRect.right-width-margin);

    panel.style.setProperty('--kgg-overlay-width',Math.round(width)+'px');
    panel.style.setProperty('--kgg-overlay-left',Math.round(left)+'px');
    panel.style.setProperty('--kgg-overlay-max-height','min(72vh,520px)');

    const measured=panel.getBoundingClientRect();
    const wantedHeight=Math.max(160,Math.min(measured.height||panel.scrollHeight||320,Math.min(520,viewHeight-(margin*2))));
    const belowTop=anchorRect.bottom+8;
    const aboveTop=anchorRect.top-wantedHeight-8;
    const enoughBelow=(belowTop+wantedHeight)<=Math.min(viewBottom-margin,appRect.bottom-margin);
    const enoughAbove=aboveTop>=Math.max(viewTop+margin,appRect.top+margin);
    let direction=cfg.preferred||'below';
    if(direction==='below'&&!enoughBelow&&enoughAbove)direction='above';
    if(direction==='above'&&!enoughAbove&&enoughBelow)direction='below';
    if(!enoughBelow&&!enoughAbove)direction=((anchorRect.top-appRect.top)>(appRect.bottom-anchorRect.bottom))?'above':'below';
    let top;
    let maxHeight;
    if(direction==='above'){
      maxHeight=Math.max(160,Math.min(520,anchorRect.top-Math.max(viewTop+margin,appRect.top+margin)-8));
      top=Math.max(viewTop+margin,anchorRect.top-Math.min(wantedHeight,maxHeight)-8);
    }else{
      top=belowTop;
      maxHeight=Math.max(160,Math.min(520,Math.min(viewBottom-margin,appRect.bottom-margin)-top));
    }
    top=clampNumber(top,viewTop+margin,Math.max(viewTop+margin,viewBottom-margin-120));
    const originX=clampNumber((anchorRect.left+anchorRect.width/2)-left,24,width-24);
    panel.style.setProperty('--kgg-overlay-top',Math.round(top)+'px');
    panel.style.setProperty('--kgg-overlay-max-height',Math.round(maxHeight)+'px');
    panel.style.setProperty('--kgg-overlay-origin',Math.round(originX)+'px '+(direction==='above'?'bottom':'top'));
    tabletOverlayState.kind=kind;
    document.body.classList.add('kggTabletOverlayActive');
    return true;
  }
  function openTabletAnchoredPanel(kind){
    if(!isTabletLayout())return false;
    const cfg=tabletPanelConfig(kind);
    if(!cfg)return false;
    const needsRender=closeTabletFloatingPanelsExcept(kind);
    if(needsRender)render();
    const panel=$(cfg.panelId);
    if(!panel)return false;
    panel.classList.remove('hidden');
    tabletOverlayState.kind=kind;
    if(typeof requestAnimationFrame==='function')requestAnimationFrame(()=>positionTabletAnchoredOverlay(kind));
    else setTimeout(()=>positionTabletAnchoredOverlay(kind),0);
    setTabletOverlayActiveFlag();
    return true;
  }
  function closeTabletAnchoredPanel(kind){
    const cfg=tabletPanelConfig(kind);
    const panel=cfg&&$(cfg.panelId);
    if(panel){panel.classList.add('hidden');clearTabletOverlayStyles(panel);}
    if(tabletOverlayState.kind===kind)tabletOverlayState.kind=null;
    setTabletOverlayActiveFlag();
    updateToggleCarets();
    setTabletAnchorActiveClasses();
  }
  function setTabletLayoutEditMode(open){
    const next=!!open&&isTabletLayout();
    document.body.classList.toggle('tabletLayoutEditMode',next);
    const btn=$('tabletMenuLayoutBtn');
    const panel=$('tabletMenuLayoutPanel');
    if(btn)btn.setAttribute('aria-expanded',String(next));
    if(panel)panel.hidden=!next;
```
