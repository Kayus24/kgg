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
PATCH_ID = 'kgg-v022-admin-debug-menu-feedback'
VERSION_NAME = '1.0.22-admin-debug-menu-feedback'
STYLE_ID = PATCH_ID + '-style'
SCRIPT_ID = PATCH_ID + '-script'
PROTECTED = ['PDF','QR-Erzeugung','Patienten-App','Scan-Kamera','Parser','Android-Wrapper','Tablet core layout/breakpoints','Plan-State','Storage']

CSS = r'''
/* KGG PATCH START: kgg-v022-admin-debug-menu-feedback-style */
.kggAdminDebugBtn,.kggAdminHubBtn{width:100%;margin-top:10px;border:1px solid var(--line,#dce3eb);border-radius:14px;padding:10px 12px;font-weight:1000;font-size:16px;background:#fff;color:var(--ink,#071027);box-shadow:var(--shadow,0 4px 14px rgba(7,16,39,.08));display:none;align-items:center;justify-content:center;gap:8px}.kggAdminHubBtn{background:#071027;color:#fff;border-color:#071027}.adminMode .kggAdminDebugBtn{display:flex}.kggDebugPanelOverlay{position:fixed;inset:0;z-index:9998;display:none;align-items:center;justify-content:center;background:rgba(7,16,39,.46);padding:14px}.kggDebugPanelOverlay.open{display:flex}.kggDebugPanel{width:min(96vw,760px);max-height:min(92vh,860px);overflow:auto;background:#fff;color:#071027;border:2px solid #111827;border-radius:24px;box-shadow:0 26px 90px rgba(7,16,39,.32);padding:14px}.kggDebugHeader{display:grid;grid-template-columns:minmax(0,1fr) auto;gap:10px;align-items:start;margin-bottom:10px}.kggDebugHeader h2{margin:0;font-size:24px;line-height:1.05;font-weight:1000}.kggDebugHeader small{display:block;margin-top:4px;color:#657386;font-weight:800}.kggDebugClose{border:0;border-radius:999px;width:42px;height:42px;font-size:24px;font-weight:1000;background:#f1f5f9;color:#111827}.kggDebugGrid,.kggDebugStatus{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:8px;margin:10px 0}.kggDebugGrid button,.kggDebugCopyBtn{border:1px solid #dce3eb;border-radius:14px;background:#f8fafc;color:#071027;min-height:44px;padding:9px 10px;font-weight:1000}.kggDebugGrid button.primary,.kggDebugCopyBtn.primary{background:#071027;color:#fff;border-color:#071027}.kggDebugGrid button.warn{background:#fff8e8;border-color:#f2d38a}.kggDebugStatusCard{border:1px solid #dce3eb;border-radius:16px;padding:10px;background:#f8fafc;min-width:0}.kggDebugStatusCard b{display:block;font-size:12px;color:#657386;margin-bottom:4px}.kggDebugStatusCard span{display:block;font-size:14px;font-weight:1000;word-break:break-word}.kggDebugProblemBox{border:1px solid #dce3eb;border-radius:16px;background:#f8fafc;padding:10px;margin:10px 0}.kggDebugProblemBox label{display:block;color:#657386;font-size:12px;font-weight:1000;margin:8px 0 4px}.kggDebugProblemBox select,.kggDebugProblemBox textarea{width:100%;border:1px solid #dce3eb;border-radius:12px;background:#fff;color:#071027;padding:10px;font:inherit}.kggDebugProblemBox textarea{min-height:80px;resize:vertical}.kggDebugOutput{width:100%;min-height:220px;max-height:42vh;overflow:auto;border:1px solid #dce3eb;border-radius:16px;background:#071027;color:#e5e7eb;padding:10px;font:12px/1.35 ui-monospace,SFMono-Regular,Menlo,Consolas,monospace;white-space:pre-wrap}.kggDebugToast{position:fixed;left:50%;bottom:calc(18px + env(safe-area-inset-bottom,0px));transform:translateX(-50%);z-index:9999;background:#111827;color:#fff;border-radius:999px;padding:10px 14px;font-weight:1000;box-shadow:0 10px 34px rgba(7,16,39,.24);opacity:0;pointer-events:none;transition:opacity .18s ease,transform .18s ease}.kggDebugToast.show{opacity:1;transform:translateX(-50%) translateY(-4px)}@media (min-width:760px){.adminMode .scanHub .kggAdminDebugBtn{display:flex!important}.adminMode .scanHub .kggAdminHubBtn{display:none!important}}@media (max-width:759px){.adminMode .scanHub .kggAdminDebugBtn{display:none!important}.adminMode .scanHub .kggAdminHubBtn{display:flex!important}.adminMode .scanHub #adminConfigBtn,.adminMode .scanHub #sharedBankBtn,.adminMode .scanHub #syncQrBtn,.adminMode .scanHub .adminConfigBtn,.adminMode .scanHub .sharedBankBtn,.adminMode .scanHub .syncQrBtn{display:none!important}.kggDebugPanelOverlay{align-items:flex-end;padding:0}.kggDebugPanel{width:100%;max-height:88vh;border-radius:24px 24px 0 0;border-left:0;border-right:0;border-bottom:0}.kggDebugGrid,.kggDebugStatus{grid-template-columns:1fr}}
/* KGG PATCH END: kgg-v022-admin-debug-menu-feedback-style */
'''.strip()

