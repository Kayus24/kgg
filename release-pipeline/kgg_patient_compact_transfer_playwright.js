#!/usr/bin/env node
"use strict";
const fs=require("fs"),http=require("http"),path=require("path"),{chromium}=require("playwright");
const ROOT=path.resolve(__dirname,"..");
function assert(x,m){if(!x)throw new Error(m)}
function enc(plan){return Buffer.from(JSON.stringify(plan),"utf8").toString("base64url")}
function typeFor(f){return f.endsWith(".html")?"text/html; charset=utf-8":f.endsWith(".js")?"text/javascript; charset=utf-8":f.endsWith(".json")?"application/json; charset=utf-8":f.endsWith(".png")?"image/png":"application/octet-stream"}
function fileFor(url){const rel=decodeURIComponent(String(url||"/").split("?")[0]).replace(/^\/+/, "")||"index.html",target=path.resolve(ROOT,rel);return target.startsWith(ROOT)&&fs.existsSync(target)&&fs.statSync(target).isFile()?target:null}
async function openCard(card){for(let i=0;i<5;i++){if(await card.evaluate(e=>e.classList.contains("kggOpen")))return;await card.locator("h3").evaluate(el=>el.click());await card.page().waitForTimeout(100)}throw new Error("card open state did not stabilize")}
async function key(page,label){await page.locator("#pad .padGrid").getByRole("button",{name:label,exact:true}).click()}
async function seed(page){
 await page.evaluate(()=>{
  const putDay=(ei,s,side,key,value,day=1)=>{v[k(ei,s,side,key,day)]=String(value)};
  putDay(0,1,"B","a",15);putDay(0,1,"B","b",12);
  putDay(0,2,"B","a",20);putDay(0,2,"B","b",10);
  putDay(0,3,"B","a",25);
  putDay(1,1,"B","b",45);
  putDay(3,1,"B","b",14);
  putDay(2,1,"L","a",11);putDay(2,1,"L","b",8);
  putDay(2,1,"R","a",13);putDay(2,1,"R","b",9);
  d=2;done=[1];save();render();
 });
 await page.waitForTimeout(500);
}
async function load(browser,port){
 const ctx=await browser.newContext({viewport:{width:390,height:844},hasTouch:true,isMobile:true});
 const page=await ctx.newPage(),errors=[];page.on("pageerror",e=>errors.push(String(e)));
 const plan={i:"transfer-smoke",t:"Transfer Smoke",v:1,d:6,e:[
  ["Pair",3,"B","kg","Wdh"],
  ["Timer",1,"B","keine","Sek."],
  ["LR",1,"LR","kg","Wdh"],
  ["One prior",1,"B","kg","Wdh"]
 ]};
 await page.addInitScript(()=>{localStorage.clear();localStorage.kggInstallAsked="1"});
 await page.goto("http://127.0.0.1:"+port+"/?plan="+encodeURIComponent("KGGH2:"+enc(plan)),{waitUntil:"networkidle"});
 await page.waitForFunction(()=>document.body.classList.contains("kggAlwaysCollapsed"));await page.waitForTimeout(900);await seed(page);
 return{ctx,page,errors};
}
async function transferTexts(page){return page.locator("#kggPadTransfer > button:not(.kggTransferGhost)").allTextContents()}
async function pairInputs(card,setIndex){return card.locator(":scope > .set").nth(setIndex).locator("input.num")}
async function clickInput(page,input){
 const compact=await page.evaluate(()=>document.body.classList.contains("kggSetViewCompact"));
 if(!compact){await input.click();return}
 const proxyIndex=await input.evaluate(el=>[...el.parentElement.querySelectorAll(".kggCompactTapProxy")].findIndex(proxy=>proxy.__kggInput===el));
 assert(proxyIndex>=0,"compact input proxy missing");
 await input.locator("xpath=..").locator(".kggCompactTapProxy").nth(proxyIndex).click();
}
async function main(){
 const server=http.createServer((req,res)=>{const f=fileFor(req.url);if(!f){res.statusCode=404;return res.end("404")}res.setHeader("Content-Type",typeFor(f));res.setHeader("Cache-Control","no-store");res.end(fs.readFileSync(f))});
 await new Promise(r=>server.listen(0,"127.0.0.1",r));const port=server.address().port,browser=await chromium.launch({headless:true});
 try{
  const {ctx,page,errors}=await load(browser,port);
  try{
   const pair=page.locator("#list .ex").nth(0);await openCard(pair);
   const s1=await pairInputs(pair,0),kg=s1.nth(0),reps=s1.nth(1);
   const hints=await Promise.all([kg.getAttribute("placeholder"),reps.getAttribute("placeholder")]);
   assert(hints[0]==="15"&&hints[1]==="12","Compact prior hints must be numeric-only beside overlay units: "+JSON.stringify(hints));
   const unitColors=await Promise.all([
    kg.evaluate(el=>getComputedStyle(el,"::placeholder").color),
    pair.locator(":scope > .set").nth(0).locator(".kggCompactUnit[data-kgg-key=\"a\"]").evaluate(el=>getComputedStyle(el).color)
   ]);
   assert(unitColors[0]===unitColors[1],"suggested number and unit are not equally gray: "+JSON.stringify(unitColors));

   await clickInput(page,kg);await page.waitForTimeout(100);
   let pairValues=(await page.locator("#kggPadPair .kggPairValue").allTextContents()).map(x=>x.trim());
   assert(JSON.stringify(pairValues)===JSON.stringify(["–","–"]),"empty pair header must show dashes, not the numpad buffer: "+JSON.stringify(pairValues));
   assert(await page.locator("#kggPadTransfer").count()===1,"transfer strip missing");
   assert(await page.locator("#padLast").isHidden(),"legacy padLast must stay hidden in Compact mode");
   assert((await page.locator("#kggPadTransfer").getAttribute("data-active-key"))==="a","transfer pointer is not associated with active kg field");
   const initialPointer=await page.evaluate(()=>{const t=document.querySelector("#kggPadTransfer"),h=document.querySelector('#kggPadPair .kggPairField[data-kgg-key="a"]');if(!t||!h)return null;const tr=t.getBoundingClientRect(),hr=h.getBoundingClientRect(),ps=getComputedStyle(t,"::before");return{key:t.dataset.pointerKey||"",pointerX:tr.left+parseFloat(ps.left||"0"),headX:hr.left+hr.width/2}});
   assert(initialPointer&&initialPointer.key==="a"&&Math.abs(initialPointer.pointerX-initialPointer.headX)<=4,"initial kg pointer is not under kg header: "+JSON.stringify(initialPointer));
   let labels=(await transferTexts(page)).map(x=>x.trim());
   assert(JSON.stringify(labels)===JSON.stringify(["15 kg","Übernehmen","12 Wdh"]),"two-value transfer layout wrong: "+JSON.stringify(labels));
   await page.locator('#kggPadTransfer button[data-kgg-transfer-key="a"]').click();await page.waitForTimeout(80);
   assert(!(await page.locator("#pad").evaluate(el=>el.classList.contains("hide"))),"pad closed after only kg was completed");
   labels=(await transferTexts(page)).map(x=>x.trim());
   assert(JSON.stringify(labels)===JSON.stringify(["12 Wdh"]),"remaining Wdh transfer did not become the only button: "+JSON.stringify(labels));
   const wdhPointer=await page.evaluate(()=>{const t=document.querySelector("#kggPadTransfer"),h=document.querySelector('#kggPadPair .kggPairField[data-kgg-key="b"]');if(!t||!h)return null;const tr=t.getBoundingClientRect(),hr=h.getBoundingClientRect(),ps=getComputedStyle(t,"::before");return{key:t.dataset.pointerKey||"",pointerX:tr.left+parseFloat(ps.left||"0"),headX:hr.left+hr.width/2,animating:t.dataset.animating||"",animations:[...t.querySelectorAll("button")].reduce((n,b)=>n+b.getAnimations().length,0)}});
   assert(wdhPointer&&wdhPointer.key==="b","remaining Wdh transfer did not retarget pointer to Wdh: "+JSON.stringify(wdhPointer));
   assert(wdhPointer.animating==="1"||wdhPointer.animations>0,"remaining Wdh transfer did not animate its morph: "+JSON.stringify(wdhPointer));
   await page.waitForTimeout(220);
   const wdhPointerFinal=await page.evaluate(()=>{const t=document.querySelector("#kggPadTransfer"),h=document.querySelector('#kggPadPair .kggPairField[data-kgg-key="b"]');const tr=t.getBoundingClientRect(),hr=h.getBoundingClientRect(),ps=getComputedStyle(t,"::before");return{pointerX:tr.left+parseFloat(ps.left||"0"),headX:hr.left+hr.width/2}});
   assert(Math.abs(wdhPointerFinal.pointerX-wdhPointerFinal.headX)<=4,"remaining Wdh pointer did not finish under Wdh header: "+JSON.stringify(wdhPointerFinal));
   assert((await kg.inputValue())==="15","kg transfer did not commit 15");
   const committedColors=await Promise.all([kg.evaluate(el=>getComputedStyle(el).color),pair.locator(":scope > .set").nth(0).locator(".kggCompactUnit[data-kgg-key=\"a\"]").evaluate(el=>getComputedStyle(el).color)]);
   assert(committedColors[0]===committedColors[1],"committed kg number/unit are not equally black: "+JSON.stringify(committedColors));
   await page.locator('#kggPadTransfer button[data-kgg-transfer-key="b"]').click();await page.waitForTimeout(100);
   assert(await page.locator("#pad").evaluate(el=>el.classList.contains("hide")),"pad did not close after pair became complete");
   assert((await reps.inputValue())==="12","Wdh transfer did not commit 12");

   const s2=await pairInputs(pair,1);await clickInput(page,s2.nth(1));await page.waitForTimeout(80);
   await page.locator('#kggPadTransfer button[data-kgg-transfer-key="b"]').click();await page.waitForTimeout(60);
   labels=(await transferTexts(page)).map(x=>x.trim());assert(JSON.stringify(labels)===JSON.stringify(["20 kg"]),"reverse transfer did not leave kg centered: "+JSON.stringify(labels));
   let kgPointer=await page.evaluate(()=>{const t=document.querySelector("#kggPadTransfer"),h=document.querySelector('#kggPadPair .kggPairField[data-kgg-key="a"]');if(!t||!h)return null;const tr=t.getBoundingClientRect(),hr=h.getBoundingClientRect(),ps=getComputedStyle(t,"::before");return{key:t.dataset.pointerKey||"",pointerX:tr.left+parseFloat(ps.left||"0"),headX:hr.left+hr.width/2}});
   assert(kgPointer&&kgPointer.key==="a","remaining kg transfer did not retarget pointer to kg: "+JSON.stringify(kgPointer));
   await page.waitForTimeout(220);
   kgPointer=await page.evaluate(()=>{const t=document.querySelector("#kggPadTransfer"),h=document.querySelector('#kggPadPair .kggPairField[data-kgg-key="a"]');const tr=t.getBoundingClientRect(),hr=h.getBoundingClientRect(),ps=getComputedStyle(t,"::before");return{pointerX:tr.left+parseFloat(ps.left||"0"),headX:hr.left+hr.width/2}});
   assert(Math.abs(kgPointer.pointerX-kgPointer.headX)<=4,"remaining kg pointer did not finish under kg header: "+JSON.stringify(kgPointer));
   await page.locator('#kggPadTransfer button[data-kgg-transfer-key="a"]').click();await page.waitForTimeout(80);
   assert(await page.locator("#pad").evaluate(el=>el.classList.contains("hide")),"reverse order did not close after completion");
   assert((await s2.nth(0).inputValue())==="20"&&(await s2.nth(1).inputValue())==="10","reverse transfer values wrong: "+JSON.stringify([await s2.nth(0).inputValue(),await s2.nth(1).inputValue()]));

   const s3=await pairInputs(pair,2);await clickInput(page,s3.nth(1));await key(page,"7");await page.waitForTimeout(80);
   labels=(await transferTexts(page)).map(x=>x.trim());
   assert(JSON.stringify(labels)===JSON.stringify(["25 kg"]),"dirty manual metric should remove center/current-field transfer: "+JSON.stringify(labels));
   await page.locator('#kggPadTransfer button[data-kgg-transfer-key="a"]').click();await page.waitForTimeout(100);
   assert(await page.locator("#pad").evaluate(el=>el.classList.contains("hide")),"manual+transfer complete pair did not close");
   assert((await s3.nth(0).inputValue())==="25"&&(await s3.nth(1).inputValue())==="7","manual buffer was lost or phantom value written");

   const one=page.locator("#list .ex").nth(3);await openCard(one);const oneInputs=one.locator("input.num");await clickInput(page,oneInputs.nth(0));await page.waitForTimeout(80);
   labels=(await transferTexts(page)).map(x=>x.trim());
   assert(JSON.stringify(labels)===JSON.stringify(["14 Wdh"]),"one-prior layout wrong: "+JSON.stringify(labels));
   assert(await page.locator("#kggPadTransfer .kggTransferBoth").count()===0,"center transfer shown with one prior");
   await page.locator('#kggPadTransfer button[data-kgg-transfer-key="b"]').click();await page.waitForTimeout(100);
   assert((await oneInputs.nth(0).inputValue())===""&&(await oneInputs.nth(1).inputValue())==="14","untouched field or sibling transfer state wrong");
   assert(!(await page.locator("#pad").evaluate(el=>el.classList.contains("hide"))),"pad closed with incomplete pair");
   await page.evaluate(()=>closePad(false));await page.waitForTimeout(80);

   const timer=page.locator("#list .ex").nth(1);await openCard(timer);const timerInput=timer.locator("input.num:not(.kggUnitInactive)").first();await clickInput(page,timerInput);await page.waitForTimeout(80);
   labels=(await transferTexts(page)).map(x=>x.trim());assert(JSON.stringify(labels)===JSON.stringify(["45 Sek."]),"single-field transfer wrong: "+JSON.stringify(labels));
   await page.locator("#kggPadTransfer button").click();await page.waitForTimeout(80);
   assert(await page.locator("#pad").evaluate(el=>el.classList.contains("hide")),"single-field transfer did not close");
   assert((await timerInput.inputValue())==="45","single-field transfer value wrong");

   const lr=page.locator("#list .ex").nth(2);await openCard(lr);const left=lr.locator(".kggSideL").first().locator("input.num");await clickInput(page,left.nth(0));await page.waitForTimeout(80);
   labels=(await transferTexts(page)).map(x=>x.trim());
   assert(labels.includes("11 kg")&&labels.includes("8 Wdh")&&!labels.includes("13 kg")&&!labels.includes("9 Wdh"),"LR transfer mixed opposite-side history: "+JSON.stringify(labels));
   await page.locator('#kggPadTransfer button[data-kgg-transfer-both="1"]').click();await page.waitForTimeout(80);
   assert(await page.locator("#pad").evaluate(el=>el.classList.contains("hide")),"center Übernehmen did not close the numpad immediately");
   assert((await left.nth(0).inputValue())==="11"&&(await left.nth(1).inputValue())==="8","LR center transfer wrong");
   const right=lr.locator(".kggSideR").first().locator("input.num");assert((await right.nth(0).inputValue())===""&&(await right.nth(1).inputValue())==="","LR center transfer polluted opposite side");
   assert(errors.length===0,"page errors: "+errors.join(" | "));
   console.log("Patient compact previous-value transfer Playwright: PASS");
  }finally{await ctx.close()}
 }finally{await browser.close();await new Promise(r=>server.close(r))}
}
main().catch(e=>{console.error("Patient compact previous-value transfer Playwright FAIL: "+(e.stack||e.message));process.exitCode=1});
