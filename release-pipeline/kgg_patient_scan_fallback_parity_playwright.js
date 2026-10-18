#!/usr/bin/env node
"use strict";
// Synthetic permission-denied scanner fallback parity. No real camera or patient data.
const fs=require("node:fs"),path=require("node:path"),http=require("node:http");
const {chromium,webkit}=require("playwright");
const ROOT=path.resolve(__dirname,"..");
const ENGINE=process.env.KGG_SCAN_FALLBACK_BROWSER||"chromium";
const MODES=["legacy","react-p7","react-p8"];
const DIAGNOSTICS=process.env.KGG_SCAN_FALLBACK_DIAGNOSTICS==="1";
const diagnosticContexts=new WeakMap(),diagnosticPages=new WeakMap();
let diagnosticDir;
const assert=(ok,message)=>{if(!ok)throw new Error(message)};
const encode=value=>"KGGH2:"+Buffer.from(JSON.stringify(value),"utf8").toString("base64url");
const mime=file=>({
  ".html":"text/html; charset=utf-8",".js":"text/javascript; charset=utf-8",
  ".css":"text/css; charset=utf-8",".json":"application/json; charset=utf-8",
  ".png":"image/png",".webmanifest":"application/manifest+json; charset=utf-8"
})[path.extname(file).toLowerCase()]||"application/octet-stream";
function diagnosticLog(event,details={}){
  const row=JSON.stringify({event,engine:ENGINE,sourceSha:process.env.KGG_SCAN_FALLBACK_HEAD_SHA,
    hostTime:new Date().toISOString(),...details});
  console.log("KGG_SCAN_DIAGNOSTIC "+row);
  try{fs.appendFileSync(path.join(diagnosticDir,"events.jsonl"),row+"\n")}catch{}
}
function scannerDiagnosticState(){
  const fab=document.getElementById("kggActionFab"),box=document.getElementById("kggActionBubbles");
  const bubble=document.getElementById("kggBubbleScan"),source=document.getElementById("kggPlanScanBtn");
  const fallback=document.getElementById("kggLiveScanFallback");
  return {readyState:document.readyState,scannerMarker:window.__kggStartScanVersion||null,
    menuMarker:window.__kggPatientMultiPlanDbAddon||null,
    fab:{exists:!!fab,handler:typeof fab?.onclick,open:fab?.classList.contains("open")??null},
    bubble:{exists:!!bubble,handler:typeof bubble?.onclick,hidden:bubble?.hidden??null,
      boxHidden:box?.hidden??null,display:bubble?getComputedStyle(bubble).display:null},
    source:{exists:!!source,handler:typeof source?.onclick},
    scanner:{exists:!!document.getElementById("kggLiveScan"),fallbackHidden:fallback?.hidden??null,
      deniedCount:window.__kggCameraDeniedCount??null}};
}
function diagnosticBounded(promise,ms){
  let timer;
  return Promise.race([promise,new Promise((_,reject)=>{
    timer=setTimeout(()=>reject(new Error("diagnostic collection deadline")),ms);
  })]).finally(()=>clearTimeout(timer));
}
async function diagnosticSnapshot(page,phase){
  try{diagnosticLog(phase,{page:diagnosticPages.get(page),
    state:await diagnosticBounded(page.evaluate(scannerDiagnosticState),1000)})}
  catch{diagnosticLog("snapshot-unavailable",{page:diagnosticPages.get(page),phase})}
}
async function startDiagnostics(ctx,mode,hasPlan){
  const tag=mode+(hasPlan?"-plan":"-rescue"),meta={tag,started:false,stopped:false};
  diagnosticContexts.set(ctx,meta);
  ctx.on("page",page=>{
    diagnosticPages.set(page,tag);
    page.on("crash",()=>diagnosticLog("page-crash",{page:tag}));
    page.on("close",()=>diagnosticLog("page-close",{page:tag}));
    page.on("console",message=>{
      const prefix="KGG_SCAN_NATIVE ",text=message.text();
      if(text.startsWith(prefix)){
        try{diagnosticLog("native-capture",{page:tag,...JSON.parse(text.slice(prefix.length))})}catch{}
      }
    });
  });
  await ctx.addInitScript({content:`(()=>{
    const state=${scannerDiagnosticState.toString()};
    for(const type of ["pointerdown","pointerup","mousedown","mouseup","click"]){
      document.addEventListener(type,event=>{
        try{
          const target=event.target instanceof Element&&event.target.closest("#kggActionFab,#kggBubbleScan,#kggPlanScanBtn");
          if(target)console.debug("KGG_SCAN_NATIVE "+JSON.stringify({type,target:target.id,
            isTrusted:event.isTrusted,browserMs:performance.now(),state:state()}));
        }catch{}
      },true);
    }
  })();`});
  await ctx.tracing.start({screenshots:true,snapshots:true,sources:true});
  meta.started=true;
  diagnosticLog("context-start",{page:tag});
}
async function finishDiagnostics(ctx){
  const meta=diagnosticContexts.get(ctx);
  if(!meta?.started||meta.stopped)return;
  meta.stopped=true;
  try{await diagnosticBounded(ctx.tracing.stop({path:path.join(diagnosticDir,meta.tag+"-trace.zip")}),2000)}
  catch{diagnosticLog("trace-unavailable",{page:meta.tag})}
}
async function diagnosticFailure(ctx,page,error){
  diagnosticLog("failure",{page:diagnosticContexts.get(ctx)?.tag,error:String(error?.message||error)});
  await Promise.allSettled([
    page?diagnosticSnapshot(page,"failure-state"):Promise.resolve(),
    page?diagnosticBounded(page.screenshot({path:path.join(diagnosticDir,
      diagnosticContexts.get(ctx).tag+"-failure.png"),timeout:1000}),1000):Promise.resolve(),
    finishDiagnostics(ctx)
  ]);
}
function server(){
  return http.createServer((request,response)=>{
    try{
      const name=new URL(request.url,"http://localhost").pathname;
      const relative=decodeURIComponent(name==="/"?"/index.html":name);
      const file=path.resolve(ROOT,"."+relative);
      if(!file.startsWith(ROOT+path.sep)||!fs.existsSync(file)||!fs.statSync(file).isFile()){
        response.writeHead(404).end("not found");return;
      }
      response.writeHead(200,{"content-type":mime(file),"cache-control":"no-store"});
      fs.createReadStream(file).pipe(response);
    }catch{response.writeHead(400).end("bad request")}
  });
}
const flags=mode=>"kggReactPad="+(mode==="legacy"?"0":"1")+
  (mode==="react-p8"?"&kggReactGrid=1":"");
