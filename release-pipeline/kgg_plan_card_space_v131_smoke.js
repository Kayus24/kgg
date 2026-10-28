"use strict";
const {chromium}=require("playwright");
const fs=require("fs"),path=require("path"),{pathToFileURL}=require("url");
const root=path.resolve(__dirname,"..");
const dir=path.join(root,"tmp","v131-ui-geometry");
fs.mkdirSync(dir,{recursive:true});
const htmlUrl=pathToFileURL(path.join(root,"kgg-update/index.html")).href;
(async()=>{
 const browser=await chromium.launch();
 const results=[];
 try{
  for(const width of [390,430,760,1280]){
   const viewport={width,height:width<760?900:800};
   const ctx=await browser.newContext({viewport,screen:viewport,isMobile:true,hasTouch:true});
   await ctx.route(/^https?:\/\//,route=>route.abort());
   await ctx.addInitScript(()=>{
    localStorage.setItem("kgg_pwa_install_prompt_seen_v1","synthetic");
    localStorage.setItem("kgg_html_app_v2_state",JSON.stringify({planId:"v131-synthetic",
     patient:{name:"UI fixture",date:"2026-10-28"},plan:[{id:"v131-ex",localId:"v131-ex",
     name:"Adduction Machine",sets:3,side:"BI",loadUnit:"kg",metricUnit:"Wdh",
     media:[{type:"image",id:"v131-test-image"}],today:[],previous:[],progressionVariants:[]}]}));
   });
   const page=await ctx.newPage();
   await page.goto(htmlUrl,{waitUntil:"domcontentloaded",timeout:45000});
   await page.waitForSelector("#planList .planCard[data-plan-id]",{timeout:25000});
   if(await page.locator("#adminSecretsModal.open").count())await page.locator("#closeAdminSecrets").click();
   const proof=await page.evaluate(async()=>{
    const card=document.querySelector("#planList .planCard[data-plan-id]");
    const badge=card?.querySelector(".planBadge.media");
    const thumb=card?.querySelector(".planThumb");
    const edit=card?.querySelector("[data-planedit]");
    const del=card?.querySelector("[data-del]");
    const missing=(!card||!badge||!thumb||!edit||!del);
    if(missing)return {missing:true,card:!!card,badge:!!badge,thumb:!!thumb,edit:!!edit,del:!!del};
    const visible=node=>getComputedStyle(node).display!=="none";
    const badgeWithoutThumb=visible(badge);
    const image=document.createElement("img");
    image.src="data:image/gif;base64,R0lGODlhAQABAAD/ACwAAAAAAQABAAACADs=";
    thumb.appendChild(image);
    await image.decode().catch(()=>{});
    const badgeWithThumb=visible(badge);
    const statuses=card.querySelector(".planBadges");
    const status=document.createElement("span");status.className="planBadge live";status.textContent="Vorschau";
    statuses.appendChild(status);
    const otherBadgeVisible=visible(status);
    const rect=node=>node.getBoundingClientRect();
    const c=rect(card),e=rect(edit),d=rect(del);
    const hit=(node,r)=>{const item=document.elementFromPoint(r.x+r.width/2,r.y+r.height/2);return item===node||node.contains(item);};
    const separated=e.right<=d.left-3||d.right<=e.left-3||e.bottom<=d.top-3||d.bottom<=e.top-3;
    return {badgeWithoutThumb,badgeWithThumb,otherBadgeVisible,
      cardWidth:c.width,cardHeight:c.height,
      edit:{x:e.x,y:e.y,width:e.width,height:e.height,rightGap:c.right-e.right,hit:hit(edit,e)},
      del:{x:d.x,y:d.y,width:d.width,height:d.height,rightGap:c.right-d.right,topGap:d.top-c.top,hit:hit(del,d)},
      separated,deleteAlign:getComputedStyle(del).placeItems,
      scrollOverflow:card.scrollWidth>card.clientWidth+1};
   });
   const phone=width===390||width===430;
   const hitbox=()=>proof.edit?.width>=43.5&&proof.edit?.height>=43.5&&
     proof.del?.width>=43.5&&proof.del?.height>=43.5&&proof.separated&&proof.edit?.hit&&proof.del?.hit;
   const pass=!proof.missing&&proof.badgeWithoutThumb&&!proof.badgeWithThumb&&proof.otherBadgeVisible&&
     (!phone||(hitbox()&&Math.abs(proof.del.rightGap)<=2&&Math.abs(proof.del.topGap)<=2&&
       Math.abs(proof.edit.rightGap-48)<=2&&!proof.scrollOverflow));
   const result={width,status:pass?"PASS":"FAIL",...proof};results.push(result);
   console.log(JSON.stringify(result));
   await page.screenshot({path:path.join(dir,`plan-card-v131-${width}.png`)});
   await ctx.close();
  }
 }finally{await browser.close();}
 fs.writeFileSync(path.join(dir,"report.json"),JSON.stringify(results,null,2));
 if(results.some(x=>x.status!=="PASS"))process.exitCode=1;
})().catch(err=>{console.error(err.stack);process.exitCode=1;});
