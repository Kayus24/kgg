"use strict";
const fs=require("fs"),path=require("path"),crypto=require("crypto");
const {pathToFileURL}=require("url");
const {chromium}=require("playwright");
const ROOT=path.resolve(__dirname,".."),html=path.join(ROOT,"kgg-update/index.html");
const dir=path.join(process.env.KGG_SMOKE_SCREENSHOT_DIR||path.join(ROOT,"tmp/cockpit-device-canaries"),"device-canaries");fs.mkdirSync(dir,{recursive:true});
const results=[];
const assert=(ok,message)=>{if(!ok)throw new Error(message);};
(async()=>{
 const browser=await chromium.launch({headless:true});
 try{
  for(const viewport of [{width:390,height:857},{width:430,height:932},{width:759,height:1000},{width:760,height:1000},{width:820,height:1180},{width:1024,height:800},{width:1280,height:800},{width:1440,height:900}])for(const count of [1,2,3]){
   const {width}=viewport;
   const context=await browser.newContext({viewport,screen:viewport,isMobile:true,hasTouch:true,locale:"de-DE"});
   await context.route(/^https?:\/\//,route=>route.abort());
   const page=await context.newPage();page.setDefaultTimeout(4000);
   await page.addInitScript(()=>{
    const ex=(id,name)=>({id,localId:id,name,sets:2,side:"BI",loadUnit:"kg",weightUnit:"kg",metricUnit:"Wdh",unit:"Wdh",previous:[],today:[],progressionVariants:[],media:[]});
    localStorage.setItem("kgg_pwa_install_prompt_seen_v1","synthetic-canaries");
    localStorage.setItem("kgg_html_app_v2_state",JSON.stringify({planId:"normal-canary",patient:{name:"Synthetic normal plan",date:"2026-10-01",therapist:""},plan:[ex("normal-a","Abduktion Maschine"),ex("normal-b","Adduktion Maschine")]}));
   });
   const result={viewport,count,checks:[]};
   try{
    await page.goto(pathToFileURL(html).href,{waitUntil:"domcontentloaded"});
    await page.waitForFunction(()=>window.KGGTherapyCockpit&&document.querySelectorAll("#planList .planCard").length===2);
    // The local admin build intentionally asks for local configuration after boot.
    // Dismiss it through its real UI before entering the Cockpit; no keys are supplied.
    await page.locator("#adminSecretsModal.open").waitFor();
    await page.locator("#closeAdminSecrets").tap();
    await page.locator("#adminSecretsModal.open").waitFor({state:"hidden"});
    result.checks.push({name:"admin-startup-dismiss",status:"PASS"});
    // Synthetic fixture only: install the requested slot count before testing UI actions.
    await page.evaluate(count=>{
     const api=window.KGGTherapyCockpit,entries=api.registry.entries();
     for(let i=0;i<count;i++)api.importCode(api.encode({planId:"canary-slot-"+i,name:"Synthetic slot "+i,exercises:entries.slice(0,2).map(e=>({id:e.id,sets:2,previous:[["10","12"],["10","12"]],today:[["10","12"],["10","12"]]}))}));
    },count);
    await page.waitForFunction(()=>document.body.classList.contains("kggTherapyCockpitOpen"));
    await page.waitForFunction(()=>window.KGG_PATCHES?.['kgg-v102-phone-cockpit-dock-navigation']?.installed);
    assert(await page.evaluate(()=>innerWidth)===width,"device emulation changed the CSS viewport");
    const test=async(name,action)=>{
     try{await action();result.checks.push({name,status:"PASS"});}
     catch(e){result.checks.push({name,status:"FAIL",error:e.message});await page.screenshot({path:path.join(dir,`${width}-${count}-${name}.png`)});}
    };
    await test("keypad-field-switch",async()=>{
     await page.locator('.kgg-tc-card[data-tc-card="0"] .kgg-tc-card-toggle').first().tap();
     await page.locator('.kgg-tc-card[data-tc-card="0"] .kgg-tc-field[data-tc-field="load"]').first().tap();
     await page.locator('.kgg-tc-pad [data-tc-key="C"]').tap();
     await page.locator('.kgg-tc-pad [data-tc-key="7"]').tap();
     await page.locator('.kgg-tc-card[data-tc-card="0"] .kgg-tc-field[data-tc-field="metric"]').first().tap();
     await page.locator('.kgg-tc-pad [data-tc-key="C"]').tap();
     await page.locator('.kgg-tc-pad [data-tc-key="9"]').tap();
     await page.locator('.kgg-tc-header .kgg-tc-title').tap();
     const data=await page.evaluate(()=>({values:window.KGGTherapyCockpit.getSlot(0).exercises[0].today[0],pad:!!document.querySelector(".kgg-tc-pad")}));
     assert(JSON.stringify(data.values)==='["7","9"]'&&!data.pad,JSON.stringify(data));
    });
    if(width<760||count===3){
      await test("return-preserves-slots",async()=>{
        await page.locator("#kggTherapyCockpitButton").tap();
        await page.waitForFunction(()=>!document.body.classList.contains("kggTherapyCockpitOpen"));
        assert(await page.evaluate(()=>window.KGGTherapyCockpit.getState().slots.filter(Boolean).length)===count,"return changed slot count");
      });
    }
    await test("normal-plan-editor",async()=>{
     await page.locator("#planList [data-planedit]").first().tap();
     await page.locator("#editorModal.open").waitFor();
     const nameAction=await page.locator('#suggestExerciseNames').evaluate(button=>{const r=button.getBoundingClientRect(),sheet=document.querySelector('#editorModal .editorSheet').getBoundingClientRect();return{left:r.left,right:r.right,sheetLeft:sheet.left,sheetRight:sheet.right,viewport:innerWidth,scroll:button.scrollWidth,client:button.clientWidth};});
     assert(nameAction.left>=nameAction.sheetLeft&&nameAction.right<=Math.min(nameAction.sheetRight,nameAction.viewport)&&nameAction.scroll<=nameAction.client+1,'new name action is clipped: '+JSON.stringify(nameAction));

     await page.locator("#closeEditor").tap();
     await page.locator("#editorModal.open").waitFor({state:"hidden"});
    });
    await test("normal-finish-hit-test",async()=>{
     await page.locator("#finishBtn").tap();
     await page.locator("#shareModal.open").waitFor();
     await page.screenshot({path:path.join(dir,`${width}-${count}-finish-open.png`)});
     await page.locator("#finishCancelBtn").tap();
     await page.locator("#shareModal.open").waitFor({state:"hidden"});
    });
    await page.screenshot({path:path.join(dir,`${width}-${count}-layout.png`)});
    result.status=result.checks.every(c=>c.status==="PASS")?"PASS":"FAIL";
   }catch(e){result.status="FAIL";result.error=e.message;}
   finally{results.push(result);await context.close();console.log(JSON.stringify(result));}
  }
 }finally{await browser.close();}
 const report={sha256:crypto.createHash("sha256").update(fs.readFileSync(html)).digest("hex"),results};
 fs.writeFileSync(path.join(dir,"report.json"),JSON.stringify(report,null,2)+"\n");
 if(results.some(r=>r.status!=="PASS"))process.exitCode=1;
})().catch(e=>{console.error(e.stack);process.exitCode=1;});
