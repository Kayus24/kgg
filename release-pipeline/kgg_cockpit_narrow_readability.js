"use strict";
const fs=require('fs'),path=require('path');
const {chromium}=require('playwright');
const {pathToFileURL}=require('url');
const root=path.resolve(__dirname,'..');
const dir=path.join(process.env.KGG_SMOKE_SCREENSHOT_DIR||path.join(root,'tmp/cockpit-layout-canaries'),'narrow-readability');fs.mkdirSync(dir,{recursive:true});
(async()=>{
 const browser=await chromium.launch();const results=[];
 try{for(const width of [760,820,1024,1280,1440]){
  const viewport={width,height:width<1000?1180:800};
  const context=await browser.newContext({viewport,screen:viewport,isMobile:true,hasTouch:true});
  await context.route(/^https?:\/\//,r=>r.abort());const page=await context.newPage();
  await page.addInitScript(()=>{localStorage.setItem('kgg_pwa_install_prompt_seen_v1','synthetic');localStorage.setItem('kgg_html_app_v2_state',JSON.stringify({planId:'synthetic-readability',patient:{name:'Synthetic',date:'2026-10-01'},plan:[{id:'synthetic-ex',localId:'synthetic-ex',name:'Abduktion Maschine',sets:2,side:'BI',loadUnit:'kg',metricUnit:'Wdh',today:[],previous:[],media:[],progressionVariants:[]}]}));});
  await page.goto(pathToFileURL(path.join(root,'kgg-update/index.html')).href);
  await page.locator('#adminSecretsModal.open').waitFor();await page.locator('#closeAdminSecrets').tap();
  await page.evaluate(()=>{const a=window.KGGTherapyCockpit;for(let i=0;i<2;i++)a.importCode(a.encode({planId:'synthetic-slot-'+i,name:'Synthetic '+i,exercises:a.registry.entries().slice(0,2).map(e=>({id:e.id,sets:2}))}));});
  await page.waitForFunction(()=>document.body.classList.contains('kggTcSlots2'));
  const data=await page.evaluate(()=>{const n=document.querySelector('#planList .planName'),s=getComputedStyle(n),r=n.getBoundingClientRect(),app=document.querySelector('.app'),actions=[...document.querySelectorAll('#planList .planCardActions button')].map(b=>{const r=b.getBoundingClientRect();return {w:r.width,h:r.height,x:r.x,y:r.y,right:r.right,bottom:r.bottom};});return {whiteSpace:s.whiteSpace,titleWidth:r.width,titleHeight:r.height,lineHeight:parseFloat(s.lineHeight),paneWidth:app.getBoundingClientRect().width,overflow:app.scrollWidth>app.clientWidth+1,actions};});
  const readable=data.whiteSpace==='nowrap'&&data.titleHeight<=data.lineHeight*1.5&&data.titleWidth>=100;
  const targets=data.actions.every(a=>a.w>=44&&a.h>=44)&&data.actions.length===2&&!(data.actions[0].x<data.actions[1].right&&data.actions[0].right>data.actions[1].x&&data.actions[0].y<data.actions[1].bottom&&data.actions[0].bottom>data.actions[1].y);
  const result={width,status:readable&&targets&&!data.overflow?'PASS':'FAIL',...data};results.push(result);console.log(JSON.stringify(result));
  await page.screenshot({path:path.join(dir,`narrow-${'actual'}-${width}.png`)});await context.close();
 }}finally{await browser.close();}
 fs.writeFileSync(path.join(dir,`narrow-${'actual'}-report.json`),JSON.stringify({sha256:require('crypto').createHash('sha256').update(fs.readFileSync(path.join(root,'kgg-update/index.html'))).digest('hex'),results},null,2));
 if(results.some(r=>r.status==='FAIL'))process.exitCode=1;
})().catch(e=>{console.error(e.stack);process.exitCode=1;});
