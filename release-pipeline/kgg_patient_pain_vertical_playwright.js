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
async function setCardOpen(page, card, index, open) {
  const isOpen = await card.evaluate(el => el.classList.contains("kggOpen"));
  if (isOpen !== open) await card.locator("h3").click();
  await page.waitForFunction(({ index, open }) => Boolean(document.querySelectorAll("#list .ex")[index]?.classList.contains("kggOpen")) === open, { index, open });
}
async function chooseValue(page, card, value) {
  const toggle = card.locator(".kggPainVerticalToggle");
  if ((await toggle.getAttribute("aria-expanded")) !== "true") await toggle.click();
  await card.locator(`.kggPainVerticalValue[data-kgg-pain-value="${value}"]`).click();
  await page.waitForFunction(({ value }) => document.querySelector("#list .ex .kggPainVerticalCurrent")?.textContent === `${value}/10`, { value });
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
  const context=await browser.newContext({viewport:{width:390,height:844},serviceWorkers:"allow"});
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
    await toggle.waitFor({state:"visible"});
    assert((await first.locator(".kggPainVerticalLabel").innerText())==="Schmerzen bei der Übung","compact label is wrong");
    assert((await first.locator(".kggPainVerticalCurrent").innerText())==="–","unset value must show a dash");
    assert((await toggle.getAttribute("aria-expanded"))==="false","scale must start closed");
    const legacy=first.locator(":scope > .pain > .painRow");
    assert(await legacy.isHidden(),"legacy horizontal scale is still visible");
    assert(await legacy.evaluate(el=>el.inert===true&&el.getAttribute("aria-hidden")==="true"),"legacy scale is not inert and aria-hidden");
    assert(await second.locator(".kggSetPain").count()>0,"set-pain mode was not created");
    assert(await second.locator(".kggPainVertical").count()===0,"exercise-pain slider must not appear in set-pain mode");

    await toggle.click();
    const stage=first.locator(".kggPainVerticalStage");
    await stage.waitFor({state:"visible"});
    const top=first.locator('.kggPainVerticalValue[data-kgg-pain-value="10"]');
    const bottom=first.locator('.kggPainVerticalValue[data-kgg-pain-value="0"]');
    const pain=first.locator(":scope > .pain");
    const topBox=await top.boundingBox(),bottomBox=await bottom.boundingBox(),stageBox=await stage.boundingBox(),painBox=await pain.boundingBox();
    assert(topBox&&bottomBox&&topBox.y<bottomBox.y,"10 must be above 0");
    assert(stageBox&&painBox&&Math.abs((painBox.x+painBox.width)-(stageBox.x+stageBox.width))<4,`vertical scale is not right aligned inside pain content: ${JSON.stringify({stageBox,painBox})}`);
    assert(stageBox&&painBox&&(stageBox.x+stageBox.width/2)>(painBox.x+painBox.width/2),"vertical scale is not in the right half of the pain content");
    assert(await stage.evaluate(el=>getComputedStyle(el).touchAction)==="none","slider touch zone must disable page scrolling");
    assert(await page.evaluate(()=>document.documentElement.scrollWidth<=window.innerWidth+1),"slider creates horizontal overflow");

    await first.locator('.kggPainVerticalValue[data-kgg-pain-value="7"]').click();
    await page.waitForFunction(()=>document.querySelector("#list .ex .kggPainVerticalCurrent")?.textContent==="7/10");
    assert((await first.locator(".kggCardProgress").getAttribute("data-kgg-progress"))==="open","pain alone changed exercise progress");

    await toggle.click();
    const box=await stage.boundingBox();assert(box,"slider box missing for drag");
    await page.mouse.move(box.x+35,box.y+box.height-22);await page.mouse.down();await page.mouse.move(box.x+35,box.y+22,{steps:8});await page.mouse.up();
    await page.waitForFunction(()=>document.querySelector("#list .ex .kggPainVerticalCurrent")?.textContent==="10/10");

    await chooseValue(page,first,0);
    assert((await first.locator(".kggPainVerticalCurrent").innerText())==="0/10","selected zero was treated as unset");
    await page.reload({waitUntil:"domcontentloaded"});await waitForRuntime(page);
    const reloadedFirst=page.locator("#list .ex").nth(0);await setCardOpen(page,reloadedFirst,0,true);
    assert((await reloadedFirst.locator(".kggPainVerticalCurrent").innerText())==="0/10","zero did not persist after reload");

    await page.locator("#days button").nth(1).click();
    await page.waitForFunction(()=>document.querySelector("#days button:nth-child(2)")?.classList.contains("active"));
    const dayTwoFirst=page.locator("#list .ex").nth(0);await setCardOpen(page,dayTwoFirst,0,true);
    assert((await dayTwoFirst.locator(".kggPainVerticalCurrent").innerText())==="–","day 2 inherited day 1 pain");
    await chooseValue(page,dayTwoFirst,4);
    await page.locator("#days button").nth(0).click();
    await page.waitForFunction(()=>document.querySelector("#days button:first-child")?.classList.contains("active"));
    const dayOneFirst=page.locator("#list .ex").nth(0);await setCardOpen(page,dayOneFirst,0,true);
    assert((await dayOneFirst.locator(".kggPainVerticalCurrent").innerText())==="0/10","day 1 pain was overwritten by day 2");
    assert(await page.locator("#list .ex .kggPainVertical").count()===1,"rerender created duplicate or set-mode sliders");
    console.log("Patient vertical pain Playwright smoke: PASS");
  } finally {
    await context.close();await browser.close();await new Promise(resolve=>server.close(resolve));
  }
}
main().catch(error=>{console.error(`Patient vertical pain Playwright smoke failed: ${error.stack||error.message}`);process.exitCode=1;});
