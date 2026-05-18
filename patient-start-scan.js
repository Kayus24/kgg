(()=>{
  const LANG_KEY='kggPatientLang';
  const $=id=>document.getElementById(id);
  const lang=()=>localStorage.getItem(LANG_KEY)==='en'?'en':'de';
  const tr=(de,en)=>lang()==='en'?en:de;
  let filling=false;

  function ready(){
    try{return p&&Array.isArray(p.ex)&&typeof v==='object'&&typeof k==='function'}catch(e){return false}
  }

  function autoFillStartValues(){
    if(filling||!ready())return;
    let day=1;
    try{day=Number(d)||1}catch(e){}
    if(day!==1)return;
    let changed=false;
    const setIfEmpty=(ei,s,side,key,value)=>{
      value=String(value||'').trim();
      if(!value)return;
      const kk=k(ei,s,side,key,1);
      if(!String(v[kk]||'').trim()){
        v[kk]=value;
        changed=true;
      }
    };
    try{
      p.ex.forEach((ex,ei)=>{
        const load=String(ex.sl||'').trim();
        const reps=String(ex.sm||'').trim();
        if(!load&&!reps)return;
        const sets=Number(ex.sets)||3;
        const sides=ex.side==='LR'?['L','R']:['B'];
        for(let s=1;s<=sets;s++){
          sides.forEach(side=>{
            setIfEmpty(ei,s,side,'a',load);
            setIfEmpty(ei,s,side,'b',reps);
          });
        }
      });
    }catch(e){}
    if(changed){
      filling=true;
      try{save()}catch(e){}
      try{setStatus(tr('Startwerte übernommen.','Start values loaded.'),'ok')}catch(e){}
      try{render()}catch(e){}
      filling=false;
    }
  }

  function handlePlanText(raw){
    const txt=String(raw||'');
    const m=txt.match(/KGGH2:[A-Za-z0-9_-]+/);
    if(!m){alert(tr('Kein Plan-QR erkannt.','No plan QR detected.'));return;}
    try{safeSave()}catch(e){}
    location.href=location.origin+location.pathname+'#'+m[0];
    setTimeout(()=>location.reload(),80);
  }

  function ensureScanInput(){
    let input=$('kggPlanScanInput');
    if(input)return input;
    input=document.createElement('input');
    input.id='kggPlanScanInput';
    input.type='file';
    input.accept='image/*';
    input.setAttribute('capture','environment');
    input.style.display='none';
    input.addEventListener('change',scanFile);
    document.body.appendChild(input);
    return input;
  }

  function promptFallback(){
    const raw=prompt(tr('Kamera-Scan nicht verfügbar. Plan-Link oder QR-Text einfügen:','Camera scan not available. Paste plan link or QR text:'));
    if(raw)handlePlanText(raw);
  }

  async function scanFile(ev){
    const input=ev.target;
    const file=input.files&&input.files[0];
    setTimeout(()=>{try{input.value=''}catch(e){}},100);
    if(!file)return;
    if(!('BarcodeDetector' in window)){
      promptFallback();
      return;
    }
    try{
      const bitmap=await createImageBitmap(file);
      const detector=new BarcodeDetector({formats:['qr_code']});
      const codes=await detector.detect(bitmap);
      const raw=codes&&codes[0]&&codes[0].rawValue;
      if(raw){
        handlePlanText(raw);
      }else{
        alert(tr('Kein QR erkannt. Bitte näher und scharf fotografieren.','No QR detected. Please take a closer, sharp photo.'));
      }
    }catch(e){
      promptFallback();
    }
  }

  function openCameraScan(){
    const input=ensureScanInput();
    input.click();
  }

  function ensureScanButton(){
    const row=$('installSmall');
    if(!row)return;
    row.classList.remove('hide');
    let btn=$('kggPlanScanBtn');
    if(!btn){
      btn=document.createElement('button');
      btn.id='kggPlanScanBtn';
      btn.type='button';
      btn.style.minHeight='38px';
      btn.style.borderRadius='999px';
      btn.style.border='1px solid #bfdbfe';
      btn.style.background='#eff6ff';
      btn.style.color='#111827';
      btn.style.fontWeight='950';
      btn.style.padding='6px 10px';
      btn.onclick=(e)=>{
        e.preventDefault();
        e.stopPropagation();
        openCameraScan();
      };
      row.insertBefore(btn,row.children[1]||null);
    }
    btn.textContent=tr('QR-Scan','QR scan');
    ensureScanInput();
  }

  function patchRender(){
    if(window.__kggStartScanPatch)return;
    window.__kggStartScanPatch=true;
    if(typeof render==='function'){
      const old=render;
      window.render=function(){
        const r=old.apply(this,arguments);
        setTimeout(autoFillStartValues,0);
        setTimeout(ensureScanButton,0);
        return r;
      };
    }
  }

  function init(){
    patchRender();
    ensureScanButton();
    autoFillStartValues();
    setTimeout(autoFillStartValues,300);
    setTimeout(autoFillStartValues,1000);
    setTimeout(ensureScanButton,300);
  }

  document.readyState==='loading'?document.addEventListener('DOMContentLoaded',init):init();
})();
