#!/usr/bin/env node
"use strict";

const fs=require("fs"),http=require("http"),path=require("path"),{chromium,webkit}=require("playwright");
const ROOT=path.resolve(process.argv[2]||path.resolve(__dirname,".."));

function assert(value,message){if(!value)throw new Error(message)}
function enc(plan){return Buffer.from(JSON.stringify(plan),"utf8").toString("base64url")}
function typeFor(file){
  if(file.endsWith(".html"))return"text/html; charset=utf-8";
  if(file.endsWith(".js"))return"text/javascript; charset=utf-8";
  if(file.endsWith(".css"))return"text/css; charset=utf-8";
  if(file.endsWith(".json"))return"application/json; charset=utf-8";
  if(file.endsWith(".png"))return"image/png";
  return"application/octet-stream";
}
function fileFor(url){
  const rel=decodeURIComponent(String(url||"/").split("?")[0]).replace(/^\/+/, "")||"index.html";
  const target=path.resolve(ROOT,rel);
  return target.startsWith(ROOT)&&fs.existsSync(target)&&fs.statSync(target).isFile()?target:null;
}
async function openCard(card){
  for(let i=0;i<5;i++){
    if(await card.evaluate(e=>e.classList.contains("kggOpen")))return;
    await card.locator("h3").evaluate(el=>el.click());
    await card.page().waitForTimeout(100);
  }
  throw new Error("card open state did not stabilize");
}
async function tapCompactValue(card,setIndex,key){
  const set=card.locator(":scope > .set").nth(setIndex);
  const proxy=set.locator(`.kggCompactTapProxy[data-kgg-key="${key}"]`).first();
  await proxy.waitFor({state:"visible"});
  await proxy.click();
}
async function assertTransferCaret(page,key,description){
  await page.waitForFunction((expected)=>{
    const legacy=document.getElementById("kggPadTransfer");
    const react=document.querySelector(".kgg-react-numpad-transfer");
    if(!legacy||!react||legacy.dataset.pointerKey!==expected)return false;
    const oldStyle=getComputedStyle(legacy,"::before");
    const newStyle=getComputedStyle(react,"::before");
    if(newStyle.content==="none"||newStyle.content==="normal")return false;
    if(parseFloat(newStyle.borderBottomWidth)<8)return false;
    if(getComputedStyle(react).overflowX==="hidden")return false;
    const oldX=legacy.getBoundingClientRect().left+parseFloat(oldStyle.left);
    const newX=react.getBoundingClientRect().left+parseFloat(newStyle.left);
    return Number.isFinite(oldX)&&Number.isFinite(newX)&&Math.abs(oldX-newX)<=3;
  },key,{timeout:1200,polling:"raf"}).catch(error=>{
    throw new Error(description+": React transfer caret does not match the legacy pointer for "+key+" ("+error.message+")");
  });
}

async function seed(page){
  await page.evaluate(()=>{
    const putDay=(ei,s,side,key,value,day=1)=>{v[k(ei,s,side,key,day)]=String(value)};
    putDay(0,1,"B","a",15);
    putDay(0,1,"B","b",12);
    d=2;
    done=[1];
    save();
    render();
  });
  await page.waitForTimeout(500);
}

