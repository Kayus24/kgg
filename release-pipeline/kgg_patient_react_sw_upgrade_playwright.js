#!/usr/bin/env node
"use strict";
// Synthetic browser regression for PR329: an installed v93 worker must not
// consume the only React cache request intended for its waiting successor.
const fs = require("node:fs");
const path = require("node:path");
const http = require("node:http");
const assert = require("node:assert/strict");
const {execFileSync} = require("node:child_process");
const {chromium} = require("playwright");
const ROOT = path.resolve(__dirname, "..");
const oldWorker = execFileSync("git", ["show", "a237aa2a9737a5b83eb6bb069f820cb8ce8653fd:service-worker.js"], {cwd:ROOT, encoding:"utf8"});
const candidateWorker = fs.readFileSync(path.join(ROOT,"service-worker.js"),"utf8");
const negativeControl = process.env.KGG_SW_UPGRADE_NEGATIVE_CONTROL === "1";
const candidateHtml = negativeControl
  ? execFileSync("git",["show","ec10a9d14a239eae842a90e8cfcf6fa849ec005d:index.html"],{cwd:ROOT,encoding:"utf8"})
  : fs.readFileSync(path.join(ROOT,"index.html"),"utf8");
const targetVersion = candidateWorker.match(/const APP_VERSION = '(\d+)';/)[1];
const targetCache = candidateWorker.match(/const CACHE_NAME = '([^']+)';/)[1];
const assets = ["patient-react-dist/kgg-patient-ui.js?v=p8-d14-react-grid-1","patient-react-dist/kgg-patient-ui.css?v=p8-d14-react-grid-1"];
const mime = {".html":"text/html; charset=utf-8",".js":"text/javascript; charset=utf-8",".css":"text/css",".json":"application/json",".png":"image/png",".svg":"image/svg+xml",".webmanifest":"application/manifest+json"};
function localWorker(text) { return text.replace("'https://cdn.jsdelivr.net/npm/qrcode-generator@1.4.4/qrcode.js'","'./patient-qr-format.js'"); }
async function workerVersion(page) {
  return page.evaluate(() => new Promise(resolve => {
    const worker = navigator.serviceWorker.controller;
    if (!worker) return resolve("");
    const channel = new MessageChannel();
    const timer = setTimeout(() => resolve(""),1500);
    channel.port1.onmessage = event => {clearTimeout(timer);resolve(String(event.data.version || ""));};
    worker.postMessage({type:"GET_APP_VERSION"},[channel.port2]);
  }));
}
async function pollAsync(check, label, timeout=10000) {
  const deadline=Date.now()+timeout;
  while(Date.now()<deadline){try {if(await check())return;} catch(error){if(!/Execution context was destroyed/.test(error.message))throw error;}await new Promise(resolve=>setTimeout(resolve,100));}
  throw new Error(label+": timed out");
}
async function scenario(browser, updateAfterLoad) {
  let serveNew = false;
  const server = http.createServer((req,res) => {
    try {
      const url = new URL(req.url,"http://localhost");
      if (!url.pathname.startsWith("/kgg/")) return res.writeHead(404).end();
      const relative = url.pathname.slice(5) || "index.html";
      if (relative === "prep.html") return res.writeHead(200,{"Content-Type":"text/html"}).end("<!doctype html><title>Synthetic SW test</title>");
      if (relative === "service-worker.js") return res.writeHead(200,{"Content-Type":"text/javascript","Cache-Control":"no-store"}).end(localWorker(serveNew ? candidateWorker : oldWorker));
      if (relative === "index.html") return res.writeHead(200,{"Content-Type":"text/html","Cache-Control":"no-store"}).end(candidateHtml);
      const file = path.resolve(ROOT,relative);
      if (!file.startsWith(ROOT+path.sep) || !fs.existsSync(file) || !fs.statSync(file).isFile()) return res.writeHead(404).end();
      res.writeHead(200,{"Content-Type":mime[path.extname(file)] || "application/octet-stream","Cache-Control":"no-store"});
      fs.createReadStream(file).pipe(res);
    } catch (_) {res.writeHead(400).end();}
  });
  await new Promise(resolve => server.listen(0,"127.0.0.1",resolve));
  const base = "http://127.0.0.1:"+server.address().port+"/kgg/";
  const context = await browser.newContext({viewport:{width:390,height:844},serviceWorkers:"allow"});
  try {
    await context.route("https://cdn.jsdelivr.net/**",route => route.fulfill({status:200,contentType:"text/javascript",body:""}));
    const setup = await context.newPage();
    await setup.goto(base+"prep.html");
    await setup.evaluate(() => navigator.serviceWorker.register("./service-worker.js"));
    await setup.waitForFunction(() => !!navigator.serviceWorker.controller,null,{timeout:15000});
    assert.equal(await workerVersion(setup),"93","baseline v93 must be active");
    const update = async () => {
      serveNew = true;
      await setup.evaluate(async () => (await navigator.serviceWorker.getRegistration("./")).update());
      await pollAsync(()=>setup.evaluate(async()=>!!(await navigator.serviceWorker.getRegistration("./")).waiting),"candidate worker must be waiting",15000);
    };
    if (!updateAfterLoad) await update();
    const plan = {i:"synthetic-worker-upgrade",t:"SYNTHETIC WORKER UPGRADE",v:1,d:3,e:[["Beinpresse",1,"B","kg","Wdh"]]};
    const page = await context.newPage();
    await page.goto(base+"?kggReactPad=1&kggReactGrid=1&plan="+encodeURIComponent("KGGH2:"+Buffer.from(JSON.stringify(plan)).toString("base64url")),{waitUntil:"domcontentloaded"});
    await page.waitForFunction(() => document.body.classList.contains("kggReactNumpadGridV1"),null,{timeout:12000});
    assert.equal(await workerVersion(page),"93","v93 remains controller while v94 waits");
    await page.evaluate(() => {put(0,1,"B","a","52");put(0,1,"B","b","12");});
    if (updateAfterLoad) await update();
    // Old and new caches are distinct. Finding an asset only in old cache is not PASS.
    await pollAsync(()=>page.evaluate(async({cacheName,assets})=>{
      const cache=await caches.open(cacheName);
      return (await Promise.all(assets.map(a=>cache.match(new URL(a,location.href).href)))).every(Boolean);
    },{cacheName:targetCache,assets}),"waiting candidate cache must contain both React assets",6000);
    await page.locator("#kggUpdateGateButton").waitFor({state:"visible",timeout:6000});
    await Promise.all([page.waitForNavigation({waitUntil:"domcontentloaded",timeout:15000}),page.locator("#kggUpdateGateButton").click()]);
    try { await pollAsync(async()=>await workerVersion(page)===targetVersion,"new worker must control client"); }
    catch(error){
      console.error("WORKER_STATE "+JSON.stringify(await page.evaluate(async()=>{
 const r=await navigator.serviceWorker.getRegistration("./");
 const query=w=>new Promise(resolve=>{if(!w)return resolve(null);const c=new MessageChannel(),t=setTimeout(()=>resolve("no-response"),1000);c.port1.onmessage=e=>{clearTimeout(t);resolve(e.data.version)};w.postMessage({type:"GET_APP_VERSION"},[c.port2])});
 return {url:location.href,controller:await query(navigator.serviceWorker.controller),active:await query(r.active),waiting:await query(r.waiting),message:document.querySelector("#kggUpdateGateStatus")?.textContent,button:document.querySelector("#kggUpdateGateButton")?.textContent,pad:document.querySelector("#pad")?.className,caches:await caches.keys()};
})));
      throw error;
    }
    assert.equal(await workerVersion(page),targetVersion);
    await context.setOffline(true);
    await page.goto(base+"?kggReactPad=1&kggReactGrid=1",{waitUntil:"domcontentloaded",timeout:12000});
    await page.waitForFunction(() => document.body.classList.contains("kggReactNumpadGridV1"),null,{timeout:10000});
    const offline = await page.evaluate(() => ({keys:document.querySelectorAll(".kgg-react-numpad-grid__key").length,css:getComputedStyle(document.querySelector(".kgg-react-numpad-grid")).display,kg:v["1|0|1|B|a"],reps:v["1|0|1|B|b"]}));
    assert.deepEqual(offline,{keys:12,css:"grid",kg:"52",reps:"12"},"offline P8 must retain CSS, keys and training");
    console.log(JSON.stringify({status:"PASS",test:"react-sw-upgrade",updateAfterLoad,oldVersion:"93",targetVersion,offline,syntheticOnly:true}));
  } finally {
    await context.setOffline(false);
    await context.close();
    server.closeAllConnections();
    await new Promise(resolve => server.close(resolve));
  }
}
(async () => {
  const browser = await chromium.launch({headless:true});
  try {await scenario(browser,false);await scenario(browser,true);} finally {await browser.close();}
})().catch(error => {console.error("React SW upgrade FAIL: "+(error.stack || error));process.exitCode=1;});
