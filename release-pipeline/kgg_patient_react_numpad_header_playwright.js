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
          const module=await import("./patient-react-dist/kgg-patient-ui.js?v=p7-d14-react-header-1");
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
    console.log("Patient React NumPad header Playwright ("+engine+"): PASS");
    await ctx.close();
  }finally{
    await browser.close();
    await new Promise(resolve=>server.close(resolve));
  }
}

main().catch(error=>{console.error(error&&error.stack||error);process.exit(1)});
