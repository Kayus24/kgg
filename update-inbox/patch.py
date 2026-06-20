#!/usr/bin/env python3
from pathlib import Path
from datetime import datetime, timezone
import json, re, sys

HTML=Path('kgg-update/index.html')
VERSION=Path('kgg-update/version.json')
RELEASE=Path('update-inbox/release.json')
PATCH_ID='qr-gallery-restore-lkg-v011'
VERSION_NAME='1.0.9-restore-lkg-qr-gallery-decode'
ROLLBACK_DEFAULT='Rollback-Notiz: Wenn v011 die App beschädigt oder QR/Scan verschlechtert, dieses v011-Paket revertieren und den vorherigen funktionierenden kgg-update/index.html + version.json Stand wiederherstellen. Danach Galerie-QR, Kamera-Scan und QR-Erzeugung testen.'
PROTECTED=['PDF','QR-Erzeugung','Patienten-App','Scan-Kamera','Parser','Android-Wrapper','Tablet-Layout','Plan-State','Storage']

JS=r"""
  /* KGG PATCH START: qr-gallery-restore-lkg-v011 */
  function scanImageCanvasFromFile(file,maxSide){return new Promise((ok,bad)=>{const u=URL.createObjectURL(file),i=new Image();i.onload=()=>{try{const s=Math.min(1,(maxSide||1800)/Math.max(1,i.naturalWidth||i.width,i.naturalHeight||i.height)),c=document.createElement('canvas');c.width=Math.max(1,Math.round((i.naturalWidth||i.width)*s));c.height=Math.max(1,Math.round((i.naturalHeight||i.height)*s));const x=c.getContext('2d',{willReadFrequently:true});x.fillStyle='#fff';x.fillRect(0,0,c.width,c.height);x.drawImage(i,0,0,c.width,c.height);URL.revokeObjectURL(u);ok(c)}catch(e){URL.revokeObjectURL(u);bad(e)}};i.onerror=()=>{URL.revokeObjectURL(u);bad(new Error('Bild konnte nicht gelesen werden'))};i.src=u})}
  function scanMakeCanvas(src,box,rot,mode){const crop=box||{x:0,y:0,w:1,h:1},flip=rot===90||rot===270,c=document.createElement('canvas');c.width=flip?Math.round(src.height*crop.h):Math.round(src.width*crop.w);c.height=flip?Math.round(src.width*crop.w):Math.round(src.height*crop.h);c.width=Math.max(64,c.width);c.height=Math.max(64,c.height);const x=c.getContext('2d',{willReadFrequently:true});x.fillStyle='#fff';x.fillRect(0,0,c.width,c.height);x.save();if(rot===90){x.translate(c.width,0);x.rotate(Math.PI/2)}else if(rot===180){x.translate(c.width,c.height);x.rotate(Math.PI)}else if(rot===270){x.translate(0,c.height);x.rotate(-Math.PI/2)}x.drawImage(src,src.width*crop.x,src.height*crop.y,src.width*crop.w,src.height*crop.h,0,0,flip?c.height:c.width,flip?c.width:c.height);x.restore();if(mode==='threshold'){const img=x.getImageData(0,0,c.width,c.height),d=img.data;for(let p=0;p<d.length;p+=4){const g=(d[p]*.299+d[p+1]*.587+d[p+2]*.114)>148?255:0;d[p]=d[p+1]=d[p+2]=g}x.putImageData(img,0,0)}return c}
  async function scanDetectQrCanvas(c,d){if(d){const h=await d.detect(c).catch(()=>[]);if(h&&h[0]&&h[0].rawValue)return h[0].rawValue}if(window.jsQR){try{const x=c.getContext('2d',{willReadFrequently:true}),im=x.getImageData(0,0,c.width,c.height),r=window.jsQR(im.data,c.width,c.height,{inversionAttempts:'attemptBoth'});if(r&&r.data)return r.data}catch(e){}}return ''}
  async function scanQrFromImageFile(file){let d=null;if('BarcodeDetector'in window){try{d=new BarcodeDetector({formats:['qr_code']})}catch(e){}}if(!d&&!window.jsQR)return{raw:'',reason:'QR-Erkennung ist in diesem Browser nicht verfügbar.'};const base=await scanImageCanvasFromFile(file,1800),boxes=[{x:0,y:0,w:1,h:1},{x:0,y:0,w:.55,h:.55},{x:.45,y:0,w:.55,h:.55},{x:0,y:.45,w:.55,h:.55},{x:.45,y:.45,w:.55,h:.55},{x:.15,y:.15,w:.7,h:.7}],rots=[0,90,180,270],modes=['normal','threshold'];let attempts=0;for(const rot of rots)for(const box of boxes)for(const mode of modes){attempts++;const raw=await scanDetectQrCanvas(scanMakeCanvas(base,box,rot,mode),d);if(raw)return{raw,attempts,hit:{rot,mode}}}return{raw:'',attempts,reason:'Kein QR lokal gefunden.'}}
  /* KGG PATCH END: qr-gallery-restore-lkg-v011 */
""".strip('\n')

def j(path, fallback):
    try:
        x=json.loads(path.read_text(encoding='utf-8'))
        return x if isinstance(x,dict) else fallback
    except Exception:
        return fallback

def repl_json(html, sid, obj):
    block='<script type="application/json" id="'+sid+'">\n'+json.dumps(obj,ensure_ascii=False,indent=2)+'\n</script>'
    pat=re.compile(r'<script\b(?=[^>]*\bid=["\']'+re.escape(sid)+r'["\'])(?=[^>]*\btype=["\']application/json["\'])[^>]*>.*?</script>',re.I|re.S)
    if pat.search(html): return pat.sub(block,html,1)
    i=html.lower().find('</head>')
    return html[:i]+block+'\n'+html[i:] if i>=0 else block+'\n'+html

