#!/usr/bin/env node
'use strict';

const fs=require('fs'),http=require('http'),path=require('path');
const {chromium}=require('playwright');
const ROOT=path.resolve(__dirname,'..');
function assert(condition,message){if(!condition)throw new Error(message)}
function codeFor(raw,format){const json=Buffer.from(JSON.stringify(raw),'utf8');if(format==='KGGH2')return 'KGGH2:'+json.toString('base64url');const fflate=require(path.join(ROOT,'vendor','fflate-0.8.3.js'));return 'KGGH3:'+Buffer.from(fflate.zlibSync(json)).toString('base64url')}
function startServer(){
  const server=http.createServer((request,response)=>{
    try{
      const pathname=decodeURIComponent(new URL(request.url,'http://127.0.0.1').pathname),relative=pathname==='/'?'index.html':pathname.replace(/^\//,'');
      const file=path.resolve(ROOT,relative);
      if(file!==ROOT&&!file.startsWith(ROOT+path.sep)){response.writeHead(403);response.end();return}
      fs.readFile(file,(error,data)=>{if(error){response.writeHead(404);response.end('not found');return}const type=file.endsWith('.html')?'text/html; charset=utf-8':file.endsWith('.js')?'text/javascript; charset=utf-8':'application/octet-stream';response.writeHead(200,{'content-type':type,'cache-control':'no-store'});response.end(data)});
    }catch(error){response.writeHead(400);response.end('bad request')}
  });
  return new Promise(resolve=>server.listen(0,'127.0.0.1',()=>resolve({server,base:'http://127.0.0.1:'+server.address().port})));
}

(async()=>{
  const raw={v:1,i:'scanner-v81',t:'Scanner Test',d:6,stepDays:6,extendDays:true,e:[['Beinpresse',3,'BI','kg','Wdh'],['Rudern',2,'LR','kg','Wdh'],['Latziehen',4,'BI','kg','Wdh']]};
  const {server,base}=await startServer();
  const browser=await chromium.launch({headless:true});
  const results=[];
  try{
    for(const format of ['KGGH2','KGGH3']){
      const code=codeFor(raw,format),context=await browser.newContext(),page=await context.newPage();
      await page.goto(base+'/index.html?plan='+encodeURIComponent(code),{waitUntil:'domcontentloaded'});
      await page.waitForFunction(()=>window.__kggPatientStartScanTest&&document.getElementById('status'),null,{timeout:10000});
      await page.waitForFunction(()=>String(document.getElementById('status')?.textContent||'').includes('importiert'),null,{timeout:10000});
      const state=await page.evaluate(({code,raw,base})=>{
        const api=window.__kggPatientStartScanTest;
        const parsed=api.parsePlanFromText(code),fromUrl=api.parsePlanFromText(base+'/index.html?plan='+encodeURIComponent(code)),fromHash=api.parsePlanFromText('#'+code),damaged=api.parsePlanFromText('KGGH3:AAAA');
        const before=localStorage.getItem('kggCurrentPlanV1'),invalidResult=window.KGGPatientPlanImport.replaceConfirmed({i:'bad',e:[[]]}),after=localStorage.getItem('kggCurrentPlanV1');
        return {payload:api.planPayloadFromText(code),parsed,fromUrl,fromHash,damaged,invalidResult,unchanged:before===after,cards:document.querySelectorAll('#list .ex').length,status:document.getElementById('status')?.textContent||''};
      },{code,raw,base});
      assert(state.payload===code,format+' scanner returned the wrong code');
      assert(JSON.stringify(state.parsed)===JSON.stringify(raw),format+' scanner parser changed plan data');
      assert(JSON.stringify(state.fromUrl)===JSON.stringify(raw)&&JSON.stringify(state.fromHash)===JSON.stringify(raw),format+' URL/hash scanner input failed');
      assert(state.damaged===null,format+' damaged scanner input was accepted');
      assert(state.invalidResult===false&&state.unchanged,format+' invalid replacement changed the stored plan');
      assert(state.cards===raw.e.length,format+' root rendered the wrong exercise count');
      results.push({format,status:state.status,cards:state.cards,payloadLength:state.payload.length});
      await context.close();
    }
    console.log(JSON.stringify({status:'PASS',patientScanFormat:true,results}));
  }finally{await browser.close();await new Promise(resolve=>server.close(resolve))}
})().catch(error=>{console.error(error.stack||error);process.exitCode=1});
