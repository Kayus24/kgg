# KGG Source Chunk 064

- Source: `kgg-update/index.html`
- Lines: 26881-26988

```html
        document.body.classList.add("kggPlanCardSwiping");
        live.classList.add("swipe-dragging");
        try{live.setPointerCapture&&live.setPointerCapture(pointerId);}catch(err){}
      }
      e.preventDefault();
      if(e.stopImmediatePropagation)e.stopImmediatePropagation();
      dx=Math.max(-live.offsetWidth*.86,Math.min(live.offsetWidth*.86,dx));
      var strength=Math.min(1,Math.abs(dx)/threshold());
      live.classList.toggle("swipe-left",dx<0);
      live.classList.toggle("swipe-right",dx>0);
      live.classList.toggle("swipe-armed",Math.abs(dx)>=threshold());
      live.style.setProperty("--swipe-strength",String(strength));
      live.style.setProperty("--kgg-plan-swipe-x",dx+"px");
      live.style.transform="translateX(var(--kgg-plan-swipe-x,0px))";
      live.style.opacity=String(1-strength*.16);
    }
    function up(e){
      var live=currentCard();
      cleanup();
      if(!active){resetTabletSwipe(live);return;}
      e.preventDefault();
      document.body.classList.remove("kggPlanCardSwiping");
      if(Math.abs(dx)>=threshold()){
        live.classList.add("swipe-removing");
        live.style.transition="transform .18s cubic-bezier(.2,.9,.2,1), opacity .18s ease";
        live.style.setProperty("--kgg-plan-swipe-x",((dx<0?-1:1)*(live.offsetWidth+96))+"px");
        live.style.opacity="0";
        setTimeout(function(){
          var del=live.querySelector(".planDeleteBtn,[data-del]");
          if(del&&typeof del.click==="function")del.click();
        },160);
        return;
      }
      live.style.transition="transform .22s cubic-bezier(.2,.9,.2,1), opacity .18s ease";
      live.style.setProperty("--kgg-plan-swipe-x","0px");
      live.style.opacity="1";
      setTimeout(function(){resetTabletSwipe(live);},230);
    }
    function cancel(){
      var live=currentCard();
      if(active){
        clearTimeout(cancelTimer);
        cancelTimer=setTimeout(function(){cleanup();resetTabletSwipe(currentCard());},900);
        return;
      }
      cleanup();
      resetTabletSwipe(live);
    }
    document.addEventListener("pointermove",move,true);
    document.addEventListener("pointerup",up,true);
    document.addEventListener("pointercancel",cancel,true);
  }
  function startTabletSwipe(ev){
    startTabletSwipeForCard(ev,ev.currentTarget);
  }
  function bindTabletSwipeGuard(){
    if(!document.body)return;
    if(document.documentElement&&!document.documentElement.dataset.kggV053TabletSwipeDocumentGuard){
      document.documentElement.dataset.kggV053TabletSwipeDocumentGuard="1";
      document.addEventListener("pointerdown",function(ev){
        if(!isTablet())return;
        var target=ev.target;
        var card=target&&target.closest&&target.closest("#planList .planCard[data-plan-id]");
        if(card)startTabletSwipeForCard(ev,card);
      },true);
    }
    document.querySelectorAll("#planList .planCard[data-plan-id]").forEach(function(card){
      if(card.dataset.kggV053TabletSwipeGuard==="1")return;
      card.dataset.kggV053TabletSwipeGuard="1";
      card.addEventListener("pointerdown",startTabletSwipe,true);
      card.onpointerdown=card.onpointerdown||startTabletSwipe;
    });
  }
  function install(){
    var menu=byId("kggPhoneAdminMenu");
    var header=document.querySelector("#createPanel.planMode .planHeader")||document.querySelector("#createPanel .planHeader");
    if(menu&&header&&!header.contains(menu))header.appendChild(menu);
    anchorTabletMenuButton();
    bindTabletSwipeGuard();
  }
  if(document.readyState==="loading")document.addEventListener("DOMContentLoaded",install,{once:true});
  else install();
  [80,240,700].forEach(function(ms){setTimeout(install,ms);});
  window.addEventListener("resize",function(){setTimeout(install,80);},{passive:true});
  window.addEventListener("orientationchange",function(){setTimeout(install,160);},{passive:true});
  if(document.body){
    new MutationObserver(function(){install();}).observe(document.body,{attributes:true,attributeFilter:["class"],childList:true,subtree:true});
  }
  window.KGG_UI_TABLET_STABILITY_V053={
    patchId:PATCH_ID,
    install:install,
    check:function(){
      var menu=byId("kggPhoneAdminMenu");
      var editor=document.querySelector("#editorModal .editorSheet");
      return {
        patchId:PATCH_ID,
        menuAnchored:!!(menu&&menu.closest("#createPanel .planHeader")),
        editorDisplay:editor?getComputedStyle(editor).display:"",
        editorColumns:editor?getComputedStyle(editor).gridTemplateColumns:""
      };
    }
  };
})();
</script>
<!-- KGG PATCH END kgg-v053-ui-tablet-stability -->

</body>
</html>
```
