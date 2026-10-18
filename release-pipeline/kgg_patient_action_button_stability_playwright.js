#!/usr/bin/env node
"use strict";
// Regression: a normal action-button press must survive its existing menu callback.
// Execute the real menu functions; unrelated plan/catalog setup is outside this fixture.
const fs=require("node:fs"),path=require("node:path"),crypto=require("node:crypto");
const assert=require("node:assert/strict");
const ROOT=path.resolve(__dirname,"..");

function menuSource(){
  const source=fs.readFileSync(path.join(ROOT,"patient-multiplan-db.js"),"utf8");
  const start=source.indexOf("  function closeBubbles(){");
  const end=source.indexOf("  function patchRender(){",start);
  assert(start>=0&&end>start,"real action-menu function boundaries missing");
  const functions=source.slice(start,end);
  for(const name of ["closeBubbles","toggleBubbles","clickSource","ensureActionBubbles"]){
    assert(functions.includes("function "+name+"("),"real menu function missing: "+name);
  }
  return {functions,sha256:crypto.createHash("sha256").update(source).digest("hex")};
}

async function verifyActionButtonStability(browser,engine){
  const source=menuSource();
  const context=await browser.newContext({viewport:{width:390,height:844},
    isMobile:true,hasTouch:true,serviceWorkers:"block"});
  const results=[];
  try{
    for(const rebuildDuringPress of [false,true]){
      const page=await context.newPage();
      page.setDefaultTimeout(7000);
      try{
        // Control covers a missing button; the callback case also checks wrong-icon repair.
        await page.setContent('<!doctype html><meta charset="utf-8">'+
          '<style>#kggActionFab{width:100px;height:60px;font-size:25px}</style>'+
          (rebuildDuringPress?'<button id="kggActionFab" type="button">wrong icon</button>':""));
        await page.addScriptTag({content:
          'const $=id=>document.getElementById(id),t=(de,en)=>de;\n'+
          'function ensureStyle(){} function ensureSourceButtons(){}\n'+
          'function ensureState(){} function ensureDbDom(){}\n'+source.functions+
          '\nwindow.__runActionMenuCallback=ensureActionBubbles;ensureActionBubbles();'});
        assert.equal(await page.locator("#kggActionFab").textContent(),"📷",
          "action button must initialize/repair its camera icon");
        const point=await page.evaluate(()=>{
          const fab=document.getElementById("kggActionFab");
          const box=document.getElementById("kggActionBubbles");
          window.__actionButtonProof={fab,child:fab.firstChild,events:[]};
          for(const type of ["mousedown","mouseup","click"]){
            document.addEventListener(type,event=>{
              if(event.target===fab)window.__actionButtonProof.events.push({
                type:event.type,trusted:event.isTrusted,target:event.target.id});
            },true);
          }
          if(!box.hidden)throw new Error("fixture menu must start closed");
          const range=document.createRange();range.selectNodeContents(fab);
          const rect=range.getBoundingClientRect();
          if(!rect.width||!rect.height)throw new Error("action-button text is not visible");
          return {x:rect.x+rect.width/2,y:rect.y+rect.height/2};
        });
        await page.mouse.move(point.x,point.y);
        let pressed=false;
        try{
          await page.mouse.down();pressed=true;
          // Deterministically interleave the actual callback registered by the app's
          // existing render/300ms/1000ms paths. No sleeps or programmatic click.
          if(rebuildDuringPress)await page.evaluate(()=>window.__runActionMenuCallback());
          await page.mouse.up();pressed=false;
        }finally{if(pressed)await page.mouse.up().catch(()=>{})}
        const state=await page.evaluate(()=>{
          const proof=window.__actionButtonProof;
          const fab=document.getElementById("kggActionFab");
          return {events:proof.events,buttonSame:fab===proof.fab,
            childSame:fab.firstChild===proof.child,
            icon:fab.textContent,menuHidden:document.getElementById("kggActionBubbles").hidden,
            buttonOpen:fab.classList.contains("open")};
        });
        const menuVisible=await page.locator("#kggBubbleScan").isVisible();
        const result={engine,rebuildDuringPress,sourceSha256:source.sha256,...state,menuVisible};
        results.push(result);
        console.log("KGG_ACTION_BUTTON_STABILITY_CASE "+JSON.stringify(result));
        assert.equal(state.events.filter(event=>event.type==="mousedown"&&event.trusted).length,1,
          "native action-button mousedown missing: "+JSON.stringify(result));
        assert.equal(state.events.filter(event=>event.type==="mouseup"&&event.trusted).length,1,
          "native action-button mouseup missing: "+JSON.stringify(result));
        assert.equal(state.events.filter(event=>event.type==="click"&&event.trusted).length,1,
          "action-menu callback swallowed native click: "+JSON.stringify(result));
        assert(menuVisible&&!state.menuHidden&&state.buttonOpen,
          "native action-button click did not open the visible menu: "+JSON.stringify(result));
      }finally{await page.close()}
    }
    console.log("KGG_ACTION_BUTTON_STABILITY_PASS "+JSON.stringify({engine,
      sourceSha256:source.sha256,control:true,rebuildDuringPress:true}));
    return results;
  }finally{await context.close()}
}

module.exports={verifyActionButtonStability};
if(require.main===module){
  async function main(){
    const args=process.argv.slice(2);
    assert(args.length===0||(args.length===2&&args[0]==="--engine"),
      "usage: node kgg_patient_action_button_stability_playwright.js [--engine chromium|webkit]");
    const engine=args[1]||"chromium";
    assert(["chromium","webkit"].includes(engine),"unsupported browser "+engine);
    const {chromium,webkit}=require("playwright");
    const browser=await (engine==="webkit"?webkit:chromium).launch({headless:true});
    try{await verifyActionButtonStability(browser,engine)}finally{await browser.close()}
  }
  main().catch(error=>{console.error("KGG action-button stability: FAIL "+(error.stack||error));
    process.exitCode=1});
}
