"use strict";
const fs=require('fs'),path=require('path');const {chromium}=require('playwright');const {pathToFileURL}=require('url');const root=path.resolve(__dirname,'..');
const dir=path.join(process.env.KGG_SMOKE_SCREENSHOT_DIR||path.join(root,'tmp/cockpit-layout-canaries'),'main-phone-flow');fs.mkdirSync(dir,{recursive:true});
(async()=>{const browser=await chromium.launch();const results=[];
 try{for(const [width,height] of [[1024,800],[1024,861],[1100,800],[1101,800],[1280,800],[820,1180],[1024,768]]){
  const viewport={width,height},context=await browser.newContext({viewport,screen:viewport,isMobile:true,hasTouch:true});await context.route(/^https?:\/\//,r=>r.abort());const page=await context.newPage();page.setDefaultTimeout(4000);const errors=[];page.on('pageerror',e=>errors.push(e.message));
  await page.addInitScript(()=>{localStorage.setItem('kgg_pwa_install_prompt_seen_v1','synthetic');localStorage.setItem('kgg_html_app_v2_state',JSON.stringify({planId:'synthetic-main-phone',patient:{name:'Synthetic',date:'2026-10-01'},plan:[{id:'synthetic-ex',localId:'synthetic-ex',name:'Abduktion Maschine',sets:2,side:'BI',loadUnit:'kg',metricUnit:'Wdh',today:[],previous:[],media:[],progressionVariants:[]}]}));});
  await page.goto(pathToFileURL(path.join(root,'kgg-update/index.html')).href);await page.locator('#adminSecretsModal.open').waitFor();await page.locator('#closeAdminSecrets').tap();
  await page.evaluate(()=>{const a=window.KGGTherapyCockpit;for(let i=0;i<2;i++)a.importCode(a.encode({planId:'synthetic-slot-'+i,name:'Synthetic '+i,exercises:a.registry.entries().slice(0,2).map(e=>({id:e.id,sets:2}))}));});
  const result={width,height,checks:[]},test=async(name,fn)=>{try{await fn();result.checks.push({name,status:'PASS'});}catch(e){result.checks.push({name,status:'FAIL',error:e.message});await page.screenshot({path:path.join(dir,`main-phone-${width}x${height}-${name}.png`)});}};
  const before=await page.evaluate(()=>{const p=window.KGGDataStore.getCurrentPlan();return JSON.stringify({id:p.id,patient:p.patient,exercises:p.exercises});});
  await test('plan-package-scanner-unforced-targets',async()=>{
    const targets={};
    // Bank is independently covered by real open/close taps; its center can be clipped before Playwright scrolls it into view.
    for(const id of ['currentPlanToggle','packageToggle','scanBtn','baseToggle','recentToggle']){
      await page.locator('#'+id).scrollIntoViewIfNeeded();
      targets[id]=await page.evaluate(id=>{
        const element=document.getElementById(id),rect=element.getBoundingClientRect(),x=rect.left+rect.width/2,y=rect.top+rect.height/2,hit=document.elementFromPoint(x,y);
        return {rect:{x:rect.x,y:rect.y,width:rect.width,height:rect.height},hit:hit?.closest('button')?.id||hit?.id||null};
      },id);
      if(targets[id].hit!==id)throw new Error(id+' pointer intercepted after scroll: '+JSON.stringify(targets));
    }
    result.hitTargets=targets;
    const current=page.locator('#currentPlanToggle');
    await current.tap();
    if(await current.getAttribute('aria-expanded')!=='true')throw new Error('currentPlanToggle did not select current plan');
    await page.locator('#planList:visible').waitFor();
    const afterCurrent=await page.evaluate(()=>{const p=window.KGGDataStore.getCurrentPlan();return JSON.stringify({id:p.id,patient:p.patient,exercises:p.exercises});});
    if(afterCurrent!==before)throw new Error('currentPlanToggle mutated plan state');
    await page.evaluate(()=>{window.__kggSyntheticScanTaps=0;document.getElementById('scanBtn').addEventListener('click',()=>window.__kggSyntheticScanTaps++,{capture:true});});
    await page.locator('#scanBtn').tap();
    if(await page.evaluate(()=>window.__kggSyntheticScanTaps)!==1)throw new Error('scanner did not receive real tap');
  });
  await test('phone-presentation',async()=>{await page.waitForFunction(()=>document.body.classList.contains('kggTcMainPanePhone')&&document.body.classList.contains('kggPhoneHasPlan')&&!document.body.classList.contains('tabletLayoutCustom'));await page.locator('#bankContent.hidden').waitFor({state:'hidden'});});
  await test('bank-open-close',async()=>{await page.locator('#bankToggle').tap();await page.locator('#bankContent:not(.hidden)').waitFor();await page.locator('#bankToggle').tap();await page.locator('#bankContent').waitFor({state:'hidden'});});
  await test('base-open-close',async()=>{await page.locator('#baseToggle').tap();await page.locator('#baseFields:not(.hidden)').waitFor();await page.locator('#baseToggle').tap();await page.locator('#baseFields').waitFor({state:'hidden'});});
  for(const [button,list] of [['recentToggle','recentList'],['packageToggle','packageList']])await test(button+'-open-close',async()=>{await page.locator('#'+button).tap();await page.locator('#'+list+':not(.hidden)').waitFor();await page.locator('#'+button).tap();await page.locator('#'+list).waitFor({state:'hidden'});});
  await test('editor-close',async()=>{await page.locator('#planList [data-planedit]').first().tap();await page.locator('#editorModal.open').waitFor();await page.locator('#closeEditor').tap();await page.locator('#editorModal').waitFor({state:'hidden'});});
  await test('finish-cancel',async()=>{const finish=page.locator('#finishBtn');await finish.scrollIntoViewIfNeeded();const r=await finish.boundingBox();const hit=await page.evaluate(([x,y])=>document.elementFromPoint(x,y)?.closest('button')?.id||null,[r.x+r.width/2,r.y+r.height/2]);if(hit!=='finishBtn')throw new Error('finish target intercepted by '+hit);await finish.tap();await page.locator('#shareModal.open').waitFor();await page.locator('#finishCancelBtn').tap();await page.locator('#shareModal').waitFor({state:'hidden'});const after=await page.evaluate(()=>{const p=window.KGGDataStore.getCurrentPlan();return JSON.stringify({id:p.id,patient:p.patient,exercises:p.exercises});});if(after!==before)throw new Error('finish cancel mutated plan state');});
  result.geometry=await page.evaluate(()=>{const out={};for(const id of ['packageLayoutSlot','packageToggle','planActions','panelTitle','savePackageBtn']){const e=document.getElementById(id),s=getComputedStyle(e),r=e.getBoundingClientRect();out[id]={style:e.getAttribute('style'),display:s.display,position:s.position,width:s.width,x:r.x,y:r.y};}return out;});
  await test('package-four-edge-taps',async()=>{
    const toggle=page.locator('#packageToggle'),list=page.locator('#packageList');
    const points=[['center',.5,.5],['lower75',.5,.75],['lower95',.5,.95],['right95',.8,.95]];
    const evidence=[];
    for(const [name,fx,fy] of points){
      await toggle.scrollIntoViewIfNeeded();
      const box=await toggle.boundingBox();
      const position={x:box.width*fx,y:box.height*fy};
      const hit=await page.evaluate(([x,y])=>document.elementFromPoint(x,y)?.closest('button')?.id||null,[box.x+position.x,box.y+position.y]);
      evidence.push({name,hit,x:box.x+position.x,y:box.y+position.y});
      if(hit!=='packageToggle')throw new Error(name+' package edge intercepted: '+JSON.stringify(evidence));
      await toggle.tap({position});
      await page.locator('#packageList:not(.hidden)').waitFor();
      await toggle.tap({position});
      await list.waitFor({state:'hidden'});
    }
    result.packageEdges=evidence;
    const after=await page.evaluate(()=>{const p=window.KGGDataStore.getCurrentPlan();return JSON.stringify({id:p.id,patient:p.patient,exercises:p.exercises});});
    if(after!==before)throw new Error('package edge taps mutated current plan');
  });
  await test('return-preserves-state',async()=>{await page.locator('#kggTherapyCockpitButton').tap();await page.waitForFunction(()=>!document.body.classList.contains('kggTcMainPanePhone')&&document.body.classList.contains('tabletLayoutCustom'));const after=await page.evaluate(()=>{const p=window.KGGDataStore.getCurrentPlan();return {plan:JSON.stringify({id:p.id,patient:p.patient,exercises:p.exercises}),count:window.KGGTherapyCockpit.getState().slots.filter(Boolean).length};});if(after.plan!==before||after.count!==2)throw new Error('layout switch changed a plan');});
  result.errors=errors;result.status=result.checks.every(c=>c.status==='PASS')&&errors.length===0?'PASS':'FAIL';results.push(result);console.log(JSON.stringify(result));await context.close();
 }}finally{await browser.close();}fs.writeFileSync(path.join(dir,`main-phone-flow-${'actual'}-report.json`),JSON.stringify({sha256:require('crypto').createHash('sha256').update(fs.readFileSync(path.join(root,'kgg-update/index.html'))).digest('hex'),results},null,2));if(results.some(r=>r.status==='FAIL'))process.exitCode=1;
})().catch(e=>{console.error(e.stack);process.exitCode=1;});
