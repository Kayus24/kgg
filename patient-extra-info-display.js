(()=>{
  const VERSION='extra-info-v1';
  if(window.__kggExtraInfoDisplay===VERSION)return;
  window.__kggExtraInfoDisplay=VERSION;
  const KEY='kggCurrentPlanV1';
  const $=id=>document.getElementById(id);
  function dec(s){s=String(s||'').replace(/-/g,'+').replace(/_/g,'/');while(s.length%4)s+='=';return decodeURIComponent(escape(atob(s)))}
  function rawPlan(){try{let h=location.hash.slice(1);if(h.startsWith('KGGH2:'))return JSON.parse(dec(h.slice(6)))}catch(e){}try{let x=JSON.parse(localStorage.getItem(KEY)||'null');return x&&x.plan?x.plan:null}catch(e){return null}}
  function clean(s){s=String(s||'').trim();if(!s)return'';if(/^video\s*(oe|ö)?ffnen$/i.test(s))return'';return s}
  function fromObj(o){if(!o||typeof o!=='object')return'';return clean(o.patientNote||o.patientInfo||o.extraInfo||o.additionalInfo||o.note||o.info||o.hint||o.instructions||o.description||(o.media&&o.media.note)||'')}
  function fromArr(a){if(!Array.isArray(a))return fromObj(a);let m=a[7];let vals=[fromObj(m),a[10],a[11],a[12],a[13]];for(const v of vals){let x=clean(v);if(x)return x}return''}
  function notes(){let r=rawPlan();let ex=Array.isArray(r&&r.e)?r.e:Array.isArray(r&&r.exercises)?r.exercises:Array.isArray(r&&r.plan)?r.plan:[];return ex.map(fromArr)}
  function style(){if($('kggExtraInfoStyle'))return;let s=document.createElement('style');s.id='kggExtraInfoStyle';s.textContent='.kggExtraInfo{margin:8px 0 10px;padding:9px 10px;border:1px solid #dbe3ef;border-radius:12px;background:#f8fafc;color:#334155;font-size:14px;line-height:1.35;font-weight:750;white-space:pre-wrap}.kggExtraInfo:before{content:"Info: ";font-weight:950;color:#111827}';document.head.appendChild(s)}
  function apply(){style();let ns=notes();document.querySelectorAll('#list .ex').forEach((card,i)=>{let old=card.querySelector('.kggExtraInfo');let text=clean(ns[i]);if(!text){if(old)old.remove();return}if(!old){old=document.createElement('div');old.className='kggExtraInfo';let anchor=card.querySelector('.muted')||card.querySelector('h3');if(anchor&&anchor.nextSibling)anchor.parentNode.insertBefore(old,anchor.nextSibling);else card.insertBefore(old,card.firstChild&&card.firstChild.nextSibling)}old.textContent=text})}
  function init(){apply();let list=$('list');if(list&&'MutationObserver'in window)new MutationObserver(()=>setTimeout(apply,30)).observe(list,{childList:true,subtree:true});setTimeout(apply,300);setTimeout(apply,1000);setTimeout(apply,2000)}
  document.readyState==='loading'?document.addEventListener('DOMContentLoaded',init):init();
})();
