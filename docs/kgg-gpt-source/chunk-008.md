# KGG Source Chunk 008

- Source: `kgg-update/index.html`
- Lines: 3361-3780

```html
        position:fixed!important;
        right:12px!important;
        top:50%!important;
        transform:translateY(-50%)!important;
        display:none!important;
        flex-direction:column!important;
        align-items:center!important;
        gap:8px!important;
        width:54px!important;
        padding:8px 6px!important;
        border:1px solid rgba(220,227,235,.95)!important;
        border-radius:999px!important;
        background:rgba(255,255,255,.96)!important;
        box-shadow:0 14px 36px rgba(7,16,39,.16)!important;
        z-index:98!important;
        pointer-events:auto;
        touch-action:none;
      }
      body.tabletLayoutUnlocked .tabletLayoutFreeTools{
        display:flex!important;
      }
      .tabletLayoutFreeTools button{
        width:42px!important;
        height:42px!important;
        min-height:42px!important;
        padding:0!important;
        border-radius:999px!important;
        font-size:24px!important;
        line-height:1!important;
      }
      .tabletScaleValue{
        min-width:0!important;
        min-height:54px!important;
        writing-mode:vertical-rl;
        transform:rotate(180deg);
        font-size:11px!important;
        line-height:1!important;
      }
      .tabletLayoutResizeHandle{
        width:34px!important;
      }
      .tabletLayoutResizeHandle::before{
        left:15px!important;
        width:3px!important;
        box-shadow:0 0 0 12px rgba(94,167,232,.08)!important;
      }
      .planCard,
      .bankRow,
      .baseCard,
      .drawerBtn,
      .primary,
      .mutedBtn,
      .tabletLockSwitch,
      #currentPlanBlock,
      #rightPlanStack{
        min-width:0!important;
      }
      .planCard b,
      .bankRow b,
      .planCard small,
      .bankRow small{
        overflow-wrap:anywhere;
      }
      .app.softKeyboard .tabletLayoutControls,
      .app.softKeyboard .tabletLayoutFreeTools{
        display:none!important;
      }
    }

    @media (min-width:760px) and (max-width:920px){
      .tabletLayoutControls{
        width:68px!important;
        min-width:68px!important;
        max-width:68px!important;
        height:58px!important;
      }
      #createPanel:not(.planMode) #packageToggle,
      #createPanel.planMode #packageToggle{
        padding-right:80px!important;
      }
      .tabletLockText{
        font-size:9px!important;
      }
      .tabletLayoutFreeTools{
        right:8px!important;
        width:50px!important;
      }
      .tabletLayoutFreeTools button{
        width:38px!important;
        height:38px!important;
        min-height:38px!important;
      }
    }

    /* v342 Tablet Free Layout:
       Extrem schmale freie Spalten clippen/adaptieren statt Nachbarbereiche zu uebermalen.
       Scale-Rail und Resize-Rail bekommen denselben ruhigen Floating-Stil. */
    @media (min-width:760px){
      body.tabletLayoutCustom .app{
        grid-template-columns:minmax(40px,var(--kgg-tablet-left-col,42vw)) minmax(110px,1fr) minmax(52px,.72fr)!important;
      }
      body.tabletLayoutCustom .scanHub,
      body.tabletLayoutCustom #inputWrap,
      body.tabletLayoutCustom #bankArea,
      body.tabletLayoutCustom #currentPlanBlock,
      body.tabletLayoutCustom .baseCard,
      body.tabletLayoutCustom .drawerBtn,
      body.tabletLayoutCustom .primary,
      body.tabletLayoutCustom .mutedBtn{
        min-width:0!important;
        max-width:100%!important;
        overflow:hidden!important;
        contain:layout paint;
      }
      body.tabletLayoutCustom .scanHub .scanBtn,
      body.tabletLayoutCustom .scanHub .scanMeta,
      body.tabletLayoutCustom #bankToggle,
      body.tabletLayoutCustom #baseToggle,
      body.tabletLayoutCustom #recentToggle,
      body.tabletLayoutCustom #packageToggle,
      body.tabletLayoutCustom #finishBtn{
        white-space:nowrap;
        text-overflow:ellipsis;
        overflow:hidden;
      }
      body.tabletLayoutLeftSlim .scanHub .scanBtn,
      body.tabletLayoutLeftSlim .scanHub .scanMeta,
      body.tabletLayoutLeftSlim #bankToggle{
        padding-left:6px!important;
        padding-right:6px!important;
        font-size:clamp(11px,calc(15px * var(--kgg-tablet-ui-scale,1)),17px)!important;
      }
      body.tabletLayoutLeftSlim #exerciseInput,
      body.tabletLayoutLeftSlim #inputWrap textarea{
        padding-left:8px!important;
        padding-right:30px!important;
        font-size:clamp(12px,calc(17px * var(--kgg-tablet-ui-scale,1)),21px)!important;
      }
      body.tabletLayoutLeftSlim .clearBtn{
        right:2px!important;
        top:4px!important;
      }
      body.tabletLayoutLeftTiny .scanHub{
        gap:4px!important;
      }
      body.tabletLayoutLeftTiny .scanHub .scanBtn,
      body.tabletLayoutLeftTiny .scanHub .scanMeta{
        font-size:0!important;
        padding:0!important;
      }
      body.tabletLayoutLeftTiny .scanHub .scanBtn::before{
        content:"\1F4F7";
        font-size:20px;
      }
      body.tabletLayoutLeftTiny .scanHub .scanMeta::before{
        content:"\1F5BC";
        font-size:18px;
      }
      body.tabletLayoutLeftTiny .scanHub .scanMeta small,
      body.tabletLayoutLeftTiny #bankToggle .dbToggleText,
      body.tabletLayoutLeftTiny .bankRow small{
        display:none!important;
      }
      body.tabletLayoutLeftTiny #bankArea.bankOpen{
        padding:5px!important;
        border-radius:16px!important;
      }
      body.tabletLayoutLeftTiny #bankArea.bankOpen #bankContent{
        margin-top:4px!important;
      }
      body.tabletLayoutLeftTiny #bankArea.bankOpen.alphaBankOpen .bankWithAz{
        grid-template-columns:24px minmax(0,1fr)!important;
        column-gap:3px!important;
      }
      body.tabletLayoutLeftTiny #bankArea.bankOpen.alphaBankOpen .az{
        width:22px!important;
        margin-top:48px!important;
        padding:2px 0!important;
      }
      body.tabletLayoutLeftTiny #bankArea.bankOpen.alphaBankOpen .az button{
        font-size:8px!important;
        min-height:13px!important;
      }
      body.tabletLayoutLeftTiny .bankRow{
        grid-template-columns:minmax(0,1fr)!important;
        min-height:42px!important;
        padding:6px 4px!important;
      }
      body.tabletLayoutLeftTiny .bankRow [data-edit]{
        display:none!important;
      }
      body.tabletLayoutLeftTiny .bankRow b{
        display:block;
        font-size:11px!important;
        line-height:1.05!important;
        overflow:hidden;
        text-overflow:ellipsis;
      }
      body.tabletLayoutScaleHuge .drawerBtn > span,
      body.tabletLayoutScaleHuge .baseCard > span,
      body.tabletLayoutScaleHuge .primary,
      body.tabletLayoutScaleHuge .mutedBtn{
        white-space:normal!important;
        line-height:1.05!important;
      }
      .tabletLayoutFreeTools{
        overflow:hidden!important;
        background:linear-gradient(180deg,rgba(255,255,255,.98),rgba(245,248,252,.95))!important;
        box-shadow:0 18px 42px rgba(7,16,39,.18),0 1px 0 rgba(255,255,255,.9) inset!important;
        backdrop-filter:blur(12px);
      }
      .tabletLayoutFreeTools::before{
        content:"";
        position:absolute;
        left:50%;
        top:54px;
        bottom:54px;
        width:4px;
        transform:translateX(-50%);
        border-radius:999px;
        background:linear-gradient(180deg,rgba(7,16,39,.12),rgba(94,167,232,.22),rgba(7,16,39,.12));
        pointer-events:none;
      }
      .tabletLayoutFreeTools button,
      .tabletScaleValue{
        position:relative;
        z-index:1;
      }
      .tabletLayoutFreeTools button{
        background:#071027!important;
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
```
