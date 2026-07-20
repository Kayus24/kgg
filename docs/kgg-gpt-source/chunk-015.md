# KGG Source Chunk 015

- Source: `kgg-update/src` modular source
- Lines: 6301-6720

```html
  };

  function objectString(id, body){
    return id + ' 0 obj\n' + body + '\nendobj\n';
  }

  function streamObject(id, stream){
    return objectString(id, '<< /Length ' + stream.length + ' >>\nstream\n' + stream + '\nendstream');
  }

  function infoString(props){
    props = props || {};
    return '<< /Title ' + pdfString(props.title || 'KGG Trainingsplan') +
      ' /Subject ' + pdfString(props.subject || '') +
      ' /Creator ' + pdfString(props.creator || 'KGG offline PDF runtime') + ' >>';
  }

  KGGOfflineJsPDF.prototype._buildPdf = function(){
    var objects = [];
    var pagesRootId = 2;
    var fontRegularId = 3;
    var fontBoldId = 4;
    var infoId = 5;
    var nextId = 6;
    var pageIds = [];
    var contentIds = [];
    var imageIds = {};
    var self = this;

    this._pages.forEach(function(page){
      pageIds.push(nextId++);
      contentIds.push(nextId++);
    });
    this._images.forEach(function(image){
      imageIds[image.name] = nextId++;
    });

    objects.push(objectString(1, '<< /Type /Catalog /Pages ' + pagesRootId + ' 0 R >>'));
    objects.push(objectString(fontRegularId, '<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>'));
    objects.push(objectString(fontBoldId, '<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica-Bold >>'));
    objects.push(objectString(infoId, infoString(this._properties)));

    var kids = pageIds.map(function(id){ return id + ' 0 R'; }).join(' ');
    objects.push(objectString(pagesRootId, '<< /Type /Pages /Kids [' + kids + '] /Count ' + pageIds.length + ' >>'));

    this._pages.forEach(function(page, index){
      var content = page.ops.join('\n') + '\n';
      var xObjects = '';
      if(page.images && page.images.length){
        var seen = {};
        var refs = page.images.filter(function(name){ if(seen[name]) return false; seen[name] = true; return true; })
          .map(function(name){ return '/' + name + ' ' + imageIds[name] + ' 0 R'; }).join(' ');
        xObjects = ' /XObject << ' + refs + ' >>';
      }
      objects.push(objectString(pageIds[index],
        '<< /Type /Page /Parent ' + pagesRootId + ' 0 R /MediaBox [0 0 ' +
        num(page.w * MM_TO_PT) + ' ' + num(page.h * MM_TO_PT) + '] /Resources << /Font << /F1 ' +
        fontRegularId + ' 0 R /F2 ' + fontBoldId + ' 0 R >>' + xObjects + ' >> /Contents ' + contentIds[index] + ' 0 R >>'));
      objects.push(streamObject(contentIds[index], content));
    });

    this._images.forEach(function(image){
      objects.push(objectString(imageIds[image.name],
        '<< /Type /XObject /Subtype /Image /Width ' + Math.max(1, Number(image.width) || 1) +
        ' /Height ' + Math.max(1, Number(image.height) || 1) +
        ' /ColorSpace /DeviceRGB /BitsPerComponent 8 /Filter /DCTDecode /Length ' + image.data.length +
        ' >>\nstream\n' + image.data + '\nendstream'));
    });

    objects.sort(function(a,b){ return Number(a.match(/^(\d+)/)[1]) - Number(b.match(/^(\d+)/)[1]); });
    var pdf = '%PDF-1.4\n%\xE2\xE3\xCF\xD3\n';
    var offsets = [0];
    objects.forEach(function(obj){
      offsets.push(pdf.length);
      pdf += obj;
    });
    var xrefStart = pdf.length;
    pdf += 'xref\n0 ' + offsets.length + '\n0000000000 65535 f \n';
    for(var i=1;i<offsets.length;i++){
      pdf += String(offsets[i]).padStart(10,'0') + ' 00000 n \n';
    }
    pdf += 'trailer\n<< /Size ' + offsets.length + ' /Root 1 0 R /Info ' + infoId + ' 0 R >>\nstartxref\n' + xrefStart + '\n%%EOF';
    return pdf;
  };

  KGGOfflineJsPDF.prototype.save = function(filename){
    var pdf = this._buildPdf();
    var bytes = new Uint8Array(pdf.length);
    for(var i=0;i<pdf.length;i++) bytes[i] = pdf.charCodeAt(i) & 255;
    var blob = new Blob([bytes], {type:'application/pdf'});
    var url = URL.createObjectURL(blob);
    var a = document.createElement('a');
    a.href = url;
    a.download = filename || 'kgg_trainingsplan.pdf';
    document.body.appendChild(a);
    a.click();
    setTimeout(function(){ URL.revokeObjectURL(url); a.remove(); }, 1000);
    return this;
  };

  global.jspdf = global.jspdf || {};
  global.jspdf.jsPDF = KGGOfflineJsPDF;
  global.jsPDF = global.jsPDF || KGGOfflineJsPDF;
})(window);

  </script>

  <script>
    // PDF-Testversion: jsPDF wird local-first geladen, damit PDF weiter lokal im Browser erzeugt wird.
    // GitHub Pages bleibt nur fuer die Patienten-App-Shell, nicht fuer PDF-Erzeugung.
    window.KGG_JSPDF_TEST_SOURCES = window.KGG_JSPDF_TEST_SOURCES || [];
    window.KGG_JSPDF_TEST_LOAD_STATE = window.KGG_JSPDF_TEST_LOAD_STATE || {status:'idle', index:0, error:null, promise:null};
    window.KGGLoadJsPdfForTest = function KGGLoadJsPdfForTest(){
      if((window.jspdf && window.jspdf.jsPDF) || window.jsPDF) return Promise.resolve((window.jspdf&&window.jspdf.jsPDF)||window.jsPDF);
      const state = window.KGG_JSPDF_TEST_LOAD_STATE;
      if(state.promise) return state.promise;
      const sources = window.KGG_JSPDF_TEST_SOURCES || [];
      state.status = 'loading';
      state.promise = new Promise((resolve,reject)=>{
        function trySource(i){
          state.index = i;
          if((window.jspdf && window.jspdf.jsPDF) || window.jsPDF){
            state.status = 'loaded';
            resolve((window.jspdf&&window.jspdf.jsPDF)||window.jsPDF);
            return;
          }
          if(i >= sources.length){
            state.status = 'failed';
            state.error = 'jsPDF konnte aus keiner Testquelle geladen werden.';
            reject(new Error(state.error));
            return;
          }
          const script = document.createElement('script');
          script.src = sources[i];
          script.async = true;
          script.onload = function(){
            const ctor = (window.jspdf&&window.jspdf.jsPDF)||window.jsPDF||null;
            if(ctor){
              state.status = 'loaded';
              resolve(ctor);
            }else{
              trySource(i+1);
            }
          };
          script.onerror = function(){trySource(i+1);};
          document.head.appendChild(script);
        }
        trySource(0);
      });
      return state.promise;
    };
    window.KGGLoadJsPdfForTest();
  </script>

<style id="kgg-mini-patch-v400-01-menu-icon-stays-hamburger">
  /* v400 mini01: Tablet-Menü-Icon bleibt Hamburger.
     Nur UI-CSS. Keine PDF/QR/Scan/Parser/Plan-State-Logik. */
  @media (min-width:760px){
    body.tabletMenuOpen .tabletMenuBtn span:nth-child(1),
    body.tabletMenuOpen .tabletMenuBtn span:nth-child(2),
    body.tabletMenuOpen .tabletMenuBtn span:nth-child(3){
      transform:none!important;
      opacity:1!important;
    }
  }
</style>


<style id="kgg-mini-patch-v400-03-menu-handle-layout-persists">
  /* v400 mini03: Seitenmenü-Handle + Layout-Bearbeitung bleibt aktiv.
     Nur Tablet-UI. Keine PDF/QR/Scan/Parser/Patient-App/Plan-State-Logik. */
  @media (min-width:760px){
    body.tabletLayoutCustom .tabletMenuBtn{
      border:1px solid rgba(10,16,36,.18)!important;
      background:#fff!important;
      box-shadow:0 1px 3px rgba(10,16,36,.12),inset 0 1px 0 rgba(255,255,255,.9)!important;
      backdrop-filter:none!important;
      -webkit-backdrop-filter:none!important;
      transform:none!important;
      outline:none!important;
    }
    body.tabletLayoutCustom .tabletMenuBtn span{
      transform:none!important;
      opacity:1!important;
      background:#0a1024!important;
      box-shadow:none!important;
    }
    body.tabletLayoutCustom.tabletMenuOpen .tabletMenuBtn{
      position:fixed!important;
      left:calc(var(--kgg-tablet-sidebar-w) - 1px)!important;
      top:calc(var(--kgg-tablet-safe-top) + 18px)!important;
      right:auto!important;
      bottom:auto!important;
      width:42px!important;
      min-width:42px!important;
      height:68px!important;
      min-height:68px!important;
      padding:0!important;
      display:grid!important;
      place-items:center!important;
      border-left:0!important;
      border-radius:0 16px 16px 0!important;
      background:rgba(255,255,255,.985)!important;
      box-shadow:7px 0 18px rgba(10,16,36,.10), inset 1px 0 0 rgba(255,255,255,.95)!important;
      z-index:1230!important;
    }
    body.tabletLayoutCustom.tabletMenuOpen .tabletMenuBtn::before{
      content:"";
      position:absolute;
      left:-1px;
      top:0;
      bottom:0;
      width:2px;
      background:rgba(255,255,255,.985);
    }
    body.tabletLayoutCustom.tabletMenuOpen .tabletMenuBtn span{
      width:22px!important;
      height:3px!important;
      margin:2.5px 0!important;
      border-radius:999px!important;
    }
    body.tabletLayoutCustom.tabletMenuOpen .tabletMenuBtn span:nth-child(1),
    body.tabletLayoutCustom.tabletMenuOpen .tabletMenuBtn span:nth-child(2),
    body.tabletLayoutCustom.tabletMenuOpen .tabletMenuBtn span:nth-child(3){
      transform:none!important;
      opacity:1!important;
    }
    body.tabletLayoutEditMode .tabletLayoutResizeHandle,
    body.tabletLayoutEditMode .tabletSplitScaleControl{
      pointer-events:auto!important;
    }
  }
</style>

<style id="kgg-mini-patch-v400-04-phone-clean-tablet-ui-guard">
  /* v400 mini04: Phone-Clean-Guard.
     Ziel: Tablet-/Admin-/Weitergabe-Overlays dürfen im echten Handy-Layout nicht sichtbar werden.
     Scope: nur max-width:759px. Tablet-Layout ab 760px bleibt unangetastet.
     Keine PDF-/QR-/Scan-/Parser-/Plan-State-Logik. */
  @media (max-width:759px){
    html,body{
      min-width:0!important;
      overflow-x:hidden!important;
    }
    #tabletMenuBtn,
    #tabletSideMenu,
    #tabletSideBackdrop,
    #tabletPackageShade,
    #tabletPackageOverlay,
    #tabletLayoutResizeHandle,
    #tabletSplitScaleControl,
    .tabletMenuBtn,
    .tabletSideMenu,
    .tabletSideBackdrop,
    .tabletPackageShade,
    .tabletPackageOverlay,
    .tabletLayoutResizeHandle,
    .tabletSplitScaleControl{
      display:none!important;
      visibility:hidden!important;
      opacity:0!important;
      pointer-events:none!important;
      transform:none!important;
    }
    #kggTherapistShareModal,
    #kggAdminMenuQrModal,
    .kggTherapistShareModal,
    .kggAdminMenuQrModal{
      display:none!important;
      visibility:hidden!important;
      opacity:0!important;
      pointer-events:none!important;
    }
    body.tabletMenuOpen #tabletSideMenu,
    body.tabletMenuOpen .tabletSideMenu,
    body.tabletPackageOverlayOpen #tabletPackageOverlay,
    body.tabletPackageOverlayOpen .tabletPackageOverlay{
      display:none!important;
      transform:none!important;
    }
    body.tabletMenuOpen,
    body.tabletPackageOverlayOpen,
    body.tabletLayoutEditMode{
      overflow-x:hidden!important;
    }
  }
</style>


<style id="kgg-mini-patch-v400-05-phone-remove-grey-helper-text">
  /* v400 mini05: Phone-only cleanup.
     Entfernt die grauen Hilfs-/Beschreibungstexte in Phone-Drawern und der
     Therapeuten-App-Auswahl, ohne Tablet-Layout/CSS ab 760px anzufassen. */
  @media (max-width:759px){
    .kggTherapistShareHint,
    .kggTherapistShareChoices small,
    #packageList .notice small,
    .tabletPackageBody p{
      display:none!important;
    }

    #packageList .notice b + br,
    #packageList .notice small + br{
      display:none!important;
    }

    .kggTherapistShareChoices button{
      min-height:48px!important;
      display:flex!important;
      align-items:center!important;
      padding:12px 14px!important;
    }

    .kggTherapistShareChoices b{
      font-size:16px!important;
      line-height:1.15!important;
    }

    #packageList .notice{
      display:grid!important;
      gap:8px!important;
    }

    #packageList .notice .mutedBtn{
      margin-top:0!important;
    }
  }
</style>



<style id="kgg-mini-patch-v400-06-phone-plan-gesture-fix">
  /* v400 mini06: Phone-only Plan-Karten Gesten-Fix.
     Scope: nur Handy-Layout bis 759px. Tablet-Layout ab 760px bleibt unveraendert.
     Repariert Swipe links/rechts und Drag-Reorder, die durch den Phone-Scroll-Guard
     transform/transition auf den Uebungskarten blockiert wurden. */
  @media (max-width:759px){
    body.kggPlanCardSwiping .planCard.swipe-dragging{
      transform:translateX(var(--kgg-plan-swipe-x,0px))!important;
      will-change:transform,opacity!important;
    }
    body.kggPlanCardSwiping .planCard.swipe-armed{
      transform:translateX(var(--kgg-plan-swipe-x,0px))!important;
    }
    body.kggPlanCardReordering .planCard.reorder-lifted,
    body.is-scrolling .planCard.reorder-lifted{
      transform:translateY(var(--drag-y,0px)) scale(1.035)!important;
      transition:none!important;
      will-change:transform!important;
      pointer-events:none!important;
    }
    body.kggPlanCardReordering .planList.reorder-active .planCard:not(.reorder-lifted){
      transition:transform .14s ease,margin .14s ease,opacity .14s ease!important;
    }
    body.kggPlanCardReordering .planCard.reorder-placeholder{
      display:block!important;
      visibility:visible!important;
    }
  }
</style>




<style id="kgg-mini-patch-v400-07-android-wrapper-fixes">
  /* v400 mini07: Android-WebView/Phone polish.
     Scope: UI-only. Tablet layout ab 760px bleibt unveraendert. */
  @media (max-width:759px){
    body.kggPlanCardReordering #bankArea,
    body.kggPlanCardReordering #dbTitle,
    body.kggPlanCardReordering .bankArea,
    body.kggPlanCardReordering .bankRows,
    body.kggPlanCardReordering .az{
      pointer-events:none!important;
    }
    body.kggPlanCardReordering .planCard.reorder-lifted,
    body.is-scrolling.kggPlanCardReordering .planCard.reorder-lifted{
      transform:translateY(var(--drag-y,0px)) scale(1.035)!important;
      z-index:9999!important;
      transition:none!important;
      will-change:transform!important;
      pointer-events:none!important;
    }
    body.kggPlanCardSwiping .planCard.swipe-dragging,
    body.is-scrolling.kggPlanCardSwiping .planCard.swipe-dragging{
      transform:translateX(var(--kgg-plan-swipe-x,0px))!important;
      transition:none!important;
      will-change:transform,opacity!important;
    }
    body.kggPlanCardSwiping .planCard.swipe-removing,
    body.is-scrolling.kggPlanCardSwiping .planCard.swipe-removing{
      transform:translateX(var(--kgg-plan-swipe-x,0px))!important;
    }
    .modal.open{
      overscroll-behavior:contain;
    }
    .sheet{
      -webkit-overflow-scrolling:touch;
    }
  }
</style>

<style id="kgg-github-patch-v401-phone-plan-ui-isolation">
  /* v401 GitHub Update 003: Phone-only Plan-UI Stabilisierung.
     Fixes:
     - Plan-Karten flackern beim Scrollen nicht mehr.
     - Antippen/Anheben einer Plan-Karte darf den Rest der App nicht nach unten schieben.
     - Reorder-Bewegungen bleiben innerhalb "Übungen im Plan".
     Scope: nur max-width:759px. Tablet-/Wrapper-Code bleibt unverändert. */
  @media (max-width:759px){
    #rightPlanStack,
    #currentPlanBlock.planSectionCurrent{
      contain:layout paint!important;
      overflow:hidden!important;
      transform:translateZ(0);
      backface-visibility:hidden;
      -webkit-backface-visibility:hidden;
    }

    body.kggPlanSectionFrozen #currentPlanBlock.planSectionCurrent{
```
