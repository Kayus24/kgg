#!/usr/bin/env node
'use strict';

// Synthetic-only, fail-closed H2/H3 scanner/link parity. Live camera not in scope.
const fs=require('fs'),http=require('http'),path=require('path');
const {execFileSync}=require('node:child_process');
const {chromium,webkit}=require('playwright');
const ROOT=path.resolve(__dirname,'..');
const ENGINE=process.env.KGG_SCAN_BROWSER||'chromium';
const OUT=process.env.KGG_PARITY_OUT?path.resolve(process.env.KGG_PARITY_OUT):null;
if(!['chromium','webkit'].includes(ENGINE))throw new Error('Unsupported KGG_SCAN_BROWSER');
if(OUT&&path.basename(OUT)!=='patient-ui-parity')throw new Error('Invalid isolated evidence path');
const SHA=process.env.KGG_PARITY_HEAD_SHA||
  execFileSync('git',['rev-parse','HEAD'],{cwd:ROOT,encoding:'utf8'}).trim();
if(!/^[0-9a-f]{40}$/i.test(SHA))throw new Error('Expected an exact candidate SHA');
function assert(condition,message){if(!condition)throw new Error(message)}
function codeFor(raw,format){
  const json=Buffer.from(JSON.stringify(raw),'utf8');
  if(format==='KGGH2')return 'KGGH2:'+json.toString('base64url');
  const fflate=require(path.join(ROOT,'vendor','fflate-0.8.3.js'));
  return 'KGGH3:'+Buffer.from(fflate.zlibSync(json)).toString('base64url')
}
function startServer(){
  const server=http.createServer((request,response)=>{
    try{
      const pathname=decodeURIComponent(new URL(request.url,'http://127.0.0.1').pathname);
      const relative=pathname==='/'?'index.html':pathname.replace(/^\/+/,'');
      const file=path.resolve(ROOT,relative);
      if(!file.startsWith(ROOT+path.sep)){response.writeHead(403).end();return}
      fs.readFile(file,(error,data)=>{
        if(error){response.writeHead(404).end('not found');return}
        const mime=({'.html':'text/html; charset=utf-8','.js':'text/javascript; charset=utf-8',
          '.css':'text/css; charset=utf-8','.json':'application/json; charset=utf-8',
          '.webp':'image/webp','.svg':'image/svg+xml'})[path.extname(file)]||'application/octet-stream';
        response.writeHead(200,{'content-type':mime,'cache-control':'no-store'});
        response.end(data)
      })
    }catch(error){response.writeHead(400).end('bad request')}
  });
  return new Promise(resolve=>server.listen(0,'127.0.0.1',
    ()=>resolve({server,base:'http://127.0.0.1:'+server.address().port})))
}
async function checkVariant(page,react){
  const card=page.locator('#list .ex').first();
  for(let attempt=0;attempt<5;attempt++){
    if(await card.evaluate(el=>el.classList.contains('kggOpen')))break;
    await card.locator('h3').click();
    await page.waitForTimeout(90)
  }
  assert(await card.evaluate(el=>el.classList.contains('kggOpen')),'synthetic card not open');
  const field=card.locator(':scope > .set').first()
    .locator(".kggCompactTapProxy[data-kgg-key='a']").first();
  await field.waitFor({state:'visible',timeout:8000});
  await field.click();
  await page.locator('#pad .padActions .padCancel').waitFor({state:'visible'});
  if(react)await page.locator("[data-kgg-react-numpad-header='v1']")
    .waitFor({state:'attached',timeout:8000});
  const mounted=await page.evaluate(()=>document.body.classList.contains('kggReactNumpadHeaderV1'));
  assert(mounted===react,'React/Legacy variant not truly mounted');
  await page.locator('#pad .padActions .padCancel').click();
  await page.locator('#pad').waitFor({state:'hidden'});
}
async function checkIncomingPlanChoices(browser,base,mode,sourcePlan){
  const context=await browser.newContext({viewport:{width:390,height:844},
    hasTouch:true,serviceWorkers:'block'});
  const page=await context.newPage();
  const errors=[];
  page.on('pageerror',error=>errors.push(error.message));
  const planA={...sourcePlan,i:'synthetic-link-a',t:'Synthetic Plan A',
    e:[['KGG Synthetic Original',1,'B','kg','Wdh']]};
  const planB={...sourcePlan,i:'synthetic-link-b',t:'Synthetic Plan B',
    e:[['KGG Synthetic Added',1,'B','kg','Wdh']]};
  const planC={...sourcePlan,i:'synthetic-link-c',t:'Synthetic Plan C',
    e:[['KGG Synthetic Replacement',1,'B','kg','Wdh']]};
  const modeQuery='?kggReactPad='+(mode==='react'?'1':'0')+'&plan=';
  const urlFor=(raw,format)=>base+'/index.html'+modeQuery+
    encodeURIComponent(codeFor(raw,format));
  try{
    await page.addInitScript(()=>localStorage.setItem('kggInstallAsked','1'));
    await page.goto(urlFor(planA,'KGGH2'),{waitUntil:'domcontentloaded',timeout:15000});
    await page.waitForFunction(()=>typeof p!=='undefined'&&p?.id==='synthetic-link-a'&&
      document.getElementById('status')?.textContent?.includes('importiert'),
      null,{timeout:12000});
    await page.evaluate(()=>put(0,1,'B','a','37'));
    assert(await page.evaluate(()=>v[k(0,1,'B','a',1)])==='37',
      'synthetic original plan value failed to persist');
    const state=()=>page.evaluate(()=>({
      current:JSON.parse(localStorage.getItem('kggCurrentPlanV1')||'null')?.plan?.i,
      multi:JSON.parse(localStorage.getItem('kggPatientMultiPlansV1')||'null'),
      active:typeof p==='undefined'?null:p.id,
      saved:localStorage.getItem('kggCurrentPlanV1')
    }));
    const choose=async(raw,format,choice)=>{
      await page.goto(urlFor(raw,format),{waitUntil:'domcontentloaded',timeout:15000});
      const dialog=page.locator('#kggPlanLinkChoiceBackdrop');
      await dialog.waitFor({state:'visible',timeout:12000});
      assert(await dialog.getByRole('dialog').count()===1,
        'link choice must be an accessible in-app dialog');
      assert(await dialog.getByRole('button',{name:'Als zusätzlichen Plan hinzufügen'}).count()===1,
        'link choice missing add action');
      assert(await dialog.getByRole('button',{name:'Aktiven Plan ersetzen'}).count()===1,
        'link choice missing replace action');
      await page.locator('#kggPlanLinkChoice'+choice).click();
      await dialog.waitFor({state:'detached',timeout:12000});
    };
    // CANCEL must not modify the active plan or silently add a slot.
    await choose(planB,'KGGH3','Cancel');
    let x=await state();
    assert(x.current===planA.i&&x.active===planA.i,
      'cancelling incoming link unexpectedly replaced the current plan');
    assert(!x.multi||x.multi.plans.every(z=>z.i!==planB.i),
      'cancelling incoming link added an unwanted plan');
    assert(await page.evaluate(()=>v[k(0,1,'B','a',1)])==='37',
      'cancel removed the original saved value');
    // ADD must preserve A in an independent saved plan slot.
    await choose(planB,'KGGH3','Add');
    // Additional plans deliberately receive unique -p IDs to isolate their state.
    await page.waitForFunction(sourceId=>{
      const next=JSON.parse(localStorage.getItem('kggCurrentPlanV1')||'null')?.plan;
      return typeof p!=='undefined'&&p?.id?.startsWith(sourceId+'-p') &&
        next?.sourcePlanId===sourceId&&next.i===p.id
    },planB.i,{timeout:12000});
    x=await state();
    assert(x.multi?.plans?.length===2&&x.current===x.active,
      'adding a second plan did not create exactly two consistent slots');
    assert(x.multi.plans.some(z=>z.i===planA.i)&&
      x.multi.plans.some(z=>z.sourcePlanId===planB.i&&z.i===x.active),
      'adding plan B overwrote plan A or omitted a unique new ID');
    // REPLACE affects active B only, not the preserved A slot.
    await choose(planC,'KGGH2','Replace');
    // Replacement deliberately receives a unique -r ID and sourcePlanId.
    await page.waitForFunction(sourceId=>{
      const next=JSON.parse(localStorage.getItem('kggCurrentPlanV1')||'null')?.plan;
      return typeof p!=='undefined'&&p?.id?.startsWith(sourceId+'-r') &&
        next?.sourcePlanId===sourceId&&next.i===p.id
    },planC.i,{timeout:12000});
    x=await state();
    assert(x.multi?.plans?.length===2&&x.current===x.active,
      'replacing active B changed total count or current/active identity');
    assert(x.multi.plans.some(z=>z.i===planA.i) &&
      x.multi.plans.some(z=>z.sourcePlanId===planC.i&&z.i===x.active) &&
      !x.multi.plans.some(z=>z.sourcePlanId===planB.i),
      'replace operation lost A, retained B or failed to assign a new ID');
    const switched=await page.evaluate(()=>window.KGGPatientMultiPlan.switchTo(0));
    assert(switched===true,'could not switch to preserved original plan');
    await page.waitForFunction(id=>typeof p!=='undefined'&&p?.id===id,
      planA.i,{timeout:10000});
    assert(await page.evaluate(()=>v[k(0,1,'B','a',1)])==='37',
      'add/replace/switch altered original plan A training values');
    await checkVariant(page,mode==='react');
    assert(errors.length===0,'link choice browser errors: '+JSON.stringify(errors));
    if(OUT){
      await page.screenshot({path:path.join(OUT,'link-'+mode+'.png'),animations:'disabled'});
      const proof={schema:1,status:'PASS',engine:ENGINE,mode,sourceSha:SHA,
        syntheticOnly:true,featureIds:['PAT-LINK-001','PAT-MULTI-002','PAT-SCAN-002'],
        assertions:{cancelPreservesActive:true,addPreservesOldPlan:true,
          activeReplaceOnly:true,savedValuesPreserved:true,uiDialog:true,
          reactOwnerVerified:true,noBrowserErrors:true},
        limitation:'Synthetic plan-link choices only; not live camera, UI plan deletion/rename or OS clipboard'};
      fs.writeFileSync(path.join(OUT,'link-'+mode+'.json'),JSON.stringify(proof,null,2)+'\n')
    }
    return {mode,status:'PASS',cancel:true,add:true,replace:true,
      originalValuePreserved:true};
  }finally{await context.close()}
}