async function verifyGridPilot(browser,port) {
  const ctx=await browser.newContext({
    viewport:{width:390,height:844},hasTouch:true,isMobile:true,serviceWorkers:"block"
  });
  const page=await ctx.newPage(),errors=[];
  page.on("pageerror",error=>errors.push(String(error)));
  const plan={i:"react-grid-smoke",t:"Synthetic P8 Grid",v:1,d:6,
    e:[["Two pairs",2,"B","kg","Wdh"]]};
  const root="http://127.0.0.1:"+port+"/";
  const enabledUrl=root+"?kggReactPad=1&kggReactGrid=1&plan="+
    encodeURIComponent("KGGH2:"+enc(plan));
  const key=index=>page.locator('[data-kgg-react-numpad-grid="v1"] > button')
    .nth(index);
  const snapshot=()=>page.evaluate(()=>({
    open:!!window.__kggNumpadEditingApi?.getSnapshot?.().padOpen,
    dirty:!!window.__kggNumpadEditingApi?.getSnapshot?.().dirty,
    value:String(window.__kggNumpadEditingApi?.getSnapshot?.().padValue??""),
    field:window.__kggNumpadEditingApi?.getSnapshot?.().meta?.key??null
  }));
  try {
    await page.addInitScript(()=>{
      if(!sessionStorage.kggP8TestBoot){
        localStorage.clear();
        localStorage.kggInstallAsked="1";
        sessionStorage.kggP8TestBoot="1";
      }
    });
    await page.goto(enabledUrl,{waitUntil:"domcontentloaded",timeout:15000});
    try {
      await page.waitForFunction(()=>document.body.classList.contains("kggReactNumpadGridV1"),
        null,{timeout:6000});
    } catch (error) {
      const diag=await page.evaluate(()=>({
        request:window.__kggReactPadRequest,
        gridFlag:new URLSearchParams(location.search).get("kggReactGrid"),
        header:document.body.classList.contains("kggReactNumpadHeaderV1"),
        grid:document.body.classList.contains("kggReactNumpadGridV1"),
        root:!!document.getElementById("kggReactNumpadGridRoot"),
        nativeKeys:document.querySelectorAll("#pad .padGrid > button").length,
        modules:performance.getEntriesByType("resource").filter(x=>x.name.includes("patient-react-dist")).map(x=>x.name),
        url:location.href.split("&plan=")[0]
      }));
      throw new Error("P8 mounting diagnostics "+JSON.stringify({diag,errors})+"; "+error.message);
    }
    const card=page.locator("#list .ex").first();
    await openCard(card);
    const inputs=card.locator(":scope > .set").first().locator("input.num");
    const kg=inputs.nth(0),wdh=inputs.nth(1);
    await tapCompactValue(card,0,"a");
    await page.locator('[data-kgg-react-numpad-header="v1"]')
      .waitFor({state:"attached",timeout:8000});
    await page.locator('[data-kgg-react-numpad-grid="v1"]')
      .waitFor({state:"visible",timeout:8000});
    const layout=await page.evaluate(()=>{
      const originals=[...document.querySelectorAll("#pad .padGrid > button")],
        react=[...document.querySelectorAll('[data-kgg-react-numpad-grid="v1"] > button')],
        geom=el=>{const b=el.getBoundingClientRect();return{x:b.x,y:b.y,w:b.width,h:b.height}};
      return {
        originalCount:originals.length,reactCount:react.length,
        labelsMatch:originals.every((el,i)=>el.textContent?.trim()===react[i]?.textContent?.trim()),
        originalHidden:originals.every(el=>getComputedStyle(el).visibility==="hidden"&&
          el.getAttribute("aria-hidden")==="true"),
        keys:react.map(geom),legacyKeys:originals.map(geom),
        allVisible:react.every(el=>getComputedStyle(el).visibility!=="hidden")
      };
    });
    assert(layout.originalCount===12&&layout.reactCount===12&&layout.labelsMatch&&
      layout.originalHidden&&layout.allVisible,"P8 key contract wrong: "+JSON.stringify(layout));
    assert(layout.keys.every((b,i)=>{
      const a=layout.legacyKeys[i];
      return Math.abs(a.x-b.x)<=3&&Math.abs(a.y-b.y)<=3&&
        Math.abs(a.w-b.w)<=3&&Math.abs(a.h-b.h)<=3;
    }),"P8 changed legacy Grid key geometry: "+JSON.stringify(layout));
    assert((await snapshot()).dirty===false,"untouched P8 buffer incorrectly dirty");
    await page.locator("#pad .padOk").click();
    assert((await kg.inputValue())==="","P8 untouched OK saved a phantom zero");

    await tapCompactValue(card,0,"a");
    await key(10).click();
    const explicitZero=await snapshot();
    assert(explicitZero.dirty&&explicitZero.value==="0",
      "P8 explicit zero did not use the legacy dirty buffer: "+JSON.stringify(explicitZero));
    await page.locator("#pad .padOk").click();
    assert((await kg.inputValue())==="0","P8 explicit zero not committed by legacy OK");

    await tapCompactValue(card,0,"b");
    await key(0).click();
    await key(9).click();
    await key(1).click();
    await key(9).click();
    let typed=await snapshot();
    assert(typed.value==="1,2","P8 accepted duplicate comma: "+JSON.stringify(typed));
    await key(11).click();
    typed=await snapshot();
    assert(typed.value==="1,","P8 Backspace diverged from legacy: "+JSON.stringify(typed));
    await key(11).click();
    await key(11).click();
    typed=await snapshot();
    assert(typed.value==="0"&&typed.dirty,"P8 Backspace lost legacy zero display");
    await page.locator("#pad .padCancel").click();
    assert((await wdh.inputValue())==="","P8 cancel incorrectly committed a buffer");

    await tapCompactValue(card,0,"b");
    await key(1).click();await key(4).click();
    const beforeSwitch=await page.evaluate(()=>({y:scrollY,main:document.querySelector("main")?.scrollTop||0}));
    await tapCompactValue(card,0,"a");
    const afterSwitch=await page.evaluate(()=>({y:scrollY,main:document.querySelector("main")?.scrollTop||0}));
    assert(Math.abs(beforeSwitch.y-afterSwitch.y)<=1&&
      Math.abs(beforeSwitch.main-afterSwitch.main)<=1,
      "P8 pair switch moved page scroll");
    assert((await snapshot()).open,"P8 kg/Wdh switch closed NumPad");
    assert((await wdh.inputValue())==="25","P8 legacy commit-on-leave was lost");
    await key(0).click();await key(4).click();
    await page.locator("#pad .padOk").click();
    assert((await kg.inputValue())==="15"&&(await wdh.inputValue())==="25",
      "P8 final two-field values diverged from legacy");

    // The existing legacy action limits the editable buffer to eight digits.
    await tapCompactValue(card,0,"a");
    await key(11).click();await key(11).click();
    for(let i=0;i<9;i++)await key(8).click();
    const lengthLimit=await snapshot();
    assert(lengthLimit.value==="99999999"&&lengthLimit.dirty,
      "P8 changed legacy digit-buffer limit: "+JSON.stringify(lengthLimit));
    await page.locator("#pad .padCancel").click();
    assert((await kg.inputValue())==="15",
      "P8 buffer-limit cancellation modified committed legacy values");

    await page.goto(root+"?kggReactPad=1&kggReactGrid=0",{waitUntil:"domcontentloaded"});
    await page.waitForFunction(()=>document.body.classList.contains("kggReactNumpadHeaderV1"),
      null,{timeout:10000});
    assert(await page.locator("#kggReactNumpadGridRoot").count()===0,
      "P8 only-rollback retained grid root");
    assert(await page.locator("#pad .padGrid > button").count()===12,
      "P8 only-rollback lost legacy buttons");
    await page.goto(root+"?kggReactPad=0&kggReactGrid=1",{waitUntil:"domcontentloaded"});
    await page.waitForFunction(()=>document.body.classList.contains("kggAlwaysCollapsed"),
      null,{timeout:10000});
    assert(!(await page.evaluate(()=>document.body.classList.contains("kggReactNumpadGridV1"))),
      "P8 persisted after P7 feature flag rollback");
    assert(await page.locator("#kggReactNumpadGridRoot").count()===0,
      "React Grid root persisted after legacy rollback");
    assert(errors.length===0,"P8 browser page errors: "+JSON.stringify(errors));
    return {status:"PASS",reactKeys:12,legacyKeys:12,zero:true,comma:true,
      backspace:true,cancel:true,stayOpen:true,rollback:true};
  }finally{await ctx.close()}
}

