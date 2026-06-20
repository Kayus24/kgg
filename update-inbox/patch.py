#!/usr/bin/env python3
from pathlib import Path
import json
import re
import sys
from datetime import datetime, timezone

HTML_PATH = Path("kgg-update/index.html")
VERSION_PATH = Path("kgg-update/version.json")

VERSION_NAME = "1.0.6-qr-gallery-bitmap-debug"
UPDATE_ID = "web-v008-qr-gallery-bitmap-debug"
SOURCE_TRUTH_ID = "kgg-source-truth"
CHANGELOG_ID = "kgg-changelog"

def fail(message: str) -> None:
    print("ERROR:", message)
    sys.exit(1)

def normalize_doctype(html: str) -> str:
    if html.lower().startswith("<!doctype html>"):
        return html
    idx = html.lower().find("<!doctype html>")
    if idx < 0:
        fail("<!doctype html> not found")
    print(f"Normalizing doctype: removed {idx} leading characters")
    return html[idx:]

def find_function_range(text: str, name: str):
    pattern = re.compile(r"(^|\n)(\s*)(?:async\s+)?function\s+" + re.escape(name) + r"\s*\(", re.M)
    m = pattern.search(text)
    if not m:
        fail(f"function {name} not found")
    start = m.start(0) + (1 if text[m.start(0):m.start(0)+1] == "\n" else 0)
    brace = text.find("{", m.end())
    if brace < 0:
        fail(f"opening brace for {name} not found")
    depth = 0
    i = brace
    in_str = None
    escape = False
    in_line_comment = False
    in_block_comment = False
    while i < len(text):
        ch = text[i]
        nxt = text[i+1] if i + 1 < len(text) else ""
        if in_line_comment:
            if ch == "\n":
                in_line_comment = False
            i += 1
            continue
        if in_block_comment:
            if ch == "*" and nxt == "/":
                in_block_comment = False
                i += 2
            else:
                i += 1
            continue
        if in_str:
            if escape:
                escape = False
            elif ch == "\\":
                escape = True
            elif ch == in_str:
                in_str = None
            i += 1
            continue
        if ch in ("'", '"', "`"):
            in_str = ch
            i += 1
            continue
        if ch == "/" and nxt == "/":
            in_line_comment = True
            i += 2
            continue
        if ch == "/" and nxt == "*":
            in_block_comment = True
            i += 2
            continue
        if ch == "{":
            depth += 1
        elif ch == "}":
            depth -= 1
            if depth == 0:
                return start, i + 1
        i += 1
    fail(f"closing brace for {name} not found")

def replace_function(text: str, name: str, code: str) -> str:
    start, end = find_function_range(text, name)
    return text[:start] + code.strip("\n") + text[end:]

def replace_once(text: str, old: str, new: str, label: str) -> str:
    count = text.count(old)
    if count < 1:
        print(f"WARN: token not found for {label}; skipping")
        return text
    if count > 1:
        print(f"WARN: token appears {count} times for {label}; replacing first only")
    return text.replace(old, new, 1)

def extract_json_script(html: str, script_id: str) -> dict:
    pattern = re.compile(
        r'<script\s+type=["\']application/json["\']\s+id=["\']' + re.escape(script_id) + r'["\']\s*>(.*?)</script>',
        re.I | re.S
    )
    m = pattern.search(html)
    if not m:
        return {}
    try:
        return json.loads(m.group(1).strip())
    except Exception as err:
        print(f"WARN: could not parse {script_id}: {err}")
        return {}

def remove_json_script(html: str, script_id: str) -> str:
    pattern = re.compile(
        r'\s*<!--\s*BEGIN\s+' + re.escape(script_id) + r'.*?END\s+' + re.escape(script_id) + r'\s*-->\s*',
        re.I | re.S
    )
    html2 = pattern.sub("\n", html)
    pattern2 = re.compile(
        r'\s*<script\s+type=["\']application/json["\']\s+id=["\']' + re.escape(script_id) + r'["\']\s*>.*?</script>\s*',
        re.I | re.S
    )
    return pattern2.sub("\n", html2)

def json_script(script_id: str, data: dict, label: str) -> str:
    body = json.dumps(data, ensure_ascii=False, indent=2)
    return (
        f'\n<!-- BEGIN {script_id}: {label}; read this before patching -->\n'
        f'<script type="application/json" id="{script_id}">\n'
        f'{body}\n'
        f'</script>\n'
        f'<!-- END {script_id} -->\n'
    )

