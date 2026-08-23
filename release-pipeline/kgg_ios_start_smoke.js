#!/usr/bin/env node
'use strict';

const fs=require('fs'),http=require('http'),path=require('path');
const {chromium}=require('playwright');
const ROOT=path.resolve(__dirname,'..');

function assert(condition,message){if(!condition)throw new Error(message)}
function codeFor(raw,format){
  const json=Buffer.from(JSON.stringify(raw),'utf8');
  if(format==='KGGH2')return 'KGGH2:'+json.toString('base64url');
  const fflate=require(path.join(ROOT,'vendor','fflate-0.8.3.js'));
  return 'KGGH3:'+Buffer.from(fflate.zlibSync(json)).toString('base64url');
}
function startServer(){
  const server=http.createServer((request,response)=>{
    try{
      const pathname=decodeURIComponent(new URL(request.url,'http://127.0.0.1').pathname);
      const relative=pathname==='/'?'index.html':pathname.replace(/^\//,'');
      const file=path.resolve(ROOT,relative);
      if(file!==ROOT&&!file.startsWith(ROOT+path.sep)){response.writeHead(403);response.end();return}
      fs.readFile(file,(error,data)=>{
        if(error){response.writeHead(404);response.end('not found');return}
        const type=file.endsWith('.html')?'text/html; charset=utf-8':file.endsWith('.js')?'text/javascript; charset=utf-8':'application/octet-stream';
        response.writeHead(200,{'content-type':type,'cache-control':'no-store'});response.end(data);
      });
    }catch(error){response.writeHead(400);response.end('bad request')}
  });
  return new Promise(resolve=>server.listen(0,'127.0.0.1',()=>resolve({server,base:'http://127.0.0.1:'+server.address().port})));
}

(async()=>{
  const raw={v:1,i:'ios-v81-synthetic',t:'iOS Start Test',d:6,stepDays:1,extendDays:true,p:{name:'Synthetisch'},e:[['Beinpresse',3,'BI','kg','Wdh','12',''],['Rudern',2,'LR','kg','Wdh','10',''],['Latziehen',4,'BI','kg','Wdh','8','']]};
  const {server,base}=await startServer();
  const browser=await chromium.launch({headless:true});
  const results=[];
  try{
    for(const format of ['KGGH2','KGGH3']){
      const context=await browser.newContext();
      const page=await context.newPage();
      const external=[];
      page.on('request',request=>{if(!request.url().startsWith(base))external.push(request.url())});
      const code=codeFor(raw,format);
      await page.goto(base+'/ios-start.html?plan='+encodeURIComponent(code),{waitUntil:'domcontentloaded'});
      await page.waitForSelector('#status',{timeout:10000});
      await page.waitForFunction(()=>String(document.getElementById('status')?.textContent||'').includes('übernommen'),null,{timeout:10000});
      const state=await page.evaluate(()=>{
        let stored=null;try{stored=JSON.parse(localStorage.getItem('kggCurrentPlanV1')||'null')}catch(error){}
        return {url:location.href,status:document.getElementById('status')?.textContent||'',cards:document.querySelectorAll('#list .ex').length,storedId:stored?.plan?.i||'',storedExercises:stored?.plan?.e?.length||0};
      });
      assert(state.storedId===raw.i,format+' iOS flow stored the wrong plan');
      assert(state.storedExercises===raw.e.length,format+' iOS flow lost exercises');
      assert(state.cards===raw.e.length,format+' iOS flow rendered the wrong card count');
      assert(!/[?#](?:plan|kgg|KGGH[23])/.test(new URL(state.url).search+new URL(state.url).hash),format+' sensitive start input remained visible');
      results.push({format,status:state.status,cards:state.cards,url:state.url,externalRequests:external.length});
      await context.close();
    }
    console.log(JSON.stringify({status:'PASS',iosStart:true,results}));
  }finally{await browser.close();await new Promise(resolve=>server.close(resolve))}
})().catch(error=>{console.error(error.stack||error);process.exitCode=1});
