#!/usr/bin/env node
"use strict";
// Synthetic preview bridge only: verifies real modular HTML menu and status contract.
const assert=require("node:assert/strict");
const path=require("node:path");
const {pathToFileURL}=require("node:url");
const {chromium}=require("playwright");
const url=pathToFileURL(path.resolve(__dirname,"../kgg-update/index.html")).href;
async function run(){
  const browser=await chromium.launch({headless:true});
  const context=await browser.newContext({viewport:{width:420,height:860},serviceWorkers:"block"});
  await context.addInitScript(()=>{
    window.__requested=0;
    window.KGGAndroidApp={
      updateStatus:()=>JSON.stringify({previewChannel:true,profile:"preview",
        versionName:"0.2.14-v404-dual-device-qr-test",releaseId:"pr373-844bafdf53bf-ci43419588710",
        rolloutCode:1794570355,loadedHtmlSource:"kgg_preview_web.html",
        pendingHealthCheck:false})
    };
    window.KGGPreviewWebUpdateNative={requestPreviewWebUpdate:()=>{window.__requested++;return true;}};
  });
  const page=await context.newPage();
  page.setDefaultTimeout(11000);
  const errors=[];page.on("pageerror",e=>errors.push(e.message));
  try{
    await page.goto(url,{waitUntil:"domcontentloaded",timeout:25000});
    await page.waitForFunction(()=>!!window.KGG_UPDATE_ZENTRALE_RESTORE&&!!window.KGGPreviewStatus,null,{timeout:15000});
    const initial=await page.evaluate(()=>window.KGGPreviewStatus.read());
    assert.equal(initial.native.previewChannel,true);
    assert.equal(initial.web.versionCode,141);
    assert.match(initial.web.versionName,/141/);
    await page.evaluate(()=>window.KGG_UPDATE_ZENTRALE_RESTORE.open());
    await page.locator("#kggPreviewVersionDialog").waitFor({state:"visible"});
    const text=await page.locator("#kggPreviewVersionDialog").innerText();
    assert.match(text,/HTML-Version/);
    assert.match(text,/v141/);
    assert.match(text,/0\.2\.14-v404/);
    assert.match(text,/pr373-844bafdf53bf/);
    assert.doesNotMatch(text,/Update-Zentrale ist im Code vorhanden/);
    await page.locator("#kggPreviewStatusCheck").click();
    assert.equal(await page.evaluate(()=>window.__requested),1);
    const after=await page.locator("#kggPreviewStatusFeedback").innerText();
    assert.match(after,/angefordert|gestartet|angefragt/i);
    assert.doesNotMatch(after,/erfolgreich aktualisiert/i);
    await page.locator("#kggPreviewStatusClose").click();
    assert.equal(await page.locator("#kggPreviewVersionDialog").isVisible(),false);
    assert.deepEqual(errors,[],errors.join("; "));
    const adminContext=await browser.newContext({viewport:{width:420,height:860},serviceWorkers:"block"});
    try{
      const adminPage=await adminContext.newPage();
      await adminPage.goto(url,{waitUntil:"domcontentloaded",timeout:25000});
      await adminPage.waitForFunction(()=>!!window.KGG_UPDATE_ZENTRALE_RESTORE);
      const adminResult=await adminPage.evaluate(()=>{
        window.__adminOpenCount=0;
        window.KGGReleaseCenter={open:()=>{window.__adminOpenCount++;}};
        window.KGG_UPDATE_ZENTRALE_RESTORE.open();
        return {count:window.__adminOpenCount,isPreview:window.KGGPreviewStatus.isPreview()};
      });
      assert.equal(adminResult.count,1,"normal Admin release center must still open");
      assert.equal(adminResult.isPreview,false,"browser without native bridge must not look like preview");
    }finally{await adminContext.close();}
    console.log("PREVIEW_VERSION_STATUS_BROWSER_PASS=true");
  }finally{await context.close();await browser.close();}
}
run().catch(e=>{console.error(e.stack||e);process.exitCode=1;});
