#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path
from datetime import datetime, timezone
import json
import re
import sys

HTML_PATH = Path('kgg-update/index.html')
VERSION_PATH = Path('kgg-update/version.json')
RELEASE_PATH = Path('update-inbox/release.json')

PATCH_ID = 'kgg-v023-admin-debug-visible-hotfix'
VERSION_NAME = '1.0.23-admin-debug-visible-hotfix'
STYLE_ID = PATCH_ID + '-style'
SCRIPT_ID = PATCH_ID + '-script'

PROTECTED = [
    'PDF',
    'QR-Erzeugung',
    'Patienten-App',
    'Scan-Kamera',
    'Parser',
    'Android-Wrapper',
    'Plan-State',
    'Storage',
]

CSS = r'''
/* KGG PATCH START: kgg-v023-admin-debug-visible-hotfix-style */
#kggAdminDebugFab{
  position:fixed!important;
  right:16px!important;
  bottom:calc(18px + env(safe-area-inset-bottom,0px))!important;
  z-index:5000!important;
  display:inline-flex!important;
  align-items:center!important;
  justify-content:center!important;
  gap:8px!important;
  min-width:118px!important;
  min-height:48px!important;
  padding:11px 14px!important;
  border:1px solid rgba(7,16,39,.22)!important;
  border-radius:999px!important;
  background:#071027!important;
  color:#fff!important;
  font:1000 15px/1 system-ui,-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,Arial,sans-serif!important;
  box-shadow:0 16px 44px rgba(7,16,39,.26),0 4px 12px rgba(7,16,39,.16)!important;
  pointer-events:auto!important;
  opacity:1!important;
  visibility:visible!important;
}
#kggAdminDebugFab:active{transform:translateY(1px)!important}
.kggDebugPanelOverlay{
  position:fixed;
  inset:0;
  z-index:5001;
  display:none;
  align-items:center;
  justify-content:center;
  padding:14px;
  background:rgba(7,16,39,.46);
}
.kggDebugPanelOverlay.open{display:flex}
.kggDebugPanel{
  width:min(96vw,760px);
  max-height:min(92vh,860px);
  overflow:auto;
  background:#fff;
  color:#071027;
  border:2px solid #111827;
  border-radius:24px;
  box-shadow:0 26px 90px rgba(7,16,39,.32);
  padding:14px;
  font-family:system-ui,-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,Arial,sans-serif;
}
.kggDebugHeader{display:grid;grid-template-columns:minmax(0,1fr) auto;gap:10px;align-items:start;margin-bottom:10px}
.kggDebugHeader h2{margin:0;font-size:24px;line-height:1.05;font-weight:1000}
.kggDebugHeader small{display:block;margin-top:4px;color:#657386;font-weight:800}
.kggDebugClose{border:0;border-radius:999px;width:42px;height:42px;font-size:24px;font-weight:1000;background:#f1f5f9;color:#111827}
.kggDebugGrid,.kggDebugStatus{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:8px;margin:10px 0}
.kggDebugGrid button,.kggDebugCopyBtn{border:1px solid #dce3eb;border-radius:14px;background:#f8fafc;color:#071027;min-height:44px;padding:9px 10px;font-weight:1000}
.kggDebugGrid button.primary,.kggDebugCopyBtn.primary{background:#071027;color:#fff;border-color:#071027}
.kggDebugGrid button.warn{background:#fff8e8;border-color:#f2d38a}
.kggDebugStatusCard{border:1px solid #dce3eb;border-radius:16px;padding:10px;background:#f8fafc;min-width:0}
.kggDebugStatusCard b{display:block;font-size:12px;color:#657386;margin-bottom:4px}
.kggDebugStatusCard span{display:block;font-size:14px;font-weight:1000;word-break:break-word}
.kggDebugProblemBox{border:1px solid #dce3eb;border-radius:16px;background:#f8fafc;padding:10px;margin:10px 0}
.kggDebugProblemBox label{display:block;color:#657386;font-size:12px;font-weight:1000;margin:8px 0 4px}
.kggDebugProblemBox select,.kggDebugProblemBox textarea{width:100%;border:1px solid #dce3eb;border-radius:12px;background:#fff;color:#071027;padding:10px;font:inherit}
.kggDebugProblemBox textarea{min-height:70px;resize:vertical}
.kggDebugOutput{
  width:100%;
  min-height:220px;
  max-height:42vh;
  overflow:auto;
  border:1px solid #dce3eb;
  border-radius:16px;
  background:#071027;
  color:#e5e7eb;
  padding:10px;
  font:12px/1.35 ui-monospace,SFMono-Regular,Menlo,Consolas,monospace;
  white-space:pre-wrap;
}
.kggDebugToast{
  position:fixed;
  left:50%;
  bottom:calc(18px + env(safe-area-inset-bottom,0px));
  transform:translateX(-50%);
  z-index:5002;
  background:#111827;
  color:#fff;
  border-radius:999px;
  padding:10px 14px;
  font-weight:1000;
  box-shadow:0 10px 34px rgba(7,16,39,.24);
  opacity:0;
  pointer-events:none;
  transition:opacity .18s ease,transform .18s ease;
}
.kggDebugToast.show{opacity:1;transform:translateX(-50%) translateY(-4px)}
@media (min-width:760px){
  #kggAdminDebugFab{
    top:84px!important;
    right:18px!important;
    bottom:auto!important;
    min-width:112px!important;
    min-height:44px!important;
  }
}
@media (max-width:759px){
  .kggDebugPanelOverlay{align-items:flex-end;padding:0}
  .kggDebugPanel{width:100%;max-height:88vh;border-radius:24px 24px 0 0;border-left:0;border-right:0;border-bottom:0}
  .kggDebugGrid,.kggDebugStatus{grid-template-columns:1fr}
}
/* KGG PATCH END: kgg-v023-admin-debug-visible-hotfix-style */
'''.strip()

