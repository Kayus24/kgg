#!/usr/bin/env node
"use strict";

// User-facing opt-in pain-per-set regression. Never changes product code.
const fs=require("fs");
const http=require("http");
const path=require("path");
const {chromium,webkit}=require("playwright");
const ROOT=path.resolve(__dirname,"..");
function assert(ok,message){if(!ok)throw new Error(message)}
function encode(x){return Buffer.from(JSON.stringify(x),"utf8").toString("base64url")}
function fileFor(requestUrl){
  const s=decodeURIComponent(String(requestUrl||"/").split("?")[0]).replace(/^\/+/,"").replace(/^kgg\/?/,"")||"index.html";
  const file=path.resolve(ROOT,s);
  return file.startsWith(ROOT+path.sep)&&fs.existsSync(file)&&fs.statSync(file).isFile()?file:null;
}
function mime(file){
  return ({".html":"text/html; charset=utf-8",".js":"text/javascript; charset=utf-8",".css":"text/css; charset=utf-8",
    ".json":"application/json; charset=utf-8",".png":"image/png",".webmanifest":"application/manifest+json; charset=utf-8"})[path.extname(file).toLowerCase()]||"application/octet-stream";
}
async function ready(page){
  await page.evaluate(()=>navigator.serviceWorker.ready);
  if(!await page.evaluate(()=>Boolean(navigator.serviceWorker.controller)))await page.reload({waitUntil:"domcontentloaded"});
  for(let i=0;i<4;i++){
    try{
      await page.waitForFunction(()=>document.querySelectorAll("#list .ex").length===2&&
        Boolean(document.querySelector("#list .ex .kggCardDots"))&&document.body.classList.contains("kggAlwaysCollapsed"),
        null,{timeout:3000});
      return;
    }catch(e){if(i===3)throw e;await page.reload({waitUntil:"domcontentloaded"})}
  }
}
async function openCard(page,idx=0){
  for(let attempt=0;attempt<5;attempt++){
    const card=page.locator("#list .ex").nth(idx);
    if(await card.evaluate(el=>el.classList.contains("kggOpen")))return card;
    await card.locator("h3").evaluate(el=>el.click());
    try{
      await page.waitForFunction(i=>Boolean(document.querySelectorAll("#list .ex")[i]?.classList.contains("kggOpen")),idx,{timeout:900});
      return page.locator("#list .ex").nth(idx);
    }catch(e){await page.waitForTimeout(150)}
  }
  throw new Error("could not open exercise card "+idx);
}
async function mode(page,next){
  const card=await openCard(page,0);
  await card.locator(".kggCardDots").click();
  await page.locator("#kggSettingsSheet").waitFor({state:"visible"});
  await page.locator("#kggSetPainMode").selectOption(next);
  await page.locator("#kggSetSave").click();
  await page.waitForFunction(()=>document.querySelector("#kggSettingsSheet")?.hidden===true);
  await page.waitForTimeout(220); // allow the scheduled legacy apply() to settle
  return openCard(page,0);
}

async function chooseSetPain(page,setIndex,value){
  const root=page.locator("#list .ex").first().locator(".kggSetPain").nth(setIndex);
  const toggle=root.locator(".kggPainVerticalToggle");
  await toggle.waitFor({state:"visible"});
  assert((await toggle.getAttribute("aria-label")||"").includes("Satz "+(setIndex+1)),"per-set bolt lacks accessible set index");
  await toggle.click();
  const modal=page.locator("#kggPainModal");
  await modal.waitFor({state:"visible"});
  assert((await modal.locator("#kggPainModalTitle").textContent()||"").includes("Satz "+(setIndex+1)),"pain dialog is not bound to the selected set");
  await modal.locator('.kggPainVerticalValue[data-kgg-pain-value="'+value+'"]').click();
  assert((await toggle.locator(".kggPainCompactText").textContent()||"")===String(value)+"⚡","per-set bolt did not display the selected value");
  await modal.locator(".kggPainModalClose").click();
  await modal.waitFor({state:"hidden"});
  assert((await toggle.getAttribute("aria-expanded"))==="false","per-set bolt did not close");
}

