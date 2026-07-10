# KGG Source Chunk 007

- Source: `kgg-update/index.html`
- Lines: 2941-3360

```html

      #createPanel.planMode #currentPlanToggle{
        min-height:58px!important;
        font-size:22px!important;
        padding-left:14px!important;
      }
      #createPanel.planMode #currentPlanToggle > small{
        font-size:13px!important;
      }

      .planCard{
        padding:15px 17px!important;
        border-radius:18px!important;
      }
      .planCard b{
        font-size:19px!important;
      }
      .planCard small{
        font-size:12.5px!important;
      }
      .planCard .drag{
        width:36px!important;
        height:36px!important;
      }
      .planCard .iconBtn{
        font-size:19px!important;
      }

      #createPanel.planMode #recentToggle,
      #createPanel.planMode #packageToggle{
        height:66px!important;
        min-height:66px!important;
        font-size:19px!important;
      }
    }

    @media (min-width:760px) and (max-width:980px){
      .app{
        grid-template-columns:minmax(380px,450px) minmax(0,1.02fr) minmax(0,.9fr)!important;
        gap:16px!important;
      }
      #inputWrap textarea,
      #exerciseInput{
        font-size:21px!important;
      }
      .bankRow b{
        font-size:17px!important;
      }
      .planCard b{
        font-size:18px!important;
      }
      #createPanel.planMode #recentToggle,
      #createPanel.planMode #packageToggle{
        height:62px!important;
        min-height:62px!important;
      }
    }



    /* v335 Tablet Proportional Columns:
       Linke und rechte Arbeitszone proportionaler verteilen.
       Linke Spalte deutlich breiter, rechter Planbereich bleibt stabil.
       UI leicht größer für bessere Tablet-Lesbarkeit.
       Nur Tablet-CSS. Keine PDF/QR/Patienten-App/Scan/Parser/Plan-State-Logik. */
    @media (min-width:760px){
      .app{
        grid-template-columns:clamp(540px,42vw,660px) minmax(0,1fr) minmax(0,.72fr)!important;
        column-gap:14px!important;
        gap:14px!important;
        padding:16px!important;
      }

      .scanHub,
      #inputWrap,
      #bankArea{
        width:100%!important;
        max-width:none!important;
        justify-self:stretch!important;
      }

      #rightPlanStack,
      #currentPlanBlock,
      #scannedPlansBlock{
        min-width:0!important;
        width:100%!important;
      }

      .scanHub .scanBtn,
      .scanHub .scanMeta,
      #baseToggle,
      #finishBtn,
      #recentToggle,
      #packageToggle{
        font-size:20px!important;
      }
      #baseToggle,
      #finishBtn{
        min-height:64px!important;
        height:64px!important;
      }

      #exerciseInput,
      #inputWrap textarea{
        font-size:23px!important;
        line-height:1.36!important;
      }
      #exerciseInput{
        min-height:120px!important;
        max-height:180px!important;
      }

      #bankArea.bankOpen.alphaBankOpen .bankWithAz{
        grid-template-columns:68px minmax(0,1fr)!important;
        column-gap:12px!important;
      }
      #bankArea.bankOpen.alphaBankOpen .az{
        width:54px!important;
        margin-top:68px!important;
      }
      #bankArea.bankOpen.alphaBankOpen .az button,
      .az button{
        font-size:13px!important;
        min-height:20px!important;
      }
      .bankRow{
        padding:14px 16px!important;
        min-height:68px!important;
      }
      .bankRow b{
        font-size:19px!important;
      }
      .bankRow small{
        font-size:13px!important;
      }

      #createPanel.planMode #currentPlanToggle{
        min-height:60px!important;
        font-size:23px!important;
        padding-left:16px!important;
        padding-right:118px!important;
      }
      #createPanel.planMode #currentPlanToggle > small{
        font-size:13px!important;
      }

      #createPanel.planMode #savePackageBtn{
        width:86px!important;
        min-width:86px!important;
        max-width:86px!important;
        height:38px!important;
        min-height:38px!important;
        margin:12px 16px 0 0!important;
      }

      #currentPlanBlock .planCard,
      .planCard{
        padding:16px 18px!important;
        min-height:76px!important;
      }
      #currentPlanBlock .planCard b,
      .planCard b{
        font-size:20px!important;
      }
      #currentPlanBlock .planMetaLine,
      #currentPlanBlock .planSourceLine,
      .planCard small{
        font-size:13px!important;
      }
      .planCard .drag{
        width:38px!important;
        height:38px!important;
        min-width:38px!important;
      }
      .planCardActions .iconBtn[data-planedit]{
        width:44px!important;
        height:44px!important;
      }

      #createPanel.planMode #recentToggle,
      #createPanel.planMode #packageToggle{
        height:66px!important;
        min-height:66px!important;
        font-size:20px!important;
      }
    }

    @media (min-width:760px) and (max-width:1120px){
      .app{
        grid-template-columns:clamp(470px,43vw,560px) minmax(0,1fr) minmax(0,.78fr)!important;
        column-gap:12px!important;
        gap:12px!important;
        padding:14px!important;
      }
      #exerciseInput,
      #inputWrap textarea{
        font-size:22px!important;
      }
      .bankRow b{font-size:18px!important;}
      #currentPlanBlock .planCard b,
      .planCard b{font-size:19px!important;}
    }

    @media (min-width:760px) and (max-width:920px){
      .app{
        grid-template-columns:clamp(405px,45vw,470px) minmax(0,1fr) minmax(0,.82fr)!important;
        column-gap:10px!important;
        gap:10px!important;
        padding:10px!important;
      }
      #exerciseInput,
      #inputWrap textarea{
        font-size:21px!important;
      }
      #bankArea.bankOpen.alphaBankOpen .bankWithAz{
        grid-template-columns:58px minmax(0,1fr)!important;
      }
      #bankArea.bankOpen.alphaBankOpen .az{
        width:46px!important;
      }
      .bankRow{min-height:62px!important;padding:12px 14px!important;}
      .bankRow b{font-size:17px!important;}
      #currentPlanBlock .planCard,
      .planCard{min-height:68px!important;padding:13px 15px!important;}
      #currentPlanBlock .planCard b,
      .planCard b{font-size:18px!important;}
      #createPanel.planMode #currentPlanToggle{font-size:21px!important;}
    }

    .tabletLayoutControls,.tabletLayoutResizeHandle{display:none}
    @media (min-width:760px){
      .tabletLayoutControls{
        position:fixed;
        top:16px;
        right:18px;
        z-index:96;
        display:flex;
        align-items:center;
        gap:8px;
        padding:6px;
        border:1px solid rgba(220,227,235,.95);
        border-radius:16px;
        background:rgba(255,255,255,.94);
        box-shadow:0 10px 28px rgba(7,16,39,.14);
      }
      .tabletLayoutControls button{
        min-height:38px;
        border-radius:12px;
        border:1px solid rgba(220,227,235,.95);
        background:#fff;
        color:#071027;
        font-weight:1000;
        padding:0 12px;
      }
      .tabletLockSwitch{
        display:flex;
        align-items:center;
        gap:8px;
        min-width:112px;
      }
      .tabletLockIcon{
        width:18px;
        text-align:center;
      }
      .tabletSwitchTrack{
        position:relative;
        width:40px;
        height:22px;
        border-radius:999px;
        background:#071027;
        box-shadow:inset 0 0 0 1px rgba(7,16,39,.22);
      }
      .tabletSwitchKnob{
        position:absolute;
        left:3px;
        top:3px;
        width:16px;
        height:16px;
        border-radius:999px;
        background:#fff;
        box-shadow:0 2px 6px rgba(7,16,39,.24);
        transition:transform .2s ease;
      }
      body.tabletLayoutUnlocked .tabletSwitchTrack{background:#e9eef5}
      body.tabletLayoutUnlocked .tabletSwitchKnob{transform:translateX(18px);background:#071027}
      .tabletLockText{
        min-width:28px;
        font-size:12px;
        font-weight:1000;
      }
      .tabletLayoutFreeTools{
        display:none;
        align-items:center;
        gap:6px;
      }
      body.tabletLayoutUnlocked .tabletLayoutFreeTools{display:flex}
      .tabletScaleValue{
        min-width:48px;
        text-align:center;
        color:#38475b;
        font-size:12px;
        font-weight:1000;
      }
      .tabletLayoutResizeHandle{
        position:fixed;
        z-index:95;
        width:26px;
        min-height:160px;
        cursor:col-resize;
        touch-action:none;
      }
      .tabletLayoutResizeHandle::before{
        content:"";
        position:absolute;
        left:11px;
        top:0;
        bottom:0;
        width:4px;
        border-radius:999px;
        background:rgba(7,16,39,.18);
        box-shadow:0 0 0 8px rgba(94,167,232,.10);
      }
      body.tabletLayoutUnlocked .tabletLayoutResizeHandle{display:block}
      body.tabletLayoutDragging .tabletLayoutResizeHandle::before{
        background:rgba(7,16,39,.34);
        box-shadow:0 0 0 10px rgba(94,167,232,.16);
      }
      body.tabletLayoutCustom .app{
        grid-template-columns:clamp(320px,var(--kgg-tablet-left-col,42vw),720px) minmax(0,1fr) minmax(0,.72fr)!important;
      }
      body.tabletLayoutCustom #exerciseInput,
      body.tabletLayoutCustom #inputWrap textarea{
        font-size:calc(23px * var(--kgg-tablet-ui-scale,1))!important;
      }
      body.tabletLayoutCustom .bankRow b,
      body.tabletLayoutCustom .planCard b{
        font-size:calc(19px * var(--kgg-tablet-ui-scale,1))!important;
      }
      body.tabletLayoutCustom .bankRow small,
      body.tabletLayoutCustom .planCard small{
        font-size:calc(13px * var(--kgg-tablet-ui-scale,1))!important;
      }
      body.tabletLayoutCustom .drawerBtn,
      body.tabletLayoutCustom .baseCard,
      body.tabletLayoutCustom .primary,
      body.tabletLayoutCustom .mutedBtn{
        font-size:calc(18px * var(--kgg-tablet-ui-scale,1))!important;
      }
      body.adminMode .adminTestBanner{display:none!important}
      body.adminMode .scanHub .adminConfigBtn,
      body.adminMode .scanHub .sharedBankBtn{
        display:flex!important;
        margin:0;
        min-height:58px;
        align-items:center;
        justify-content:center;
      }
      body.adminMode .scanHub{
        grid-template-columns:minmax(150px,1fr) minmax(150px,1fr) minmax(140px,.8fr) minmax(170px,1fr)!important;
      }
    }

    /* v341 Tablet Layout Controls:
       Schloss teilt sich den Paketbereich, freie Tools liegen als rechte Vertikalleiste. */
    @media (min-width:760px){
      body.tabletLayoutCustom .app{
        grid-template-columns:minmax(140px,var(--kgg-tablet-left-col,42vw)) minmax(180px,1fr) minmax(84px,.72fr)!important;
      }
      .tabletLayoutControls{
        position:relative!important;
        top:auto!important;
        right:auto!important;
        grid-column:3!important;
        grid-row:5!important;
        align-self:stretch!important;
        justify-self:end!important;
        display:flex!important;
        width:78px!important;
        min-width:78px!important;
        max-width:78px!important;
        height:66px!important;
        min-height:0!important;
        padding:0!important;
        gap:0!important;
        border:0!important;
        border-radius:18px!important;
        background:transparent!important;
        box-shadow:none!important;
        z-index:36!important;
        pointer-events:none;
      }
      .tabletLayoutControls .tabletLockSwitch{
        pointer-events:auto;
        width:100%!important;
        height:100%!important;
        min-width:0!important;
        min-height:0!important;
        display:flex!important;
        flex-direction:column!important;
        align-items:center!important;
        justify-content:center!important;
        gap:2px!important;
        padding:5px 4px!important;
        border-radius:18px!important;
        background:#fff!important;
        box-shadow:0 2px 10px rgba(7,16,39,.075)!important;
      }
      .tabletLockIcon{
        width:auto!important;
        min-width:0!important;
        font-size:18px!important;
        line-height:1!important;
      }
      .tabletSwitchTrack{
        width:34px!important;
        height:18px!important;
      }
      .tabletSwitchKnob{
        width:12px!important;
        height:12px!important;
```