def update_embedded_metadata(html: str, version_code: int, version_name: str) -> str:
    protected = [
        "PDF",
        "QR-Erzeugung",
        "Patienten-App",
        "Scan-Kamera",
        "Parser",
        "Android-Wrapper",
        "Tablet-Layout",
        "Plan-State",
        "Storage",
    ]
    released_at = datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
    source_truth = extract_json_script(html, SOURCE_TRUTH_ID) or {}
    changelog = extract_json_script(html, CHANGELOG_ID) or {}

    source_truth.update({
        "schema": int(source_truth.get("schema") or 1),
        "app": "KGG Plan",
        "purpose": "Machine-readable Source Truth for local LLMs, Codex agents and future patch automation.",
        "currentWebVersion": {
            "versionCode": version_code,
            "versionName": version_name,
            "channel": "github-pages-main",
            "updateUrl": "https://kayus24.github.io/kgg/kgg-update/version.json",
            "sha256": "see kgg-update/version.json",
            "releasedAt": released_at,
        },
        "protectedAreas": protected,
        "lastUpdateIntent": {
            "id": UPDATE_ID,
            "summary": "Adds QR gallery/photo import diagnostics and a stronger BarcodeDetector ImageBitmap fallback for uploaded images.",
            "notTouched": protected,
        },
    })
    fixes = list(source_truth.get("activeFixes") or [])
    for item in ["phone-admin-banner-hidden", "qr-photo-upload-decode", "embedded-source-truth", "embedded-changelog", "qr-gallery-bitmap-detector-fallback", "qr-photo-import-debug"]:
        if item not in fixes:
            fixes.append(item)
    source_truth["activeFixes"] = fixes
    rules = list(source_truth.get("rulesForFutureAgents") or [])
    for rule in [
        "Read kgg-source-truth and kgg-changelog before changing the app.",
        "Do not touch protectedAreas without explicit Max approval.",
        "If a user request conflicts with Source Truth, stop and ask Max before changing code.",
        "Every update must add or update a changelog entry.",
        "Do not put API keys, patient data, admin-safe codes, secrets or private links in this JSON.",
        "The HTML file must start exactly with <!doctype html>.",
    ]:
        if rule not in rules:
            rules.append(rule)
    source_truth["rulesForFutureAgents"] = rules

    entries = list(changelog.get("entries") or [])
    entries = [e for e in entries if not (isinstance(e, dict) and e.get("versionName") == version_name)]
    entries.insert(0, {
        "versionCode": version_code,
        "versionName": version_name,
        "type": "github-web-update",
        "title": "QR-Foto/Galerie-Import mit Debug und Bitmap-Fallback",
        "summary": "Verbessert QR-Erkennung aus Galerie-/Fotodatenbank-Bildern durch zusätzlichen BarcodeDetector-ImageBitmap-Fallback und sichtbare Warnungen, wenn ein Bild nicht dekodiert werden kann.",
        "changedAreas": [
            "QR-Bildimport",
            "HTML/JS",
            "eingebettete Source Truth",
            "eingebetteter Changelog"
        ],
        "notTouched": protected,
        "testStatus": {
            "githubPages": "pending",
            "androidApp": "pending",
            "qrGalleryImport": "pending"
        }
    })
    changelog = {
        "schema": int(changelog.get("schema") or 1),
        "latestVersionCode": version_code,
        "entries": entries[:20],
    }

    html = remove_json_script(html, SOURCE_TRUTH_ID)
    html = remove_json_script(html, CHANGELOG_ID)
    blocks = json_script(SOURCE_TRUTH_ID, source_truth, "embedded Source Truth") + json_script(CHANGELOG_ID, changelog, "embedded Changelog")
    head_idx = html.lower().find("</head>")
    if head_idx < 0:
        fail("</head> not found")
    return html[:head_idx] + blocks + html[head_idx:]

