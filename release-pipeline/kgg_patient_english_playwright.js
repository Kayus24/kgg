#!/usr/bin/env node
'use strict';
// Regression: translated display must never become canonical plan or QR data.
const fs=require('fs'),http=require('http'),path=require('path'),{chromium}=require('playwright');
const ROOT=path.resolve(__dirname,'..');
const BANK=[['Abduktion Maschine','Hip Abduction Machine'],['Adduktion Maschine','Hip Adduction Machine'],['Beinpresse','Leg Press'],['Bridging','Glute Bridge'],['Copenhagen Plank','Copenhagen Plank'],['Ergometer / Bike','Exercise Bike / Ergometer'],['Fire Hydrants','Fire Hydrants'],['Hip Thrust','Hip Thrust'],['Kniebeuger Maschine','Leg Curl Machine'],['Kniestrecker Maschine','Leg Extension Machine'],['Rudern','Row'],['Latziehen','Lat Pulldown'],['Pallof Press','Pallof Press'],['Plank','Plank'],['Squat','Squat'],['Romanian Deadlift','Romanian Deadlift'],['Wadenheben','Calf Raise'],['Schulterpresse','Shoulder Press']];
const EXTRA=[['Kniebeuge','Squat'],['Rudern sitzend','Seated Row'],['Sitzendes Kabelrudern','Seated Cable Row'],['Brustpresse Maschine','Machine Chest Press'],['Brustpresse','Chest Press'],['Schulterdrücken','Shoulder Press'],['Latzug','Lat Pulldown'],['Beinbeuger sitzend','Seated Leg Curl'],['Unterarmstütz','Plank'],['Seitstütz mit Hüftsenken','Side Plank Hip Dips'],['Rückenstrecker','Back Extension'],['Beinschwünge','Leg Swings']];
const svg='data:image/svg+xml,'+encodeURIComponent('<svg xmlns="http://www.w3.org/2000/svg" width="120" height="80"><rect width="120" height="80" fill="#dbeafe"/></svg>');
function assert(ok,message){if(!ok)throw new Error(message)}
const code=plan=>'KGGH2:'+Buffer.from(JSON.stringify(plan)).toString('base64url');
const media=[{id:'english-synthetic-image',type:'image',src:svg,mime:'image/svg+xml'}];
function snapshot(page){return page.evaluate(()=>({plan:JSON.stringify(p),raw:localStorage.getItem('kggCurrentPlanV1'),values:JSON.stringify(v),day:d,names:p.ex.map(e=>e.n)}))}
async function toggle(page,overlay=false){if(overlay)await page.locator('#kggLangSwitch').evaluate(el=>el.click());else await page.locator('#kggLangSwitch').click();await page.waitForTimeout(150)}
async function main(){
  const active=fs.readFileSync(path.join(ROOT,'kgg-update/src/runtime/app-core.html'),'utf8');
  const bankBlock=active.match(/const bank=\[([\s\S]*?)\]\.map/)[1];
  const activeNames=[...bankBlock.matchAll(/\['[^']+','([^']+)'/g)].map(x=>x[1]);
  assert(JSON.stringify(activeNames)===JSON.stringify(BANK.map(x=>x[0])),'English acceptance table does not cover the actual complete active bank');
  const server=http.createServer((req,res)=>{const rel=new URL(req.url,'http://local').pathname.replace(/^\/+/, '')||'index.html',f=path.resolve(ROOT,rel);if(!f.startsWith(ROOT+path.sep)||!fs.existsSync(f)){res.statusCode=404;return res.end()}res.setHeader('Content-Type',f.endsWith('.html')?'text/html; charset=utf-8':f.endsWith('.js')?'text/javascript; charset=utf-8':f.endsWith('.css')?'text/css':'application/octet-stream');res.setHeader('Cache-Control','no-store');res.end(fs.readFileSync(f))});
  await new Promise(r=>server.listen(0,'127.0.0.1',r));const base='http://127.0.0.1:'+server.address().port;
  const browser=await chromium.launch({headless:true});
  try{
    for(const react of [false,true]){
      const ctx=await browser.newContext({viewport:{width:390,height:844},isMobile:true,hasTouch:true,serviceWorkers:'block'}),page=await ctx.newPage(),errors=[];page.on('pageerror',e=>errors.push(e.message));
      await page.addInitScript(()=>{localStorage.kggInstallAsked='1'});
      const entries=[...BANK,...EXTRA],plan={i:'english-ui-'+react,t:'Synthetic English coverage',v:1,d:6,e:entries.map((x,i)=>[x[0],1,i===0?'LR':'B','kg','Wdh','','',i===0?media:[]])};
      await page.goto(base+'/?kggReactPad='+(react?'1':'0')+'&plan='+encodeURIComponent(code(plan)),{waitUntil:'domcontentloaded'});await page.waitForFunction(()=>document.querySelectorAll('#list .ex').length===30);await page.waitForTimeout(1500);
      const before=await snapshot(page);await toggle(page);
      const titles=await page.locator('#list .ex h3').allTextContents();
      assert(JSON.stringify(titles)===JSON.stringify(entries.map(x=>x[1])),'English exercise display incomplete: '+JSON.stringify(titles));
      assert(await page.locator('html').getAttribute('lang')==='en','document language did not update');
      assert((await page.locator('#meta').textContent()).includes('exercises'),'plan metadata did not update');
      const after=await snapshot(page);assert(JSON.stringify(before)===JSON.stringify(after),'language toggle changed canonical plan/storage/values/day');
      if(process.argv.includes('--catalog-only')){await ctx.close();continue}
      const card=page.locator('#list .ex').first();await card.locator('h3').click();await card.locator('.kggCardDots').click();
      assert((await page.locator('#kggSettingsSheet').innerText()).includes('Edit exercise'),'settings English missing');
      assert(await page.locator('#kggSetUnitB').inputValue()==='reps','settings unit shows canonical German unit');
      await toggle(page,true);assert((await page.locator('#kggSettingsSheet').innerText()).includes('Übung anpassen'),'open settings reverse toggle missing');await toggle(page,true);await page.locator('#kggSetCancel').click();
      if(process.env.KGG_I18N_SYNC_ASSERT==='1')await page.evaluate(()=>{
        const previous=window.openPad;
        window.openPad=function(...args){const result=previous.apply(this,args);
          window.__kggSyncLocaleObservation={title:document.getElementById('padTitle')?.textContent,
            previous:document.getElementById('padLast')?.textContent};return result;};
      });
      const proxy=card.locator('.kggCompactTapProxy').first();await proxy.click();
      if(process.env.KGG_I18N_SYNC_ASSERT==='1'){
        const instant=await page.evaluate(()=>window.__kggSyncLocaleObservation);
        assert(instant&&!/eingeben|Wert|\u00fcbernehmen|Vorwert/.test(JSON.stringify(instant)),
          'Synchronous English NumPad contract failed: '+JSON.stringify(instant));
      }

      // The existing i18n MutationObserver schedules translation after the tap.
      // Require the same English-only UI contract as soon as it actually settles.
      try {
        await page.waitForFunction(() => {
          const pad=document.getElementById('pad');
          return pad && !pad.classList.contains('hide') && document.documentElement.lang==='en' &&
            !/eingeben|Wert|übernehmen|Vorwert/.test(pad.innerText);
        },null,{timeout:2000,polling:'raf'});
      } catch(error) {
        const details=await page.evaluate(() => ({
          htmlLang:document.documentElement.lang,
          selectedLang:localStorage.getItem('kggPatientLang'),
          open:!document.getElementById('pad')?.classList.contains('hide'),
          padText:document.getElementById('pad')?.innerText||'',
          reactHeader:document.body.classList.contains('kggReactNumpadHeaderV1')
        }));
        throw new Error('English NumPad did not settle to English: '+JSON.stringify(details)+'; '+error.message);
      }
      assert(!/eingeben|Wert|übernehmen|Vorwert/.test(await page.locator('#pad').innerText()),'English NumPad has German text');
      if(react){await page.locator('.kgg-react-numpad-header').waitFor();assert(await page.locator('.kgg-react-numpad-header').getAttribute('aria-label')==='Value entry','React aria remains German')}
      await page.locator('#pad .padGrid button').filter({hasText:/^2$/}).click();await page.locator('#pad .padOk').click();
      assert((await page.locator('#status').textContent()).includes('saved'),'English commit status missing');
      const namesBeforeQr=(await snapshot(page)).names;await page.getByRole('button',{name:'Show current values as QR',exact:true}).click();
      assert((await page.locator('#endTitle').textContent()).includes('Current values'),'QR title is German');assert(!/Tag|Satz|Schmerz|Wdh|\bli\b|\bre\b/.test(await page.locator('#sum').textContent()),'QR summary has German system text');
      const qr=await page.locator('#qr').getAttribute('data-payload');const returned=JSON.parse(Buffer.from(qr.slice(6),'base64url').toString());assert(JSON.stringify(returned.e.map(x=>x[0]))===JSON.stringify(namesBeforeQr),'English names leaked into return QR');
      const englishSummary=await page.locator('#sum').textContent();await toggle(page);assert(/Satz/.test(await page.locator('#sum').textContent()),'open summary did not return to German');await toggle(page);assert(await page.locator('#sum').textContent()===englishSummary,'open summary roundtrip differs');assert(await page.locator('#qr').getAttribute('data-payload')===qr,'language changed QR payload');
      await page.reload();await page.waitForFunction(()=>document.querySelectorAll('#list .ex').length===30);await page.waitForTimeout(1200);assert((await page.locator('#list .ex h3').first().textContent())==='Hip Abduction Machine','reload lost English display');
      assert(errors.length===0,'page errors: '+errors.join(' | '));await ctx.close();
    }
    console.log('Patient English Playwright: PASS (active bank18, additional12, Legacy + React; canonical names preserved)');
  }finally{await browser.close();await new Promise(r=>server.close(r))}
}
main().catch(e=>{console.error('Patient English Playwright FAIL: '+(e.stack||e.message));process.exitCode=1});
