"use strict";
// Install pop-up appears only with a real install prompt, and the iPhone
// transfer bundle carries plans + values losslessly into the installed app.
const fs=require("fs"),http=require("http"),path=require("path"),{chromium}=require("playwright");
const ROOT=path.resolve(__dirname,"..");
const assert=(v,m)=>{if(!v)throw new Error(m)};
const enc=plan=>Buffer.from(JSON.stringify(plan),"utf8").toString("base64url");
const ANDROID="Mozilla/5.0 (Linux; Android 14; SM-S911B) AppleWebKit/537.36 (KHTML, like Gecko) SamsungBrowser/26.0 Chrome/122.0.0.0 Mobile Safari/537.36";
const IOS="Mozilla/5.0 (iPhone; CPU iPhone OS 17_5 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.5 Mobile/15E148 Safari/604.1";
function fileFor(url){const rel=decodeURIComponent(String(url||"/").split("?")[0].split("#")[0]).replace(/^\/+/,"")||"index.html",target=path.resolve(ROOT,rel);return target.startsWith(ROOT)&&fs.existsSync(target)&&fs.statSync(target).isFile()?target:null}
function typeFor(f){return f.endsWith(".html")?"text/html; charset=utf-8":f.endsWith(".js")?"text/javascript; charset=utf-8":f.endsWith(".json")?"application/json; charset=utf-8":"application/octet-stream"}
const plan={i:"install-transfer",t:"Install transfer",v:1,d:2,e:[["Beinpresse",3,"B","kg","Wdh","40","10"]]};
const popupVisible=page=>page.evaluate(()=>Boolean(document.getElementById("kggInstallPopup")));
async function open(browser,base,ua,query){
 const ctx=await browser.newContext({viewport:{width:390,height:844},serviceWorkers:"block",userAgent:ua});
 const page=await ctx.newPage();
 await page.goto(base+"/?plan="+encodeURIComponent("KGGH2:"+enc(plan))+(query||""),{waitUntil:"domcontentloaded"});
 await page.waitForFunction(()=>document.querySelector("#plan")&&!document.querySelector("#plan").classList.contains("hide"));
 return {ctx,page};
}
(async()=>{
 const server=http.createServer((req,res)=>{const f=fileFor(req.url);if(!f){res.statusCode=404;return res.end("404")}res.setHeader("Content-Type",typeFor(f));res.setHeader("Cache-Control","no-store");res.end(fs.readFileSync(f))});
 await new Promise(r=>server.listen(0,"127.0.0.1",r));
 const base="http://127.0.0.1:"+server.address().port;
 const browser=await chromium.launch({headless:true});
 try{
  // 1) Android without a real install prompt: no pop-up.
  let {ctx,page}=await open(browser,base,ANDROID);
  await page.waitForTimeout(5000);
  assert(!(await popupVisible(page)),"pop-up shown without a real install prompt");
  // 2) Real prompt arrives: pop-up with one-tap install; accepted -> done + no re-show.
  await page.evaluate(()=>{window.__installCalls=0;const e=new Event("beforeinstallprompt",{cancelable:true});Object.defineProperty(e,"prompt",{value:async()=>{window.__installCalls++}});Object.defineProperty(e,"userChoice",{value:Promise.resolve({outcome:"accepted"})});window.dispatchEvent(e)});
  await page.waitForFunction(()=>document.getElementById("kggInstallPopup"),null,{timeout:5000});
  const text=await page.locator("#kggInstallPopup").innerText();
  assert(/Jetzt installieren/.test(text)&&!/⋮|☰|Teilen/.test(text),"pop-up is not the one-tap install variant: "+text);
  await page.getByRole("button",{name:"Jetzt installieren"}).click();
  await page.waitForFunction(()=>/Installiert/.test((document.getElementById("kggInstallPopupStatus")||{}).textContent||""));
  const st=await page.evaluate(()=>({calls:window.__installCalls,done:localStorage.getItem("kggInstallPopupDone"),plan:!!localStorage.getItem("kggCurrentPlanV1")}));
  assert(st.calls===1&&st.done==="1"&&st.plan,"install not completed cleanly: "+JSON.stringify(st));
  await ctx.close();
  // 3) Dismissed prompt -> snoozed, plan untouched.
  ({ctx,page}=await open(browser,base,ANDROID));
  await page.evaluate(()=>{const e=new Event("beforeinstallprompt",{cancelable:true});Object.defineProperty(e,"prompt",{value:async()=>{}});Object.defineProperty(e,"userChoice",{value:Promise.resolve({outcome:"dismissed"})});window.dispatchEvent(e)});
  await page.waitForFunction(()=>document.getElementById("kggInstallPopup"),null,{timeout:5000});
  await page.getByRole("button",{name:"Jetzt installieren"}).click();
  await page.waitForFunction(()=>!document.getElementById("kggInstallPopup"));
  assert(Number(await page.evaluate(()=>localStorage.getItem("kggInstallPopupSnoozeUntil")))>Date.now(),"dismiss did not snooze");
  await ctx.close();
  // 4) Existing legacy installBox must not remain visible behind/after Later.
  ({ctx,page}=await open(browser,base,ANDROID));
  await page.evaluate(()=>localStorage.removeItem("kggInstallAsked"));
  await page.evaluate(()=>{
    const e=new Event("beforeinstallprompt",{cancelable:true});
    Object.defineProperty(e,"prompt",{value:async()=>{}});
    Object.defineProperty(e,"userChoice",{value:Promise.resolve({outcome:"dismissed"})});
    window.dispatchEvent(e);
  });
  await page.waitForFunction(()=>document.getElementById("kggInstallPopup"),null,{timeout:7000});
  assert(await page.evaluate(()=>document.getElementById("installBox").classList.contains("hide")),
    "legacy installBox visible beneath the new installation prompt");
  await page.getByRole("button",{name:"Sp\u00e4ter"}).click();
  const deferred=await page.evaluate(()=>({
    legacyHidden:document.getElementById("installBox").classList.contains("hide"),
    newHidden:!document.getElementById("kggInstallPopupBackdrop"),
    snoozed:Number(localStorage.getItem("kggInstallPopupSnoozeUntil"))>Date.now(),
    legacyAsked:localStorage.getItem("kggInstallAsked")==="1"
  }));
  assert(deferred.legacyHidden&&deferred.newHidden&&deferred.snoozed&&deferred.legacyAsked,
    "Later must dismiss both installation dialogs and snooze: "+JSON.stringify(deferred));
  await ctx.close();
  // 5) iPhone Safari: no pop-up by default (no real install prompt exists there).
  ({ctx,page}=await open(browser,base,IOS));
  await page.waitForTimeout(3500);
  assert(!(await popupVisible(page)),"iPhone pop-up shown although iOS flow is not enabled");
  // 5) Transfer bundle round trip into an "installed" context.
  await page.evaluate(()=>{localStorage.setItem("kgg-install-transfer-test-values",JSON.stringify({"0":{"1":"42"}}))});
  const code=await page.evaluate(()=>window.KGGInstallTransfer.encodeBundle());
  const snap=await page.evaluate(()=>{const o={};for(let i=0;i<localStorage.length;i++){const k=localStorage.key(i);if(/^kgg/i.test(k))o[k]=localStorage.getItem(k)}return o});
  await ctx.close();
  ctx=await browser.newContext({viewport:{width:390,height:844},serviceWorkers:"block",userAgent:IOS});
  await ctx.addInitScript(()=>{Object.defineProperty(navigator,"standalone",{get:()=>true})});
  page=await ctx.newPage();
  await page.goto(base+"/ios-start.html?install=1&plan="+encodeURIComponent("KGGH2:"+enc(plan))+"#kggt="+code,{waitUntil:"domcontentloaded"});
  await page.waitForURL(u=>!/ios-start/.test(String(u)),{timeout:8000});
  await page.waitForFunction(()=>document.querySelector("#plan")&&!document.querySelector("#plan").classList.contains("hide"),null,{timeout:8000});
  const got=await page.evaluate(()=>({values:localStorage.getItem("kgg-install-transfer-test-values"),current:localStorage.getItem("kggCurrentPlanV1"),imported:localStorage.getItem("kggTransferImported"),choice:!!document.getElementById("kggPlanLinkChoiceBackdrop")}));
  assert(got.values===snap["kgg-install-transfer-test-values"],"values were not transferred");
  assert(got.current&&JSON.parse(got.current).plan.i==="install-transfer","plan was not transferred");
  assert(got.imported&&!got.choice,"transfer not marked or asked to replace plan: "+JSON.stringify(got));
  await page.waitForFunction(()=>/übernommen/.test((document.getElementById("kggInstallToast")||{}).textContent||""),null,{timeout:5000});
  // 6) Relaunch never overwrites newer data with the old bundle.
  await page.evaluate(()=>localStorage.setItem("kgg-install-transfer-test-values","newer"));
  await page.goto(base+"/ios-start.html?install=1#kggt="+code,{waitUntil:"domcontentloaded"});
  await page.waitForURL(u=>!/ios-start/.test(String(u)),{timeout:8000});
  assert(await page.evaluate(()=>localStorage.getItem("kgg-install-transfer-test-values"))==="newer","relaunch overwrote newer values");
  await ctx.close();
  // 7) iPhone Safari opening the install page stays there with the steps (no redirect).
  ctx=await browser.newContext({viewport:{width:390,height:844},serviceWorkers:"block",userAgent:IOS});page=await ctx.newPage();
  await page.goto(base+"/ios-start.html?install=1&plan="+encodeURIComponent("KGGH2:"+enc(plan))+"#kggt="+code,{waitUntil:"domcontentloaded"});
  await page.waitForTimeout(800);
  assert(/ios-start/.test(page.url())&&/Zum Home-Bildschirm/.test(await page.locator("body").innerText()),"install page did not stay with steps");
  // 8) Old iPhone plan links (without install=1) still forward as before.
  await page.goto(base+"/ios-start.html?plan="+encodeURIComponent("KGGH2:"+enc(plan)),{waitUntil:"domcontentloaded"});
  await page.waitForURL(u=>!/ios-start/.test(String(u)),{timeout:8000});
  await ctx.close();
  console.log("Patient install transfer Playwright: PASS");
 }finally{await browser.close();await new Promise(r=>server.close(r))}
})().catch(e=>{console.error("Patient install transfer Playwright FAIL: "+(e.stack||e.message));process.exitCode=1});