async function checkPlanManagement(browser,base,mode,sourcePlan){
  const context=await browser.newContext({viewport:{width:390,height:844},
    hasTouch:true,serviceWorkers:'block'});
  const page=await context.newPage();
  const errors=[];
  page.on('pageerror',error=>errors.push(error.message));
  const planA={...sourcePlan,i:'synthetic-manage-a',t:'Synthetic Plan A',
    e:[['KGG Synthetic Manage A',1,'B','kg','Wdh']]};
  const planB={...sourcePlan,i:'synthetic-manage-b',t:'Synthetic Plan B',
    e:[['KGG Synthetic Manage B',1,'B','kg','Wdh']]};
  const state=()=>page.evaluate(()=>({
    multi:JSON.parse(localStorage.getItem('kggPatientMultiPlansV1')||'null'),
    current:JSON.parse(localStorage.getItem('kggCurrentPlanV1')||'null')?.plan,
    runtime:typeof p==='undefined'?null:{id:p.id,title:p.title},
    firstValue:typeof v==='undefined'?null:v[k(0,1,'B','a',1)]
  }));
  const openManager=async()=>{
    const fab=page.locator('#kggActionFab');
    await fab.waitFor({state:'visible',timeout:12000});
    await fab.click();
    await page.locator('#kggBubblePlans').waitFor({state:'visible',timeout:8000});
    await page.locator('#kggBubblePlans').click();
    const panel=page.locator('#kggPlanDeletePanel');
    await panel.waitFor({state:'visible',timeout:8000});
    return panel
  };
  try{
    await page.addInitScript(()=>localStorage.setItem('kggInstallAsked','1'));
    await page.goto(base+'/index.html?kggReactPad='+(mode==='react'?'1':'0')+
      '&plan='+encodeURIComponent(codeFor(planA,'KGGH2')),
      {waitUntil:'domcontentloaded',timeout:15000});
    await page.waitForFunction(id=>typeof p!=='undefined'&&p?.id===id,
      planA.i,{timeout:12000});
    await page.evaluate(()=>put(0,1,'B','a','51'));
    assert((await state()).firstValue==='51','plan-management seed not saved');
    const added=await page.evaluate(raw=>window.KGGPatientPlanSlots.addPlan(raw),planB);
    assert(added===true,'synthetic management setup did not add second plan');
    await page.waitForFunction(id=>{
      const multi=JSON.parse(localStorage.getItem('kggPatientMultiPlansV1')||'null');
      return multi?.plans?.length===2 && multi.active===1 &&
        multi.plans[1]?.sourcePlanId===id
    },planB.i,{timeout:12000});
    let panel=await openManager();
    assert(await panel.locator('.kggPlanManageCard').count()===2,
      'manage menu failed to show two plans');
    assert((await panel.locator('.kggPlanManageCard').nth(0).innerText()).includes('Gespeicherter Plan'),
      'inactive plan A is not correctly distinguished');
    assert((await panel.locator('.kggPlanManageCard').nth(1).innerText()).includes('Aktiver Plan'),
      'active plan B is not correctly marked');
    page.once('dialog',dialog=>{
      assert(dialog.type()==='prompt','rename action did not open a prompt');
      return dialog.accept('  Preserved  Plan A  ')
    });
    await panel.locator('.kggPlanRenameBtn[data-index="0"]').click();
    await page.waitForFunction(()=>{
      const s=JSON.parse(localStorage.getItem('kggPatientMultiPlansV1')||'null');
      return s?.plans?.[0]?.t==='Preserved Plan A'
    },null,{timeout:10000});
    await panel.waitFor({state:'hidden',timeout:10000});
    panel=await openManager();
    assert((await panel.locator('.kggPlanManageCard').first().innerText())
      .includes('Preserved Plan A'),'management list did not update renamed plan');
    if(OUT){
      fs.mkdirSync(OUT,{recursive:true});
      await page.screenshot({path:path.join(OUT,'manage-'+mode+'.png'),
        animations:'disabled'})
    }
    page.once('dialog',dialog=>{
      assert(dialog.type()==='confirm','delete action did not ask for confirmation');
      return dialog.dismiss()
    });
    await panel.locator('.kggPlanDeleteBtn[data-index="1"]').click();
    assert((await state()).multi?.plans?.length===2,
      'cancelled plan deletion changed plan count');
    page.once('dialog',dialog=>{
      assert(dialog.type()==='confirm','delete confirmation missing');
      return dialog.accept()
    });
    await panel.locator('.kggPlanDeleteBtn[data-index="1"]').click();
    const afterDelete=()=>page.evaluate(()=>{
      const saved=JSON.parse(localStorage.getItem('kggPatientMultiPlansV1')||'null');
      const current=JSON.parse(localStorage.getItem('kggCurrentPlanV1')||'null')?.plan;
      return {remainingIds:saved?.plans?.map(x=>x.i),activeIndex:saved?.active,
        activeLexical:typeof p==='undefined'?null:{id:p.id,title:p.title},
        windowPlan:window.p?{id:window.p.id,title:window.p.title}:null,
        currentId:current?.i,renderedTitle:document.getElementById('title')?.textContent,
        valuesLexical:typeof v==='undefined'?null:v[k(0,1,'B','a',1)],
        valuesWindow:window.v?.['1|0|1|B|a']??null};
    });
    try{
      await page.waitForFunction(id=>{
        const s=JSON.parse(localStorage.getItem('kggPatientMultiPlansV1')||'null');
        return s?.plans?.length===1 && s.plans[0]?.i===id
      },planA.i,{timeout:12000});
    }catch(error){
      throw new Error('Deleting active plan failed to update saved plan slots: '+
        JSON.stringify(await afterDelete())+'; original='+error.message);
    }
    const snapshot=await afterDelete();
    assert(snapshot.activeLexical?.id===planA.i&&
      snapshot.activeLexical?.title==='Preserved Plan A'&&
      snapshot.renderedTitle==='Preserved Plan A',
      'Deleting active plan left a stale runtime/display: '+JSON.stringify(snapshot));
    const final=await state();
    assert(final.firstValue==='51',
      'rename/delete changed original plan A training value');
    assert(final.current?.i===planA.i,
      'deleting active B failed to restore original Plan A');
    panel=await openManager();
    assert(await panel.locator('.kggPlanDeleteBtn').count()===0,
      'last remaining plan exposes destructive delete action');
    await panel.locator('.kggPlanManageClose').click();
    await checkVariant(page,mode==='react');
    assert(errors.length===0,'plan management browser errors: '+JSON.stringify(errors));
    if(OUT){
      const proof={schema:1,status:'PASS',engine:ENGINE,mode,sourceSha:SHA,
        syntheticOnly:true,
        featureIds:['PAT-MULTI-001','PAT-MULTI-004','PAT-MULTI-005',
          'PAT-MULTI-006','PAT-DEL-001'],
        assertions:{actionMenu:true,activePlanLabel:true,renamePersists:true,
          cancelDeletePreservesPlans:true,deleteActiveRestoresOther:true,
          originalValuePreserved:true,cannotDeleteLastPlan:true,
          reactOwnerVerified:true,noBrowserErrors:true},
        limitation:'Synthetic plan-management UI (rename/delete plan only); not exercise deletion or real media cleanup'};
      fs.writeFileSync(path.join(OUT,'manage-'+mode+'.json'),JSON.stringify(proof,null,2)+'\n')
    }
    return {mode,status:'PASS',renamed:true,cancelDeletion:true,
      deletedActive:true,preservedOriginal:true};
  }finally{await context.close()}
}

