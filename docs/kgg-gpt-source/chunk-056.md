# KGG Source Chunk 056

- Source: `kgg-update/index.html`
- Lines: 23521-23940

```html
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
    if(next){closeTabletPackageOverlay(false);closeTabletFloatingPanelsExcept('layout');}
    requestAnimationFrame(()=>{updateTabletLayoutHandle();updateTabletLayoutCollisionGuard();});
  }
  function toggleTabletLayoutEditMode(){setTabletLayoutEditMode(!document.body.classList.contains('tabletLayoutEditMode'));}
  function closeTabletPackageOverlay(closeMenu){
    document.body.classList.remove('tabletPackageOverlayOpen');
    const overlay=$('tabletPackageOverlay'), shade=$('tabletPackageShade');
    if(overlay){
      overlay.setAttribute('aria-hidden','true');
      overlay.style.removeProperty('transform');
      overlay.style.removeProperty('visibility');
      overlay.style.removeProperty('transition');
    }
    if(shade){shade.hidden=true;shade.setAttribute('aria-hidden','true');}
    const btn=$('tabletMenuPackagesBtn');
    if(btn)btn.setAttribute('aria-expanded','false');
    if(closeMenu)setTabletSideMenuOpen(false);
  }
  function openTabletPackageOverlay(){
    if(!isTabletLayout())return false;
    setTabletLayoutEditMode(false);
    closeTabletFloatingPanelsExcept('packageOverlay');
    document.body.classList.add('tabletPackageOverlayOpen');
    const overlay=$('tabletPackageOverlay'), shade=$('tabletPackageShade'), btn=$('tabletMenuPackagesBtn');
    if(shade){shade.hidden=false;shade.setAttribute('aria-hidden','false');}
    if(overlay){
      overlay.setAttribute('aria-hidden','false');
      overlay.style.setProperty('transition','none','important');
      overlay.style.setProperty('transform','translate3d(0,0,0)','important');
      overlay.style.setProperty('visibility','visible','important');
    }
    if(btn)btn.setAttribute('aria-expanded','true');
    setTabletSideMenuOpen(true);
    renderTabletPackageOverlay();
    setTimeout(()=>{const input=$('tabletPackageSearch'); if(input)input.focus();},40);
    return true;
  }
  function toggleTabletPackageOverlay(){
    if(document.body.classList.contains('tabletPackageOverlayOpen')){closeTabletPackageOverlay(false);return true;}
    return openTabletPackageOverlay();
  }
  const phoneFloatingDrawerState={kind:null};
  function ensurePhoneDrawerBackdrop(){
    let backdrop=$('phoneDrawerBackdrop');
    if(!backdrop){
      backdrop=document.createElement('div');
      backdrop.id='phoneDrawerBackdrop';
      backdrop.className='kggPhoneDrawerBackdrop';
      backdrop.setAttribute('aria-hidden','true');
      backdrop.addEventListener('click',()=>closePhoneFloatingDrawer());
      document.body.appendChild(backdrop);
    }
    return backdrop;
  }
  function closePhoneFloatingDrawer(){
    const recent=$('recentList'), packages=$('packageList'), recentBtn=$('recentToggle'), packageBtn=$('packageToggle');
    if(recent)recent.classList.add('hidden');
    if(packages)packages.classList.add('hidden');
    if(recentBtn)recentBtn.classList.remove('phoneButtonFloat');
    if(packageBtn)packageBtn.classList.remove('phoneButtonFloat');
    document.body.classList.remove('kggPhoneDrawerOpen');
    phoneFloatingDrawerState.kind=null;
    setTabletOverlayActiveFlag();
  }
  function openPhoneFloatingDrawer(kind){
    if(!isPhoneLayout())return false;
    if(shouldIgnorePhoneScrollToggle())return false;
    const recent=$('recentList'), packages=$('packageList'), recentBtn=$('recentToggle'), packageBtn=$('packageToggle');
    const target=kind==='recent'?recent:packages;
    const targetBtn=kind==='recent'?recentBtn:packageBtn;
    const other=kind==='recent'?packages:recent;
    const otherBtn=kind==='recent'?packageBtn:recentBtn;
    if(!target||!targetBtn)return false;
    if(phoneFloatingDrawerState.kind===kind&&!target.classList.contains('hidden')){
      closePhoneFloatingDrawer();
      return true;
    }
    ensurePhoneDrawerBackdrop();
    if(other)other.classList.add('hidden');
    if(otherBtn)otherBtn.classList.remove('phoneButtonFloat');
    target.classList.remove('hidden');
    targetBtn.classList.add('phoneButtonFloat');
    document.body.classList.add('kggPhoneDrawerOpen');
    phoneFloatingDrawerState.kind=kind;
    setTabletOverlayActiveFlag();
    return true;
  }
  function openTabletExclusivePanel(kind){
    if(!isTabletLayout())return false;
    if(kind==='package')return openTabletPackageOverlay();
    if(['base','recent'].includes(kind))return openTabletAnchoredPanel(kind);
    const needsRender=closeTabletFloatingPanelsExcept(kind);
    if(needsRender)render();
    return true;
  }
  function repositionTabletOverlay(){
    if(!isTabletLayout())return;
    if(tabletOverlayState.kind)positionTabletAnchoredOverlay(tabletOverlayState.kind);
  }
  function setTabletSideMenuOpen(open){
    const next=!!open&&isTabletLayout();
    document.body.classList.toggle('tabletMenuOpen',next);
    const btn=$('tabletMenuBtn');
    if(btn){
      btn.setAttribute('aria-expanded',String(next));
      btn.setAttribute('aria-label',next?'Tablet-Menue schliessen':'Tablet-Menue oeffnen');
    }
    const menu=$('tabletSideMenu');
    if(menu)menu.setAttribute('aria-hidden',String(!next));
    const backdrop=$('tabletSideBackdrop');
    if(backdrop)backdrop.setAttribute('aria-hidden',String(!next));
    if(next)closeTabletFloatingPanelsExcept('menu');
    else{closeTabletPackageOverlay(false); if(document.body.classList.contains('tabletLayoutEditMode'))setTabletLayoutEditMode(false);}
    requestAnimationFrame(()=>{updateTabletLayoutHandle();updateTabletLayoutCollisionGuard();});
    setTimeout(()=>{updateTabletLayoutHandle();updateTabletLayoutCollisionGuard();},260);
    return next;
  }
  window.addEventListener('resize',()=>{setTimeout(repositionTabletOverlay,30); setTimeout(syncScannedPlansMobileDock,30); setTimeout(()=>{if(!isTabletLayout())setTabletSideMenuOpen(false);},30);});
  window.addEventListener('orientationchange',()=>setTimeout(repositionTabletOverlay,120));
  if(window.visualViewport){
    window.visualViewport.addEventListener('resize',()=>{setTimeout(repositionTabletOverlay,30); setTimeout(syncScannedPlansMobileDock,30);});
    window.visualViewport.addEventListener('scroll',()=>setTimeout(repositionTabletOverlay,30));
  }
  document.addEventListener('pointerdown',ev=>{
    if(!isTabletLayout()||!tabletOverlayState.kind)return;
    const cfg=tabletPanelConfig(tabletOverlayState.kind);
    if(!cfg)return;
    const panel=$(cfg.panelId), anchor=$(cfg.anchorId);
    const target=ev.target;
    if(panel&&panel.contains(target))return;
    if(anchor&&anchor.contains(target))return;
    closeTabletAnchoredPanel(tabletOverlayState.kind);
  },true);
  document.addEventListener('keydown',ev=>{
    if(ev.key!=='Escape'||!isTabletLayout())return;
    if(document.body.classList.contains('tabletPackageOverlayOpen')){closeTabletPackageOverlay(false);return;}
    if(tabletOverlayState.kind)closeTabletAnchoredPanel(tabletOverlayState.kind);
  });

  initScanAutoCollapseOnUiOpen();
  if(renderPatientHashView())return;
  $('visionBtn').onclick=()=>setLargePdfMode(!state.largePdfMode);
  $('exerciseInput').addEventListener('input',()=>upsertLiveExerciseFromText()); $('exerciseInput').addEventListener('focus',()=>render()); $('clearInput').onclick=()=>{clearInputAndRemoveLiveTextExercises();};
  $('bankToggle').onclick=ev=>{if(guardPhoneScrollToggle(ev))return; const opening=!state.bankOpen; if(opening)openTabletExclusivePanel('bank'); toggleBankOpenFromUi(); setTabletOverlayActiveFlag();};
  $('dbTitle').onclick=ev=>{if(guardPhoneScrollToggle(ev))return; const opening=!state.bankOpen; if(opening)openTabletExclusivePanel('bank'); state.bankOpen=!state.bankOpen; render(); setTabletOverlayActiveFlag();};
  $('dbTitle').addEventListener('keydown',ev=>{if(ev.key==='Enter'||ev.key===' '){ev.preventDefault();if(guardPhoneScrollToggle(ev))return; const opening=!state.bankOpen; if(opening)openTabletExclusivePanel('bank'); state.bankOpen=!state.bankOpen; render(); setTabletOverlayActiveFlag();}});
  $('finishBtn').onclick=()=>{closeTabletFloatingPanelsExcept('modal'); openFinishModal();};
  $('baseToggle').onclick=ev=>{if(guardPhoneScrollToggle(ev))return; const base=$('baseFields'); const opening=base.classList.contains('hidden'); if(isTabletLayout()){if(opening)openTabletAnchoredPanel('base'); else closeTabletAnchoredPanel('base');}else{base.classList.toggle('hidden',!opening); setTabletOverlayActiveFlag();}};
  $('recentToggle').onclick=ev=>{if(guardPhoneScrollToggle(ev))return; const recent=$('recentList'); const opening=recent.classList.contains('hidden'); if(isTabletLayout()){if(opening)openTabletAnchoredPanel('recent'); else closeTabletAnchoredPanel('recent');}else{openPhoneFloatingDrawer('recent');}};
  $('packageToggle').onclick=ev=>{if(guardPhoneScrollToggle(ev))return; if(isTabletLayout())toggleTabletPackageOverlay(); else openPhoneFloatingDrawer('package');};
  $('exportBtn').onclick=exportData; $('pdfBtn').onclick=finishWithPdf; $('patientBtn').onclick=finishWithPatientApp; $('closeShare').onclick=closeFinishModal; $('copyShare').onclick=()=>navigator.clipboard&&navigator.clipboard.writeText($('shareText').value); $('patientName').addEventListener('input',()=>{state.patient.name=$('patientName').value;syncStatePlanToStore('ui_patient_name_input');save();render();}); $('planDate').addEventListener('input',()=>{state.patient.date=$('planDate').value;save();syncStatePlanToStore('ui_patient_date_input');}); $('therapistName').addEventListener('input',()=>{state.patient.therapist=$('therapistName').value;save();syncStatePlanToStore('ui_patient_therapist_input');}); $('planNotes').addEventListener('input',()=>{state.patient.notes=$('planNotes').value;save();syncStatePlanToStore('ui_patient_notes_input');}); $('scanBtn').onclick=()=>window.KGGScan.pick('camera'); $('filePickBtn').onclick=()=>window.KGGScan.pick('file'); $('filePickBtn').addEventListener('keydown',ev=>{if(ev.key==='Enter'||ev.key===' '){ev.preventDefault();window.KGGScan.pick('file');}}); $('fileInput').onchange=ev=>window.KGGScan.handleInput(ev.target,'camera'); $('filePickerInput').onchange=ev=>window.KGGScan.handleInput(ev.target,'file'); $('closeEditor').onclick=closeEditor; $('saveExercise').onclick=saveEditedExercise; $('deleteExercise').onclick=()=>{if(state.editId){if($('deleteExercise').dataset.scope==='bank')openBankDeleteModal(state.editId); else removeExercise(state.editId);} closeEditor();};
  $('attachExerciseImage').onclick=()=>$('editMediaFile').click();
  $('editMediaFile').onchange=handleEditorMediaFileSelected;
  $('removeExerciseImage').onclick=removeEditorMedia;
  $('finishPdfBtn').onclick=()=>finishWithPdf({large:false});
  $('finishLargePdfBtn').onclick=openLargePdfModal;
  $('finishPatientBtn').onclick=finishWithPatientApp;
  $('finishCancelBtn').onclick=closeFinishModal;
  $('shareModal').addEventListener('click',ev=>{if(ev.target===$('shareModal'))closeFinishModal();});
  $('cancelLargePdf').onclick=closeLargePdfModal;
  $('confirmLargePdf').onclick=()=>{closeLargePdfModal();finishWithPdf({large:true});};
  $('largePdfModal').addEventListener('click',ev=>{if(ev.target===$('largePdfModal'))closeLargePdfModal();});
  $('cancelLongMediaShare').onclick=closeLongMediaConfirmModal;
  $('confirmLongMediaShare').onclick=confirmLongMediaShare;
  $('longMediaConfirmModal').addEventListener('click',ev=>{if(ev.target===$('longMediaConfirmModal'))closeLongMediaConfirmModal();});
  $('adminConfigBtn').onclick=openAdminSecretsModal;
  $('closeAdminSecrets').onclick=closeAdminSecretsModal;
  $('saveAdminSecrets').onclick=saveAdminSecretsFromModal;
  if($('loadAdminSafeFile'))$('loadAdminSafeFile').onclick=()=>$('adminSafeFileInput').click();
  if($('adminSafeFileInput'))$('adminSafeFileInput').onchange=ev=>importAdminSafeFile(ev.target.files&&ev.target.files[0]).catch(err=>alert('Admin-Safe-Datei konnte nicht gelesen werden: '+err.message)).finally(()=>{ev.target.value='';});
  if($('importAdminCodePackage'))$('importAdminCodePackage').onclick=()=>importAdminCodePackageFromClipboard().catch(err=>alert('Code-Paket konnte nicht gelesen werden: '+err.message));
  if($('exportAdminCodePackage'))$('exportAdminCodePackage').onclick=()=>exportAdminCodePackageToClipboard().catch(err=>alert('Code-Paket konnte nicht kopiert werden: '+err.message));
  if($('downloadAdminSafeFile'))$('downloadAdminSafeFile').onclick=downloadAdminSafeFile;
  $('clearAdminSecrets').onclick=()=>{clearLocalAdminSecrets(); if($('adminGeminiKey1'))$('adminGeminiKey1').value=''; if($('adminGeminiKey2'))$('adminGeminiKey2').value=''; if($('adminMediaDropzoneEndpoint'))$('adminMediaDropzoneEndpoint').value=''; if($('adminMediaDropzoneUploadToken'))$('adminMediaDropzoneUploadToken').value='';};
  $('adminSecretsModal').addEventListener('click',ev=>{if(ev.target===$('adminSecretsModal'))closeAdminSecretsModal();});
  $('sharedBankBtn').onclick=openSharedBankModal;
  $('copySharedBank').onclick=copySharedBankPayload;
  $('pickSharedBankFile').onclick=()=>$('sharedBankFile').click();
  $('sharedBankFile').onchange=handleSharedBankFile;
  $('applySharedBank').onclick=applySharedBankFromText;
  $('closeSharedBank').onclick=closeSharedBankModal;
  $('sharedBankModal').addEventListener('click',ev=>{if(ev.target===$('sharedBankModal'))closeSharedBankModal();});

  if($('tabletMenuBtn'))$('tabletMenuBtn').onclick=()=>setTabletSideMenuOpen(!document.body.classList.contains('tabletMenuOpen'));
  if($('tabletMenuClose'))$('tabletMenuClose').onclick=()=>setTabletSideMenuOpen(false);
  if($('tabletSideBackdrop'))$('tabletSideBackdrop').onclick=()=>setTabletSideMenuOpen(false);
  if($('syncQrBtn'))$('syncQrBtn').onclick=openSyncPairModal;
  if($('tabletSyncQrBtn'))$('tabletSyncQrBtn').onclick=openSyncPairModal;
  if($('copySyncPairCode'))$('copySyncPairCode').onclick=copySyncPairCode;
  if($('testNativeSyncBtn'))$('testNativeSyncBtn').onclick=()=>testNativeSyncRoundtrip();
  if($('downloadSyncFileBtn'))$('downloadSyncFileBtn').onclick=downloadNativeSyncFile;
  if($('importSyncFileBtn'))$('importSyncFileBtn').onclick=()=>{const input=$('syncImportInput'); if(input)input.click();};
  if($('syncImportInput'))$('syncImportInput').onchange=ev=>{const file=ev&&ev.target&&ev.target.files&&ev.target.files[0]; importNativeSyncFile(file).finally(()=>{if(ev&&ev.target)ev.target.value='';});};
  if($('closeSyncPairModal'))$('closeSyncPairModal').onclick=closeSyncPairModal;
  if($('syncPairModal'))$('syncPairModal').addEventListener('click',ev=>{if(ev.target===$('syncPairModal'))closeSyncPairModal();});
  const kggAdminMenuQrTargets={
    colleague:{title:'Kolleg:innen-Web-App QR',hint:'Oeffnet die jeweils verlinkte Kolleg:innen-Web-App.',url:'https://kayus24.github.io/kgg/therapist-app/latest-html.html'},
    admin:{title:'Admin-Web-App QR',hint:'Oeffnet diese Admin-Web-App-Version. Manifest/Latest wird separat freigegeben.',url:'https://kayus24.github.io/kgg/therapist-app/releases/v388/web/KGG_APP_ADMIN_v388_android_flow_fixes.html'},
    android:{title:'Kolleg:innen-App APK QR',hint:'Oeffnet die aktuelle Android-Download-Seite fuer Kolleg:innen. Keine API-Keys, keine Sync-Daten.',url:'https://kayus24.github.io/kgg/therapist-app/latest-android.html'}
  };
  function closeKggTherapistShareModal(){
    const modal=$('kggTherapistShareModal');
    if(!modal)return;
    modal.classList.remove('isOpen');
    modal.setAttribute('aria-hidden','true');
  }
  function openKggTherapistShareModal(){
```
