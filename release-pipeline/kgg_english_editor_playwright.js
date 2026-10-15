#!/usr/bin/env node
'use strict';
const fs=require('fs'),http=require('http'),path=require('path'),assert=require('assert/strict'),{chromium}=require('playwright'),crypto=require('crypto');
const key=Buffer.alloc(32,7),iv=Buffer.alloc(12,3),cipher=crypto.createCipheriv('aes-256-gcm',key,iv),encrypted=Buffer.concat([cipher.update('<svg xmlns="http://www.w3.org/2000/svg" width="120" height="80"><rect width="120" height="80" fill="#2563eb"/></svg>'),cipher.final(),cipher.getAuthTag()]);
const fixtureMedia={id:'english-editor-media',type:'image',mime:'image/svg+xml',name:'Synthetic SVG',crypto:{key:key.toString('base64url'),iv:iv.toString('base64url')},encrypted:true};
const ROOT=path.resolve(__dirname,'..'),canonical='Eigene Testübung',english='My test exercise';
async function main(){
 let mediaBundle=null;const server=http.createServer((req,res)=>{if(req.url==='/synthetic-image'){res.setHeader('Content-Type','application/octet-stream');return res.end(encrypted)}if(req.url==='/synthetic-media'){if(req.method==='POST'){const parts=[];req.on('data',part=>parts.push(part));req.on('end',()=>{mediaBundle=Buffer.concat(parts);res.end('OK')});return}res.setHeader('Content-Type','application/octet-stream');return res.end(mediaBundle||Buffer.alloc(0))}const rel=new URL(req.url,'http://local').pathname.replace(/^\/+/, '')||'index.html',f=path.resolve(ROOT,rel);if(!f.startsWith(ROOT+path.sep)||!fs.existsSync(f)){res.statusCode=404;return res.end()}res.setHeader('Content-Type',f.endsWith('.html')?'text/html; charset=utf-8':f.endsWith('.js')?'text/javascript; charset=utf-8':f.endsWith('.css')?'text/css':'application/octet-stream');res.setHeader('Cache-Control','no-store');res.end(fs.readFileSync(f))});
 await new Promise(r=>server.listen(0,'127.0.0.1',r));const base='http://127.0.0.1:'+server.address().port,browser=await chromium.launch({headless:true});
 const ctx=await browser.newContext({viewport:{width:1280,height:900},serviceWorkers:'block'}),page=await ctx.newPage(),errors=[];page.on('requestfailed',r=>{if(!errors.length)console.log('Synthetic request failed '+r.url()+' '+r.failure()?.errorText)});page.on('pageerror',e=>{if(!errors.length)console.error('First fixture page error: '+e.stack);errors.push(e.message)});
 async function openBankEditor(){if(!await page.locator('#bankContent [data-edit="synthetic-custom"]').isVisible())await page.locator('#bankToggle').click();await page.locator('#bankContent [data-edit="synthetic-custom"]').click()}
 try{
  const shareBase='https://patient-preview.example/kgg/';fixtureMedia.downloadUrl=base+'/synthetic-image';fixtureMedia.status='ready';
  await page.addInitScript(({shareBase,canonical,base,fixtureMedia})=>{window.KGG_PATIENT_BASE_URL=shareBase;window.KGGMediaUploadAdapter={upload:async blob=>{await fetch(base+'/synthetic-media',{method:'POST',body:blob});return {id:'synthetic-media-bundle',downloadUrl:base+'/synthetic-media'}}};localStorage.kggInstallAsked='1';if(!localStorage.getItem('kgg_html_app_v2_custom_exercise_bank'))localStorage.setItem('kgg_html_app_v2_custom_exercise_bank',JSON.stringify([{id:'synthetic-custom',name:canonical,aliases:canonical,sets:1,unit:'Wdh',weightUnit:'kg',media:[fixtureMedia],custom:true},{id:'synthetic-linked',name:'Verknüpfte Stufe',nameEn:'Linked English stage',sets:1,unit:'Wdh',weightUnit:'kg',media:[fixtureMedia],custom:true}]))},{shareBase,canonical,base,fixtureMedia});
  await page.goto(base+'/kgg-update/index.html',{waitUntil:'domcontentloaded'});await page.waitForFunction(()=>window.KGGSharedExerciseEditor&&window.KGGSharedBank);await page.waitForTimeout(1500);if(await page.locator('#adminSecretsModal.open').isVisible())await page.locator('#closeAdminSecrets').click();
  await page.evaluate(async data=>{const db=await new Promise((resolve,reject)=>{const req=indexedDB.open('kgg_media_v1',1);req.onupgradeneeded=()=>{if(!req.result.objectStoreNames.contains('encryptedBlobs'))req.result.createObjectStore('encryptedBlobs',{keyPath:'id'})};req.onsuccess=()=>resolve(req.result);req.onerror=()=>reject(req.error)});await new Promise((resolve,reject)=>{const tx=db.transaction('encryptedBlobs','readwrite');tx.objectStore('encryptedBlobs').put({id:'english-editor-media',blob:new Blob([Uint8Array.from(atob(data),c=>c.charCodeAt(0))],{type:'application/octet-stream'})});tx.oncomplete=resolve;tx.onerror=()=>reject(tx.error)})},encrypted.toString('base64'));
  // Real bank gear button, fields and Save interactions; media transport remains local synthetic.

  await openBankEditor();
  await page.locator('#editNameEn').fill(english);await page.locator('#kgg015ProgressionBox summary').click();
  await page.locator('[data-kgg015-add-slot="after"]').click();await page.locator('#kgg015AddName').fill('Basis');await page.locator('[data-kgg015-new]').click();
  await page.locator('[data-kgg015-name-en="1"]').fill('My authored stage');
  await page.locator('[data-kgg015-add-slot="after"]').click();await page.locator('#kgg015AddName').fill('Verknüpfte');await page.locator('[data-kgg015-existing="synthetic-linked"]').click();
  assert.equal(await page.locator('[data-kgg015-name-en="2"]').inputValue(),'Linked English stage','linked bank EN not carried to active variant draft');
  await page.locator('#saveExercise').click();
  const stored=()=>page.evaluate(name=>JSON.parse(localStorage.getItem('kgg_html_app_v2_custom_exercise_bank')).find(ex=>ex.name===name),canonical);
  assert.equal((await stored()).nameEn,english,'editor save did not persist EN bank field');assert.equal((await stored()).name,canonical,'editor changed canonical name');
  await page.reload();await page.waitForFunction(()=>window.KGGSharedExerciseEditor&&window.KGGSharedBank);await page.waitForTimeout(1500);if(await page.locator('#adminSecretsModal.open').isVisible())await page.locator('#closeAdminSecrets').click();
  await openBankEditor();
  assert.equal(await page.locator('#editNameEn').inputValue(),english,'editor reload lost authored English');
  await page.locator('#kgg015ProgressionBox summary').click();assert.equal(await page.locator('[data-kgg015-name-en="1"]').inputValue(),'My authored stage');
  await page.locator('[data-kgg015-name-en="1"]').fill('');await page.locator('#saveExercise').click();
  assert.equal((await stored()).progressionVariants[1].nameEn,'','variant clear did not persist');
  await page.reload();await page.waitForFunction(()=>window.KGGSharedExerciseEditor);await page.waitForTimeout(1500);if(await page.locator('#adminSecretsModal.open').isVisible())await page.locator('#closeAdminSecrets').click();
  await openBankEditor();if(await page.locator('#kgg015ProgressionBox details').getAttribute('open')===null)await page.locator('#kgg015ProgressionBox summary').click();
  assert.equal(await page.locator('[data-kgg015-name-en="1"]').inputValue(),'','variant clear lost on reload');await page.locator('[data-kgg015-name-en="1"]').fill('My authored stage');await page.locator('#saveExercise').click();
  assert.equal((await stored()).progressionVariants[1].name,'Basis');assert.equal((await stored()).progressionVariants[1].nameEn,'My authored stage','variant editor save/reload lost EN field');
  if(!await page.locator('[data-add="synthetic-custom"]').isVisible())await page.locator('#bankToggle').click();await page.locator('[data-add="synthetic-custom"]').first().click();await page.waitForFunction(name=>window.KGGDataStore?.getCurrentPlan().exercises.some(ex=>ex.name===name),canonical);
  const exercise=await page.evaluate(()=>KGGDataStore.getCurrentPlan().exercises[0]);assert.equal(exercise.nameEn,english,'bank-to-plan path lost authored English');
  if(await page.locator('#adminSecretsModal.open').isVisible())await page.locator('#closeAdminSecrets').click();
  await page.evaluate(base=>{window.KGGMediaUploadAdapter={upload:async blob=>{await fetch(base+'/synthetic-media',{method:'POST',body:blob});return {id:'synthetic-media-bundle',downloadUrl:base+'/synthetic-media'}}}},base);
  await page.locator('#finishBtn').click();await page.locator('#finishPatientBtn').click();await page.waitForFunction(()=>document.getElementById('patientAppLink')?.href.includes('plan='));
  const url=await page.locator('#patientAppLink').getAttribute('href');assert.ok(url.startsWith(shareBase),'patient builder did not use reserved synthetic share host');
  const decoded=await page.evaluate(url=>KGGPlanFormat.decodePlanText(url).raw,url);assert.equal(decoded.m.exerciseNamesEn[canonical],english);assert.equal(decoded.m.exerciseNamesEn.Basis,'My authored stage');assert.equal(decoded.e[0][0],canonical);assert.equal(decoded.e[0][11].v[1].n,'Basis','variant tuple changed to English');
  // The existing builder requires a shareable HTTPS URL. Replay its exact payload locally.
  await page.goto(base+'/'+new URL(url).search,{waitUntil:'domcontentloaded'});await page.waitForFunction(()=>document.querySelector('#list .ex h3'));await page.waitForTimeout(1300);await page.locator('#kggLangSwitch').click();
  assert.ok((await page.locator('#list .ex h3').allTextContents()).every(name=>name===english),'patient display did not use authored English metadata');
  await page.locator('#list .ex').first().locator('h3').click();await page.locator('#list .ex').first().locator('[data-kgg015-main-next]').click();await page.waitForTimeout(150);
  assert.ok((await page.locator('.kgg015MainProgressionStage').first().textContent()).includes('My authored stage'),'real stage selection did not use authored EN');
  await page.locator('#list .ex').first().locator('.kggCompactTapProxy').first().click();await page.locator('#pad .padGrid button').filter({hasText:/^2$/}).click();await page.locator('#pad .padOk').click();await page.waitForTimeout(150);
  assert.equal(await page.locator('#list .ex h3').first().textContent(),'My authored stage','committed stage display did not use authored EN');
  await page.getByRole('button',{name:'Show current values as QR',exact:true}).click();const qr=await page.locator('#qr').getAttribute('data-payload');const returned=JSON.parse(Buffer.from(qr.slice(6),'base64url').toString());assert.equal(returned.e[0][0],canonical,'authored English leaked into canonical return QR');assert.equal(returned.e[0][7].s[0].n,'Basis');assert.equal(returned.e[0][7].s[0].i,decoded.e[0][11].v[1].i);assert.ok((await page.locator('#sum').textContent()).includes('My authored stage'),'summary did not use authored stage EN');
  assert.equal(errors.length,0,'browser errors: '+errors.slice(0,5).join(' | '));console.log('English editor Playwright: PASS (editor Save→bank Reload→plan→KGGH3 link→English display→German return QR)');
 }finally{await ctx.close();await browser.close();await new Promise(r=>server.close(r))}
}
main().catch(e=>{console.error('English editor Playwright FAIL: '+(e.stack||e.message));process.exitCode=1});