async function selected(page){
  return page.locator("#list .ex").first().locator(".kggSetPain .kggPainScale")
    .evaluateAll(nodes=>nodes.map(n=>n.querySelector("button.on")?.dataset.val||null));
}
async function caseTest(browser,origin,react){
  const context=await browser.newContext({viewport:{width:390,height:844},hasTouch:true,isMobile:true,serviceWorkers:"allow"});
  const page=await context.newPage();page.setDefaultTimeout(5000);
  const errors=[];page.on("pageerror",error=>errors.push(error.message));
  const plan={i:"pain-per-set-e2e",t:"Pain per set contract",v:1,d:6,e:[
    ["Set pain candidate",2,"B","kg","Wdh"],["Unchanged exercise pain",1,"B","kg","Wdh"]]};
  const url=origin+"/kgg/?kggReactPad="+(react?"1":"0")+"&plan="+encodeURIComponent("KGGH2:"+encode(plan));
  try{
    await page.goto(url,{waitUntil:"domcontentloaded"});await ready(page);
    let card=await openCard(page);
    assert(await card.locator(".kggSetPain").count()===0,"default per-set mode unexpectedly enabled");
    assert(await card.locator(".pain").isVisible()||await card.locator(".kggPainVerticalToggle").isVisible(),"default exercise-pain control hidden");
    assert(await page.locator("#list .ex").nth(1).locator(".kggSetPain").count()===0,"unselected second exercise changed");
    card=await mode(page,"set");
    const stored=await page.evaluate(()=>JSON.parse(localStorage.getItem("kggPatientExerciseSettingsV1")||"{}"));
    assert(stored["pain-per-set-e2e|set pain candidate"]?.painMode==="set","pain-mode not persisted");
    assert(await card.locator(".kggSetPain").count()===2,"expected two per-set pain controls");
    await page.waitForFunction(()=>document.querySelectorAll("#list .ex")[0]?.querySelectorAll(".kggSetPain .kggPainVerticalToggle").length===2);
    const triggers=card.locator(".kggSetPain .kggPainVerticalToggle");
    assert(await triggers.count()===2,"expected one per-set bolt per set");
    const boltSizes=await triggers.evaluateAll(nodes=>nodes.map(n=>({width:n.getBoundingClientRect().width,height:n.getBoundingClientRect().height,text:n.querySelector(".kggPainCompactText")?.textContent||""})));
    assert(boltSizes.every(x=>x.width>=44&&x.width<=90&&x.height>=40&&x.text==="⚡"),"per-set bolt is not compact, tappable and unset: "+JSON.stringify(boltSizes));
    assert(await card.locator(".kggSetPain .kggPainScale").evaluateAll(nodes=>nodes.every(x=>x.hidden&&x.inert&&getComputedStyle(x).display==="none")),"legacy inline pain scale must be hidden but kept for set commit");
    assert(await card.locator(".pain").isHidden(),"exercise pain remains visible");
    assert(await page.locator("#list .ex").nth(1).locator(".kggSetPain").count()===0,"other exercise changed");
    await chooseSetPain(page,0,3);
    assert(await page.locator("#pad").evaluate(el=>el.classList.contains("hide")),
      "pain-scale tap opened the NumPad");
    await chooseSetPain(page,1,8);
    assert(await page.locator("#pad").evaluate(el=>el.classList.contains("hide")),
      "second pain-scale tap opened the NumPad");
    let values=await selected(page);
    assert(JSON.stringify(values)===JSON.stringify(["3","8"]),"set pain not independent: "+JSON.stringify(values));
    const state=await page.evaluate(()=>({
      day:d,first:v[k(0,1,"P","pain")],second:v[k(0,2,"P","pain")],
      other:v[k(1,0,"P","pain")]
    }));
    assert(state.first==="3"&&state.second==="8"&&state.other===undefined,"state pollution: "+JSON.stringify(state));
    await page.locator("#days button").nth(1).evaluate(el=>el.click());await openCard(page);
    assert(await page.evaluate(()=>d)===2,"did not enter day 2");
    values=await selected(page);
    assert(JSON.stringify(values)===JSON.stringify(["0","0"]),"day 2 reused day 1: "+JSON.stringify(values));
    await chooseSetPain(page,0,5);
    assert(await page.evaluate(()=>v[k(0,1,"P","pain")])==="5","day 2 value not saved");
    await page.locator("#days button").nth(0).evaluate(el=>el.click());await openCard(page);
    values=await selected(page);
    assert(JSON.stringify(values)===JSON.stringify(["3","8"]),"day 1 overwritten after day switch: "+JSON.stringify(values));
    assert((await page.locator("#list .ex").first().locator(".kggSetPain .kggPainCompactText").first().textContent())==="3⚡","day 1 per-set bolt did not restore its independent value");
    await page.reload({waitUntil:"domcontentloaded"});await ready(page);await openCard(page);
    values=await selected(page);
    assert(JSON.stringify(values)===JSON.stringify(["3","8"]),"pain not persistent on reload: "+JSON.stringify(values));
    await page.waitForFunction(()=>document.querySelectorAll("#list .ex")[0]?.querySelectorAll(".kggSetPain .kggPainVerticalToggle").length===2);
    card=await mode(page,"exercise");
    assert(await card.locator(".kggSetPain").count()===0,"per-set remained after disable");
    assert(await card.locator(".pain").isVisible()||await card.locator(".kggPainVerticalToggle").isVisible(),"exercise pain not restored");
    await mode(page,"set");
    values=await selected(page);
    assert(JSON.stringify(values)===JSON.stringify(["3","8"]),"toggle destroyed per-set data");
    assert(await page.locator("#list .ex").first().locator(".kggSetPain .kggPainVerticalToggle").count()===2,"reactivated per-set mode lost the bolt triggers");
    assert(errors.length===0,"page errors: "+JSON.stringify(errors));
    console.log("Patient per-set pain opt-in regression: PASS ("+(react?"React opt-in":"Legacy")+")");
  }finally{await context.close()}
}
async function main(){
  const server=http.createServer((req,res)=>{
    const file=fileFor(req.url);
    if(!file){res.writeHead(404);res.end("404");return}
    res.writeHead(200,{"Content-Type":mime(file),"Cache-Control":"no-store","Service-Worker-Allowed":"/"});
    fs.createReadStream(file).pipe(res);
  });
  await new Promise(resolve=>server.listen(0,"127.0.0.1",resolve));
  let browser;
  try{
    const engine=process.env.KGG_PAIN_BROWSER||"chromium";
    assert(engine==="chromium"||engine==="webkit","unsupported pain-test browser "+engine);
    browser=await ({chromium,webkit})[engine].launch({headless:true});
    const origin="http://127.0.0.1:"+server.address().port;
    await caseTest(browser,origin,false);
    await caseTest(browser,origin,true);
  }finally{if(browser)await browser.close();await new Promise(resolve=>server.close(resolve))}
}
const alarm=setTimeout(()=>{console.error("Patient per-set pain regression: bounded 90s timeout");process.exit(124)},90000);
main().then(()=>clearTimeout(alarm)).catch(error=>{
  clearTimeout(alarm);console.error("Patient per-set pain regression: FAIL "+(error.stack||error));process.exitCode=1;
});
