# KGG Source Chunk 009

- Source: `kgg-update/index.html`
- Lines: 3781-4200

```html
      body.tabletLayoutRightTiny #recentToggle .recentMini{
        font-size:0!important;
      }
      body.tabletLayoutRightTiny #packageToggle > span::before{
        content:"\1F4E6";
        font-size:22px;
      }
      body.tabletLayoutRightTiny #finishBtn{
        font-size:0!important;
      }
      body.tabletLayoutRightTiny #finishBtn::before{
        content:"OK";
        font-size:18px;
      }
      body.tabletLayoutRightTiny #baseToggle > span:first-child{
        font-size:0!important;
      }
      body.tabletLayoutRightTiny #baseToggle > span:first-child::before{
        content:"\25B6  \1F464";
        font-size:20px;
      }
    }

    /* v344 Tablet Scale/Fit:
       Der freie Tablet-Modus skaliert jetzt die ganze Arbeits-UI breiter,
       und Aktionsbuttons werden erst sehr spaet icon-only. */
    @media (min-width:760px){
      body.tabletLayoutCustom .app{
        grid-template-columns:minmax(24px,var(--kgg-tablet-left-col,42vw)) minmax(84px,1fr) minmax(44px,.72fr)!important;
      }
      body.tabletLayoutCustom :is(.panelTitle,#currentPlanToggle){
        font-size:clamp(10px,calc(30px * var(--kgg-tablet-ui-scale,1)),58px)!important;
        line-height:1.04!important;
      }
      body.tabletLayoutCustom :is(.scanBtn,.scanMeta.filePickBtn,#baseToggle,#finishBtn,#recentToggle,#packageToggle,.drawerBtn,.baseCard,.primary,.mutedBtn,.tabletLockSwitch){
        font-size:clamp(7px,calc(20px * var(--kgg-tablet-ui-scale,1)),40px)!important;
        line-height:1.08!important;
      }
      body.tabletLayoutCustom :is(.label,#currentPlanBlock .label,.dbTitle,.bankLabel,.suggestion){
        font-size:clamp(7px,calc(16px * var(--kgg-tablet-ui-scale,1)),34px)!important;
        line-height:1.1!important;
      }
      body.tabletLayoutCustom :is(textarea,#exerciseInput,#inputWrap textarea){
        font-size:clamp(8px,calc(23px * var(--kgg-tablet-ui-scale,1)),48px)!important;
        line-height:1.28!important;
        padding:clamp(6px,calc(16px * var(--kgg-tablet-ui-scale,1)),28px) clamp(28px,calc(46px * var(--kgg-tablet-ui-scale,1)),70px) clamp(6px,calc(16px * var(--kgg-tablet-ui-scale,1)),28px) clamp(6px,calc(14px * var(--kgg-tablet-ui-scale,1)),28px)!important;
      }
      body.tabletLayoutCustom .clearBtn{
        font-size:clamp(14px,calc(24px * var(--kgg-tablet-ui-scale,1)),44px)!important;
        padding:clamp(2px,calc(6px * var(--kgg-tablet-ui-scale,1)),12px)!important;
      }
      body.tabletLayoutCustom :is(.bankRow,.planCard){
        padding:clamp(4px,calc(12px * var(--kgg-tablet-ui-scale,1)),26px) clamp(5px,calc(14px * var(--kgg-tablet-ui-scale,1)),30px)!important;
        min-height:clamp(34px,calc(66px * var(--kgg-tablet-ui-scale,1)),132px)!important;
        border-radius:clamp(9px,calc(18px * var(--kgg-tablet-ui-scale,1)),34px)!important;
      }
      body.tabletLayoutCustom .bankRow{
        grid-template-columns:minmax(0,1fr) auto!important;
      }
      body.tabletLayoutCustom :is(.bankRow b,.planCard b){
        font-size:clamp(8px,calc(20px * var(--kgg-tablet-ui-scale,1)),40px)!important;
        line-height:1.08!important;
      }
      body.tabletLayoutCustom :is(.bankRow small,.planCard small,.recentMini,.drawerBtn .mini,.scanMeta small){
        font-size:clamp(6px,calc(12px * var(--kgg-tablet-ui-scale,1)),24px)!important;
        line-height:1.08!important;
      }
      body.tabletLayoutCustom :is(.iconBtn,.planCard .iconBtn){
        font-size:clamp(10px,calc(22px * var(--kgg-tablet-ui-scale,1)),42px)!important;
        padding:clamp(2px,calc(8px * var(--kgg-tablet-ui-scale,1)),16px)!important;
      }
      body.tabletLayoutCustom .planCard .drag{
        width:clamp(18px,calc(38px * var(--kgg-tablet-ui-scale,1)),76px)!important;
        height:clamp(18px,calc(38px * var(--kgg-tablet-ui-scale,1)),76px)!important;
        font-size:clamp(9px,calc(18px * var(--kgg-tablet-ui-scale,1)),36px)!important;
        margin-right:clamp(3px,calc(8px * var(--kgg-tablet-ui-scale,1)),16px)!important;
      }
      body.tabletLayoutCustom :is(.scanHub,.inner,#currentPlanBlock,#inputWrap,#bankArea.bankOpen,.baseCard,.drawerBtn){
        border-radius:clamp(10px,calc(20px * var(--kgg-tablet-ui-scale,1)),36px)!important;
      }
      body.tabletLayoutCustom .scanHub{
        padding:clamp(6px,calc(14px * var(--kgg-tablet-ui-scale,1)),26px)!important;
      }
      body.tabletLayoutCustom #currentPlanBlock{
        padding:clamp(6px,calc(14px * var(--kgg-tablet-ui-scale,1)),28px)!important;
      }
      body.tabletLayoutCustom :is(.scanHub .scanBtn,.scanHub .scanMeta,#baseToggle,#finishBtn,#recentToggle,#packageToggle){
        min-height:clamp(34px,calc(62px * var(--kgg-tablet-ui-scale,1)),118px)!important;
        height:auto!important;
        padding:clamp(5px,calc(12px * var(--kgg-tablet-ui-scale,1)),24px)!important;
      }
      body.tabletLayoutCustom #bankArea.bankOpen.alphaBankOpen .az{
        display:flex!important;
        flex-direction:column!important;
        justify-content:space-between!important;
        height:calc(100% - 58px)!important;
        padding:3px 0 14px!important;
        box-sizing:border-box!important;
        overflow:visible!important;
      }
      body.tabletLayoutCustom #bankArea.bankOpen.alphaBankOpen .az button,
      body.tabletLayoutCustom .az button{
        flex:1 1 0!important;
        min-height:0!important;
        line-height:1!important;
        font-size:clamp(6px,calc(12px * var(--kgg-tablet-ui-scale,1)),22px)!important;
      }
      .packageLayoutSlot{
        grid-template-columns:minmax(84px,1fr) minmax(74px,88px)!important;
        align-items:stretch!important;
      }
      .packageLayoutSlot #packageToggle,
      .packageLayoutSlot .tabletLayoutControls{
        height:auto!important;
        min-height:clamp(48px,calc(66px * var(--kgg-tablet-ui-scale,1)),112px)!important;
      }
      .packageLayoutSlot #packageToggle > span,
      #recentToggle .recentText,
      #recentToggle .recentMini{
        max-width:100%!important;
        opacity:1!important;
        white-space:normal!important;
        overflow:hidden!important;
        text-overflow:ellipsis!important;
      }
      body.tabletLayoutRightSlim .packageLayoutSlot{
        grid-template-columns:minmax(72px,1fr) minmax(64px,76px)!important;
        gap:6px!important;
      }
      body.tabletLayoutRightSlim #packageToggle > span,
      body.tabletLayoutRightSlim #recentToggle .recentText{
        font-size:clamp(8px,calc(15px * var(--kgg-tablet-ui-scale,1)),26px)!important;
        line-height:1.02!important;
      }
      body.tabletLayoutRightTiny .packageLayoutSlot{
        grid-template-columns:minmax(44px,1fr) 48px!important;
        gap:4px!important;
      }
      body.tabletLayoutRightTiny #packageToggle > span,
      body.tabletLayoutRightTiny #recentToggle .recentText,
      body.tabletLayoutRightTiny #recentToggle .recentMini{
        font-size:0!important;
      }
      body.tabletLayoutRightTiny #packageToggle > span::before{
        content:"\1F4E6";
        font-size:22px;
      }
      .tabletLayoutFreeTools{
        width:94px!important;
        padding:12px 10px!important;
        border-radius:34px!important;
      }
      .tabletLayoutFreeTools button{
        width:74px!important;
        height:58px!important;
        min-height:58px!important;
        font-size:38px!important;
        border-radius:26px!important;
      }
      .tabletScaleValue{
        min-height:92px!important;
        font-size:15px!important;
      }
      .tabletLayoutFreeTools::before{
        top:82px!important;
        bottom:82px!important;
      }
      .tabletLayoutResizeHandle{
        width:70px!important;
        background:
          radial-gradient(circle at 50% 18px,rgba(7,16,39,.38) 0 8px,rgba(255,255,255,.98) 9px 16px,transparent 17px),
          radial-gradient(circle at 50% calc(100% - 18px),rgba(7,16,39,.38) 0 8px,rgba(255,255,255,.98) 9px 16px,transparent 17px),
          linear-gradient(180deg,rgba(7,16,39,.16),rgba(7,16,39,.42),rgba(7,16,39,.16)) center/6px calc(100% - 30px) no-repeat!important;
      }
      .tabletLayoutResizeHandle::before{
        width:36px!important;
        height:112px!important;
        box-shadow:0 16px 40px rgba(7,16,39,.18),0 0 0 1px rgba(200,209,220,.96) inset!important;
      }
      .tabletLayoutResizeHandle::after{
        width:18px!important;
        height:68px!important;
      }
    }

    /* v345 Tablet Reset/Spacing:
       Freies Layout bekommt echte Mindestabstaende, gleich hohe Button-Zeilen,
       skalierende Popups und eine laengere Scale-Schiene mit Reset. */
    @media (min-width:760px){
      body.tabletLayoutCustom{
        --kgg-tablet-live-gap:clamp(8px,calc(14px * var(--kgg-tablet-ui-scale,1)),24px);
      }
      body.tabletLayoutCustom .app{
        grid-template-rows:auto minmax(clamp(58px,calc(68px * var(--kgg-tablet-ui-scale,1)),122px),auto) minmax(clamp(92px,calc(126px * var(--kgg-tablet-ui-scale,1)),220px),auto) minmax(0,1fr) minmax(clamp(54px,calc(64px * var(--kgg-tablet-ui-scale,1)),112px),auto)!important;
        gap:var(--kgg-tablet-live-gap)!important;
        column-gap:var(--kgg-tablet-live-gap)!important;
        row-gap:var(--kgg-tablet-live-gap)!important;
        align-items:stretch!important;
      }
      body.tabletLayoutCustom :is(.scanHub,#inputWrap,#bankArea,#baseToggle,#rightPlanStack,#currentPlanBlock,#recentToggle,#packageToggle,.packageLayoutSlot){
        min-width:0!important;
        box-sizing:border-box!important;
      }
      body.tabletLayoutCustom .scanHub{
        display:grid!important;
        grid-template-columns:repeat(auto-fit,minmax(clamp(78px,calc(150px * var(--kgg-tablet-ui-scale,1)),260px),1fr))!important;
        grid-auto-rows:minmax(clamp(44px,calc(62px * var(--kgg-tablet-ui-scale,1)),104px),auto)!important;
        gap:var(--kgg-tablet-live-gap)!important;
        align-content:start!important;
        align-self:stretch!important;
        overflow:visible!important;
        z-index:35!important;
      }
      body.tabletLayoutCustom .scanHub :is(.scanBtn,.scanMeta,.adminConfigBtn,.sharedBankBtn){
        grid-row:auto!important;
        height:auto!important;
        min-height:clamp(44px,calc(62px * var(--kgg-tablet-ui-scale,1)),104px)!important;
        align-self:stretch!important;
        justify-content:center!important;
        text-align:center!important;
        white-space:normal!important;
        overflow:hidden!important;
        text-overflow:ellipsis!important;
        padding:clamp(5px,calc(10px * var(--kgg-tablet-ui-scale,1)),18px)!important;
      }
      body.tabletLayoutCustom .scanHub .adminConfigBtn,
      body.tabletLayoutCustom .scanHub .sharedBankBtn{
        display:flex!important;
        margin:0!important;
      }
      body.tabletLayoutCustom:not(.adminMode) .scanHub .adminConfigBtn,
      body.tabletLayoutCustom:not(.adminMode) .scanHub .sharedBankBtn{
        display:none!important;
      }
      body.tabletLayoutCustom #baseToggle{
        overflow:hidden!important;
        z-index:20!important;
      }
      body.tabletLayoutCustom #inputWrap{
        z-index:18!important;
      }
      body.tabletLayoutCollisionTight .scanHub{
        grid-template-columns:repeat(auto-fit,minmax(62px,1fr))!important;
        gap:8px!important;
      }
      body.tabletLayoutCollisionTight .scanHub :is(.scanBtn,.scanMeta,.adminConfigBtn,.sharedBankBtn),
      body.tabletLayoutCollisionTight #baseToggle{
        font-size:clamp(7px,calc(14px * var(--kgg-tablet-ui-scale,1)),24px)!important;
        line-height:1.02!important;
        padding:5px 7px!important;
      }
      body.tabletLayoutCustom .planActions{
        gap:var(--kgg-tablet-live-gap)!important;
        align-items:stretch!important;
      }
      body.tabletLayoutCustom #createPanel.planMode :is(#recentToggle,#packageToggle,#finishBtn),
      body.tabletLayoutCustom #createPanel:not(.planMode) :is(#recentToggle,#packageToggle){
        min-height:clamp(48px,calc(64px * var(--kgg-tablet-ui-scale,1)),112px)!important;
        height:auto!important;
        align-self:stretch!important;
        box-sizing:border-box!important;
      }
      body.tabletLayoutCustom #baseFields:not(.hidden),
      body.tabletLayoutCustom #recentList:not(.hidden),
      body.tabletLayoutCustom #packageList:not(.hidden),
      body.tabletLayoutCustom .sheet{
        font-size:clamp(11px,calc(16px * var(--kgg-tablet-ui-scale,1)),30px)!important;
        padding:clamp(10px,calc(16px * var(--kgg-tablet-ui-scale,1)),30px)!important;
        border-radius:clamp(16px,calc(24px * var(--kgg-tablet-ui-scale,1)),38px)!important;
      }
      body.tabletLayoutCustom #baseFields:not(.hidden) :is(input,select,textarea),
      body.tabletLayoutCustom .sheet :is(input,select,textarea,button),
      body.tabletLayoutCustom #recentList:not(.hidden) button,
      body.tabletLayoutCustom #packageList:not(.hidden) button{
        font-size:clamp(10px,calc(16px * var(--kgg-tablet-ui-scale,1)),30px)!important;
        min-height:clamp(38px,calc(48px * var(--kgg-tablet-ui-scale,1)),86px)!important;
      }
      .tabletLayoutFreeTools{
        width:106px!important;
        padding:14px 10px!important;
        gap:12px!important;
        border-radius:38px!important;
      }
      .tabletLayoutFreeTools button{
        width:84px!important;
        height:66px!important;
        min-height:66px!important;
        font-size:40px!important;
        border-radius:28px!important;
      }
      #tabletLayoutReset{
        height:54px!important;
        min-height:54px!important;
        font-size:30px!important;
        background:#fff!important;
        color:#38475b!important;
        border:1px solid rgba(220,227,235,.95)!important;
      }
      .tabletScaleValue{
        min-height:126px!important;
        font-size:15px!important;
      }
      .tabletLayoutFreeTools::before{
        top:92px!important;
        bottom:154px!important;
      }
      .tabletLayoutControls,
      .packageLayoutSlot .tabletLayoutControls{
        min-width:82px!important;
      }
      body.tabletLayoutRightTiny .tabletLayoutControls,
      body.tabletLayoutRightTiny .packageLayoutSlot .tabletLayoutControls{
        min-width:52px!important;
      }
    }

    /* v346 phone keyboard and drawer polish */
    @media (max-width:759px){
      body.phoneTextFocus{
        scroll-padding-bottom:calc(var(--kgg-phone-keyboard-inset,0px) + 170px);
      }
      body.phoneTextFocus #inputWrap{
        position:sticky;
        bottom:calc(var(--kgg-phone-keyboard-inset,0px) + 12px);
        z-index:74;
        transform:translateZ(0);
        box-shadow:0 14px 34px rgba(7,16,39,.16),0 0 0 1px rgba(220,227,235,.92);
        animation:phoneInputLift .18s cubic-bezier(.2,.75,.22,1) both;
      }
      body.phoneTextFocus #suggestion:not(.hidden),
      .suggestion:not(.hidden){
        transform-origin:top center;
        animation:phoneSuggestionIn .22s cubic-bezier(.2,.75,.22,1) both;
      }
      #bankArea.bankOpen{
        transform-origin:top center;
        animation:phoneBankShellIn .26s cubic-bezier(.18,.84,.24,1) both;
      }
      #bankArea.bankOpen #bankContent{
        transform-origin:top center;
        animation:phoneBankContentIn .28s cubic-bezier(.18,.84,.24,1) both!important;
      }
      #bankToggle.phoneButtonFloat,
      #recentToggle.phoneButtonFloat,
      #packageToggle.phoneButtonFloat{
        position:relative;
        z-index:90;
        transform-origin:center bottom;
        box-shadow:0 18px 38px rgba(7,16,39,.22),0 1px 0 rgba(255,255,255,.9) inset;
        animation:phoneButtonDockFloat .32s cubic-bezier(.2,.85,.22,1) both;
      }
      #recentList:not(.hidden),
      #packageList:not(.hidden){
        transform-origin:bottom center;
        animation:phoneDrawerFromButton .34s cubic-bezier(.18,.84,.24,1) both!important;
      }
      @keyframes phoneInputLift{
        0%{transform:translateY(10px) scale(.992);opacity:.98}
        100%{transform:translateY(0) scale(1);opacity:1}
      }
      @keyframes phoneSuggestionIn{
        0%{opacity:0;transform:translateY(-8px) scale(.985);filter:blur(1px)}
        100%{opacity:1;transform:translateY(0) scale(1);filter:blur(0)}
      }
      @keyframes phoneBankShellIn{
        0%{opacity:.92;transform:translateY(-6px) scale(.992)}
        100%{opacity:1;transform:translateY(0) scale(1)}
      }
      @keyframes phoneBankContentIn{
        0%{opacity:0;transform:translateY(-10px) scale(.985);clip-path:inset(0 0 100% 0 round 16px)}
        100%{opacity:1;transform:translateY(0) scale(1);clip-path:inset(0 0 0 0 round 16px)}
      }
      @keyframes phoneButtonDockFloat{
        0%{transform:translateY(0) scale(1)}
        55%{transform:translateY(10px) scale(1.035)}
        100%{transform:translateY(16px) scale(1.02)}
      }
      @keyframes phoneDrawerFromButton{
        0%{opacity:0;transform:translateY(34px) scale(.94);filter:blur(2px)}
        65%{opacity:1;transform:translateY(-3px) scale(1.01);filter:blur(0)}
        100%{opacity:1;transform:translateY(0) scale(1);filter:blur(0)}
      }
    }

    /* Composer state clarity */
    @media (max-width:759px){
      .bankArea.bankOpen.searchBankOpen{
        display:grid;
        grid-template-columns:56px minmax(0,1fr);
        column-gap:8px;
        align-items:start;
      }
      .bankArea.bankOpen.searchBankOpen #bankToggle{
        grid-column:1;
        grid-row:1;
      }
      .bankArea.bankOpen.searchBankOpen #bankContent{
        grid-column:2;
        grid-row:1;
        margin-top:0;
      }
      .bankArea.bankOpen.searchBankOpen .bankLabel{
        margin:0 0 4px;
        border-radius:10px;
      }
    }
    /* Tablet DB search: Top-Treffer beginnen neben dem Uebungsdatenbank-Maennchen. */
    @media (min-width:760px){
      #bankArea.bankOpen.searchBankOpen{
        display:grid;
        grid-template-columns:56px minmax(0,1fr);
        column-gap:8px;
        align-items:start;
        align-content:start;
        height:auto;
        min-height:0;
      }
      #bankArea.bankOpen.searchBankOpen #bankToggle{
        grid-column:1;
        grid-row:1;
```