JS = r'''
(function(){
'use strict';
var PATCH_ID='kgg-v023-admin-debug-visible-hotfix';
var errs=[];
function now(){try{return new Date().toISOString()}catch(e){return String(Date.now())}}
function push(kind,err){errs.push({time:now(),kind:kind,message:String(err&&(err.message||err.reason)||err||''),stack:String(err&&err.stack||'')});if(errs.length>30)errs.shift()}
window.addEventListener('error',function(e){push('window.error',e.error||e.message)});
window.addEventListener('unhandledrejection',function(e){push('unhandledrejection',e.reason||e)});
function q(s,r){return (r||document).querySelector(s)}
function esc(v){return String(v==null?'':v).replace(/[&<>"']/g,function(c){return {'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]})}
function readJson(id){var el=document.getElementById(id);if(!el)return null;try{return JSON.parse((el.textContent||'').trim())}catch(e){return {parseError:String(e)}}}
function txt(id){var el=document.getElementById(id);return el?String(el.textContent||'').trim():''}
function rect(sel){var el=q(sel);if(!el)return null;var r=el.getBoundingClientRect();return {x:Math.round(r.x),y:Math.round(r.y),w:Math.round(r.width),h:Math.round(r.height),display:getComputedStyle(el).display,visibility:getComputedStyle(el).visibility,visible:!!(r.width||r.height)}}
function version(){var st=readJson('kgg-source-truth')||{},cv=st.currentVersion||st.currentWebVersion||{};return {versionCode:cv.versionCode||null,versionName:cv.versionName||null,patchId:cv.lastPatchId||st.latestPatchId||null,runtimeBadge:txt('kggRuntimeVersion'),buildBadge:txt('kggBuildBadge'),title:document.title||''}}
function features(){return {barcodeDetector:'BarcodeDetector'in window,jsQR:typeof window.jsQR==='function',qrGalleryDebug:!!window.KGG_QR_GALLERY_DEBUG,serviceWorker:!!navigator.serviceWorker,clipboard:!!(navigator.clipboard&&navigator.clipboard.writeText),localStorage:(function(){try{var k='__kgg_dbg_'+Date.now();localStorage.setItem(k,'1');localStorage.removeItem(k);return true}catch(e){return false}})(),online:navigator.onLine}}
function layout(){return {width:innerWidth,height:innerHeight,dpr:devicePixelRatio||1,mediaPhone:matchMedia('(max-width:759px)').matches,mediaTablet:matchMedia('(min-width:760px)').matches,bodyClasses:document.body?Array.prototype.slice.call(document.body.classList):[],app:rect('.app'),scanHub:rect('#scanHub,.scanHub'),tabletMenuBtn:rect('#tabletMenuBtn,.tabletMenuBtn'),tabletSideMenu:rect('#tabletSideMenu,.tabletSideMenu'),debugFab:rect('#kggAdminDebugFab'),adminConfigBtn:rect('#adminConfigBtn'),sharedBankBtn:rect('#sharedBankBtn'),syncQrBtn:rect('#syncQrBtn')}}
function storageInfo(){var a=[];try{for(var i=0;i<localStorage.length;i++){var k=localStorage.key(i);a.push({key:k,length:String(localStorage.getItem(k)||'').length})}}catch(e){a.push({error:String(e)})}a.sort(function(x,y){return String(x.key).localeCompare(String(y.key))});return {totalKeys:a.length,localStorageKeys:a.slice(0,80)}}
function sourceSummary(){var st=readJson('kgg-source-truth'),cl=readJson('kgg-changelog'),pr=readJson('kgg-patch-rules');return {sourceTruth:st?{currentVersion:st.currentVersion||st.currentWebVersion||null,latestPatchId:st.latestPatchId||null,activeFixes:st.activeFixes||null,parseError:st.parseError||null}:null,changelog:cl?{latestVersionCode:cl.latestVersionCode||null,latestVersionName:cl.latestVersionName||null,entryCount:Array.isArray(cl.entries)?cl.entries.length:null,latestEntries:Array.isArray(cl.entries)?cl.entries.slice(0,6).map(function(e){return {patchId:e.patchId,versionName:e.versionName,title:e.title,status:e.status}}):null,parseError:cl.parseError||null}:null,patchRules:pr?{schema:pr.schema||null,mustUpdateOnEveryPatch:pr.mustUpdateOnEveryPatch||null,adminDebugMenuPolicy:pr.adminDebugMenuPolicy||null,parseError:pr.parseError||null}:null}}
function problem(){return {type:(q('#kggDebugProblemType')||{}).value||'',notes:(q('#kggDebugProblemNotes')||{}).value||''}}
function report(){var qr=null;try{qr=window.KGG_QR_GALLERY_DEBUG&&typeof window.KGG_QR_GALLERY_DEBUG.check==='function'?window.KGG_QR_GALLERY_DEBUG.check():null}catch(e){qr={error:String(e)}}return {generatedAt:now(),patchId:PATCH_ID,url:location.href,userProblem:problem(),version:version(),features:features(),layout:layout(),sourceTruth:sourceSummary(),storage:storageInfo(),qrGalleryDebug:qr,lastErrors:errs.slice(),userAgent:navigator.userAgent}}
function pretty(v){return JSON.stringify(v,null,2)}
function card(k,v){return '<div class="kggDebugStatusCard"><b>'+esc(k)+'</b><span>'+esc(v)+'</span></div>'}
function toast(m){var t=q('#kggDebugToast');if(!t){t=document.createElement('div');t.id='kggDebugToast';t.className='kggDebugToast';document.body.appendChild(t)}t.textContent=m;t.classList.add('show');clearTimeout(toast.t);toast.t=setTimeout(function(){t.classList.remove('show')},1800)}
function update(){var out=q('#kggDebugOutput');if(out)out.value=pretty(report());var s=q('#kggDebugStatus'),f=features(),v=version(),l=layout();if(s)s.innerHTML=[card('Version',v.versionName||v.buildBadge||'unbekannt'),card('Layout',l.mediaTablet?'Tablet ≥760':'Handy <760'),card('Debug Button',l.debugFab&&l.debugFab.visible?'sichtbar':'nicht sichtbar'),card('BarcodeDetector',f.barcodeDetector?'ja':'nein'),card('jsQR',f.jsQR?'ja':'nein'),card('QR Debug',f.qrGalleryDebug?'ja':'nein')].join('')}
async function copy(){update();var out=q('#kggDebugOutput'),s=out?out.value:pretty(report());try{if(navigator.clipboard&&navigator.clipboard.writeText){await navigator.clipboard.writeText(s)}else{var ta=document.createElement('textarea');ta.value=s;ta.style.position='fixed';ta.style.left='-100vw';document.body.appendChild(ta);ta.focus();ta.select();document.execCommand('copy');ta.remove()}toast('Debug-Bericht kopiert')}catch(e){push('copy',e);toast('Kopieren fehlgeschlagen')}}
function click(sel,msg){var el=q(sel);if(el){el.click();return true}toast(msg||'Button nicht gefunden');return false}
function act(a){try{if(a==='adminConfig'){close();click('#adminConfigBtn','Admin-Konfig nicht gefunden')}else if(a==='sharedBank'){close();click('#sharedBankBtn','Übungsdatenbank teilen nicht gefunden')}else if(a==='syncQr'){close();click('#syncQrBtn','QR/Sync nicht gefunden')}else if(a==='qrDebug'){var out=q('#kggDebugOutput');if(out)out.value=pretty(window.KGG_QR_GALLERY_DEBUG&&window.KGG_QR_GALLERY_DEBUG.check?window.KGG_QR_GALLERY_DEBUG.check():{available:false,reason:'KGG_QR_GALLERY_DEBUG fehlt'})}else if(a==='sourceTruth'){var o=q('#kggDebugOutput');if(o)o.value=pretty(sourceSummary())}else if(a==='refresh'){update();toast('Debug aktualisiert')}else if(a==='copy'){copy()}}catch(e){push('action:'+a,e);update()}}
function ensureModal(){if(q('#kggDebugPanelOverlay'))return;var o=document.createElement('div');o.id='kggDebugPanelOverlay';o.className='kggDebugPanelOverlay';o.innerHTML='<section class="kggDebugPanel" role="dialog" aria-modal="true" aria-labelledby="kggDebugTitle"><div class="kggDebugHeader"><div><h2 id="kggDebugTitle">🛠 Admin Debug / Feedback</h2><small>Nur intern. Bericht kopieren und in Chat/GitHub posten.</small></div><button class="kggDebugClose" id="kggDebugClose" type="button">×</button></div><div id="kggDebugStatus" class="kggDebugStatus"></div><div class="kggDebugGrid"><button type="button" data-kgg-debug-action="refresh" class="primary">Diagnose aktualisieren</button><button type="button" data-kgg-debug-action="copy" class="primary">Bericht kopieren</button><button type="button" data-kgg-debug-action="qrDebug">QR-Debug</button><button type="button" data-kgg-debug-action="sourceTruth">Source Truth</button><button type="button" data-kgg-debug-action="syncQr" class="warn">QR / Sync</button><button type="button" data-kgg-debug-action="adminConfig" class="warn">Admin-Konfig</button><button type="button" data-kgg-debug-action="sharedBank" class="warn">Übungsdatenbank teilen</button></div><div class="kggDebugProblemBox"><label>Problemtyp</label><select id="kggDebugProblemType"><option value="qr-gallery">QR aus Galerie</option><option value="tablet-layout">Tablet-Layout</option><option value="phone-menu">Handy-Menü</option><option value="update">Update/PWA</option><option value="storage">Speicher/Plan-State</option><option value="other">Sonstiges</option></select><label>Notiz von Max</label><textarea id="kggDebugProblemNotes" placeholder="Was ist passiert?"></textarea></div><textarea id="kggDebugOutput" class="kggDebugOutput" readonly spellcheck="false"></textarea><button type="button" class="kggDebugCopyBtn primary" data-kgg-debug-action="copy">Debug-Bericht kopieren</button></section>';document.body.appendChild(o);o.addEventListener('click',function(e){if(e.target===o)close();var b=e.target&&e.target.closest&&e.target.closest('[data-kgg-debug-action]');if(b)act(b.getAttribute('data-kgg-debug-action'))});q('#kggDebugClose').addEventListener('click',close);var t=q('#kggDebugProblemType'),n=q('#kggDebugProblemNotes');if(t)t.addEventListener('change',update);if(n)n.addEventListener('input',function(){clearTimeout(n.t);n.t=setTimeout(update,180)})}
function open(defaultType){ensureModal();var o=q('#kggDebugPanelOverlay'),t=q('#kggDebugProblemType');if(t&&defaultType)t.value=defaultType;update();o.classList.add('open');o.setAttribute('aria-hidden','false')}
function close(){var o=q('#kggDebugPanelOverlay');if(o){o.classList.remove('open');o.setAttribute('aria-hidden','true')}}
function ensureFab(){if(q('#kggAdminDebugFab'))return;var b=document.createElement('button');b.id='kggAdminDebugFab';b.type='button';b.textContent='🛠 Debug';b.setAttribute('aria-label','KGG Admin Debug öffnen');b.addEventListener('click',function(){open(matchMedia('(min-width:760px)').matches?'tablet-layout':'phone-menu')});document.body.appendChild(b)}
function init(){ensureFab();ensureModal();update()}
window.KGG_ADMIN_DEBUG_MENU={patchId:PATCH_ID,open:open,close:close,report:report,refresh:update,errors:function(){return errs.slice()}};
if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',init);else init();
})();
'''.strip()


