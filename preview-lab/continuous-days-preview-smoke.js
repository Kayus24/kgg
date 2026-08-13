#!/usr/bin/env node
'use strict';
const fs=require('fs');
const http=require('http');
const path=require('path');
const {chromium}=require('playwright');
const ROOT=path.resolve(process.argv[2]||'');
function assert(ok,msg){if(!ok)throw new Error(msg)}
function type(file){return{'.html':'text/html; charset=utf-8','.js':'text/javascript; charset=utf-8','.json':'application/json; charset=utf-8','.webmanifest':'application/manifest+json; charset=utf-8','.png':'image/png'}[path.extname(file).toLowerCase()]||'application/octet-stream'}
function resolveFile(url){const rel=decodeURIComponent(String(url||'/').split('?')[0]).replace(/^\/+/, '')||'index.html',file=path.resolve(ROOT,rel);if((!file.startsWith(ROOT+path.sep)&&file!==ROOT)||!fs.existsSync(file)||!fs.statSync(file).isFile())return null;return file}
function decodePayload(raw){return JSON.parse(Buffer.from(String(raw||'').replace(/^KGGD1:/,''),'base64url').toString('utf8'))}
async function boot(page){
  await page.locator('#plan').waitFor({state:'visible',timeout:10000});
  await page.evaluate(()=>Promise.race([navigator.serviceWorker.ready,new Promise((_,reject)=>setTimeout(()=>reject(new Error('SW ready timeout')),12000))]));
  await page.reload({waitUntil:'domcontentloaded'});
  await page.locator('#plan').waitFor({state:'visible',timeout:10000});
  await page.locator('#kggCurrentDayBox').waitFor({state:'visible',timeout:10000});
}
async function day(page,n){
  try{
    await page.waitForFunction(n=>Number(d)===n&&document.querySelector('#kggCurrentDayBox .kggCurrentDayBig')?.textContent.trim()===`Tag ${n}`,n,{timeout:10000});
  }catch(error){
    const diagnostic=await page.evaluate(()=>({
      href:location.href,
      runtimeDay:typeof d!=='undefined'?Number(d):null,
      done:typeof done!=='undefined'&&Array.isArray(done)?done.slice():null,
      next:typeof next==='function'?next():null,
      hub:document.querySelector('#kggCurrentDayBox .kggCurrentDayBig')?.textContent||'',
      status:document.getElementById('status')?.textContent||'',
      planId:typeof p!=='undefined'&&p?p.id||'':'',
      planDays:typeof p!=='undefined'&&p?p.days||null:null,
      continuous:typeof p!=='undefined'&&p?p.extendDays!==false:null,
      metaKey:typeof mk==='function'?mk():'',
      meta:typeof mk==='function'?localStorage.getItem(mk()):null,
      doneKey:typeof dk==='function'?dk():'',
      storedDone:typeof dk==='function'?localStorage.getItem(dk()):null,
      currentPlan:localStorage.getItem('kggCurrentPlanV1'),
      multi:localStorage.getItem('kggPatientMultiPlansV1'),
    }));
    throw new Error(`expected T${n}; preview day diagnostic=${JSON.stringify(diagnostic)}; cause=${error.message}`);
  }
}
async function menu(page,base){await page.goto(base+'continuous-days-test.html',{waitUntil:'domcontentloaded'});await page.locator('#scenario-t7').waitFor({state:'visible'})}
async function clickScenario(page,id){await page.locator(id).click();await page.waitForLoadState('domcontentloaded');await boot(page)}
async function finish(page,qrDay,nextDay){await page.locator('#plan > button.btn').click();await page.locator('#end').waitFor({state:'visible'});const payload=decodePayload(await page.locator('#qr').getAttribute('data-payload'));assert(Number(payload.d)===qrDay,`QR expected T${qrDay}, got ${payload.d}`);assert(payload.final===true,'final QR flag missing');assert(await page.evaluate(()=>Number(d))===nextDay,`expected prepared T${nextDay}`)}
async function main(){
  assert(ROOT&&fs.existsSync(path.join(ROOT,'index.html')),'preview root missing index.html');
  assert(fs.existsSync(path.join(ROOT,'continuous-days-test.html')),'preview test page missing');
  const provenance=JSON.parse(fs.readFileSync(path.join(ROOT,'preview-provenance.json'),'utf8'));
  assert(provenance.sourceCommit==='cb69bc6b6fbe9a544db26bede50a71365a9492ed','preview provenance does not match accepted runtime');
  const server=http.createServer((req,res)=>{const file=resolveFile(req.url);if(!file){res.writeHead(404);res.end('not found');return}res.writeHead(200,{'Content-Type':type(file),'Cache-Control':'no-store','Service-Worker-Allowed':'/'});fs.createReadStream(file).pipe(res)});
  await new Promise(r=>server.listen(0,'127.0.0.1',r));const base=`http://127.0.0.1:${server.address().port}/`;
  const browser=await chromium.launch({headless:true});const context=await browser.newContext({viewport:{width:390,height:844},serviceWorkers:'allow'});const page=await context.newPage();page.setDefaultTimeout(10000);const errors=[];page.on('pageerror',e=>errors.push(e.message));
  try{
    console.log('[preview-days] T7 -> T8');await menu(page,base);await clickScenario(page,'#scenario-t7');await day(page,7);await finish(page,7,8);await page.locator('#end .btn2').filter({hasText:'Zurück zum Plan'}).click();await page.locator('#end').waitFor({state:'hidden'});await day(page,8);
    console.log('[preview-days] T12 -> T13 -> T14');await menu(page,base);await clickScenario(page,'#scenario-t12');await day(page,13);await finish(page,13,14);
    console.log('[preview-days] T99 -> T100 + paging');await menu(page,base);await clickScenario(page,'#scenario-t99');await day(page,100);assert(await page.locator('#days button').count()===12,'preview T100 grew hidden core day buttons');await page.locator('#kggHistoryToggle').click();await page.locator('#kggHistoryList').waitFor({state:'visible'});assert(await page.locator('#kggHistoryList .kggDayCard[data-day]').count()===30,'preview history initial page is not 30');await page.locator('#kggHistoryMore').click();assert(await page.locator('#kggHistoryList .kggDayCard[data-day]').count()===60,'preview history +30 failed');
    console.log('[preview-days] multi-plan T28 / T5');await menu(page,base);await clickScenario(page,'#scenario-multi');await day(page,28);await page.evaluate(()=>window.KGGPatientMultiPlan.switchTo(1));await day(page,5);await page.evaluate(()=>window.KGGPatientMultiPlan.switchTo(0));await day(page,28);
    console.log('[preview-days] fixed T12 stays T12');await menu(page,base);await clickScenario(page,'#scenario-fixed');await day(page,12);await finish(page,12,12);
    assert(errors.length===0,'preview page errors: '+errors.join(' | '));
    console.log(JSON.stringify({status:'PASS',sourceCommit:provenance.sourceCommit,t7ToT8:true,t12ToT13:true,t99ToT100:true,multiPlan:true,fixedPlan:true}));
  }finally{await context.close();await browser.close();if(server.closeAllConnections)server.closeAllConnections();await new Promise(r=>server.close(r))}
}
main().catch(e=>{console.error('KGG continuous-day preview smoke FAIL: '+(e.stack||e.message));process.exitCode=1});