async function main(){
  const server=http.createServer((req,res)=>{
    const file=fileFor(req.url);
    if(!file){res.statusCode=404;return res.end("404")}
    res.setHeader("Content-Type",typeFor(file));
    res.setHeader("Cache-Control","no-store");
    res.end(fs.readFileSync(file));
  });
  await new Promise(resolve=>server.listen(0,"127.0.0.1",resolve));
  const port=server.address().port;
  const engine=process.env.KGG_REACT_HEADER_BROWSER||"chromium";
  assert(engine==="chromium"||engine==="webkit","invalid test browser "+engine);
  const browser=await (engine==="webkit"?webkit:chromium).launch({headless:true});

  try{
    const ctx=await browser.newContext({viewport:{width:390,height:844},hasTouch:true,isMobile:true});
    const page=await ctx.newPage();
    const errors=[];
    let reactRequests=0;

    page.on("pageerror",error=>errors.push(String(error)));
    page.on("request",request=>{
      if(request.url().includes("/patient-react-dist/"))reactRequests+=1;
    });

    const plan={
      i:"react-header-smoke",
      t:"React Header Smoke",
      v:1,
      d:6,
      e:[["Pair",2,"B","kg","Wdh"]]
    };

    await page.addInitScript(()=>{
      if(!sessionStorage.kggReactHeaderTestBoot){
        localStorage.clear();
        localStorage.kggInstallAsked="1";
        sessionStorage.kggReactHeaderTestBoot="1";
      }
    });
    const enabledUrl="http://127.0.0.1:"+port+"/?kggReactPad=1&plan="+encodeURIComponent("KGGH2:"+enc(plan));
    await page.goto(enabledUrl,{waitUntil:"networkidle"});
    await page.waitForFunction(()=>document.body.classList.contains("kggAlwaysCollapsed"));
    await page.waitForTimeout(1200);
    const boot=await page.evaluate(()=>({
      requested:window.__kggReactPadRequest,
      stored:localStorage.getItem("kggPatientReactPadV1"),
      bodyMode:document.body.classList.contains("kggReactNumpadHeaderV1"),
      root:!!document.getElementById("kggReactNumpadHeaderRoot"),
      assets:performance.getEntriesByType("resource").map(entry=>entry.name).filter(name=>name.includes("patient-react-dist"))
    }));
    let manualImport=null;
    if(!boot.bodyMode||!boot.root){
      manualImport=await page.evaluate(async()=>{
        try{
          const module=await import("./patient-react-dist/kgg-patient-ui.js?v=p8-d14-react-grid-1");
          return{keys:Object.keys(module),mountType:typeof module.mountLegacyNumpadHeaderIsland,mountResult:!!module.mountLegacyNumpadHeaderIsland?.()};
        }catch(error){
          return{error:String(error),stack:error&&error.stack||""};
        }
      });
    }
    assert(boot.bodyMode&&boot.root,"React header bootstrap failed: "+JSON.stringify({boot,reactRequests,errors,manualImport}));
    assert(reactRequests>=2,"React JS/CSS assets were not requested when feature flag was enabled");

    await seed(page);
    const card=page.locator("#list .ex").first();
    await openCard(card);
    const inputs=card.locator(":scope > .set").first().locator("input.num");
    const kg=inputs.nth(0),wdh=inputs.nth(1);

    await tapCompactValue(card,0,"a");
    await page.waitForFunction(()=>!!document.querySelector("[data-kgg-react-numpad-header='v1']"));
    await page.waitForTimeout(850);

    const legacyGeometry=await page.evaluate(()=>{
      const pair=document.getElementById("kggPadPair");
      const transfer=document.getElementById("kggPadTransfer");
      if(!pair||!transfer)return null;
      const pr=pair.getBoundingClientRect(),tr=transfer.getBoundingClientRect();
      return{
        pairVisibility:getComputedStyle(pair).visibility,
        transferVisibility:getComputedStyle(transfer).visibility,
        pairWidth:pr.width,
        pairHeight:pr.height,
        transferWidth:tr.width,
        transferHeight:tr.height
      };
    });
    assert(legacyGeometry&&legacyGeometry.pairVisibility==="hidden"&&legacyGeometry.transferVisibility==="hidden","legacy header was not visually hidden under React island: "+JSON.stringify(legacyGeometry));
    assert(legacyGeometry.pairWidth>100&&legacyGeometry.pairHeight>40&&legacyGeometry.transferWidth>100&&legacyGeometry.transferHeight>40,"legacy geometry collapsed under React overlay: "+JSON.stringify(legacyGeometry));

    const reactPair=page.locator(".kgg-react-numpad-pair__button");
    assert(await reactPair.count()===2,"React pair does not expose two controls");
    assert(JSON.stringify((await page.locator(".kgg-react-numpad-pair__value").allTextContents()).map(x=>x.trim()))===JSON.stringify(["–","–"]),"React pair initial values are wrong");

    let transferLabels=(await page.locator(".kgg-react-numpad-transfer__button").allTextContents()).map(x=>x.trim());
    assert(JSON.stringify(transferLabels)===JSON.stringify(["15 kg","Übernehmen","12 Wdh"]),"React transfer strip does not mirror legacy state: "+JSON.stringify(transferLabels));
    await assertTransferCaret(page,"a","three segment kg active");

    const scrollBefore=await page.evaluate(()=>({windowY:window.scrollY,mainTop:document.querySelector("main")?.scrollTop||0}));
    await page.locator('.kgg-react-numpad-pair__button[data-kgg-key="b"]').click();
    await page.waitForFunction(()=>window.__kggNumpadEditingApi?.getSnapshot?.().meta?.key==="b");
    await page.waitForTimeout(80);
    const scrollAfter=await page.evaluate(()=>({windowY:window.scrollY,mainTop:document.querySelector("main")?.scrollTop||0}));
    assert(Math.abs(scrollAfter.windowY-scrollBefore.windowY)<=1&&Math.abs(scrollAfter.mainTop-scrollBefore.mainTop)<=1,"React same-row pair switch moved page scroll: "+JSON.stringify({scrollBefore,scrollAfter}));
    assert(!(await page.locator("#pad").evaluate(el=>el.classList.contains("hide"))),"React pair switch closed the legacy NumPad");
    await assertTransferCaret(page,"b","three segment Wdh active");

    await page.locator('.kgg-react-numpad-transfer__button[data-kgg-transfer-key="b"]').click();
    await page.waitForTimeout(80);
    assert((await wdh.inputValue())==="12","React Wdh transfer did not delegate legacy commit");
    assert(!(await page.locator("#pad").evaluate(el=>el.classList.contains("hide"))),"React transfer closed before pair was complete");
    transferLabels=(await page.locator(".kgg-react-numpad-transfer__button").allTextContents()).map(x=>x.trim());
    assert(JSON.stringify(transferLabels)===JSON.stringify(["15 kg"]),"React transfer did not collapse to remaining kg: "+JSON.stringify(transferLabels));
    await assertTransferCaret(page,"a","single remaining kg transfer");

    await page.locator('.kgg-react-numpad-transfer__button[data-kgg-transfer-key="a"]').click();
    await page.waitForTimeout(100);
    assert((await kg.inputValue())==="15","React kg transfer did not delegate legacy commit");
    assert(await page.locator("#pad").evaluate(el=>el.classList.contains("hide")),"React pair completion did not close legacy NumPad");

    reactRequests=0;
    await page.goto("http://127.0.0.1:"+port+"/?kggReactPad=0",{waitUntil:"networkidle"});
    await page.waitForFunction(()=>document.body.classList.contains("kggAlwaysCollapsed"));
    assert(reactRequests===0,"React assets loaded after explicit rollback flag");
    assert(!(await page.evaluate(()=>document.body.classList.contains("kggReactNumpadHeaderV1"))),"React body mode survived rollback reload");
    assert(await page.locator("#kggReactNumpadHeaderRoot").count()===0,"React root survived rollback reload");

    const legacyCard=page.locator("#list .ex").first();
    await openCard(legacyCard);
    await tapCompactValue(legacyCard,0,"a");
    await page.waitForTimeout(80);
    const legacyVisible=await page.locator("#kggPadPair").evaluate(el=>getComputedStyle(el).visibility!=="hidden"&&el.getBoundingClientRect().height>40);
    assert(legacyVisible,"legacy pair was not restored after kggReactPad=0");

    assert(errors.length===0,"page errors: "+JSON.stringify(errors));
    await ctx.close();
    const grid=await verifyGridPilot(browser,port);
    console.log("Patient React NumPad header + P8 Grid ("+engine+"): PASS "+JSON.stringify(grid));
  }finally{
    await browser.close();
    await new Promise(resolve=>server.close(resolve));
  }
}

main().catch(error=>{console.error(error&&error.stack||error);process.exit(1)});
