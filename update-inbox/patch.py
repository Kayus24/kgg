#!/usr/bin/env python3
from pathlib import Path
import base64,json,os,re,sys,zlib
HTML_PATH=Path(os.environ.get("KGG_INDEX_HTML","kgg-update/index.html"))
VERSION_PATH=Path(os.environ.get("KGG_VERSION_JSON","kgg-update/version.json"))
VERSION_NAME="1.0.5-qr-photo-source-truth"
PATCH_MARKER="kgg-mini-patch-v400-09-qr-photo-upload-decode"
SOURCE_TRUTH_MARKER="kgg-source-truth"
CHANGELOG_MARKER="kgg-changelog"
UPDATE_URL="https://kayus24.github.io/kgg/kgg-update/version.json"
PROTECTED_AREAS=["PDF","QR-Erzeugung","Patienten-App","Scan-Kamera","Parser","Android-Wrapper","Tablet-Layout","Plan-State","Storage"]
IMG_Z="""eNq9Vklz2zYUvudXYKYHUh5SUtxeag070yR23emSRJpMziD5KKICAQcEJWtE/fc+LJRI2nKaHKoDSbwd39tEyOyKbNbruGKCxQ9UZ2W8/Wk+j+c/x19U/FBKLePmgUuaxzlkModXxPyWMm1qDQrIx2V8qzYgRCPWpGhAkTeM5/iiTU1+oxwUg9mdMfOOahApFZups/EHrUDReJVRQVIOLNWkEVskgUB9vSCiUcQosXhmbMbvTAAM3eyYyglKplDXKGnsXc3wUTQi00wKUqPNJdD8jnH4tUYb9JPiYYGnycE6V6AbJYiAHfmgZMVqCEMFteRbiBT8A5meJL84UUIyKWqNKhTDSoyKMbu0x3Cy8EKOPZXCYJWEqO7thSutMOjQCyC14bptg2DyVBeUksormyA6JUtvW+P71nyGgQGEbKQQGohgWanJGjjUIMgOVA7iqXXz8lgs/3RYOImjfR/H+L2lYkvrO0Tn94quYSUblUFY21e0Y7kuoxLYutRRRR9XLO+gdWjVKvuc/EV1OUVu+Dqyn0o2Ig+tbts6S1NBMROUfx4Qt2hODkle63V3r5Ob+wtuXHBjP/dDqnU0onWKI1ecVUyfff14PY/+bqoUa6C7f9teX8/nw/gy7ACvxAQGaK3MehEboMzjfugts+gnucyaCoSeZpg+DbcczCkMHDvoVOzJQXQBDePmykYzGSq5217Wuh9puej0Y+L116DfSqzCR4zqOg+iw45xbntPwZcGg+X7G60aOHYG9OMUi4+v9B6RCX4oiiIYcpam8OfRPOpfKxqE27PFbHFWUuoSu+xWUBwleWI8XpL52FDO9D4JSjTV850rurOl3hX5f4rBTxLHeraRrE2fOdNOZhQ1in//JGLV2o4hF+ypz5H83PhB8kjkyZT5vrlijOV+JCcBrfciC/o8LJ4E7zkeMlbwGYTO88aMVzugnp0s39iHrMCBI3K58y1kfb1huqIPkw5WrfbdZ+cltRIJ3VGG5T7WdNEdbF29xwUnNDWXuQkKDD+25OB4Aso58Im+PFqdy8i9fMX5gx+09uqTxfFkt2CCcr4/GPteNOOyNkVxzMwyD+0Rczs5HDs1z3HyljW4u+Q4bKkSYYCr3a7fFGvi5ikIpICSr6HOSo40EZECY0lptsHVX7jinJ035TSIzh47ZFxI7skB97/iSeCLqJcUQ8al5TP4PjVFO1pi/d5wSXup9c6r8Ss5QXORqeXhljIUl58er9sihjTM16se6tIFr3gf+JdgP932Zbj9XkeUBx4Wlys8d/+Kemhd+Me0GCl+HWJvuqf5PwJ9gtpHMaxwXSq5I2dW2/bx+sa/WKMy7rqxm4GFG/MGe5MaBVu56VWvLUQfq+P1+9Q8j/8C0Ebpaw=="""
QR_Z="""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"""

def fail(m): print("ERROR:",m); sys.exit(1)
def inflate(s): return zlib.decompress(base64.b64decode(s)).decode("utf-8")
def normalize_doctype(t):
    t=t.lstrip("\ufeff\r\n\t ")
    m=re.search(r"(?is)<!doctype\s+html\s*>",t[:200])
    t=(t[m.start():] if m else "<!doctype html>\n"+t)
    t=re.sub(r"(?is)^<!doctype\s+html\s*>","<!doctype html>",t,count=1)
    if not t.startswith("<!doctype html>"): fail("Doctype normalization failed")
    return t
def replace_between(t,start_token,end_token,repl):
    s=t.find(start_token)
    if s<0: fail(f"Start token not found: {start_token!r}")
    e=t.find(end_token,s)
    if e<0: fail(f"End token not found after {start_token!r}: {end_token!r}")
    return t[:s]+repl.rstrip()+"\n  "+t[e:]
def pat(script_id):
    return re.compile(r"\n?\s*(?:<!--\s*KGG\s+"+re.escape(script_id)+r".*?-->\s*)?<script\b(?=[^>]*\btype=[\"']application/json[\"'])(?=[^>]*\bid=[\"']"+re.escape(script_id)+r"[\"'])[^>]*>.*?</script>\s*\n?",re.I|re.S)
