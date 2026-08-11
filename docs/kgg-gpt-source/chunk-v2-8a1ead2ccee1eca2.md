
<!-- KGG PATCH START kgg-v046-tablet-runtime-viewport-guard -->
<script id="kgg-v046-tablet-runtime-viewport-guard-script">
(function(){
  "use strict";
  var PATCH_ID="kgg-v046-tablet-runtime-viewport-guard";
  var PHONE_QUERY="(max-width:759px)";
  function isPhoneViewport(){return !!(window.matchMedia&&window.matchMedia(PHONE_QUERY).matches);}
  window.KGG_TABLET_RUNTIME_VIEWPORT_GUARD_V046={
    patchId:PATCH_ID,
    phoneQuery:PHONE_QUERY,
    check:function(){
      return {
        patchId:PATCH_ID,
        phoneViewport:isPhoneViewport(),
        phoneHasPlanClass:!!(document.body&&document.body.classList.contains("kggPhoneHasPlan")),
        phonePhotoOpen:!!(document.body&&document.body.classList.contains("kggPhonePhotoMenuOpen")),
        scanHydrated:!!(document.getElementById("scanBtn")&&document.getElementById("scanBtn").dataset.kggV042ScanHydrated==="1")
      };
    }
  };
})();
</script>
<!-- KGG PATCH END kgg-v046-tablet-runtime-viewport-guard -->