JS = r'''
(function(){
'use strict';
var PATCH_ID='kgg-v022-admin-debug-menu-feedback';
var errs=[];
function now(){try{return new Date().toISOString()}catch(e){return String(Date.now())}}
function push(kind,err){errs.push({time:now(),kind:kind,message:String(err&& (err.message||err.reason)||err||''),stack:String(err&&err.stack||'')});if(errs.length>20)errs.shift()}
window.addEventListener('error',function(e){push('window.error',e.error||e.message)});
window.addEventListener('unhandledrejection',function(e){push('unhandledrejection',e.reason||e)});
function q(s,r){return(r||document).querySelector(s)}
function esc(v){return String(v==null?'':v).replace(/[&<>"']/g,function(c){return {'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]})}
function readJson(id){var el=document.getElementById(id);if(!el)return null;try{return JSON.parse((el.textContent||'').trim())}catch(e){return {parseError:String(e)}}}
function txt(id){var el=document.getElementById(id);return el?String(el.textContent||'').trim():''}
function rect(sel){var el=q(sel);if(!el)return null;var r=el.getBoundingClientRect();return {x:Math.round(r.x),y:Math.round(r.y),w:Math.round(r.width),h:Math.round(r.height),display:getComputedStyle(el).display,visible:!!(r.width||r.height)}}
function version(){var st=readJson('kgg-source-truth')||{},cv=st.currentVersion||st.currentWebVersion||{};return {versionCode:cv.versionCode||null,versionName:cv.versionName||null,patchId:cv.lastPatchId||st.latestPatchId||null,runtimeBadge:txt('kggRuntimeVersion'),buildBadge:txt('kggBuildBadge'),title:document.title||''}}
function features(){return {barcodeDetector:'BarcodeDetector'in window,jsQR:typeof window.jsQR==='function',qrGalleryDebug:!!window.KGG_QR_GALLERY_DEBUG,serviceWorker:!!navigator.serviceWorker,clipboard:!!(navigator.clipboard&&navigator.clipboard.writeText),localStorage:(function(){try{var k='__kgg_dbg_'+Date.now();localStorage.setItem(k,'1');localStorage.removeItem(k);return true}catch(e){return false}})(),online:navigator.onLine}}
function layout(){return {width:innerWidth,height:innerHeight,dpr:devicePixelRatio||1,mediaPhone:matchMedia('(max-width:759px)').matches,mediaTablet:matchMedia('(min-width:760px)').matches,bodyClasses:document.body?Array.prototype.slice.call(document.body.classList):[],app:rect('.app'),scanHub:rect('#scanHub,.scanHub'),adminConfigBtn:rect('#adminConfigBtn'),sharedBankBtn:rect('#sharedBankBtn'),syncQrBtn:rect('#syncQrBtn'),debugBtn:rect('#kggAdminDebugBtn'),adminHubBtn:rect('#kggAdminHubBtn')}}
function storageInfo(){var a=[];try{for(var i=0;i<localStorage.length;i++){var k=localStorage.key(i);a.push({key:k,length:String(localStorage.getItem(k)||'').length})}}catch(e){a.push({error:String(e)})}a.sort(function(x,y){return String(x.key).localeCompare(String(y.key))});return {totalKeys:a.length,localStorageKeys:a.slice(0,80)}}
function sourceSummary(){var st=readJson('kgg-source-truth'),cl=readJson('kgg-changelog'),pr=readJson('kgg-patch-rules');return {sourceTruth:st?{currentVersion:st.currentVersion||st.currentWebVersion||null,latestPatchId:st.latestPatchId||null,activeFixes:st.activeFixes||null,parseError:st.parseError||null}:null,changelog:cl?{latestVersionCode:cl.latestVersionCode||null,latestVersionName:cl.latestVersionName||null,entryCount:Array.isArray(cl.entries)?cl.entries.length:null,latestEntries:Array.isArray(cl.entries)?cl.entries.slice(0,5).map(function(e){return {patchId:e.patchId,versionName:e.versionName,title:e.title,status:e.status}}):null,parseError:cl.parseError||null}:null,patchRules:pr?{schema:pr.schema||null,mustUpdateOnEveryPatch:pr.mustUpdateOnEveryPatch||null,adminDebugMenuPolicy:pr.adminDebugMenuPolicy||null,parseError:pr.parseError||null}:null}}
function problem(){return {type:(q('#kggDebugProblemType')||{}).value||'',notes:(q('#kggDebugProblemNotes')||{}).value||''}}
function report(){var qr=null;try{qr=window.KGG_QR_GALLERY_DEBUG&&typeof window.KGG_QR_GALLERY_DEBUG.check==='function'?window.KGG_QR_GALLERY_DEBUG.check():null}catch(e){qr={error:String(e)}}return {generatedAt:now(),patchId:PATCH_ID,url:location.href,userProblem:problem(),version:version(),features:features(),layout:layout(),sourceTruth:sourceSummary(),storage:storageInfo(),qrGalleryDebug:qr,lastErrors:errs.slice(),userAgent:navigator.userAgent}}
function pretty(v){return JSON.stringify(v,null,2)}
function card(k,v){return '<div class="kggDebugStatusCard"><b>'+esc(k)+'</b><span>'+esc(v)+'</span></div>'}
function toast(m){var t=q('#kggDebugToast');if(!t){t=document.createElement('div');t.id='kggDebugToast';t.className='kggDebugToast';document.body.appendChild(t)}t.textContent=m;t.classList.add('show');clearTimeout(toast.t);toast.t=setTimeout(function(){t.classList.remove('show')},1800)}
function update(){var out=q('#kggDebugOutput');if(out)out.value=pretty(report());var s=q('#kggDebugStatus'),f=features(),v=version(),l=layout();if(s)s.innerHTML=[card('Version',v.versionName||v.buildBadge||'unbekannt'),card('Layout',l.mediaTablet?'Tablet ≥760':'Handy <760'),card('BarcodeDetector',f.barcodeDetector?'ja':'nein'),card('jsQR',f.jsQR?'ja':'nein'),card('QR Debug',f.qrGalleryDebug?'ja':'nein'),card('Online',f.online?'ja':'nein')].join('')}
async function copy(){update();var out=q('#kggDebugOutput'),s=out?out.value:pretty(report());try{if(navigator.clipboard&&navigator.clipboard.writeText){await navigator.clipboard.writeText(s)}else{var ta=document.createElement('textarea');ta.value=s;ta.style.position='fixed';ta.style.left='-100vw';document.body.appendChild(ta);ta.focus();ta.select();document.execCommand('copy');ta.remove()}toast('Debug-Bericht kopiert')}catch(e){push('copy',e);toast('Kopieren fehlgeschlagen')}}
function click(sel,msg){var el=q(sel);if(el){el.click();return true}toast(msg||'Button nicht gefunden');return false}
function act(a){try{if(a==='adminConfig'){close();click('#adminConfigBtn','Admin-Konfig nicht gefunden')}else if(a==='sharedBank'){close();click('#sharedBankBtn','Übungsdatenbank teilen nicht gefunden')}else if(a==='syncQr'){close();click('#syncQrBtn','QR/Sync nicht gefunden')}else if(a==='qrDebug'){var out=q('#kggDebugOutput');if(out)out.value=pretty(window.KGG_QR_GALLERY_DEBUG&&window.KGG_QR_GALLERY_DEBUG.check?window.KGG_QR_GALLERY_DEBUG.check():{available:false,reason:'KGG_QR_GALLERY_DEBUG fehlt'})}else if(a==='sourceTruth'){var o=q('#kggDebugOutput');if(o)o.value=pretty(sourceSummary())}else if(a==='refresh'){update();toast('Debug aktualisiert')}else if(a==='copy'){copy()}}catch(e){push('action:'+a,e);update()}}
function ensureModal(){if(q('#kggDebugPanelOverlay'))return;var o=document.createElement('div');o.id='kggDebugPanelOverlay';o.className='kggDebugPanelOverlay';o.innerHTML='<section class="kggDebugPanel" role="dialog" aria-modal="true" aria-labelledby="kggDebugTitle"><div class="kggDebugHeader"><div><h2 id="kggDebugTitle">🛠 Admin Debug / Feedback</h2><small>Nur intern. Bericht kopieren und in Chat/GitHub posten.</small></div><button class="kggDebugClose" id="kggDebugClose" type="button">×</button></div><div id="kggDebugStatus" class="kggDebugStatus"></div><div class="kggDebugGrid"><button type="button" data-kgg-debug-action="refresh" class="primary">Diagnose aktualisieren</button><button type="button" data-kgg-debug-action="copy" class="primary">Bericht kopieren</button><button type="button" data-kgg-debug-action="qrDebug">QR-Debug</button><button type="button" data-kgg-debug-action="sourceTruth">Source Truth</button><button type="button" data-kgg-debug-action="syncQr" class="warn">QR / Sync</button><button type="button" data-kgg-debug-action="adminConfig" class="warn">Admin-Konfig</button><button type="button" data-kgg-debug-action="sharedBank" class="warn">Übungsdatenbank teilen</button></div><div class="kggDebugProblemBox"><label>Problemtyp</label><select id="kggDebugProblemType"><option value="qr-gallery">QR aus Galerie</option><option value="tablet-layout">Tablet-Layout</option><option value="phone-menu">Handy-Menü</option><option value="update">Update/PWA</option><option value="storage">Speicher/Plan-State</option><option value="other">Sonstiges</option></select><label>Notiz von Max</label><textarea id="kggDebugProblemNotes" placeholder="Was ist passiert?"></textarea></div><textarea id="kggDebugOutput" class="kggDebugOutput" readonly spellcheck="false"></textarea><button type="button" class="kggDebugCopyBtn primary" data-kgg-debug-action="copy">Debug-Bericht kopieren</button></section>';document.body.appendChild(o);o.addEventListener('click',function(e){if(e.target===o)close();var b=e.target&&e.target.closest&&e.target.closest('[data-kgg-debug-action]');if(b)act(b.getAttribute('data-kgg-debug-action'))});q('#kggDebugClose').addEventListener('click',close);var t=q('#kggDebugProblemType'),n=q('#kggDebugProblemNotes');if(t)t.addEventListener('change',update);if(n)n.addEventListener('input',function(){clearTimeout(n.t);n.t=setTimeout(update,180)})}
function open(defaultType){ensureModal();var o=q('#kggDebugPanelOverlay'),t=q('#kggDebugProblemType');if(t&&defaultType)t.value=defaultType;update();o.classList.add('open');o.setAttribute('aria-hidden','false')}
function close(){var o=q('#kggDebugPanelOverlay');if(o){o.classList.remove('open');o.setAttribute('aria-hidden','true')}}
function buttons(){var hub=q('#scanHub')||q('.scanHub');if(!hub)return false;if(!q('#kggAdminDebugBtn')){var d=document.createElement('button');d.id='kggAdminDebugBtn';d.className='mutedBtn kggAdminDebugBtn';d.type='button';d.textContent='🛠 Debug';d.addEventListener('click',function(){open('tablet-layout')});var after=q('#sharedBankBtn')||q('#adminConfigBtn')||hub.lastElementChild;if(after&&after.parentNode===hub)after.insertAdjacentElement('afterend',d);else hub.appendChild(d)}if(!q('#kggAdminHubBtn')){var h=document.createElement('button');h.id='kggAdminHubBtn';h.className='kggAdminHubBtn';h.type='button';h.textContent='⚙ Admin-Menü';h.addEventListener('click',function(){open('phone-menu')});var fp=q('#filePickBtn')||hub.lastElementChild;if(fp&&fp.parentNode===hub)fp.insertAdjacentElement('afterend',h);else hub.appendChild(h)}document.documentElement.classList.add('kggAdminDebugMenuReady');return true}
function init(){ensureModal();if(buttons()){update();return}var i=0,t=setInterval(function(){i++;if(buttons()||i>40){clearInterval(t);update()}},150)}
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

def json_pat(script_id: str) -> re.Pattern:
    return re.compile(r'<script\b(?=[^>]*\bid=["\']'+re.escape(script_id)+r'["\'])(?=[^>]*\btype=["\']application/json["\'])[^>]*>\s*(.*?)\s*</script>', re.I|re.S)

def load_block(html: str, script_id: str, fallback: dict) -> dict:
    m = json_pat(script_id).search(html)
    if not m:
        return fallback
    try:
        data = json.loads(m.group(1).strip())
        return data if isinstance(data, dict) else fallback
    except Exception:
        return fallback

def replace_block(html: str, script_id: str, data: dict) -> str:
    block = '<script type="application/json" id="'+script_id+'">\n'+json.dumps(data, ensure_ascii=False, indent=2)+'\n</script>'
    pat = json_pat(script_id)
    if pat.search(html):
        return pat.sub(block, html, count=1)
    i = html.lower().find('</head>')
    return html[:i]+block+'\n'+html[i:] if i >= 0 else html+'\n'+block+'\n'

def upsert_tag(html: str, tag: str, tag_id: str, content: str, before: str) -> str:
    block = '<'+tag+' id="'+tag_id+'">\n'+content+'\n</'+tag+'>'
    pat = re.compile(r'<'+tag+r'\b(?=[^>]*\bid=["\']'+re.escape(tag_id)+r'["\'])[^>]*>.*?</'+tag+r'>', re.I|re.S)
    if pat.search(html):
        return pat.sub(block, html, count=1)
    i = html.lower().rfind(before)
    return html[:i]+block+'\n'+html[i:] if i >= 0 else html+'\n'+block

def update_meta(html: str, release: dict, manifest: dict) -> str:
    vn = release.get('versionName') or VERSION_NAME
    code = next_code(manifest, vn)
    st = load_block(html, 'kgg-source-truth', {'schema':1,'app':'KGG Plan','activeFixes':[]})
    cur = st.get('currentVersion') if isinstance(st.get('currentVersion'), dict) else {}
    cur.update({'versionCode':code,'versionName':vn,'lastPatchId':PATCH_ID,'updatedBy':'update-inbox'})
    st['currentVersion'] = cur
    st['latestPatchId'] = PATCH_ID
    fixes = st.get('activeFixes') if isinstance(st.get('activeFixes'), list) else []
    for item in ['admin-debug-menu-feedback','embedded-source-truth','patch-retention-guard']:
        if item not in fixes:
            fixes.append(item)
    st['activeFixes'] = fixes
    st['lastUpdateIntent'] = {'id':PATCH_ID,'summary':'Adds admin debug/feedback menu as v022. Tablet gets debug entry in scan/admin rail; phone gets consolidated Admin-Menue for admin actions.','touched':['Admin debug UI','HTML embedded metadata','Source Truth','Changelog','Patch rules'],'notTouched':PROTECTED}
    html = replace_block(html, 'kgg-source-truth', st)
    cl = load_block(html, 'kgg-changelog', {'schema':1,'entries':[]})
    entries = cl.get('entries') if isinstance(cl.get('entries'), list) else []
    entries = [e for e in entries if not (isinstance(e, dict) and e.get('patchId') == PATCH_ID)]
    entries.insert(0, {'versionCode':code,'versionName':vn,'patchId':PATCH_ID,'status':'active','type':'github-web-update','title':'Admin Debug-/Feedback-Menue','reason':'Max braucht eine Admin-Oberfläche, die bei QR-, Layout-, Update-, Speicher- und anderen Problemen direkt verwertbares Feedback liefert.','whatChanged':['Adds Admin Debug / Feedback menu as v022.','Tablet: Debug entry is inserted into the scan/admin side rail.','Phone: Admin-Konfig, QR/Sync and Übungsdatenbank teilen are hidden from the scan hub and exposed through one Admin-Menue button.','Debug report includes version, feature availability, QR debug, layout rectangles, source truth/changelog summary, localStorage key summary and last runtime errors.','Adds global KGG_ADMIN_DEBUG_MENU.report() for future agents.'],'touchedAreas':['Admin debug UI','HTML embedded metadata','Source Truth','Changelog','Patch rules'],'notTouched':PROTECTED,'testStatus':{'tabletMenu':'pending','phoneMenu':'pending','debugReportCopy':'pending','adminActions':'pending'},'rollbackNote':'Remove or supersede only with explicit new admin debug menu patch; do not silently delete feedback tooling.','createdAt':datetime.now(timezone.utc).isoformat()})
    cl['schema'] = cl.get('schema', 1)
    cl['latestVersionCode'] = code
    cl['latestVersionName'] = vn
    cl['entries'] = entries
    html = replace_block(html, 'kgg-changelog', cl)
    rules = load_block(html, 'kgg-patch-rules', {'schema':1})
    rules['adminDebugMenuPolicy'] = {'patchId':PATCH_ID,'purpose':'Keep an in-app admin feedback/debug path available for future QR/layout/update/storage issues.','doNotRemoveWithout':['supersededBy','reason','testEvidence','Max approval'],'expectedGlobal':'KGG_ADMIN_DEBUG_MENU.report()'}
    must = rules.get('mustUpdateOnEveryPatch') if isinstance(rules.get('mustUpdateOnEveryPatch'), list) else []
    for item in ['kgg-source-truth.currentVersion','kgg-changelog.entries','kgg-patch-rules']:
        if item not in must:
            must.append(item)
    rules['mustUpdateOnEveryPatch'] = must
    return replace_block(html, 'kgg-patch-rules', rules)

def validate(html: str) -> None:
    for token in ['<!doctype html', STYLE_ID, SCRIPT_ID, PATCH_ID, 'KGG_ADMIN_DEBUG_MENU', 'kggAdminHubBtn', 'kggAdminDebugBtn', 'Admin Debug / Feedback', 'id="kgg-source-truth"', 'id="kgg-changelog"']:
        if token.lower() not in html.lower():
            fail('required token missing: '+token)
    if len(re.findall(r'<style\b(?=[^>]*\bid=["\']'+re.escape(STYLE_ID)+r'["\'])', html, re.I)) != 1:
        fail('style tag count invalid')
    if len(re.findall(r'<script\b(?=[^>]*\bid=["\']'+re.escape(SCRIPT_ID)+r'["\'])', html, re.I)) != 1:
        fail('script tag count invalid')

def main() -> None:
    if not HTML_PATH.exists():
        fail(f'missing {HTML_PATH}')
    release = read_json(RELEASE_PATH, {'versionName':VERSION_NAME})
    manifest = read_json(VERSION_PATH, {})
    html = HTML_PATH.read_text(encoding='utf-8')
    i = html.lower().find('<!doctype html')
    if i < 0:
        fail('doctype missing')
    html = html[i:]
    html = upsert_tag(html, 'style', STYLE_ID, CSS, '</head>')
    html = upsert_tag(html, 'script', SCRIPT_ID, JS, '</body>')
    html = update_meta(html, release, manifest)
    validate(html)
    HTML_PATH.write_text(html, encoding='utf-8', newline='\n')
    print('Applied', PATCH_ID)
    print('Expected versionName:', release.get('versionName') or VERSION_NAME)

if __name__ == '__main__':
    main()
