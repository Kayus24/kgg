<!-- KGG PATCH START kgg-v094-shared-reorder-core -->
<!-- Shared Reorder Core -->
<script id="kgg-v094-shared-reorder-core">
(function(){
  "use strict";
  const PATCH_ID="kgg-v094-shared-reorder-core";
  var shared=window.KGGSharedReorder;
  window.KGG_PATCHES=window.KGG_PATCHES||{};
  window.KGG_PATCHES[PATCH_ID]={installed:!!(shared&&typeof shared.targetIndex==='function'&&typeof shared.move==='function'),version:1,contract:"normal plan and Therapy-Cockpit use the same reorder target and array semantics"};
})();
</script>
<!-- KGG PATCH END kgg-v094-shared-reorder-core -->
