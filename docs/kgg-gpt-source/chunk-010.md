# KGG Source Chunk 010

- Source: `kgg-update/src` modular source
- Lines: 4201-4620

```html
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
      }
      #bankArea.bankOpen.searchBankOpen #bankContent{
        grid-column:2;
        grid-row:1;
        flex:none;
        height:auto;
        min-height:0;
        margin-top:0;
        overflow:visible;
      }
      #bankArea.bankOpen.searchBankOpen .bankLabel{
        margin:0 0 4px;
        border-radius:10px;
      }
      #bankArea.bankOpen.searchBankOpen .bankRows{
        max-height:min(46vh,440px);
        height:auto;
        overflow:auto;
      }
    }
    .planCard.is-live-draft{
      border-style:dashed;
      background:#fffdf5;
      box-shadow:0 0 0 2px rgba(242,211,138,.32) inset,0 6px 18px rgba(7,16,39,.05);
    }
    .planCard.is-live-draft .planIndex{
      display:none;
    }
    .planCard.is-live-draft .drag,
    .planCard.is-live-draft [data-planedit],
    .planCard.is-live-draft [data-plandel]{
      opacity:.55;
    }
    .planBadge.live{
      background:#fff8e8;
      color:#72490a;
      border-color:#f2d38a;
    }

    /* Tablet plan action row cleanup:
       With exercises in the plan, history/package/layout lock stay in one calm row. */
    @media (min-width:760px){
      #createPanel.planMode{
        --kgg-plan-action-h:clamp(56px,calc(64px * var(--kgg-tablet-ui-scale,1)),128px);
      }
      #createPanel.planMode .planActions{
        grid-column:2!important;
        grid-row:5!important;
        display:contents!important;
      }
      #createPanel.planMode #recentToggle{
        grid-column:2!important;
        grid-row:5!important;
        align-self:start!important;
        justify-self:stretch!important;
        width:100%!important;
        min-width:0!important;
        height:var(--kgg-plan-action-h)!important;
        min-height:var(--kgg-plan-action-h)!important;
        max-height:var(--kgg-plan-action-h)!important;
        padding:8px 14px!important;
        border-radius:18px!important;
        box-sizing:border-box!important;
        overflow:hidden!important;
      }
      #createPanel.planMode .packageLayoutSlot{
        grid-column:3!important;
        grid-row:5!important;
        align-self:start!important;
        justify-self:stretch!important;
        width:100%!important;
        min-width:0!important;
        height:var(--kgg-plan-action-h)!important;
        min-height:var(--kgg-plan-action-h)!important;
        max-height:var(--kgg-plan-action-h)!important;
        display:grid!important;
        grid-template-columns:minmax(0,1fr) minmax(72px,82px)!important;
        gap:10px!important;
        box-sizing:border-box!important;
        overflow:visible!important;
      }
      #createPanel.planMode .packageLayoutSlot #packageToggle{
        grid-column:1!important;
        grid-row:1!important;
        width:100%!important;
        min-width:0!important;
        height:var(--kgg-plan-action-h)!important;
        min-height:var(--kgg-plan-action-h)!important;
        max-height:var(--kgg-plan-action-h)!important;
        padding:8px 12px!important;
        justify-content:center!important;
        box-sizing:border-box!important;
      }
      #createPanel.planMode .packageLayoutSlot .tabletLayoutControls{
        grid-column:2!important;
        grid-row:1!important;
        align-self:stretch!important;
        justify-self:stretch!important;
        width:auto!important;
        min-width:72px!important;
        max-width:82px!important;
        height:var(--kgg-plan-action-h)!important;
        min-height:var(--kgg-plan-action-h)!important;
        max-height:var(--kgg-plan-action-h)!important;
        box-sizing:border-box!important;
      }
      #createPanel.planMode .packageLayoutSlot .tabletLockSwitch{
        width:100%!important;
        height:var(--kgg-plan-action-h)!important;
        min-height:var(--kgg-plan-action-h)!important;
        max-height:var(--kgg-plan-action-h)!important;
        padding:6px 8px!important;
        box-sizing:border-box!important;
      }
      #createPanel.planMode .packageLayoutSlot #packageToggle > span,
      #createPanel.planMode #recentToggle .recentText,
      #createPanel.planMode #recentToggle .recentMini{
        max-width:100%!important;
        opacity:1!important;
      }
    }
    @media (min-width:760px) and (max-width:980px){
      #createPanel.planMode .packageLayoutSlot{
        grid-template-columns:minmax(0,1fr) minmax(66px,76px)!important;
        gap:8px!important;
      }
      #createPanel.planMode .packageLayoutSlot .tabletLayoutControls{
        min-width:66px!important;
        max-width:76px!important;
      }
      #createPanel.planMode #recentToggle,
      #createPanel.planMode .packageLayoutSlot #packageToggle{
        padding-left:10px!important;
        padding-right:10px!important;
      }
    }
  .syncQrBtn,
  .tabletSyncQrBtn{
    border:1px solid var(--line);
    background:#fff;
    color:#071027;
    font-weight:1000;
    box-shadow:var(--shadow);
    display:inline-flex;
    align-items:center;
    justify-content:center;
  }
  .syncQrBtn{
    border-radius:16px;
    min-width:58px;
    min-height:58px;
    padding:0 14px;
    font-size:21px;
  }
  .syncPairSheet .notice{margin-top:8px}
  .syncPairQrBox{min-height:280px}
  .syncPairStatus{
    display:block;
    margin-top:8px;
    color:var(--muted);
    font-weight:900;
    font-size:13px;
    text-align:center;
  }
  .syncPeerList{
    margin-top:10px;
    border:1px solid var(--line);
    border-radius:14px;
    background:#fff;
    padding:8px;
    display:grid;
    gap:7px;
  }
  .syncPeerHead{
    display:flex;
    align-items:center;
    justify-content:space-between;
    gap:8px;
    font-weight:1000;
    font-size:13px;
    color:#071027;
  }
  .syncPeerHead small{color:var(--muted);font-weight:900}
  .syncPeerRow{
    display:grid;
    grid-template-columns:auto minmax(0,1fr);
    align-items:center;
    gap:8px;
    border-top:1px solid rgba(15,23,42,.08);
    padding-top:7px;
    font-size:13px;
  }
  .syncPeerRow input{width:18px;height:18px}
  .syncPeerName{font-weight:1000;color:#071027;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
  .syncPeerMeta{color:var(--muted);font-weight:850;font-size:11px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
  .syncPeerEmpty{color:var(--muted);font-weight:900;font-size:12px;text-align:center}
  .syncDiagnostics{
    margin-top:10px;
    border:1px solid var(--line);
    border-radius:14px;
    background:#f8fbff;
    padding:9px 10px;
    color:#324154;
    font-size:12px;
    font-weight:850;
    display:grid;
    gap:4px;
  }
  .syncDiagnostics b{color:#071027}
  .syncDiagnostics .warn{color:#9a3412}
  .syncPairActions{
    display:grid;
    grid-template-columns:1fr 1fr;
    gap:8px;
    margin-top:10px;
  }
  .syncPairActions .primary{grid-column:1/-1}
  @media(max-width:759px){
    .scanHub{
      display:grid;
      grid-template-columns:minmax(0,1fr) auto;
      gap:10px;
      align-items:stretch;
    }
    .scanHub .scanBtn{grid-column:1;grid-row:1}
    .scanHub .syncQrBtn{grid-column:2;grid-row:1}
    .scanHub .scanMeta{grid-column:1/-1}
    .scanHub .adminConfigBtn,
    .scanHub .sharedBankBtn,
    .scanHub #scanPreview{grid-column:1/-1}
    .tabletSyncQrBtn{display:none!important}
  }
  @media(min-width:760px){
    .scanHub .syncQrBtn{display:none!important}
    .tabletSyncQrBtn{
      width:100%;
      min-height:38px;
      border-radius:12px;
      padding:0 8px;
      font-size:13px;
      line-height:1;
    }
    .packageLayoutSlot .tabletLayoutControls{
      height:auto!important;
      min-height:66px!important;
      display:grid!important;
      grid-template-columns:1fr!important;
      gap:6px!important;
      padding:4px!important;
    }
    .packageLayoutSlot .tabletLayoutControls .tabletLockSwitch,
    .packageLayoutSlot .tabletLayoutControls .tabletSyncQrBtn{
      width:100%!important;
    }
  }

/* v361: Tablet side menu, safe top spacing and clean bottom actions */
.tabletMenuBtn,
.tabletSideBackdrop,
.tabletSideMenu{display:none;}

@media (max-width:759px){
  .app{
    padding-top:max(24px,calc(env(safe-area-inset-top) + 20px))!important;
    padding-left:14px!important;
    padding-right:14px!important;
  }
  .scanHub{margin-top:6px!important;}
  .tabletMenuBtn,
  .tabletSideBackdrop,
  .tabletSideMenu{display:none!important;}
}

@media (min-width:760px){
  .scanHub{
    grid-template-columns:58px minmax(148px,.78fr) minmax(148px,.78fr) minmax(140px,.82fr) minmax(170px,1fr)!important;
    align-items:stretch!important;
    column-gap:12px!important;
  }
  body.colleagueMode .scanHub{
    grid-template-columns:58px minmax(150px,.82fr) minmax(150px,.82fr) minmax(170px,1fr)!important;
  }
  .tabletMenuBtn{
    display:inline-grid!important;
    place-items:center;
    grid-column:1!important;
    grid-row:1!important;
    width:54px;
    min-width:54px;
    min-height:54px;
    border:1.4px solid rgba(10,16,36,.14);
    border-radius:18px;
    background:#fff;
    box-shadow:0 12px 26px rgba(10,16,36,.10), inset 0 1px 0 rgba(255,255,255,.78);
    cursor:pointer;
    touch-action:manipulation;
  }
  .tabletMenuBtn span{
    display:block;
    width:25px;
    height:3px;
    border-radius:999px;
    background:#0a1024;
    margin:3px 0;
    transition:transform .18s ease, opacity .18s ease;
  }
  body.tabletMenuOpen .tabletMenuBtn span:nth-child(1){transform:translateY(9px) rotate(45deg);}
```
