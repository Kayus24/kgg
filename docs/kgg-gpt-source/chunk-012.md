# KGG Source Chunk 012

- Source: `kgg-update/index.html`
- Lines: 5041-5460

```html
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
    #rightPlanStack .planSectionHeader,
    #bankArea #bankToggle{
      flex:0 0 auto!important;
    }
    #rightPlanStack .planSectionBody,
    #rightPlanStack .scanInboxList,
    #bankArea.bankOpen .bankRows{
      min-height:0!important;
      overscroll-behavior:contain;
    }
    #createPanel.planMode #recentToggle,
    #createPanel.planMode #packageToggle{
      justify-content:center!important;
      min-width:0!important;
      width:100%!important;
    }
  }
  /* v385: actual UI-flow fixes layered after the v384 build-identity baseline. */
  @media (max-width:759px){
    body.is-scrolling :is(#currentPlanBlock,#planList,#rightPlanStack,.planSection,.planSectionBody){
      transition:none!important;
      animation:none!important;
      scroll-behavior:auto!important;
    }
    body.is-scrolling .planSection.collapsed{
      max-height:58px!important;
    }
    body.kggPlanCardSwiping .planCard.swipe-dragging,
    body.is-scrolling .planCard.swipe-dragging{
      transform:translateX(var(--kgg-plan-swipe-x,0px))!important;
      transition:none!important;
      will-change:transform,opacity;
    }
    body.kggPlanCardSwiping .planCard.swipe-removing,
    body.is-scrolling .planCard.swipe-removing{
      transform:translateX(var(--kgg-plan-swipe-x,0px))!important;
    }
  }
  @media (min-width:760px){
    :root{
      --kgg-tablet-safe-top:max(46px,calc(env(safe-area-inset-top) + 34px));
      --kgg-tablet-safe-bottom:max(8px,env(safe-area-inset-bottom));
    }
    body{
      padding-top:var(--kgg-tablet-safe-top)!important;
      padding-bottom:var(--kgg-tablet-safe-bottom)!important;
    }
    .app,
    body.tabletLayoutCustom .app{
      height:calc(var(--kgg-visual-vh,100dvh) - var(--kgg-tablet-safe-top) - var(--kgg-tablet-safe-bottom))!important;
      max-height:calc(var(--kgg-visual-vh,100dvh) - var(--kgg-tablet-safe-top) - var(--kgg-tablet-safe-bottom))!important;
    }
    .scanHub{
      position:relative!important;
      z-index:80!important;
    }
    .tabletMenuBtn,
    body.tabletLayoutCustom .tabletMenuBtn{
      position:relative!important;
      top:auto!important;
      left:auto!important;
      z-index:1300!important;
      pointer-events:auto!important;
      touch-action:manipulation!important;
      align-self:center!important;
      justify-self:center!important;
    }
    body.tabletMenuOpen .tabletMenuBtn{
      position:fixed!important;
      top:calc(var(--kgg-tablet-safe-top) + 2px)!important;
      left:18px!important;
    }
    .tabletSideBackdrop{z-index:1200!important;}
    .tabletSideMenu{z-index:1210!important;}
    #createPanel.planMode .planActions{
      grid-column:2/4!important;
      grid-row:5!important;
      display:grid!important;
      grid-template-columns:minmax(0,1fr) minmax(0,1fr)!important;
      gap:12px!important;
      align-self:stretch!important;
      min-width:0!important;
    }
    #createPanel.planMode #recentToggle{
      grid-column:1!important;
      grid-row:1!important;
      align-self:stretch!important;
      justify-self:stretch!important;
      width:100%!important;
    }
    #createPanel.planMode .packageLayoutSlot{
      grid-column:3!important;
      grid-row:5!important;
      align-self:stretch!important;
      justify-self:stretch!important;
      width:100%!important;
    }
  }
  /* v382: automatic web update and Android APK update handoff. */
  @media (max-width:759px){
    #currentPlanBlock #planList.planList{
      gap:6px!important;
      margin:6px 0!important;
    }
    #currentPlanBlock .planCard{
      min-height:50px!important;
      padding:7px 8px!important;
      border-radius:14px!important;
      grid-template-columns:minmax(0,1fr) auto!important;
      gap:6px!important;
      align-items:center!important;
    }
    #currentPlanBlock .planCard .planMain{
      gap:6px!important;
      min-width:0!important;
      align-items:center!important;
    }
    #currentPlanBlock .planCard .drag{
      width:28px!important;
      min-width:28px!important;
      height:36px!important;
      min-height:36px!important;
      padding:0!important;
      margin:0!important;
      border-radius:10px!important;
      font-size:16px!important;
      line-height:1!important;
    }
    #currentPlanBlock .planThumb{
      width:30px!important;
      min-width:30px!important;
      height:30px!important;
      border-radius:9px!important;
    }
    #currentPlanBlock .planCard .planText{
      gap:0!important;
      min-width:0!important;
    }
    #currentPlanBlock .planCard .planText b{
      flex-wrap:nowrap!important;
      gap:3px!important;
      min-width:0!important;
      font-size:16px!important;
      line-height:1.12!important;
    }
    #currentPlanBlock .planIndex,
    #currentPlanBlock .planBadges{
      flex:0 0 auto!important;
    }
    #currentPlanBlock .planName{
      min-width:0!important;
      overflow:hidden!important;
      overflow-wrap:normal!important;
      text-overflow:ellipsis!important;
      white-space:nowrap!important;
    }
    #currentPlanBlock .planMetaLine{
      display:block!important;
      margin-top:1px!important;
      color:#637083!important;
      font-size:12px!important;
      line-height:1.12!important;
      overflow:hidden!important;
      text-overflow:ellipsis!important;
      white-space:nowrap!important;
    }
    #currentPlanBlock .planCardActions{
      gap:1px!important;
      padding-right:18px!important;
    }
    #currentPlanBlock .planCardActions .iconBtn[data-planedit]{
      width:36px!important;
      min-width:36px!important;
      height:36px!important;
      min-height:36px!important;
      padding:0!important;
      border-radius:999px!important;
      font-size:16px!important;
      box-shadow:0 1px 5px rgba(7,16,39,.06)!important;
    }
    #currentPlanBlock .planDeleteBtn{
      top:4px!important;
      right:5px!important;
      width:24px!important;
      min-width:24px!important;
      height:24px!important;
      min-height:24px!important;
      border:0!important;
      background:transparent!important;
      box-shadow:none!important;
      font-size:18px!important;
      opacity:.58!important;
    }
    #editorModal .editorSheet{
      max-height:calc(100dvh - 18px)!important;
      overflow:auto!important;
      padding:14px 14px calc(14px + env(safe-area-inset-bottom))!important;
      border-radius:22px 22px 0 0!important;
      scroll-padding-bottom:14px!important;
    }
    #editorModal .editorHeader{
      gap:8px!important;
      margin-bottom:8px!important;
    }
    #editorModal .editorHeader h2{
      font-size:22px!important;
      line-height:1.05!important;
    }
    #editorModal .editorDeleteBtn{
      width:34px!important;
      min-width:34px!important;
      height:34px!important;
      min-height:34px!important;
      border-radius:11px!important;
      font-size:17px!important;
      box-shadow:none!important;
      opacity:.78!important;
    }
    #editorModal .grid2{
      gap:7px!important;
    }
    #editorModal .field{
      gap:3px!important;
      margin:4px 0!important;
    }
    #editorModal .field label{
      font-size:11px!important;
      line-height:1.1!important;
    }
    #editorModal .field input,
    #editorModal .field select{
      min-height:44px!important;
      height:44px!important;
      border-radius:11px!important;
      padding:8px 10px!important;
      font-size:15px!important;
    }
    #editorModal .editorStartHint{
      margin-top:8px!important;
      padding:10px!important;
      border-radius:14px!important;
    }
    #editorModal .editorStartHint>b{
      display:block!important;
      margin-bottom:5px!important;
      font-size:15px!important;
      line-height:1.1!important;
    }
    #editorModal .editorStartGrid{
      gap:7px!important;
      margin-top:0!important;
    }
    #editorModal .editorMediaBox{
      display:grid!important;
      grid-template-columns:auto minmax(0,1fr) auto!important;
      align-items:center!important;
      gap:8px!important;
      margin-top:8px!important;
      padding:8px 10px!important;
      border-radius:14px!important;
    }
    #editorModal .editorMediaHead{
      display:contents!important;
    }
    #editorModal .editorMediaHead b{
      grid-column:1!important;
      font-size:16px!important;
      line-height:1!important;
      white-space:nowrap!important;
    }
    #editorModal .editorMediaStatus{
      grid-column:2!important;
      display:block!important;
      min-width:0!important;
      margin:0!important;
      font-size:12px!important;
      line-height:1.15!important;
      overflow:hidden!important;
      text-overflow:ellipsis!important;
      white-space:nowrap!important;
    }
    #editorModal .editorMediaActions{
      grid-column:3!important;
      display:flex!important;
      justify-content:flex-end!important;
      gap:6px!important;
    }
    #editorModal .editorMediaActions button{
      min-height:42px!important;
      border-radius:12px!important;
      padding:0 11px!important;
      font-size:14px!important;
      white-space:nowrap!important;
    }
    #editorModal .editorMediaPreview:not(.hidden){
      grid-column:1/-1!important;
      min-height:54px!important;
      margin-top:2px!important;
      border-radius:12px!important;
    }
    #editorModal .editorMediaPreview img{
      max-height:84px!important;
      object-fit:cover!important;
    }
    #editorModal .editorAdvanced{
      margin-top:8px!important;
      padding:0!important;
      border-radius:14px!important;
      overflow:hidden!important;
    }
    #editorModal .editorAdvanced summary{
      min-height:44px!important;
      padding:0 12px!important;
      align-items:center!important;
      justify-content:space-between!important;
      list-style:none!important;
      cursor:pointer!important;
    }
    #editorModal .editorAdvanced summary::-webkit-details-marker{
      display:none!important;
    }
    #editorModal .editorAdvanced summary::after{
      content:"▾";
      color:#071027;
      font-size:18px;
      line-height:1;
    }
    #editorModal .editorAdvanced[open]{
      padding-bottom:10px!important;
    }
    #editorModal .editorAdvanced[open] summary::after{
      transform:rotate(180deg);
    }
    #editorModal .editorAdvancedGrid{
      grid-template-columns:1fr!important;
      gap:6px!important;
      margin:0 10px!important;
    }
    #editorModal .editorActions{
      gap:6px!important;
      margin-top:10px!important;
    }
    #editorModal .editorActions button{
      min-height:46px!important;
      border-radius:13px!important;
      font-size:16px!important;
    }
    #editorModal .editorCancelBtn{
      min-height:42px!important;
      margin-top:6px!important;
      border:0!important;
      background:transparent!important;
      box-shadow:none!important;
      font-size:15px!important;
    }
  }
```
