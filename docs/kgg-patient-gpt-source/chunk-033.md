# KGG Patient Source Chunk 033

- Source file: `patient-set-k2-inline-editor.js`
- Characters: 1-7353
- Full source SHA-256: `42932bff4be2094454ef810256d50e864a346f6350aff70b8e4d88bf9b29aa7b`

```
/* KGG K2: inline kg/Wdh editor. Presentation only; KGG NumPad owns all saves. */
(()=>{
  'use strict';
  const VERSION='patient-k2-inline-field-v1';
  if(window.__kggPatientK2InlineEditor===VERSION)return;
  window.__kggPatientK2InlineEditor=VERSION;
  const $=id=>document.getElementById(id);
  let editor=null,activeField=null,installed=false;
  const draft=()=>window.__kggPadDraftApi;
  const controller=()=>window.__kggNumpadEditingApi;
  const padOpen=()=>!!($('pad')&&!$('pad').classList.contains('hide'));
  const compact=()=>document.body.classList.contains('kggSetViewCompact');
  const editing=()=>padOpen()&&compact()&&!!$('kggPadPair');
  function meta(input){
    if(!input)return null;
    if(input.__kggSetMeta)return input.__kggSetMeta;
    if(input.__kggLastMeta)return input.__kggLastMeta;
    const str=input.getAttribute('onclick')||'';
    const part=re=>str.match(re)?.[1]||'';
    const m={ei:Number(part(/ei:\s*(\d+)/)),s:Number(part(/s:\s*(\d+)/)),side:part(/side:\s*['"]([^'"]+)['"]/),key:part(/key:\s*['"]([^'"]+)['"]/)};
    return Number.isFinite(m.ei)&&Number.isFinite(m.s)&&m.side&&m.key?m:null;
  }
  function css(){
    if($('kggK2InlineStyle'))return;
    const style=document.createElement('style');
    style.id='kggK2InlineStyle';
    style.textContent=[
      '#pad #kggPadPair .kggPairField{position:relative!important}',
      '#pad #kggPadPair .kggPairField.kggK2Editing .kggPairValue{visibility:hidden!important}',
      '#pad #kggPadPair .kggK2Editor{position:absolute!important;z-index:5;left:10px;top:20px;',
      'width:calc(100% - 62px);height:33px;min-height:0;box-sizing:border-box;border:0;',
      'border-radius:4px;background:transparent;outline:none;padding:0;text-align:left;',
      'font:900 22px/1.1 system-ui;color:#111827;caret-color:#2563eb;',
      'font-variant-numeric:tabular-nums}',
      '#pad.kggPadLargeUi #kggPadPair .kggK2Editor{top:33px;height:48px;font-size:40px!important}',
      '#pad #kggPadPair .kggK2Clear{position:absolute;right:4px;top:50%;transform:translateY(-40%);',
      'z-index:7;min-width:42px;min-height:44px;display:grid;place-items:center;border:0;',
      'border-radius:11px;background:#e8eef7;color:#345075;font:700 25px/1 system-ui;',
      'cursor:pointer;touch-action:manipulation}',
      '#pad .kggK2Clear:focus-visible{outline:2px solid #2563eb;outline-offset:1px}',
      '#pad.kggPadLargeUi #kggPadPair .kggK2Clear{min-width:44px;min-height:46px}'
    ].join('');
    document.head.appendChild(style);
  }
  function sanitize(text){
    let value=String(text||'').replace(/[^0-9,]/g,'');
    const comma=value.indexOf(',');
    if(comma>=0)value=value.slice(0,comma+1)+value.slice(comma+1).replace(/,/g,'');
    return value.slice(0,8);
  }
  function updateDraft(value,position){
    if(!editing()||!editor||!editor.isConnected)return;
    const clean=sanitize(value);
    draft()?.setValue(clean||'0');
    controller()?.markDirty?.();
    editor.value=clean;
    editor.focus({preventScroll:true});
    const at=Math.max(0,Math.min(clean.length,position??clean.length));
    editor.setSelectionRange(at,at);
  }
  function clearField(field){
    if(!editing()||!field)return;
    if(field!==activeField){
      const source=field.__kggPairInput,m=meta(source);
      if(!source||!m)return;
      // Existing controller commits dirty source and switches without closing.
      window.openPad(source,m);
    }
    if(field!==activeField)return;
    updateDraft('',0); // Existing KGG convention persists this as 0 on OK.
  }
  function addClear(field){
    if(field.querySelector('.kggK2Clear'))return;
    const button=document.createElement('button');
    button.type='button';button.className='kggK2Clear';
    button.textContent='×';
    button.setAttribute('aria-label',(field.dataset.kggKey==='a'?'kg':'Wdh')+' vollständig löschen');
    button.addEventListener('click',event=>{
      event.preventDefault();event.stopPropagation();event.stopImmediatePropagation();
      clearField(field);
    });
    field.appendChild(button);
  }
  function show(){
    if(!editing()){hide();return}
    css();
    const pair=$('kggPadPair');
    const field=pair?.querySelector('.kggPairField.kggPairActive');
    if(!field)return;
    if(!editor){
      editor=document.createElement('input');
      editor.id='kggK2InlineEditor';editor.className='kggK2Editor';
      editor.type='text';editor.inputMode='none';editor.autocomplete='off';
      editor.spellcheck=false;
      editor.setAttribute('aria-label','Zahl im aktuellen kg- oder Wdh-Feld bearbeiten');
      editor.addEventListener('input',()=>{
        if(!editing())return;
        updateDraft(editor.value,editor.selectionStart);
      });
    }
    for(const f of pair.querySelectorAll('.kggPairField')){
      f.classList.remove('kggK2Editing');
      addClear(f);
    }
    activeField=field;field.classList.add('kggK2Editing');
    field.appendChild(editor);
    const text=String(draft()?.getValue?.()||'0');
    editor.value=text;
    editor.focus({preventScroll:true});
    editor.setSelectionRange(text.length,text.length);
  }
  function hide(){
    document.querySelectorAll('#kggPadPair .kggK2Editing').forEach(f=>f.classList.remove('kggK2Editing'));
    if(editor?.isConnected)editor.remove();
    activeField=null;
  }
  function atCursor(kind,arg){
    if(!editing()||!editor?.isConnected)return false;
    let str=editor.value,start=editor.selectionStart??str.length,end=editor.selectionEnd??start;
    let caret=start;
    if(kind==='digit'){
      if(str==='0'&&start===end&&start===1){str='';start=end=0}
      if(arg===','&&str.includes(',')&&!str.slice(start,end).includes(','))return true;
      if(str.length-(end-start)>=8)return true;
      str=str.slice(0,start)+arg+str.slice(end);caret=start+arg.length;
    }else if(kind==='back'){
      if(start===end&&start>0)start--;
      str=str.slice(0,start)+str.slice(end);caret=start;
    }else if(kind==='last'){
      str=String(arg||'0');caret=str.length;
    }
    updateDraft(str,caret);
    return true;
  }
  function install(){
    if(installed||typeof window.openPad!=='function')return;
    installed=true;
    const oldOpen=window.openPad;
    window.openPad=function(){
      const out=oldOpen.apply(this,arguments);
      show();return out;
    };
    const oldPress=window.padPress;
    if(typeof oldPress==='function')window.padPress=function(x){
      return atCursor('digit',String(x))?undefined:oldPress.apply(this,arguments);
    };
    const oldBack=window.padBack;
    if(typeof oldBack==='function')window.padBack=function(){
      return atCursor('back')?undefined:oldBack.apply(this,arguments);
    };
    const oldLast=window.padUseLast;
    if(typeof oldLast==='function')window.padUseLast=function(){
      const out=oldLast.apply(this,arguments);
      if(editing()&&editor?.isConnected){
        const value=String(draft()?.getValue?.()||'0');
        editor.value=value;editor.setSelectionRange(value.length,value.length);
      }
      return out;
    };
    const oldClose=window.closePad;
    if(typeof oldClose==='function')window.closePad=function(){
      const out=oldClose.apply(this,arguments);
      if(!padOpen())hide();
      return out;
    };
  }
  if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',install,{once:true});
  else install();
})();
```
