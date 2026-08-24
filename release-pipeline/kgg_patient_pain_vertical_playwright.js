#!/usr/bin/env node
"use strict";

const fs = require("fs");
const http = require("http");
const path = require("path");
const { chromium } = require("playwright");

const ROOT = path.resolve(__dirname, "..");
function assert(condition, message) { if (!condition) throw new Error(message); }
function encodePlan(plan) { return Buffer.from(JSON.stringify(plan), "utf8").toString("base64url"); }
function contentType(filename) {
  return { ".html":"text/html; charset=utf-8", ".js":"text/javascript; charset=utf-8", ".json":"application/json; charset=utf-8", ".webmanifest":"application/manifest+json; charset=utf-8", ".png":"image/png" }[path.extname(filename).toLowerCase()] || "application/octet-stream";
}
function safeFile(urlPath) {
  const pathname = decodeURIComponent(String(urlPath || "/").split("?")[0]).replace(/^\/+/, "");
  const relative = pathname.replace(/^kgg\/?/, "") || "index.html";
  const target = path.resolve(ROOT, relative);
  if ((!target.startsWith(`${ROOT}${path.sep}`) && target !== ROOT) || !fs.existsSync(target) || !fs.statSync(target).isFile()) return null;
  return target;
}
async function waitForRuntime(page) {
  await page.evaluate(() => navigator.serviceWorker.ready);
  if (!(await page.evaluate(() => Boolean(navigator.serviceWorker.controller)))) await page.reload({ waitUntil:"domcontentloaded" });
  await page.waitForFunction(() => Boolean(navigator.serviceWorker.controller), null, { timeout:12000 });
  for (let attempt=0; attempt<4; attempt+=1) {
    await page.locator("#plan").waitFor({ state:"visible" });
    if (await page.locator("#list .ex .kggPainVerticalToggle").count()) return;
    await page.reload({ waitUntil:"domcontentloaded" });
  }
  const diagnostics = await page.evaluate(() => ({ scripts:[...document.scripts].map(s=>s.src).filter(Boolean), body:document.body.className }));
  throw new Error(`vertical pain runtime was not injected: ${JSON.stringify(diagnostics)}`);
}
async function setCardOpen(page, _card, index, open) {
  for (let attempt=0; attempt<4; attempt+=1) {
    const card=page.locator("#list .ex").nth(index);
    await card.waitFor({state:"attached",timeout:5000});
    const isOpen=await card.evaluate(el=>el.classList.contains("kggOpen"));
    if (isOpen===open) return;
    const header=card.locator("h3");
    await header.waitFor({state:"attached",timeout:5000});
    await header.evaluate(element=>element.click());
    try {
      await page.waitForFunction(({index,open})=>Boolean(document.querySelectorAll("#list .ex")[index]?.classList.contains("kggOpen"))===open,{index,open},{timeout:1500});
      return;
    } catch (error) {
      await page.waitForTimeout(60);
    }
  }
  const diagnostic=await page.evaluate(({index,open})=>({
    index,open,
    cardCount:document.querySelectorAll("#list .ex").length,
    classes:document.querySelectorAll("#list .ex")[index]?.className||"",
    hasHeader:Boolean(document.querySelectorAll("#list .ex")[index]?.querySelector("h3")),
  }),{index,open});
  throw new Error(`card open state did not stabilize: ${JSON.stringify(diagnostic)}`);
}
async function openModal(toggle, modal) {
  if ((await toggle.getAttribute("aria-expanded")) !== "true") await toggle.click();
  await modal.waitFor({ state:"visible" });
}
async function chooseValue(page, value) {
  const modal=page.locator("#kggPainModal");
  await modal.locator(`.kggPainVerticalValue[data-kgg-pain-value="${value}"]`).click();
  await page.waitForFunction(({ value }) => document.querySelector("#kggPainModal .kggPainVerticalStage")?.getAttribute("aria-valuenow") === String(value), { value });
}
async function pointerDrag(stage, x, startY, endY, steps=8) {
  await stage.evaluate((element, gesture) => {
    const dispatch=(type,y,buttons)=>element.dispatchEvent(new PointerEvent(type,{
      bubbles:true,cancelable:true,composed:true,pointerId:91,pointerType:"touch",
      isPrimary:true,button:0,buttons,clientX:gesture.x,clientY:y
    }));
    dispatch("pointerdown",gesture.startY,1);
    for(let step=1;step<=gesture.steps;step+=1){
      const y=gesture.startY+(gesture.endY-gesture.startY)*(step/gesture.steps);
      dispatch("pointermove",y,1);
    }
    dispatch("pointerup",gesture.endY,0);
  },{x,startY,endY,steps});
}
async function main() {
  const server = http.createServer((request,response) => {
    const file=safeFile(request.url);
    if(!file){response.writeHead(404,{"Content-Type":"text/plain"});response.end("not found");return;}
    response.writeHead(200,{"Content-Type":contentType(file),"Cache-Control":"no-store","Service-Worker-Allowed":"/"});
    fs.createReadStream(file).pipe(response);
  });
  await new Promise(resolve=>server.listen(0,"127.0.0.1",resolve));
  const {port}=server.address();
  const browser=await chromium.launch({headless:true});
  const context=await browser.newContext({viewport:{width:390,height:844},serviceWorkers:"allow",hasTouch:true});
  const page=await context.newPage();
  const plan={i:"vertical-pain-playwright",t:"Vertikale Schmerzskala",v:1,d:6,e:[["Beinpresse",1,"B","kg","Wdh"],["Satzschmerz",2,"B","kg","Wdh"]]};
  const payload=`KGGH2:${encodePlan(plan)}`;
  const url=`http://127.0.0.1:${port}/kgg/?plan=${encodeURIComponent(payload)}`;
  await page.addInitScript(() => {
    localStorage.setItem("kggPatientExerciseSettingsV1", JSON.stringify({"vertical-pain-playwright|satzschmerz":{painMode:"set"}}));
  });
  try {
    await page.goto(url,{waitUntil:"domcontentloaded"});
    await waitForRuntime(page);
    const cards=page.locator("#list .ex");
    assert(await cards.count()===2,"expected two exercise cards");
    const first=cards.nth(0),second=cards.nth(1);
    await setCardOpen(page,first,0,true);
    const toggle=first.locator(".kggPainVerticalToggle");
    const modal=page.locator("#kggPainModal");
    await toggle.waitFor({state:"visible"});
    assert((await first.locator(".kggPainVerticalLabel").innerText())==="Schmerzen bei der Übung?","compact label is wrong");
    assert((await first.locator(".kggPainVerticalCurrent").innerText())==="–","unset value must show a dash");
    assert((await toggle.getAttribute("aria-expanded"))==="false","scale must start closed");
    assert(await page.locator("#kggPainModal").count()===1,"floating pain modal must be a singleton");
    const legacy=first.locator(":scope > .pain > .painRow");
    assert(await legacy.isHidden(),"legacy horizontal scale is still visible");
    assert(await legacy.evaluate(el=>el.inert===true&&el.getAttribute("aria-hidden")==="true"),"legacy scale is not inert and aria-hidden");
    assert(await second.locator(".kggSetPain").count()>0,"set-pain mode was not created");
    assert(await second.locator(".kggPainVertical").count()===0,"exercise-pain trigger must not appear in set-pain mode");

    await page.evaluate(()=>window.scrollTo(0,Math.min(250,document.documentElement.scrollHeight-window.innerHeight)));
    await page.waitForTimeout(380);
    const before=await page.evaluate(()=>{
    const cards=[...document.querySelectorAll("#list .ex")];
    const layoutTop=element=>{let top=0;for(let node=element;node;node=node.offsetParent)top+=node.offsetTop;return top};
    return{scrollY:window.scrollY,firstHeight:cards[0].offsetHeight,secondLayoutTop:layoutTop(cards[1])};
  });
    await openModal(toggle,modal);
    await page.waitForTimeout(220);
    const after=await page.evaluate(()=>{
    const cards=[...document.querySelectorAll("#list .ex")];
    const layoutTop=element=>{let top=0;for(let node=element;node;node=node.offsetParent)top+=node.offsetTop;return top};
    return{firstHeight:cards[0].offsetHeight,secondLayoutTop:layoutTop(cards[1]),bodyPosition:getComputedStyle(document.body).position};
  });
    assert(before.firstHeight===after.firstHeight,`opening modal changed exercise-card height: ${JSON.stringify({before,after})}`);
    assert(before.secondLayoutTop===after.secondLayoutTop,`opening modal shifted following exercise: ${JSON.stringify({before,after})}`);
    assert(after.bodyPosition==="fixed","background scroll was not locked");
    const modalStyle=await modal.evaluate(el=>{const s=getComputedStyle(el);return{position:s.position,zIndex:Number(s.zIndex),backdrop:s.backdropFilter||s.webkitBackdropFilter,background:s.backgroundColor}});
    assert(modalStyle.position==="fixed","pain window is not a fixed overlay");
    assert(modalStyle.zIndex===9500,"pain overlay z-index contract changed");
    assert(modalStyle.backdrop&&modalStyle.backdrop!=="none","pain overlay has no blur");
    assert((await modal.locator("#kggPainModalTitle").innerText())==="Schmerzen bei der Übung?","modal title is wrong");
    assert((await modal.locator("#kggPainModalMaxDescription").innerText())==="Schlimmster vorstellbarer Schmerz","maximum description is wrong");
    assert((await modal.locator("#kggPainModalMinDescription").innerText())==="Gar kein Schmerz","minimum description is wrong");
    const maxDescBox=await modal.locator("#kggPainModalMaxDescription").boundingBox();
    const minDescBox=await modal.locator("#kggPainModalMinDescription").boundingBox();
    const tenBox=await modal.locator('[data-kgg-pain-value="10"]').boundingBox();
    const zeroBox=await modal.locator('[data-kgg-pain-value="0"]').boundingBox();
    assert(maxDescBox&&tenBox&&maxDescBox.y+maxDescBox.height<=tenBox.y+1,"maximum description is not above 10");
    assert(minDescBox&&zeroBox&&minDescBox.y>=zeroBox.y+zeroBox.height-1,"minimum description is not below 0");
    const compactGeometry=await page.evaluate(()=>{
      const dialog=document.getElementById('kggPainModalDialog')?.getBoundingClientRect();
      const body=document.querySelector('#kggPainModalDialog .kggPainModalBody')?.getBoundingClientRect();
      const stage=document.querySelector('#kggPainModalDialog .kggPainVerticalStage')?.getBoundingClientRect();
      const close=document.querySelector('#kggPainModalDialog .kggPainModalClose');
      return dialog&&body&&stage?{dialogWidth:dialog.width,bodyWidth:body.width,stageWidth:stage.width,leftGap:body.left-dialog.left,rightGap:dialog.right-body.right,closePosition:close?getComputedStyle(close).position:''}:null;
    });
    assert(compactGeometry&&compactGeometry.dialogWidth<=200,`compact dialog is still too wide: ${JSON.stringify(compactGeometry)}`);
    assert(compactGeometry&&compactGeometry.bodyWidth>=144&&compactGeometry.stageWidth/compactGeometry.bodyWidth>=.98,`slider does not use compact modal body: ${JSON.stringify(compactGeometry)}`);
    assert(compactGeometry&&Math.abs(compactGeometry.leftGap-compactGeometry.rightGap)<=2,`compact content is not centered: ${JSON.stringify(compactGeometry)}`);
    assert(compactGeometry&&compactGeometry.closePosition==='absolute',`close button still occupies header flow: ${JSON.stringify(compactGeometry)}`);
    assert(await page.locator("body > *:not(#kggPainModal)[inert]").count()>0,"background content was not made inert");

    await chooseValue(page,7);
    assert((await first.locator(".kggPainVerticalCurrent").innerText())==="7/10","tap did not update compact value");
    assert(await modal.isVisible(),"modal auto-closed after choosing a value");
    assert((await toggle.getAttribute("aria-expanded"))==="true","trigger no longer reports open modal");
    assert((await first.locator(".kggCardProgress").getAttribute("data-kgg-progress"))==="open","pain alone changed exercise progress");

    const stage=modal.locator(".kggPainVerticalStage");
    const stageBox=await stage.boundingBox();assert(stageBox,"slider box missing for drag");
    await pointerDrag(stage,stageBox.x+35,stageBox.y+stageBox.height-stageBox.height/22,stageBox.y+stageBox.height/22,8);
    await page.waitForFunction(()=>document.querySelector("#list .ex .kggPainVerticalCurrent")?.textContent==="10/10");
    assert(await modal.isVisible(),"modal closed after pointer drag");

    const dialog=modal.locator("#kggPainModalDialog");
    await dialog.click({position:{x:20,y:20}});
    assert(await modal.isVisible(),"click inside dialog closed modal");
    await modal.click({position:{x:8,y:8}});
    await modal.waitFor({state:"hidden"});
    await page.waitForFunction(expected=>{
      const active=String(document.activeElement?.className||"");
      return Math.abs(window.scrollY-expected)<=1&&getComputedStyle(document.body).position!=="fixed"&&active.includes("kggPainVerticalToggle");
    },before.scrollY,{timeout:5000});
    const restored=await page.evaluate(()=>({scrollY:window.scrollY,bodyPosition:getComputedStyle(document.body).position,active:document.activeElement?.className||""}));
    assert(Math.abs(restored.scrollY-before.scrollY)<=1,`closing modal did not restore scroll position: ${JSON.stringify({before:before.scrollY,restored})}`);
    assert(restored.bodyPosition!=="fixed","closing modal did not unlock body");
    assert(String(restored.active).includes("kggPainVerticalToggle"),"focus did not return to pain trigger");

    await openModal(toggle,modal);
    await chooseValue(page,0);
    assert((await first.locator(".kggPainVerticalCurrent").innerText())==="0/10","selected zero was treated as unset");
    await modal.locator(".kggPainModalClose").click();
    await modal.waitFor({state:"hidden"});
    await page.reload({waitUntil:"domcontentloaded"});await waitForRuntime(page);
    const reloadedFirst=page.locator("#list .ex").nth(0);await setCardOpen(page,reloadedFirst,0,true);
    assert((await reloadedFirst.locator(".kggPainVerticalCurrent").innerText())==="0/10","zero did not persist after reload");

    const reloadedToggle=reloadedFirst.locator(".kggPainVerticalToggle");
    await openModal(reloadedToggle,page.locator("#kggPainModal"));
    await page.locator("#days button").nth(1).evaluate(element=>element.click());
    await page.waitForFunction(()=>typeof d!=="undefined"&&Number(d)===2);
    assert(await page.locator("#kggPainModal").isHidden(),"day change did not close pain modal");
    const dayTwoFirst=page.locator("#list .ex").nth(0);await setCardOpen(page,dayTwoFirst,0,true);
    assert((await dayTwoFirst.locator(".kggPainVerticalCurrent").innerText())==="–","day 2 inherited day 1 pain");
    await openModal(dayTwoFirst.locator(".kggPainVerticalToggle"),page.locator("#kggPainModal"));
    await chooseValue(page,4);
    await page.locator("#kggPainModal .kggPainModalClose").click();
    await page.locator("#days button").nth(0).evaluate(element=>element.click());
    await page.waitForFunction(()=>typeof d!=="undefined"&&Number(d)===1);
    const dayOneFirst=page.locator("#list .ex").nth(0);await setCardOpen(page,dayOneFirst,0,true);
    assert((await dayOneFirst.locator(".kggPainVerticalCurrent").innerText())==="0/10","day 1 pain was overwritten by day 2");
    assert(await page.locator("#kggPainModal").count()===1,"rerender created duplicate overlays");
    assert(await page.locator("#list .ex .kggPainVertical").count()===1,"rerender created duplicate or set-mode triggers");

    await page.setViewportSize({width:844,height:390});
    await openModal(dayOneFirst.locator(".kggPainVerticalToggle"),page.locator("#kggPainModal"));
    const shortViewport=await page.evaluate(()=>{
      const dialog=document.getElementById("kggPainModalDialog")?.getBoundingClientRect();
      const ten=document.querySelector('[data-kgg-pain-value="10"]')?.getBoundingClientRect();
      const zero=document.querySelector('[data-kgg-pain-value="0"]')?.getBoundingClientRect();
      return{dialog,ten,zero,height:innerHeight,width:document.documentElement.scrollWidth};
    });
    assert(shortViewport.dialog&&shortViewport.dialog.top>=0&&shortViewport.dialog.bottom<=shortViewport.height+1,"dialog overflows short viewport");
    assert(shortViewport.ten&&shortViewport.zero&&shortViewport.ten.top>=0&&shortViewport.zero.bottom<=shortViewport.height+1,"0 or 10 is unreachable in short viewport");
    assert(shortViewport.width<=844+1,"modal creates horizontal overflow");
    await page.setViewportSize({width:1024,height:768});await page.waitForTimeout(80);
    const wideCompact=await page.evaluate(()=>{
      const dialog=document.getElementById('kggPainModalDialog')?.getBoundingClientRect();
      const body=document.querySelector('#kggPainModalDialog .kggPainModalBody')?.getBoundingClientRect();
      return dialog&&body?{dialogWidth:dialog.width,bodyWidth:body.width,leftGap:body.left-dialog.left,rightGap:dialog.right-body.right,documentWidth:document.documentElement.scrollWidth}:null;
    });
    assert(wideCompact&&wideCompact.dialogWidth<=200&&wideCompact.bodyWidth>=149,`wide viewport reintroduced excess white space: ${JSON.stringify(wideCompact)}`);
    assert(wideCompact&&Math.abs(wideCompact.leftGap-wideCompact.rightGap)<=2,`wide compact content is not centered: ${JSON.stringify(wideCompact)}`);
    assert(wideCompact&&wideCompact.documentWidth<=1024+1,"wide compact modal creates horizontal overflow");
    console.log("Patient vertical pain floating modal Playwright smoke: PASS");
  } finally {
    await context.close();await browser.close();await new Promise(resolve=>server.close(resolve));
  }
}
main().catch(error=>{console.error(`Patient vertical pain floating modal Playwright smoke failed: ${error.stack||error.message}`);process.exitCode=1;});
