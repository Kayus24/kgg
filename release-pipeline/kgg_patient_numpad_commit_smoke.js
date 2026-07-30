#!/usr/bin/env node
'use strict';

const fs=require('fs');
const path=require('path');
const vm=require('vm');

const ROOT=path.resolve(__dirname,'..');
const source=fs.readFileSync(path.join(ROOT,'patient-numpad-visibility-fix.js'),'utf8');
function assert(condition,message){if(!condition)throw new Error(message)}

function classList(initial=[]){
  const values=new Set(initial);
  return {add(...xs){xs.forEach(x=>values.add(x))},remove(...xs){xs.forEach(x=>values.delete(x))},contains(x){return values.has(x)},toggle(x,on){if(on===undefined)on=!values.has(x);on?values.add(x):values.delete(x);return on}};
}
function input(name){return {name,value:'',placeholder:'kg',classList:classList(),matches(sel){return sel==='input.num'},closest(){return null},getBoundingClientRect(){return {left:20,top:100,right:140,bottom:150,width:120,height:50}}}}

const timers=[];
const listeners={};
const padBox={getBoundingClientRect(){return {left:0,top:600,right:400,bottom:800,width:400,height:200}}};
const pad={classList:classList(['hide']),querySelector(sel){return sel==='.padBox'?padBox:null}};
const padVal={textContent:'0'};
const main={style:{}};
const body={classList:classList(),appendChild(){}};
const document={
  readyState:'complete',
  activeElement:null,
  body,
  head:{appendChild(){}},
  documentElement:{clientWidth:400},
  getElementById(id){if(id==='pad')return pad;if(id==='padVal')return padVal;return null},
  querySelector(sel){return sel==='main'?main:null},
  querySelectorAll(){return []},
  createElement(){return {id:'',style:{},classList:classList(),remove(){},querySelector(){return null}}},
  addEventListener(type,fn){(listeners[type]||(listeners[type]=[])).push(fn)}
};
function fire(type,target){for(const fn of listeners[type]||[])fn({target})}
function flush(maxDelay=Infinity){
  const ready=timers.filter(t=>t.delay<=maxDelay);
  for(const t of ready)timers.splice(timers.indexOf(t),1);
  ready.sort((a,b)=>a.delay-b.delay).forEach(t=>t.fn());
}

const commits=[];
let baseActive=null;
const outside={matches(){return false},closest(){return null}};
const context={
  console,
  document,
  MutationObserver:function(){this.observe=()=>{};this.disconnect=()=>{}},
  getComputedStyle(){return {fontSize:'16px',borderRadius:'12px'}},
  requestAnimationFrame(fn){fn()},
  addEventListener(){},
  setTimeout(fn,delay=0){timers.push({fn,delay});return timers.length},
  clearTimeout(){},
  window:{
    __KGG_TEST__:true,
    innerWidth:400,
    innerHeight:800,
    scrollBy(){},
    openPad(el){baseActive=el;document.activeElement=el;pad.classList.remove('hide');padVal.textContent=el.value||'0'},
    closePad(ok){if(ok&&baseActive){baseActive.value=padVal.textContent||'0';commits.push({name:baseActive.name,value:baseActive.value})}pad.classList.add('hide');baseActive=null},
    padUseLast(){padVal.textContent='9'}
  }
};
context.window.window=context.window;
context.window.document=document;
context.globalThis=context;
vm.createContext(context);
vm.runInContext(source,context,{filename:'patient-numpad-visibility-fix.js'});

const a=input('A'),b=input('B'),c=input('C'),d=input('D'),e=input('E'),f=input('F');
context.window.openPad(a,{key:'a'});padVal.textContent='12';a.value='12';
fire('pointerdown',b);
assert(commits.length===1&&commits[0].name==='A'&&commits[0].value==='12','field A was not committed before switching to B');
context.window.openPad(b,{key:'b'});padVal.textContent='20';b.value='20';
flush(120);
assert(context.window.__kggNumpadCommitTest.getEditingInput()===b,'old cleanup cleared the newly opened field B');
fire('pointerdown',c);
assert(commits.length===2&&commits[1].name==='B'&&commits[1].value==='20','field B was not committed before switching to C');
context.window.openPad(c,{key:'a'});padVal.textContent='30';c.value='30';
fire('pointerdown',outside);
assert(commits.length===3&&commits[2].name==='C'&&commits[2].value==='30','outside tap did not commit field C');
flush(120);
assert(context.window.__kggNumpadCommitTest.getEditingInput()===null,'closed editor was not cleaned after outside commit');

context.window.openPad(d,{key:'a'});padVal.textContent='44';d.value='44';
fire('pointerdown',d);
assert(commits.length===3,'same-field pointerdown caused an unnecessary commit');
context.window.closePad(false);
flush(120);
assert(commits.length===3,'cancel path committed field D');

context.window.openPad(e,{key:'a'});padVal.textContent='55';e.value='55';
context.window.openPad(f,{key:'b'});
assert(commits.length===4&&commits[3].name==='E'&&commits[3].value==='55','programmatic field switch fallback did not commit field E');

console.log('Patient numpad commit-on-leave smoke: OK');
