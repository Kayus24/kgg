(()=>{
const V='last-value-hints-v2-units';
if(window.__kggLastValueHints===V)return;
window.__kggLastValueHints=V;
const $=id=>document.getElementById(id);
function css(){if($('kggLastValueHintsStyle'))return;const s=document.createElement('style');s.id='kggLastValueHintsStyle';s.textContent='input.num::placeholder{color:#cbd5e1!important;opacity:1!important;font-weight:900!important}input.num.kggHasLastHint{background:linear-gradient(#fff,#fff)!important}';document.head.appendChild(s)}
function metaFromInput(input){
 if(!input)return null;
 if(input.__kggLastMeta)return input.__kggLastMeta;
 const a=input.getAttribute('onclick')||input.getAttribute('onfocus')||'';
 const g=(re)=>{const m=a.match(re);return m?m[1]:''};
 const ei=Number(g(/ei\s*:\s*(\d+)/));
 const s=Number(g(/s\s*:\s*(\d+)/));
 const side=g(/side\s*:\s*['"]([^'"]+)['"]/);
 const key=g(/key\s*:\s*['"]([^'"]+)['"]/);
 if(Number.isFinite(ei)&&Number.isFinite(s)&&side&&key){input.__kggLastMeta={ei,s,side,key};return input.__kggLastMeta}
 return null;
}
function first(a){for(const x of a){if(x!==undefined&&x!==null&&String(x).trim()!=='')return String(x)}return''}
function prevValue(m){
 if(!m||typeof v==='undefined'||typeof k!=='function')return'';
 const day=Number(typeof d!=='undefined'?d:1)||1;
 const other=m.side==='L'?'R':m.side==='R'?'L':'B';
 for(let dd=day-1;dd>=1;dd--){
   let arr=[v[k(m.ei,m.s,m.side,m.key,dd)]];
   if(m.side!=='B')arr.push(v[k(m.ei,m.s,other,m.key,dd)]);
   let x=first(arr);if(x)return x;
 }
 if(typeof getLastValue==='function')return getLastValue(m)||'';
 return'';
}
function unitFor(m){
 try{
   const ex=(typeof p!=='undefined'&&p&&p.ex&&m)?p.ex[m.ei]:null;
   const raw=m&&m.key==='b'?(ex&&ex.m):(ex&&ex.u);
   const unit=String(raw||'').trim();
   return /^(keine|none|-)$/i.test(unit)?'':unit;
 }catch(e){return''}
}
function hintText(m,last){const unit=unitFor(m);return unit?String(last)+' '+unit:String(last)}
function applyOne(input){const m=metaFromInput(input);const last=prevValue(m);if(last){input.placeholder=hintText(m,last);input.classList.add('kggHasLastHint')}else{if(input.classList.contains('kggHasLastHint'))input.placeholder='';input.classList.remove('kggHasLastHint')}}
function apply(){css();document.querySelectorAll('input.num').forEach(applyOne)}
function patch(){if(window.__kggLastValueHintsPatchedV2)return;window.__kggLastValueHintsPatchedV2=1;if(typeof openPad==='function'){const old=openPad;window.openPad=function(input,meta){if(input&&meta)input.__kggLastMeta=meta;const r=old.apply(this,arguments);applyOne(input);return r}}if(typeof put==='function'){const oldPut=put;window.put=function(){const r=oldPut.apply(this,arguments);setTimeout(apply,40);return r}}}
function init(){patch();apply();const list=$('list');if(list&&'MutationObserver'in window)new MutationObserver(()=>setTimeout(()=>{patch();apply()},40)).observe(list,{childList:true,subtree:true});setTimeout(()=>{patch();apply()},300);setTimeout(apply,1200);setTimeout(apply,2500)}
document.readyState==='loading'?document.addEventListener('DOMContentLoaded',init):init();
})();