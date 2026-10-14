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
    assert(results.length===4,'missing engine/mode/format coverage');
    console.log(JSON.stringify({status:'PASS',engine:ENGINE,syntheticOnly:true,sourceSha:SHA,results}))
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
