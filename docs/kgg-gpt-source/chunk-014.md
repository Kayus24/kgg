# KGG Source Chunk 014

- Source: `kgg-update/index.html`
- Lines: 5881-6300

```html
(function(global){
  'use strict';

  var MM_TO_PT = 72 / 25.4;
  var PAGE_SIZES = {
    a4: { portrait: { w: 210, h: 297 }, landscape: { w: 297, h: 210 } }
  };

  function resolvePageSize(format, orientation){
    var isLandscape = String(orientation || 'portrait').toLowerCase() === 'landscape';
    if(Array.isArray(format) && format.length >= 2){
      var w = Number(format[0]) || 297;
      var h = Number(format[1]) || 210;
      if(isLandscape && w < h){ var tmp = w; w = h; h = tmp; }
      if(!isLandscape && w > h){ var tmp2 = w; w = h; h = tmp2; }
      return { w: w, h: h };
    }
    var key = String(format || 'a4').toLowerCase();
    return (PAGE_SIZES[key] && PAGE_SIZES[key][isLandscape ? 'landscape' : 'portrait']) || PAGE_SIZES.a4.landscape;
  }

  function clampByte(value){
    value = Number(value);
    if(!isFinite(value)) return 0;
    return Math.max(0, Math.min(255, value));
  }

  function colorFromArgs(args){
    if(args.length === 1){
      var g = clampByte(args[0]);
      return [g, g, g];
    }
    return [clampByte(args[0]), clampByte(args[1]), clampByte(args[2])];
  }

  function colorCmd(color, op){
    return (color[0] / 255).toFixed(3) + ' ' +
      (color[1] / 255).toFixed(3) + ' ' +
      (color[2] / 255).toFixed(3) + ' ' + op;
  }

  function num(value){
    value = Number(value);
    if(!isFinite(value)) value = 0;
    return String(Math.round(value * 1000) / 1000);
  }

  function sanitizeText(value){
    return String(value == null ? '' : value)
      .replace(/ä/g,'ae').replace(/ö/g,'oe').replace(/ü/g,'ue')
      .replace(/Ä/g,'Ae').replace(/Ö/g,'Oe').replace(/Ü/g,'Ue')
      .replace(/ß/g,'ss')
      .replace(/[–—]/g,'-').replace(/…/g,'...')
      .replace(/[·•]/g,' - ')
      .replace(/[^\x09\x0A\x0D\x20-\x7E]/g,'');
  }

  function pdfString(value){
    return '(' + sanitizeText(value).replace(/\\/g,'\\\\').replace(/\(/g,'\\(').replace(/\)/g,'\\)') + ')';
  }

  function approxTextWidth(text, fontSize){
    return sanitizeText(text).length * fontSize * 0.48;
  }

  function makePage(size){
    return { w: size.w, h: size.h, ops: [], images: [] };
  }

  function binaryFromDataUrl(dataUrl){
    var raw = String(dataUrl || '');
    var comma = raw.indexOf(',');
    if(comma < 0) return '';
    var header = raw.slice(0, comma).toLowerCase();
    var data = raw.slice(comma + 1);
    if(header.indexOf(';base64') >= 0){
      try{ return atob(data); }catch(e){ return ''; }
    }
    try{ return decodeURIComponent(data); }catch(e){ return data; }
  }

  function jpegSizeFromBinary(binary){
    if(!binary || binary.length < 4) return { w: 1, h: 1 };
    function byte(i){ return binary.charCodeAt(i) & 255; }
    if(byte(0) !== 255 || byte(1) !== 216) return { w: 1, h: 1 };
    var i = 2;
    while(i + 8 < binary.length){
      while(i < binary.length && byte(i) !== 255) i++;
      while(i < binary.length && byte(i) === 255) i++;
      var marker = byte(i++);
      if(marker === 217 || marker === 218) break;
      if(i + 2 > binary.length) break;
      var len = (byte(i) << 8) | byte(i + 1);
      if(len < 2 || i + len > binary.length) break;
      if((marker >= 192 && marker <= 195) || (marker >= 197 && marker <= 199) || (marker >= 201 && marker <= 203) || (marker >= 205 && marker <= 207)){
        return { h: ((byte(i + 3) << 8) | byte(i + 4)) || 1, w: ((byte(i + 5) << 8) | byte(i + 6)) || 1 };
      }
      i += len;
    }
    return { w: 1, h: 1 };
  }

  function KGGOfflineJsPDF(options){
    options = options || {};
    var orientation = String(options.orientation || 'portrait').toLowerCase();
    var size = resolvePageSize(options.format || 'a4', orientation);
    this._pages = [makePage(size)];
    this._page = this._pages[0];
    this._font = 'normal';
    this._fontSize = 10;
    this._lineWidth = 0.2;
    this._drawColor = [0,0,0];
    this._textColor = [0,0,0];
    this._fillColor = [0,0,0];
    this._properties = {};
    this._imageSeq = 0;
    this._images = [];
    this.internal = {
      pageSize: {
        width: size.w,
        height: size.h,
        getWidth: function(){ return size.w; },
        getHeight: function(){ return size.h; }
      }
    };
  }

  KGGOfflineJsPDF.prototype._x = function(x){ return x * MM_TO_PT; };
  KGGOfflineJsPDF.prototype._y = function(y){ return this._page.h * MM_TO_PT - y * MM_TO_PT; };
  KGGOfflineJsPDF.prototype._push = function(cmd){ this._page.ops.push(cmd); };

  KGGOfflineJsPDF.prototype.setProperties = function(props){
    this._properties = props || {};
    return this;
  };

  KGGOfflineJsPDF.prototype.setFont = function(_family, style){
    this._font = /bold/i.test(String(style || '')) ? 'bold' : 'normal';
    return this;
  };

  KGGOfflineJsPDF.prototype.setFontSize = function(size){
    this._fontSize = Number(size) || this._fontSize;
    return this;
  };

  KGGOfflineJsPDF.prototype.setLineWidth = function(width){
    this._lineWidth = Number(width) || 0.1;
    return this;
  };

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
```
