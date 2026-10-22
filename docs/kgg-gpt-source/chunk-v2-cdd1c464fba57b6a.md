<!-- KGG PATCH START kgg-v103-plan-card-action-touch-spacing -->
<!-- Normaler Plan: 44px-Aktionsziele ohne Überlappung von Bearbeiten und Löschen -->
<style id="kgg-v103-plan-card-action-touch-spacing-style">
  #currentPlanBlock #planList .planCardActions{padding-right:50px!important;gap:4px!important;min-height:44px!important;}
</style>
<script id="kgg-v103-plan-card-action-touch-spacing">
(function(){
  "use strict";
  var PATCH_ID="kgg-v103-plan-card-action-touch-spacing";
  window.KGG_PATCHES=window.KGG_PATCHES||{};
  window.KGG_PATCHES[PATCH_ID]={installed:true,version:1,dependsOn:"kgg-v099-shared-card-swipe-undo",contract:"44px edit/delete touch targets remain separately hit-testable in normal plan cards"};
})();
</script>
<!-- KGG PATCH END kgg-v103-plan-card-action-touch-spacing -->
