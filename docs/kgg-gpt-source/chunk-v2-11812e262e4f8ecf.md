<!-- KGG PATCH START kgg-v118-cockpit-scroll-position -->
<style id="kgg-v118-cockpit-scroll-position-style">
@media(max-width:759px){
 #kggTherapyCockpitBoard{display:flex!important;flex-direction:column!important;min-height:0!important;overflow:hidden!important;}
 .kgg-tce-mobile-nav{flex:0 0 auto!important;}
 .kgg-tc-grid.kgg-tce-mobile-grid{flex:1 1 auto!important;min-height:0!important;height:100%!important;overflow:hidden!important;}
 .kgg-tce-mobile-grid .kgg-tc-card{height:100%!important;min-height:0!important;overflow:hidden!important;}
 .kgg-tce-mobile-grid .kgg-tc-card-body{min-height:0!important;overflow:hidden!important;}
 .kgg-tce-mobile-grid .kgg-tc-scroll{flex:1 1 auto!important;min-height:0!important;overflow-y:auto!important;}
}
</style>
<script id="kgg-v118-cockpit-scroll-position">
(function(){
  "use strict";
  const PATCH_ID="kgg-v118-cockpit-scroll-position";
  // Den kleinstmoeglichen Patch hier implementieren. Bestehende Hooks beibehalten.
  window.KGG_PATCHES=window.KGG_PATCHES||{};
  window.KGG_PATCHES[PATCH_ID]={installed:true};
})();
</script>
<!-- KGG PATCH END kgg-v118-cockpit-scroll-position -->
