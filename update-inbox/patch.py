#!/usr/bin/env python3
from pathlib import Path
import hashlib
import json
import re
import urllib.request

INDEX = Path('kgg-update/index.html')
VERSION = Path('kgg-update/version.json')
URL = 'https://cdn.jsdelivr.net/npm/jsqr@1.4.0/dist/jsQR.js'
PID = 'kgg-v021-embed-jsqr-gallery-decode'

def put_before(html, end_tag, block):
    m = re.search(end_tag, html, re.I)
    return html[:m.start()] + block + '\n' + html[m.start():] if m else html + '\n' + block

def norm(html):
    html = html.lstrip('\ufeff\r\n\t ')
    m = re.search(r'(?is)<!doctype\s+html\s*>', html[:500])
    if not m:
        raise SystemExit('missing doctype')
    html = html[m.start():]
    return re.sub(r'(?is)^<!doctype\s+html\s*>', '<!doctype html>', html, 1)

def script_tag(script_id, body):
    return '<script id="' + script_id + '">\n' + body + '\n</script>\n'

def main():
    html = norm(INDEX.read_text(encoding='utf-8'))

    if PID + '-lib' not in html:
        js = urllib.request.urlopen(URL, timeout=30).read().decode('utf-8')
        if 'jsQR' not in js[:100000]:
            raise SystemExit('jsQR source validation failed')
        sha = hashlib.sha256(js.encode('utf-8')).hexdigest()
        block = '\n<!-- KGG PATCH START ' + PID + ' lib sha256=' + sha + ' -->\n' + script_tag(PID + '-lib', js) + '<!-- KGG PATCH END ' + PID + ' lib -->\n'
        html = put_before(html, r'</head\s*>', block)

    if PID + '-wrapper' not in html:
        wrapper = r"""
(function(){
  var oldDetect = window.detectQrOnCanvas;
  function getImageData(canvas){
    try{
      var ctx = canvas && canvas.getContext && canvas.getContext('2d',{willReadFrequently:true});
      return ctx ? ctx.getImageData(0,0,canvas.width,canvas.height) : null;
    }catch(e){ return null; }
  }
  function jsqrFallback(canvas){
    if(!canvas || typeof window.jsQR !== 'function') return '';
    var img = getImageData(canvas);
    if(!img) return '';
    try{
      var hit = window.jsQR(img.data, canvas.width, canvas.height, {inversionAttempts:'attemptBoth'});
      return hit && hit.data ? String(hit.data) : '';
    }catch(e){ return ''; }
  }
  async function wrappedDetect(canvas, detector){
    if(typeof oldDetect === 'function' && oldDetect !== wrappedDetect){
      try{
        var oldResult = await oldDetect(canvas, detector);
        if(oldResult) return oldResult;
      }catch(e){}
    }
    return jsqrFallback(canvas);
  }
  try{ window.detectQrOnCanvas = wrappedDetect; }catch(e){}
  try{ detectQrOnCanvas = wrappedDetect; }catch(e){}
  window.KGG_QR_GALLERY_DEBUG = {
    patchId: 'kgg-v021-embed-jsqr-gallery-decode',
    check: function(){ return { patchId:this.patchId, jsQR:typeof window.jsQR==='function', detectQrOnCanvas:typeof window.detectQrOnCanvas }; }
  };
})();
"""
        block = '\n<!-- KGG PATCH START ' + PID + ' wrapper -->\n' + script_tag(PID + '-wrapper', wrapper) + '<!-- KGG PATCH END ' + PID + ' wrapper -->\n'
        html = put_before(html, r'</body\s*>', block)

    if 'KGG_QR_GALLERY_DEBUG' not in html:
        raise SystemExit('wrapper validation failed')
    INDEX.write_text(html, encoding='utf-8', newline='\n')

    if VERSION.exists():
        data = json.loads(VERSION.read_text(encoding='utf-8'))
        code = data.get('versionCode', 0)
        if isinstance(code, int):
            data['indexUrl'] = 'index.html?v=' + str(code + 1)
            VERSION.write_text(json.dumps(data, ensure_ascii=False, indent=2) + '\n', encoding='utf-8', newline='\n')

    print('Applied ' + PID)

if __name__ == '__main__':
    main()
