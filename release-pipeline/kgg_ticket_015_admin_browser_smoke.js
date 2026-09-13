#!/usr/bin/env node
'use strict';

// Ticket 015 admin loop: responsive editor gallery, add, hold-main, sort and delete.
// Local preview only; service workers are disabled and no secrets are read.

const fs=require('fs');
const http=require('http');
const path=require('path');
const {chromium}=require('playwright');

const ROOT=path.resolve(__dirname,'..');
function fail(message){throw new Error(message)}
function assert(condition,message){if(!condition)fail(message)}
function encodePlan(plan){return Buffer.from(JSON.stringify(plan),'utf8').toString('base64url')}
function contentType(file){return {'.html':'text/html; charset=utf-8','.js':'text/javascript; charset=utf-8','.json':'application/json; charset=utf-8','.png':'image/png'}[path.extname(file).toLowerCase()]||'application/octet-stream'}
function safeFile(urlPath){const relative=decodeURIComponent(String(urlPath||'/').split('?')[0]).replace(/^\/+/, '')||'index.html';const target=path.resolve(ROOT,relative);if(!target.startsWith(ROOT+path.sep)&&target!==ROOT)return null;if(!fs.existsSync(target)||!fs.statSync(target).isFile())return null;return target}

async function main(){
  const server=http.createServer((request,response)=>{const file=safeFile(request.url);if(!file){response.writeHead(404);response.end('not found');return}response.writeHead(200,{'Content-Type':contentType(file),'Cache-Control':'no-store','Service-Worker-Allowed':'/'});fs.createReadStream(file).pipe(response)});
  await new Promise(resolve=>server.listen(0,'127.0.0.1',resolve));
  const port=server.address().port;
  const browser=await chromium.launch({headless:true});
  const context=await browser.newContext({viewport:{width:390,height:844},serviceWorkers:'block'});
  const page=await context.newPage();
  const errors=[];page.on('pageerror',error=>errors.push(error.message));
  const stageMedia='data:image/svg+xml,'+encodeURIComponent('<svg xmlns="http://www.w3.org/2000/svg" width="120" height="80"><rect width="120" height="80" fill="#dbeafe"/><circle cx="60" cy="40" r="22" fill="#2563eb"/></svg>');
  const exercise={id:'p-admin-1',localId:'p-admin-1',name:'Basis',sets:3,unit:'Wdh',weightUnit:'kg',measure:'wdh',media:[{id:'base-media',type:'image',src:stageMedia}],progressionGroupId:'admin-gallery-group',progressionMainId:'base',progressionVariants:[
    {id:'easy',name:'Leichter',order:0,media:[{id:'easy-media',type:'image',src:stageMedia}]},
    {id:'base',name:'Basis',order:1,media:[{id:'base-media',type:'image',src:stageMedia}]},
    {id:'hard',name:'Schwerer',order:2,media:[{id:'hard-media',type:'image',src:stageMedia}]},
  ]};
  const savedState={plan:[exercise],patient:{},packages:[],bankOpen:false,editId:null,sortMenuId:null,reorderSuppressClick:false,largePdfMode:false,textSyncing:false};
  await page.addInitScript(state=>localStorage.setItem('kgg_html_app_v2_state',JSON.stringify(state)),savedState);
  const url=`http://127.0.0.1:${port}/kgg-update/index.html`;
  try{
    await page.goto(url,{waitUntil:'domcontentloaded'});
    await page.waitForTimeout(900);const adminConfig=page.locator('#adminSecretsModal');if(await adminConfig.evaluate(node=>node.classList.contains('open')).catch(()=>false))await page.locator('#closeAdminSecrets').click();
    const card=page.locator('#planList .planCard').first();await card.waitFor({state:'visible'});
    await card.locator('[data-planedit]').click();
    const modal=page.locator('#editorModal');await modal.waitFor({state:'visible'});
    const box=page.locator('#kgg015ProgressionBox');await box.waitFor({state:'visible'});
    assert(await page.locator('.editorMediaBox').evaluate(node=>node.compareDocumentPosition(document.querySelector('.kgg015ProgressionBox'))&Node.DOCUMENT_POSITION_FOLLOWING),'progression editor is not directly below the image section');
    assert(await page.locator('.editorAdvanced').evaluate(node=>document.querySelector('#kgg015ProgressionBox').compareDocumentPosition(node)&Node.DOCUMENT_POSITION_FOLLOWING),'progression editor is not before Mehr');
    await box.locator('summary').click();
    assert(await page.locator('.kgg015StageCard').count()===3,'admin gallery did not render all existing stages');
    assert(await page.locator('[data-kgg015-add-slot]').count()===2,'admin gallery did not render both empty plus slots');
    assert(await page.locator('.kgg015StageCard.is-main').count()===1,'admin gallery must expose exactly one main stage');
    assert(await page.locator('.kgg015StageHandle').count()===0,'progression cards must not show a separate drag handle');
    assert(await page.locator('.kgg015StageCard').first().evaluate(node=>node.getAttribute('draggable')==='true'),'progression card is not draggable');
    assert(await page.locator('.kgg015StageRemove').first().evaluate(node=>{const r=node.getBoundingClientRect();return r.width>=44&&r.height>=44}),'delete control is not finger-sized');
    assert(await page.locator('.kgg015StageCard').first().evaluate(node=>getComputedStyle(node).touchAction==='none'),'touch stage card must own pointer gestures');
    assert(await page.evaluate(()=>{const bridge=window.KGGProgressionEditorBridge||{};return typeof bridge.readMedia==='function'&&typeof window.KGGTicket015AdminEditor?.saveEditor==='function';}),'admin editor bridges for media and parent save are missing');
    await page.locator('[data-kgg015-add-slot="after"]').click();
    await page.locator('[data-kgg015-add-name]').fill('Squat');
    await page.locator('[data-kgg015-existing]').first().click();
    assert(await page.locator('.kgg015StageCard').count()===4,'existing catalog exercise was not attached as a stage');
    assert((await page.locator('.kgg015StageCard').last().innerText()).includes('Squat'),'attached catalog stage has the wrong name');
    await page.locator('#editName').fill('Basis mit Entwurf');
    await page.locator('.kgg015StageCard').filter({hasText:'Squat'}).click();
    assert(await page.locator('#editName').inputValue()==='Squat','opening a linked stage did not open its editor');
    await page.locator('#closeEditor').click();
    await page.locator('#planList [data-planedit]').click();
    assert(await page.locator('#editName').inputValue()==='Basis mit Entwurf','parent editor draft was not saved before opening a linked stage');
    assert(await page.evaluate(()=>{const row=(window.KGGProgressionEditorBridge.catalog()||[]).find(item=>item.name==='Basis mit Entwurf');return !!(row&&row.progressionMainId);}), 'selected main stage was not persisted to the exercise-bank projection');
    if(!await page.locator('#kgg015ProgressionBox details').evaluate(node=>node.open))await page.locator('#kgg015ProgressionBox summary').click();
    await page.locator('[data-kgg015-add-slot="before"]').click();
    await page.locator('[data-kgg015-add-name]').fill('Neue Therapievariante');
    await page.locator('[data-kgg015-new]').click();
    assert(await page.locator('.kgg015StageCard').count()===5,'new stage creation path did not add a stage');

    const holdCard=page.locator('.kgg015StageCard').filter({hasText:'Schwerer'}).first();await holdCard.scrollIntoViewIfNeeded();const holdBox=await holdCard.boundingBox();assert(holdBox,'hard stage is not measurable');
    await page.mouse.move(holdBox.x+holdBox.width/2,holdBox.y+holdBox.height/2);await page.mouse.down();await page.waitForFunction(()=>[...document.querySelectorAll('.kgg015StageCard')].some(node=>node.classList.contains('is-vibrating')||node.classList.contains('is-holding')),null,{timeout:2200});
    await page.waitForTimeout(300);await page.mouse.up();await page.waitForTimeout(80);
    assert(await page.locator('.kgg015StageCard.is-main').count()===1,'main-stage hold produced more than one main stage');
    assert(await page.locator('.kgg015StageCard.is-main').innerText().then(text=>text.includes('Schwerer')),'main-stage hold did not move the blue main border');

    const lastStage=page.locator('.kgg015StageCard').last(),firstStage=page.locator('.kgg015StageCard').first();await lastStage.dragTo(firstStage);await page.waitForTimeout(80);
    assert(await page.locator('.kgg015StageCard').count()===5,'drag sorting changed the stage count');
    const touchBefore=await page.locator('.kgg015StageCard').nth(1).getAttribute('data-kgg015-stage-id');
    await page.locator('.kgg015StageCard').nth(1).evaluate(async node=>{const r=node.getBoundingClientRect(),base={bubbles:true,clientX:r.left+r.width/2,clientY:r.top+r.height/2,pointerId:41,pointerType:'touch',button:0};node.dispatchEvent(new PointerEvent('pointerdown',base));await new Promise(resolve=>setTimeout(resolve,220));document.dispatchEvent(new PointerEvent('pointermove',{...base,clientX:r.left-160,clientY:base.clientY}));document.dispatchEvent(new PointerEvent('pointerup',{...base,clientX:r.left-160,clientY:base.clientY}));});
    await page.waitForTimeout(100);
    const touchAfter=await page.locator('.kgg015StageCard').first().getAttribute('data-kgg015-stage-id');
    assert(touchAfter===touchBefore,'touch long-press reorder did not move the stage card');
    const mediaBridge=await page.evaluate(async()=>{const keyBytes=crypto.getRandomValues(new Uint8Array(16)),iv=crypto.getRandomValues(new Uint8Array(12)),plain=new TextEncoder().encode('ticket-015-media');const key=await crypto.subtle.importKey('raw',keyBytes,{name:'AES-GCM'},false,['encrypt','decrypt']);const encrypted=await crypto.subtle.encrypt({name:'AES-GCM',iv},key,plain);const b64=bytes=>{let s='';for(const b of bytes)s+=String.fromCharCode(b);return btoa(s).replace(/\+/g,'-').replace(/\//g,'_').replace(/=+$/,'')};const db=await new Promise((resolve,reject)=>{const req=indexedDB.open('kgg_media_v1',1);req.onupgradeneeded=()=>{if(!req.result.objectStoreNames.contains('encryptedBlobs'))req.result.createObjectStore('encryptedBlobs',{keyPath:'id'});};req.onsuccess=()=>resolve(req.result);req.onerror=()=>reject(req.error)});await new Promise((resolve,reject)=>{const tx=db.transaction('encryptedBlobs','readwrite');tx.objectStore('encryptedBlobs').put({id:'ticket-015-bridge-media',blob:new Blob([encrypted],{type:'application/octet-stream'}),savedAt:new Date().toISOString()});tx.oncomplete=resolve;tx.onerror=()=>reject(tx.error)});const blob=await window.KGGProgressionEditorBridge.readMedia({id:'ticket-015-bridge-media',mime:'text/plain',crypto:{key:b64(keyBytes),iv:b64(iv)}});return blob instanceof Blob&&blob.size===plain.length;});
    assert(mediaBridge,'admin editor media bridge did not decrypt an IndexedDB upload');

    const swipeStage=page.locator('.kgg015StageCard').nth(1);await swipeStage.scrollIntoViewIfNeeded();const swipeBox=await swipeStage.boundingBox();assert(swipeBox,'stage for vertical delete is not measurable');
    await swipeStage.evaluate(node=>{const rect=node.getBoundingClientRect(),base={bubbles:true,clientX:rect.left+rect.width/2,clientY:rect.top+rect.height/2,pointerId:31,pointerType:'touch',button:0};node.dispatchEvent(new PointerEvent('pointerdown',base));document.dispatchEvent(new PointerEvent('pointermove',{...base,clientY:base.clientY-70}));document.dispatchEvent(new PointerEvent('pointerup',{...base,clientY:base.clientY-70}));});
    const dialog=page.locator('[data-kgg015-delete-dialog]');const swipeDebug=await page.evaluate(()=>({dialogHidden:document.querySelector('[data-kgg015-delete-dialog]')?.hidden,status:document.querySelector('[data-kgg015-status]')?.textContent,cards:[...document.querySelectorAll('.kgg015StageCard')].map(node=>({index:node.dataset.kgg015Index,classes:node.className}))}));assert((await dialog.evaluate(node=>node.hidden===false)),'vertical swipe did not open delete confirmation: '+JSON.stringify(swipeDebug));await dialog.locator('[data-kgg015-delete-cancel]').click();assert(await page.locator('.kgg015StageCard').count()===5,'cancelled deletion changed stage state');
    await page.locator('.kgg015StageCard.is-main [data-kgg015-remove]').click();await dialog.locator('[data-kgg015-delete-confirm]').click();await page.waitForTimeout(60);
    assert(await page.locator('.kgg015StageCard').count()===4,'confirmed deletion did not remove exactly one stage');assert(await page.locator('.kgg015StageCard.is-main').count()===1,'deleting the main stage did not select a replacement main stage');

    for(const width of [360,390,600,700,768,1024]){await page.setViewportSize({width,height:844});await page.waitForTimeout(40);const responsive=await page.evaluate(()=>({overflow:document.documentElement.scrollWidth>window.innerWidth+1,box:document.querySelector('#kgg015ProgressionBox')?.getBoundingClientRect().width||0}));assert(!responsive.overflow,'responsive editor overflow at '+width+'px');assert(responsive.box>0,'progression editor disappeared at '+width+'px');}

    await page.locator('#saveExercise').click();await page.locator('#editorModal').waitFor({state:'hidden'});await page.locator('#planList [data-planedit]').click();await page.locator('#kgg015ProgressionBox summary').click();await page.waitForTimeout(80);
    assert(await page.locator('.kgg015StageCard').count()===4,'saved progression stages did not survive editor reopen');assert(await page.locator('.kgg015StageCard.is-main').count()===1,'saved main stage did not survive editor reopen');assert(errors.length===0,'admin preview raised page errors: '+errors.join(' | '));
    console.log('Ticket 015 admin browser smoke: OK');
  }finally{await Promise.race([browser.close(),new Promise(resolve=>setTimeout(resolve,5000))]);await new Promise(resolve=>server.close(resolve))}
}
main().catch(error=>{console.error(error.stack||error);process.exitCode=1});
