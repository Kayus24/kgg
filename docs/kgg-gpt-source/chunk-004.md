# KGG Source Chunk 004

- Source: `kgg-update/index.html`
- Lines: 1681-2100

```html
      #baseFields{grid-column:1/4;grid-row:2;background:#fff;border:1px solid var(--line);border-radius:18px;padding:12px;box-shadow:var(--shadow);z-index:4}
      #baseFields.hidden{display:none!important}
      #inputLabel{grid-column:1;grid-row:1;margin:0;align-self:end;font-size:20px;line-height:1;font-weight:1000}
      #dbTitle{grid-column:1;grid-row:1;margin:0;align-self:end}
      #inputWrap{grid-column:1;grid-row:3;align-self:stretch;border-radius:20px}
      #exerciseInput{min-height:126px;max-height:190px;font-size:22px}
      #bankArea{grid-column:1;grid-row:4;align-self:stretch;min-height:0;overflow:hidden;background:#fff;border-radius:20px}
      #bankArea.bankOpen{display:flex;flex-direction:column;overflow:hidden;border:2px solid #111827;box-shadow:var(--shadow);padding:10px;height:100%;min-height:0}
      #bankArea.bankOpen #bankContent{flex:1;min-height:0;margin-top:8px}
      #bankArea.bankOpen .bankRows{max-height:none;height:100%}
      #bankArea:not(.bankOpen) .drawerBtn{height:64px;min-height:64px;border:2px solid #111827;border-radius:20px;font-size:20px}
      #currentPlanBlock{grid-column:2/4;grid-row:3/5;align-self:start;min-height:38vh;min-width:0;background:#fff;border:2px solid #111827;border-radius:24px;box-shadow:var(--shadow);padding:14px;overflow:hidden}
      #currentPlanBlock.hidden{display:block!important;visibility:hidden;pointer-events:none}
      #currentPlanBlock .label{margin:0 0 12px;font-size:20px;line-height:1;font-weight:1000}
      #planList{max-height:calc(100dvh - 310px);overflow:auto;padding-right:2px}
      .planCard{border-radius:18px;padding:12px 14px;grid-template-columns:minmax(0,1fr) auto}
      .planCard b{font-size:20px}
      .planCard small{font-size:14px}
      .planActions{grid-column:2;grid-row:5;display:grid;grid-template-columns:minmax(0,1.15fr) minmax(0,.85fr);gap:14px;align-self:stretch}
      .planActions:not(.hasPlan){grid-template-columns:1fr}
      .planActions:not(.hasPlan) #finishBtn.hidden{display:none!important}
      #createPanel:not(.planMode) #recentToggle,#createPanel:not(.planMode) #packageToggle{height:64px;min-height:64px;width:100%;box-sizing:border-box;align-self:stretch}
      #finishBtn{grid-column:auto;grid-row:auto;height:64px;min-height:64px;margin:0;border-radius:18px;font-size:22px}
      #finishBtn.hidden{display:block!important;visibility:hidden;pointer-events:none;padding-left:0;padding-right:0;border-width:0}
      #recentToggle{grid-column:auto;grid-row:auto;height:64px;min-height:64px;border-radius:18px;justify-content:center}
      #packageToggle{grid-column:3;grid-row:5;height:64px;min-height:64px;border-radius:18px;justify-content:center}
      #createPanel:not(.planMode) .planActions{grid-column:2/4;grid-template-columns:minmax(0,1fr) minmax(0,1fr)}
      #createPanel:not(.planMode) #recentToggle{grid-column:1;width:100%}
      #createPanel:not(.planMode) #packageToggle{grid-column:2/4;grid-row:5;justify-self:end;width:calc(50% - 7px)}
      #createPanel.planMode .planHeader .panelTitle{grid-column:2;grid-row:1}
      #createPanel.planMode .planActions{display:contents}
      #createPanel.planMode #finishBtn{grid-column:3;grid-row:1;align-self:end;justify-self:stretch;width:100%;height:54px;min-height:54px;border-radius:18px;font-size:20px;opacity:1;scale:1 1;animation:none}
      #createPanel.planMode #recentToggle{grid-column:2;grid-row:5;width:100%;min-width:0}
      #createPanel.planMode #packageToggle{grid-column:3;grid-row:5;width:100%}
      .planActions.hasPlan #recentToggle{width:auto;min-width:0;padding:10px 12px}
      #createPanel.planMode #recentToggle{width:100%;justify-self:stretch}
      .planActions.hasPlan .recentText,.planActions.hasPlan .recentMini{max-width:none;opacity:1}
      #recentList,#packageList{grid-row:4/5;align-self:end;z-index:28;max-height:min(42vh,360px);overflow:auto;background:rgba(255,255,255,.96);border:1px solid rgba(220,227,235,.92);border-radius:22px;padding:10px;box-shadow:0 18px 48px rgba(7,16,39,.18),0 4px 14px rgba(7,16,39,.08);backdrop-filter:blur(10px);transform-origin:bottom center;animation:tabletDrawerRise .28s cubic-bezier(.18,.84,.24,1) both}
      #recentList{grid-column:2}
      #packageList{grid-column:2/4}
      #recentList.hidden,#packageList.hidden{display:none!important}
      #recentList .notice,#packageList .notice{margin-top:0}
      @keyframes tabletDrawerRise{0%{opacity:0;transform:translateY(22px) scale(.96);filter:blur(2px)}70%{opacity:1;transform:translateY(-4px) scale(1.01);filter:blur(0)}100%{opacity:1;transform:translateY(0) scale(1);filter:blur(0)}}
      .bottomPad{display:none}
      .footerActions{display:none!important}
      .modal{align-items:center}
      .sheet{width:min(92vw,620px);border-radius:24px}
      .app.softKeyboard{height:calc(var(--kgg-visual-vh,100vh) - 20px);min-height:0;padding:12px;gap:10px;grid-template-rows:auto 56px minmax(82px,auto) minmax(0,1fr)}
      .app.softKeyboard .scanHub{gap:8px}
      .app.softKeyboard .scanHub .scanBtn,.app.softKeyboard .scanHub .scanMeta{font-size:15px;border-radius:14px}
      .app.softKeyboard .planHeader .panelTitle{font-size:26px}
      .app.softKeyboard #baseToggle,.app.softKeyboard #savePackageBtn{height:56px;min-height:56px;border-radius:15px}
      .app.softKeyboard #inputLabel,.app.softKeyboard #dbTitle{font-size:18px}
      .app.softKeyboard #inputWrap{border-radius:16px}
      .app.softKeyboard #exerciseInput{min-height:82px;max-height:120px;font-size:20px;line-height:1.25;padding-top:12px;padding-bottom:12px}
      .app.softKeyboard #bankArea{grid-row:4;min-height:0}
      .app.softKeyboard #bankArea.bankOpen{padding:8px;height:100%;min-height:0}
      .app.softKeyboard #bankArea.bankOpen #bankContent,.app.softKeyboard #bankArea.bankOpen .bankWithAz{height:100%;min-height:0}
      .app.softKeyboard #bankArea.bankOpen.alphaBankOpen .az{display:flex;flex-direction:column;height:calc(100% - 58px);margin-top:58px;padding:2px 0}
      .app.softKeyboard #bankArea.bankOpen.alphaBankOpen .az button{flex:1 1 0;min-height:0;font-size:10px;line-height:1}
      .app.softKeyboard .bankRow{padding:8px 10px}
      .app.softKeyboard .bankRow b{font-size:14px}
      .app.softKeyboard .bankRow small{font-size:10px}
      .app.softKeyboard #currentPlanBlock{padding:10px;border-radius:20px}
      .app.softKeyboard #currentPlanBlock .label{font-size:17px;margin-bottom:8px}
      .app.softKeyboard .planCard{padding:8px 10px;border-radius:15px}
      .app.softKeyboard .planCard b{font-size:17px}
      .app.softKeyboard .planCard small{font-size:12px}
      .app.softKeyboard #finishBtn,.app.softKeyboard #recentToggle,.app.softKeyboard #packageToggle{display:none!important}
      .app.softKeyboard #recentList,.app.softKeyboard #packageList{max-height:min(34vh,260px)}
    }
    #finishNotice:empty{display:none}
    .patientQrOutput{padding:8px;margin-top:4px;display:flex;flex-direction:column}
    .patientQrOutput .patientOutputTitle,
    .patientQrOutput #patientShareNotice,
    .patientQrOutput #patientQrStatus{display:none!important}
    .patientQrOutput .qrBox{margin-top:0;min-height:clamp(360px,84vw,520px);padding:6px;border-radius:18px}
    .patientQrOutput .qrBox img{width:100%;max-width:min(88vw,500px);height:auto}
    .patientQrOutput #patientQrBox{order:1}
    .patientQrOutput #patientAppLink{order:2}
    .patientQrOutput #copyPatientLink{order:3;width:100%;margin-top:8px}
    .patientQrOutput #patientLinkCopyField{order:4}
    .patientShareActions{display:grid;grid-template-columns:minmax(0,1fr) minmax(0,1fr);gap:8px;margin-top:8px}
    .patientShareActions .patientLink,
    .patientShareActions .mutedBtn{margin-top:0;min-height:48px;display:grid;place-items:center}
    @media (max-width:390px){.patientQrOutput .qrBox{min-height:clamp(330px,82vw,470px)}.patientShareActions{grid-template-columns:1fr}.patientShareActions .patientLink,.patientShareActions .mutedBtn{min-height:44px}}


    /* v309 Tablet Layout Fix: nur Tablet-CSS, keine PDF/QR/Scan/Parser-Logik. */
    @media (min-width:760px){
      .app{position:relative;isolation:isolate}

      /* Admin-Hinweis darf nicht mehr als ungeplantes Grid-Item unten ins Layout rutschen. */
      .adminTestBanner{position:absolute;left:18px;right:18px;bottom:8px;z-index:3;margin:0;padding:8px 10px;font-size:13px;line-height:1.15;pointer-events:none;opacity:.92}
      .adminTestBanner small{font-size:11px;line-height:1.15}

      /* Sichtbares Tablet-Raster stabilisieren. */
      .app{grid-template-columns:minmax(360px,430px) minmax(0,1fr) minmax(150px,190px);grid-template-rows:auto 68px minmax(126px,auto) minmax(0,1fr) 64px;gap:14px;align-items:stretch}
      .scanHub{grid-column:1;grid-row:2;align-self:stretch;min-width:0}
      .planHeader .panelTitle{grid-column:2/4;grid-row:1;align-self:end;min-width:0}
      #inputLabel,#dbTitle{grid-column:1;grid-row:1;align-self:end;min-width:0}
      #inputWrap{grid-column:1;grid-row:3;min-width:0;align-self:stretch}
      #bankArea{grid-column:1;grid-row:4;min-width:0;align-self:stretch}
      #currentPlanBlock{grid-column:2/4;grid-row:3/5;min-width:0;align-self:stretch}
      #baseToggle{grid-column:2;grid-row:2;min-width:0;align-self:stretch}
      #savePackageBtn{grid-column:3;grid-row:2;align-self:stretch;justify-self:stretch}
      #baseFields{grid-column:1/4;grid-row:2;align-self:start}

      /* Wenn kein Paket-Speichern-Button sichtbar ist, darf Basisdaten nicht schmal/frei schweben. */
      #createPanel:not(.planMode) #baseToggle,
      #savePackageBtn.hidden + #baseToggle{grid-column:2/4}
      #createPanel:not(.planMode) #savePackageBtn.hidden{display:none!important}

      /* Versteckte Planfläche soll im Leerzustand keine unsichtbare große Box erzwingen. */
      #createPanel:not(.planMode) #currentPlanBlock.hidden{display:none!important}

      /* Untere Tablet-Aktionen bündig halten. */
      #createPanel:not(.planMode) .planActions{grid-column:2;grid-row:5;display:grid;grid-template-columns:1fr;gap:14px;min-width:0}
      #createPanel:not(.planMode) #recentToggle{grid-column:1;grid-row:1;width:100%;height:64px;min-height:64px;justify-content:center}
      #createPanel:not(.planMode) #packageToggle{grid-column:3;grid-row:5;width:100%;justify-self:stretch;height:64px;min-height:64px}
      #createPanel.planMode #recentToggle,
      #createPanel.planMode #packageToggle{height:64px;min-height:64px;align-self:stretch}

      /* Eingabe/DB links als eine ruhige Spalte; rechts Planfläche voll ausnutzen. */
      #exerciseInput{width:100%;min-height:126px;max-height:190px}
      #bankArea:not(.bankOpen) .drawerBtn{width:100%;height:64px;min-height:64px}
      #currentPlanBlock .label{white-space:nowrap}
      #planList{max-height:100%;overflow:auto}

      /* Schmaler Tablet-Splitscreen: feste rechte Icon-Spalte etwas entspannen. */
      @media (max-width:920px){
        .app{grid-template-columns:minmax(320px,390px) minmax(0,1fr) minmax(126px,150px);gap:12px;padding:14px}
        #baseToggle{font-size:19px}
        #packageToggle,#recentToggle,#finishBtn{font-size:18px}
        .adminTestBanner{left:14px;right:14px;bottom:6px}
      }
    }

    /* v310 Tablet Layout Overlap Fix: Scan-Vorschau aus dem linken Eingabe-Raster nehmen, Bottom-Zeile sichtbar halten. */
    @media (min-width:760px){
      body{padding:8px;background:#e8eef6;overflow:hidden}
      .app{
        height:calc(100vh - 16px);
        height:calc(100dvh - 16px);
        height:calc(var(--kgg-visual-vh,100dvh) - 16px);
        max-height:calc(var(--kgg-visual-vh,100dvh) - 16px);
        min-height:0;
        grid-template-rows:auto 68px minmax(112px,auto) minmax(0,1fr) 64px;
        overflow:hidden;
      }

      /* Der Admin-Hinweis darf auf Tablet keinen Platz fressen und keine Buttons unten verdecken. */
      .adminTestBanner{display:none!important}

      /* ScanPreview war der sichtbare Überlappungsfehler: nicht mehr als dritte Zeile in .scanHub wachsen lassen. */
      .scanHub{overflow:visible;z-index:30;align-self:stretch}
      .scanHub #scanPreview:not(.hidden){
        position:absolute;
        left:calc(18px + min(430px,36vw) + 14px);
        right:18px;
        top:164px;
        max-height:calc(100% - 246px);
        overflow:auto;
        margin:0;
        z-index:35;
        border:2px solid #93d8a0;
        box-shadow:0 14px 40px rgba(7,16,39,.16);
      }
      .app:has(#createPanel.planMode) .scanHub #scanPreview{display:none!important}

      /* Eingabe und DB bleiben links sauber gestapelt; keine Vorschau darf darunterlaufen. */
      #inputWrap{position:relative;z-index:2;align-self:start}
      #bankArea{position:relative;z-index:1;min-height:0}
      #exerciseInput{min-height:112px;max-height:154px}
      #bankArea:not(.bankOpen) .drawerBtn{height:64px;min-height:64px}

      /* Rechter Leerzustand: keine unsichtbare Planbox und keine abgeschnittene untere Zeile. */
      #createPanel:not(.planMode) #currentPlanBlock.hidden{display:none!important}
      #createPanel:not(.planMode) .planActions,
      #createPanel:not(.planMode) #packageToggle,
      #createPanel.planMode #recentToggle,
      #createPanel.planMode #packageToggle,
      #createPanel.planMode #finishBtn{align-self:stretch;min-height:64px;height:64px}
      #recentList,#packageList{max-height:min(36vh,300px)}

      @media (max-width:920px){
        body{padding:6px}
        .app{height:calc(100dvh - 12px);height:calc(var(--kgg-visual-vh,100dvh) - 12px);max-height:calc(var(--kgg-visual-vh,100dvh) - 12px);padding:12px;gap:10px;grid-template-rows:auto 60px minmax(98px,auto) minmax(0,1fr) 58px}
        .scanHub #scanPreview:not(.hidden){left:calc(12px + min(390px,42vw) + 10px);right:12px;top:142px;max-height:calc(100% - 212px)}
        .scanHub .scanBtn,.scanHub .scanMeta{font-size:15px}
        #baseToggle,#savePackageBtn{height:60px;min-height:60px}
        #exerciseInput{min-height:98px;max-height:132px;font-size:20px}
        #bankArea:not(.bankOpen) .drawerBtn,#recentToggle,#packageToggle,#finishBtn{height:58px;min-height:58px}
      }
    }



    /* v311 Tablet Textfeld Visibility Fix: Admin-Buttons dürfen die Eingabezeile nicht überdecken. */
    @media (min-width:760px){
      /* Im Admin-Modus erzeugen Admin-Konfig + DB-Teilen eine zweite ScanHub-Zeile.
         Diese lief über grid-row:3 und verdeckte das Übungseingabe-Textfeld.
         Für Tablet-Testlayout werden diese Nebenbuttons ausgeblendet; Scan/Datei bleiben sichtbar. */
      .adminMode .scanHub .adminConfigBtn,
      .adminMode .scanHub .sharedBankBtn{
        display:none!important;
      }
      .adminMode .scanHub{
        grid-template-columns:minmax(0,1fr) minmax(0,1fr)!important;
        grid-auto-rows:68px!important;
        overflow:visible;
      }
      .scanHub .scanBtn,
      .scanHub .scanMeta{
        grid-row:1!important;
      }
      #inputWrap{
        display:block!important;
        visibility:visible!important;
        opacity:1!important;
        z-index:40;
      }
      #bankArea{
        z-index:10;
      }
      #exerciseInput{
        display:block!important;
        visibility:visible!important;
      }
      @media (max-width:920px){
        .adminMode .scanHub{grid-auto-rows:60px!important;}
      }
    }


    /* v312 Tablet Bank/A-Z Height Fix: Bank links bis zur unteren Kante erweitern und A-Z-Leiste als echte volle Touch-Leiste nutzbar machen. */
    @media (min-width:760px){
      /* Linke Bank darf die sonst leere linke Bottom-Zeile mitnutzen. Rechte Bottom-Buttons bleiben in Spalte 2/3. */
      #bankArea{
        grid-row:4/6;
        align-self:stretch;
        min-height:0;
      }
      #bankArea.bankOpen{
        display:flex;
        flex-direction:column;
        height:100%;
        min-height:0;
        overflow:hidden;
      }
      #bankArea.bankOpen #bankContent{
        flex:1 1 auto;
        height:100%;
        min-height:0;
        overflow:hidden;
      }
      #bankArea.bankOpen.alphaBankOpen .bankWithAz{
        height:100%;
        min-height:0;
        grid-template-columns:56px minmax(0,1fr);
        column-gap:8px;
      }
      #bankArea.bankOpen.alphaBankOpen .az{
        display:flex;
        flex-direction:column;
        height:calc(100% - 64px);
        min-height:0;
        margin-top:64px;
        padding:4px 0;
        touch-action:none;
        pointer-events:auto;
        z-index:6;
      }
      #bankArea.bankOpen.alphaBankOpen .az button{
        flex:1 1 0;
        min-height:13px;
        display:grid;
        place-items:center;
        font-size:10px;
        line-height:1;
        padding:0;
      }
      #bankArea.bankOpen.alphaBankOpen .bankRows{
        height:100%;
        max-height:none;
        min-height:0;
        overflow:auto;
        overscroll-behavior:contain;
      }
      #bankArea.bankOpen.alphaBankOpen .bankRow{
        min-height:62px;
      }
      @media (max-width:920px){
        #bankArea.bankOpen.alphaBankOpen .az button{min-height:11px;font-size:9.5px}
        #bankArea.bankOpen.alphaBankOpen .bankRow{min-height:58px}
      }
    }



    /* v316 Tablet Anchor Overlay Manager: Panels bleiben im sicheren Layer, öffnen aber aus ihrem Button-Anker. Keine Scan/PDF/QR/DB-Datenlogik. */
    @media (min-width:760px){
      body.kggTabletOverlayActive .app{isolation:isolate}
      /* Basisdaten, Plan-Historie und Pakete werden auf Tablet dynamisch am jeweiligen Button positioniert. */
      #baseFields:not(.hidden),
      #recentList:not(.hidden),
      #packageList:not(.hidden){
        position:fixed!important;
        z-index:160!important;
        left:var(--kgg-overlay-left,calc(50% - min(92vw,760px)/2))!important;
        right:auto!important;
        top:var(--kgg-overlay-top,84px)!important;
        width:var(--kgg-overlay-width,min(92vw,760px))!important;
        max-height:var(--kgg-overlay-max-height,calc(100dvh - 130px))!important;
        overflow:auto!important;
        grid-column:auto!important;
        grid-row:auto!important;
        align-self:auto!important;
        justify-self:auto!important;
        background:rgba(255,255,255,.985)!important;
        border:2px solid #111827!important;
        border-radius:24px!important;
        padding:14px!important;
        box-shadow:0 22px 64px rgba(7,16,39,.28),0 5px 18px rgba(7,16,39,.12)!important;
        backdrop-filter:none!important;
        transform-origin:var(--kgg-overlay-origin,top center)!important;
        animation:kggTabletAnchorOverlayIn .18s cubic-bezier(.18,.84,.24,1) both!important;
      }
      #baseFields:not(.hidden){
        display:grid!important;
        grid-template-columns:1fr 1fr!important;
        gap:10px!important;
      }
      #baseFields:not(.hidden) .field:last-child{grid-column:1/-1!important}
      #recentList:not(.hidden),#packageList:not(.hidden){display:block!important}
      #recentList:not(.hidden) .notice,#packageList:not(.hidden) .notice{margin-top:0}
      .modal.open{z-index:220!important}
      .kggScanV295 .scanDecisionBackdrop{z-index:99980!important}
      .kggScanV295 .scanDecision{z-index:99990!important}
      .scanHub #scanPreview:not(.hidden){z-index:70!important}
      #inputWrap{z-index:30}
      #bankArea{z-index:25}
      @keyframes kggTabletAnchorOverlayIn{0%{opacity:0;transform:scale(.965)}100%{opacity:1;transform:scale(1)}}
      @media (max-width:920px){
        #baseFields:not(.hidden),#recentList:not(.hidden),#packageList:not(.hidden){
          padding:12px!important;
        }
      }
    }


    /* v317 Plan-Card-Polish auf Basis v316: Medien-Badge + gelbe Neu/Prüfen-Karten wie im schöneren Planlayout. */
    .planCard{
      background:#fff;
      border:1px solid rgba(220,227,235,.95);
      box-shadow:0 2px 10px rgba(7,16,39,.055);
      align-items:center;
      gap:10px;
    }
    .planCard.is-new,
    .planCard.is-review{
      background:#fff9df;
      border-color:#dfc265;
      box-shadow:0 2px 10px rgba(120,87,0,.08);
    }
    .planCard .planMain{
      min-width:0;
      gap:10px;
    }
    .planThumb{
      width:42px;
      height:42px;
      min-width:42px;
      border:1px solid rgba(220,227,235,.95);
      border-radius:12px;
      background:#f6f8fb;
      display:inline-grid;
      place-items:center;
      overflow:hidden;
      color:#637083;
      font-size:18px;
      box-shadow:0 2px 8px rgba(7,16,39,.045);
    }
    .planThumb img{
      width:100%;
      height:100%;
      display:block;
      object-fit:cover;
    }
    .planThumbFallback{
      background:#eef3f8;
    }
    .planCard .drag{
      width:34px;
      height:34px;
      min-width:34px;
      border:1px solid rgba(220,227,235,.95);
      background:#fff;
      color:#2d3a4e;
      font-size:18px;
      line-height:1;
      border-radius:999px;
      margin-right:0;
    }
    .planCard .planText{
      min-width:0;
      gap:2px;
    }
    .planCard .planText b{
      display:flex;
      align-items:center;
      flex-wrap:wrap;
      gap:4px;
      min-width:0;
      line-height:1.15;
    }
    .planCard .planName{
      min-width:0;
      overflow-wrap:anywhere;
    }
```
