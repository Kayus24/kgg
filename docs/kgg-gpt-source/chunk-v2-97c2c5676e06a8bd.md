<!-- KGG PATCH START kgg-v099-shared-card-swipe-undo -->
<!-- KGG-Karten: gemeinsame Swipe- und Undo-Rückmeldung -->
<style id="kgg-v099-shared-card-swipe-undo-style">
  #kggSharedUndoToast{position:fixed;z-index:2147482200;left:50%;bottom:calc(16px + env(safe-area-inset-bottom));display:flex;align-items:center;gap:12px;width:max-content;max-width:min(92vw,480px);min-height:56px;box-sizing:border-box;padding:6px 8px 6px 16px;border:1px solid #cbd5e1;border-radius:16px;background:#1f2937;color:#fff;box-shadow:0 12px 34px rgba(15,23,42,.28);font:600 14px/1.35 -apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;opacity:0;visibility:hidden;transform:translate(-50%,12px);transition:opacity .16s ease,transform .16s ease,visibility .16s;}
  #kggSharedUndoToast.is-visible{opacity:1;visibility:visible;transform:translate(-50%,0);}
  #kggSharedUndoToast .kgg-shared-undo-message{min-width:0;overflow-wrap:anywhere;}
  #kggSharedUndoToast button{flex:0 0 auto;min-width:72px;min-height:44px;padding:8px 12px;border:1px solid rgba(255,255,255,.42);border-radius:11px;background:#fff;color:#1d4ed8;font:800 13px/1 -apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;cursor:pointer;}
  #kggSharedUndoToast button:focus-visible{outline:3px solid #93c5fd;outline-offset:2px;}
  #planList .planCardActions>[data-planedit],#planList .planCardActions>[data-del]{box-sizing:border-box!important;flex:0 0 44px!important;width:44px!important;height:44px!important;min-width:44px!important;min-height:44px!important;padding:0!important;display:grid!important;place-items:center!important;}
  #kggTherapyCockpitRoot .kgg-tce-tool,#kggTherapyCockpitRoot .kgg-tce-drag{min-height:44px!important;}
  #kggTherapyCockpitRoot .kgg-tc-pad-mode{min-height:44px!important;}
  #kggTherapyCockpitRoot .kgg-tc-icon-btn{min-width:44px!important;min-height:44px!important;}
  @media(prefers-reduced-motion:reduce){#kggSharedUndoToast{transition:none;transform:translate(-50%,0)}}
  .kgg-v099-swiping{will-change:transform,opacity;touch-action:pan-y;}
  .kgg-v099-swiping.is-armed{background-color:#fef2f2!important;}
</style>
<script id="kgg-v099-shared-card-swipe-undo">
(function(){
  "use strict";
  var PATCH_ID="kgg-v099-shared-card-swipe-undo",timer=0,serial=0,current=null;
  function ensureToast(){
    var toast=document.getElementById("kggSharedUndoToast");if(toast)return toast;
    toast=document.createElement("div");toast.id="kggSharedUndoToast";toast.setAttribute("role","status");toast.setAttribute("aria-live","polite");toast.setAttribute("aria-atomic","true");
    toast.innerHTML='<span class="kgg-shared-undo-message"></span><button type="button" aria-label="Letzte Löschung rückgängig machen">Rückgängig</button>';document.body.appendChild(toast);return toast;
  }
  function hide(id){if(id!=null&&current&&current.id!==id)return;clearTimeout(timer);timer=0;var toast=document.getElementById("kggSharedUndoToast");if(toast)toast.classList.remove("is-visible");current=null;}
  function show(message,onUndo,duration,owner){
    var toast=ensureToast(),parent=owner&&owner.closest&&owner.closest(".modal.open")||document.body;
    if(toast.parentElement!==parent)parent.appendChild(toast);toast.inert=false;
    var id=++serial;clearTimeout(timer);current={id:id,undo:typeof onUndo==="function"?onUndo:null};
    toast.querySelector(".kgg-shared-undo-message").textContent=String(message||"Änderung übernommen");toast.classList.add("is-visible");
    var button=toast.querySelector("button");button.onclick=function(){if(!current||current.id!==id)return;var undo=current.undo;hide(id);if(undo)undo();};
    timer=setTimeout(function(){hide(id);},Math.max(1000,Math.min(8000,Number(duration)||5000)));return id;
  }
  window.KGGSharedUndo={show:show,hide:hide,durationMs:5000};
  window.KGG_PATCHES=window.KGG_PATCHES||{};
  window.KGG_PATCHES[PATCH_ID]={installed:true,version:1,undoDurationMs:5000,contract:{actionAxis:"horizontal",negativeDirection:"delete",positiveDirection:"delete",axisLockPx:10,actionThresholdRatio:0.28,undoDurationMs:5000}};
})();
</script>
<!-- KGG PATCH END kgg-v099-shared-card-swipe-undo -->