def extract_json_script(html,script_id):
    m=re.search(r"<script\b(?=[^>]*\btype=[\"']application/json[\"'])(?=[^>]*\bid=[\"']"+re.escape(script_id)+r"[\"'])[^>]*>(.*?)</script>",html,re.I|re.S)
    if not m: return None
    try: return json.loads(m.group(1).strip())
    except Exception: return None
def remove_json_script(html,script_id): return pat(script_id).sub("\n",html)
def json_script_block(script_id,payload,label):
    return f'  <!-- KGG {script_id}: {label}. Machine-readable; safe for local LLM/code review. -->\n  <script type="application/json" id="{script_id}">\n'+json.dumps(payload,ensure_ascii=False,indent=2)+"\n  </script>\n"
def merge_entries(existing,new):
    out=[]; seen=set()
    for e in list(new)+list(existing or []):
        if not isinstance(e,dict): continue
        k=(e.get("versionCode"),e.get("versionName"),e.get("title"))
        if k in seen: continue
        seen.add(k); out.append(e)
    out.sort(key=lambda x:int(x.get("versionCode") or 0),reverse=True)
    return out
def current_code():
    try: return int(json.loads(VERSION_PATH.read_text(encoding="utf-8")).get("versionCode",0)) if VERSION_PATH.exists() else 0
    except Exception: return 0
def embed(html,target_code):
    old_log=extract_json_script(html,CHANGELOG_MARKER) or {}
    source={"schema":1,"app":"KGG Plan","purpose":"Machine-readable Source Truth for local LLMs, Codex agents and future patch automation.","currentWebVersion":{"versionCode":target_code,"versionName":VERSION_NAME,"channel":"github-pages-main","updateUrl":UPDATE_URL,"sha256":"see kgg-update/version.json","releasedAt":"2026-06-20T00:00:00Z"},"activeFixes":["phone-admin-banner-hidden","qr-photo-upload-decode","embedded-source-truth","embedded-changelog"],"knownWorkingAndroidWrapper":{"name":"android-urlfix-debug-v3-or-newer","mustUseUpdateUrl":UPDATE_URL,"note":"Older APKs with placeholder update URLs do not receive GitHub web updates."},"protectedAreas":PROTECTED_AREAS,"rulesForFutureAgents":["Read kgg-source-truth and kgg-changelog before changing the app.","Do not touch protectedAreas without explicit Max approval.","If a user request conflicts with Source Truth, stop and ask Max before changing code.","Every update must add or update a changelog entry.","Do not put API keys, patient data, admin-safe codes, secrets or private links in this JSON.","The HTML file must start exactly with <!doctype html>.","The real SHA-256 of index.html belongs in kgg-update/version.json, not inside embedded Source Truth."],"lastUpdateIntent":{"id":"web-v008-qr-photo-source-truth","summary":"Combines QR photo upload decoding improvements with embedded Source Truth and Changelog.","notTouched":PROTECTED_AREAS}}
    entry={"versionCode":target_code,"versionName":VERSION_NAME,"type":"github-web-update","title":"QR-Foto-Upload + eingebettete Source Truth","summary":"Verbessert QR-Erkennung aus Bild-/Fotodatenbank-Upload und bettet Source Truth sowie Changelog direkt in die App-HTML ein.","changedAreas":["QR photo upload decode","HTML embedded metadata","Source Truth","Changelog"],"notTouched":PROTECTED_AREAS,"testStatus":{"githubPages":"pending","androidApp":"pending"},"handoffNote":"Lokale LLMs können index.html lesen und finden kgg-source-truth sowie kgg-changelog direkt im Code."}
    changelog={"schema":1,"latestVersionCode":target_code,"entries":merge_entries(old_log.get("entries"),[entry])}
    html=remove_json_script(remove_json_script(html,SOURCE_TRUTH_MARKER),CHANGELOG_MARKER)
    block=json_script_block(SOURCE_TRUTH_MARKER,source,"embedded Source Truth")+json_script_block(CHANGELOG_MARKER,changelog,"embedded Changelog")
    m=re.search(r"(?i)</head>",html)
    if not m: fail("</head> not found; cannot embed Source Truth")
    return html[:m.start()]+block+html[m.start():]
def main():
    if not HTML_PATH.exists(): fail(f"{HTML_PATH} not found")
    html=normalize_doctype(HTML_PATH.read_text(encoding="utf-8"))
    img_start="  /* kgg-mini-patch-v400-09-qr-photo-upload-decode" if PATCH_MARKER in html else "  function scanImageCanvasFromFile(file,maxSide){"
    html=replace_between(html,img_start,"function scanCloneCanvas(src){",inflate(IMG_Z))
    html=replace_between(html,"  function scanFilteredCanvas(src,mode){","function safeBase64JsonDecode(value){",inflate(QR_Z))
    if PATCH_MARKER not in html: fail("QR photo upload patch marker missing after replacement")
    html=html.replace("KGG GitHub Update v003 Plan UI Stability","KGG GitHub Update v008 QR Photo + Source Truth")
    html=html.replace("KGG GitHub Update v007 QR Photo Upload Decode","KGG GitHub Update v008 QR Photo + Source Truth")
    target=current_code()+1
    HTML_PATH.write_text(embed(html,target),encoding="utf-8",newline="\n")
    print("Patched:",HTML_PATH)
    print("expected versionCode after pipeline:",target)
    print("versionName:",VERSION_NAME)
    print("embedded metadata:",SOURCE_TRUTH_MARKER,CHANGELOG_MARKER)
    print("separate JSON files: not created")
if __name__=="__main__": main()
