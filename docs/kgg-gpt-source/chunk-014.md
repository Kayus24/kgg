# KGG Source Chunk 014

- Source: `kgg-update/index.html`
- Lines: 5881-6300

```html
    body.tabletLayoutCustom.tabletMenuOpen .app{width:calc(100vw - var(--kgg-tablet-sidebar-w))!important;transform:translateX(var(--kgg-tablet-sidebar-w))!important;grid-template-columns:var(--kgg-tablet-left-col,var(--kgg-tablet-left-menu)) minmax(0,1fr) 126px!important;}
    body.tabletLayoutCustom #scanHub{grid-template-columns:36px minmax(0,1fr) minmax(0,1fr)!important;}
    body.tabletLayoutCustom .tabletSideBackdrop,body.tabletLayoutCustom.tabletMenuOpen .tabletSideBackdrop{display:none!important;opacity:0!important;pointer-events:none!important;visibility:hidden!important;}
    body.tabletLayoutCustom .tabletSideMenu{display:flex!important;position:fixed!important;left:0!important;top:var(--kgg-tablet-safe-top)!important;bottom:auto!important;width:var(--kgg-tablet-sidebar-w)!important;min-width:var(--kgg-tablet-sidebar-w)!important;max-width:var(--kgg-tablet-sidebar-w)!important;height:calc(100dvh - var(--kgg-tablet-safe-top))!important;max-height:calc(100dvh - var(--kgg-tablet-safe-top))!important;padding:calc(env(safe-area-inset-top) + 16px) 12px calc(env(safe-area-inset-bottom) + 14px)!important;box-sizing:border-box!important;gap:18px!important;background:rgba(255,255,255,.98)!important;border-right:1px solid rgba(15,23,42,.12)!important;box-shadow:16px 0 40px rgba(15,23,42,.12)!important;transform:translateX(-100%)!important;transition:transform .22s cubic-bezier(.22,.8,.32,1)!important;z-index:1210!important;overflow-x:hidden!important;overflow-y:auto!important;visibility:visible!important;}
    body.tabletLayoutCustom.tabletMenuOpen .tabletSideMenu{transform:translateX(0)!important;}
    body.tabletLayoutCustom .tabletSideMenuHead{min-height:34px!important;padding:0!important;margin:0!important;font-size:18px!important;line-height:1!important;}
    body.tabletLayoutCustom .tabletMenuClose{width:34px!important;height:34px!important;min-width:34px!important;border-radius:999px!important;font-size:22px!important;}
    body.tabletLayoutCustom .tabletSideMenuMain{display:grid!important;gap:12px!important;margin:0!important;padding:0!important;border:0!important;}
    body.tabletLayoutCustom .tabletMenuNavAction{width:100%!important;min-height:50px!important;display:grid!important;grid-template-columns:32px minmax(0,1fr)!important;align-items:center!important;justify-items:start!important;gap:8px!important;padding:8px 8px!important;border:0!important;border-radius:12px!important;background:#fff!important;color:#071027!important;box-shadow:none!important;overflow:visible!important;text-align:left!important;font-size:13px!important;line-height:1.15!important;font-weight:950!important;white-space:normal!important;}
    body.tabletLayoutCustom .tabletMenuActionIcon{width:30px!important;height:30px!important;display:grid!important;place-items:center!important;font-size:21px!important;line-height:1!important;flex:0 0 auto!important;color:#071027!important;}
    body.tabletLayoutCustom .tabletSideMenuLayoutPanel[hidden]{display:none!important;}
    body.tabletLayoutCustom .tabletSideMenuLayoutPanel{display:grid!important;gap:8px!important;padding:8px!important;border:1px solid rgba(220,227,235,.95)!important;border-radius:12px!important;background:#f7f9fc!important;}
    body.tabletLayoutCustom .tabletSideMenu .tabletLayoutControls{display:grid!important;gap:8px!important;width:100%!important;}
    body.tabletLayoutCustom .tabletSideMenu .tabletLayoutFreeTools{display:grid!important;grid-template-columns:42px minmax(0,1fr) 42px!important;grid-template-areas:"plus value minus" "reset reset reset"!important;gap:6px!important;}
    body.tabletLayoutCustom .tabletSideMenu .tabletLayoutFreeTools.hidden{display:none!important;}
    body.tabletLayoutCustom .tabletSideMenu .tabletLayoutFreeTools button,body.tabletLayoutCustom .tabletSideMenu .tabletLockSwitch{min-height:38px!important;border-radius:10px!important;}
    body.tabletLayoutCustom #recentList:not(.hidden),body.tabletLayoutCustom #packageList:not(.hidden){display:block!important;position:fixed!important;left:calc(var(--kgg-tablet-sidebar-w) + 14px)!important;top:calc(var(--kgg-tablet-safe-top) + 58px)!important;width:min(480px,calc(100vw - var(--kgg-tablet-sidebar-w) - 34px))!important;max-height:calc(100dvh - var(--kgg-tablet-safe-top) - 86px)!important;overflow:auto!important;z-index:1205!important;background:rgba(255,255,255,.98)!important;border:1px solid rgba(220,227,235,.95)!important;border-radius:16px!important;box-shadow:0 18px 48px rgba(7,16,39,.18)!important;padding:10px!important;}
    body.tabletLayoutCustom .kggTherapistShareModal{position:fixed!important;inset:0!important;display:none!important;place-items:center!important;z-index:1320!important;background:rgba(7,16,39,.35)!important;padding:18px!important;box-sizing:border-box!important;}
    body.tabletLayoutCustom .kggTherapistShareModal.isOpen{display:grid!important;}
    .kggTherapistShareSheet{width:min(92vw,440px)!important;display:grid!important;gap:12px!important;background:#fff!important;color:#071027!important;border:2px solid #111827!important;border-radius:20px!important;padding:16px!important;box-shadow:0 22px 70px rgba(7,16,39,.24)!important;}
    .kggTherapistShareSheet h2{margin:0!important;font-size:22px!important;line-height:1.05!important;}
    .kggTherapistShareHint{margin:0!important;color:#657386!important;font-weight:800!important;}
    .kggTherapistShareChoices{display:grid!important;gap:10px!important;}
    .kggTherapistShareChoices button{min-height:62px!important;padding:10px 12px!important;border:1px solid #dce3eb!important;border-radius:14px!important;background:#fff!important;text-align:left!important;box-shadow:0 4px 14px rgba(7,16,39,.08)!important;}
    .kggTherapistShareChoices b{display:block!important;font-size:16px!important;}
    .kggTherapistShareChoices small{display:block!important;margin-top:3px!important;color:#657386!important;font-weight:800!important;line-height:1.25!important;}
  }
  /* v399: Tablet package overlay, split-handle scale control and safer scaled buttons only. */
  @media (min-width:760px){
    :root{--kgg-tablet-package-w:clamp(360px,32vw,520px);--kgg-tablet-collision-gap:14px;--kgg-tablet-button-safe-gap:clamp(10px,var(--kgg-tablet-collision-gap),28px);}
    body.tabletLayoutCustom .tabletMenuBtn{display:inline-flex!important;flex-direction:column!important;align-items:center!important;justify-content:center!important;gap:4px!important;width:44px!important;min-width:44px!important;max-width:44px!important;padding:0!important;box-sizing:border-box!important;}
    body.tabletLayoutCustom .tabletMenuBtn span{display:block!important;margin:0!important;flex:0 0 auto!important;width:24px!important;height:3px!important;}
    body.tabletLayoutCustom .app{gap:max(var(--kgg-tablet-gap),var(--kgg-tablet-button-safe-gap))!important;column-gap:max(var(--kgg-tablet-gap),var(--kgg-tablet-button-safe-gap))!important;row-gap:max(var(--kgg-tablet-gap),calc(var(--kgg-tablet-button-safe-gap) - 2px))!important;}
    body.tabletLayoutCustom .scanHub{gap:var(--kgg-tablet-button-safe-gap)!important;}
    body.tabletLayoutCustom .scanHub :is(.scanBtn,.scanMeta),body.tabletLayoutCustom #baseToggle,body.tabletLayoutCustom :is(#finishBtn,#recentToggle,#packageToggle){min-width:0!important;overflow:hidden!important;text-wrap:balance;}
    body.tabletLayoutCollisionTight .scanHub{gap:var(--kgg-tablet-button-safe-gap)!important;}
    body.tabletLayoutCollisionTight .scanHub :is(.scanBtn,.scanMeta,.adminConfigBtn,.sharedBankBtn),body.tabletLayoutCollisionTight #baseToggle{font-size:clamp(8px,calc(13px * var(--kgg-tablet-ui-scale,1)),22px)!important;line-height:1.08!important;padding:6px 8px!important;}
    body.tabletLayoutCustom .tabletLayoutResizeHandle{pointer-events:none!important;z-index:1190!important;}
    body.tabletLayoutEditMode .tabletLayoutResizeHandle{display:block!important;pointer-events:auto!important;}
    body.tabletLayoutEditMode .tabletLayoutResizeHandle::before{width:18px!important;background:rgba(255,255,255,.92)!important;border:1px solid rgba(210,218,229,.98)!important;box-shadow:0 10px 28px rgba(7,16,39,.14)!important;}
    .tabletSplitScaleControl{position:absolute;left:50%;top:50%;transform:translate(-50%,-50%);display:none;grid-template-rows:42px 34px 42px;align-items:center;justify-items:center;width:48px;padding:7px 5px;border:1px solid rgba(210,218,229,.98);border-radius:999px;background:rgba(255,255,255,.98);box-shadow:0 14px 34px rgba(7,16,39,.16),inset 0 1px 0 rgba(255,255,255,.9);gap:4px;}
    body.tabletLayoutEditMode .tabletSplitScaleControl{display:grid;}
    .tabletSplitScaleControl button{width:36px;height:36px;border-radius:999px;border:1px solid rgba(210,218,229,.98);background:#fff;color:#071027;font-size:22px;font-weight:950;line-height:1;box-shadow:0 5px 13px rgba(7,16,39,.09);}
    .tabletSplitScaleValue{font-size:12px;font-weight:950;color:#344054;line-height:1;white-space:nowrap;}
    body.tabletLayoutEditMode #tabletMenuLayoutBtn,body.tabletPackageOverlayOpen #tabletMenuPackagesBtn{background:#eef5ff!important;color:#071027!important;box-shadow:inset 3px 0 0 #0b63ce,0 8px 18px rgba(7,16,39,.08)!important;}
    body.tabletPackageOverlayOpen.tabletMenuOpen .app{width:100vw!important;transform:translateX(0)!important;}
    .tabletPackageShade{display:none;position:fixed;left:var(--kgg-tablet-sidebar-w);right:0;top:var(--kgg-tablet-safe-top);bottom:0;background:rgba(7,16,39,.42);z-index:1212;backdrop-filter:blur(1px);}
    body.tabletPackageOverlayOpen .tabletPackageShade{display:block!important;}
    .tabletPackageOverlay{display:flex;position:fixed;left:var(--kgg-tablet-sidebar-w);top:var(--kgg-tablet-safe-top);bottom:0;width:var(--kgg-tablet-package-w);max-width:calc(100vw - var(--kgg-tablet-sidebar-w) - 20px);z-index:1220;flex-direction:column;gap:14px;padding:16px 16px 18px;box-sizing:border-box;background:rgba(255,255,255,.98);border-right:1px solid rgba(15,23,42,.12);border-radius:0 20px 20px 0;box-shadow:24px 0 58px rgba(7,16,39,.18);transform:translateX(calc(-100% - var(--kgg-tablet-sidebar-w)));transition:transform .22s cubic-bezier(.22,.8,.32,1);overflow:hidden;visibility:hidden;}
    body.tabletPackageOverlayOpen .tabletPackageOverlay{transform:translate3d(0,0,0)!important;visibility:visible!important;transition:none!important;}
    .tabletPackageHead{display:flex;align-items:center;justify-content:space-between;gap:12px;min-height:38px;}
    .tabletPackageTitle{display:flex;align-items:center;gap:10px;color:#071027;font-size:20px;font-weight:950;}
    .tabletPackageTitle span{width:32px;height:32px;display:grid;place-items:center;border-radius:10px;background:#eef5ff;}
    .tabletPackageClose{width:36px;height:36px;border-radius:999px;border:1px solid rgba(220,227,235,.95);background:#fff;color:#071027;font-size:24px;font-weight:900;line-height:1;}
    .tabletPackageSearch{display:grid;grid-template-columns:24px minmax(0,1fr);align-items:center;gap:8px;min-height:46px;padding:0 12px;border:1px solid rgba(220,227,235,.95);border-radius:14px;background:#fff;box-shadow:0 4px 14px rgba(7,16,39,.05);color:#667085;}
    .tabletPackageSearch input{border:0!important;outline:0!important;background:transparent!important;font-size:14px!important;font-weight:750!important;color:#071027!important;min-width:0!important;}
    .tabletPackageCards{display:grid;gap:12px;overflow:auto;padding:2px 2px 8px;overscroll-behavior:contain;}
    .tabletPackageCard{display:grid;grid-template-columns:54px minmax(0,1fr) 30px;gap:12px;align-items:center;width:100%;min-height:118px;padding:12px;border:1px solid rgba(220,227,235,.95);border-radius:14px;background:#fff;color:#071027;text-align:left;box-shadow:0 5px 18px rgba(7,16,39,.07);}
    .tabletPackageIcon{width:48px;height:48px;display:grid;place-items:center;border-radius:12px;background:#eef5ff;font-size:24px;}
    .tabletPackageCard:nth-child(4n+2) .tabletPackageIcon{background:#f1f8e9;}
    .tabletPackageCard:nth-child(4n+3) .tabletPackageIcon{background:#f4edff;}
    .tabletPackageCard:nth-child(4n+4) .tabletPackageIcon{background:#eaf8fb;}
    .tabletPackageBody{min-width:0;display:grid;gap:7px;}
    .tabletPackageBody b{font-size:15px;font-weight:950;line-height:1.15;}
    .tabletPackageBody p{margin:0;color:#475467;font-size:12px;font-weight:750;line-height:1.32;}
    .tabletPackageMeta{display:flex;gap:8px;flex-wrap:wrap;}
    .tabletPackageMeta span{display:inline-flex;align-items:center;min-height:24px;padding:0 8px;border:1px solid rgba(220,227,235,.95);border-radius:999px;background:#f8fafc;color:#344054;font-size:11px;font-weight:900;}
    .tabletPackageArrow{font-size:26px;color:#071027;font-weight:950;text-align:center;}
    .tabletPackageEmpty{padding:18px;border:1px dashed rgba(148,163,184,.8);border-radius:14px;background:#f8fafc;color:#667085;font-weight:850;line-height:1.35;}
  }
</style>

  <script>
    /* KGG v182 mobile single-file: inline offline PDF runtime, no external file needed. */
/*
 * KGG offline PDF runtime shim.
 * Provides the small jsPDF API surface used by kgg_plan_generator_v178/v179.
 * No network, no API keys, no JSON output.
 */
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
```
