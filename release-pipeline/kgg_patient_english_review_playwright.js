#!/usr/bin/env node
'use strict';
const fs=require('fs'),http=require('http'),path=require('path'),assert=require('assert/strict'),{chromium}=require('playwright');
const ROOT=path.resolve(__dirname,'..');
const plan={i:'review-english',t:'Synthetic review',v:1,d:6,e:[['Wadenheben',1,'B','kg','Wdh'],['Eigene Übung',1,'B','kg','Wdh'],['Basis',1,'B','kg','Wdh']],m:{exerciseNamesEn:{'Eigene Übung':'Tag 1 Exercise'}}};
async function main(){
 const server=http.createServer((req,res)=>{const rel=new URL(req.url,'http://local').pathname.replace(/^\/+/, '')||'index.html',f=path.resolve(ROOT,rel);if(!f.startsWith(ROOT+path.sep)||!fs.existsSync(f)){res.statusCode=404;return res.end()}res.setHeader('Content-Type',f.endsWith('.html')?'text/html; charset=utf-8':f.endsWith('.js')?'text/javascript; charset=utf-8':'application/octet-stream');res.end(fs.readFileSync(f))});
 await new Promise(r=>server.listen(0,'127.0.0.1',r));const base='http://127.0.0.1:'+server.address().port,browser=await chromium.launch({headless:true}),ctx=await browser.newContext({viewport:{width:390,height:844},serviceWorkers:'block'}),page=await ctx.newPage(),failures=[];
 const check=(ok,name)=>{console.log(name+': '+(ok?'PASS':'RED'));if(!ok)failures.push(name)};
 try{
  await page.addInitScript(()=>localStorage.kggInstallAsked='1');await page.goto(base+'/?plan='+encodeURIComponent('KGGH2:'+Buffer.from(JSON.stringify(plan)).toString('base64url')),{waitUntil:'domcontentloaded'});await page.waitForFunction(()=>document.querySelectorAll('#list .ex').length===3);await page.waitForTimeout(1300);
  await page.locator('#kggActionFab').click();await page.locator('#kggLangSwitch').click();await page.waitForTimeout(150);
  check(await page.title()==='KGG Training Plan','document title English');check((await page.locator('#kggBubbleReplace').textContent()).includes('Replace plan'),'open action replace English');
  check(await page.locator('#list .ex h3').nth(2).textContent()==='Basis','free exercise Basis preserved');
  const contract=await page.evaluate(()=>{const i=KGGPatientI18n;return {summary:KGGPatientSummaryDisplay.render({day:1,englishNames:{'Eigene Übung':'Tag 1 Exercise'},entries:[{name:'Eigene Übung',side:'B',u:'none',m:'Wdh',values:[['','8']],pain:'0'}],changes:[]}),stages:typeof i.progressionName==='function'?[i.progressionName('Basis'),i.progressionName('Leichter'),i.progressionName('Schwerer')]:[],statuses:['Weitere Trainingstage hinzugefügt: bis T12.','Plan aktualisiert. Übungen: 2.','Plan aktualisiert. Werte behalten. Neue Übungen: 3.','Plan ersetzt. Übernommene Werte: 4.'].map(x=>[x,i.systemText(x)])}});
  check(contract.summary==='Tag 1 Exercise — Day 1\n1. Set: 8 reps','authored English summary name preserved');check(JSON.stringify(contract.stages)===JSON.stringify(['Basis','Leichter','Schwerer']),'free stage names preserved without authored English');
  check(await page.evaluate(()=>KGGPatientI18n.progressionName('Basis',{englishName:'Authored base'})==='Authored base'),'explicit stage translation displayed');
  check(JSON.stringify(contract.statuses.map(x=>x[1]))===JSON.stringify(['More training days added: through day 12.','Plan updated. Exercises: 2.','Plan updated. Values kept. New exercises: 3.','Plan replaced. Values copied: 4.']),'numeric status fixture forms English');
  await page.locator('#kggActionFab').click();await page.locator('#kggPatientDbBtn').click();await page.locator('#kggDbSearch').fill('Calf');check(await page.locator('.kggDbCard').count()===1,'English database search finds canonical Calf Raise');await page.locator('#kggDbClose').click();
  // Controlled browser capability event opens the actual product installation box.
  await page.evaluate(()=>{localStorage.removeItem('kggInstallAsked');const e=new Event('beforeinstallprompt');e.prompt=async()=>{};e.userChoice=Promise.resolve({outcome:'dismissed'});window.dispatchEvent(e);maybeAskInstall()});await page.locator('#installBox').waitFor({state:'visible'});await page.waitForTimeout(150);
  check((await page.locator('#installBox').innerText()).includes('Add plan to the home screen?')&&(await page.locator('#installBox').innerText()).includes('No thanks'),'actual install box English');
  await page.locator('#kggLangSwitch').click();await page.waitForTimeout(150);check((await page.locator('#installBox').innerText()).includes('Nein danke'),'open install box reverse locale');
  const reverse=await page.evaluate(statuses=>statuses.map(x=>KGGPatientI18n.systemText(x[1])),contract.statuses);check(JSON.stringify(reverse)===JSON.stringify(contract.statuses.map(x=>x[0])),'numeric statuses reverse locale');
  check(await page.evaluate(()=>KGGPatientI18n.systemText('Enter reps')==='Wdh eingeben'&&KGGPatientI18n.systemText('Use 8 reps')==='8 Wdh übernehmen'),'pad recognized units reverse locale');
  assert.equal(failures.length,0,'review regressions: '+failures.join('; '));console.log('English review Playwright: PASS');
 }finally{await ctx.close();await browser.close();await new Promise(r=>server.close(r))}
}
main().catch(e=>{console.error(e.stack||e.message);process.exitCode=1});
