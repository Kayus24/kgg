"use strict";
const fs=require("fs"),http=require("http"),path=require("path"),{chromium}=require("playwright");
const ROOT=path.resolve(__dirname,"..");
const assert=(v,m)=>{if(!v)throw new Error(m)};
const enc=plan=>Buffer.from(JSON.stringify(plan),"utf8").toString("base64url");
function fileFor(url){const rel=decodeURIComponent(String(url||"/").split("?")[0]).replace(/^\/+/, "")||"index.html",target=path.resolve(ROOT,rel);return target.startsWith(ROOT)&&fs.existsSync(target)&&fs.statSync(target).isFile()?target:null}
function typeFor(f){return f.endsWith(".html")?"text/html; charset=utf-8":f.endsWith(".js")?"text/javascript; charset=utf-8":f.endsWith(".json")?"application/json; charset=utf-8":"application/octet-stream"}
(async()=>{
 const server=http.createServer((req,res)=>{const f=fileFor(req.url);if(!f){res.statusCode=404;return res.end("404")}res.setHeader("Content-Type",typeFor(f));res.setHeader("Cache-Control","no-store");res.end(fs.readFileSync(f))});
 await new Promise(r=>server.listen(0,"127.0.0.1",r));
 const browser=await chromium.launch({headless:true}),ctx=await browser.newContext({viewport:{width:390,height:844},serviceWorkers:"block"}),page=await ctx.newPage();
 try{
  const plan={i:"install-capability",t:"Install capability",v:1,d:2,e:[["Beinpresse",3,"B","kg","Wdh","40","10"]]};
  await page.goto("http://127.0.0.1:"+server.address().port+"/?plan="+encodeURIComponent("KGGH2:"+enc(plan)),{waitUntil:"domcontentloaded"});
  await page.waitForFunction(()=>document.querySelector("#plan")&&!document.querySelector("#plan").classList.contains("hide"));
  await page.waitForTimeout(1200);
  let state=await page.evaluate(()=>({box:!document.querySelector("#installBox").classList.contains("hide"),offerText:!document.querySelector("#installOfferText").classList.contains("hide"),offerBtn:!document.querySelector("#installOfferBtn").classList.contains("hide"),hint:document.querySelector("#installHint").innerHTML}));
  assert(!state.box&&!state.offerText&&!state.offerBtn&&state.hint==="","install UI appeared without a real prompt: "+JSON.stringify(state));
  await page.evaluate(()=>{
    localStorage.removeItem("kggInstallAsked");window.__installCalls=0;
    const e=new Event("beforeinstallprompt",{cancelable:true});
    Object.defineProperty(e,"prompt",{value:async()=>{window.__installCalls++}});
    Object.defineProperty(e,"userChoice",{value:Promise.resolve({outcome:"accepted"})});
    window.dispatchEvent(e);
  });
  await page.waitForTimeout(80);
  state=await page.evaluate(()=>({box:!document.querySelector("#installBox").classList.contains("hide"),offerText:!document.querySelector("#installOfferText").classList.contains("hide"),offerBtn:!document.querySelector("#installOfferBtn").classList.contains("hide"),hint:document.querySelector("#installHint").innerHTML}));
  assert(state.box&&state.offerText&&state.offerBtn&&state.hint==="","install UI did not appear for real capability event: "+JSON.stringify(state));
  assert((await page.locator("#installBox").innerText()).includes("Installieren"),"install dialog lost install action");
  assert(!(await page.locator("#installBox").innerText()).match(/Anleitung|Safari|Chrome|Samsung|Firefox/i),"manual install instructions leaked into dialog");
  await page.locator("#installBox").getByRole("button",{name:"Installieren",exact:true}).click();
  await page.waitForTimeout(80);
  state=await page.evaluate(()=>({box:!document.querySelector("#installBox").classList.contains("hide"),offerText:!document.querySelector("#installOfferText").classList.contains("hide"),offerBtn:!document.querySelector("#installOfferBtn").classList.contains("hide"),calls:window.__installCalls}));
  assert(!state.box&&!state.offerText&&!state.offerBtn&&state.calls===1,"prompt was not consumed exactly once: "+JSON.stringify(state));
  console.log("Patient capability-only install Playwright: PASS");
 }finally{await ctx.close();await browser.close();await new Promise(r=>server.close(r))}
})().catch(e=>{console.error("Patient capability-only install Playwright FAIL: "+(e.stack||e.message));process.exitCode=1});