async function main(){
  const raw={v:1,i:'scanner-v81',t:'SYNTHETIC Scan Contract',d:6,stepDays:6,
    extendDays:true,e:[
      ['KGG Synthetic Scan Pair',3,'BI','kg','Wdh'],
      ['KGG Synthetic Scan LR',2,'LR','kg','Wdh'],
      ['KGG Synthetic Scan Other',4,'BI','kg','Wdh']
    ]};
  const {server,base}=await startServer();
  const browser=await ({chromium,webkit})[ENGINE].launch({headless:true});
  const results=[];
  try{
    for(const mode of ['legacy','react']){
      for(const format of ['KGGH2','KGGH3']){
        const code=codeFor(raw,format);
        const context=await browser.newContext({viewport:{width:390,height:844},
          hasTouch:true,serviceWorkers:'block'});
        const page=await context.newPage();
        const errors=[];
        page.on('pageerror',error=>errors.push(error.message));
        try{
          await page.addInitScript(()=>localStorage.setItem('kggInstallAsked','1'));
          await page.goto(base+'/index.html?kggReactPad='+(mode==='react'?'1':'0')+
            '&plan='+encodeURIComponent(code),{waitUntil:'domcontentloaded',timeout:15000});
          await page.waitForFunction(()=>window.__kggPatientStartScanTest&&
            document.getElementById('status'),null,{timeout:12000});
          await page.waitForFunction(()=>String(document.getElementById('status')
            ?.textContent||'').includes('importiert'),null,{timeout:12000});
          const state=await page.evaluate(({code,raw,base})=>{
            const api=window.__kggPatientStartScanTest;
            const before=localStorage.getItem('kggCurrentPlanV1');
            const parsed=api.parsePlanFromText(code);
            const fromUrl=api.parsePlanFromText(base+'/index.html?plan='+encodeURIComponent(code));
            const fromHash=api.parsePlanFromText('#'+code);
            const damaged=api.parsePlanFromText('KGGH3:AAAA');
            const invalidResult=window.KGGPatientPlanImport.replaceConfirmed({i:'bad',e:[[]]});
            return {payload:api.planPayloadFromText(code),parsed,fromUrl,fromHash,
              damaged,invalidResult,unchanged:before===localStorage.getItem('kggCurrentPlanV1'),
              before,cards:document.querySelectorAll('#list .ex').length,
              status:document.getElementById('status')?.textContent||''}
          },{code,raw,base});
          assert(state.payload===code,format+' scanner returned wrong payload');
          assert(JSON.stringify(state.parsed)===JSON.stringify(raw),format+' parser changed plan');
          assert(JSON.stringify(state.fromUrl)===JSON.stringify(raw)&&
            JSON.stringify(state.fromHash)===JSON.stringify(raw),format+' URL/hash parser failed');
          assert(state.damaged===null,format+' damaged text accepted');
          assert(state.invalidResult===false&&state.unchanged,
            format+' invalid replacement changed stored plan');
          assert(state.cards===raw.e.length,format+' rendered wrong exercise count');
          await checkVariant(page,mode==='react');
          assert((await page.evaluate(()=>localStorage.getItem('kggCurrentPlanV1')))===state.before,
            'opening/cancelling NumPad changed saved plan');
          assert(errors.length===0,'unexpected page errors: '+JSON.stringify(errors));
          if(OUT&&format==='KGGH3'){
            fs.mkdirSync(OUT,{recursive:true});
            await page.screenshot({path:path.join(OUT,'scan-'+mode+'.png'),
              animations:'disabled'})
          }
          results.push({engine:ENGINE,mode,format,cards:state.cards,payloadLength:state.payload.length,
            imported:true,planRetained:true,variantMounted:true})
        }finally{await context.close()}
      }
      if(OUT){
        const modeResults=results.filter(row=>row.mode===mode);
        assert(modeResults.length===2,'missing one parser format in '+mode);
        const proof={schema:1,status:'PASS',syntheticOnly:true,engine:ENGINE,
          mode,sourceSha:SHA,featureIds:['PAT-IMPORT-001','PAT-IMPORT-002'],
          assertions:{h2Imported:true,h3Imported:true,urlHashAccepted:true,
            invalidPlanRejected:true,existingPlanPreserved:true,
            exerciseCardsCorrect:true,reactOwnerVerified:true,noBrowserErrors:true},
          limitation:'Synthetic H2/H3 link/text import only; NOT live camera, photo upload or physical QR scanning'};
        fs.writeFileSync(path.join(OUT,'scan-'+mode+'.json'),JSON.stringify(proof,null,2)+'\n')
      }
    }
    const planLinkChoices=[];
    for(const mode of ['legacy','react']){
      planLinkChoices.push(await checkIncomingPlanChoices(browser,base,mode,raw));
    }
    const management=[];
    for(const mode of ['legacy','react']){
      management.push(await checkPlanManagement(browser,base,mode,raw));
    }
    assert(results.length===4,'missing engine/mode/format coverage');
    console.log(JSON.stringify({status:'PASS',engine:ENGINE,syntheticOnly:true,sourceSha:SHA,results,planLinkChoices,management}))
  }finally{
    await browser.close();
    if(typeof server.closeAllConnections==='function')server.closeAllConnections();
    await Promise.race([new Promise(resolve=>server.close(()=>resolve())),
      new Promise(resolve=>setTimeout(resolve,2000))])
  }
}
const alarm=setTimeout(()=>{console.error('KGG scan format parity: bounded 120s timeout');process.exit(124)},120000);
main().then(()=>clearTimeout(alarm)).catch(error=>{
  clearTimeout(alarm);console.error('KGG scan format parity FAIL: '+(error.stack||error));process.exitCode=1
});
