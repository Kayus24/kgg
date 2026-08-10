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
  readyState:'complete',activeElement:null,body,head:{appendChild(){}},documentElement:{clientWidth:400},
  getElementById(id){if(id==='pad')return pad;if(id==='padVal')return padVal;return null},
  querySelector(sel){return sel==='main'?main:null},querySelectorAll(){return []},
  createElement(){return {id:'',style:{},classList:classList(),remove(){},querySelector(){return null}}},
  addEventListener(type,fn){(listeners[type]||(listeners[type]=[])).push(fn)}
};
function fire(type,target){for(const fn of listeners[type]||[])fn({target})}
function flush(maxDelay=Infinity){const ready=timers.filter(t=>t.delay<=maxDelay);for(const t of ready)timers.splice(timers.indexOf(t),1);ready.sort((a,b)=>a.delay-b.delay).forEach(t=>t.fn())}

const commits=[];
const closeCalls=[];
let baseActive=null;
const outside={matches(){return false},closest(){return null}};
const context={console,document,MutationObserver:function(){this.observe=()=>{};this.disconnect=()=>{}},getComputedStyle(){return {fontSize:'16px',borderRadius:'12px'}},requestAnimationFrame(fn){fn()},addEventListener(){},setTimeout(fn,delay=0){timers.push({fn,delay});return timers.length},clearTimeout(){},window:{
  __KGG_TEST__:true,innerWidth:400,innerHeight:800,scrollBy(){},
  put(ei,s,side,key,value){commits.push({ei,s,side,key,value})},
  openPad(el,meta){baseActive={el,meta};document.activeElement=el;pad.classList.remove('hide');padVal.textContent=el.value||'0'},
  closePad(ok){closeCalls.push(ok);if(ok&&baseActive){const value=padVal.textContent||'0';baseActive.el.value=value;const m=baseActive.meta;context.window.put(m.ei,m.s,m.side,m.key,value)}pad.classList.add('hide');baseActive=null},
  padUseLast(){padVal.textContent='9'}
}};
context.window.window=context.window;context.window.document=document;context.globalThis=context;
vm.createContext(context);vm.runInContext(source,context,{filename:'patient-numpad-visibility-fix.js'});

const a=input('A'),b=input('B'),c=input('C'),d=input('D'),e=input('E'),f=input('F');
const ma={ei:0,s:1,side:'B',key:'a'},mb={ei:0,s:1,side:'B',key:'b'},mc={ei:0,s:2,side:'B',key:'a'};
context.window.openPad(a,ma);padVal.textContent='12';
fire('pointerdown',b);
assert(commits.length===0,'pointerdown committed before the target field opened');
context.window.openPad(b,mb);
assert(commits.length===1&&commits[0].value==='12'&&a.value==='12','field A was not saved during the in-place switch');
assert(closeCalls.length===0,'field switch called closePad and caused a visible blink');
assert(!pad.classList.contains('hide'),'numpad closed during A to B switch');
assert(context.window.__kggNumpadCommitTest.getEditingInput()===b,'field B did not become the active editor');

padVal.textContent='20';
context.window.openPad(c,mc);
assert(commits.length===2&&commits[1].value==='20'&&b.value==='20','field B was not saved during the next in-place switch');
assert(closeCalls.length===0&&!pad.classList.contains('hide'),'numpad blinked during B to C switch');
flush(120);
assert(context.window.__kggNumpadCommitTest.getEditingInput()===c,'delayed cleanup cleared the open field C');

padVal.textContent='30';
fire('pointerdown',outside);
assert(closeCalls.length===1&&closeCalls[0]===true,'outside tap did not close with save');
assert(commits.length===3&&commits[2].value==='30','outside tap did not save field C');
flush(120);
assert(context.window.__kggNumpadCommitTest.getEditingInput()===null,'closed editor was not cleaned after outside save');

context.window.openPad(d,ma);padVal.textContent='44';
fire('pointerdown',d);
assert(commits.length===3,'same-field pointerdown caused an unnecessary save');
context.window.closePad(false);flush(120);
assert(commits.length===3,'cancel path saved field D');

context.window.openPad(e,ma);padVal.textContent='55';
context.window.openPad(f,mb);
assert(commits.length===4&&commits[3].value==='55','programmatic field switch did not save field E');
assert(closeCalls.length===2&&closeCalls[1]===false,'programmatic switch unexpectedly closed the numpad');
assert(!pad.classList.contains('hide'),'numpad was not left open after programmatic switch');

console.log('Patient numpad stay-open switch smoke: OK');
