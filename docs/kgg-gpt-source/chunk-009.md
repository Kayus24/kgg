# KGG Source Chunk 009

- Source: `kgg-update/src` modular source
- Lines: 3781-4200

```html
        color:#fff!important;
        border:0!important;
        box-shadow:0 8px 18px rgba(7,16,39,.22)!important;
      }
      .tabletLayoutResizeHandle{
        width:42px!important;
        border:1px solid rgba(220,227,235,.95);
        border-radius:999px;
        background:linear-gradient(180deg,rgba(255,255,255,.96),rgba(245,248,252,.9));
        box-shadow:0 18px 42px rgba(7,16,39,.14),0 1px 0 rgba(255,255,255,.9) inset;
        backdrop-filter:blur(12px);
      }
      .tabletLayoutResizeHandle::before{
        left:50%!important;
        top:50%!important;
        bottom:auto!important;
        width:5px!important;
        height:84px!important;
        transform:translate(-50%,-50%)!important;
        background:linear-gradient(180deg,rgba(7,16,39,.18),rgba(94,167,232,.34),rgba(7,16,39,.18))!important;
        box-shadow:none!important;
      }
      .tabletLayoutResizeHandle::after{
        content:"";
        position:absolute;
        left:50%;
        top:50%;
        width:18px;
        height:104px;
        transform:translate(-50%,-50%);
        border-radius:999px;
        background:
          radial-gradient(circle at 50% 22%,rgba(7,16,39,.34) 0 2px,transparent 3px),
          radial-gradient(circle at 50% 50%,rgba(7,16,39,.28) 0 2px,transparent 3px),
          radial-gradient(circle at 50% 78%,rgba(7,16,39,.34) 0 2px,transparent 3px);
        pointer-events:none;
      }
      body.tabletLayoutDragging .tabletLayoutResizeHandle{
        box-shadow:0 24px 56px rgba(7,16,39,.2),0 0 0 5px rgba(94,167,232,.14)!important;
      }
    }

    /* v343 Tablet Collision Avoidance:
       Fix sperrt nur die Regler, gespeicherte Groesse/Breite bleibt sichtbar.
       Paket und Schloss stehen nebeneinander. */
    @media (min-width:760px){
      body.tabletLayoutCustom .app{
        grid-template-columns:minmax(40px,var(--kgg-tablet-left-col,42vw)) minmax(110px,1fr) minmax(52px,.72fr)!important;
      }
      body.tabletLayoutCustom #exerciseInput,
      body.tabletLayoutCustom #inputWrap textarea{
        font-size:clamp(10px,calc(23px * var(--kgg-tablet-ui-scale,1)),46px)!important;
      }
      body.tabletLayoutCustom .bankRow b,
      body.tabletLayoutCustom .planCard b{
        font-size:clamp(9px,calc(19px * var(--kgg-tablet-ui-scale,1)),38px)!important;
      }
      body.tabletLayoutCustom .bankRow small,
      body.tabletLayoutCustom .planCard small{
        font-size:clamp(8px,calc(13px * var(--kgg-tablet-ui-scale,1)),26px)!important;
      }
      body.tabletLayoutCustom .drawerBtn,
      body.tabletLayoutCustom .baseCard,
      body.tabletLayoutCustom .primary,
      body.tabletLayoutCustom .mutedBtn{
        font-size:clamp(10px,calc(18px * var(--kgg-tablet-ui-scale,1)),36px)!important;
      }
      .packageLayoutSlot{
        grid-column:3!important;
        grid-row:5!important;
        align-self:stretch!important;
        justify-self:stretch!important;
        min-width:0!important;
        display:grid!important;
        grid-template-columns:minmax(0,1fr) 82px!important;
        gap:10px!important;
      }
      #createPanel:not(.planMode) .packageLayoutSlot,
      #createPanel.planMode .packageLayoutSlot{
        grid-column:3!important;
        grid-row:5!important;
      }
      .packageLayoutSlot #packageToggle{
        grid-column:1!important;
        grid-row:1!important;
        width:100%!important;
        min-width:0!important;
        height:66px!important;
        min-height:66px!important;
        padding:8px 12px!important;
        justify-content:center!important;
      }
      .packageLayoutSlot .tabletLayoutControls{
        grid-column:2!important;
        grid-row:1!important;
        width:82px!important;
        min-width:82px!important;
        max-width:82px!important;
        height:66px!important;
        justify-self:stretch!important;
      }
      .packageLayoutSlot .tabletLockSwitch{
        border:1px solid rgba(220,227,235,.95)!important;
        background:linear-gradient(180deg,#fff,#f6f8fb)!important;
        box-shadow:0 8px 22px rgba(7,16,39,.12),0 1px 0 rgba(255,255,255,.9) inset!important;
      }
      body.tabletLayoutUnlocked .tabletLockSwitch{
        border-color:rgba(94,167,232,.7)!important;
        box-shadow:0 10px 26px rgba(94,167,232,.18),0 1px 0 rgba(255,255,255,.9) inset!important;
      }
      .tabletLayoutFreeTools{
        width:78px!important;
        padding:10px 8px!important;
      }
      .tabletLayoutFreeTools button{
        width:62px!important;
        height:62px!important;
        min-height:62px!important;
        font-size:34px!important;
      }
      .tabletScaleValue{
        min-height:74px!important;
        font-size:14px!important;
      }
      .tabletLayoutFreeTools::before{
        top:76px!important;
        bottom:76px!important;
      }
      .tabletLayoutResizeHandle{
        border:0!important;
        width:58px!important;
        border-radius:0!important;
        background:
          radial-gradient(circle at 50% 18px,rgba(7,16,39,.32) 0 7px,rgba(255,255,255,.96) 8px 14px,transparent 15px),
          radial-gradient(circle at 50% calc(100% - 18px),rgba(7,16,39,.32) 0 7px,rgba(255,255,255,.96) 8px 14px,transparent 15px),
          linear-gradient(180deg,rgba(7,16,39,.18),rgba(94,167,232,.42),rgba(7,16,39,.18)) center/5px calc(100% - 28px) no-repeat!important;
        box-shadow:none!important;
        backdrop-filter:none!important;
      }
      .tabletLayoutResizeHandle::before{
        left:50%!important;
        top:50%!important;
        width:30px!important;
        height:92px!important;
        transform:translate(-50%,-50%)!important;
        border-radius:999px!important;
        background:linear-gradient(180deg,rgba(255,255,255,.97),rgba(245,248,252,.92))!important;
        box-shadow:0 14px 34px rgba(7,16,39,.16),0 0 0 1px rgba(220,227,235,.9) inset!important;
      }
      .tabletLayoutResizeHandle::after{
        width:16px!important;
        height:58px!important;
        background:
          radial-gradient(circle at 50% 16%,rgba(7,16,39,.34) 0 2px,transparent 3px),
          radial-gradient(circle at 50% 50%,rgba(7,16,39,.28) 0 2px,transparent 3px),
          radial-gradient(circle at 50% 84%,rgba(7,16,39,.34) 0 2px,transparent 3px)!important;
      }
      body.tabletLayoutLeftSlim #bankToggle,
      body.tabletLayoutLeftSlim .scanHub .scanBtn,
      body.tabletLayoutLeftSlim .scanHub .scanMeta{
        border-radius:14px!important;
      }
      body.tabletLayoutRightSlim #finishBtn,
      body.tabletLayoutRightSlim #baseToggle,
      body.tabletLayoutRightSlim #recentToggle,
      body.tabletLayoutRightSlim #packageToggle,
      body.tabletLayoutRightSlim .tabletLockSwitch{
        padding-left:6px!important;
        padding-right:6px!important;
        border-radius:14px!important;
        font-size:clamp(10px,calc(14px * var(--kgg-tablet-ui-scale,1)),20px)!important;
      }
      body.tabletLayoutRightTiny .packageLayoutSlot{
        grid-template-columns:minmax(0,1fr) 52px!important;
        gap:4px!important;
      }
      body.tabletLayoutRightTiny .packageLayoutSlot .tabletLayoutControls{
        width:52px!important;
        min-width:52px!important;
        max-width:52px!important;
      }
      body.tabletLayoutRightTiny .tabletLockText,
      body.tabletLayoutRightTiny .tabletSwitchTrack{
        display:none!important;
      }
      body.tabletLayoutRightTiny .tabletLockIcon{
        font-size:22px!important;
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
```
