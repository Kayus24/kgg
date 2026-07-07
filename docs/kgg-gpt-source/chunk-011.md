# KGG Source Chunk 011

- Source: `kgg-update/index.html`
- Lines: 4621-5040

```html
  .tabletSideMenu #tabletLayoutReset{grid-area:reset;min-height:44px!important;}
  .tabletSideMenu .tabletLayoutFreeTools.hidden{display:none!important;}
  /* v375: Admin tools live in the tablet side menu, not in the scan row. */
  body.adminMode .scanHub{
    grid-template-columns:58px minmax(148px,1fr) minmax(148px,1fr)!important;
  }
  body.adminMode .scanHub .adminConfigBtn,
  body.adminMode .scanHub .sharedBankBtn,
  body.adminMode .scanHub .syncQrBtn{
    display:none!important;
  }
  body.adminMode .scanHub #scanPreview{
    grid-column:1 / -1!important;
  }
  .tabletSideMenu{
    overflow-y:auto;
  }
  .tabletSideMenuAction{
    min-height:54px;
    width:100%;
    border:1px solid rgba(10,16,36,.12);
    border-radius:17px;
    background:#fff;
    color:#0a1024;
    font-size:.94rem;
    font-weight:900;
    text-align:left;
    padding:0 14px;
    box-shadow:0 10px 22px rgba(10,16,36,.07), inset 0 1px 0 rgba(255,255,255,.82);
    cursor:pointer;
  }
  .tabletSideMenuAction:active{
    transform:translateY(1px);
  }
  .tabletSideMenuQrActions{
    display:grid;
    grid-template-columns:1fr;
    gap:10px;
  }
  .packageLayoutSlot{
    grid-template-columns:1fr!important;
    align-items:stretch!important;
  }
  .packageLayoutSlot .tabletLayoutControls{display:none!important;}
  .packageLayoutSlot #packageToggle{width:100%!important;min-width:0!important;}
}

.kggAdminMenuQrModal{
  position:fixed;
  inset:0;
  z-index:1300;
  display:none;
  place-items:center;
  padding:22px;
  background:rgba(10,16,36,.26);
  backdrop-filter:blur(10px);
}
.kggAdminMenuQrModal.isOpen{display:grid;}
.kggAdminMenuQrSheet{
  width:min(520px,94vw);
  border:1.5px solid rgba(10,16,36,.12);
  border-radius:26px;
  background:#fff;
  box-shadow:0 30px 90px rgba(10,16,36,.22);
  padding:22px;
}
.kggAdminMenuQrSheet h2{
  margin:0 0 8px;
  color:#0a1024;
  font-size:1.35rem;
  font-weight:950;
}
.kggAdminMenuQrHint{
  margin:0 0 14px;
  color:#667085;
  font-size:.94rem;
  line-height:1.35;
  font-weight:750;
}
.kggAdminMenuQrBox{
  min-height:250px;
  display:grid;
  place-items:center;
  border:1px solid rgba(10,16,36,.10);
  border-radius:20px;
  background:#f8fafc;
  padding:14px;
}
.kggAdminMenuQrBox img{
  width:min(300px,72vw);
  height:min(300px,72vw);
  image-rendering:pixelated;
}
.kggAdminMenuQrLink{
  width:100%;
  min-height:76px;
  margin-top:12px;
  border:1px solid rgba(10,16,36,.12);
  border-radius:16px;
  padding:10px;
  resize:vertical;
  font-size:.82rem;
  line-height:1.35;
  color:#344054;
}
.kggAdminMenuQrButtons{
  display:grid;
  grid-template-columns:1fr 1fr;
  gap:10px;
  margin-top:12px;
}
.kggAdminMenuQrButtons button{
  min-height:48px;
  border-radius:16px;
  border:1px solid rgba(10,16,36,.12);
  background:#fff;
  color:#0a1024;
  font-weight:900;
  cursor:pointer;
}
.kggAdminMenuQrButtons .primary{
  background:#0a1024;
  color:#fff;
}


/* v362: keep the plan-card delete X in the top-right corner. */
.planCard{position:relative;}
.planCard .planDeleteBtn{
  position:absolute!important;
  top:6px!important;
  right:8px!important;
  z-index:5;
  display:inline-grid!important;
  place-items:center!important;
  width:30px!important;
  min-width:30px!important;
  height:30px!important;
  min-height:30px!important;
  padding:0!important;
  line-height:1!important;
  border-radius:999px!important;
}
.planCardActions{padding-right:24px;}

/* v376: tablet density and right-side menu polish from the latest QA screenshots. */
@media (min-width:760px){
  body.tabletLayoutCustom .app{
    width:min(100%,1280px)!important;
    grid-template-columns:minmax(300px,390px) minmax(0,1fr)!important;
    gap:10px!important;
    padding:12px 14px 76px!important;
  }
  body.tabletLayoutCustom .tabletMenuBtn{
    position:fixed!important;
    right:16px!important;
    top:16px!important;
    left:auto!important;
    z-index:1200!important;
    width:44px!important;
    min-width:44px!important;
    height:44px!important;
    min-height:44px!important;
    padding:8px!important;
    border-radius:14px!important;
    background:#fff!important;
    border:1px solid rgba(10,16,36,.16)!important;
    box-shadow:0 8px 22px rgba(7,16,39,.13)!important;
  }
  body.tabletLayoutCustom .scanHub{
    grid-template-columns:1fr 1fr!important;
    grid-auto-rows:56px!important;
    gap:8px!important;
    padding:0!important;
    min-height:0!important;
  }
  body.tabletLayoutCustom .scanHub .scanBtn,
  body.tabletLayoutCustom .scanHub .scanMeta,
  body.tabletLayoutCustom :is(#baseToggle,#finishBtn,#recentToggle,#packageToggle){
    min-height:46px!important;
    height:46px!important;
    border-radius:13px!important;
    padding:0 12px!important;
    font-size:15px!important;
    line-height:1.08!important;
  }
  body.tabletLayoutCustom .scanHub .scanMeta small{display:none!important}
  body.tabletLayoutCustom .panel{padding:10px!important;border-radius:18px!important}
  body.tabletLayoutCustom .inner{padding:8px!important;border-radius:16px!important}
  body.tabletLayoutCustom .panelTitle{font-size:24px!important;line-height:1.05!important;margin-bottom:8px!important}
  body.tabletLayoutCustom textarea{
    min-height:70px!important;
    max-height:118px!important;
    padding:12px 38px 12px 12px!important;
    font-size:16px!important;
    line-height:1.28!important;
  }
  body.tabletLayoutCustom .dbTitle{font-size:18px!important;margin:6px 0!important}
  body.tabletLayoutCustom .bankRows{max-height:calc(var(--kgg-visual-vh,100vh) - 214px)!important}
  body.tabletLayoutCustom .bankRow{min-height:48px!important;padding:7px 9px!important}
  body.tabletLayoutCustom .bankRow b{font-size:14px!important;line-height:1.12!important}
  body.tabletLayoutCustom .bankRow small{font-size:10px!important;margin-top:1px!important}
  body.tabletLayoutCustom .bankWithAz{grid-template-columns:38px minmax(0,1fr)!important}
  body.tabletLayoutCustom .az{font-size:10px!important;line-height:1.12!important;padding:4px 0!important}
  body.tabletLayoutCustom .az button{font-size:10px!important;min-height:14px!important}
  body.tabletLayoutCustom .rightPlanStack{min-height:calc(var(--kgg-visual-vh,100vh) - 180px)!important}
  body.tabletLayoutCustom .planCard{min-height:48px!important;padding:7px 9px!important;border-radius:13px!important}
  body.tabletLayoutCustom .planCard b{font-size:14px!important;line-height:1.15!important}
  body.tabletLayoutCustom .planCard small{font-size:10px!important;line-height:1.15!important}
  body.tabletLayoutCustom .planCard .drag,
  body.tabletLayoutCustom .planCard .iconBtn{width:30px!important;height:30px!important;min-width:30px!important;min-height:30px!important;padding:0!important}
  body.tabletLayoutCustom #planActions{
    grid-template-columns:minmax(0,1fr) minmax(0,1fr)!important;
    gap:10px!important;
  }
}</style>
<style>
  /* v365: Finish modal output actions are balanced; PDF is no longer the dominant black action. */
  #shareModal .finishOutputBtn{display:flex;align-items:center;justify-content:center;gap:9px;font-weight:1000}
  #shareModal .finishPdfBtn{background:#fff;border:1px solid var(--line);color:var(--ink)}
  #shareModal .finishAppBtn{background:#edf5ff;border:1px solid #9cccf4;color:#073254}
  #shareModal .finishIcon{display:inline-flex;align-items:center;justify-content:center;font-size:20px;line-height:1}</style>
<style>
  /* v366: mobile history/packages open from a floating bottom anchor. */
  @media (max-width:759px){
    .kggPhoneDrawerBackdrop{
      position:fixed;
      inset:0;
      z-index:88;
      background:rgba(7,16,39,.24);
      backdrop-filter:blur(8px);
      -webkit-backdrop-filter:blur(8px);
      opacity:0;
      pointer-events:none;
      transition:opacity .22s ease;
    }
    body.kggPhoneDrawerOpen .kggPhoneDrawerBackdrop{opacity:1;pointer-events:auto}
    body.kggPhoneDrawerOpen #recentToggle.phoneButtonFloat,
    body.kggPhoneDrawerOpen #packageToggle.phoneButtonFloat{
      position:fixed!important;
      left:16px!important;
      right:16px!important;
      bottom:calc(12px + env(safe-area-inset-bottom))!important;
      z-index:92!important;
      width:auto!important;
      min-width:0!important;
      height:58px!important;
      min-height:58px!important;
      border-radius:18px!important;
      justify-content:center!important;
      background:#fff!important;
      color:var(--ink)!important;
      border:1px solid rgba(220,227,235,.96)!important;
      box-shadow:0 22px 54px rgba(7,16,39,.26),0 5px 14px rgba(7,16,39,.12)!important;
      transform-origin:center bottom;
      animation:kggPhoneButtonDock .28s cubic-bezier(.18,.84,.24,1) both!important;
    }
    body.kggPhoneDrawerOpen #recentList:not(.hidden),
    body.kggPhoneDrawerOpen #packageList:not(.hidden){
      position:fixed!important;
      left:16px!important;
      right:16px!important;
      bottom:calc(86px + env(safe-area-inset-bottom))!important;
      z-index:91!important;
      max-height:min(56dvh,390px)!important;
      overflow:auto!important;
      background:rgba(255,255,255,.98)!important;
      border:1px solid rgba(220,227,235,.96)!important;
      border-radius:22px!important;
      padding:10px!important;
      box-shadow:0 22px 58px rgba(7,16,39,.24),0 4px 14px rgba(7,16,39,.10)!important;
      backdrop-filter:blur(10px);
      -webkit-backdrop-filter:blur(10px);
      transform-origin:bottom center;
      animation:kggPhoneDrawerFromDock .30s cubic-bezier(.18,.84,.24,1) both!important;
    }
    body.kggPhoneDrawerOpen #recentList:not(.hidden) .notice,
    body.kggPhoneDrawerOpen #packageList:not(.hidden) .notice{margin-top:0}
    @keyframes kggPhoneButtonDock{
      0%{opacity:.92;transform:translateY(18px) scale(.96);filter:blur(1px)}
      65%{opacity:1;transform:translateY(-3px) scale(1.015);filter:blur(0)}
      100%{opacity:1;transform:translateY(0) scale(1);filter:blur(0)}
    }
    @keyframes kggPhoneDrawerFromDock{
      0%{opacity:0;transform:translateY(28px) scale(.965);filter:blur(2px)}
      72%{opacity:1;transform:translateY(-4px) scale(1.01);filter:blur(0)}
      100%{opacity:1;transform:translateY(0) scale(1);filter:blur(0)}
    }
    body.is-scrolling :is(#recentList,#packageList,#baseFields,#bankContent,.bankArea,.dbTitle,.dbTitleTrain,.planActions,.finishBtn,#recentToggle,#packageToggle,#bankToggle,.phoneButtonFloat,.scanJobCard){
      transition:none!important;
      animation:none!important;
      scroll-behavior:auto!important;
    }
    body.is-scrolling :is(.dbTitle .dbTitleTrain,.bankArea.bankOpen #bankContent,#recentList,#packageList){
      transform:none!important;
      filter:none!important;
    }
  }
  /* v383: UI flow stability only. No PDF/QR/parser/plan-state changes. */
  @media (max-width:759px){
    body.is-scrolling.phoneTextFocus #inputWrap{
      position:relative!important;
      bottom:auto!important;
      z-index:auto!important;
      transform:none!important;
      animation:none!important;
      box-shadow:var(--shadow)!important;
    }
    body.is-scrolling :is(#recentList,#packageList,#baseFields,#bankContent,.bankArea,.dbTitle,.dbTitleTrain,.planActions,.finishBtn,#recentToggle,#packageToggle,#bankToggle,#baseToggle,.phoneButtonFloat,.scanJobCard,#inputWrap,.suggestion,#currentPlanBlock,.planSection,.planCard){
      transition:none!important;
      animation:none!important;
      scroll-behavior:auto!important;
    }
    body.is-scrolling :is(.dbTitle .dbTitleTrain,.bankArea.bankOpen #bankContent,#recentList,#packageList,#inputWrap,.suggestion,.phoneButtonFloat,.finishBtn,.planCard){
      transform:none!important;
      filter:none!important;
      scale:1 1!important;
    }
    .planActions,
    .planActions .finishBtn,
    .planActions #recentToggle,
    .recentText,
    .recentMini{
      transition:none!important;
    }
    .planActions.hasPlan .finishBtn{
      animation:none!important;
      transform:none!important;
      scale:1 1!important;
    }
    :is(.finishBtn,#recentToggle,#packageToggle,#bankToggle,#baseToggle,.planSectionHeader,.iconBtn):active{
      transform:none!important;
      scale:1 1!important;
    }
    .dbTitle.fullBankOpen .dbTitleTrain,
    .bankArea.bankOpen #bankContent,
    #bankArea.bankOpen{
      animation:none!important;
      transform:none!important;
      filter:none!important;
      clip-path:none!important;
    }
    #bankArea.bankOpen{
      overflow:hidden!important;
    }
    #bankArea.bankOpen #bankContent{
      min-height:0!important;
      overflow:hidden!important;
    }
    #bankArea.bankOpen .bankRows{
      overflow:auto!important;
      overscroll-behavior:contain;
      scroll-behavior:auto!important;
    }
    #bankArea.bankOpen.searchBankOpen{
      grid-template-columns:56px minmax(0,1fr)!important;
      align-items:start!important;
    }
    #bankArea.bankOpen.searchBankOpen #bankToggle{
      grid-column:1!important;
      grid-row:1!important;
    }
    #bankArea.bankOpen.searchBankOpen #bankContent{
      grid-column:2!important;
      grid-row:1!important;
      min-width:0!important;
      margin-top:0!important;
    }
    #bankArea.bankOpen.searchBankOpen .bankRows{
      max-height:min(52dvh,420px)!important;
    }
    body.kggPhoneDrawerOpen #recentToggle.phoneButtonFloat,
    body.kggPhoneDrawerOpen #packageToggle.phoneButtonFloat,
    body.kggPhoneDrawerOpen #recentList:not(.hidden),
    body.kggPhoneDrawerOpen #packageList:not(.hidden){
      animation:none!important;
      transform:none!important;
      filter:none!important;
    }
    #editorModal{
      align-items:center!important;
      padding:14px!important;
      background:rgba(7,16,39,.52)!important;
    }
    #editorModal .editorSheet{
      width:min(100% - 28px,520px)!important;
      max-height:calc(100dvh - 28px)!important;
      border-radius:22px!important;
      overflow:auto!important;
      overscroll-behavior:contain;
      box-shadow:0 24px 70px rgba(7,16,39,.28)!important;
    }
    #editorModal .editorMediaPreview img,
    #currentPlanBlock .planThumb img,
    .kggAdminMenuQrBox img,
    .qrBox img{
      object-fit:contain!important;
    }
    #editorModal .editorCancelBtn{
      display:grid!important;
      place-items:center!important;
      color:#38475b!important;
    }
  }
  @media (min-width:760px){
    body{
      padding-top:max(18px,calc(env(safe-area-inset-top) + 14px))!important;
    }
    .app,
    body.tabletLayoutCustom .app{
      height:calc(var(--kgg-visual-vh,100dvh) - 36px - env(safe-area-inset-top))!important;
      max-height:calc(var(--kgg-visual-vh,100dvh) - 36px - env(safe-area-inset-top))!important;
    }
    .tabletMenuBtn,
    body.tabletLayoutCustom .tabletMenuBtn{
      top:max(14px,calc(env(safe-area-inset-top) + 12px))!important;
      z-index:1200!important;
      pointer-events:auto!important;
      touch-action:manipulation!important;
    }
```
