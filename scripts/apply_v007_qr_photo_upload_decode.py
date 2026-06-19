#!/usr/bin/env python3
from pathlib import Path
import hashlib
import json
import sys

HTML_PATH = Path("kgg-update/index.html")
VERSION_PATH = Path("kgg-update/version.json")
VERSION_CODE_MIN = 7
VERSION_NAME = "1.0.4-qr-photo-upload-decode"
PATCH_MARKER = "kgg-mini-patch-v400-09-qr-photo-upload-decode"

def fail(message: str) -> None:
    print("ERROR:", message)
    sys.exit(1)

def replace_between(text: str, start_token: str, end_token: str, replacement: str) -> str:
    start = text.find(start_token)
    if start < 0:
        fail(f"Start token not found: {start_token!r}")
    end = text.find(end_token, start)
    if end < 0:
        fail(f"End token not found after {start_token!r}: {end_token!r}")
    return text[:start] + replacement.rstrip() + "\n  " + text[end:]

def main() -> None:
    if not HTML_PATH.exists():
        fail(f"{HTML_PATH} not found")
    if not VERSION_PATH.exists():
        fail(f"{VERSION_PATH} not found")

    html = HTML_PATH.read_text(encoding="utf-8")

    if not html.lstrip().lower().startswith("<!doctype html>"):
        idx = html.lower().find("<!doctype html>")
        if idx < 0:
            fail("<!doctype html> not found")
        print(f"Normalizing doctype: removed {idx} leading characters")
        html = html[idx:]

    image_loader_code = r'''
  /* kgg-mini-patch-v400-09-qr-photo-upload-decode
     Robustere QR-Erkennung fuer Bilder aus Galerie/Foto-Datenbank.
     Kamera-Scan bleibt unveraendert; nur Datei-/Bild-Decoding wird verbessert.
  */
  function scanReadFileAsDataUrl(file){
    return new Promise((resolve,reject)=>{
      const reader=new FileReader();
      reader.onload=()=>resolve(String(reader.result||''));
      reader.onerror=()=>reject(reader.error||new Error('Bild konnte nicht gelesen werden'));
      reader.readAsDataURL(file);
    });
  }
  function scanCanvasFromImageSource(source,width,height,maxSide){
    const srcW=Math.max(1,Math.round(width||source.naturalWidth||source.videoWidth||source.width||1));
    const srcH=Math.max(1,Math.round(height||source.naturalHeight||source.videoHeight||source.height||1));
    const limit=Math.max(320,Number(maxSide)||2200);
    const scale=Math.min(1,limit/Math.max(1,srcW,srcH));
    const canvas=document.createElement('canvas');
    canvas.width=Math.max(1,Math.round(srcW*scale));
    canvas.height=Math.max(1,Math.round(srcH*scale));
    const ctx=canvas.getContext('2d',{willReadFrequently:true});
    ctx.fillStyle='#fff';
    ctx.fillRect(0,0,canvas.width,canvas.height);
    ctx.imageSmoothingEnabled=true;
    ctx.imageSmoothingQuality='high';
    ctx.drawImage(source,0,0,canvas.width,canvas.height);
    return canvas;
  }
  function scanImageElementFromUrl(url){
    return new Promise((resolve,reject)=>{
      const img=new Image();
      img.onload=()=>resolve(img);
      img.onerror=()=>reject(new Error('Bild konnte nicht gelesen werden'));
      img.decoding='async';
      img.src=url;
    });
  }
  async function scanImageCanvasFromFile(file,maxSide){
    const limit=Math.max(320,Number(maxSide)||2200);
    if(window.createImageBitmap){
      try{
        const bitmap=await createImageBitmap(file,{imageOrientation:'from-image'});
        try{return scanCanvasFromImageSource(bitmap,bitmap.width,bitmap.height,limit);}
        finally{try{bitmap.close();}catch(closeErr){}}
      }catch(bitmapErr){
        console.warn('QR-Dateibild: createImageBitmap fehlgeschlagen, fallback auf Image/FileReader.',bitmapErr);
      }
    }
    let url='';
    try{
      url=URL.createObjectURL(file);
      const img=await scanImageElementFromUrl(url);
      return scanCanvasFromImageSource(img,img.naturalWidth||img.width,img.naturalHeight||img.height,limit);
    }catch(objectUrlErr){
      console.warn('QR-Dateibild: ObjectURL fehlgeschlagen, fallback auf DataURL.',objectUrlErr);
      try{
        const dataUrl=await scanReadFileAsDataUrl(file);
        const img=await scanImageElementFromUrl(dataUrl);
        return scanCanvasFromImageSource(img,img.naturalWidth||img.width,img.naturalHeight||img.height,limit);
      }catch(dataUrlErr){
        throw dataUrlErr||objectUrlErr||new Error('Bild konnte nicht gelesen werden');
      }
    }finally{
      if(url){try{URL.revokeObjectURL(url);}catch(revokeErr){}}
    }
  }
'''
    html = replace_between(
        html,
        "  function scanImageCanvasFromFile(file,maxSide){",
        "function scanCloneCanvas(src){",
        image_loader_code
    )

    qr_decode_code = r'''
  function scanScaleCanvas(src,minSide,maxSide){
    const shortest=Math.max(1,Math.min(src.width,src.height));
    const longest=Math.max(1,Math.max(src.width,src.height));
    const minTarget=Math.max(120,Number(minSide)||0);
    const maxTarget=Math.max(minTarget,Number(maxSide)||2600);
    let scale=1;
    if(minTarget&&shortest<minTarget)scale=minTarget/shortest;
    if(longest*scale>maxTarget)scale=maxTarget/longest;
    if(Math.abs(scale-1)<0.03)return src;
    const canvas=document.createElement('canvas');
    canvas.width=Math.max(1,Math.round(src.width*scale));
    canvas.height=Math.max(1,Math.round(src.height*scale));
    const ctx=canvas.getContext('2d',{willReadFrequently:true});
    ctx.fillStyle='#fff';
    ctx.fillRect(0,0,canvas.width,canvas.height);
    ctx.imageSmoothingEnabled=scale<1;
    ctx.imageSmoothingQuality='high';
    ctx.drawImage(src,0,0,canvas.width,canvas.height);
    return canvas;
  }
  function scanFilteredCanvas(src,mode){
    if(mode==='normal')return src;
    const canvas=scanCloneCanvas(src);
    const ctx=canvas.getContext('2d',{willReadFrequently:true});
    if(mode==='contrast'){
      ctx.save();
      ctx.filter='contrast(2.05) brightness(1.12) saturate(0)';
      ctx.drawImage(src,0,0);
      ctx.restore();
      return canvas;
    }
    if(mode==='softContrast'){
      ctx.save();
      ctx.filter='contrast(1.45) brightness(1.05) saturate(0)';
      ctx.drawImage(src,0,0);
      ctx.restore();
      return canvas;
    }
    if(mode==='threshold'||mode==='thresholdLow'||mode==='thresholdHigh'||mode==='invert'){
      const img=ctx.getImageData(0,0,canvas.width,canvas.height);
      const d=img.data;
      const threshold=mode==='thresholdLow'?118:(mode==='thresholdHigh'?178:148);
      for(let i=0;i<d.length;i+=4){
        let g=(d[i]*.299+d[i+1]*.587+d[i+2]*.114)>threshold?255:0;
        if(mode==='invert')g=255-g;
        d[i]=d[i+1]=d[i+2]=g;
      }
      ctx.putImageData(img,0,0);
      return canvas;
    }
    return canvas;
  }
  async function detectQrOnCanvas(canvas,detector){
    if(detector){
      const hits=await detector.detect(canvas).catch(()=>[]);
      if(hits&&hits.length){
        const raw=hits[0].rawValue||hits[0].rawData||'';
        if(raw)return raw;
      }
    }
    if(window.jsQR){
      try{
        const ctx=canvas.getContext('2d',{willReadFrequently:true});
        const img=ctx.getImageData(0,0,canvas.width,canvas.height);
        const code=window.jsQR(img.data,canvas.width,canvas.height,{inversionAttempts:'attemptBoth'});
        if(code&&code.data)return code.data;
      }catch(err){}
    }
    return '';
  }
  async function scanDetectQrDirectFromFile(file,detector){
    if(!detector||!window.createImageBitmap)return '';
    let bitmap=null;
    try{
      bitmap=await createImageBitmap(file,{imageOrientation:'from-image'});
      const hits=await detector.detect(bitmap).catch(()=>[]);
      if(hits&&hits.length)return hits[0].rawValue||hits[0].rawData||'';
    }catch(err){
      console.warn('QR-Dateibild: Direkt-BarcodeDetector fehlgeschlagen.',err);
    }finally{
      if(bitmap){try{bitmap.close();}catch(closeErr){}}
    }
    return '';
  }
  async function scanQrFromImageFile(file){
    let detector=null;
    if('BarcodeDetector' in window){
      try{detector=new BarcodeDetector({formats:['qr_code']});}catch(err){detector=null;}
    }
    if(!detector&&!window.jsQR)return {raw:'',reason:'QR-Erkennung ist in diesem Browser nicht verfügbar.'};

    const direct=await scanDetectQrDirectFromFile(file,detector);
    if(direct)return {raw:direct,attempts:1,hit:{source:'direct-bitmap',mode:'native'}};

    const crops=[
      {id:'full',x:0,y:0,w:1,h:1},
      {id:'center',x:.12,y:.12,w:.76,h:.76},
      {id:'wide-center',x:.05,y:.18,w:.90,h:.64},
      {id:'tall-center',x:.18,y:.05,w:.64,h:.90},
      {id:'top-left',x:0,y:0,w:.58,h:.58},
      {id:'top-right',x:.42,y:0,w:.58,h:.58},
      {id:'bottom-left',x:0,y:.42,w:.58,h:.58},
      {id:'bottom-right',x:.42,y:.42,w:.58,h:.58},
      {id:'top-band',x:0,y:0,w:1,h:.42},
      {id:'bottom-band',x:0,y:.58,w:1,h:.42},
      {id:'left-band',x:0,y:0,w:.42,h:1},
      {id:'right-band',x:.58,y:0,w:.42,h:1},
      {id:'top-third-left',x:0,y:0,w:.50,h:.40},
      {id:'top-third-right',x:.50,y:0,w:.50,h:.40},
      {id:'mid-third-left',x:0,y:.30,w:.50,h:.40},
      {id:'mid-third-right',x:.50,y:.30,w:.50,h:.40}
    ];
    const modes=['normal','softContrast','contrast','thresholdLow','threshold','thresholdHigh','invert'];
    const maxSides=[2200,3200,1600];
    const seenBases=new Set();
    let attempts=1;
    let lastReason='';
    for(const maxSide of maxSides){
      let base=null;
      try{base=await scanImageCanvasFromFile(file,maxSide);}catch(err){
        lastReason=err&&err.message||String(err);
        continue;
      }
      const key=base.width+'x'+base.height;
      if(seenBases.has(key))continue;
      seenBases.add(key);
      for(const rot of [0,90,180,270]){
        const rotated=scanRotateCanvas(base,rot);
        for(const box of crops){
          const crop=box.id==='full'?rotated:scanCropCanvas(rotated,box);
          const prepared=scanScaleCanvas(crop,640,2600);
          for(const mode of modes){
            attempts++;
            const target=scanFilteredCanvas(prepared,mode);
            const raw=await detectQrOnCanvas(target,detector);
            if(raw)return {raw,attempts,hit:{rot,crop:box.id,mode,maxSide,canvas:key}};
          }
        }
      }
    }
    return {raw:'',attempts,reason:lastReason||'Kein QR lokal gefunden.'};
  }
'''
    html = replace_between(
        html,
        "  function scanFilteredCanvas(src,mode){",
        "function safeBase64JsonDecode(value){",
        qr_decode_code
    )

    if PATCH_MARKER not in html:
        fail("Patch marker missing after replacement")

    html = html.replace("KGG GitHub Update v003 Plan UI Stability", "KGG GitHub Update v007 QR Photo Upload Decode")
    HTML_PATH.write_text(html, encoding="utf-8")

    data = HTML_PATH.read_bytes()
    sha = hashlib.sha256(data).hexdigest()

    manifest = json.loads(VERSION_PATH.read_text(encoding="utf-8"))
    current_code = int(manifest.get("versionCode") or 0)
    manifest["versionCode"] = max(VERSION_CODE_MIN, current_code + 1)
    manifest["versionName"] = VERSION_NAME
    manifest["indexUrl"] = manifest.get("indexUrl") or "index.html"
    manifest["sha256"] = sha
    manifest["notes"] = (
        "GitHub update: improves QR recognition from uploaded gallery/photo-library images. "
        "Camera scan path is unchanged; file-image decoding now tries EXIF-aware bitmap loading, "
        "DataURL fallback, larger canvases, more crops, rotations and contrast/threshold passes."
    )
    VERSION_PATH.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    print("Patched:", HTML_PATH)
    print("versionCode:", manifest["versionCode"])
    print("versionName:", manifest["versionName"])
    print("sha256:", sha)

if __name__ == "__main__":
    main()
