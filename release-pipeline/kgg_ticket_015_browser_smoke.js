#!/usr/bin/env node
'use strict';

// Ticket 015 browser loop: gallery selection, zero-value recording, dominance and notes.
// Local preview only; service workers are disabled so the test cannot touch a live release.

const fs=require('fs');
const http=require('http');
const path=require('path');
const {chromium}=require('playwright');

const ROOT=path.resolve(__dirname,'..');
function fail(message){throw new Error(message)}
function assert(condition,message){if(!condition)fail(message)}
function encodePlan(plan){return Buffer.from(JSON.stringify(plan),'utf8').toString('base64url')}
function contentType(file){return {'.html':'text/html; charset=utf-8','.js':'text/javascript; charset=utf-8','.json':'application/json; charset=utf-8','.png':'image/png'}[path.extname(file).toLowerCase()]||'application/octet-stream'}
function safeFile(urlPath){const relative=decodeURIComponent(String(urlPath||'/').split('?')[0]).replace(/^\/+/, '')||'index.html';const target=path.resolve(ROOT,relative);if(!target.startsWith(ROOT+path.sep)&&target!==ROOT)return null;if(!fs.existsSync(target)||!fs.statSync(target).isFile())return null;return target}

async function main(){
  const server=http.createServer((request,response)=>{const file=safeFile(request.url);if(!file){response.writeHead(404);response.end('not found');return}response.writeHead(200,{'Content-Type':contentType(file),'Cache-Control':'no-store','Service-Worker-Allowed':'/'});fs.createReadStream(file).pipe(response)});
  await new Promise(resolve=>server.listen(0,'127.0.0.1',resolve));
  const port=server.address().port;
  const browser=await chromium.launch({headless:true});
  const context=await browser.newContext({viewport:{width:390,height:844},serviceWorkers:'block'});
  const page=await context.newPage();
  const errors=[];page.on('pageerror',error=>errors.push(error.message));
  const plan={i:'ticket-015-browser',t:'Progressions-Testplan',v:1,d:6,e:[[
    'Kniebeuge',2,'B','kg','Wdh','','',[], '', '',
    {g:'progression-group-1',v:[
      {i:'easy',n:'Leichter',o:0,s:'',m:[]},
      {i:'base',n:'Basis',o:1,s:'',m:[]},
      {i:'hard',n:'Schwerer',o:2,s:'',m:[]},
    ]},
  ]]};
  const url=`http://127.0.0.1:${port}/?plan=KGGH2:${encodePlan(plan)}`;
  try{
    await page.goto(url,{waitUntil:'networkidle'});
    const card=page.locator('#list .ex').first();await card.waitFor({state:'visible'});await card.locator('h3').click();
    await page.locator('.kgg015Gallery').first().waitFor({state:'visible'});
    assert(await page.locator('.kgg015Gallery').count()===2,'one progression gallery per set was not rendered');
    assert((await page.locator('.kgg015Gallery').first().locator('.kgg015GalleryStage').innerText()).includes('Leichter'),'first set did not start at the easier stage');

    await page.locator('.kgg015Gallery').first().locator('[data-kgg015-next]').click();
    await page.waitForFunction(()=>document.querySelector('.kgg015Gallery')?.textContent.includes('Basis'));
    await page.locator('.kgg015Gallery').first().locator('[data-kgg015-next]').click();
    await page.waitForFunction(()=>document.querySelector('.kgg015Gallery')?.textContent.includes('Schwerer'));
    await page.evaluate(()=>{window.put(0,1,'B','a','0');window.put(0,1,'B','b','0');window.put(0,1,'B','a','0');});
    await page.evaluate(()=>window.put(0,2,'B','a','0'));
    const afterZero=await page.evaluate(()=>JSON.parse(localStorage.getItem('kggProgressionHistoryV1')||'{}'));
    assert(afterZero.current&&Object.keys(afterZero.current.records||{}).length===2,'zero-value edits did not create exactly one record per set');
    assert(afterZero.current.records['0|1'].id==='hard','selected hard stage was not recorded for set 1');
    assert(afterZero.current.records['0|2'].id==='easy','default easy stage was not recorded for set 2');

    await page.evaluate(()=>window.showQr(true));
    await page.waitForTimeout(120);
    const afterFinish=await page.evaluate(()=>JSON.parse(localStorage.getItem('kggProgressionHistoryV1')||'{}'));
    assert(afterFinish.groups['progression-group-1'].dominantId==='hard','dominant tie did not choose the higher stage');
    assert((await card.locator('h3').innerText())==='Schwerer','dominant stage did not become the displayed exercise name');

    await page.locator('.kgg015Gallery').first().locator('[data-kgg015-prev]').click();
    await page.evaluate(()=>window.put(0,1,'B','a','0'));
    await page.evaluate(()=>window.showQr(false));
    await page.waitForTimeout(80);
    assert((await page.locator('#sum').innerText()).includes('Variantenwechsel:'),'actual stage change was missing from documentation');
    assert(errors.length===0,`patient preview raised page errors: ${errors.join(' | ')}`);
    console.log('Ticket 015 browser smoke: OK');
  }finally{await browser.close();await new Promise(resolve=>server.close(resolve))}
}

main().catch(error=>{console.error(error.stack||error);process.exitCode=1});
