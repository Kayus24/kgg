# KGG Source Chunk 053

- Source: `kgg-update/src` modular source
- Lines: 22261-22680

```html
    ctx.fillStyle='#fff';
    ctx.fillRect(0,0,canvas.width,canvas.height);
    ctx.save();
    if(rot===90){ctx.translate(canvas.width,0);ctx.rotate(Math.PI/2);}
    else if(rot===180){ctx.translate(canvas.width,canvas.height);ctx.rotate(Math.PI);}
    else if(rot===270){ctx.translate(0,canvas.height);ctx.rotate(-Math.PI/2);}
    ctx.drawImage(src,0,0);
    ctx.restore();
    return canvas;
  }
  function scanScaleCanvas(src,minSide,maxSide){
    const shortest=Math.max(1,Math.min(src.width,src.height));
    const longest=Math.max(1,Math.max(src.width,src.height));
    const minTarget=Math.max(120,Number(minSide)||0);
    const maxTarget=Math.max(minTarget,Number(maxSide)||2600);
    let scale=1;
    if(minTarget&&shortest<minTarget)scale=minTarget/shortest;
    if(longest*scale>maxTarget)scale=maxTarget/longest;
    if(Math.abs(scale-1)<0.03)return src;
    const canvas=document.createElement('canvas');
    canvas.width=Math.max(1,Math.round(src.width*scale));
    canvas.height=Math.max(1,Math.round(src.height*scale));
    const ctx=canvas.getContext('2d',{willReadFrequently:true});
    ctx.fillStyle='#fff';
    ctx.fillRect(0,0,canvas.width,canvas.height);
    ctx.imageSmoothingEnabled=scale<1;
    ctx.imageSmoothingQuality='high';
    ctx.drawImage(src,0,0,canvas.width,canvas.height);
    return canvas;
  }
  function scanFilteredCanvas(src,mode){
    if(mode==='normal')return src;
    const canvas=scanCloneCanvas(src);
    const ctx=canvas.getContext('2d',{willReadFrequently:true});
    if(mode==='contrast'){
      ctx.save();
      ctx.filter='contrast(2.05) brightness(1.12) saturate(0)';
      ctx.drawImage(src,0,0);
      ctx.restore();
      return canvas;
    }
    if(mode==='softContrast'){
      ctx.save();
      ctx.filter='contrast(1.45) brightness(1.05) saturate(0)';
      ctx.drawImage(src,0,0);
      ctx.restore();
      return canvas;
    }
    if(mode==='threshold'||mode==='thresholdLow'||mode==='thresholdHigh'||mode==='invert'){
      const img=ctx.getImageData(0,0,canvas.width,canvas.height);
      const d=img.data;
      const threshold=mode==='thresholdLow'?118:(mode==='thresholdHigh'?178:148);
      for(let i=0;i<d.length;i+=4){
        let g=(d[i]*.299+d[i+1]*.587+d[i+2]*.114)>threshold?255:0;
        if(mode==='invert')g=255-g;
        d[i]=d[i+1]=d[i+2]=g;
      }
      ctx.putImageData(img,0,0);
      return canvas;
    }
    return canvas;
  }
  /* kgg-mini-patch-v400-10-qr-gallery-bitmap-debug
     Galerie-/Fotodatenbank-QR-Fix:
     Einige Android WebViews erkennen QR-Codes per BarcodeDetector auf Kamera-Bildern,
     aber nicht zuverlässig auf Canvas-Crops aus Galerie-Dateien. Deshalb wird jeder
     Canvas-Versuch zusätzlich als PNG-Blob -> ImageBitmap dekodiert und dann erneut
     an BarcodeDetector gegeben. Außerdem bleiben Warnungen in der Scan-Vorschau sichtbar.
  */
  function scanCanvasToBlob(canvas,type,quality){
    return new Promise(resolve=>{
      try{
        canvas.toBlob(blob=>resolve(blob),type||'image/png',quality||.92);
      }catch(err){resolve(null);}
    });
  }
  async function scanDetectQrViaBitmapFromCanvas(canvas,detector){
    if(!detector||!window.createImageBitmap||!canvas||!canvas.toBlob)return '';
    let blob=null,bitmap=null;
    try{
      blob=await scanCanvasToBlob(canvas,'image/png',.92);
      if(!blob)return '';
      bitmap=await createImageBitmap(blob);
      const hits=await detector.detect(bitmap).catch(()=>[]);
      if(hits&&hits.length){
        return hits[0].rawValue||hits[0].rawData||'';
      }
    }catch(err){
      return '';
    }finally{
      if(bitmap){try{bitmap.close();}catch(closeErr){}}
    }
    return '';
  }
  async function detectQrOnCanvas(canvas,detector){
    if(detector){
      try{
        const hits=await detector.detect(canvas).catch(()=>[]);
        if(hits&&hits.length){
          const raw=hits[0].rawValue||hits[0].rawData||'';
          if(raw)return raw;
        }
      }catch(err){}
      const bitmapRaw=await scanDetectQrViaBitmapFromCanvas(canvas,detector);
      if(bitmapRaw)return bitmapRaw;
    }
    if(window.jsQR){
      try{
        const ctx=canvas.getContext('2d',{willReadFrequently:true});
        const img=ctx.getImageData(0,0,canvas.width,canvas.height);
        const code=window.jsQR(img.data,canvas.width,canvas.height,{inversionAttempts:'attemptBoth'});
        if(code&&code.data)return code.data;
      }catch(err){}
    }
    return '';
  }
  async function scanDetectQrDirectFromFile(file,detector){
    if(!detector||!window.createImageBitmap)return '';
    let bitmap=null;
    try{
      bitmap=await createImageBitmap(file,{imageOrientation:'from-image'});
      const hits=await detector.detect(bitmap).catch(()=>[]);
      if(hits&&hits.length)return hits[0].rawValue||hits[0].rawData||'';
    }catch(err){
      console.warn('QR-Dateibild: Direkt-BarcodeDetector fehlgeschlagen.',err);
    }finally{
      if(bitmap){try{bitmap.close();}catch(closeErr){}}
    }
    return '';
  }
  async function scanQrFromImageFile(file){
    const fileName=String(file&&file.name||'Bild');
    const fileType=String(file&&file.type||'unbekannter Typ');
    const fileSize=Number(file&&file.size||0);
    const heicHint=/heic|heif/i.test(fileName+' '+fileType);
    let detector=null;
    if('BarcodeDetector' in window){
      try{detector=new BarcodeDetector({formats:['qr_code']});}catch(err){detector=null;}
    }
    if(!detector&&!window.jsQR){
      return {
        raw:'',
        attempts:0,
        reason:'QR-Erkennung ist in diesem WebView nicht verfügbar. BarcodeDetector/jsQR fehlt.',
        debug:{fileName,fileType,fileSize,barcodeDetector:false,jsQR:false}
      };
    }

    const direct=await scanDetectQrDirectFromFile(file,detector);
    if(direct)return {raw:direct,attempts:1,hit:{source:'direct-bitmap',mode:'native'},debug:{fileName,fileType,fileSize}};

    const crops=[
      {id:'full',x:0,y:0,w:1,h:1},
      {id:'center',x:.08,y:.08,w:.84,h:.84},
      {id:'center-tight',x:.20,y:.20,w:.60,h:.60},
      {id:'wide-center',x:.03,y:.15,w:.94,h:.70},
      {id:'tall-center',x:.15,y:.03,w:.70,h:.94},
      {id:'top-left',x:0,y:0,w:.62,h:.62},
      {id:'top-right',x:.38,y:0,w:.62,h:.62},
      {id:'bottom-left',x:0,y:.38,w:.62,h:.62},
      {id:'bottom-right',x:.38,y:.38,w:.62,h:.62},
      {id:'top-band',x:0,y:0,w:1,h:.48},
      {id:'bottom-band',x:0,y:.52,w:1,h:.48},
      {id:'left-band',x:0,y:0,w:.48,h:1},
      {id:'right-band',x:.52,y:0,w:.48,h:1},
      {id:'top-third-left',x:0,y:0,w:.54,h:.44},
      {id:'top-third-right',x:.46,y:0,w:.54,h:.44},
      {id:'mid-third-left',x:0,y:.28,w:.54,h:.44},
      {id:'mid-third-right',x:.46,y:.28,w:.54,h:.44},
      {id:'bottom-third-left',x:0,y:.56,w:.54,h:.44},
      {id:'bottom-third-right',x:.46,y:.56,w:.54,h:.44}
    ];
    const modes=['normal','softContrast','contrast','thresholdLow','threshold','thresholdHigh','invert'];
    const maxSides=[4096,3200,2600,1800,1200];
    const rotations=[0,90,180,270];
    const seenBases=new Set();
    let attempts=1;
    let lastReason='';
    let lastCanvas='';
    for(const maxSide of maxSides){
      let base=null;
      try{
        base=await scanImageCanvasFromFile(file,maxSide);
      }catch(err){
        lastReason=err&&err.message||String(err);
        continue;
      }
      const key=base.width+'x'+base.height;
      lastCanvas=key;
      if(seenBases.has(key))continue;
      seenBases.add(key);
      for(const rot of rotations){
        const rotated=scanRotateCanvas(base,rot);
        for(const box of crops){
          const crop=box.id==='full'?rotated:scanCropCanvas(rotated,box);
          const prepared=scanScaleCanvas(crop,860,3200);
          for(const mode of modes){
            attempts++;
            const target=scanFilteredCanvas(prepared,mode);
            const raw=await detectQrOnCanvas(target,detector);
            if(raw){
              return {
                raw,
                attempts,
                hit:{rot,crop:box.id,mode,maxSide,canvas:key,detector:!!detector,jsQR:!!window.jsQR},
                debug:{fileName,fileType,fileSize,lastCanvas:key}
              };
            }
          }
        }
      }
    }
    const support='BarcodeDetector='+(!!detector)+', jsQR='+(!!window.jsQR);
    const heicText=heicHint?' HEIC/HEIF wird von Android WebView oft nicht als Canvas-Bild dekodiert; bitte als Screenshot/PNG/JPG testen.':'';
    return {
      raw:'',
      attempts,
      reason:(lastReason?lastReason+'; ':'')+'Kein QR im hochgeladenen Bild gefunden. '+support+', Datei='+fileName+', Typ='+fileType+', Groesse='+fileSize+', Canvas='+lastCanvas+'.'+heicText,
      debug:{fileName,fileType,fileSize,attempts,lastCanvas,barcodeDetector:!!detector,jsQR:!!window.jsQR,heicHint}
    };
  }
  function safeBase64JsonDecode(value){
    const raw=String(value||'').trim();
    const body=raw.replace(/^[^:]+:/,'').replace(/-/g,'+').replace(/_/g,'/');
    const padded=body+'='.repeat((4-body.length%4)%4);
    const decoded=decodeURIComponent(escape(atob(padded)));
    return parseLooseJson(decoded).json;
  }
  function safeJsonRepair(text){
    let s=String(text||'').trim();
    s=s.replace(/```(?:json)?/gi,'').replace(/```/g,'').trim();
    const firstObj=s.indexOf('{'), firstArr=s.indexOf('[');
    let start=-1,end=-1;
    if(firstArr>=0&&(firstObj<0||firstArr<firstObj)){start=firstArr;end=s.lastIndexOf(']');}
    else {start=firstObj;end=s.lastIndexOf('}');}
    if(start>=0&&end>start)s=s.slice(start,end+1);
    s=s.replace(/,\s*([}\]])/g,'$1');
    s=s.replace(/}\s*{/g,'},{').replace(/]\s*\[/g,'],[');
    s=s.replace(/"\s*\n\s*"/g,'","');
    s=s.replace(/\n/g,' ');
    return s;
  }
  function parseLooseJson(text){
    const original=String(text||'');
    const tries=[original,safeJsonRepair(original)];
    let last=null;
    for(const candidate of tries){
      if(!candidate||!candidate.trim())continue;
      try{return {ok:true,json:JSON.parse(candidate),source:candidate,repaired:candidate!==original};}
      catch(err){last=err;}
    }
    return {ok:false,json:null,source:original,error:last};
  }
  function decodeKggQueryPayload(value){
    const encoded=decodeURIComponent(String(value||'')).trim();
    try{return safeBase64JsonDecode(encoded);}catch(err){}
    return parseLooseJson(encoded).json;
  }
  function parseScannedQrRaw(raw){
    const text=String(raw||'').trim();
    if(!text)throw new Error('QR leer.');
    let payloadText=text;
    try{
      const url=new URL(text);
      if(url.hash)payloadText=url.hash;
      const q=url.searchParams.get('kgg')||url.searchParams.get('payload')||url.searchParams.get('p');
      if(q)return {type:'query',json:decodeKggQueryPayload(q),raw:text};
    }catch(err){}
    const candidates=[payloadText,text];
    try{candidates.push(decodeURIComponent(payloadText));}catch(err){}
    try{candidates.push(decodeURIComponent(text));}catch(err){}
    const findCode=prefix=>{
      const re=new RegExp(prefix+':([A-Za-z0-9_-]+)','i');
      for(const candidate of candidates){
        const hit=String(candidate||'').match(re);
        if(hit)return hit;
      }
      return null;
    };
    const cfg2=findCode('KGGCFG2');
    if(cfg2)return {type:'KGGCFG2',json:safeBase64JsonDecode(cfg2[1]),raw:text};
    const cfg1=findCode('KGGCFG1');
    if(cfg1)return {type:'KGGCFG1',json:safeBase64JsonDecode(cfg1[1]),raw:text};
    const h2=findCode('KGGH2');
    if(h2)return {type:'KGGH2',json:safeBase64JsonDecode(h2[1]),raw:text};
    const sync2=findCode('KGGSYNC2');
    if(sync2)return {type:'KGGSYNC2',json:safeBase64JsonDecode(sync2[1]),raw:text};
    const sync1=findCode('KGGSYNC1');
    if(sync1)return {type:'KGGSYNC1',json:safeBase64JsonDecode(sync1[1]),raw:text};
    const d1=findCode('KGGD1');
    if(d1)return {type:'KGGD1',json:safeBase64JsonDecode(d1[1]),raw:text};
    for(const candidate of candidates){
      const hashKgg=String(candidate||'').match(/#kgg=([^&\s]+)/i);
      if(hashKgg)return {type:'hash-kgg',json:decodeKggQueryPayload(hashKgg[1]),raw:text};
    }
    const parsed=parseLooseJson(text);
    if(parsed.ok)return {type:'json',json:parsed.json,raw:text,repaired:parsed.repaired};
    throw new Error('QR erkannt, aber Format nicht lesbar.');
  }
  function stripScanExerciseName(name){
    return String(name||'').replace(/^\s*(?:EX|ÜB|UE)\s*\d+\s*[:.)|\-–—]*\s*/i,'').replace(/\s+/g,' ').trim();
  }
  function scanPayloadExercises(payload){
    if(!payload)return [];
    if(Array.isArray(payload))return payload;
    if(Array.isArray(payload.exercises))return payload.exercises;
    if(Array.isArray(payload.planExercises))return payload.planExercises;
    if(Array.isArray(payload.plan))return payload.plan;
    if(Array.isArray(payload.e)){
      try{return convertKggH2PayloadToPatientPayload(payload).plan||[];}catch(err){return payload.e;}
    }
    if(payload.payload)return scanPayloadExercises(payload.payload);
    if(payload.json)return scanPayloadExercises(payload.json);
    return [];
  }
  function scanNonEmptyValue(value){
    if(value==null)return '';
    if(Array.isArray(value))return value.map(scanNonEmptyValue).filter(v=>v!=='').join(',');
    const text=String(value).trim();
    if(!text||text==='null'||text==='undefined')return '';
    return text;
  }
  function scanAsNumberList(value){
    if(value==null)return [];
    if(Array.isArray(value))return value.flatMap(scanAsNumberList);
    if(typeof value==='number'&&Number.isFinite(value))return [value];
    if(typeof value==='string')return (value.match(/-?\d+(?:[,.]\d+)?/g)||[]).map(v=>Number(String(v).replace(',','.'))).filter(Number.isFinite);
    return [];
  }
  function scanIsBlankValue(value){
    const text=scanNonEmptyValue(value);
    return !text || text==='0' || text==='0.0' || text==='0,0';
  }
  function scanUnitLabel(value,fallback){return scanNonEmptyValue(value)||fallback||'';}
  function scanExerciseName(item){
    if(typeof item==='string')return stripScanExerciseName(item);
    if(Array.isArray(item)){
      try{return stripScanExerciseName(expandKggH2Exercise(item).name);}catch(err){return stripScanExerciseName(item[0]||'');}
    }
    return stripScanExerciseName(item&&((item.name||item.title||item.exercise||item.uebung||item['übung'])||''));
  }
  function scanExerciseApplyLine(item){
    const name=scanExerciseName(item);
    if(!name)return '';
    let source=item;
    if(Array.isArray(item)){try{source=expandKggH2Exercise(item);}catch(err){source={};}}
    const side=normalizeSideMode(source&&source.side||source&&source.side_mode||source&&source.laterality||source&&source.seite||'BI');
    return name+(side==='LR'?' li/re':'');
  }
  function scanApplyTextFromExercises(exercises){
    return (exercises||[]).map(scanExerciseApplyLine).filter(Boolean).join(', ');
  }
  function scanFindNumberSequence(item){
    if(!item)return [];
    const candidates=[item.values,item.numbers,item.group,item.t1,item.T1,item.row,item.rowValues,item.load,item.weight,item.startLoad,item.lastLoad,item.metric,item.reps,item.time,item.startMetric,item.lastMetric];
    for(const candidate of candidates){
      const nums=scanAsNumberList(candidate);
      if(nums.length>=3)return nums;
    }
    if(item.sets&&Array.isArray(item.sets)){
      const out=[];
      item.sets.forEach(set=>{
        if(set.right||set.left){
          const li=set.left||set.li||set.L||{};
          const re=set.right||set.re||set.R||{};
          out.push(...scanAsNumberList(li.load||li.weight||li.kg));
          out.push(...scanAsNumberList(li.reps||li.metric||li.wdh||li.time||li.sec));
          out.push(...scanAsNumberList(re.load||re.weight||re.kg));
          out.push(...scanAsNumberList(re.reps||re.metric||re.wdh||re.time||re.sec));
          const p=scanAsNumberList(set.pain||set.schmerz); if(p.length)out.push(p[0]);
        }else{
          out.push(...scanAsNumberList(set.load||set.weight||set.kg));
          out.push(...scanAsNumberList(set.reps||set.metric||set.wdh||set.time||set.sec));
          const p=scanAsNumberList(set.pain||set.schmerz); if(p.length)out.push(p[0]);
        }
      });
      if(out.length)return out;
    }
    return [];
  }
  function scanFindPainValues(item){
    if(!item)return [];
    const candidates=[item.pain,item.schmerz,item.painValues,item.schmerzwerte,item.painScale,item.painScores,item.scores];
    for(const c of candidates){const nums=scanAsNumberList(c); if(nums.length)return nums;}
    if(item.sets&&Array.isArray(item.sets))return item.sets.map(set=>scanAsNumberList(set.pain||set.schmerz)[0]).filter(Number.isFinite);
    return [];
  }
  function scanFormatNumber(value){
    if(value==null||value==='')return '';
    const n=Number(value);
    if(Number.isFinite(n))return String(Math.round(n*100)/100).replace('.',',');
    return String(value).trim();
  }
  function scanFormatPain(value){
    if(value==null||value==='')return '';
    const n=Number(value);
    if(!Number.isFinite(n))return String(value).trim();
    if(n<=0)return '';
    return String(n).replace('.',',');
  }
  function scanStructuredSetLinesFromValues(item,source){
    const side=normalizeSideMode(source.side||source.side_mode||source.laterality||source.seite||'BI');
    const loadUnit=scanUnitLabel(source.weightUnit||source.loadUnit||source.weight_unit,'kg');
    const metricUnit=scanUnitLabel(source.unit||source.metricUnit||source.metric_unit,'Wdh');
    const isTime=/zeit|sek|sec|min|time/i.test(metricUnit) || /keine/i.test(loadUnit);
    const nums=scanFindNumberSequence(source);
    const pains=scanFindPainValues(source);
    const lines=[];
    if(side==='LR' && nums.length>=12){
      for(let s=0;s<3;s++){
        const base=s*4;
        const liLoad=scanFormatNumber(nums[base]), liMetric=scanFormatNumber(nums[base+1]);
        const reLoad=scanFormatNumber(nums[base+2]), reMetric=scanFormatNumber(nums[base+3]);
        const pain=scanFormatPain(pains[s]||nums[12+s]);
        lines.push('Satz '+(s+1)+':');
        lines.push('  Li: '+liMetric+' '+metricUnit+(liLoad?' @ '+liLoad+' '+loadUnit:''));
        lines.push('  Re: '+reMetric+' '+metricUnit+(reLoad?' @ '+reLoad+' '+loadUnit:''));
        if(pain)lines.push('  Schmerz: '+pain+'/10');
      }
      return lines;
```