def fail(msg: str) -> None:
    print('ERROR:', msg)
    sys.exit(1)


def read_json(path: Path, fallback: dict) -> dict:
    try:
        data = json.loads(path.read_text(encoding='utf-8'))
        return data if isinstance(data, dict) else fallback
    except Exception:
        return fallback


def next_code(manifest: dict, version_name: str) -> int:
    try:
        cur = int(manifest.get('versionCode', 0))
    except Exception:
        cur = 0
    return cur if manifest.get('versionName') == version_name else cur + 1


def comment_spans(html: str):
    return [(m.start(), m.end()) for m in re.finditer(r'<!--.*?-->', html, re.S)]


def in_spans(pos: int, spans) -> bool:
    return any(start <= pos < end for start, end in spans)


def json_pat(script_id: str) -> re.Pattern:
    return re.compile(
        r'<script\b(?=[^>]*\bid=["\']' + re.escape(script_id) + r'["\'])'
        r'(?=[^>]*\btype=["\']application/json["\'])[^>]*>\s*(.*?)\s*</script>',
        re.I | re.S,
    )


def first_active_match(html: str, pat: re.Pattern):
    spans = comment_spans(html)
    for match in pat.finditer(html):
        if not in_spans(match.start(), spans):
            return match
    return None


def load_active_json(html: str, script_id: str, fallback: dict) -> dict:
    match = first_active_match(html, json_pat(script_id))
    if not match:
        return fallback
    try:
        data = json.loads(match.group(1).strip())
        return data if isinstance(data, dict) else fallback
    except Exception:
        return fallback


