(()=>{
  const VERSION='v4_inner_input_focus_ring';
  const STYLE='kggPatientUiMicroPolishStyle';
  const $=id=>document.getElementById(id);

  function ensureStyle(){
    const old=$(STYLE); if(old) old.remove();
    const s=document.createElement('style'); s.id=STYLE;
    s.textContent=`
      .kggPainScale button{display:flex!important;align-items:center!important;justify-content:center!important;text-align:center!important;line-height:1!important;padding:0!important;min-height:44px!important;font-variant-numeric:tabular-nums!important;-webkit-font-smoothing:antialiased!important}
      .kggPainScale button.on{transform:translateY(-2px)!important}.kggPainScale button:active{transform:scale(.94)!important}
      input.num{box-sizing:border-box!important;display:block!important;width:100%!important;line-height:1.15!important;transform:none!important;transition:background .16s ease,box-shadow .16s ease,border-color .16s ease!important}
      input.num.kggEditing{outline:none!important;box-shadow:inset 0 0 0 3px rgba(17,24,39,.92)!important;border-color:#111827!important;background:#f8fafc!important;transform:none!important;position:relative!important;z-index:2!important}
      .set input.num,.set .num{min-width:0!important}.set{align-items:stretch!important}
      body.kggAlwaysCollapsed .ex .pain:not(.kggHiddenGlobalPain){padding-left:10px!important;padding-right:10px!important;margin-top:18px!important}
      body.kggAlwaysCollapsed .ex .pain:not(.kggHiddenGlobalPain) .painRow{display:grid!important;grid-template-columns:minmax(0,1fr) 44px!important;gap:6px!important;align-items:center!important;width:100%!important}
      body.kggAlwaysCollapsed .ex .pain:not(.kggHiddenGlobalPain) .kggPainScale{margin-top:0!important;min-width:0!important;width:100%!important;grid-template-columns:repeat(11,minmax(28px,1fr))!important;gap:5px!important}
      body.kggAlwaysCollapsed .ex .pain:not(.kggHiddenGlobalPain) .kggPainScale button{min-height:48px!important;border-radius:13px!important;font-size:17px!important;font-weight:950!important}
      body.kggAlwaysCollapsed .ex .pain:not(.kggHiddenGlobalPain) .kggPainCaption{margin-top:0!important;min-width:44px!important;text-align:right!important;font-size:15px!important;font-weight:950!important;align-self:center!important;white-space:nowrap!important;color:#475569!important}
      .kggSetPain .kggPainScale{gap:4px!important}.kggSetPain .kggPainScale button{min-height:42px!important;font-size:14px!important;border-radius:11px!important}
      body.kggAlwaysCollapsed .ex.kggHasSetPain > .pain,body.kggAlwaysCollapsed .ex .pain.kggHiddenGlobalPain{display:none!important;max-height:0!important;opacity:0!important;margin:0!important;padding:0!important;border:0!important;pointer-events:none!important}
      body.kggAlwaysCollapsed .ex{transition:box-shadow .20s ease,border-color .20s ease,background .20s ease,transform .18s ease!important}
      body.kggAlwaysCollapsed .ex .set,body.kggAlwaysCollapsed .ex .pain{display:block!important;overflow:hidden!important;opacity:1;transform:translateY(0);max-height:380px;transition:max-height .24s cubic-bezier(.16,.84,.44,1),opacity .18s ease,transform .22s cubic-bezier(.16,.84,.44,1),margin .20s ease,padding .20s ease,border-color .20s ease!important;will-change:max-height,opacity,transform}
      body.kggAlwaysCollapsed .ex .pain{max-height:290px}
      body.kggAlwaysCollapsed .ex:not(.kggOpen) .set,body.kggAlwaysCollapsed .ex:not(.kggOpen) .pain{display:block!important;max-height:0!important;opacity:0!important;transform:translateY(-6px)!important;margin-top:0!important;margin-bottom:0!important;padding-top:0!important;padding-bottom:0!important;border-top-color:transparent!important;border-bottom-color:transparent!important;pointer-events:none!important}
      body.kggAlwaysCollapsed .ex.kggOpen .set,body.kggAlwaysCollapsed .ex.kggOpen .pain{opacity:1!important;transform:translateY(0)!important}
      body.kggAlwaysCollapsed .ex.kggOpen{animation:kggCardOpenSoft .20s ease both}@keyframes kggCardOpenSoft{from{transform:translateY(-2px)}to{transform:translateY(0)}}
      .kggSettingsBackdrop{animation:kggSettingsBackdropIn .16s ease both!important}.kggSettingsBackdrop.kggClosing{animation:kggSettingsBackdropOut .16s ease both!important}
      #kggSettingsSheet{transform-origin:bottom center!important;animation:kggSettingsSheetIn .22s cubic-bezier(.16,.84,.44,1) both!important;will-change:transform,opacity!important}#kggSettingsSheet.kggClosing{animation:kggSettingsSheetOut .16s ease both!important;pointer-events:none!important}
      @keyframes kggSettingsSheetIn{from{opacity:0;transform:translateY(18px) scale(.985)}to{opacity:1;transform:translateY(0) scale(1)}}@keyframes kggSettingsSheetOut{from{opacity:1;transform:translateY(0) scale(1)}to{opacity:0;transform:translateY(14px) scale(.985)}}@keyframes kggSettingsBackdropIn{from{opacity:0}to{opacity:1}}@keyframes kggSettingsBackdropOut{from{opacity:1}to{opacity:0}}
      @media(max-width:430px){body.kggAlwaysCollapsed .ex .pain:not(.kggHiddenGlobalPain){padding-left:8px!important;padding-right:8px!important}body.kggAlwaysCollapsed .ex .pain:not(.kggHiddenGlobalPain) .painRow{grid-template-columns:minmax(0,1fr) 38px!important;gap:5px!important}body.kggAlwaysCollapsed .ex .pain:not(.kggHiddenGlobalPain) .kggPainScale{gap:4px!important;grid-template-columns:repeat(11,minmax(24px,1fr))!important}body.kggAlwaysCollapsed .ex .pain:not(.kggHiddenGlobalPain) .kggPainScale button{min-height:44px!important;font-size:16px!important;border-radius:12px!important}body.kggAlwaysCollapsed .ex .pain:not(.kggHiddenGlobalPain) .kggPainCaption{min-width:38px!important;font-size:14px!important}.kggSetPain .kggPainScale button{min-height:40px!important;font-size:13px!important}}
      @media(prefers-reduced-motion:reduce){body.kggAlwaysCollapsed .ex,body.kggAlwaysCollapsed .ex .set,body.kggAlwaysCollapsed .ex .pain,#kggSettingsSheet,.kggSettingsBackdrop{animation:none!important;transition:none!important}}
    `;
    document.head.appendChild(s);
  }

  function markPainModeCards(){document.querySelectorAll('#list .ex').forEach(card=>{const hasSetPain=!!card.querySelector('.kggSetPain');card.classList.toggle('kggHasSetPain',hasSetPain);const global=card.querySelector(':scope > .pain');if(global)global.classList.toggle('kggHiddenGlobalPain',hasSetPain)})}
  function softClose(e){const sh=$('kggSettingsSheet'),bd=$('kggSettingsBackdrop');if(!sh||sh.hidden)return;const target=e.target;if(!(target&&((target.id==='kggSettingsBackdrop')||(target.closest&&target.closest('#kggSetCancel')))))return;e.preventDefault();e.stopPropagation();if(e.stopImmediatePropagation)e.stopImmediatePropagation();sh.classList.add('kggClosing');if(bd)bd.classList.add('kggClosing');setTimeout(()=>{sh.hidden=true;sh.classList.remove('kggClosing');if(bd){bd.hidden=true;bd.classList.remove('kggClosing')}},170)}
  function apply(){ensureStyle();setTimeout(markPainModeCards,0);setTimeout(markPainModeCards,60)}
  function patchRender(){if(window.__kggUiMicroPolishRenderPatch||typeof render!=='function')return;window.__kggUiMicroPolishRenderPatch=1;const old=render;render=function(){const r=old.apply(this,arguments);setTimeout(apply,30);return r}}
  function init(){if(window.__kggPatientUiMicroPolish===VERSION)return;window.__kggPatientUiMicroPolish=VERSION;apply();patchRender();document.addEventListener('click',softClose,true);setTimeout(apply,300);setTimeout(apply,1000);setTimeout(apply,2000)}
  document.readyState==='loading'?document.addEventListener('DOMContentLoaded',init):init();
})();
