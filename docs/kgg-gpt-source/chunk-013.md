# KGG Source Chunk 013

- Source: `kgg-update/index.html`
- Lines: 5461-5880

```html

  /* v397/v398 base: Tablet gap cleanup against marked reference screenshots.
     UI-only: no PDF, QR, Scan, parser, plan-state or media logic changes. */
  @media (min-width:760px){
    html,body{
      width:100%!important;
      min-height:100%!important;
      margin:0!important;
      padding:0!important;
      overflow:hidden!important;
      background:#e8eef6!important;
    }
    body{display:block!important;}
    body.tabletLayoutCustom .app,
    .app{
      width:100vw!important;
      max-width:none!important;
      height:100dvh!important;
      max-height:100dvh!important;
      min-height:0!important;
      margin:0!important;
      padding:8px 10px!important;
      border:0!important;
      border-radius:0!important;
      box-shadow:none!important;
      display:grid!important;
      grid-template-columns:minmax(300px,31vw) minmax(0,1fr) 126px!important;
      grid-template-rows:44px 92px minmax(0,1fr)!important;
      gap:8px!important;
      align-items:stretch!important;
      overflow:hidden!important;
    }
    body.tabletLayoutCustom .adminTestBanner,
    body.tabletLayoutCustom .topbar,
    body.tabletLayoutCustom #panelTitle,
    body.tabletLayoutCustom #savePackageBtn,
    body.tabletLayoutCustom #syncQrBtn,
    body.tabletLayoutCustom #adminConfigBtn,
    body.tabletLayoutCustom #sharedBankBtn,
    body.tabletLayoutCustom #scanPreview,
    body.tabletLayoutCustom #inputLabel,
    body.tabletLayoutCustom #dbTitle{
      display:none!important;
    }
    body.tabletLayoutCustom #createPanel,
    body.tabletLayoutCustom #createPanel .inner,
    body.tabletLayoutCustom #createPanel .tools,
    body.tabletLayoutCustom #planActions{
      display:contents!important;
      min-height:0!important;
      margin:0!important;
      padding:0!important;
      border:0!important;
      box-shadow:none!important;
      background:transparent!important;
    }
    body.tabletLayoutCustom #scanHub{
      grid-column:1!important;
      grid-row:1!important;
      height:44px!important;
      min-height:44px!important;
      margin:0!important;
      padding:0!important;
      border:0!important;
      border-radius:0!important;
      box-shadow:none!important;
      background:transparent!important;
      display:grid!important;
      grid-template-columns:36px minmax(0,1fr) minmax(0,1fr)!important;
      gap:8px!important;
      overflow:visible!important;
    }
    body.tabletLayoutCustom #tabletMenuBtn,
    body.tabletLayoutCustom #scanBtn,
    body.tabletLayoutCustom #filePickBtn{
      width:100%!important;
      height:44px!important;
      min-height:44px!important;
      margin:0!important;
      align-self:stretch!important;
      justify-self:stretch!important;
      box-sizing:border-box!important;
    }
    body.tabletLayoutCustom #tabletMenuBtn{
      grid-column:1!important;
      display:flex!important;
      border-radius:12px!important;
    }
    body.tabletLayoutCustom #scanBtn{
      grid-column:2!important;
      padding:0 10px!important;
      border-radius:12px!important;
      font-size:16px!important;
      justify-content:center!important;
    }
    body.tabletLayoutCustom #filePickBtn{
      grid-column:3!important;
      display:flex!important;
      align-items:center!important;
      justify-content:center!important;
      padding:0 10px!important;
      border:1px solid var(--line)!important;
      border-radius:12px!important;
      background:#fff!important;
      font-size:16px!important;
      line-height:1!important;
      box-shadow:var(--shadow)!important;
    }
    body.tabletLayoutCustom #filePickBtn small{display:none!important;}
    body.tabletLayoutCustom #baseToggle{
      grid-column:2/4!important;
      grid-row:1!important;
      width:100%!important;
      height:44px!important;
      min-height:44px!important;
      margin:0!important;
      align-self:stretch!important;
      justify-self:stretch!important;
      border-radius:14px!important;
      font-size:14px!important;
      padding:0 14px!important;
    }
    body.tabletLayoutCustom #createPanel.planMode #baseToggle{
      grid-column:2/3!important;
    }
    body.tabletLayoutCustom #inputWrap{
      grid-column:1!important;
      grid-row:2!important;
      width:100%!important;
      height:92px!important;
      min-height:92px!important;
      margin:0!important;
      align-self:stretch!important;
      overflow:hidden!important;
      border-radius:14px!important;
    }
    body.tabletLayoutCustom #exerciseInput{
      height:100%!important;
      min-height:0!important;
      resize:none!important;
      padding:12px 42px 12px 12px!important;
      font-size:18px!important;
      line-height:1.25!important;
      box-sizing:border-box!important;
    }
    body.tabletLayoutCustom #bankArea.bankOpen,
    body.tabletLayoutCustom #bankArea{
      grid-column:1!important;
      grid-row:3!important;
      width:100%!important;
      height:100%!important;
      min-height:0!important;
      max-height:none!important;
      margin:0!important;
      align-self:stretch!important;
      border-radius:16px!important;
      overflow:hidden!important;
    }
    body.tabletLayoutCustom #bankContent,
    body.tabletLayoutCustom #bankContent .bankWithAz,
    body.tabletLayoutCustom #bankContent .bankRows{
      min-height:0!important;
      max-height:none!important;
      height:100%!important;
    }
    body.tabletLayoutCustom #rightPlanStack,
    body.tabletLayoutCustom #rightPlanStack.hidden{
      grid-column:2/4!important;
      grid-row:2/4!important;
      display:flex!important;
      flex-direction:column!important;
      width:100%!important;
      height:100%!important;
      min-height:0!important;
      margin:0!important;
      gap:0!important;
      align-self:stretch!important;
      justify-self:stretch!important;
      visibility:visible!important;
      pointer-events:auto!important;
      overflow:hidden!important;
    }
    body.tabletLayoutCustom #currentPlanBlock,
    body.tabletLayoutCustom #rightPlanStack #currentPlanBlock.hidden{
      display:flex!important;
      flex-direction:column!important;
      flex:1 1 auto!important;
      width:100%!important;
      height:100%!important;
      min-height:0!important;
      margin:0!important;
      padding:12px!important;
      border:2px solid #111827!important;
      border-radius:18px!important;
      background:#fff!important;
      box-shadow:none!important;
      visibility:visible!important;
      pointer-events:auto!important;
      overflow:hidden!important;
    }
    body.tabletLayoutCustom #rightPlanStack #scannedPlansBlock.hidden{
      display:none!important;
    }
    body.tabletLayoutCustom #currentPlanToggle{
      flex:0 0 auto!important;
      min-height:44px!important;
      padding:8px 10px!important;
      font-size:18px!important;
      border-radius:12px!important;
    }
    body.tabletLayoutCustom #currentPlanBlock .planSectionBody{
      flex:1 1 auto!important;
      min-height:0!important;
      overflow:auto!important;
      padding:8px 0 0!important;
    }
    body.tabletLayoutCustom #currentPlanBlock #planList{
      min-height:100%!important;
      margin:0!important;
      padding:0!important;
      display:grid!important;
      align-content:start!important;
    }
    body.tabletLayoutCustom #currentPlanBlock #planList:empty::before{
      content:"Noch keine Übungen im Plan\A Füge Übungen aus der Datenbank hinzu.";
      white-space:pre;
      min-height:220px;
      display:grid;
      place-items:center;
      text-align:center;
      color:#5f6875;
      font-weight:800;
      font-size:13px;
    }
    body.tabletLayoutCustom #recentToggle,
    body.tabletLayoutCustom #packageToggle,
    body.tabletLayoutCustom #recentList,
    body.tabletLayoutCustom #packageList,
    body.tabletLayoutCustom #packageLayoutSlot{
      display:none!important;
    }
    body.tabletLayoutCustom #finishBtn,
    body.tabletLayoutCustom #finishBtn.hidden,
    body.tabletLayoutCustom #createPanel:not(.planMode) #finishBtn,
    body.tabletLayoutCustom #createPanel:not(.planMode) #finishBtn.hidden{
      display:none!important;
    }
    body.tabletLayoutCustom #createPanel .tools,
    body.tabletLayoutCustom #createPanel .tools #planActions,
    body.tabletLayoutCustom #createPanel:not(.planMode) .tools #planActions,
    body.tabletLayoutCustom #createPanel.planMode .tools #planActions{
      display:contents!important;
      width:auto!important;
      height:auto!important;
      min-height:0!important;
      margin:0!important;
      padding:0!important;
      border:0!important;
      box-shadow:none!important;
      background:transparent!important;
    }
    body.tabletLayoutCustom #createPanel .tools #packageLayoutSlot,
    body.tabletLayoutCustom #createPanel:not(.planMode) .tools #packageLayoutSlot,
    body.tabletLayoutCustom #createPanel.planMode .tools #packageLayoutSlot,
    body.tabletLayoutCustom #createPanel .tools #packageToggle,
    body.tabletLayoutCustom #createPanel.planMode .tools #packageToggle,
    body.tabletLayoutCustom #createPanel .tools #recentToggle,
    body.tabletLayoutCustom #createPanel.planMode .tools #recentToggle{
      display:none!important;
      width:0!important;
      height:0!important;
      min-height:0!important;
      margin:0!important;
      padding:0!important;
      border:0!important;
      overflow:hidden!important;
    }
    body.tabletLayoutCustom #createPanel #rightPlanStack,
    body.tabletLayoutCustom #createPanel #rightPlanStack.hidden,
    body.tabletLayoutCustom #createPanel:not(.planMode) #rightPlanStack,
    body.tabletLayoutCustom #createPanel:not(.planMode) #rightPlanStack.hidden,
    body.tabletLayoutCustom #createPanel.planMode #rightPlanStack,
    body.tabletLayoutCustom #createPanel.planMode #rightPlanStack.hidden{
      grid-column:2/4!important;
      grid-row:2/4!important;
      display:flex!important;
      flex-direction:column!important;
      width:100%!important;
      height:100%!important;
      min-height:0!important;
      margin:0!important;
      gap:0!important;
      align-self:stretch!important;
      justify-self:stretch!important;
      visibility:visible!important;
      pointer-events:auto!important;
      overflow:hidden!important;
    }
    body.tabletLayoutCustom #createPanel #rightPlanStack #currentPlanBlock,
    body.tabletLayoutCustom #createPanel #rightPlanStack #currentPlanBlock.hidden,
    body.tabletLayoutCustom #createPanel:not(.planMode) #rightPlanStack #currentPlanBlock.hidden,
    body.tabletLayoutCustom #createPanel.planMode #rightPlanStack #currentPlanBlock.hidden{
      display:flex!important;
      flex-direction:column!important;
      flex:1 1 auto!important;
      width:100%!important;
      height:100%!important;
      min-height:0!important;
      margin:0!important;
      visibility:visible!important;
      pointer-events:auto!important;
    }
    body.tabletLayoutCustom #createPanel.planMode #finishBtn{
      grid-column:3!important;
      grid-row:1!important;
      display:flex!important;
      visibility:visible!important;
      opacity:1!important;
      pointer-events:auto!important;
      scale:1 1!important;
      width:126px!important;
      min-width:126px!important;
      height:44px!important;
      min-height:44px!important;
      margin:0!important;
      justify-content:center!important;
      align-items:center!important;
      padding:0 16px!important;
      border-width:0!important;
      border-radius:14px!important;
      font-size:16px!important;
    }
  }

  /* v398: Confirmed Tablet Sidebar + Tab S9 layout only.
     No PDF, patient app, Scan/OCR core, parser, plan-state or media/upload changes. */
  @media (min-width:760px){
    :root{--kgg-tablet-sidebar-w:230px;--kgg-tablet-safe-top:calc(env(safe-area-inset-top) + 32px);--kgg-tablet-gap:8px;--kgg-tablet-left-default:clamp(460px,42vw,540px);--kgg-tablet-left-menu:clamp(360px,40vw,440px);}
    html,body{width:100%!important;min-height:100%!important;margin:0!important;overflow:hidden!important;background:#e8eef6!important;}
    body.tabletLayoutCustom{padding:var(--kgg-tablet-safe-top) 0 0!important;box-sizing:border-box!important;}
    body.tabletLayoutCustom .app{width:100vw!important;max-width:none!important;height:calc(100dvh - var(--kgg-tablet-safe-top))!important;max-height:calc(100dvh - var(--kgg-tablet-safe-top))!important;margin:0!important;padding:0 10px 8px!important;box-sizing:border-box!important;display:grid!important;grid-template-columns:var(--kgg-tablet-left-col,var(--kgg-tablet-left-default)) minmax(0,1fr) 126px!important;grid-template-rows:44px 92px minmax(0,1fr)!important;gap:var(--kgg-tablet-gap)!important;transform:translateX(0)!important;transition:width .2s ease,transform .2s ease,grid-template-columns .2s ease!important;overflow:hidden!important;}
    body.tabletLayoutCustom.tabletMenuOpen .app{width:calc(100vw - var(--kgg-tablet-sidebar-w))!important;transform:translateX(var(--kgg-tablet-sidebar-w))!important;grid-template-columns:var(--kgg-tablet-left-col,var(--kgg-tablet-left-menu)) minmax(0,1fr) 126px!important;}
    body.tabletLayoutCustom #scanHub{grid-template-columns:36px minmax(0,1fr) minmax(0,1fr)!important;}
    body.tabletLayoutCustom .tabletSideBackdrop,body.tabletLayoutCustom.tabletMenuOpen .tabletSideBackdrop{display:none!important;opacity:0!important;pointer-events:none!important;visibility:hidden!important;}
    body.tabletLayoutCustom .tabletSideMenu{display:flex!important;position:fixed!important;left:0!important;top:var(--kgg-tablet-safe-top)!important;bottom:auto!important;width:var(--kgg-tablet-sidebar-w)!important;min-width:var(--kgg-tablet-sidebar-w)!important;max-width:var(--kgg-tablet-sidebar-w)!important;height:calc(100dvh - var(--kgg-tablet-safe-top))!important;max-height:calc(100dvh - var(--kgg-tablet-safe-top))!important;padding:calc(env(safe-area-inset-top) + 16px) 12px calc(env(safe-area-inset-bottom) + 14px)!important;box-sizing:border-box!important;gap:18px!important;background:rgba(255,255,255,.98)!important;border-right:1px solid rgba(15,23,42,.12)!important;box-shadow:16px 0 40px rgba(15,23,42,.12)!important;transform:translateX(-100%)!important;transition:transform .22s cubic-bezier(.22,.8,.32,1)!important;z-index:1210!important;overflow-x:hidden!important;overflow-y:auto!important;visibility:visible!important;}
    body.tabletLayoutCustom.tabletMenuOpen .tabletSideMenu{transform:translateX(0)!important;}
    body.tabletLayoutCustom .tabletSideMenuHead{min-height:34px!important;padding:0!important;margin:0!important;font-size:18px!important;line-height:1!important;}
    body.tabletLayoutCustom .tabletMenuClose{width:34px!important;height:34px!important;min-width:34px!important;border-radius:999px!important;font-size:22px!important;}
    body.tabletLayoutCustom .tabletSideMenuMain{display:grid!important;gap:12px!important;margin:0!important;padding:0!important;border:0!important;}
    body.tabletLayoutCustom .tabletMenuNavAction{width:100%!important;min-height:50px!important;display:grid!important;grid-template-columns:32px minmax(0,1fr)!important;align-items:center!important;justify-items:start!important;gap:8px!important;padding:8px 8px!important;border:0!important;border-radius:12px!important;background:#fff!important;color:#071027!important;box-shadow:none!important;overflow:visible!important;text-align:left!important;font-size:13px!important;line-height:1.15!important;font-weight:950!important;white-space:normal!important;}
    body.tabletLayoutCustom .tabletMenuActionIcon{width:30px!important;height:30px!important;display:grid!important;place-items:center!important;font-size:21px!important;line-height:1!important;flex:0 0 auto!important;color:#071027!important;}
    body.tabletLayoutCustom .tabletSideMenuLayoutPanel[hidden]{display:none!important;}
    body.tabletLayoutCustom .tabletSideMenuLayoutPanel{display:grid!important;gap:8px!important;padding:8px!important;border:1px solid rgba(220,227,235,.95)!important;border-radius:12px!important;background:#f7f9fc!important;}
    body.tabletLayoutCustom .tabletSideMenu .tabletLayoutControls{display:grid!important;gap:8px!important;width:100%!important;}
    body.tabletLayoutCustom .tabletSideMenu .tabletLayoutFreeTools{display:grid!important;grid-template-columns:42px minmax(0,1fr) 42px!important;grid-template-areas:"plus value minus" "reset reset reset"!important;gap:6px!important;}
    body.tabletLayoutCustom .tabletSideMenu .tabletLayoutFreeTools.hidden{display:none!important;}
    body.tabletLayoutCustom .tabletSideMenu .tabletLayoutFreeTools button,body.tabletLayoutCustom .tabletSideMenu .tabletLockSwitch{min-height:38px!important;border-radius:10px!important;}
    body.tabletLayoutCustom #recentList:not(.hidden),body.tabletLayoutCustom #packageList:not(.hidden){display:block!important;position:fixed!important;left:calc(var(--kgg-tablet-sidebar-w) + 14px)!important;top:calc(var(--kgg-tablet-safe-top) + 58px)!important;width:min(480px,calc(100vw - var(--kgg-tablet-sidebar-w) - 34px))!important;max-height:calc(100dvh - var(--kgg-tablet-safe-top) - 86px)!important;overflow:auto!important;z-index:1205!important;background:rgba(255,255,255,.98)!important;border:1px solid rgba(220,227,235,.95)!important;border-radius:16px!important;box-shadow:0 18px 48px rgba(7,16,39,.18)!important;padding:10px!important;}
    body.tabletLayoutCustom .kggTherapistShareModal{position:fixed!important;inset:0!important;display:none!important;place-items:center!important;z-index:1320!important;background:rgba(7,16,39,.35)!important;padding:18px!important;box-sizing:border-box!important;}
    body.tabletLayoutCustom .kggTherapistShareModal.isOpen{display:grid!important;}
    .kggTherapistShareSheet{width:min(92vw,440px)!important;display:grid!important;gap:12px!important;background:#fff!important;color:#071027!important;border:2px solid #111827!important;border-radius:20px!important;padding:16px!important;box-shadow:0 22px 70px rgba(7,16,39,.24)!important;}
    .kggTherapistShareSheet h2{margin:0!important;font-size:22px!important;line-height:1.05!important;}
    .kggTherapistShareHint{margin:0!important;color:#657386!important;font-weight:800!important;}
    .kggTherapistShareChoices{display:grid!important;gap:10px!important;}
    .kggTherapistShareChoices button{min-height:62px!important;padding:10px 12px!important;border:1px solid #dce3eb!important;border-radius:14px!important;background:#fff!important;text-align:left!important;box-shadow:0 4px 14px rgba(7,16,39,.08)!important;}
    .kggTherapistShareChoices b{display:block!important;font-size:16px!important;}
    .kggTherapistShareChoices small{display:block!important;margin-top:3px!important;color:#657386!important;font-weight:800!important;line-height:1.25!important;}
  }
  /* v399: Tablet package overlay, split-handle scale control and safer scaled buttons only. */
  @media (min-width:760px){
    :root{--kgg-tablet-package-w:clamp(360px,32vw,520px);--kgg-tablet-collision-gap:14px;--kgg-tablet-button-safe-gap:clamp(10px,var(--kgg-tablet-collision-gap),28px);}
    body.tabletLayoutCustom .tabletMenuBtn{display:inline-flex!important;flex-direction:column!important;align-items:center!important;justify-content:center!important;gap:4px!important;width:44px!important;min-width:44px!important;max-width:44px!important;padding:0!important;box-sizing:border-box!important;}
    body.tabletLayoutCustom .tabletMenuBtn span{display:block!important;margin:0!important;flex:0 0 auto!important;width:24px!important;height:3px!important;}
    body.tabletLayoutCustom .app{gap:max(var(--kgg-tablet-gap),var(--kgg-tablet-button-safe-gap))!important;column-gap:max(var(--kgg-tablet-gap),var(--kgg-tablet-button-safe-gap))!important;row-gap:max(var(--kgg-tablet-gap),calc(var(--kgg-tablet-button-safe-gap) - 2px))!important;}
    body.tabletLayoutCustom .scanHub{gap:var(--kgg-tablet-button-safe-gap)!important;}
    body.tabletLayoutCustom .scanHub :is(.scanBtn,.scanMeta),body.tabletLayoutCustom #baseToggle,body.tabletLayoutCustom :is(#finishBtn,#recentToggle,#packageToggle){min-width:0!important;overflow:hidden!important;text-wrap:balance;}
    body.tabletLayoutCollisionTight .scanHub{gap:var(--kgg-tablet-button-safe-gap)!important;}
    body.tabletLayoutCollisionTight .scanHub :is(.scanBtn,.scanMeta,.adminConfigBtn,.sharedBankBtn),body.tabletLayoutCollisionTight #baseToggle{font-size:clamp(8px,calc(13px * var(--kgg-tablet-ui-scale,1)),22px)!important;line-height:1.08!important;padding:6px 8px!important;}
    body.tabletLayoutCustom .tabletLayoutResizeHandle{pointer-events:none!important;z-index:1190!important;}
    body.tabletLayoutEditMode .tabletLayoutResizeHandle{display:block!important;pointer-events:auto!important;}
    body.tabletLayoutEditMode .tabletLayoutResizeHandle::before{width:18px!important;background:rgba(255,255,255,.92)!important;border:1px solid rgba(210,218,229,.98)!important;box-shadow:0 10px 28px rgba(7,16,39,.14)!important;}
    .tabletSplitScaleControl{position:absolute;left:50%;top:50%;transform:translate(-50%,-50%);display:none;grid-template-rows:42px 34px 42px;align-items:center;justify-items:center;width:48px;padding:7px 5px;border:1px solid rgba(210,218,229,.98);border-radius:999px;background:rgba(255,255,255,.98);box-shadow:0 14px 34px rgba(7,16,39,.16),inset 0 1px 0 rgba(255,255,255,.9);gap:4px;}
    body.tabletLayoutEditMode .tabletSplitScaleControl{display:grid;}
    .tabletSplitScaleControl button{width:36px;height:36px;border-radius:999px;border:1px solid rgba(210,218,229,.98);background:#fff;color:#071027;font-size:22px;font-weight:950;line-height:1;box-shadow:0 5px 13px rgba(7,16,39,.09);}
    .tabletSplitScaleValue{font-size:12px;font-weight:950;color:#344054;line-height:1;white-space:nowrap;}
    body.tabletLayoutEditMode #tabletMenuLayoutBtn,body.tabletPackageOverlayOpen #tabletMenuPackagesBtn{background:#eef5ff!important;color:#071027!important;box-shadow:inset 3px 0 0 #0b63ce,0 8px 18px rgba(7,16,39,.08)!important;}
    body.tabletPackageOverlayOpen.tabletMenuOpen .app{width:100vw!important;transform:translateX(0)!important;}
    .tabletPackageShade{display:none;position:fixed;left:var(--kgg-tablet-sidebar-w);right:0;top:var(--kgg-tablet-safe-top);bottom:0;background:rgba(7,16,39,.42);z-index:1212;backdrop-filter:blur(1px);}
    body.tabletPackageOverlayOpen .tabletPackageShade{display:block!important;}
    .tabletPackageOverlay{display:flex;position:fixed;left:var(--kgg-tablet-sidebar-w);top:var(--kgg-tablet-safe-top);bottom:0;width:var(--kgg-tablet-package-w);max-width:calc(100vw - var(--kgg-tablet-sidebar-w) - 20px);z-index:1220;flex-direction:column;gap:14px;padding:16px 16px 18px;box-sizing:border-box;background:rgba(255,255,255,.98);border-right:1px solid rgba(15,23,42,.12);border-radius:0 20px 20px 0;box-shadow:24px 0 58px rgba(7,16,39,.18);transform:translateX(calc(-100% - var(--kgg-tablet-sidebar-w)));transition:transform .22s cubic-bezier(.22,.8,.32,1);overflow:hidden;visibility:hidden;}
    body.tabletPackageOverlayOpen .tabletPackageOverlay{transform:translate3d(0,0,0)!important;visibility:visible!important;transition:none!important;}
    .tabletPackageHead{display:flex;align-items:center;justify-content:space-between;gap:12px;min-height:38px;}
    .tabletPackageTitle{display:flex;align-items:center;gap:10px;color:#071027;font-size:20px;font-weight:950;}
    .tabletPackageTitle span{width:32px;height:32px;display:grid;place-items:center;border-radius:10px;background:#eef5ff;}
    .tabletPackageClose{width:36px;height:36px;border-radius:999px;border:1px solid rgba(220,227,235,.95);background:#fff;color:#071027;font-size:24px;font-weight:900;line-height:1;}
    .tabletPackageSearch{display:grid;grid-template-columns:24px minmax(0,1fr);align-items:center;gap:8px;min-height:46px;padding:0 12px;border:1px solid rgba(220,227,235,.95);border-radius:14px;background:#fff;box-shadow:0 4px 14px rgba(7,16,39,.05);color:#667085;}
    .tabletPackageSearch input{border:0!important;outline:0!important;background:transparent!important;font-size:14px!important;font-weight:750!important;color:#071027!important;min-width:0!important;}
    .tabletPackageCards{display:grid;gap:12px;overflow:auto;padding:2px 2px 8px;overscroll-behavior:contain;}
    .tabletPackageCard{display:grid;grid-template-columns:54px minmax(0,1fr) 30px;gap:12px;align-items:center;width:100%;min-height:118px;padding:12px;border:1px solid rgba(220,227,235,.95);border-radius:14px;background:#fff;color:#071027;text-align:left;box-shadow:0 5px 18px rgba(7,16,39,.07);}
    .tabletPackageIcon{width:48px;height:48px;display:grid;place-items:center;border-radius:12px;background:#eef5ff;font-size:24px;}
    .tabletPackageCard:nth-child(4n+2) .tabletPackageIcon{background:#f1f8e9;}
    .tabletPackageCard:nth-child(4n+3) .tabletPackageIcon{background:#f4edff;}
    .tabletPackageCard:nth-child(4n+4) .tabletPackageIcon{background:#eaf8fb;}
    .tabletPackageBody{min-width:0;display:grid;gap:7px;}
    .tabletPackageBody b{font-size:15px;font-weight:950;line-height:1.15;}
    .tabletPackageBody p{margin:0;color:#475467;font-size:12px;font-weight:750;line-height:1.32;}
    .tabletPackageMeta{display:flex;gap:8px;flex-wrap:wrap;}
    .tabletPackageMeta span{display:inline-flex;align-items:center;min-height:24px;padding:0 8px;border:1px solid rgba(220,227,235,.95);border-radius:999px;background:#f8fafc;color:#344054;font-size:11px;font-weight:900;}
    .tabletPackageArrow{font-size:26px;color:#071027;font-weight:950;text-align:center;}
    .tabletPackageEmpty{padding:18px;border:1px dashed rgba(148,163,184,.8);border-radius:14px;background:#f8fafc;color:#667085;font-weight:850;line-height:1.35;}
  }
</style>

  <script>
    /* KGG v182 mobile single-file: inline offline PDF runtime, no external file needed. */
/*
 * KGG offline PDF runtime shim.
 * Provides the small jsPDF API surface used by kgg_plan_generator_v178/v179.
 * No network, no API keys, no JSON output.
 */
```