def replace_active_json(html: str, script_id: str, data: dict, anchor: str | None = None) -> str:
    block = '<script type="application/json" id="' + script_id + '">\n' + json.dumps(data, ensure_ascii=False, indent=2) + '\n</script>'
    pat = json_pat(script_id)
    match = first_active_match(html, pat)
    if match:
        return html[:match.start()] + block + html[match.end():]
    if anchor and anchor in html:
        idx = html.find(anchor) + len(anchor)
        return html[:idx] + '\n' + block + html[idx:]
    idx = html.lower().find('</head>')
    return html[:idx] + block + '\n' + html[idx:] if idx >= 0 else html + '\n' + block + '\n'


def upsert_tag(html: str, tag: str, tag_id: str, content: str, before: str) -> str:
    block = '<' + tag + ' id="' + tag_id + '">\n' + content + '\n</' + tag + '>'
    pat = re.compile(r'<' + tag + r'\b(?=[^>]*\bid=["\']' + re.escape(tag_id) + r'["\'])[^>]*>.*?</' + tag + r'>', re.I | re.S)
    match = first_active_match(html, pat)
    if match:
        return html[:match.start()] + block + html[match.end():]
    idx = html.lower().rfind(before)
    return html[:idx] + block + '\n' + html[idx:] if idx >= 0 else html + '\n' + block + '\n'


