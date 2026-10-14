#!/usr/bin/env node
'use strict';
const fs=require('fs');
const http=require('http');
const path=require('path');
const {execFileSync}=require('node:child_process');
const {chromium,webkit}=require('playwright');
const ENGINE=process.env.KGG_DAYS_BROWSER||'chromium';
const MODE=process.env.KGG_DAYS_MODE||'legacy';
if(!['chromium','webkit'].includes(ENGINE)||!['legacy','react'].includes(MODE))throw new Error('Unsupported browser/mode');

const ROOT=path.resolve(__dirname,'..');
function assert(condition,message){if(!condition)throw new Error(message)}
function encodePlan(plan){return Buffer.from(JSON.stringify(plan),'utf8').toString('base64url')}
function decodePayload(payload){const raw=String(payload||'').replace(/^KGGD1:/,'');return JSON.parse(Buffer.from(raw,'base64url').toString('utf8'))}
function contentType(filename){return{'.html':'text/html; charset=utf-8','.js':'text/javascript; charset=utf-8','.json':'application/json; charset=utf-8','.webmanifest':'application/manifest+json; charset=utf-8','.png':'image/png'}[path.extname(filename).toLowerCase()]||'application/octet-stream'}
function safeFile(urlPath){const pathname=decodeURIComponent(String(urlPath||'/').split('?')[0]).replace(/^\/+/,''),relative=pathname.replace(/^kgg\/?/,'')||'index.html',target=path.resolve(ROOT,relative);if((!target.startsWith(`${ROOT}${path.sep}`)&&target!==ROOT)||!fs.existsSync(target)||!fs.statSync(target).isFile())return null;return target}
async function waitForRuntime(page){
  await page.evaluate(()=>navigator.serviceWorker.ready);
  if(!(await page.evaluate(()=>Boolean(navigator.serviceWorker.controller))))await page.reload({waitUntil:'domcontentloaded'});
  await page.waitForFunction(()=>Boolean(navigator.serviceWorker.controller),null,{timeout:12000});
  for(let attempt=0;attempt<5;attempt+=1){
    await page.locator('#plan').waitFor({state:'visible'});
    if(await page.locator('#kggCurrentDayBox').count())return;
    await page.reload({waitUntil:'domcontentloaded'});
  }
  throw new Error('continuous-day runtime/day hub was not injected');
}
async function seedCurrent(page,doneDays,lastOpenDay){
  await page.evaluate(({doneDays,lastOpenDay})=>{
    done=Array.from(doneDays||[],Number);
    d=Number(lastOpenDay)||1;
    save();
  },{doneDays,lastOpenDay});
  await page.reload({waitUntil:'domcontentloaded'});
  await waitForRuntime(page);
}
async function currentDay(page){return page.evaluate(()=>Number(d))}
async function assertHubDay(page,day){await page.waitForFunction(day=>document.querySelector('#kggCurrentDayBox .kggCurrentDayBig')?.textContent.trim()===`Tag ${day}`,day,{timeout:8000});assert(await currentDay(page)===day,`runtime day is not T${day}`)}
async function waitForVisibleDayButtons(page,count){await page.waitForFunction(expected=>document.querySelectorAll('#days button').length===expected,count,{timeout:8000});assert(await page.locator('#days button').count()===count,`day-button DOM did not settle at ${count}`)}
async function dismissInstallOverlay(page){
  const box=page.locator('#installBox');
  if(await box.count()&&await box.isVisible().catch(()=>false)){
    const dismiss=box.getByRole('button',{name:/Nein danke|No thanks/i});
    assert((await dismiss.count())===1&&await dismiss.isVisible(),'Install guide is blocking and has no usable dismiss action');
    await dismiss.click();
  }
}
async function confirmTicket034FinishIfShown(page){const modal=page.locator('#kggTicket034FinishModal');if(!(await modal.count())||!(await modal.isVisible().catch(()=>false)))return;const confirm=modal.getByRole('button',{name:'Training beenden',exact:true});assert(await confirm.count()===1,'Ticket-034 finish modal did not expose exactly one confirm button');await confirm.click();await modal.waitFor({state:'hidden'})}
async function finishFromUi(page,expectedQrDay,expectedNextDay){
  await dismissInstallOverlay(page);
  await page.locator('#plan > button.btn').click();
  await confirmTicket034FinishIfShown(page);
  await page.locator('#end').waitFor({state:'visible'});
  assert((await page.locator('#endTitle').innerText())===`Training T${expectedQrDay} beendet`,`end title is not T${expectedQrDay}`);
  const decoded=decodePayload(await page.locator('#qr').getAttribute('data-payload'));
  assert(Number(decoded.d)===expectedQrDay,`QR day changed before export: ${JSON.stringify(decoded)}`);
  assert(decoded.final===true,'final QR lost finalize=true');
  assert(await currentDay(page)===expectedNextDay,`runtime did not prepare T${expectedNextDay} after finishing T${expectedQrDay}`);
  if(expectedQrDay===7)await captureEvidence(page,'final-qr');
  await page.locator('#end .btn2').filter({hasText:'Zurück zum Plan'}).click();
  await page.locator('#end').waitFor({state:'hidden'});
  await assertHubDay(page,expectedNextDay);
}
async function interimQrFromUi(page, expectedDay){
  await dismissInstallOverlay(page);
  const before=await page.evaluate(()=>({
    day:Number(d),done:JSON.stringify([...done].sort((a,b)=>a-b)),values:JSON.stringify(v)
  }));
  assert(before.day===expectedDay,'interim QR began on wrong day');
  const trigger=page.locator('#plan > button.btn2[onclick="showQr(false)"]');
  assert(await trigger.count()===1,'interim QR button not uniquely available');
  await trigger.click();
  await page.locator('#end').waitFor({state:'visible'});
  const qr=page.locator('#qr'),payload=await qr.getAttribute('data-payload');
  assert(typeof payload==='string'&&payload.startsWith('KGGD1:'),'interim QR payload missing');
  const decoded=decodePayload(payload);
  assert(Number(decoded.d)===expectedDay&&decoded.final===false,
    'interim QR incorrectly finished a day: '+JSON.stringify(decoded));
  assert((await page.locator('#endTitle').innerText())==='Aktuelle Werte T'+expectedDay,
    'interim QR title not showing current day');
  assert((await page.locator('#endInfo').innerText()).includes('beendet das Training nicht'),
    'interim QR has lost its nonfinal warning');
  const img=qr.locator('img');
  await img.waitFor({state:'visible',timeout:8000});
  await captureEvidence(page,'interim-qr');
  await img.click();
  const full=page.locator('#kggQrFull');
  await full.waitFor({state:'visible',timeout:8000});
  assert(await full.locator('img[alt="QR-Code"]').count()===1,
    'interim QR fullscreen lost its image');
  await full.getByRole('button',{name:'Schließen'}).click();
  await full.waitFor({state:'detached',timeout:8000});
  assert(await qr.getAttribute('data-payload')===payload,'fullscreen changed QR payload');
  await qr.getByRole('button',{name:'QR-Code kopieren'}).click();
  assert(await qr.getAttribute('data-payload')===payload,
    'copy action changed QR payload');
  // Clipboard access may be denied in CI. Button/payload safety is verified,
  // successful OS clipboard copying is NOT claimed by this browser test.
  const after=await page.evaluate(()=>({
    day:Number(d),done:JSON.stringify([...done].sort((a,b)=>a-b)),values:JSON.stringify(v)
  }));
  assert(JSON.stringify(after)===JSON.stringify(before),
    'nonfinal QR mutated training day/completion/values');
  await page.locator('#end .btn2').filter({hasText:'Zurück zum Plan'}).click();
  await page.locator('#end').waitFor({state:'hidden'});
  await assertHubDay(page,expectedDay);
}

