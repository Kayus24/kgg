#!/usr/bin/env python3
"""Validate the patient PWA manifest, icon and service-worker delivery contract."""
from __future__ import annotations
import json,re,shutil,struct,subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
MANIFEST_PATHS=(ROOT/"manifest.json",ROOT/"manifest-v64.webmanifest")
ICON_CONTRACT={"kgg-icon-192-v63.png":(192,192,"any"),"kgg-icon-512-v63.png":(512,512,"any"),"kgg-icon-maskable-512-v63.png":(512,512,"maskable")}
def fail(message:str)->None:raise SystemExit(f"PWA contract failed: {message}")
def read_png_size(path:Path)->tuple[int,int]:
 data=path.read_bytes()
 if len(data)<24 or data[:8]!=b"\x89PNG\r\n\x1a\n":fail(f"{path.name} is not a readable PNG")
 if data[12:16]!=b"IHDR":fail(f"{path.name} has no PNG IHDR header")
 return struct.unpack(">II",data[16:24])
def load_manifest(path:Path)->dict:
 try:return json.loads(path.read_text(encoding="utf-8"))
 except (OSError,json.JSONDecodeError) as exc:fail(f"cannot parse {path.name}: {exc}")
def validate_manifest(manifest:dict,path:Path)->None:
 expected={"name":"KGG Handyplan","short_name":"KGG Plan","start_url":"./","scope":"./","display":"standalone"}
 for key,value in expected.items():
  if manifest.get(key)!=value:fail(f"{path.name} has {key}={manifest.get(key)!r}, expected {value!r}")
 icons=manifest.get("icons")
 if not isinstance(icons,list) or len(icons)!=len(ICON_CONTRACT):fail(f"{path.name} must contain exactly {len(ICON_CONTRACT)} icons")
 by_src={entry.get("src"):entry for entry in icons if isinstance(entry,dict)}
 if set(by_src)!=set(ICON_CONTRACT):fail(f"{path.name} icon sources do not match the v63 icon contract")
 for src,(width,height,purpose) in ICON_CONTRACT.items():
  entry=by_src[src]
  if entry.get("type")!="image/png":fail(f"{src} must be declared as image/png")
  if entry.get("sizes")!=f"{width}x{height}":fail(f"{src} has the wrong declared size")
  if entry.get("purpose")!=purpose:fail(f"{src} has purpose={entry.get('purpose')!r}, expected {purpose!r}")
  if read_png_size(ROOT/src)!=(width,height):fail(f"{src} has the wrong actual size")
def validate_worker()->str:
 worker_path=ROOT/"service-worker.js";worker=worker_path.read_text(encoding="utf-8")
 match=re.search(r"const APP_VERSION = '([0-9]+)';",worker)
 if not match:fail("service-worker.js has no numeric APP_VERSION")
 version=match.group(1)
 required=(f"kgg-handyplan-v{version}-",f"const APP_VERSION = '{version}';","const RECOVERY_PATH = './update-recovery.html';","./manifest-v64.webmanifest","./kgg-icon-192-v63.png","./kgg-icon-512-v63.png","./kgg-icon-maskable-512-v63.png",f"./patient-version-label.js?v={version}","./patient-storage-v7.js?v=storage-v7-1","./patient-set-summary-groups.js?v=set-summary-groups-2-range-label","./patient-card-progress.js?v=card-progress-1-two-fields","./patient-install-prompt.js?v=install-prompt-1-shared-reference","./patient-plan-delete.js?v=plan-delete-1-safe","GET_UPDATE_DIAGNOSTICS","isRecoveryRequest(event.request)",'rel="manifest" href="./manifest-v64.webmanifest"','rel="icon" type="image/png" sizes="192x192" href="./kgg-icon-192-v63.png"','rel="apple-touch-icon" sizes="192x192" href="./kgg-icon-192-v63.png"')
 for fragment in required:
  if fragment not in worker:fail(f"service-worker.js is missing {fragment!r}")
 if "v59.png" in worker or "v59'" in worker or 'v59"' in worker:fail("service-worker.js still contains a v59 icon reference")
 node=shutil.which("node")
 if node:
  result=subprocess.run([node,"--check",str(worker_path)],cwd=ROOT,capture_output=True,text=True,check=False)
  if result.returncode!=0:fail(f"service-worker.js is invalid JavaScript: {result.stderr.strip()}")
 return version
def validate_update_lifecycle(version:str)->None:
 label=(ROOT/"patient-version-label.js").read_text(encoding="utf-8")
 if f"const RELEASE='{version}';" not in label:fail(f"patient-version-label.js is not aligned with release {version}")
 recovery=(ROOT/"update-recovery.html").read_text(encoding="utf-8")
 if f"const RELEASE='{version}';" not in recovery:fail(f"update-recovery.html is not aligned with release {version}")
def validate_static_compatibility(manifest:dict)->None:
 html=(ROOT/"index.html").read_text(encoding="utf-8-sig")
 if '<link rel="manifest" href="manifest.json">' not in html:fail("index.html no longer exposes the first-load compatibility manifest")
 if load_manifest(ROOT/"manifest.json")!=manifest:fail("manifest.json and manifest-v64.webmanifest must remain identical")
 if not (ROOT/"update-recovery.html").is_file():fail("update-recovery.html is missing")
def main()->int:
 manifests=[load_manifest(path) for path in MANIFEST_PATHS]
 for manifest,path in zip(manifests,MANIFEST_PATHS):validate_manifest(manifest,path)
 validate_static_compatibility(manifests[1]);version=validate_worker();validate_update_lifecycle(version);print("Patient PWA contract: OK");return 0
if __name__=="__main__":raise SystemExit(main())