def update_meta(html: str, release: dict, manifest: dict) -> str:
    version_name = release.get('versionName') or VERSION_NAME
    code = next_code(manifest, version_name)

    source = load_active_json(html, 'kgg-source-truth', {'schema': 1, 'app': 'KGG Plan', 'activeFixes': []})
    current = source.get('currentVersion') if isinstance(source.get('currentVersion'), dict) else {}
    current.update({
        'versionCode': code,
        'versionName': version_name,
        'lastPatchId': PATCH_ID,
        'updatedBy': 'update-inbox',
    })
    source['currentVersion'] = current
    source['latestPatchId'] = PATCH_ID
    fixes = source.get('activeFixes') if isinstance(source.get('activeFixes'), list) else []
    for item in ['admin-debug-visible-hotfix', 'admin-debug-menu-feedback', 'embedded-source-truth', 'patch-retention-guard']:
        if item not in fixes:
            fixes.append(item)
    source['activeFixes'] = fixes
    source['lastUpdateIntent'] = {
        'id': PATCH_ID,
        'summary': 'Hotfix: make admin debug entry visible independent of adminMode and repair active source-truth block.',
        'touched': ['Admin debug UI', 'HTML embedded metadata', 'Source Truth', 'Changelog', 'Patch rules'],
        'notTouched': PROTECTED,
    }
    html = replace_active_json(html, 'kgg-source-truth', source, '<!-- END kgg-source-truth -->')

    changelog = load_active_json(html, 'kgg-changelog', {'schema': 1, 'entries': []})
    entries = changelog.get('entries') if isinstance(changelog.get('entries'), list) else []
    entries = [entry for entry in entries if not (isinstance(entry, dict) and entry.get('patchId') == PATCH_ID)]
    entries.insert(0, {
        'versionCode': code,
        'versionName': version_name,
        'patchId': PATCH_ID,
        'status': 'active',
        'type': 'github-web-update',
        'title': 'Admin Debug sichtbar Hotfix',
        'reason': 'v022 aktualisierte Version/Metadaten, aber der sichtbare Debug-Einstieg erschien in der Tablet-UI nicht zuverlässig.',
        'whatChanged': [
            'Adds always-visible Admin Debug floating button independent of .adminMode.',
            'Keeps KGG_ADMIN_DEBUG_MENU.report() available for future agents.',
            'Repairs active kgg-source-truth insertion when older source-truth text is trapped inside an HTML comment.',
            'Does not change PDF, QR generation, patient app, scan camera, parser, plan state or storage.',
        ],
        'touchedAreas': ['Admin debug UI', 'HTML embedded metadata', 'Source Truth', 'Changelog', 'Patch rules'],
        'notTouched': PROTECTED,
        'testStatus': {
            'debugFabVisible': 'pending',
            'debugReportCopy': 'pending',
            'workflowIndexUrl': 'pending',
        },
        'createdAt': datetime.now(timezone.utc).isoformat(),
    })
    changelog['schema'] = changelog.get('schema', 1)
    changelog['latestVersionCode'] = code
    changelog['latestVersionName'] = version_name
    changelog['entries'] = entries
    html = replace_active_json(html, 'kgg-changelog', changelog, '<!-- END kgg-changelog -->')

    rules = load_active_json(html, 'kgg-patch-rules', {'schema': 1})
    rules['adminDebugVisibleHotfix'] = {
        'patchId': PATCH_ID,
        'purpose': 'Debug entry must be visible in admin/therapist app even when adminMode class is missing.',
        'expectedGlobal': 'KGG_ADMIN_DEBUG_MENU.report()',
        'expectedButton': '#kggAdminDebugFab',
        'doNotRemoveWithout': ['supersededBy', 'reason', 'testEvidence', 'Max approval'],
    }
    must = rules.get('mustUpdateOnEveryPatch') if isinstance(rules.get('mustUpdateOnEveryPatch'), list) else []
    for item in ['kgg-source-truth.currentVersion', 'kgg-changelog.entries', 'kgg-patch-rules', 'kgg-update/version.json.indexUrl']:
        if item not in must:
            must.append(item)
    rules['mustUpdateOnEveryPatch'] = must
    html = replace_active_json(html, 'kgg-patch-rules', rules, '<!-- END kgg-patch-rules -->')
    return html


