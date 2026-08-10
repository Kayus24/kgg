# KGG Source Chunk 006

- Source: `kgg-update/src` modular source
- Lines: 2521-2940

```html
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
       Der +📦 Button war zwar im Planheader, klebte aber optisch am oberen Rand.
       Nur Tablet-CSS: kleiner, flacher, vertikal in der Kopfzeile zentriert. Keine Logik. */
    @media (min-width:760px){
      #createPanel.planMode #currentPlanBlock{
        position:relative;
      }
      #createPanel.planMode #savePackageBtn{
        grid-column:2 / 4!important;
        grid-row:3!important;
        justify-self:end!important;
        align-self:start!important;
        width:86px!important;
        min-width:86px!important;
        max-width:86px!important;
        height:36px!important;
        min-height:36px!important;
        margin:8px 14px 0 0!important;
        padding:0 10px!important;
        border:1px solid rgba(220,227,235,.96)!important;
        border-radius:14px!important;
        background:#fff!important;
        box-shadow:0 1px 5px rgba(7,16,39,.055)!important;
        z-index:66!important;
        align-items:center!important;
        justify-content:center!important;
        line-height:1!important;
      }
      #createPanel.planMode #savePackageBtn .packageBox{
        font-size:23px!important;
        line-height:1!important;
      }
      #createPanel.planMode #savePackageBtn .packagePlus{
        font-size:16px!important;
        line-height:1!important;
      }
      #createPanel.planMode #currentPlanToggle{
        min-height:52px!important;
        padding-right:112px!important;
        align-items:center!important;
      }
      #createPanel.planMode #currentPlanToggle > small{
        margin-right:0!important;
      }
      @media (max-width:920px){
        #createPanel.planMode #savePackageBtn{
          width:78px!important;
          min-width:78px!important;
          max-width:78px!important;
          height:34px!important;
          min-height:34px!important;
          margin:8px 10px 0 0!important;
          padding:0 8px!important;
        }
        #createPanel.planMode #savePackageBtn .packageBox{font-size:21px!important;}
        #createPanel.planMode #savePackageBtn .packagePlus{font-size:15px!important;}
        #createPanel.planMode #currentPlanToggle{padding-right:96px!important;}
      }
    }


    /* v330 Tablet Column/Package Balance:
       Linke Spalte bekommt mehr Raum Richtung Mitte; Mittelabstand kleiner.
       +📦 Button wird innerhalb der Plan-Kopfzeile tiefer/zentrierter geführt.
       Nur Tablet-CSS, keine PDF/QR/Patienten-App/Scan/Parser/Plan-State-Logik. */
    @media (min-width:760px){
      /* Linke Arbeits-Spalte breiter, rechte Arbeitszone bleibt zwei gleich große Aktionsspalten. */
      .app{
        grid-template-columns:minmax(420px,500px) minmax(0,1fr) minmax(0,1fr)!important;
        gap:10px!important;
        column-gap:10px!important;
      }

      /* Linke Spalte optisch etwas mehr in die Mitte holen, ohne die rechte Planliste zu beschädigen. */
      .scanHub,
      #inputWrap,
      #bankArea{
        justify-self:stretch!important;
        width:100%!important;
      }

      /* Planbereich bleibt bündig, bekommt aber weniger übertriebene Leerweite. */
      #rightPlanStack,
      #currentPlanBlock{
        min-width:0!important;
      }

      /* +📦 nicht an der oberen Kante kleben lassen: Header wird minimal höher, Button sitzt darin zentriert. */
      #createPanel.planMode #currentPlanToggle{
        min-height:62px!important;
        padding-top:14px!important;
        padding-bottom:12px!important;
        padding-right:118px!important;
        align-items:center!important;
      }
      #createPanel.planMode #savePackageBtn{
        grid-column:2 / 4!important;
        grid-row:3!important;
        justify-self:end!important;
        align-self:start!important;
        width:86px!important;
        min-width:86px!important;
        max-width:86px!important;
        height:38px!important;
        min-height:38px!important;
        margin:12px 16px 0 0!important;
        padding:0 10px!important;
        border-radius:15px!important;
        z-index:72!important;
      }

      /* Untere Buttons exakt gleich groß halten. */
      #createPanel.planMode #recentToggle,
      #createPanel.planMode #packageToggle{
        width:100%!important;
        min-width:0!important;
        height:60px!important;
        min-height:60px!important;
      }

      @media (max-width:1040px){
        .app{
          grid-template-columns:minmax(390px,460px) minmax(0,1fr) minmax(0,1fr)!important;
          gap:9px!important;
          column-gap:9px!important;
        }
        #createPanel.planMode #currentPlanToggle{
          padding-right:108px!important;
        }
        #createPanel.planMode #savePackageBtn{
          width:80px!important;
          min-width:80px!important;
          max-width:80px!important;
          height:36px!important;
          min-height:36px!important;
          margin:12px 12px 0 0!important;
        }
      }

      @media (max-width:920px){
        .app{
          grid-template-columns:minmax(350px,420px) minmax(0,1fr) minmax(0,1fr)!important;
          gap:8px!important;
          column-gap:8px!important;
        }
        #createPanel.planMode #currentPlanToggle{
          min-height:58px!important;
          padding-top:12px!important;
          padding-bottom:10px!important;
          padding-right:98px!important;
        }
        #createPanel.planMode #savePackageBtn{
```
