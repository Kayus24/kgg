/* KGGH3 local plan codec v81. Uses local fflate 0.8.3 only. */
(function(global){
  'use strict';
  const VERSION='v81-kgg-h3-plan-format';
  const H2='KGGH2:', H3='KGGH3:';
  const LIMITS={maxCodeChars:12000,maxJsonBytes:96*1024,maxCompressedBytes:32*1024,maxExercises:40,maxFieldChars:4096};
  function utf8Encode(text){
    if(typeof TextEncoder==='function')return new TextEncoder().encode(String(text));
    const binary=unescape(encodeURIComponent(String(text))),out=new Uint8Array(binary.length);
    for(let i=0;i<binary.length;i++)out[i]=binary.charCodeAt(i);
    return out;
  }
  function utf8Decode(bytes){
    if(typeof TextDecoder==='function'){
      try{return new TextDecoder('utf-8',{fatal:true}).decode(bytes)}catch(err){throw new Error('UTF-8-Daten sind beschädigt.')}
    }
    try{let binary='';for(let i=0;i<bytes.length;i++)binary+=String.fromCharCode(bytes[i]);return decodeURIComponent(escape(binary))}
    catch(err){throw new Error('UTF-8-Daten sind beschädigt.')}
  }
  function b64Encode(bytes){
    let binary='';
    for(let i=0;i<bytes.length;i+=0x8000)binary+=String.fromCharCode.apply(null,bytes.subarray(i,i+0x8000));
    return btoa(binary).replace(/\+/g,'-').replace(/\//g,'_').replace(/=+$/,'');
  }
  function b64Decode(value){
    const body=String(value||'').trim();
    if(!body||body.length>LIMITS.maxCodeChars||body.length%4===1||!/^[A-Za-z0-9_-]+$/.test(body))throw new Error('KGGH3-QR ist beschädigt oder zu groß.');
    const text=body.replace(/-/g,'+').replace(/_/g,'/'),padded=text+'='.repeat((4-text.length%4)%4);
    let binary='';
    try{binary=atob(padded)}catch(err){throw new Error('KGGH3-Base64 ist beschädigt.')}
    const bytes=new Uint8Array(binary.length);
    for(let i=0;i<binary.length;i++)bytes[i]=binary.charCodeAt(i);
    return bytes;
  }
  function isObject(value){return !!value&&typeof value==='object'&&!Array.isArray(value)}
  function asBoundedString(value,label,required){
    if(value==null&&!required)return;
    if(typeof value!=='string'||value.length>LIMITS.maxFieldChars||(required&&!value.trim()))throw new Error(label+' ist ungültig.');
  }
  function asInteger(value,label,min,max){
    const n=typeof value==='number'?value:(typeof value==='string'&&/^\d+$/.test(value)?Number(value):NaN);
    if(!Number.isInteger(n)||n<min||n>max)throw new Error(label+' ist ungültig.');
  }
  function validatePlan(raw){
    if(!isObject(raw))throw new Error('Plan-Schema ist ungültig.');
    asBoundedString(raw.i,'Plan-ID',false);
    asBoundedString(raw.t,'Plan-Titel',false);
    if(raw.v!==undefined)asInteger(raw.v,'Plan-Version',1,10000);
    if(raw.d!==undefined)asInteger(raw.d,'Trainingstage',1,366);
    if(raw.stepDays!==undefined)asInteger(raw.stepDays,'Schritt-Tage',1,366);
    if(raw.extendDays!==undefined&&typeof raw.extendDays!=='boolean')throw new Error('Plan-Fortsetzung ist ungültig.');
    if(raw.patient!==undefined&&!isObject(raw.patient))throw new Error('Patientendaten sind ungültig.');
    if(raw.p!==undefined&&!isObject(raw.p))throw new Error('Patientendaten sind ungültig.');
    if(raw.m!==undefined&&!isObject(raw.m))throw new Error('Plan-Metadaten sind ungültig.');
    if(!Array.isArray(raw.e)||raw.e.length<1||raw.e.length>LIMITS.maxExercises)throw new Error('Übungsanzahl ist ungültig.');
    raw.e.forEach((item,index)=>{
      if(!Array.isArray(item)||item.length<5)throw new Error('Übung '+(index+1)+' ist unvollständig.');
      asBoundedString(item[0],'Übungsname '+(index+1),true);
      asInteger(item[1],'Sätze '+(index+1),1,100);
      asBoundedString(item[2],'Seite '+(index+1),true);
      asBoundedString(item[3],'Einheit '+(index+1),false);
      asBoundedString(item[4],'Messwert '+(index+1),false);
      for(let i=5;i<item.length;i++){
        const value=item[i];
        if(typeof value==='string'&&value.length>LIMITS.maxFieldChars)throw new Error('Übungsdaten '+(index+1)+' sind zu groß.');
        if(value&&typeof value==='object'){
          let json='';
          try{json=JSON.stringify(value)}catch(err){throw new Error('Übungsdaten '+(index+1)+' sind nicht lesbar.')}
          if(json.length>LIMITS.maxFieldChars*8)throw new Error('Übungsdaten '+(index+1)+' sind zu groß.');
        }
      }
    });
    let json='';
    try{json=JSON.stringify(raw)}catch(err){throw new Error('Plan ist nicht lesbar.')}
    const jsonBytes=utf8Encode(json).length;
    if(jsonBytes>LIMITS.maxJsonBytes)throw new Error('Plan ist zu groß.');
    return {raw,json,jsonBytes};
  }
  function decodeCode(code){
    const text=String(code||'').trim();
    const match=text.match(/^(KGGH[23]):([A-Za-z0-9_-]+)$/i);
    if(!match)throw new Error('Kein KGGH2/KGGH3-Plan.');
    const prefix=match[1].toUpperCase()+':',body=match[2];
    if(text.length>LIMITS.maxCodeChars)throw new Error('Plan-QR ist zu groß.');
    const compressed=prefix===H3?b64Decode(body):null;
    let bytes=compressed;
    if(prefix===H2)bytes=b64Decode(body);
    else{
      if(!global.fflate||typeof global.fflate.unzlibSync!=='function')throw new Error('Lokaler KGGH3-Decoder fehlt.');
      if(compressed.length>LIMITS.maxCompressedBytes)throw new Error('Komprimierter Plan ist zu groß.');
      try{bytes=global.fflate.unzlibSync(compressed)}catch(err){throw new Error('Komprimierter Plan ist beschädigt.')}
    }
    if(!bytes||bytes.length>LIMITS.maxJsonBytes)throw new Error('Plan ist zu groß.');
    let raw;
    try{raw=JSON.parse(utf8Decode(bytes))}catch(err){throw new Error('Plan-JSON ist beschädigt.')}
    const checked=validatePlan(raw);
    return {format:prefix.slice(0,-1),prefix,body,raw:checked.raw,jsonBytes:checked.jsonBytes,compressedBytes:compressed?compressed.length:bytes.length};
  }
  function encodeCode(raw,prefix){
    const checked=validatePlan(raw),bytes=utf8Encode(checked.json);
    if(prefix===H3){
      if(!global.fflate||typeof global.fflate.zlibSync!=='function')throw new Error('Lokaler KGGH3-Encoder fehlt.');
      const compressed=global.fflate.zlibSync(bytes);
      const body=b64Encode(compressed),code=H3+body;
      if(code.length>LIMITS.maxCodeChars)throw new Error('Plan-QR ist zu groß.');
      return code;
    }
    const code=H2+b64Encode(bytes);
    if(code.length>LIMITS.maxCodeChars)throw new Error('Plan-Link ist zu groß.');
    return code;
  }
  function candidates(input){
    const values=[],add=value=>{const text=String(value||'').trim();if(text&&!values.includes(text))values.push(text)};
    add(input);
    try{add(decodeURIComponent(String(input||'')))}catch(err){}
    try{
      const url=new URL(String(input||''),global.location&&global.location.href||undefined);
      ['plan','kgg'].forEach(key=>{const value=url.searchParams.get(key);if(value){add(value);try{add(decodeURIComponent(value))}catch(err){}}});
      if(url.hash){add(url.hash.slice(1));try{add(decodeURIComponent(url.hash.slice(1)))}catch(err){}}
    }catch(err){}
    return values;
  }
  function findPlanCode(input){
    for(const value of candidates(input)){
      const match=String(value).match(/(KGGH[23]):([A-Za-z0-9_-]+)/i);
      if(match)return match[1].toUpperCase()+':'+match[2];
    }
    return '';
  }
  function decodePlanText(input){
    const code=findPlanCode(input);
    if(!code)throw new Error('Kein KGGH2/KGGH3-Plan.');
    return decodeCode(code);
  }
  function encodeKggH2(raw){return encodeCode(raw,H2)}
  function encodeKggH3(raw){return encodeCode(raw,H3)}
  function rewriteH3StartInput(){
    const code=findPlanCode(global.location&&global.location.href||'');
    if(!/^KGGH3:/i.test(code))return false;
    try{
      const parsed=decodeCode(code),h2=encodeKggH2(parsed.raw);
      const query='?plan='+encodeURIComponent(h2);
      if(global.history&&typeof global.history.replaceState==='function')global.history.replaceState(null,'',String(global.location.pathname||'')+query);
      return true;
    }catch(err){
      global.__KGG_PLAN_FORMAT_ERROR=String(err&&err.message||err);
      return false;
    }
  }
  function guardStartInput(){
    const code=findPlanCode(global.location&&global.location.href||'');
    if(!code)return false;
    try{decodeCode(code);return true}catch(err){
      global.__KGG_PLAN_FORMAT_ERROR=String(err&&err.message||err);
      try{if(global.history&&typeof global.history.replaceState==='function')global.history.replaceState(null,'',String(global.location.pathname||''))}catch(innerErr){}
      return false;
    }
  }
  function fingerprint(raw){
    const stable=value=>Array.isArray(value)?value.map(stable):value&&typeof value==='object'?Object.keys(value).sort().reduce((out,key)=>(out[key]=stable(value[key]),out),{}):value;
    let json='';try{json=JSON.stringify(stable(raw))}catch(err){json=''};
    let hash=2166136261;for(let i=0;i<json.length;i++){hash^=json.charCodeAt(i);hash=Math.imul(hash,16777619)}
    return (hash>>>0).toString(16).padStart(8,'0');
  }
  global.KGGPlanFormat={version:VERSION,limits:LIMITS,validatePlan,decodeCode,decodePlanText,encodeKggH2,encodeKggH3,findPlanCode,rewriteH3StartInput,fingerprint};
  try{rewriteH3StartInput();guardStartInput()}catch(err){global.__KGG_PLAN_FORMAT_ERROR=String(err&&err.message||err)}
})(typeof window!=='undefined'?window:globalThis);
