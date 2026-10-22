"use strict";
// Real pointer/hit tests against synthetic plans. The unreleased station script is
// test support only: importing it must never require an Android product change.
const fs=require('fs'),path=require('path'),crypto=require('crypto');
const {pathToFileURL}=require('url'),{chromium}=require('playwright');
const ROOT=path.resolve(__dirname,'..'),HTML=path.join(ROOT,'kgg-update/index.html');
const output=path.join(process.env.KGG_SMOKE_SCREENSHOT_DIR||path.join(ROOT,'tmp/cockpit-reported'),'reported');
fs.mkdirSync(output,{recursive:true});
const only=process.argv[2],results=[];
const assert=(v,m)=>{if(!v)throw Error(m)};
async function swipe(page,context,x,y,dy){const c=await context.newCDPSession(page);await c.send('Input.dispatchTouchEvent',{type:'touchStart',touchPoints:[{x,y}]});for(let i=1;i<=16;i++){await c.send('Input.dispatchTouchEvent',{type:'touchMove',touchPoints:[{x,y:y+dy*i/16}]});await page.waitForTimeout(16)}await c.send('Input.dispatchTouchEvent',{type:'touchEnd',touchPoints:[]});await page.waitForTimeout(250);await c.detach()}
(async()=>{const browser=await chromium.launch({headless:true});try{
 for(const [width,height,count] of [[1280,800,1],[1280,800,2],[1280,800,3],[820,1180,2],[1024,640,1],[390,857,1]]){
  const context=await browser.newContext({viewport:{width,height},screen:{width,height},isMobile:true,hasTouch:true,locale:'de-DE'});
  const page=await context.newPage();page.setDefaultTimeout(6000);await context.route(/^https?:/,r=>r.abort());
  await page.addInitScript(()=>{localStorage.setItem('kgg_pwa_install_prompt_seen_v1','synthetic');const ex=(id,name)=>({id,name,sets:3,side:'BI',loadUnit:'kg',weightUnit:'kg',metricUnit:'Wdh',unit:'Wdh',media:[]});localStorage.setItem('kgg_html_app_v2_state',JSON.stringify({planId:'synthetic-main',patient:{name:'Synthetic'},plan:[ex('a','Kniebeuger Maschine'),ex('b','Hip Thrust')]}))});
  await page.goto(pathToFileURL(HTML).href);await page.locator('#closeAdminSecrets').tap();
  await page.evaluate(count=>{const a=KGGTherapyCockpit;for(let i=0;i<count;i++)a.importCode(a.encode({planId:'synthetic-'+i,name:'Synthetic '+i,exercises:a.registry.entries().slice(0,12).map(e=>({id:e.id,sets:8,previous:Array.from({length:8},()=>['20','10'])}))}))},count);
  // Existing entry gesture guard intentionally ignores Add for 450ms after opening.
  await page.waitForTimeout(600);
  const card=page.locator('.kgg-tc-card[data-tc-card="0"]');
  async function test(name,fn){if(only&&name!==only)return;try{await fn();results.push({width,height,count,name,status:'PASS'})}catch(e){results.push({width,height,count,name,status:'FAIL',error:e.message});await page.screenshot({path:path.join(output,`${width}-${count}-${name}.png`)})}finally{await page.keyboard.press('Escape');if(await page.locator('#kggTceAddModal').isVisible())await page.locator('#kggTceAddModal [data-tce-close]').tap();}}
  await test('scroll',async()=>{
   await card.locator('.kgg-tc-card-toggle').first().tap();
   const scroll=card.locator('.kgg-tc-scroll'),before=await page.evaluate(()=>KGGTherapyCockpit.getSlot(0).exercises.map(e=>e.id));
   const box=await scroll.boundingBox();await swipe(page,context,box.x+box.width*.7,box.y+box.height*.8,-Math.min(250,box.height*.6));
   assert(await scroll.evaluate(e=>e.scrollTop)>20,'touch did not scroll expanded plan');
   if(count>1)assert(await page.locator('.kgg-tc-card[data-tc-card="1"] .kgg-tc-scroll').evaluate(e=>e.scrollTop)===0,'neighbour scrolled');
   assert(JSON.stringify(before)===JSON.stringify(await page.evaluate(()=>KGGTherapyCockpit.getSlot(0).exercises.map(e=>e.id))),'scroll reordered exercises');
   await card.locator('.kgg-tce-add-card').scrollIntoViewIfNeeded();assert(await card.locator('.kgg-tce-add-card').isVisible(),'last action unreachable');
   const pos=await scroll.evaluate(e=>e.scrollTop);await page.waitForTimeout(400);await page.locator('.kgg-tce-add-card').first().click();await page.locator('#kggTceAddModal').waitFor({state:'visible'});await page.locator('#kggTceAddModal [data-tce-close]').click();
   assert(Math.abs(await scroll.evaluate(e=>e.scrollTop)-pos)<3,'closing dialog reset scroll');
  });
  await test('modal',async()=>{
   await card.locator('.kgg-tce-add-card').tap();
   await page.locator('#kggTceAddModal').waitFor({state:'visible'});
   assert(!await page.locator('#kggTherapyCockpitButton').isVisible(),'seam handle above modal');
   await page.keyboard.press('Tab');assert(await page.evaluate(()=>!!document.activeElement.closest('#kggTceAddModal')),'focus left dialog');
   await page.keyboard.press('Escape');assert(!await page.locator('#kggTceAddModal').isVisible(),'Escape did not close');
  });
  await test('layout',async()=>{if(count!==1||width<1100)return;
   const r=await page.evaluate(()=>{const n=document.querySelector('#planList .planName'),p=n.closest('.planCard');return {name:n.getBoundingClientRect().width,height:n.getBoundingClientRect().height,line:parseFloat(getComputedStyle(n).lineHeight),plan:p.getBoundingClientRect().width,edit:p.querySelector('[data-planedit]').getBoundingClientRect().x,text:n.getBoundingClientRect().x}});
   assert(r.name>=160&&r.height<=r.line*2+2,'normal plan name cramped '+JSON.stringify(r));assert(r.edit<r.text,'settings are not left of name');
  });
  await test('pad',async()=>{
   await card.locator('.kgg-tc-card-toggle').first().tap();if(!await card.locator('.kgg-tc-field').count())await card.locator('.kgg-tc-card-toggle').first().tap();
   await card.locator('.kgg-tc-field').first().tap();
   const ok=page.locator('.kgg-tc-pad [data-tc-key="OK"]');await ok.tap();
   await card.locator('.kgg-tc-field').first().tap();
   // v120 places/reveals the newly rendered pad in requestAnimationFrame.
   // Await the actual hit-test contract; do not assert before that render task.
   const okReady=()=>{const key=document.querySelector('.kgg-tc-pad [data-tc-key="OK"]');if(!key)return false;const r=key.getBoundingClientRect(),hit=document.elementFromPoint(r.x+r.width/2,r.y+r.height/2);return r.width>0&&r.height>0&&r.bottom<=innerHeight&&!!hit&&key.contains(hit)};
   await page.waitForFunction(okReady,null,{timeout:5000}).catch(async error=>{console.error('Keypad readiness diagnostics',JSON.stringify(await page.evaluate(()=>{const key=document.querySelector('.kgg-tc-pad [data-tc-key="OK"]'),r=key?.getBoundingClientRect(),hit=r&&document.elementFromPoint(r.x+r.width/2,r.y+r.height/2);return {viewport:{width:innerWidth,height:innerHeight},rect:r?.toJSON(),hitClass:String(hit?.className||''),hitAction:hit?.getAttribute('data-tc-action'),padClass:key?.closest('.kgg-tc-pad')?.className}}).catch(()=>null)));throw error;});
   assert(await page.evaluate(okReady),'OK key covered');
   await page.locator('.kgg-tc-pad [data-tc-key="C"]').tap();await page.locator('.kgg-tc-pad [data-tc-key="7"]').tap();await card.locator('.kgg-tc-field[data-tc-field="metric"]').first().tap();
   assert(await page.evaluate(()=>KGGTherapyCockpit.getSlot(0).exercises[0].today[0][0])==='7','field switch lost value');await page.locator('.kgg-tc-header .kgg-tc-title').tap();
  });
  await test('previous',async()=>{
   const toggle=card.locator('.kgg-tc-card-toggle').first();await toggle.tap();if(!await card.locator('.kgg-tc-field').count())await toggle.tap();
   await card.locator('[data-tc-action="use-previous"]').first().tap();
   assert(JSON.stringify(await page.evaluate(()=>KGGTherapyCockpit.getSlot(0).exercises[0].today[0]))==='["20","10"]','previous pair not copied');
  });
  await test('media',async()=>{
   await page.route('https://synthetic.invalid/image.png',r=>r.fulfill({contentType:'image/png',body:Buffer.from('iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMCAO+jRZkAAAAASUVORK5CYII=','base64')}));
   await page.evaluate(()=>{const s=KGGTherapyCockpit.getSlot(0);s.exercises[0].media=[{id:'synthetic-image',type:'image',mimeType:'image/png',downloadUrl:'https://synthetic.invalid/image.png'}];KGGTherapyCockpit.updateSlot(0,s);});
   await page.waitForFunction(()=>document.querySelector('.kgg-tc-card[data-tc-card="0"] .kgg-tc-thumb img')?.naturalWidth>0);
   // Exercise the existing encrypted local media bridge with actual AES-GCM and IndexedDB.
   // Do not return the asynchronous fixture Promise across the DevTools boundary.
   // Start it once; await its real terminal state using the existing 6000ms default.
   let mediaFixtureFailure=null;
   try {
    await page.evaluate(()=>{
     if(Object.prototype.hasOwnProperty.call(globalThis,'__kggSyntheticMediaFixture'))throw Error('Overlapping synthetic media fixture');
     const state={status:'pending',error:null};globalThis.__kggSyntheticMediaFixture=state;
     state.task=(async()=>{
    const bytes=Uint8Array.from(atob('iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMCAO+jRZkAAAAASUVORK5CYII='),c=>c.charCodeAt(0));
    const key=await crypto.subtle.generateKey({name:'AES-GCM',length:256},true,['encrypt','decrypt']),iv=crypto.getRandomValues(new Uint8Array(12));
    const raw=new Uint8Array(await crypto.subtle.exportKey('raw',key)),enc=await crypto.subtle.encrypt({name:'AES-GCM',iv},key,bytes),b64=a=>btoa(String.fromCharCode(...a)).replace(/\+/g,'-').replace(/\//g,'_').replace(/=+$/,'');
    const media={id:'synthetic-local',type:'image',mime:'image/png',mimeType:'image/png',crypto:{key:b64(raw),iv:b64(iv)}};
    const db=await new Promise((resolve,reject)=>{const req=indexedDB.open('kgg_media_v1',1);req.onupgradeneeded=()=>req.result.createObjectStore('encryptedBlobs',{keyPath:'id'});req.onsuccess=()=>resolve(req.result);req.onerror=()=>reject(req.error)});
    await new Promise((resolve,reject)=>{const tx=db.transaction('encryptedBlobs','readwrite');tx.objectStore('encryptedBlobs').put({id:media.id,blob:new Blob([enc])});tx.oncomplete=resolve;tx.onerror=()=>reject(tx.error)});db.close();
    const current=KGGDataStore.getCurrentPlan();current.exercises[0].media=[media];KGGDataStore.setCurrentPlan(current,'synthetic-media-test');
    const slot=KGGTherapyCockpit.getSlot(0);slot.exercises[0].media=[media];KGGTherapyCockpit.updateSlot(0,slot);
     })().then(()=>{state.status='done'},error=>{
       state.error={name:error?.name||'Error',message:error?.message||String(error),stack:error?.stack||''};state.status='failed';
     });
    });
    await page.waitForFunction(()=>['done','failed'].includes(globalThis.__kggSyntheticMediaFixture?.status));
    const completion=await page.evaluate(()=>{const s=globalThis.__kggSyntheticMediaFixture;return{status:s?.status,error:s?.error}});
    if(completion.status==='failed'){
      const error=new Error(completion.error.message);error.name=completion.error.name;error.stack=completion.error.stack||error.stack;throw error;
    }
    assert(completion.status==='done','encrypted media fixture did not complete');
   } catch(error) {mediaFixtureFailure=error;throw error;}
   finally {
    try {
     const released=await page.evaluate(()=>{delete globalThis.__kggSyntheticMediaFixture;return !Object.prototype.hasOwnProperty.call(globalThis,'__kggSyntheticMediaFixture')});
     assert(released,'synthetic media fixture reference not released');
    } catch(cleanupError) {if(!mediaFixtureFailure)throw cleanupError;}
   }
   await page.waitForFunction(()=>document.querySelector('.kgg-tc-card[data-tc-card="0"] .kgg-tc-thumb img')?.src.startsWith('blob:')&&document.querySelector('.kgg-tc-card[data-tc-card="0"] .kgg-tc-thumb img').naturalWidth>0);
   await page.evaluate(()=>{const s=KGGTherapyCockpit.getSlot(0);s.exercises[0].media=[{id:'synthetic-missing',type:'image',downloadUrl:'https://synthetic.invalid/missing.png'}];KGGTherapyCockpit.updateSlot(0,s);});
   await page.waitForFunction(()=>document.querySelector('.kgg-tc-card[data-tc-card="0"] .kgg-tc-thumb')?.dataset.mediaState==='missing');
   assert(!await card.locator('.kgg-tc-exercise').first().locator('.kgg-tc-thumb img').count(),'broken image rendered');
  });
  await test('wrapper',async()=>{
   await page.evaluate(()=>window.KGGDeviceTestStation={});await page.addScriptTag({path:path.join(ROOT,'android-wrapper/app/src/preview/assets/android/kgg_dual_device_fixtures.js')});await page.addScriptTag({path:path.join(__dirname,'fixtures/cockpit-v123/kgg_device_test_station.js')});
   assert(!await page.locator('#kgg-device-test-station h2').isVisible(),'station not collapsed');
   await card.locator('.kgg-tce-add-card').tap();assert(!await page.locator('#kgg-device-test-station').isVisible(),'station covers dialog');await page.keyboard.press('Escape');
  });
  await context.close();
 }
}finally{await browser.close()}const report={sha256:crypto.createHash('sha256').update(fs.readFileSync(HTML)).digest('hex'),results};fs.writeFileSync(path.join(output,'report.json'),JSON.stringify(report,null,2));console.log(JSON.stringify(report,null,2));if(results.some(r=>r.status!=='PASS'))process.exitCode=1})().catch(e=>{console.error(e.stack);process.exitCode=1});