async function makePage(browser,base,mode,plan){
  const ctx=await browser.newContext({viewport:{width:390,height:844},
    isMobile:true,hasTouch:true,serviceWorkers:"block"});
  let page;
  try{
  if(DIAGNOSTICS)await startDiagnostics(ctx,mode,Boolean(plan));
  await ctx.addInitScript(()=>{
    localStorage.setItem("kggInstallAsked","1");
    window.__kggCameraDeniedCount=0;
    Object.defineProperty(navigator,"mediaDevices",{configurable:true,value:{
      getUserMedia:async()=>{window.__kggCameraDeniedCount++;
        throw new DOMException("synthetic permission denied","NotAllowedError")}
    }});
  });
  page=await ctx.newPage();const errors=[],dialogs=[],prompts=[];
  page.setDefaultTimeout(7000);
  page.on("pageerror",e=>errors.push(String(e)));
  page.on("dialog",async dialog=>{
    dialogs.push({type:dialog.type(),message:dialog.message()});
    if(dialog.type()==="prompt")await dialog.accept(prompts.shift()||"");
    else await dialog.accept();
  });
  const url=base+"/?"+flags(mode)+(plan?"&plan="+encodeURIComponent(encode(plan)):"");
  await page.goto(url,{waitUntil:"domcontentloaded"});
  await page.waitForFunction(()=>Boolean(window.__kggStartScanVersion));
  if(mode==="react-p8"){
    await page.waitForFunction(()=>document.body.classList.contains("kggReactNumpadGridV1")&&
      document.querySelectorAll(".kgg-react-numpad-grid__key").length===12);
  }else{
    assert(!await page.evaluate(()=>document.body.classList.contains("kggReactNumpadGridV1")),
      "non-P8 mode mounted P8 grid");
  }
  const reactFlag=await page.evaluate(()=>localStorage.getItem("kggPatientReactPadV1")==="1");
  assert(reactFlag===(mode!=="legacy"),"React opt-in flag inconsistent in "+mode);
  return {ctx,page,errors,dialogs,prompts};
  }catch(error){
    if(DIAGNOSTICS){await diagnosticFailure(ctx,page,error).catch(()=>{});await ctx.close().catch(()=>{})}
    throw error;
  }
}
async function capture(page){
  return page.evaluate(()=>({
    planId:p?.id??null,title:p?.title??null,count:p?.ex?.length??0,
    day:Number(d),done:[...done],
    values:Object.fromEntries(Object.entries(v||{}).sort(([a],[b])=>a.localeCompare(b))),
    storedCurrent:JSON.parse(localStorage.getItem("kggCurrentPlanV1")||"null")?.plan?.i||null
  }));
}
// Reuse the existing scanner smoke's visible-button / FAB action-bubble path.
async function openPatientScanner(page){
  const bubble=page.locator("#kggBubbleScan"),fab=page.locator("#kggActionFab");
  if(DIAGNOSTICS)await diagnosticSnapshot(page,"scanner-open-entry");
  if(await bubble.count()&&await bubble.isVisible().catch(()=>false)){
    await bubble.click();return;
  }
  if(await fab.count()&&await fab.isVisible().catch(()=>false)){
    if(DIAGNOSTICS)await diagnosticSnapshot(page,"before-fab-click");
    await fab.click();
    if(DIAGNOSTICS)await diagnosticSnapshot(page,"after-fab-click");
    await bubble.waitFor({state:"visible"});await bubble.click();return;
  }
  const direct=page.locator("#kggPlanScanBtn");
  await direct.waitFor({state:"visible"});
  await direct.click();
}
async function denied(page){
  const attempts=await page.evaluate(()=>window.__kggCameraDeniedCount);
  await openPatientScanner(page);
  await page.locator("#kggLiveScanFallback:not([hidden])").waitFor({state:"visible"});
  assert(await page.locator("#kggLiveScan").getAttribute("role")==="dialog",
    "fallback is not a scanner dialog");
  assert(await page.locator(".kggLivePhoto").isVisible()&&
    await page.locator(".kggLivePaste").isVisible()&&
    await page.locator(".kggLiveRetry").isVisible(),
    "one or more camera fallback actions missing");
  const state=await page.evaluate(()=>({
    attempts:window.__kggCameraDeniedCount,
    fallbackDisplay:getComputedStyle(document.querySelector("#kggLiveScanFallback")).display,
    status:document.querySelector("#kggLiveScanStatus")?.textContent||"",
    active:window.__kggPatientStartScanTest?.scannerActive()
  }));
  assert(state.attempts===attempts+1&&!state.active&&state.fallbackDisplay!=="none",
    "synthetic camera failure did not reach visible fallback: "+JSON.stringify(state));
  return state;
}
async function run(browser,base,mode){
  // Avoid catalog-recognized names: media/CDN fetching belongs to the separate media suite.
  // The scanner suite must remain strictly synthetic and independent of network assets.
  const plan={i:"synthetic-scan-fallback",t:"Baseline scan",v:1,d:6,
    e:[["KGG Synthetic Fixture Alpha",2,"B","kg","Wdh"]]};
  const next={i:"synthetic-scan-update",t:"Fallback Link Update",v:2,d:6,
    e:[["KGG Synthetic Fixture Alpha",2,"B","kg","Wdh"],
       ["KGG Synthetic Fixture Beta",1,"B","kg","Wdh"]]};
  const x=await makePage(browser,base,mode,plan);
  try{
    const {page}=x;
    await page.waitForFunction(()=>document.querySelectorAll("#list .ex").length===1&&
      Boolean(document.querySelector("#kggPlanScanBtn")));
    await page.evaluate(()=>{put(0,1,"B","a","22");put(0,1,"B","b","9")});
    const before=await capture(page);
    assert(before.values&&Object.keys(before.values).length===2,
      "synthetic training fixture was not established: "+JSON.stringify(before));

    const first=await denied(page);
    await page.locator(".kggLiveRetry").click();
    await page.locator("#kggLiveScanFallback:not([hidden])").waitFor({state:"visible"});
    assert(await page.evaluate(()=>window.__kggCameraDeniedCount)===first.attempts+1,
      "retry did not make a second native camera request");
    assert(JSON.stringify((await capture(page)).values)===JSON.stringify(before.values),
      "permission failure/retry mutated training");
    await page.locator(".kggLiveScanClose").click();
    await page.locator("#kggLiveScan").waitFor({state:"detached"});

    await denied(page);
    const [fileChooser]=await Promise.all([
      page.waitForEvent("filechooser",{timeout:6000}),
      page.locator(".kggLivePhoto").click()
    ]);
    assert(!fileChooser.isMultiple(),"photo fallback unexpected multiple-file chooser");
    await page.locator("#kggLiveScan").waitFor({state:"detached"});
    const input=page.locator("#kggPlanScanInput");
    assert(await input.getAttribute("accept")==="image/*"&&
      await input.getAttribute("capture")==="environment",
      "photo fallback lost capture/file path");
    assert(JSON.stringify((await capture(page)).values)===JSON.stringify(before.values),
      "photo chooser without file mutated training");

    await denied(page);
    x.prompts.push("KGGH3:AAAA");
    const alert=page.waitForEvent("dialog",{predicate:d=>d.type()==="alert",timeout:6000});
    await page.locator(".kggLivePaste").click();
    await alert;
    await page.locator("#kggLiveScan").waitFor({state:"detached"});
    assert(x.dialogs.some(d=>d.type==="prompt")&&x.dialogs.some(d=>d.type==="alert"),
      "invalid plan link did not trigger safe prompt+alert fallback");
    assert(JSON.stringify(await capture(page))===JSON.stringify(before),
      "invalid scanner plan changed state");

    await denied(page);
    x.prompts.push(encode(next));
    await page.locator(".kggLivePaste").click();
    await page.waitForFunction(()=>p?.title==="Fallback Link Update"&&p.ex.length===2);
    const after=await capture(page);
    assert(after.values&&JSON.stringify(after.values)===JSON.stringify(before.values)&&
      after.day===before.day&&JSON.stringify(after.done)===JSON.stringify(before.done),
      "valid link update changed training values/day");
    assert(after.count===2&&after.planId===before.planId,
      "valid scanner update failed to preserve current plan identity");
    await page.reload({waitUntil:"domcontentloaded"});
    await page.waitForFunction(()=>p?.ex?.length===2&&window.__kggStartScanVersion);
    const reloaded=await capture(page);
    assert(JSON.stringify(reloaded.values)===JSON.stringify(before.values)&&
      reloaded.title===after.title,"valid scanner update not persistent on reload");
    assert(x.errors.length===0,"scanner raised page errors: "+x.errors.join(" | "));

    const rescue=await makePage(browser,base,mode,null);
    try{
      await rescue.page.locator("#kggQrRescue .scanBig").waitFor({state:"visible"});
      await rescue.page.locator("#kggQrRescue .scanBig").click();
      await rescue.page.locator("#kggLiveScanFallback:not([hidden])")
        .waitFor({state:"visible"});
      await rescue.page.locator(".kggLiveScanClose").click();
      await rescue.page.locator("#kggLiveScan").waitFor({state:"detached"});
      assert(rescue.errors.length===0,"plan-rescue page errors: "+rescue.errors.join(" | "));
    }catch(error){if(DIAGNOSTICS)await diagnosticFailure(rescue.ctx,rescue.page,error).catch(()=>{});throw error}
    finally{if(DIAGNOSTICS)await finishDiagnostics(rescue.ctx);await rescue.ctx.close()}

    console.log("KGG_SCAN_FALLBACK_PARITY_PASS "+JSON.stringify({
      engine:ENGINE,mode,denied:true,retry:true,photoChooser:true,
      invalidCodeSafe:true,validLinkUpdate:true,reload:true,noPlanRescue:true,
      sourceSha:process.env.KGG_SCAN_FALLBACK_HEAD_SHA||"local"
    }));
  }catch(error){if(DIAGNOSTICS)await diagnosticFailure(x.ctx,x.page,error).catch(()=>{});throw error}
  finally{if(DIAGNOSTICS)await finishDiagnostics(x.ctx);await x.ctx.close()}
}
async function main(){
  assert(ENGINE==="chromium"||ENGINE==="webkit","unsupported browser "+ENGINE);
  if(DIAGNOSTICS){
    const attempt=process.env.KGG_SCAN_FALLBACK_DIAGNOSTIC_ATTEMPT;
    assert(/^[1-4]$/.test(attempt||"")&&process.env.RUNNER_TEMP,"diagnostics require runner temp and attempt1–4");
    assert(/^[0-9a-f]{40}$/.test(process.env.KGG_SCAN_FALLBACK_HEAD_SHA||""),"diagnostics require bound source SHA");
    diagnosticDir=path.join(process.env.RUNNER_TEMP,"kgg-integrated-"+ENGINE,"patient-ui-parity","attempt-"+attempt);
    fs.mkdirSync(diagnosticDir,{recursive:true});
    diagnosticLog("process-start",{attempt});
  }
  const app=server();await new Promise(ok=>app.listen(0,"127.0.0.1",ok));
  let browser;
  try{
    browser=await (ENGINE==="chromium"?chromium:webkit).launch({headless:true});
    if(DIAGNOSTICS)browser.on("disconnected",()=>diagnosticLog("browser-disconnected"));
    const base="http://127.0.0.1:"+app.address().port;
    for(const mode of MODES)await run(browser,base,mode);
    console.log("KGG scanner fallback parity: PASS "+ENGINE+" (3 modes)");
  }finally{if(browser)await browser.close();await new Promise(ok=>app.close(ok))}
}
const timer=setTimeout(()=>{console.error("Scanner fallback bounded 140s timeout");process.exit(124)},140000);
main().then(()=>clearTimeout(timer)).catch(err=>{
  clearTimeout(timer);console.error("KGG scanner fallback parity: FAIL "+(err.stack||err));process.exitCode=1;
});
