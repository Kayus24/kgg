# KGG Source Chunk 015

- Source: `kgg-update/src` modular source
- Lines: 6301-6720

```html
  KGGOfflineJsPDF.prototype.setDrawColor = function(){
    this._drawColor = colorFromArgs(arguments);
    return this;
  };

  KGGOfflineJsPDF.prototype.setTextColor = function(){
    this._textColor = colorFromArgs(arguments);
    return this;
  };

  KGGOfflineJsPDF.prototype.setFillColor = function(){
    this._fillColor = colorFromArgs(arguments);
    return this;
  };

  KGGOfflineJsPDF.prototype.addPage = function(_format, orientation){
    var current = this._pages[0];
    var useLandscape = String(orientation || '').toLowerCase() === 'landscape' || current.w > current.h;
    var size = resolvePageSize(Array.isArray(_format) ? _format : [current.w, current.h], useLandscape ? 'landscape' : 'portrait');
    this._page = makePage(size);
    this._pages.push(this._page);
    return this;
  };

  KGGOfflineJsPDF.prototype.rect = function(x,y,w,h,style){
    var op = String(style || '').toUpperCase().indexOf('F') >= 0 ? 'f' : 'S';
    var px = this._x(x);
    var py = this._y(y + h);
    this._push('q\n' + colorCmd(this._drawColor,'RG') + '\n' + colorCmd(this._fillColor,'rg') + '\n' +
      num(this._lineWidth * MM_TO_PT) + ' w\n' +
      num(px) + ' ' + num(py) + ' ' + num(w * MM_TO_PT) + ' ' + num(h * MM_TO_PT) + ' re ' + op + '\nQ');
    return this;
  };

  KGGOfflineJsPDF.prototype.roundedRect = function(x,y,w,h){
    return this.rect(x,y,w,h);
  };

  KGGOfflineJsPDF.prototype.line = function(x1,y1,x2,y2){
    this._push('q\n' + colorCmd(this._drawColor,'RG') + '\n' +
      num(this._lineWidth * MM_TO_PT) + ' w\n' +
      num(this._x(x1)) + ' ' + num(this._y(y1)) + ' m ' +
      num(this._x(x2)) + ' ' + num(this._y(y2)) + ' l S\nQ');
    return this;
  };

  KGGOfflineJsPDF.prototype.text = function(text,x,y,opts){
    opts = opts || {};
    var size = this._fontSize;
    var px = this._x(x);
    if(opts.align === 'right') px -= approxTextWidth(text, size);
    if(opts.align === 'center') px -= approxTextWidth(text, size) / 2;
    var py = this._y(y);
    var fontName = this._font === 'bold' ? '/F2' : '/F1';
    this._push('q\n' + colorCmd(this._textColor,'rg') + '\nBT\n' +
      fontName + ' ' + num(size) + ' Tf\n' +
      num(px) + ' ' + num(py) + ' Td\n' +
      pdfString(text) + ' Tj\nET\nQ');
    return this;
  };

  KGGOfflineJsPDF.prototype.addImage = function(dataUrl, format, x, y, w, h){
    var fmt = String(format || '').toUpperCase();
    var raw = String(dataUrl || '');
    if(fmt !== 'JPEG' && fmt !== 'JPG' && raw.slice(0, 22).toLowerCase().indexOf('data:image/jpeg') !== 0){
      return this;
    }
    var binary = binaryFromDataUrl(raw);
    if(!binary) return this;
    var size = jpegSizeFromBinary(binary);
    var name = 'Im' + (++this._imageSeq);
    this._images.push({ name: name, data: binary, width: size.w, height: size.h });
    this._page.images.push(name);
    this._push('q\n' +
      num((Number(w) || 1) * MM_TO_PT) + ' 0 0 ' + num((Number(h) || 1) * MM_TO_PT) + ' ' +
      num(this._x(x)) + ' ' + num(this._y((Number(y) || 0) + (Number(h) || 1))) + ' cm\n/' + name + ' Do\nQ');
    return this;
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
```
