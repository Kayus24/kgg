# KGG Source Chunk 005

- Source: `kgg-update/index.html`
- Lines: 2101-2520

```html
        font-size:clamp(10px,calc(14px * var(--kgg-tablet-ui-scale,1)),22px)!important;
      }
    }
    @media (min-width:760px){
      #rightPlanStack{grid-column:2/4!important;grid-row:3/5!important;align-self:stretch;min-height:0;overflow:hidden}
      #rightPlanStack #currentPlanBlock,#rightPlanStack #scannedPlansBlock{grid-column:auto!important;grid-row:auto!important;align-self:auto!important;padding:0!important;min-height:0!important;overflow:hidden!important}
      #rightPlanStack #currentPlanBlock:not(.collapsed),#rightPlanStack #scannedPlansBlock:not(.collapsed){flex:1 1 auto;max-height:none}
      #rightPlanStack .planSectionBody,#rightPlanStack .scanInboxList{max-height:100%;overflow:auto}
      #rightPlanStack #planList{max-height:none!important;height:auto!important;overflow:visible!important;padding-right:0!important}
      #rightPlanStack #currentPlanBlock .label{display:none!important}
      #currentPlanBlock{grid-column:auto!important;grid-row:auto!important}
      #createPanel:not(.planMode) #rightPlanStack.hidden{display:none!important}
    }



    /* v321 Tablet Layout/Caret Fix:
       - Aktueller-Plan-Titel im Tablet-Planmodus ausblenden
       - Fertig eine Zeile tiefer setzen
       - +Paket-Button auf Höhe von "Übungen im Plan" andocken
       - Gescannte Pläne/Übungen im Plan wirklich vollständig kollabieren
       - Carets für Basisdaten / Übungen im Plan / Gescannte Pläne stabilisieren
       - Aktive Floating-Button-Anker bleiben über dem Popup klickbar */
    .planSectionHeader{
      justify-content:flex-start;
    }
    .planSectionHeader::before{
      content:"▶";
      flex:0 0 auto;
      display:inline-grid;
      place-items:center;
      width:1.1em;
      margin-right:4px;
      font-size:.92em;
      line-height:1;
      color:#071027;
    }
    .planSectionHeader[aria-expanded="true"]::before{
      content:"▼";
    }
    .planSectionHeader > span{
      flex:1 1 auto;
      min-width:0;
    }
    .planSectionHeader > small{
      flex:0 0 auto;
      margin-left:auto;
    }
    .planSection.collapsed{
      flex:0 0 54px!important;
      height:54px!important;
      min-height:54px!important;
      max-height:54px!important;
      overflow:hidden!important;
      background:#f8fafc;
      opacity:.98;
    }
    .planSection.collapsed .planSectionBody,
    .planSection.collapsed .scanInboxList{
      display:none!important;
      height:0!important;
      min-height:0!important;
      max-height:0!important;
      padding:0!important;
      margin:0!important;
      overflow:hidden!important;
    }

    @media (min-width:760px){
      /* Großer doppelter Titel "Aktueller Plan" ist im Planmodus überflüssig. */
      #createPanel.planMode .planHeader .panelTitle{
        display:none!important;
      }

      /* Fertig rutscht aus der obersten Kopfzeile in die Button-Zeile neben Basisdaten. */
      #createPanel.planMode #finishBtn{
        grid-column:3;
        grid-row:2;
        align-self:stretch;
        justify-self:stretch;
        width:100%;
        height:68px;
        min-height:68px;
        margin:0;
        border-radius:18px;
        font-size:20px;
        opacity:1;
        scale:1 1;
        animation:none;
      }

      /* +Paket-Button optisch an die Kopfzeile des Planblocks andocken. */
      #createPanel.planMode #savePackageBtn{
        grid-column:3;
        grid-row:3;
        align-self:start;
        justify-self:stretch;
        width:100%;
        height:50px;
        min-height:50px;
        margin:0;
        border-radius:18px;
        z-index:46;
      }
      #createPanel.planMode #rightPlanStack.planOpen #currentPlanToggle{
        padding-right:176px;
      }
      #createPanel.planMode:has(#rightPlanStack.scanOpen) #savePackageBtn{
        visibility:hidden!important;
        pointer-events:none!important;
      }

      /* Kollabierte Scan-/Planleisten bleiben wirklich nur Headerleisten. */
      #rightPlanStack .planSection.collapsed{
        flex:0 0 54px!important;
        height:54px!important;
        min-height:54px!important;
        max-height:54px!important;
      }
      #rightPlanStack .planSection.collapsed .planSectionBody,
      #rightPlanStack .planSection.collapsed .scanInboxList{
        display:none!important;
        padding:0!important;
        margin:0!important;
        height:0!important;
        max-height:0!important;
        overflow:hidden!important;
      }

      /* Der zugehörige Button bleibt als aktiver Anker über dem schwebenden Fenster. */
      .kggOverlayAnchorActive{
        position:relative!important;
        z-index:190!important;
        box-shadow:0 18px 42px rgba(7,16,39,.22), var(--shadow)!important;
        outline:2px solid rgba(7,16,39,.16);
        outline-offset:2px;
      }

      @media (max-width:920px){
        #createPanel.planMode #finishBtn{
          height:60px;
          min-height:60px;
          font-size:18px;
        }
        #createPanel.planMode #savePackageBtn{
          height:48px;
          min-height:48px;
        }
        #createPanel.planMode #rightPlanStack.planOpen #currentPlanToggle{
          padding-right:142px;
        }
      }
    }


    /* v324: In beiden UI-Varianten heißt der übergeordnete Planbereich wieder "Aktueller Plan". */
    @media (min-width:760px){
      #createPanel.planMode .planHeader .panelTitle{display:block!important}
    }

    /* v324 Aktueller-Plan/Scan-Dock Fix:
       Mobile-only: "Gescannte Pläne" sitzt außerhalb der Aktueller-Plan-Bubble, oberhalb davon.
       Keine PDF/QR/Patienten-App/Parser/Scan-Core-Änderungen. */
    @media (max-width:759px){
      /* Aktueller Plan ist wieder die Überschrift für Basisdaten + Übungskarten. */
      #createPanel.planMode .planHeader{display:grid!important;grid-template-columns:minmax(0,1fr) auto;align-items:center;margin:0 0 8px;min-height:0}
      #createPanel.planMode .planHeader .panelTitle{display:block!important;font-size:26px;line-height:1.05;margin:0;letter-spacing:-.4px}
      #createPanel.scanPanelOpen .planHeader{display:grid!important}

      /* Scan-Ergebnisse werden auf Handy in den separaten Dock oberhalb der Plan-Bubble verschoben. */
      .mobileScannedPlansDock{display:block;margin:0 0 10px}
      .mobileScannedPlansDock.hidden{display:none!important}
      .mobileScannedPlansDock .planSection{border:1px solid #bfe8c5!important;border-radius:20px;box-shadow:0 2px 10px rgba(7,16,39,.055);background:#f7fff8!important;overflow:hidden}
      .mobileScannedPlansDock .planSectionHeader{min-height:48px;padding:10px 12px;font-size:18px;background:#f7fff8!important}
      .mobileScannedPlansDock .scanInboxList{padding:0 8px 8px}
      .mobileScannedPlansDock .scanInboxCard{border:1px solid #e3e9ef;border-radius:16px;box-shadow:none;padding:10px;margin-bottom:8px;background:#fff}
      .mobileScannedPlansDock .scanInboxText{min-height:88px;border-color:#e3e9ef;border-radius:12px;font-size:12.5px;line-height:1.32}
      .mobileScannedPlansDock .planSection.collapsed{flex:0 0 48px!important;height:48px!important;min-height:48px!important;max-height:48px!important;border-color:#bfe8c5!important;background:#f7fff8!important}
      .mobileScannedPlansDock .planSection.collapsed .scanInboxList{display:none!important;height:0!important;min-height:0!important;max-height:0!important;padding:0!important;margin:0!important;overflow:hidden!important}

      /* Rechte Planstruktur enthält auf Handy nur noch den Übungsbereich; Scans sitzen im Dock darüber. */
      .rightPlanStack{gap:8px;margin:8px 0 10px}
      .rightPlanStack.planOpen #currentPlanBlock{order:1!important;animation:kggSectionSwapIn .20s cubic-bezier(.2,.85,.2,1) both}
      .rightPlanStack.scanOpen #currentPlanBlock{order:1!important}

      /* Rahmen reduzieren: Struktur bleibt, aber keine Kiste-in-Kiste-Optik. */
      .panel{border:1px solid rgba(17,24,39,.18);box-shadow:0 2px 12px rgba(7,16,39,.055);border-radius:22px;padding:10px;background:rgba(255,255,255,.82)}
      .inner{border:0;border-radius:18px;padding:8px;background:transparent}
      #rightPlanStack .planSection{border:1px solid rgba(17,24,39,.22);border-radius:20px;box-shadow:0 2px 10px rgba(7,16,39,.055)}
      #rightPlanStack .planSection.collapsed{flex:0 0 48px!important;height:48px!important;min-height:48px!important;max-height:48px!important;border-color:rgba(17,24,39,.16);background:#fbfcfe}
      #rightPlanStack .planSectionHeader{min-height:48px;padding:10px 12px;font-size:18px}
      #rightPlanStack .planSectionBody{padding:0 8px 8px}
      #rightPlanStack .planCard{box-shadow:none;border-color:rgba(220,227,235,.9)}
    }


    /* v327 Tablet Shell Full-Bleed Fix:
       Ziel: Tablet wirkt nicht mehr wie frei schwebende Mockup-Karte.
       Nur äußere Tablet-Shell/Viewport, keine PDF/QR/Scan/Parser/Plan-State-Logik. */
    @media (min-width:760px){
      html,body{
        width:100%;
        min-width:0;
        height:100%;
        min-height:100%;
        overflow:hidden;
        background:#f7f9fc;
      }
      body{
        display:block;
        padding:0!important;
        margin:0!important;
        align-items:stretch!important;
        justify-content:stretch!important;
      }
      .app{
        width:100vw!important;
        max-width:none!important;
        height:100vh!important;
        height:100dvh!important;
        height:var(--kgg-visual-vh,100dvh)!important;
        max-height:var(--kgg-visual-vh,100dvh)!important;
        min-height:0!important;
        margin:0!important;
        border:0!important;
        border-radius:0!important;
        box-shadow:none!important;
        background:#f7f9fc!important;
        padding:12px 14px 10px!important;
        overflow:hidden!important;
        grid-template-columns:minmax(360px,430px) minmax(0,1fr) minmax(150px,190px)!important;
        grid-template-rows:auto 64px minmax(104px,auto) minmax(0,1fr) 60px!important;
        gap:12px!important;
      }
      /* Innenkarten behalten die App-Struktur, nur der Außen-Mockup-Rahmen verschwindet. */
      #inputWrap,
      #bankArea.bankOpen,
      #currentPlanBlock,
      #scannedPlansBlock,
      .planSection,
      .baseCard,
      .drawerBtn,
      .scanHub .scanBtn,
      .scanHub .scanMeta{
        box-shadow:0 2px 10px rgba(7,16,39,.055);
      }
      .scanHub .scanBtn,
      .scanHub .scanMeta,
      #baseToggle,
      #finishBtn,
      #recentToggle,
      #packageToggle{
        min-height:60px!important;
        height:60px!important;
      }
      #savePackageBtn{
        min-height:48px!important;
        height:48px!important;
      }
      #exerciseInput{
        min-height:104px;
        max-height:160px;
      }
      #bankArea.bankOpen.alphaBankOpen .az{
        height:calc(100% - 58px);
        margin-top:58px;
      }
      #recentList:not(.hidden),
      #packageList:not(.hidden),
      #baseFields:not(.hidden){
        max-height:calc(var(--kgg-visual-vh,100dvh) - 104px)!important;
      }
      .app.softKeyboard{
        height:var(--kgg-visual-vh,100dvh)!important;
        max-height:var(--kgg-visual-vh,100dvh)!important;
        padding:8px 10px!important;
        gap:8px!important;
        grid-template-rows:auto 54px minmax(78px,auto) minmax(0,1fr) 0!important;
      }
      .app.softKeyboard .scanHub .scanBtn,
      .app.softKeyboard .scanHub .scanMeta,
      .app.softKeyboard #baseToggle,
      .app.softKeyboard #finishBtn,
      .app.softKeyboard #recentToggle,
      .app.softKeyboard #packageToggle{
        min-height:54px!important;
        height:54px!important;
      }
      .app.softKeyboard #exerciseInput{
        min-height:78px;
        max-height:116px;
      }
      @media (max-width:920px){
        .app{
          padding:8px 10px 8px!important;
          gap:10px!important;
          grid-template-columns:minmax(320px,390px) minmax(0,1fr) minmax(126px,150px)!important;
          grid-template-rows:auto 58px minmax(92px,auto) minmax(0,1fr) 56px!important;
        }
        .scanHub .scanBtn,
        .scanHub .scanMeta,
        #baseToggle,
        #finishBtn,
        #recentToggle,
        #packageToggle{
          min-height:56px!important;
          height:56px!important;
        }
        #exerciseInput{
          min-height:92px;
          max-height:132px;
        }
      }
    }


    /* v328 Tablet Header/Package Fix:
       - ausgefahrene Übungsdatenbank-Überschrift auf Tablet ausblenden
       - großen Titel "Aktueller Plan" im Tablet-Planmodus entfernen
       - Stift-Symbol direkt an "Übungen im Plan" hängen
       - +📦 sauber in die Plan-Kopfzeile docken, ohne Zähler/Text zu verdecken
       - Plan-Historie und Übungspakete unten gleich groß machen
       Keine PDF/QR/Patienten-App/Scan/Parser/Plan-State-Logik. */
    @media (min-width:760px){
      /* Rechts und unten echte gleichmäßige Tablet-Arbeitszonen. */
      .app{
        grid-template-columns:minmax(360px,430px) minmax(0,1fr) minmax(0,1fr)!important;
      }

      /* Ausgefahrene DB braucht keine zusätzliche Kopfzeile oben links. */
      #dbTitle.fullBankOpen,
      #dbTitle.searchBankOpen{
        display:none!important;
      }

      /* Der globale Titel konkurriert mit der eigentlichen Plan-Kopfzeile. */
      #createPanel.planMode .planHeader .panelTitle{
        display:none!important;
      }

      /* Stift gehört zum konkreten Abschnitt, nicht als großer Seitentitel. */
      #createPanel.planMode #currentPlanToggle > span::before{
        content:"✏️ ";
      }

      /* +Paket nicht als schwebender rechter Großbutton, sondern als Kopfzeilen-Aktion. */
      #createPanel.planMode #savePackageBtn{
        grid-column:2 / 4!important;
        grid-row:3!important;
        justify-self:end!important;
        align-self:start!important;
        width:118px!important;
        min-width:118px!important;
        max-width:118px!important;
        height:48px!important;
        min-height:48px!important;
        margin:0 14px 0 0!important;
        border-radius:18px!important;
        z-index:66!important;
      }
      #createPanel.planMode #currentPlanToggle{
        padding-right:154px!important;
      }
      #createPanel.planMode #currentPlanToggle > small{
        margin-right:6px;
      }
      #createPanel.planMode:has(#rightPlanStack.scanOpen) #savePackageBtn{
        visibility:hidden!important;
        pointer-events:none!important;
      }

      /* Untere Aktionsbuttons: gleiche Breite, gleiche Höhe, ruhige Zeile. */
      #createPanel.planMode #recentToggle,
      #createPanel.planMode #packageToggle{
        grid-row:5!important;
        width:100%!important;
        min-width:0!important;
        height:60px!important;
        min-height:60px!important;
        justify-self:stretch!important;
        align-self:stretch!important;
      }
      #createPanel.planMode #recentToggle{grid-column:2!important;}
      #createPanel.planMode #packageToggle{grid-column:3!important;}
      .planActions.hasPlan #recentToggle{
        width:100%!important;
        min-width:0!important;
        padding:10px 12px!important;
      }
      .planActions.hasPlan .recentText,
      .planActions.hasPlan .recentMini{
        max-width:none!important;
        opacity:1!important;
      }

      @media (max-width:920px){
        .app{
          grid-template-columns:minmax(320px,390px) minmax(0,1fr) minmax(0,1fr)!important;
        }
        #createPanel.planMode #savePackageBtn{
          width:104px!important;
          min-width:104px!important;
          max-width:104px!important;
          height:46px!important;
          min-height:46px!important;
          margin-right:10px!important;
        }
        #createPanel.planMode #currentPlanToggle{
          padding-right:132px!important;
        }
        #createPanel.planMode #recentToggle,
        #createPanel.planMode #packageToggle{
          height:56px!important;
          min-height:56px!important;
        }
      }
    }


    /* v329 Tablet Package Button Header Align:
```