function rawPlan(id,title){return{i:id,t:title,v:1,d:12,extendDays:true,stepDays:6,e:[[title+' Übung',1,'B','kg','Wdh']]}}
async function captureEvidence(page,kind){
  if(!process.env.KGG_PARITY_OUT)return;
  const out=path.resolve(process.env.KGG_PARITY_OUT);
  assert(path.basename(out)==='patient-ui-parity','continuous day proof requires isolated parity artifact directory');
  fs.mkdirSync(out,{recursive:true});
  await page.screenshot({path:path.join(out,'days-'+MODE+'-'+kind+'.png'),animations:'disabled'});
}
async function verifyVariantMounted(page){
  const card=page.locator("#list .ex").first();
  for(let attempt=0;attempt<5;attempt++){
    if(await card.evaluate(el=>el.classList.contains("kggOpen")))break;
    await card.locator("h3").click();
    await page.waitForTimeout(90);
  }
  assert(await card.evaluate(el=>el.classList.contains("kggOpen")),"day-flow card would not open");
  await card.locator(":scope > .set").first().locator(".kggCompactTapProxy[data-kgg-key='a']").first().click({timeout:8000});
  if(MODE==="react")await page.locator("[data-kgg-react-numpad-header='v1']").waitFor({state:"attached",timeout:8000});
  const mounted=await page.evaluate(()=>document.body.classList.contains("kggReactNumpadHeaderV1"));
  assert(mounted===(MODE==="react"),"Requested React mode differs from mounted variant: "+JSON.stringify({MODE,mounted}));
  await page.locator("#pad .padActions .padCancel").click({timeout:8000});
}
async function main(){
  const watchdog=setTimeout(()=>{console.error('KGG patient continuous days Playwright FAIL: global 150s watchdog');process.exit(1)},150000);
  const mark=message=>console.log('[continuous-days] '+message);
  const server=http.createServer((request,response)=>{const file=safeFile(request.url);if(!file){response.writeHead(404,{'Content-Type':'text/plain'});response.end('not found');return}response.writeHead(200,{'Content-Type':contentType(file),'Cache-Control':'no-store','Service-Worker-Allowed':'/'});fs.createReadStream(file).pipe(response)});
  await new Promise(resolve=>server.listen(0,'127.0.0.1',resolve));
  const {port}=server.address();
  const browser=await (ENGINE==='webkit'?webkit:chromium).launch({headless:true});
  const context=await browser.newContext({viewport:{width:390,height:844},serviceWorkers:'allow'});
  // The day/QR contract is not a media-source availability test.
  // Use a deterministic, CORS-safe image for the unrelated external RepDB asset;
  // the separate patient media suites continue to test real source failures.
  const syntheticMedia='<svg xmlns="http://www.w3.org/2000/svg" width="64" height="64">'+
    '<rect width="64" height="64" fill="#dbe3ef"/></svg>';
  await context.route(/^https:\/\/exercise-dataset\.com\/images\/flat\//,
    route=>route.fulfill({status:200,contentType:'image/svg+xml',
      headers:{'access-control-allow-origin':'*'},body:syntheticMedia}));
  const page=await context.newPage();
  // The install guide has a separate delayed auto-day migration. Keep this
  // continuous-day regression focused on the day-history/runtime contract.
  await page.addInitScript(()=>{window.__kggAutoDayRan=1;localStorage.setItem('kggInstallAsked','1')});
  page.setDefaultTimeout(8000);page.setDefaultNavigationTimeout(15000);
  const errors=[];page.on('pageerror',e=>errors.push(e.message));
  const plan={i:'continuous-days-playwright',t:'Fortlaufender Testplan',v:1,d:12,extendDays:true,stepDays:6,e:[['Beinpresse',1,'B','kg','Wdh']]};
  const url=`http://127.0.0.1:${port}/kgg/?kggReactPad=${MODE==='react'?'1':'0'}&plan=${encodeURIComponent('KGGH2:'+encodePlan(plan))}`;
  try{
    mark('boot continuous fixture');
    await page.goto(url,{waitUntil:'domcontentloaded'});
    await page.waitForTimeout(800);
    const boot=await page.evaluate(()=>({planHidden:document.getElementById('plan')?.classList.contains('hide'),status:document.getElementById('status')?.textContent||'',statusClass:document.getElementById('status')?.className||'',href:location.href,currentPlan:localStorage.getItem('kggCurrentPlanV1')||'',hasDayFlow:Boolean(window.KGGPatientDayFlow)}));
    if(boot.planHidden)throw new Error('patient core boot failed before service worker: '+JSON.stringify({boot,pageErrors:errors}));
    await waitForRuntime(page);
    await verifyVariantMounted(page);
    assert((await page.locator('#meta').innerText()).includes('fortlaufender Trainingsplan'),'continuous plan metadata still shows a fixed day count');
    assert(await page.locator('#extendBtn').isHidden(),'legacy +days button is still visible');

    mark('T7 to T8');
    await seedCurrent(page,[1,2,3,4,5,6],7);
    await assertHubDay(page,7);
    mark('T7 intermediate QR remains unfinalized');
    await interimQrFromUi(page,7);
    await finishFromUi(page,7,8);

    mark('T12 to T13 and reload');
    await seedCurrent(page,Array.from({length:12},(_,i)=>i+1),13);
    await assertHubDay(page,13);
    await waitForVisibleDayButtons(page,12);
    await page.evaluate(()=>put(0,1,'B','a','42'));
    assert(await page.evaluate(()=>v[k(0,1,'B','a',13)])==='42','T13 value was not stored');
    await page.reload({waitUntil:'domcontentloaded'});await waitForRuntime(page);await assertHubDay(page,13);
    assert(await page.evaluate(()=>v[k(0,1,'B','a',13)])==='42','T13 value was lost after reload');
    await finishFromUi(page,13,14);

    mark('T99 to T100 and paged history');
    await seedCurrent(page,Array.from({length:99},(_,i)=>i+1),100);
    await assertHubDay(page,100);
    await waitForVisibleDayButtons(page,12);
    await page.locator('#kggHistoryToggle').click();
    await page.locator('#kggHistoryList').waitFor({state:'visible'});
    assert(await page.locator('#kggHistoryList .kggDayCard[data-day]').count()===30,'history did not limit initial T100 DOM to 30 day cards');
    assert(await page.locator('#kggHistoryMore').count()===1,'T100 history has no older-training pagination control');
    await page.locator('#kggHistoryMore').click();
    assert(await page.locator('#kggHistoryList .kggDayCard[data-day]').count()===60,'older-training pagination did not expand by 30');
    await captureEvidence(page,'history-100');
    await page.locator('#kggHistoryBackdrop').click({position:{x:2,y:2}});

    mark('historical finalize preserves front');
    await page.evaluate(()=>{d=4;render()});
    await page.waitForFunction(()=>Number(d)===4);
    await page.locator('#plan > button.btn').click();
    await confirmTicket034FinishIfShown(page);
    await page.locator('#end').waitFor({state:'visible'});
    assert(decodePayload(await page.locator('#qr').getAttribute('data-payload')).d===4,'historical QR did not stay on T4');
    assert(await currentDay(page)===4,'historical finalize unexpectedly moved the in-session selected day');
    await page.reload({waitUntil:'domcontentloaded'});await waitForRuntime(page);await assertHubDay(page,100);

    // Two plans keep independent resume days.
    mark('multi-plan independent days');
    await page.evaluate(({planA,planB})=>{
      function planHash(raw){const ex=(raw.e||[]).map(e=>[e[0]||'Übung',Number(e[1])||3,e[2]||'LR',e[3]||'kg',e[4]||'Wdh']);const text=JSON.stringify({i:raw.i||'plan',t:raw.t||'KGG Trainingsplan',e:ex});let h=2166136261;for(let i=0;i<text.length;i++){h^=text.charCodeAt(i);h=Math.imul(h,16777619)}return(h>>>0).toString(36)}
      function keys(raw){const base='kgg-'+raw.i+'-'+planHash(raw);return{done:base+'-done',meta:base+'-meta'}}
      const a=keys(planA),b=keys(planB);
      localStorage.setItem(a.done,JSON.stringify(Array.from({length:27},(_,i)=>i+1)));
      localStorage.setItem(a.meta,JSON.stringify({lastOpenDay:28,lastCompletedDay:27,storageVersion:6}));
      localStorage.setItem(b.done,JSON.stringify([1,2,3,4]));
      localStorage.setItem(b.meta,JSON.stringify({lastOpenDay:5,lastCompletedDay:4,storageVersion:6}));
      localStorage.setItem('kggPatientMultiPlansV1',JSON.stringify({version:1,plans:[planA,planB],active:0,day:{0:28,1:5}}));
      localStorage.setItem('kggCurrentPlanV1',JSON.stringify({plan:planA,importedAt:new Date().toISOString()}));
    },{planA:rawPlan('continuous-plan-a','Plan A'),planB:rawPlan('continuous-plan-b','Plan B')});
    await page.reload({waitUntil:'domcontentloaded'});await waitForRuntime(page);await assertHubDay(page,28);
    await page.evaluate(()=>window.KGGPatientMultiPlan.switchTo(1));await assertHubDay(page,5);
    await page.evaluate(()=>window.KGGPatientMultiPlan.switchTo(0));await assertHubDay(page,28);
    await page.reload({waitUntil:'domcontentloaded'});await waitForRuntime(page);await assertHubDay(page,28);

    // Explicit fixed plans keep their hard end.
    mark('fixed plan hard end');
    const fixed={i:'fixed-days-playwright',t:'Fester Testplan',v:1,d:12,extendDays:false,stepDays:6,e:[['Fix',1,'B','kg','Wdh']]};
    await page.goto(`http://127.0.0.1:${port}/kgg/?kggReactPad=${MODE==='react'?'1':'0'}&plan=${encodeURIComponent('KGGH2:'+encodePlan(fixed))}`,{waitUntil:'domcontentloaded'});
    await page.locator('#kggPlanLinkChoice').waitFor({state:'visible'});
    await page.locator('#kggPlanLinkChoiceReplace').click();
    await page.locator('#kggPlanLinkChoiceBackdrop').waitFor({state:'detached'});
    await waitForRuntime(page);
    await seedCurrent(page,Array.from({length:12},(_,i)=>i+1),12);await assertHubDay(page,12);
    assert((await page.locator('#meta').innerText()).includes('12 Trainingstage'),'fixed plan lost its finite day label');
    await page.locator('#plan > button.btn').click();await confirmTicket034FinishIfShown(page);await page.locator('#end').waitFor({state:'visible'});
    assert(decodePayload(await page.locator('#qr').getAttribute('data-payload')).d===12,'fixed plan final QR day is wrong');
    assert(await currentDay(page)===12,'fixed plan advanced beyond its hard end');

    mark('final assertions');
    assert(errors.length===0,`continuous-day browser raised page errors: ${errors.join(' | ')}`);
    const proof={schema:1,status:'PASS',syntheticOnly:true,engine:ENGINE,mode:MODE,
      sourceSha:process.env.KGG_PARITY_HEAD_SHA||execFileSync('git',['rev-parse','HEAD'],{cwd:ROOT,encoding:'utf8'}).trim(),
      featureIds:['PAT-DAY-001','PAT-DAY-002','PAT-DAY-003','PAT-DAY-004','PAT-HIST-001','PAT-STOR-001','PAT-MULTI-003','PAT-FIN-001','PAT-QR-001','PAT-QR-002','PAT-QR-004'],
      assertions:{t7ToT8:true,t12ToT13:true,t99ToT100:true,reloadT13:true,historyPagination:true,multiPlanIndependent:true,fixedPlanBounded:true,finalQrDays:true,interimQrNonfinal:true,interimQrFullscreen:true,copyActionPreservesPayload:true}};
    if(process.env.KGG_PARITY_OUT){
      const out=path.resolve(process.env.KGG_PARITY_OUT);
      assert(path.basename(out)==='patient-ui-parity','day proof requires isolated parity artifact directory');
      fs.mkdirSync(out,{recursive:true});
      fs.writeFileSync(path.join(out,'days-'+MODE+'.json'),JSON.stringify(proof,null,2)+'\n');
    }
    console.log(JSON.stringify(proof));
  }finally{clearTimeout(watchdog);await context.close().catch(()=>{});await browser.close().catch(()=>{});if(typeof server.closeAllConnections==='function')server.closeAllConnections();await Promise.race([new Promise(resolve=>server.close(()=>resolve())),new Promise(resolve=>setTimeout(resolve,2000))])}
}
main().catch(error=>{console.error(`KGG patient continuous days Playwright FAIL: ${error.stack||error.message}`);process.exitCode=1});
