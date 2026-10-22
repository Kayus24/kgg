<!-- KGG PATCH START kgg-v108-cockpit-add-modal-dismissal -->
<!-- Cockpit Add-Modal Schliessen -->
<script id="kgg-v108-cockpit-add-modal-dismissal">
(function(){
  "use strict";
  const PATCH_ID="kgg-v108-cockpit-add-modal-dismissal";
  let installed=false;
  function modal(){return document.getElementById("kggTceAddModal");}
  function restoreFocus(node){
    const slot=String(node&&node.dataset&&node.dataset.tceSlot||"");
    window.setTimeout(function(){
      const trigger=document.querySelector('.kgg-tce-add-card[data-tce-slot="'+slot+'"]');
      if(trigger&&typeof trigger.focus==="function")trigger.focus();
    },0);
  }
  function close(node){
    if(!node||node.hidden)return false;
    node.hidden=true;
    restoreFocus(node);
    return true;
  }
  function install(){
    if(installed)return;
    const node=modal();
    if(!node){window.setTimeout(install,50);return;}
    installed=true;
    node.addEventListener("click",function(event){if(event.target===node)close(node);});
    document.addEventListener("keydown",function(event){
      if(event.key!=="Escape")return;
      const current=modal();
      if(!current||current.hidden)return;
      event.preventDefault();event.stopPropagation();close(current);
    },true);
    window.KGG_PATCHES=window.KGG_PATCHES||{};
    window.KGG_PATCHES[PATCH_ID]={installed:true,version:1,dependsOn:"kgg-v107-cockpit-seam-pull-handle",contract:"cockpit add modal closes by existing cancel action, Escape or backdrop without closing from inside-sheet clicks"};
  }
  if(document.readyState==="loading")document.addEventListener("DOMContentLoaded",install,{once:true});else install();
})();
</script>
<!-- KGG PATCH END kgg-v108-cockpit-add-modal-dismissal -->