def main():
    if not HTML.exists(): sys.exit('ERROR: missing kgg-update/index.html')
    release=j(RELEASE,{'versionName':VERSION_NAME,'rollbackNote':ROLLBACK_DEFAULT})
    manifest=j(VERSION,{})
    rollback=release.get('rollbackNote') or ROLLBACK_DEFAULT
    name=release.get('versionName') or VERSION_NAME
    try: code=int(manifest.get('versionCode'))+(0 if manifest.get('versionName')==name else 1)
    except Exception: code=None
    html=HTML.read_text(encoding='utf-8')
    p=html.lower().find('<!doctype html')
    if p<0: sys.exit('ERROR: <!doctype html> not found')
    html=html[p:]
    start=html.find('/* KGG PATCH START: qr-gallery-restore-lkg-v011')
    if start>=0:
        while start>0 and html[start-1]==' ': start-=1
        end=html.find('/* KGG PATCH END: qr-gallery-restore-lkg-v011 */',start)
        if end<0: sys.exit('ERROR: v011 marker without end')
        end=html.find('\n',end); end=len(html) if end<0 else end
    else:
        points=[html.find(s) for s in ['  function scanImageCanvasFromFile','function scanImageCanvasFromFile','  async function scanQrFromImageFile','async function scanQrFromImageFile']]
        points=[x for x in points if x>=0]
        if not points: sys.exit('ERROR: QR decoder entry not found')
        start=min(points)
        ends=[html.find(s,start) for s in ['  function safeBase64JsonDecode','function safeBase64JsonDecode']]
        ends=[x for x in ends if x>=0]
        if not ends: sys.exit('ERROR: QR decoder boundary not found')
        end=min(ends)
    html=html[:start]+JS+'\n'+html[end:]
    if 'KGG INTERNAL SOURCE TRUTH — READ THIS FIRST' not in html:
        i=html.lower().find('<html')
        note='<!-- KGG INTERNAL SOURCE TRUTH — READ THIS FIRST: read kgg-source-truth, kgg-changelog and kgg-patch-rules before patching. -->\n'
        html=html[:i]+note+html[i:] if i>=0 else note+html
    st=j_from_html(html,'kgg-source-truth',{'schema':1,'currentVersion':{},'activeFixes':[]})
    st.setdefault('currentVersion',{})
    if code is not None: st['currentVersion']['versionCode']=code
    st['currentVersion'].update({'versionName':name,'lastPatchId':PATCH_ID,'updatedBy':'update-inbox'})
    st['protectedAreas']=PROTECTED
    fixes=st.get('activeFixes') if isinstance(st.get('activeFixes'),list) else []
    for x in [PATCH_ID,'patch-retention-guard']:
        if x not in fixes: fixes.append(x)
    st['activeFixes']=fixes
    st['lastKnownGoodRestores']=[{'patchId':PATCH_ID,'restoresFrom':'KGG_APP_KOLLEGEN_v360/v366','rollbackNote':rollback,'preserve':['Kamera-Scan','QR-Erzeugung','Parser','Storage','Tablet-Layout']}]
    html=repl_json(html,'kgg-source-truth',st)
    cl=j_from_html(html,'kgg-changelog',{'schema':1,'entries':[]})
    entries=cl.get('entries') if isinstance(cl.get('entries'),list) else []
    for e in entries:
        if isinstance(e,dict) and e.get('patchId')!=PATCH_ID and ('qr-gallery' in str(e.get('patchId','')) or 'qr-photo' in str(e.get('patchId',''))):
            e.setdefault('status','superseded'); e.setdefault('supersededBy',PATCH_ID); e.setdefault('whySuperseded','v011 restores last-known-good gallery decoder')
    entry={'versionCode':code,'versionName':name,'patchId':PATCH_ID,'status':'active','title':'Restore last-known-good QR gallery decoder','reason':'Galerie-QR war nach neueren Patches weiter kaputt; alter funktionierender Decoder wird wiederhergestellt.','supersedes':['qr-photo-upload-decode-v007','qr-gallery-bitmap-debug-v008','qr-gallery-crop-grid-decode-v010'],'notTouched':PROTECTED,'rollbackNote':rollback,'createdAt':datetime.now(timezone.utc).isoformat()}
    entries=[e for e in entries if not (isinstance(e,dict) and e.get('patchId')==PATCH_ID)]
    entries.insert(0,entry); cl.update({'schema':cl.get('schema',1),'latestVersionCode':code,'latestVersionName':name,'entries':entries})
    html=repl_json(html,'kgg-changelog',cl)
    rules=j_from_html(html,'kgg-patch-rules',{'schema':1})
    rules['patchRetentionPolicy']={'rule':'Do not remove latest functional patch silently.','whenReplacingPatchRequire':['supersedes','supersededBy','reason','rollbackNote']}
    html=repl_json(html,'kgg-patch-rules',rules)
    if not html.lower().startswith('<!doctype html') or PATCH_ID not in html: sys.exit('ERROR: validation failed')
    HTML.write_text(html,encoding='utf-8',newline='\n')
    print('Applied',PATCH_ID)

def j_from_html(html, sid, fallback):
    m=re.search(r'<script\b(?=[^>]*\bid=["\']'+re.escape(sid)+r'["\'])(?=[^>]*\btype=["\']application/json["\'])[^>]*>\s*(.*?)\s*</script>',html,re.I|re.S)
    if not m: return fallback
    try:
        x=json.loads(m.group(1)); return x if isinstance(x,dict) else fallback
    except Exception:
        return fallback

if __name__=='__main__':
    main()
