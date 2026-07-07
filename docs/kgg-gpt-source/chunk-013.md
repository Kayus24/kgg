# KGG Source Chunk 013

- Source: `kgg-update/index.html`
- Lines: 5461-5880

```html
      grid-column:2/4!important;
      grid-row:5!important;
      width:calc(50% - 6px)!important;
      justify-self:start!important;
      align-self:stretch!important;
    }
    #createPanel.planMode .packageLayoutSlot{
      grid-column:2/4!important;
      grid-row:5!important;
      width:calc(50% - 6px)!important;
      justify-self:end!important;
      align-self:stretch!important;
      display:grid!important;
      grid-template-columns:minmax(0,1fr)!important;
    }
    #createPanel.planMode .packageLayoutSlot #packageToggle{
      width:100%!important;
      min-width:0!important;
      justify-content:center!important;
    }
    #createPanel.planMode .packageLayoutSlot .tabletLayoutControls{
      display:none!important;
    }
    body.tabletLayoutCustom #createPanel .planActions{
      grid-column:2/4!important;
      grid-row:5!important;
      display:grid!important;
      grid-template-columns:minmax(0,1fr) minmax(0,1fr)!important;
      gap:12px!important;
      width:100%!important;
      min-width:0!important;
      align-self:stretch!important;
      z-index:1!important;
    }
    body.tabletLayoutCustom #createPanel .planActions #finishBtn.hidden{
      display:none!important;
    }
    body.tabletLayoutCustom #createPanel .planActions #recentToggle{
      grid-column:1!important;
      grid-row:1!important;
      width:100%!important;
      min-width:0!important;
      justify-self:stretch!important;
    }
    body.tabletLayoutCustom #createPanel .packageLayoutSlot{
      grid-column:2/4!important;
      grid-row:5!important;
      width:calc((100% - 12px) / 2)!important;
      min-width:0!important;
      justify-self:end!important;
      align-self:stretch!important;
      z-index:2!important;
    }
  }
  @media (max-width:759px){
    body.phoneTextFocus #inputWrap{
      position:relative!important;
      bottom:auto!important;
      transform:none!important;
      animation:none!important;
    }
    body.phoneTextFocus #suggestion:not(.hidden),
    body.phoneTextFocus #currentPlanBlock,
    body.phoneTextFocus .planActions,
    body.phoneTextFocus .finishBtn{
      transform:none!important;
      animation:none!important;
      transition:none!important;
    }
    .planActions,
    .planActions .finishBtn,
    .planActions #recentToggle,
    #packageToggle,
    .phoneButtonFloat{
      transform:none!important;
      animation:none!important;
      transition:none!important;
    }
  }

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
```
