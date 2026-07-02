# KGG Source Chunk 015

- Source: `kgg-update/index.html`
- Lines: 6301-6720

```html
      bottom:auto!important;
      width:42px!important;
      min-width:42px!important;
      height:68px!important;
      min-height:68px!important;
      padding:0!important;
      display:grid!important;
      place-items:center!important;
      border-left:0!important;
      border-radius:0 16px 16px 0!important;
      background:rgba(255,255,255,.985)!important;
      box-shadow:7px 0 18px rgba(10,16,36,.10), inset 1px 0 0 rgba(255,255,255,.95)!important;
      z-index:1230!important;
    }
    body.tabletLayoutCustom.tabletMenuOpen .tabletMenuBtn::before{
      content:"";
      position:absolute;
      left:-1px;
      top:0;
      bottom:0;
      width:2px;
      background:rgba(255,255,255,.985);
    }
    body.tabletLayoutCustom.tabletMenuOpen .tabletMenuBtn span{
      width:22px!important;
      height:3px!important;
      margin:2.5px 0!important;
      border-radius:999px!important;
    }
    body.tabletLayoutCustom.tabletMenuOpen .tabletMenuBtn span:nth-child(1),
    body.tabletLayoutCustom.tabletMenuOpen .tabletMenuBtn span:nth-child(2),
    body.tabletLayoutCustom.tabletMenuOpen .tabletMenuBtn span:nth-child(3){
      transform:none!important;
      opacity:1!important;
    }
    body.tabletLayoutEditMode .tabletLayoutResizeHandle,
    body.tabletLayoutEditMode .tabletSplitScaleControl{
      pointer-events:auto!important;
    }
  }
</style>

<style id="kgg-mini-patch-v400-04-phone-clean-tablet-ui-guard">
  /* v400 mini04: Phone-Clean-Guard.
     Ziel: Tablet-/Admin-/Weitergabe-Overlays dürfen im echten Handy-Layout nicht sichtbar werden.
     Scope: nur max-width:759px. Tablet-Layout ab 760px bleibt unangetastet.
     Keine PDF-/QR-/Scan-/Parser-/Plan-State-Logik. */
  @media (max-width:759px){
    html,body{
      min-width:0!important;
      overflow-x:hidden!important;
    }
    #tabletMenuBtn,
    #tabletSideMenu,
    #tabletSideBackdrop,
    #tabletPackageShade,
    #tabletPackageOverlay,
    #tabletLayoutResizeHandle,
    #tabletSplitScaleControl,
    .tabletMenuBtn,
    .tabletSideMenu,
    .tabletSideBackdrop,
    .tabletPackageShade,
    .tabletPackageOverlay,
    .tabletLayoutResizeHandle,
    .tabletSplitScaleControl{
      display:none!important;
      visibility:hidden!important;
      opacity:0!important;
      pointer-events:none!important;
      transform:none!important;
    }
    #kggTherapistShareModal,
    #kggAdminMenuQrModal,
    .kggTherapistShareModal,
    .kggAdminMenuQrModal{
      display:none!important;
      visibility:hidden!important;
      opacity:0!important;
      pointer-events:none!important;
    }
    body.tabletMenuOpen #tabletSideMenu,
    body.tabletMenuOpen .tabletSideMenu,
    body.tabletPackageOverlayOpen #tabletPackageOverlay,
    body.tabletPackageOverlayOpen .tabletPackageOverlay{
      display:none!important;
      transform:none!important;
    }
    body.tabletMenuOpen,
    body.tabletPackageOverlayOpen,
    body.tabletLayoutEditMode{
      overflow-x:hidden!important;
    }
  }
</style>


<style id="kgg-mini-patch-v400-05-phone-remove-grey-helper-text">
  /* v400 mini05: Phone-only cleanup.
     Entfernt die grauen Hilfs-/Beschreibungstexte in Phone-Drawern und der
     Therapeuten-App-Auswahl, ohne Tablet-Layout/CSS ab 760px anzufassen. */
  @media (max-width:759px){
    .kggTherapistShareHint,
    .kggTherapistShareChoices small,
    #packageList .notice small,
    .tabletPackageBody p{
      display:none!important;
    }

    #packageList .notice b + br,
    #packageList .notice small + br{
      display:none!important;
    }

    .kggTherapistShareChoices button{
      min-height:48px!important;
      display:flex!important;
      align-items:center!important;
      padding:12px 14px!important;
    }

    .kggTherapistShareChoices b{
      font-size:16px!important;
      line-height:1.15!important;
    }

    #packageList .notice{
      display:grid!important;
      gap:8px!important;
    }

    #packageList .notice .mutedBtn{
      margin-top:0!important;
    }
  }
</style>



<style id="kgg-mini-patch-v400-06-phone-plan-gesture-fix">
  /* v400 mini06: Phone-only Plan-Karten Gesten-Fix.
     Scope: nur Handy-Layout bis 759px. Tablet-Layout ab 760px bleibt unveraendert.
     Repariert Swipe links/rechts und Drag-Reorder, die durch den Phone-Scroll-Guard
     transform/transition auf den Uebungskarten blockiert wurden. */
  @media (max-width:759px){
    body.kggPlanCardSwiping .planCard.swipe-dragging{
      transform:translateX(var(--kgg-plan-swipe-x,0px))!important;
      will-change:transform,opacity!important;
    }
    body.kggPlanCardSwiping .planCard.swipe-armed{
      transform:translateX(var(--kgg-plan-swipe-x,0px))!important;
    }
    body.kggPlanCardReordering .planCard.reorder-lifted,
    body.is-scrolling .planCard.reorder-lifted{
      transform:translateY(var(--drag-y,0px)) scale(1.035)!important;
      transition:none!important;
      will-change:transform!important;
      pointer-events:none!important;
    }
    body.kggPlanCardReordering .planList.reorder-active .planCard:not(.reorder-lifted){
      transition:transform .14s ease,margin .14s ease,opacity .14s ease!important;
    }
    body.kggPlanCardReordering .planCard.reorder-placeholder{
      display:block!important;
      visibility:visible!important;
    }
  }
</style>




<style id="kgg-mini-patch-v400-07-android-wrapper-fixes">
  /* v400 mini07: Android-WebView/Phone polish.
     Scope: UI-only. Tablet layout ab 760px bleibt unveraendert. */
  @media (max-width:759px){
    body.kggPlanCardReordering #bankArea,
    body.kggPlanCardReordering #dbTitle,
    body.kggPlanCardReordering .bankArea,
    body.kggPlanCardReordering .bankRows,
    body.kggPlanCardReordering .az{
      pointer-events:none!important;
    }
    body.kggPlanCardReordering .planCard.reorder-lifted,
    body.is-scrolling.kggPlanCardReordering .planCard.reorder-lifted{
      transform:translateY(var(--drag-y,0px)) scale(1.035)!important;
      z-index:9999!important;
      transition:none!important;
      will-change:transform!important;
      pointer-events:none!important;
    }
    body.kggPlanCardSwiping .planCard.swipe-dragging,
    body.is-scrolling.kggPlanCardSwiping .planCard.swipe-dragging{
      transform:translateX(var(--kgg-plan-swipe-x,0px))!important;
      transition:none!important;
      will-change:transform,opacity!important;
    }
    body.kggPlanCardSwiping .planCard.swipe-removing,
    body.is-scrolling.kggPlanCardSwiping .planCard.swipe-removing{
      transform:translateX(var(--kgg-plan-swipe-x,0px))!important;
    }
    .modal.open{
      overscroll-behavior:contain;
    }
    .sheet{
      -webkit-overflow-scrolling:touch;
    }
  }
</style>

<style id="kgg-github-patch-v401-phone-plan-ui-isolation">
  /* v401 GitHub Update 003: Phone-only Plan-UI Stabilisierung.
     Fixes:
     - Plan-Karten flackern beim Scrollen nicht mehr.
     - Antippen/Anheben einer Plan-Karte darf den Rest der App nicht nach unten schieben.
     - Reorder-Bewegungen bleiben innerhalb "Übungen im Plan".
     Scope: nur max-width:759px. Tablet-/Wrapper-Code bleibt unverändert. */
  @media (max-width:759px){
    #rightPlanStack,
    #currentPlanBlock.planSectionCurrent{
      contain:layout paint!important;
      overflow:hidden!important;
      transform:translateZ(0);
      backface-visibility:hidden;
      -webkit-backface-visibility:hidden;
    }

    body.kggPlanSectionFrozen #currentPlanBlock.planSectionCurrent{
      height:var(--kgg-current-plan-freeze-h,auto)!important;
      min-height:var(--kgg-current-plan-freeze-h,auto)!important;
      max-height:var(--kgg-current-plan-freeze-h,none)!important;
    }

    #currentPlanBlock .planSectionBody{
      contain:layout paint!important;
      overflow:auto!important;
      overscroll-behavior:contain!important;
      -webkit-overflow-scrolling:touch;
      max-height:min(46dvh,380px);
      transform:translateZ(0);
      backface-visibility:hidden;
      -webkit-backface-visibility:hidden;
    }

    #currentPlanBlock #planList.planList{
      contain:layout paint!important;
      isolation:isolate;
      transform:translateZ(0);
      backface-visibility:hidden;
      -webkit-backface-visibility:hidden;
    }

    #currentPlanBlock .planCard{
      backface-visibility:hidden;
      -webkit-backface-visibility:hidden;
      transform:translate3d(0,0,0);
      will-change:auto;
    }

    body.is-scrolling #currentPlanBlock .planCard:not(.swipe-dragging):not(.swipe-removing):not(.reorder-lifted):not(.reorder-prelift){
      transform:translate3d(0,0,0)!important;
      transition:none!important;
      animation:none!important;
      filter:none!important;
    }

    #currentPlanBlock .planCard.reorder-prelift,
    body.kggPlanSectionFrozen #currentPlanBlock .planCard.reorder-prelift{
      position:relative;
      z-index:8;
      transform:translate3d(0,-3px,0) scale(1.018)!important;
      box-shadow:0 10px 26px rgba(7,16,39,.16),0 2px 8px rgba(7,16,39,.10)!important;
      transition:transform .11s cubic-bezier(.2,.85,.2,1),box-shadow .11s ease!important;
    }

    body.kggPlanCardReordering #currentPlanBlock .planSectionBody{
      overflow:hidden!important;
      touch-action:none!important;
    }

    body.kggPlanCardReordering #currentPlanBlock .planCard.reorder-lifted,
    body.is-scrolling.kggPlanCardReordering #currentPlanBlock .planCard.reorder-lifted{
      transform:translate3d(0,var(--drag-y,0px),0) scale(1.035)!important;
      z-index:9999!important;
      opacity:.985!important;
      transition:none!important;
      pointer-events:none!important;
      will-change:transform!important;
    }

    body.kggPlanCardReordering #currentPlanBlock .planCard.reorder-placeholder{
      height:20px!important;
      min-height:20px!important;
      padding:0!important;
      margin:2px 0!important;
      border:0!important;
      border-radius:999px!important;
      background:transparent!important;
      box-shadow:none!important;
      overflow:visible!important;
      opacity:1!important;
      transform:none!important;
    }

    body.kggPlanCardReordering #currentPlanBlock .planCard.reorder-placeholder::before{
      content:"";
      position:absolute;
      left:16%;
      right:16%;
      top:50%;
      height:12px;
      transform:translateY(-50%);
      border-radius:999px;
      background:radial-gradient(ellipse at center,rgba(7,16,39,.20) 0%,rgba(7,16,39,.10) 45%,rgba(7,16,39,0) 78%);
      filter:blur(7px);
    }

    body.kggPlanCardReordering #currentPlanBlock .planCard.reorder-gap-before,
    body.kggPlanCardReordering #currentPlanBlock .planCard.reorder-gap-after{
      margin-top:0!important;
      margin-bottom:0!important;
    }

    body.kggPlanCardReordering :is(#bankArea,#dbTitle,.bankArea,.bankRows,.az,#inputWrap,#exerciseInput,.suggestion){
      transition:none!important;
      animation:none!important;
      transform:none!important;
      filter:none!important;
      pointer-events:none!important;
    }
  }
</style>
<style id="kgg-mini-patch-v400-08-phone-hide-admin-file-banner">
  /* v400 mini08: Phone-only cleanup.
     Entfernt die gelbe ADMIN-DATEI/Admin-Test-Box nur im Handy-Layout.
     Tablet-Layout ab 760px bleibt unveraendert. */
  @media (max-width:759px){
    .adminTestBanner{
      display:none!important;
    }
  }
</style>

  <!-- KGG kgg-source-truth: embedded Source Truth. Machine-readable; safe for local LLM/code review. -->
<!-- KGG kgg-changelog: embedded Changelog. Machine-readable; safe for local LLM/code review. -->

<!-- KGG PATCH START kgg-v021-embed-jsqr-gallery-decode lib sha256=bc40c8a15196236b2314db0856f72ca0b49980cd5413b8c852a7349f5fee0859 -->
<script id="kgg-v021-embed-jsqr-gallery-decode-lib">
(function webpackUniversalModuleDefinition(root, factory) {
	if(typeof exports === 'object' && typeof module === 'object')
		module.exports = factory();
	else if(typeof define === 'function' && define.amd)
		define([], factory);
	else if(typeof exports === 'object')
		exports["jsQR"] = factory();
	else
		root["jsQR"] = factory();
})(typeof self !== 'undefined' ? self : this, function() {
return /******/ (function(modules) { // webpackBootstrap
/******/ 	// The module cache
/******/ 	var installedModules = {};
/******/
/******/ 	// The require function
/******/ 	function __webpack_require__(moduleId) {
/******/
/******/ 		// Check if module is in cache
/******/ 		if(installedModules[moduleId]) {
/******/ 			return installedModules[moduleId].exports;
/******/ 		}
/******/ 		// Create a new module (and put it into the cache)
/******/ 		var module = installedModules[moduleId] = {
/******/ 			i: moduleId,
/******/ 			l: false,
/******/ 			exports: {}
/******/ 		};
/******/
/******/ 		// Execute the module function
/******/ 		modules[moduleId].call(module.exports, module, module.exports, __webpack_require__);
/******/
/******/ 		// Flag the module as loaded
/******/ 		module.l = true;
/******/
/******/ 		// Return the exports of the module
/******/ 		return module.exports;
/******/ 	}
/******/
/******/
/******/ 	// expose the modules object (__webpack_modules__)
/******/ 	__webpack_require__.m = modules;
/******/
/******/ 	// expose the module cache
/******/ 	__webpack_require__.c = installedModules;
/******/
/******/ 	// define getter function for harmony exports
/******/ 	__webpack_require__.d = function(exports, name, getter) {
/******/ 		if(!__webpack_require__.o(exports, name)) {
/******/ 			Object.defineProperty(exports, name, {
/******/ 				configurable: false,
/******/ 				enumerable: true,
/******/ 				get: getter
/******/ 			});
/******/ 		}
/******/ 	};
/******/
/******/ 	// getDefaultExport function for compatibility with non-harmony modules
/******/ 	__webpack_require__.n = function(module) {
/******/ 		var getter = module && module.__esModule ?
/******/ 			function getDefault() { return module['default']; } :
/******/ 			function getModuleExports() { return module; };
/******/ 		__webpack_require__.d(getter, 'a', getter);
/******/ 		return getter;
/******/ 	};
/******/
/******/ 	// Object.prototype.hasOwnProperty.call
/******/ 	__webpack_require__.o = function(object, property) { return Object.prototype.hasOwnProperty.call(object, property); };
/******/
/******/ 	// __webpack_public_path__
/******/ 	__webpack_require__.p = "";
/******/
/******/ 	// Load entry module and return exports
```
