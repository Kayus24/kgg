"use strict";
const fs=require("fs"),http=require("http"),path=require("path"),{chromium}=require("playwright");
const ROOT=path.resolve(__dirname,"..");
function assert(x,m){if(!x)throw new Error(m)}
function enc(x){return Buffer.from(JSON.stringify(x),"utf8").toString("base64url")}
function typeFor(f){return f.endsWith(".html")?"text/html; charset=utf-8":f.endsWith(".js")?"text/javascript; charset=utf-8":f.endsWith(".json")?"application/json; charset=utf-8":f.endsWith(".png")?"image/png":"application/octet-stream"}
function fileFor(url){const rel=decodeURIComponent(String(url||"/").split("?")[0]).replace(/^\/+/, "")||"index.html",target=path.resolve(ROOT,rel);return target.startsWith(ROOT)&&fs.existsSync(target)&&fs.statSync(target).isFile()?target:null}
async function waitRuntime(page){await page.locator("#plan").waitFor({state:"visible"});await page.waitForFunction(()=>window.__kggPatientStartValuesDay1&&window.__kggPatientCardSettings);await page.waitForTimeout(1300)}
async function main(){
 const server=http.createServer((req,res)=>{const f=fileFor(req.url);if(!f){res.statusCode=404;return res.end("404")}res.setHeader("Content-Type",typeFor(f));res.setHeader("Cache-Control","no-store");res.end(fs.readFileSync(f))});
 await new Promise(r=>server.listen(0,"127.0.0.1",r));const port=server.address().port,browser=await chromium.launch({headless:true}),ctx=await browser.newContext({viewport:{width:390,height:844},hasTouch:true}),page=await ctx.newPage(),errors=[];
 page.on("pageerror",e=>errors.push(String(e)));
 const plan={i:"unit-semantics",t:"Unit semantics",v:1,d:6,e:[
  ["Timed hold",1,"B","keine","Sek.","99","30"],
  ["Pressure",1,"B","bar","Wdh","2","8"],
  ["Watt interval",1,"B","Watt","Sek.","120","45"]
 ]};
 try{
  await page.addInitScript(()=>{localStorage.kggInstallAsked="1"});
  await page.goto("http://127.0.0.1:"+port+"/?plan="+encodeURIComponent("KGGH2:"+enc(plan)),{waitUntil:"networkidle"});
  await waitRuntime(page);
  const state=await page.evaluate(()=>({
    day:Number(d),done:[...done],unit:p.ex[0].u,
    a:v[k(0,1,"B","a",1)]||"",b:v[k(0,1,"B","b",1)]||"",
    barA:v[k(1,1,"B","a",1)]||"",barB:v[k(1,1,"B","b",1)]||"",
    wattA:v[k(2,1,"B","a",1)]||"",wattB:v[k(2,1,"B","b",1)]||""
  }));
  assert(state.unit==="keine","explicit no-load unit changed: "+JSON.stringify(state));
  assert(state.a==="","inactive load field received start value: "+JSON.stringify(state));
  assert(state.b==="30","active seconds start value missing: "+JSON.stringify(state));
  assert(state.barA==="2"&&state.barB==="8","bar/Wdh start values wrong: "+JSON.stringify(state));
  assert(state.wattA==="120"&&state.wattB==="45","Watt/Sek start values wrong: "+JSON.stringify(state));
  const first=page.locator("#list .ex").nth(0);
  const muted=first.locator(":scope > .muted"),meta=await muted.nth(0).textContent(),suggestion=await muted.nth(1).textContent();
  assert(!/keine|none/i.test(meta||"")&&/Sek\.?/.test(meta||""),"card metadata exposes inactive unit: "+meta);
  assert(!/keine|none/i.test(suggestion||"")&&/30 Sek\.?/.test(suggestion||""),"T1 suggestion exposes inactive field: "+suggestion);
  const badge=first.locator(".kggCardProgress");
  assert((await badge.getAttribute("data-kgg-expected-count"))==="1","progress counts inactive field");
  const summary=await page.evaluate(()=>text(1));
  assert(/30 Sek\.?/.test(summary)&&!/keine|\?\s*keine/i.test(summary),"visible summary has phantom field: "+summary);
  await page.reload({waitUntil:"networkidle"});await waitRuntime(page);
  const afterReload=await page.evaluate(()=>({unit:p.ex[0].u,a:v[k(0,1,"B","a",1)]||"",b:v[k(0,1,"B","b",1)]||""}));
  assert(afterReload.unit==="keine"&&afterReload.a===""&&afterReload.b==="30","reload revived inactive load field: "+JSON.stringify(afterReload));
  const histState=await page.evaluate(()=>{if(!done.includes(1))done.push(1);d=2;save();render();return{d:Number(d),done:[...done],today:typeof next==="function"?Number(next()):null}});await page.waitForTimeout(250);
  assert(histState.today===2,"history fixture did not establish current day 2: "+JSON.stringify(histState));
  const history=page.locator("#kggHistoryToggle");await history.click();await page.locator("#kggHistoryList:not([hidden])").waitFor({state:"visible",timeout:5000});
  const hist=await page.locator("#kggHistoryList").innerText();
  assert(/Timed hold/.test(hist)&&/30 Sek\.?/.test(hist),"history lost active single field: "+hist);
  assert(!/\?\s*keine|keine\s*[×@]/i.test(hist),"history exposes phantom inactive field: "+hist);
  assert(errors.length===0,"page errors: "+errors.join(" | "));
  console.log(JSON.stringify({status:"PASS",noLoadStart:true,reload:true,history:true,units:["keine/Sek.","bar/Wdh","Watt/Sek."]}));
 }finally{await ctx.close();await browser.close();await new Promise(r=>server.close(r))}
}
main().catch(e=>{console.error("KGG patient unit semantics Playwright FAIL: "+(e.stack||e.message));process.exitCode=1});