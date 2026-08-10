<!-- KGG PATCH START kgg-v062-tablet-recent-package-shell-geometry -->
<!-- Plan-Historie mit stabiler Hintergrund-Geometrie -->
<style id="kgg-v062-tablet-recent-package-shell-geometry-style">
.tabletRecentHost[hidden]{display:none!important;}
@media (min-width:760px){
  body.tabletLayoutCustom.tabletMenuOpen.tabletPackageOverlayOpen .app{
    width:calc(100vw - var(--kgg-tablet-sidebar-w,380px))!important;
    max-width:calc(100vw - var(--kgg-tablet-sidebar-w,380px))!important;
    transform:translateX(var(--kgg-tablet-sidebar-w,380px))!important;
  }
  body.tabletRecentOverlayMode #tabletPackageOverlay .tabletPackageSearch,
  body.tabletRecentOverlayMode #tabletPackageOverlay #tabletPackageCards{
    display:none!important;
  }
  body.tabletRecentOverlayMode #tabletPackageOverlay #tabletRecentHost{
    display:grid!important;
    grid-template-columns:minmax(0,1fr);
    gap:12px;
    min-height:0;
    overflow:auto;
    padding:2px 2px 8px;
    overscroll-behavior:contain;
  }
  body.tabletRecentOverlayMode #tabletPackageOverlay #recentList:not(.hidden){
    display:grid!important;
    gap:12px!important;
    position:static!important;
    inset:auto!important;
    left:auto!important;
    right:auto!important;
    top:auto!important;
    bottom:auto!important;
    width:100%!important;
    max-width:none!important;
    max-height:none!important;
    overflow:visible!important;
    z-index:auto!important;
    margin:0!important;
    padding:0!important;
    background:transparent!important;
    border:0!important;
    border-radius:0!important;
    box-shadow:none!important;
    transform:none!important;
    animation:none!important;
  }
  body.tabletRecentOverlayMode #tabletPackageOverlay #recentList>.notice{margin:0!important;}
  body.tabletRecentOverlayMode #tabletMenuRecentBtn{background:#eef5ff!important;color:#071027!important;box-shadow:inset 3px 0 0 #0b63ce,0 8px 18px rgba(7,16,39,.08)!important;}
  body.tabletRecentOverlayMode #tabletMenuPackagesBtn{background:#fff!important;color:#0a1024!important;box-shadow:0 10px 22px rgba(10,16,36,.07),inset 0 1px 0 rgba(255,255,255,.82)!important;}
}
</style>
<script id="kgg-v062-tablet-recent-package-shell-geometry">
(function(){
  'use strict';
  var PATCH_ID='kgg-v062-tablet-recent-package-shell-geometry';
  var TABLET_QUERY='(min-width:760px)';
  var recentMode=false,allowPackageClick=false,returnFocusAfterClose=false,closeCleanupTimer=0,focusTimer=0,opener=null,originMarker=null,originParent=null,originNext=null,shellDefaults=null;
  function byId(id){return document.getElementById(id);}
  function isTablet(){return !!(window.matchMedia&&window.matchMedia(TABLET_QUERY).matches&&document.body&&document.body.classList.contains('tabletLayoutCustom'));}
  function shellParts(){var overlay=byId('tabletPackageOverlay');return {overlay:overlay,shade:byId('tabletPackageShade'),close:byId('tabletPackageClose'),search:overlay&&overlay.querySelector('.tabletPackageSearch'),cards:byId('tabletPackageCards'),titleIcon:overlay&&overlay.querySelector('.tabletPackageTitle span'),titleText:overlay&&overlay.querySelector('.tabletPackageTitle strong')};}
  function rememberShellDefaults(parts){if(shellDefaults||!parts.overlay)return;shellDefaults={overlayLabel:parts.overlay.getAttribute('aria-label')||'Uebungspakete',closeLabel:parts.close&&parts.close.getAttribute('aria-label')||'Uebungspakete schliessen',icon:parts.titleIcon&&parts.titleIcon.textContent||'📦',title:parts.titleText&&parts.titleText.textContent||'Übungspakete'};}
  function ensureRecentHost(){var parts=shellParts(),recent=byId('recentList');if(!parts.overlay||!recent)return null;rememberShellDefaults(parts);var host=byId('tabletRecentHost');if(!host){host=document.createElement('div');host.id='tabletRecentHost';host.className='tabletRecentHost';host.hidden=true;parts.overlay.appendChild(host);}if(!originMarker||!originMarker.parentNode){originParent=recent.parentNode;originNext=recent.nextSibling;originMarker=document.createComment('kgg-tablet-recent-origin');if(originParent)originParent.insertBefore(originMarker,recent);}return host;}
  function restoreRecentNode(){var recent=byId('recentList');if(!recent)return;if(originMarker&&originMarker.parentNode){originMarker.parentNode.insertBefore(recent,originMarker.nextSibling);return;}if(originParent){var next=originNext&&originNext.parentNode===originParent?originNext:null;originParent.insertBefore(recent,next);}}
  function setExpanded(id,value){var el=byId(id);if(el)el.setAttribute('aria-expanded',String(!!value));}
  function setRecentChrome(){var parts=shellParts();rememberShellDefaults(parts);if(parts.overlay)parts.overlay.setAttribute('aria-label','Plan-Historie');if(parts.close)parts.close.setAttribute('aria-label','Plan-Historie schliessen');if(parts.titleIcon)parts.titleIcon.textContent='🕘';if(parts.titleText)parts.titleText.textContent='Plan-Historie';setExpanded('tabletMenuRecentBtn',true);setExpanded('recentToggle',true);setExpanded('tabletMenuPackagesBtn',false);setExpanded('packageToggle',false);}
  function restorePackageChrome(keepOverlay){var parts=shellParts();if(shellDefaults){if(parts.overlay)parts.overlay.setAttribute('aria-label',shellDefaults.overlayLabel);if(parts.close)parts.close.setAttribute('aria-label',shellDefaults.closeLabel);if(parts.titleIcon)parts.titleIcon.textContent=shellDefaults.icon;if(parts.titleText)parts.titleText.textContent=shellDefaults.title;}setExpanded('tabletMenuRecentBtn',false);setExpanded('recentToggle',false);setExpanded('tabletMenuPackagesBtn',!!keepOverlay);setExpanded('packageToggle',!!keepOverlay);}
  function focusRecentEntry(){clearTimeout(focusTimer);focusTimer=setTimeout(function(){if(!recentMode)return;var recent=byId('recentList');var target=recent&&recent.querySelector('[data-recent-index]');if(!target)target=byId('tabletPackageClose');if(target&&target.focus)target.focus();},80);}
  function cleanupTabletRecentMode(options){options=options||{};if(!recentMode&&!document.body.classList.contains('tabletRecentOverlayMode'))return;clearTimeout(closeCleanupTimer);clearTimeout(focusTimer);var focusTarget=opener;var keepOverlay=!!options.keepOverlay&&document.body.classList.contains('tabletPackageOverlayOpen');recentMode=false;document.body.classList.remove('tabletRecentOverlayMode');var recent=byId('recentList');if(recent)recent.classList.add('hidden');restoreRecentNode();var host=byId('tabletRecentHost');if(host)host.hidden=true;restorePackageChrome(keepOverlay);opener=null;returnFocusAfterClose=false;if(options.focus&&focusTarget&&focusTarget.isConnected&&focusTarget.focus){setTimeout(function(){try{focusTarget.focus();}catch(err){}},0);}}
  function scheduleClosedCleanup(){clearTimeout(closeCleanupTimer);closeCleanupTimer=setTimeout(function(){if(recentMode&&!document.body.classList.contains('tabletPackageOverlayOpen'))cleanupTabletRecentMode({focus:returnFocusAfterClose});},240);}
  function openOriginalPackageShell(){if(document.body.classList.contains('tabletPackageOverlayOpen'))return true;var button=byId('tabletMenuPackagesBtn')||byId('packageToggle');if(!button)return false;allowPackageClick=true;try{button.click();}finally{allowPackageClick=false;}return document.body.classList.contains('tabletPackageOverlayOpen');}
  function openTabletRecentInPackageShell(source){if(!isTablet())return false;if(recentMode){returnFocusAfterClose=true;var closeButton=byId('tabletPackageClose');if(closeButton)closeButton.click();else cleanupTabletRecentMode({focus:true});return true;}var host=ensureRecentHost(),recent=byId('recentList');if(!host||!recent)return false;opener=source||byId('tabletMenuRecentBtn')||byId('recentToggle');recent.classList.add('hidden');['--kgg-overlay-width','--kgg-overlay-left','--kgg-overlay-top','--kgg-overlay-max-height','--kgg-overlay-origin'].forEach(function(name){recent.style.removeProperty(name);});if(!openOriginalPackageShell())return false;document.body.classList.add('tabletRecentOverlayMode');recentMode=true;returnFocusAfterClose=false;host.hidden=false;host.appendChild(recent);recent.classList.remove('hidden');setRecentChrome();focusRecentEntry();return true;}
  function switchToPackages(){if(!recentMode)return false;cleanupTabletRecentMode({keepOverlay:true,focus:false});clearTimeout(focusTimer);focusTimer=setTimeout(function(){var input=byId('tabletPackageSearch');if(input&&input.focus)input.focus();},60);return true;}
  function closeAfterRecentRestore(){setTimeout(function(){if(!recentMode)return;returnFocusAfterClose=false;var closeButton=byId('tabletPackageClose');if(closeButton)closeButton.click();else cleanupTabletRecentMode({focus:false});},0);}
  function captureTabletClicks(ev){var target=ev.target&&ev.target.closest?ev.target.closest('button,#tabletPackageShade'):null;if(!target)return;if(recentMode){var restore=ev.target.closest&&ev.target.closest('#tabletRecentHost [data-recent-index]');if(restore){returnFocusAfterClose=false;closeAfterRecentRestore();return;}if((target.id==='tabletMenuPackagesBtn'||target.id==='packageToggle')&&!allowPackageClick){ev.preventDefault();ev.stopPropagation();if(ev.stopImmediatePropagation)ev.stopImmediatePropagation();switchToPackages();return;}if(target.id==='tabletMenuRecentBtn'||target.id==='recentToggle'){ev.preventDefault();ev.stopPropagation();if(ev.stopImmediatePropagation)ev.stopImmediatePropagation();returnFocusAfterClose=true;var closeButton=byId('tabletPackageClose');if(closeButton)closeButton.click();else cleanupTabletRecentMode({focus:true});return;}if(target.id==='tabletPackageClose'||target.id==='tabletPackageShade'){returnFocusAfterClose=true;return;}if(target.id==='tabletMenuClose'||target.id==='tabletMenuBtn'||target.id==='tabletSideBackdrop'||target.closest('.tabletSideMenuAction'))returnFocusAfterClose=false;}if(!isTablet()||allowPackageClick)return;if(target.id==='tabletMenuRecentBtn'||target.id==='recentToggle'){ev.preventDefault();ev.stopPropagation();if(ev.stopImmediatePropagation)ev.stopImmediatePropagation();openTabletRecentInPackageShell(target);}}
  function install(){if(!document.body)return;ensureRecentHost();document.addEventListener('click',captureTabletClicks,true);document.addEventListener('keydown',function(ev){if(recentMode&&ev.key==='Escape')returnFocusAfterClose=true;},true);new MutationObserver(function(){if(recentMode&&!document.body.classList.contains('tabletPackageOverlayOpen'))scheduleClosedCleanup();}).observe(document.body,{attributes:true,attributeFilter:['class']});var recent=byId('recentList');if(recent)new MutationObserver(function(){if(recentMode&&recent.classList.contains('hidden')&&document.body.classList.contains('tabletPackageOverlayOpen'))closeAfterRecentRestore();}).observe(recent,{attributes:true,attributeFilter:['class']});var cleanupViewport=function(){if(recentMode&&!isTablet())cleanupTabletRecentMode({focus:false});};window.addEventListener('resize',function(){setTimeout(cleanupViewport,40);},{passive:true});window.addEventListener('orientationchange',function(){setTimeout(cleanupViewport,140);},{passive:true});window.addEventListener('pageshow',cleanupViewport,{passive:true});}
  if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',install,{once:true});else install();
  window.KGG_TABLET_RECENT_PACKAGE_SHELL={patchId:PATCH_ID,open:openTabletRecentInPackageShell,cleanup:cleanupTabletRecentMode,switchToPackages:switchToPackages};
  window.KGG_PATCHES=window.KGG_PATCHES||{};window.KGG_PATCHES[PATCH_ID]={installed:true,kind:'kgg-tablet-recent-package-shell-geometry'};
})();
</script>
<!-- KGG PATCH END kgg-v062-tablet-recent-package-shell-geometry -->
