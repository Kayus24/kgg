#!/usr/bin/env node
'use strict';

const fs=require('fs');
const http=require('http');
const path=require('path');
const crypto=require('crypto');
const {chromium}=require('playwright');

const ROOT=path.resolve(__dirname,'..');
const OUTPUT_DIR=path.join(ROOT,'tmp','patient-storage-v7');
const round=Number((process.argv.find(arg=>arg.startsWith('--round='))||'--round=1').split('=')[1])||1;
const iterations=Number((process.argv.find(arg=>arg.startsWith('--iterations='))||'--iterations=5').split('=')[1])||5;
const report={version:'patient-storage-v7-regression-v1',round,iterations,startedAt:new Date().toISOString(),runs:[],failureFingerprints:{},approachChangeRequired:false};
let workerMode='candidate';

function assert(condition,message){if(!condition)throw new Error(message)}
function encodePlan(plan){return Buffer.from(JSON.stringify(plan),'utf8').toString('base64url')}
function planUrl(baseUrl,plan){return`${baseUrl}/index.html?plan=${encodeURIComponent(`KGGH2:${encodePlan(plan)}`)}`}
function randomId(label){return`storage-v7-r${round}-${label}-${crypto.randomUUID()}`}
function clone(value){return JSON.parse(JSON.stringify(value))}
function contentType(file){
  if(file.endsWith('.html'))return'text/html; charset=utf-8';
  if(file.endsWith('.js'))return'application/javascript; charset=utf-8';
  if(file.endsWith('.json')||file.endsWith('.webmanifest'))return'application/json; charset=utf-8';
  if(file.endsWith('.png'))return'image/png';
  if(file.endsWith('.svg'))return'image/svg+xml';
  return'application/octet-stream';
}
function injectedIndex(source){
  return source.replace('</body>','<script>window.__KGG_TEST__=true</script><script src="./patient-start-scan.js"></script><script src="./patient-multiplan-db.js"></script><script src="./patient-plan-delete.js"></script></body>');
}
function createServer(){
  const server=http.createServer((request,response)=>{
    const url=new URL(request.url,'http://127.0.0.1');
    if(url.pathname==='/__blank.html'){response.writeHead(200,{'Content-Type':'text/html; charset=utf-8','Cache-Control':'no-store'});response.end('<!doctype html><title>blank</title>');return}
    const relative=url.pathname==='/'?'index.html':url.pathname.replace(/^\/+/,'');
    const target=path.resolve(ROOT,relative);
    if(!target.startsWith(ROOT+path.sep)){response.writeHead(403).end('forbidden');return}
    try{
      let body=fs.readFileSync(target);
      if(relative==='index.html')body=Buffer.from(injectedIndex(body.toString('utf8')),'utf8');
      if(relative==='service-worker.js'&&workerMode==='old'){
        let text=body.toString('utf8');
        const version=Number((text.match(/const APP_VERSION = '([0-9]+)'/)||[])[1]||1);
        text=text.replace(/const APP_VERSION = '[0-9]+';/,`const APP_VERSION = '${Math.max(1,version-1)}';`)
          .replace(/const CACHE_NAME = '[^']+';/,`const CACHE_NAME = 'kgg-handyplan-v${Math.max(1,version-1)}-storage-v7-old-worker';`);
        body=Buffer.from(text,'utf8');
      }
      response.writeHead(200,{'Content-Type':contentType(target),'Cache-Control':'no-store'});
      response.end(body);
    }catch(error){response.writeHead(404).end('not found')}
  });
  return new Promise(resolve=>server.listen(0,'127.0.0.1',()=>resolve({server,baseUrl:`http://127.0.0.1:${server.address().port}`})));
}
async function ready(page){
  await page.waitForFunction(()=>typeof p==='object'&&p&&Array.isArray(p.ex)&&typeof window.KGGPatientStorageV7==='object');
}
async function openPlan(page,baseUrl,plan){
  await page.goto(planUrl(baseUrl,plan),{waitUntil:'domcontentloaded'});
  await ready(page);
}
async function reset(page,baseUrl){
  await page.goto(`${baseUrl}/__blank.html`,{waitUntil:'domcontentloaded'});
  await page.evaluate(()=>localStorage.clear());
}
async function snapshot(page){
  return page.evaluate(()=>({
    planId:p.id,title:p.title,values:JSON.parse(JSON.stringify(v)),done:[...done],day:d,
    meta:JSON.parse(localStorage.getItem(mk())||'{}'),
    keys:Object.keys(localStorage).sort()
  }));
}
async function runCase(run,name,fn){
  const started=Date.now();
  try{
    await fn();
    run.cases.push({name,status:'passed',durationMs:Date.now()-started});
  }catch(error){
    const message=String(error&&error.message||error);
    const fingerprint=`${name}:${message.replace(/[0-9a-f]{8}-[0-9a-f-]{27}/gi,'<uuid>')}`;
    run.cases.push({name,status:'failed',durationMs:Date.now()-started,error:message,fingerprint});
    report.failureFingerprints[fingerprint]=(report.failureFingerprints[fingerprint]||0)+1;
    if(report.failureFingerprints[fingerprint]>=3)report.approachChangeRequired=true;
  }
}
function basePlan(id,title='Basis'){
  return{i:id,t:title,v:1,d:6,extendDays:true,stepDays:6,e:[['Beinpresse',2,'B','kg','Wdh','',''],['Rudern',2,'LR','kg','Wdh','','']]};
}
async function runWorkerCase(browser,baseUrl,id){
  workerMode='old';
  const context=await browser.newContext({viewport:{width:390,height:844},serviceWorkers:'allow'});
  const page=await context.newPage();
  try{
    const plan=basePlan(id,'Service Worker Alt');
    await openPlan(page,baseUrl,plan);
    await page.evaluate(()=>{put(0,1,'B','a','73');});
    await page.evaluate(()=>navigator.serviceWorker.ready);
    workerMode='candidate';
    const updated=await page.evaluate(async()=>{
      const registration=await navigator.serviceWorker.ready;
      await registration.update();
      let worker=registration.waiting||registration.installing;
      if(worker&&worker.state!=='installed'&&worker.state!=='activated'){
        await new Promise((resolve,reject)=>{
          const timer=setTimeout(()=>reject(new Error('service worker install timeout')),12000);
          worker.addEventListener('statechange',()=>{if(worker.state==='installed'||worker.state==='activated'){clearTimeout(timer);resolve()}});
        });
      }
      worker=registration.waiting||worker;
      if(worker&&worker.state!=='activated')worker.postMessage({type:'SKIP_WAITING'});
      await new Promise(resolve=>{const timer=setTimeout(resolve,4000);navigator.serviceWorker.addEventListener('controllerchange',()=>{clearTimeout(timer);resolve()},{once:true})});
      return true;
    });
    assert(updated,'service worker update did not run');
    await page.reload({waitUntil:'domcontentloaded'});await ready(page);
    const value=await page.evaluate(()=>val(0,1,'B','a'));
    assert(value==='73','service worker update lost patient value');
  }finally{workerMode='candidate';await context.close()}
}
async function runIteration(browser,baseUrl,index){
  const run={iteration:index,profileId:crypto.randomUUID(),startedAt:new Date().toISOString(),cases:[]};
  const context=await browser.newContext({viewport:{width:390,height:844},serviceWorkers:'block'});
  const page=await context.newPage();
  const ids={
    reload:randomId(`i${index}-reload`),days:randomId(`i${index}-days`),title:randomId(`i${index}-title`),
    add:randomId(`i${index}-add`),reorder:randomId(`i${index}-reorder`),incompatible:randomId(`i${index}-incompatible`),
    separateA:randomId(`i${index}-separate-a`),separateB:randomId(`i${index}-separate-b`),
    multiA:randomId(`i${index}-multi-a`),multiB:randomId(`i${index}-multi-b`),
    legacy:randomId(`i${index}-legacy`),deleteA:randomId(`i${index}-delete-a`),deleteB:randomId(`i${index}-delete-b`),
    lifecycle:randomId(`i${index}-lifecycle`),worker:randomId(`i${index}-worker`)
  };
  try{
    await runCase(run,'01-reload-persists',async()=>{
      await reset(page,baseUrl);await openPlan(page,baseUrl,basePlan(ids.reload));
      await page.evaluate(()=>put(0,1,'B','a','41'));await page.reload({waitUntil:'domcontentloaded'});await ready(page);
      assert(await page.evaluate(()=>val(0,1,'B','a'))==='41','reload lost value');
    });
    await runCase(run,'02-days-and-completion-separated',async()=>{
      await reset(page,baseUrl);await openPlan(page,baseUrl,basePlan(ids.days));
      await page.evaluate(()=>{put(0,1,'B','a','51');done=[1];d=2;save()});await page.reload({waitUntil:'domcontentloaded'});await ready(page);
      const result=await page.evaluate(()=>({done:[...done],t1:v[k(0,1,'B','a',1)]||'',t2:v[k(0,1,'B','a',2)]||''}));
      assert(result.done.join(',')==='1','completed T1 was not saved');assert(result.t1==='51'&&result.t2==='','T2 did not start empty');
    });
    await runCase(run,'03-title-change-keeps-values',async()=>{
      await reset(page,baseUrl);const original=basePlan(ids.title,'Alter Titel');await openPlan(page,baseUrl,original);
      await page.evaluate(()=>put(0,1,'B','a','61'));const changed={...original,t:'Neuer Titel'};await openPlan(page,baseUrl,changed);
      assert(await page.evaluate(()=>val(0,1,'B','a'))==='61','title change lost value');
    });
    await runCase(run,'04-added-exercise-keeps-values',async()=>{
      await reset(page,baseUrl);const original=basePlan(ids.add);await openPlan(page,baseUrl,original);
      await page.evaluate(()=>put(0,1,'B','a','62'));const changed=clone(original);changed.e.push(['Latzug',2,'B','kg','Wdh','','']);await openPlan(page,baseUrl,changed);
      assert(await page.evaluate(()=>val(0,1,'B','a'))==='62','adding exercise lost existing value');
    });
    await runCase(run,'05-reorder-maps-correct-exercise',async()=>{
      await reset(page,baseUrl);const original={...basePlan(ids.reorder),e:[['Beinpresse',2,'B','kg','Wdh','',''],['Rudern',2,'LR','kg','Wdh','',''],['Rudern',2,'LR','kg','Wdh','','']]};await openPlan(page,baseUrl,original);
      await page.evaluate(()=>{put(0,1,'B','a','11');put(1,1,'L','a','22');put(2,1,'L','a','23')});const changed={...original,e:[original.e[1],original.e[0],original.e[2]]};await openPlan(page,baseUrl,changed);
      const result=await page.evaluate(()=>({row1:v[k(0,1,'L','a')]||'',press:v[k(1,1,'B','a')]||'',row2:v[k(2,1,'L','a')]||''}));
      assert(result.row1==='22'&&result.press==='11'&&result.row2==='23','reorder or duplicate occurrence assigned values incorrectly');
    });
    await runCase(run,'06-incompatible-side-or-unit-isolated',async()=>{
      await reset(page,baseUrl);const original={...basePlan(ids.incompatible),e:[['Rudern',2,'B','kg','Wdh','','']]};await openPlan(page,baseUrl,original);
      await page.evaluate(()=>{put(0,1,'B','a','31');put(0,1,'B','b','12')});const changed={...original,e:[['Rudern',2,'LR','lb','Sek','','']]};await openPlan(page,baseUrl,changed);
      const result=await page.evaluate(()=>({left:v[k(0,1,'L','a')]||'',right:v[k(0,1,'R','b')]||'',orphans:(JSON.parse(localStorage.getItem(mk())||'{}').orphans||[]).length}));
      assert(result.left===''&&result.right==='','incompatible exercise received foreign values');assert(result.orphans>=2,'incompatible values were not archived');
    });
    await runCase(run,'07-different-plan-ids-are-isolated',async()=>{
      await reset(page,baseUrl);const withoutId={t:'Lokaler UUID-Plan',v:1,d:6,e:[['Beinpresse',1,'B','kg','Wdh','','']]};await openPlan(page,baseUrl,withoutId);
      const firstId=await page.evaluate(()=>p.id);await page.reload({waitUntil:'domcontentloaded'});await ready(page);const secondId=await page.evaluate(()=>p.id);
      assert(/^[0-9a-f]{8}-[0-9a-f-]{27}$/i.test(firstId)&&secondId===firstId,'missing plan id did not receive one persistent UUID');
      await reset(page,baseUrl);const a=basePlan(ids.separateA),b=basePlan(ids.separateB);await openPlan(page,baseUrl,a);await page.evaluate(()=>put(0,1,'B','a','71'));
      await openPlan(page,baseUrl,b);await page.evaluate(()=>put(0,1,'B','a','72'));await openPlan(page,baseUrl,a);assert(await page.evaluate(()=>val(0,1,'B','a'))==='71','plan A received plan B value');
      await openPlan(page,baseUrl,b);assert(await page.evaluate(()=>val(0,1,'B','a'))==='72','plan B lost isolated value');
    });
    await runCase(run,'08-multiplan-switch-keeps-values',async()=>{
      await reset(page,baseUrl);const a=basePlan(ids.multiA),b=basePlan(ids.multiB);await openPlan(page,baseUrl,a);await page.evaluate(()=>put(0,1,'B','a','81'));
      await page.evaluate(raw=>{const state=KGGPatientMultiPlan.ensureState();state.plans.push(raw);localStorage.setItem('kggPatientMultiPlansV1',JSON.stringify(state));},b);
      await page.evaluate(()=>KGGPatientMultiPlan.switchTo(1));await page.evaluate(()=>put(0,1,'B','a','82'));await page.evaluate(()=>KGGPatientMultiPlan.switchTo(0));
      assert(await page.evaluate(()=>val(0,1,'B','a'))==='81','switch back to plan A lost value');await page.evaluate(()=>KGGPatientMultiPlan.switchTo(1));
      assert(await page.evaluate(()=>val(0,1,'B','a'))==='82','switch to plan B lost value');
    });
    await runCase(run,'09-legacy-migration-priority-and-idempotence',async()=>{
      await reset(page,baseUrl);const original=basePlan(ids.legacy,'Legacy Alt');await openPlan(page,baseUrl,original);await page.evaluate(()=>{put(0,1,'B','a','91');put(1,1,'L','a','92');done=[1,3];save()});
      const changed={...original,t:'Legacy Neu',e:[original.e[1],original.e[0]]};
      const seeded=await page.evaluate(next=>{
        const current=JSON.parse(localStorage.getItem('kggCurrentPlanV1')).plan,stable=KGGPatientStorageV7.storageKeys(current);
        const oldLegacy=KGGPatientStorageV7.legacyKeys(current),oldValues=JSON.parse(localStorage.getItem(oldLegacy.values)||'{}');
        [stable.values,stable.done,stable.meta].forEach(key=>localStorage.removeItem(key));
        const currentLegacy=KGGPatientStorageV7.legacyKeys(next);
        localStorage.setItem(currentLegacy.values,JSON.stringify({'1|0|1|L|a':'999'}));
        localStorage.setItem(currentLegacy.done,JSON.stringify([6]));
        localStorage.setItem(currentLegacy.meta,JSON.stringify({lastSavedAt:'2999-01-01T00:00:00.000Z',lastOpenDay:6,planRaw:next}));
        p=null;
        return{oldValues,oldBase:oldLegacy.base,mapped:KGGPatientStorageV7.remapValues(oldValues,KGGPatientStorageV7.exerciseRefs(current),KGGPatientStorageV7.exerciseRefs(next),[])};
      },changed);
      assert(seeded.oldValues['1|0|1|B|a']==='91'&&seeded.oldValues['1|1|1|L|a']==='92','legacy dual-write missing before migration: '+JSON.stringify(seeded));
      assert(seeded.mapped.values['1|1|1|B|a']==='91'&&seeded.mapped.values['1|0|1|L|a']==='92','exercise remap failed before migration: '+JSON.stringify(seeded));
      await openPlan(page,baseUrl,changed);
      let result=await page.evaluate(()=>({row:v[k(0,1,'L','a',1)]||'',press:v[k(1,1,'B','a',1)]||'',done:[...done],meta:JSON.parse(localStorage.getItem(mk())||'{}')}));
      assert(result.row==='92'&&result.press==='91','legacy migration ignored exact previous-plan hash: '+JSON.stringify(result));assert(result.done.join(',')==='1,3','legacy completion days were not migrated');assert(result.meta.migratedFrom,'migration source was not recorded');
      const first=JSON.stringify({row:result.row,press:result.press,done:result.done,migratedFrom:result.meta.migratedFrom,orphans:result.meta.orphans});await page.reload({waitUntil:'domcontentloaded'});await ready(page);
      result=await page.evaluate(()=>({row:v[k(0,1,'L','a',1)]||'',press:v[k(1,1,'B','a',1)]||'',done:[...done],meta:JSON.parse(localStorage.getItem(mk())||'{}')}));
      assert(JSON.stringify({row:result.row,press:result.press,done:result.done,migratedFrom:result.meta.migratedFrom,orphans:result.meta.orphans})===first,'legacy migration was not idempotent');
      await reset(page,baseUrl);const latestOld=basePlan(ids.legacy+'-latest','Nur letzter Legacy-Eintrag');await openPlan(page,baseUrl,latestOld);await page.evaluate(()=>put(0,1,'B','a','95'));
      const latestNew={...latestOld,t:'Aktualisierte Legacy-Struktur',e:[latestOld.e[1],latestOld.e[0]]};
      await page.evaluate(next=>{
        const current=JSON.parse(localStorage.getItem('kggCurrentPlanV1')).plan,stable=KGGPatientStorageV7.storageKeys(current);
        [stable.values,stable.done,stable.meta,stable.previous].forEach(key=>localStorage.removeItem(key));
        localStorage.setItem('kggCurrentPlanV1',JSON.stringify({plan:next,importedAt:new Date().toISOString()}));
        localStorage.setItem('kgg-foreign-plan-deadbeef-values',JSON.stringify({'1|0|1|B|a':'777'}));
        localStorage.setItem('kgg-foreign-plan-deadbeef-meta',JSON.stringify({lastSavedAt:'2999-01-01T00:00:00.000Z',planRaw:{i:'foreign-plan',e:next.e}}));
        p=null;
      },latestNew);
      await openPlan(page,baseUrl,latestNew);
      const latestResult=await page.evaluate(()=>({mapped:v[k(1,1,'B','a',1)]||'',foreign:Object.values(v).includes('777'),source:JSON.parse(localStorage.getItem(mk())||'{}').migratedFrom||''}));
      assert(latestResult.mapped==='95'&&!latestResult.foreign&&latestResult.source,'latest same-id legacy fallback failed or imported a foreign plan');
    });
    await runCase(run,'10-delete-only-selected-plan',async()=>{
      await reset(page,baseUrl);const a=basePlan(ids.deleteA),b=basePlan(ids.deleteB);await openPlan(page,baseUrl,a);await page.evaluate(()=>put(0,1,'B','a','101'));await openPlan(page,baseUrl,b);await page.evaluate(()=>put(0,1,'B','a','102'));
      const result=await page.evaluate(({a,b})=>{__kggPlanDeleteTest.removeLocalPlanKeys(a);const ak=KGGPatientStorageV7.storageKeys(a),bk=KGGPatientStorageV7.storageKeys(b);return{a:localStorage.getItem(ak.values),b:JSON.parse(localStorage.getItem(bk.values)||'{}'),foreign:Object.keys(localStorage).filter(key=>key.startsWith('kgg-'+a.i+'-'))}}, {a,b});
      assert(result.a===null&&result.foreign.length===0,'selected plan keys were not fully deleted');assert(result.b['1|0|1|B|a']==='102','deleting plan A changed plan B');
    });
    await runCase(run,'11-lifecycle-events-save',async()=>{
      await reset(page,baseUrl);const plan=basePlan(ids.lifecycle);await openPlan(page,baseUrl,plan);
      await page.evaluate(()=>{v[k(0,1,'B','a')]='111';window.dispatchEvent(new Event('pagehide'))});await page.reload({waitUntil:'domcontentloaded'});await ready(page);assert(await page.evaluate(()=>val(0,1,'B','a'))==='111','pagehide did not save');
      await page.evaluate(()=>{v[k(0,1,'B','a')]='112';Object.defineProperty(document,'visibilityState',{value:'hidden',configurable:true});document.dispatchEvent(new Event('visibilitychange'))});await page.reload({waitUntil:'domcontentloaded'});await ready(page);assert(await page.evaluate(()=>val(0,1,'B','a'))==='112','background visibility did not save');
      await page.evaluate(()=>put(0,1,'B','a','113'));await page.reload({waitUntil:'domcontentloaded'});await ready(page);assert(await page.evaluate(()=>val(0,1,'B','a'))==='113','ordinary reload lost autosaved value');
    });
    await runCase(run,'12-old-service-worker-updates-without-loss',()=>runWorkerCase(browser,baseUrl,ids.worker));
  }finally{
    await context.close();
    run.finishedAt=new Date().toISOString();
    run.status=run.cases.every(item=>item.status==='passed')?'passed':'failed';
    report.runs.push(run);
  }
}

(async()=>{
  fs.mkdirSync(OUTPUT_DIR,{recursive:true});
  const {server,baseUrl}=await createServer();
  const browser=await chromium.launch({headless:true});
  try{
    for(let index=1;index<=iterations;index++){
      await runIteration(browser,baseUrl,index);
      if(report.approachChangeRequired)break;
    }
  }finally{
    await browser.close();await new Promise(resolve=>server.close(resolve));
  }
  report.finishedAt=new Date().toISOString();
  report.status=!report.approachChangeRequired&&report.runs.length===iterations&&report.runs.every(run=>run.status==='passed')?'passed':'failed';
  const output=path.join(OUTPUT_DIR,`round-${round}.json`);
  fs.writeFileSync(output,JSON.stringify(report,null,2)+'\n','utf8');
  if(report.status!=='passed'){
    console.error(`Patient storage v7 regression FAILED: ${output}`);
    if(report.approachChangeRequired)console.error('Same failure fingerprint reached three occurrences; change the technical approach before retrying.');
    process.exit(1);
  }
  console.log(`Patient storage v7 regression PASS: round ${round}, ${iterations} fresh profiles (${output})`);
})().catch(error=>{console.error(error&&error.stack||error);process.exit(1)});
