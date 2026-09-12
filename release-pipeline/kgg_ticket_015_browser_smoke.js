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
  const stageMedia='data:image/svg+xml,'+encodeURIComponent('<svg xmlns="http://www.w3.org/2000/svg" width="120" height="80"><rect width="120" height="80" fill="#dbeafe"/><circle cx="60" cy="40" r="22" fill="#2563eb"/></svg>');
  const plan={i:'ticket-015-browser',t:'Progressions-Testplan',v:1,d:6,e:[[
    'Kniebeuge',2,'B','kg','Wdh','','',[], '', '', 'exercise',
    {g:'progression-group-1',v:[
      {i:'easy',n:'Leichter',o:0,s:'',m:[{id:'easy-media',type:'image',src:stageMedia}]},
      {i:'base',n:'Basis',o:1,s:'',m:[{id:'base-media',type:'image',src:stageMedia}]},
      {i:'hard',n:'Schwerer',o:2,s:'',m:[{id:'hard-media',type:'image',src:stageMedia}]},
    ]},
  ]]};
  const url=`http://127.0.0.1:${port}/?plan=KGGH2:${encodePlan(plan)}`;
  try{
    await page.goto(url,{waitUntil:'domcontentloaded'});
    const card=page.locator('#list .ex').first();await card.waitFor({state:'visible'});await card.locator('h3').click();
    await page.locator('.kgg015MainPager').first().waitFor({state:'visible'});
    assert(await page.locator('.kgg015Gallery').count()===0,'legacy per-set progression galleries must not remain visible');
    assert(await page.locator('.kgg015MainProgressionThumb').count()===3,'all progression stages must be shown as main-image thumbnails');
    assert(await page.locator('.kgg015MainProgressionThumb[aria-current="true"]').count()===1,'exactly one progression thumbnail must be active');
    assert((await page.locator('.kgg015MainProgressionStage').innerText()).includes('Leichter'),'main pager did not start at the easier stage');
    await page.locator('.kgg015MainProgressionControls').first().waitFor({state:'visible'});
    assert(await page.locator('[data-kgg015-main-prev]').isDisabled(),'main image minus control must be disabled at the easiest stage');
    assert(!(await page.locator('[data-kgg015-main-next]').isDisabled()),'main image plus control must be enabled when a harder stage exists');
    await page.locator('[data-kgg015-main-next]').click();
    await page.waitForFunction(()=>document.querySelector('.kgg015MainProgressionStage')?.textContent.includes('Basis'));
    assert(await page.evaluate(()=>p.ex[0].media?.[0]?.id)==='base-media','main exercise image did not switch to the selected stage');
    const pager=page.locator('.kgg015MainPager').first();
    await page.waitForTimeout(700);
    const pagerBox=await (await page.waitForFunction(()=>{const node=document.querySelector('.kgg015MainPager');const rect=node?.getBoundingClientRect();return rect&&rect.width>0&&rect.height>0?{x:rect.x,y:rect.y,width:rect.width,height:rect.height}:false})).jsonValue();
    assert(pagerBox,'main pager must have a measurable swipe area');
    await pager.evaluate((node,dx)=>{const rect=node.getBoundingClientRect(),x=rect.x+rect.width*.2,y=rect.y+rect.height*.25,base={bubbles:true,clientX:x,clientY:y,pointerId:17,pointerType:'touch'};node.dispatchEvent(new PointerEvent('pointerdown',base));node.dispatchEvent(new PointerEvent('pointermove',{...base,clientX:x+dx}));},pagerBox.width*.45);
    const dragDebug=await page.locator('.kgg015MainPagerTrack').evaluate(node=>({dragging:node.classList.contains('is-dragging'),style:node.getAttribute('style'),pagerHandler:typeof node.parentElement?.onpointerdown}));
    assert(dragDebug.dragging,'pager must track the pointer before release: '+JSON.stringify(dragDebug));
    assert((await page.locator('.kgg015MainPagerTrack').getAttribute('style')||'').includes('translate3d'),'pager must move with the pointer in real time');
    await pager.dispatchEvent('pointerup',{bubbles:true,clientX:0,clientY:0,pointerId:17,pointerType:'touch'});
    await page.waitForFunction(()=>document.querySelector('.kgg015MainProgressionStage')?.textContent.includes('Leichter'));
    assert(await page.evaluate(()=>p.ex[0].media?.[0]?.id)==='easy-media','swipe release did not elastically snap to the previous stage');
    await page.locator('.kgg015MainProgressionThumb').nth(2).click();
    await page.waitForFunction(()=>document.querySelector('.kgg015MainProgressionStage')?.textContent.includes('Schwerer'));
    const activeThumb=await page.locator('.kgg015MainProgressionThumb[aria-current="true"]').evaluate(node=>({stage:node.dataset.kgg015MainStage,text:node.querySelector('.kgg015MainProgressionThumbLabel')?.textContent.trim(),label:node.getAttribute('aria-label')}));
    assert(activeThumb.stage==='hard'&&activeThumb.text==='3','thumbnail selection did not use the shared progression state: '+JSON.stringify(activeThumb));
    await page.evaluate(()=>{window.put(0,1,'B','a','0');window.put(0,1,'B','b','0');window.put(0,1,'B','a','0');});
    await page.evaluate(()=>window.put(0,2,'B','a','0'));
    const afterZero=await page.evaluate(()=>JSON.parse(localStorage.getItem('kggProgressionHistoryV1')||'{}'));
    assert(afterZero.current&&Object.keys(afterZero.current.records||{}).length===2,'zero-value edits did not create exactly one record per set');
    assert(afterZero.current.records['0|1'].id==='hard','selected hard stage was not recorded for set 1');
    assert(afterZero.current.records['0|2'].id==='easy','default easy stage was not recorded for set 2');

    await page.evaluate(()=>window.showQr(true));
    const finishConfirm=page.locator('[data-kgg-ticket034-action="confirm"]');
    if(await finishConfirm.isVisible().catch(()=>false))await finishConfirm.click();
    await page.waitForTimeout(120);
    const afterFinish=await page.evaluate(()=>JSON.parse(localStorage.getItem('kggProgressionHistoryV1')||'{}'));
    assert(afterFinish.groups['ticket-015-browser|progression-group-1'].dominantId==='hard','dominant tie did not choose the higher stage');
    assert((await card.locator('h3').innerText())==='Schwerer','dominant stage did not become the displayed exercise name');
    const qrWire=await page.evaluate(()=>{const payload=document.getElementById('qr')?.dataset.payload||'';const raw=payload.replace(/^KGGD1:/,'').replace(/-/g,'+').replace(/_/g,'/');const padded=raw+'='.repeat((4-raw.length%4)%4);return JSON.parse(decodeURIComponent(escape(atob(padded))))});
    assert(qrWire.e&&qrWire.e[0]&&qrWire.e[0][7]&&qrWire.e[0][7].k==='kgg015','KGGD1 QR omitted the progression selection marker');
    assert(qrWire.e[0][7].s[0].i==='hard','KGGD1 QR omitted the selected hard stage');

    await page.locator('[data-kgg015-main-prev]').click();
    await page.evaluate(()=>window.put(0,1,'B','a','0'));
    await page.evaluate(()=>window.showQr(false));
    await page.waitForTimeout(80);
    assert((await page.locator('#sum').innerText()).includes('Variantenwechsel:'),'actual stage change was missing from documentation');
    assert(errors.length===0,`patient preview raised page errors: ${errors.join(' | ')}`);
    console.log('Ticket 015 browser smoke: OK');
  }finally{
    await Promise.race([browser.close(),new Promise(resolve=>setTimeout(resolve,5000))]);
    await new Promise(resolve=>server.close(resolve))
  }
}

main().catch(error=>{console.error(error.stack||error);process.exitCode=1});