def validate(html: str) -> None:
    active_html = re.sub(r'<!--.*?-->', '', html, flags=re.S)
    required = [
        '<!doctype html',
        STYLE_ID,
        SCRIPT_ID,
        PATCH_ID,
        'KGG_ADMIN_DEBUG_MENU',
        'kggAdminDebugFab',
        'id="kgg-source-truth"',
        'id="kgg-changelog"',
    ]
    for token in required:
        if token.lower() not in active_html.lower():
            fail('required active token missing: ' + token)
    if len(re.findall(r'<style\b(?=[^>]*\bid=["\']' + re.escape(STYLE_ID) + r'["\'])', active_html, re.I)) != 1:
        fail('style tag count invalid')
    if len(re.findall(r'<script\b(?=[^>]*\bid=["\']' + re.escape(SCRIPT_ID) + r'["\'])', active_html, re.I)) != 1:
        fail('script tag count invalid')


def main() -> None:
    if not HTML_PATH.exists():
        fail(f'missing {HTML_PATH}')
    release = read_json(RELEASE_PATH, {'versionName': VERSION_NAME})
    manifest = read_json(VERSION_PATH, {})
    html = HTML_PATH.read_text(encoding='utf-8')
    idx = html.lower().find('<!doctype html')
    if idx < 0:
        fail('doctype missing')
    html = html[idx:]
    html = upsert_tag(html, 'style', STYLE_ID, CSS, '</head>')
    html = upsert_tag(html, 'script', SCRIPT_ID, JS, '</body>')
    html = update_meta(html, release, manifest)
    validate(html)
    HTML_PATH.write_text(html, encoding='utf-8', newline='\n')
    print('Applied', PATCH_ID)
    print('Expected versionName:', release.get('versionName') or VERSION_NAME)


if __name__ == '__main__':
    main()
