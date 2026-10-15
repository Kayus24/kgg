'use strict';
const fs=require('fs'),http=require('http'),path=require('path'),{chromium}=require('playwright');
const ROOT=path.resolve(__dirname,'..');
const plan={i:'import-session-values',t:'Synthetic training',v:1,d:6,e:[['Beinpresse',2,'B','kg','Wdh','','']]};
const incoming={...plan,i:'incoming-session-values',t:'Synthetic imported training',e:[...plan.e,['Rudern',1,'B','kg','Wdh','','']]};
const code=p=>'KGGH2:'+Buffer.from(JSON.stringify(p)).toString('base64url');
function assert(ok,message){if(!ok)throw new Error(message)}
async function state(page){return page.evaluate(()=>({values:{...v},day:d,done:[...done],id:p.id,inputs:Array.from(document.querySelectorAll('input.num'),e=>e.value),summary:text(d)}))}
async function main(){
 const server=http.createServer((req,res)=>{const rel=new URL(req.url,'http://localhost').pathname.slice(1)||'index.html',file=path.resolve(ROOT,rel);if(!file.startsWith(ROOT+path.sep)||!fs.existsSync(file)||!fs.statSync(file).isFile()){res.statusCode=404;return res.end()};res.setHeader('Content-Type',file.endsWith('.html')?'text/html; charset=utf-8':file.endsWith('.js')?'text/javascript; charset=utf-8':'application/octet-stream');res.end(fs.readFileSync(file))});
 await new Promise(r=>server.listen(0,'127.0.0.1',r));
 const base='http://127.0.0.1:'+server.address().port,browser=await chromium.launch({headless:true});
 try{for(const mode of ['update','add','replace','replace-link']){
  const context=await browser.newContext({serviceWorkers:'block',viewport:{width:390,height:844}}),page=await context.newPage(),errors=[];
  page.on('pageerror',e=>errors.push(e.message));
  await page.addInitScript(()=>{Object.defineProperty(navigator,'mediaDevices',{configurable:true,value:{getUserMedia:()=>Promise.reject(new Error('synthetic camera unavailable'))}});localStorage.kggInstallAsked='1'});
  await page.goto(base+'/index.html#'+code(plan));
  await page.waitForFunction(()=>window.KGGPatientPlanImport&&window.KGGPatientPlanSlots&&window.__kggPatientStartValuesDay1);
  await page.evaluate(()=>{put(0,1,'B','a','52');put(0,1,'B','b','12');put(0,2,'B','a','47');put(0,2,'B','b','10');showQr(true);document.getElementById('end').classList.add('hide')});
  const before=await state(page),storageKey=await page.evaluate(()=>sk()),storedBefore=await page.evaluate(()=>localStorage.getItem(sk()));
  if(mode==='replace-link'){
   await page.goto(base+'/index.html?plan='+encodeURIComponent(code(incoming)));
   await page.locator('#kggPlanLinkChoiceReplace').click();
  }else{
   page.on('dialog',async dialog=>{if(dialog.type()==='prompt')await dialog.accept(code(incoming));else await dialog.accept()});
   await page.locator('#kggActionFab').click();
   await page.locator(mode==='replace'?'#kggBubbleReplace':mode==='add'?'#kggBubbleAdd':'#kggBubbleScan').click();
   await page.locator('.kggLivePaste').click();
  }
  await page.waitForFunction(()=>p.title==='Synthetic imported training');
  await page.waitForTimeout(1500); // Includes both delayed start-value initializers.
  const after=await state(page);
  assert(after.inputs.every(x=>x===''),mode+': previous session was entered as current values: '+JSON.stringify(after));
  assert(after.summary==='',mode+': current summary contains previous training');
  if(mode==='update')assert(JSON.stringify(after.values)===JSON.stringify(before.values)&&after.day===2&&JSON.stringify(after.done)==='[1]','update changed existing training history');
  else assert(Object.keys(after.values).length===0&&after.day===1&&after.done.length===0,mode+': imported plan reused session state');
  assert(await page.evaluate(key=>localStorage.getItem(key),storageKey)===storedBefore,mode+': old stored training changed');
  await page.reload();await page.waitForFunction(()=>window.__kggPatientStartValuesDay1);await page.waitForTimeout(1500);
  assert((await state(page)).inputs.every(x=>x===''),mode+': reload filled current training');
  assert(errors.length===0,mode+': '+errors.join('; '));
  console.log('PASS '+mode+' retains history without entering previous session values');
  await context.close();
 }}finally{await browser.close();await new Promise(r=>server.close(r))}
}
main().catch(e=>{console.error(e.stack||e.message);process.exitCode=1});
