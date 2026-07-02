# KGG Source Chunk 010

- Source: `kgg-update/index.html`
- Lines: 4201-4620

```html
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
  body.tabletMenuOpen .tabletMenuBtn span:nth-child(2){opacity:0;}
  body.tabletMenuOpen .tabletMenuBtn span:nth-child(3){transform:translateY(-9px) rotate(-45deg);}
  .tabletSideBackdrop{
    position:fixed;
    inset:0;
    z-index:1090;
    display:block;
    opacity:0;
    pointer-events:none;
    background:rgba(10,16,36,.18);
    backdrop-filter:blur(10px);
    transition:opacity .22s ease;
  }
  body.tabletMenuOpen .tabletSideBackdrop{
    opacity:1;
    pointer-events:auto;
  }
  .tabletSideMenu{
    position:fixed;
    top:0;
    bottom:0;
    left:0;
    z-index:1100;
    display:flex;
    width:min(380px,86vw);
    flex-direction:column;
    gap:18px;
    padding:calc(env(safe-area-inset-top) + 22px) 18px calc(env(safe-area-inset-bottom) + 22px);
    background:rgba(255,255,255,.96);
    border-right:1.5px solid rgba(10,16,36,.10);
    box-shadow:26px 0 70px rgba(10,16,36,.18);
    transform:translateX(-106%);
    transition:transform .24s cubic-bezier(.22,.8,.32,1);
  }
  body.tabletMenuOpen .tabletSideMenu{transform:translateX(0);}
  .tabletSideMenuHead{
    display:flex;
    align-items:center;
    justify-content:space-between;
    gap:12px;
    font-size:1.25rem;
    font-weight:900;
  }
  .tabletMenuClose{
    width:42px;
    height:42px;
    border-radius:999px;
    border:1px solid rgba(10,16,36,.12);
    background:#fff;
    font-size:1.35rem;
    font-weight:900;
    color:#0a1024;
    cursor:pointer;
  }
  .tabletSideMenuGroup{
    display:flex;
    flex-direction:column;
    gap:12px;
    padding:14px;
    border:1px solid rgba(10,16,36,.10);
    border-radius:22px;
    background:#f8fafc;
  }
  .tabletSideMenuGroup h3{
    margin:0;
    font-size:1rem;
    font-weight:900;
    color:#0a1024;
  }
  .tabletSideHint{
    margin:0;
    font-size:.86rem;
    line-height:1.35;
    color:#667085;
    font-weight:750;
  }
  .tabletSideMenu .tabletLayoutControls{
    position:static!important;
    display:grid!important;
    grid-template-columns:1fr 1fr;
    width:100%!important;
    min-width:0!important;
    height:auto!important;
    padding:0!important;
    gap:10px!important;
    border:0!important;
    box-shadow:none!important;
    background:transparent!important;
  }
  .tabletSideMenu .tabletLockSwitch,
  .tabletSideMenu .tabletSyncQrBtn{
    min-height:54px!important;
    width:100%!important;
    border-radius:17px!important;
    font-size:.92rem!important;
  }
  .tabletSideMenu .tabletLayoutFreeTools{
    grid-column:1 / -1!important;
    position:static!important;
    display:grid!important;
    grid-template-columns:58px 1fr 58px!important;
    grid-template-areas:"plus value minus" "reset reset reset";
    /* v361 side menu scale grid polish */
    align-items:center!important;
    width:100%!important;
    min-width:0!important;
    height:auto!important;
    padding:10px!important;
    border-radius:21px!important;
  }
  .tabletSideMenu #tabletScalePlus{grid-area:plus;}
  .tabletSideMenu #tabletScaleValue{grid-area:value;text-align:center;}
  .tabletSideMenu #tabletScaleMinus{grid-area:minus;}
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
```