def main() -> None:
    if not HTML_PATH.exists():
        fail(f"{HTML_PATH} not found")
    if not VERSION_PATH.exists():
        fail(f"{VERSION_PATH} not found")

    html = normalize_doctype(HTML_PATH.read_text(encoding="utf-8"))
    manifest = json.loads(VERSION_PATH.read_text(encoding="utf-8"))
    current_code = int(manifest.get("versionCode") or 0)
    next_code = max(8, current_code + 1)

    detect_code = r"""
  /* kgg-mini-patch-v400-10-qr-gallery-bitmap-debug
     Galerie-/Fotodatenbank-QR-Fix:
     Einige Android WebViews erkennen QR-Codes per BarcodeDetector auf Kamera-Bildern,
     aber nicht zuverlässig auf Canvas-Crops aus Galerie-Dateien. Deshalb wird jeder
     Canvas-Versuch zusätzlich als PNG-Blob -> ImageBitmap dekodiert und dann erneut
     an BarcodeDetector gegeben. Außerdem bleiben Warnungen in der Scan-Vorschau sichtbar.
  */
  function scanCanvasToBlob(canvas,type,quality){
    return new Promise(resolve=>{
      try{
        canvas.toBlob(blob=>resolve(blob),type||'image/png',quality||.92);
      }catch(err){resolve(null);}
    });
  }
  async function scanDetectQrViaBitmapFromCanvas(canvas,detector){
    if(!detector||!window.createImageBitmap||!canvas||!canvas.toBlob)return '';
    let blob=null,bitmap=null;
    try{
      blob=await scanCanvasToBlob(canvas,'image/png',.92);
      if(!blob)return '';
      bitmap=await createImageBitmap(blob);
      const hits=await detector.detect(bitmap).catch(()=>[]);
      if(hits&&hits.length){
        return hits[0].rawValue||hits[0].rawData||'';
      }
    }catch(err){
      return '';
    }finally{
      if(bitmap){try{bitmap.close();}catch(closeErr){}}
    }
    return '';
  }
  async function detectQrOnCanvas(canvas,detector){
    if(detector){
      try{
        const hits=await detector.detect(canvas).catch(()=>[]);
        if(hits&&hits.length){
          const raw=hits[0].rawValue||hits[0].rawData||'';
          if(raw)return raw;
        }
      }catch(err){}
      const bitmapRaw=await scanDetectQrViaBitmapFromCanvas(canvas,detector);
      if(bitmapRaw)return bitmapRaw;
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
"""
    html = replace_function(html, "detectQrOnCanvas", detect_code)

    scan_qr_code = r"""
  async function scanQrFromImageFile(file){
    const fileName=String(file&&file.name||'Bild');
    const fileType=String(file&&file.type||'unbekannter Typ');
    const fileSize=Number(file&&file.size||0);
    const heicHint=/heic|heif/i.test(fileName+' '+fileType);
    let detector=null;
    if('BarcodeDetector' in window){
      try{detector=new BarcodeDetector({formats:['qr_code']});}catch(err){detector=null;}
    }
    if(!detector&&!window.jsQR){
      return {
        raw:'',
        attempts:0,
        reason:'QR-Erkennung ist in diesem WebView nicht verfügbar. BarcodeDetector/jsQR fehlt.',
        debug:{fileName,fileType,fileSize,barcodeDetector:false,jsQR:false}
      };
    }

    const direct=await scanDetectQrDirectFromFile(file,detector);
    if(direct)return {raw:direct,attempts:1,hit:{source:'direct-bitmap',mode:'native'},debug:{fileName,fileType,fileSize}};

    const crops=[
      {id:'full',x:0,y:0,w:1,h:1},
      {id:'center',x:.08,y:.08,w:.84,h:.84},
      {id:'center-tight',x:.20,y:.20,w:.60,h:.60},
      {id:'wide-center',x:.03,y:.15,w:.94,h:.70},
      {id:'tall-center',x:.15,y:.03,w:.70,h:.94},
      {id:'top-left',x:0,y:0,w:.62,h:.62},
      {id:'top-right',x:.38,y:0,w:.62,h:.62},
      {id:'bottom-left',x:0,y:.38,w:.62,h:.62},
      {id:'bottom-right',x:.38,y:.38,w:.62,h:.62},
      {id:'top-band',x:0,y:0,w:1,h:.48},
      {id:'bottom-band',x:0,y:.52,w:1,h:.48},
      {id:'left-band',x:0,y:0,w:.48,h:1},
      {id:'right-band',x:.52,y:0,w:.48,h:1},
      {id:'top-third-left',x:0,y:0,w:.54,h:.44},
      {id:'top-third-right',x:.46,y:0,w:.54,h:.44},
      {id:'mid-third-left',x:0,y:.28,w:.54,h:.44},
      {id:'mid-third-right',x:.46,y:.28,w:.54,h:.44},
      {id:'bottom-third-left',x:0,y:.56,w:.54,h:.44},
      {id:'bottom-third-right',x:.46,y:.56,w:.54,h:.44}
    ];
    const modes=['normal','softContrast','contrast','thresholdLow','threshold','thresholdHigh','invert'];
    const maxSides=[4096,3200,2600,1800,1200];
    const rotations=[0,90,180,270];
    const seenBases=new Set();
    let attempts=1;
    let lastReason='';
    let lastCanvas='';
    for(const maxSide of maxSides){
      let base=null;
      try{
        base=await scanImageCanvasFromFile(file,maxSide);
      }catch(err){
        lastReason=err&&err.message||String(err);
        continue;
      }
      const key=base.width+'x'+base.height;
      lastCanvas=key;
      if(seenBases.has(key))continue;
      seenBases.add(key);
      for(const rot of rotations){
        const rotated=scanRotateCanvas(base,rot);
        for(const box of crops){
          const crop=box.id==='full'?rotated:scanCropCanvas(rotated,box);
          const prepared=scanScaleCanvas(crop,860,3200);
          for(const mode of modes){
            attempts++;
            const target=scanFilteredCanvas(prepared,mode);
            const raw=await detectQrOnCanvas(target,detector);
            if(raw){
              return {
                raw,
                attempts,
                hit:{rot,crop:box.id,mode,maxSide,canvas:key,detector:!!detector,jsQR:!!window.jsQR},
                debug:{fileName,fileType,fileSize,lastCanvas:key}
              };
            }
          }
        }
      }
    }
    const support='BarcodeDetector='+(!!detector)+', jsQR='+(!!window.jsQR);
    const heicText=heicHint?' HEIC/HEIF wird von Android WebView oft nicht als Canvas-Bild dekodiert; bitte als Screenshot/PNG/JPG testen.':'';
    return {
      raw:'',
      attempts,
      reason:(lastReason?lastReason+'; ':'')+'Kein QR im hochgeladenen Bild gefunden. '+support+', Datei='+fileName+', Typ='+fileType+', Groesse='+fileSize+', Canvas='+lastCanvas+'.'+heicText,
      debug:{fileName,fileType,fileSize,attempts,lastCanvas,barcodeDetector:!!detector,jsQR:!!window.jsQR,heicHint}
    };
  }
"""
    html = replace_function(html, "scanQrFromImageFile", scan_qr_code)

    # Keep QR photo import failures visible as warnings in the scan card instead of silently treating them as paper only.
    old = """    job.pages.push(scanFileMeta(file));
    job.status='queued';"""
    new = """    job.pages.push(scanFileMeta(file));
    if(kind==='file'&&qr&&!qr.raw){
      const qrWarn='QR-Foto-Import: '+(qr.reason||'Kein QR im Bild erkannt.');
      job.warnings.push(qrWarn);
      try{console.warn(qrWarn,qr.debug||{});}catch(err){}
    }
    job.status='queued';"""
    html = replace_once(html, old, new, "scanAcceptFile QR gallery warning")

    # Make the file picker prefer broadly decodable images while still allowing Android's image/* provider.
    html = html.replace('accept="image/*,.jpg,.jpeg,.png,.webp,.heic,.heif" multiple', 'accept="image/*,.jpg,.jpeg,.png,.webp" multiple')
    html = html.replace("input.accept='image/*,.jpg,.jpeg,.png,.webp,.heic,.heif';", "input.accept='image/*,.jpg,.jpeg,.png,.webp';")

    html = update_embedded_metadata(html, next_code, VERSION_NAME)

    if "kgg-mini-patch-v400-10-qr-gallery-bitmap-debug" not in html:
        fail("patch marker missing")
    if not html.lower().startswith("<!doctype html>"):
        fail("HTML does not start with <!doctype html> after patch")
    HTML_PATH.write_text(html, encoding="utf-8")
    print(f"Patched {HTML_PATH}")
    print(f"Expected next versionName: {VERSION_NAME}")
    print(f"Embedded source truth versionCode: {next_code}")

if __name__ == "__main__":
    main()
