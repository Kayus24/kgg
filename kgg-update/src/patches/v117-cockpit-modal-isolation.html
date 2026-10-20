<!-- KGG PATCH START kgg-v117-cockpit-modal-isolation -->
<style id="kgg-v117-cockpit-modal-isolation-style">
body.kggCockpitModalOpen #kggTherapyCockpitButton,body.kggCockpitModalOpen #kgg-device-test-station{visibility:hidden!important;pointer-events:none!important;}
body.kggCockpitOwnModal #kggTherapyCockpitRoot{z-index:2147482500!important;}
</style>
<script id="kgg-v117-cockpit-modal-isolation">
(function(){
  "use strict";
  const PATCH_ID="kgg-v117-cockpit-modal-isolation";
  let current=null,returnTo=null;const saved=new Map();
  const visible=e=>!e.hidden&&e.getClientRects().length&&getComputedStyle(e).visibility!=='hidden';
  function restore(){saved.forEach((value,node)=>node.inert=value);saved.clear();}
  function sync(){
    const root=document.getElementById('kggTherapyCockpitRoot');if(!root)return;
    const nodes=Array.from(document.querySelectorAll('.modal.open,.kgg-tce-modal:not([hidden]),.kgg-tc-modal:not([hidden])')).filter(visible);
    const next=nodes[nodes.length-1]||null;if(next===current)return;
    restore();const old=current;current=next;
    document.body.classList.toggle('kggCockpitModalOpen',!!next);
    document.body.classList.toggle('kggCockpitOwnModal',!!next&&root.contains(next));
    if(next){
      if(!old)returnTo=document.activeElement;
      let branch=next;
      while(branch&&branch!==document.body){const parent=branch.parentElement;if(!parent)break;Array.from(parent.children).forEach(node=>{if(node!==branch&&!['SCRIPT','STYLE','LINK'].includes(node.tagName)){saved.set(node,node.inert);node.inert=true;}});branch=parent;}
      if(!next.contains(document.activeElement)){const focus=next.querySelector('input,button,select,textarea,[tabindex]');if(focus)focus.focus();}
    }else if(returnTo&&returnTo.isConnected&&!returnTo.closest('[inert]')){returnTo.focus();returnTo=null;}
  }
  function boot(){new MutationObserver(sync).observe(document.body,{subtree:true,childList:true,attributes:true,attributeFilter:['hidden','class']});sync();}
  document.addEventListener('keydown',function(event){if(event.key!=='Tab'||!current)return;const items=Array.from(current.querySelectorAll('button,input,select,textarea,a[href],[tabindex]')).filter(e=>!e.disabled&&e.tabIndex>=0&&visible(e));if(!items.length)return;const first=items[0],last=items[items.length-1];if(event.shiftKey&&(document.activeElement===first||!current.contains(document.activeElement))){event.preventDefault();last.focus();}else if(!event.shiftKey&&(document.activeElement===last||!current.contains(document.activeElement))){event.preventDefault();first.focus();}},true);
  if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',boot,{once:true});else boot();
  window.KGG_PATCHES=window.KGG_PATCHES||{};
  window.KGG_PATCHES[PATCH_ID]={installed:true};
})();
</script>
<!-- KGG PATCH END kgg-v117-cockpit-modal-isolation -->
