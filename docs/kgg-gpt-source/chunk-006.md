# KGG Source Chunk 006

- Source: `kgg-update/index.html`
- Lines: 2521-2940

```html
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
          width:74px!important;
          min-width:74px!important;
          max-width:74px!important;
          height:34px!important;
          min-height:34px!important;
          margin:12px 10px 0 0!important;
          padding:0 8px!important;
        }
      }
    }




    /* v331 Tablet Left Column + Scale Up:
       - linke Spalte bekommt mehr Raum zur Mitte
       - gesamtes Tablet-Layout wieder leicht größer
       - keine Logikänderung */
    @media (min-width:760px){
      .app{
        grid-template-columns:minmax(395px,475px) minmax(0,1fr) minmax(0,.92fr)!important;
        gap:16px!important;
      }

      #inputWrap textarea,
      #exerciseInput{
        font-size:21px!important;
        line-height:1.34!important;
      }
      #inputWrap textarea{
        min-height:106px!important;
      }

      .scanBtn,
      .scanMeta.filePickBtn,
      #baseToggle,
      #finishBtn{
        font-size:19px!important;
      }

      .bankArea.bankOpen.alphaBankOpen .bankWithAz{
        grid-template-columns:60px minmax(0,1fr)!important;
        column-gap:10px!important;
      }
      .bankArea.bankOpen.alphaBankOpen .az{
        width:48px!important;
      }
      .az button{
        font-size:12px!important;
        min-height:18px!important;
      }
      .bankRow{
        padding:12px 14px!important;
      }
      .bankRow b{
        font-size:17px!important;
      }
      .bankRow small{
        font-size:12px!important;
      }

      #createPanel.planMode #currentPlanToggle{
        min-height:56px!important;
        font-size:21px!important;
      }
      .planCard{
        padding:14px 16px!important;
      }
      .planCard b{
        font-size:18px!important;
      }
      .planCard small{
        font-size:12px!important;
      }

      #createPanel.planMode #recentToggle,
      #createPanel.planMode #packageToggle{
        height:64px!important;
        min-height:64px!important;
        font-size:18px!important;
      }
    }

    @media (min-width:760px) and (max-width:920px){
      .app{
        grid-template-columns:minmax(350px,420px) minmax(0,1fr) minmax(0,.92fr)!important;
        gap:14px!important;
      }
      #inputWrap textarea,
      #exerciseInput{
        font-size:20px!important;
      }
      .bankRow b{
        font-size:16px!important;
      }
      .planCard b{
        font-size:17px!important;
      }
    }



    /* v332 Tablet Left Column More Width + Readability:
       - linke Spalte nochmals breiter
       - Tablet-Gesamtlayout etwas größer für bessere Lesbarkeit
       - keine Logikänderung */
    @media (min-width:760px){
      .app{
        grid-template-columns:minmax(430px,520px) minmax(0,1.08fr) minmax(0,.88fr)!important;
        gap:18px!important;
        padding:18px!important;
      }

      .scanHub{
        gap:12px!important;
      }
      .scanBtn,
      .scanMeta.filePickBtn,
      #baseToggle,
      #finishBtn,
      #recentToggle,
      #packageToggle{
        font-size:20px!important;
      }
      #baseToggle,
      #finishBtn{
        min-height:62px!important;
      }

      #inputWrap textarea,
      #exerciseInput{
        font-size:22px!important;
        line-height:1.36!important;
      }
      #inputWrap textarea{
        min-height:118px!important;
        padding:18px 48px 18px 16px!important;
      }

      .bankArea.bankOpen.alphaBankOpen .bankWithAz{
        grid-template-columns:64px minmax(0,1fr)!important;
        column-gap:12px!important;
      }
      .bankArea.bankOpen.alphaBankOpen .az{
        width:52px!important;
        margin-top:68px!important;
      }
      .az button{
        font-size:12.5px!important;
        min-height:20px!important;
      }
      .bankRows{
        max-height:none!important;
      }
      .bankRow{
        padding:13px 15px!important;
      }
      .bankRow b{
        font-size:18px!important;
      }
      .bankRow small{
        font-size:12px!important;
      }

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
```
