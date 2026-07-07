# KGG Source Chunk 053

- Source: `kgg-update/index.html`
- Lines: 22261-22680

```html
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
    }
    if(isTime){
      for(let s=0;s<3;s++){
        const idx=nums.length>=6?s*2+1:s;
        const metric=scanFormatNumber(nums[idx]);
        const pain=scanFormatPain(pains[s]||nums[(nums.length>=9?s*3+2:-1)]);
        if(metric)lines.push('Satz '+(s+1)+': '+metric+' '+metricUnit+(pain?' · Schmerz: '+pain+'/10':''));
      }
      return lines;
    }
    if(nums.length>=9){
      for(let s=0;s<3;s++){
        const base=s*3;
        const load=scanFormatNumber(nums[base]), metric=scanFormatNumber(nums[base+1]), pain=scanFormatPain(nums[base+2]||pains[s]);
        if(load||metric)lines.push('Satz '+(s+1)+': '+(metric||'')+' '+metricUnit+(load?' @ '+load+' '+loadUnit:'')+(pain?' · Schmerz: '+pain+'/10':''));
      }
      return lines;
    }
    if(nums.length>=6){
      for(let s=0;s<3;s++){
        const load=scanFormatNumber(nums[s*2]), metric=scanFormatNumber(nums[s*2+1]), pain=scanFormatPain(pains[s]);
        if(load||metric)lines.push('Satz '+(s+1)+': '+(metric||'')+' '+metricUnit+(load?' @ '+load+' '+loadUnit:'')+(pain?' · Schmerz: '+pain+'/10':''));
      }
      return lines;
    }
    const load=scanNonEmptyValue(source.startLoad||source.load||source.weight||source.lastLoad||'');
    const metric=scanNonEmptyValue(source.startMetric||source.metric||source.reps||source.time||source.lastMetric||'');
    const pain=scanFormatPain((pains||[])[0]||source.pain||source.schmerz);
    if(metric||load)lines.push('Satz 1: '+(metric?scanFormatNumber(metric)+' '+metricUnit:'')+(load?' @ '+scanFormatNumber(load)+' '+loadUnit:'')+(pain?' · Schmerz: '+pain+'/10':''));
    else if(pain)lines.push('Schmerz: '+pain+'/10');
    return lines;
  }
  function scanExerciseToDocText(item){
    if(typeof item==='string')return stripScanExerciseName(item);
    let source=item;
    if(Array.isArray(item)){
      try{source=expandKggH2Exercise(item);}catch(err){source={name:item[0]||''};}
    }
    const name=scanExerciseName(source);
    if(!name)return '';
    const lines=scanStructuredSetLinesFromValues(item,source);
    return [name].concat(lines).filter(Boolean).join('\n');
  }
  function formatScanExerciseLine(item){
    return scanExerciseToDocText(item);
  }
  function scanResultToPlanText(result){
    if(!result)return '';
    if(typeof result==='string')return cleanGeminiScanText(result);
    if(result.planText)return String(result.planText||'').trim();
    if(result.text)return cleanGeminiScanText(result.text);
    if(result.rawText)return cleanGeminiScanText(result.rawText);
    const exercises=scanPayloadExercises(result);
    if(exercises.length)return exercises.map(scanExerciseToDocText).filter(Boolean).join('\n\n');
    return '';
  }
  function scanResultToApplyText(result){
    if(!result)return '';
    if(result.applyText)return String(result.applyText||'').trim();
    const exercises=scanPayloadExercises(result);
    if(exercises.length)return scanApplyTextFromExercises(exercises);
    const text=scanResultToPlanText(result);
    return String(text||'').split(/\n+/).map(line=>line.trim()).filter(line=>line&&!/^Satz\s+\d+\s*:/i.test(line)&&!/^\s*(Li|Re|Schmerz)\s*:/i.test(line)).join(', ');
  }
  function scanResultToCopyText(job){
    const short=job&&job.short?String(job.short).trim():'';
    const result=job&&job.result||{};
    const quality=result.quality||{};
    const text=result.copyText||result.planText||scanResultToPlanText(result)||result.rawText||'';
    const lines=[];
    if(short)lines.push(short);
    if(result.type)lines.push('Typ: '+result.type);
    if(quality.warnings&&quality.warnings.length)lines.push('Prüfen: '+quality.warnings.join(', '));
    if(text)lines.push('',text);
    return lines.join('\n').trim();
  }
  function scanPaperQuality(text,result){
    const raw=String(text||'').trim();
    const parts=raw.split(/[,\n]+/).map(part=>part.trim()).filter(Boolean);
    const exerciseLike=parts.filter(part=>/[a-zäöüß]{4,}/i.test(part)&&!/^unbekannte\s+übung/i.test(part));
    const numbers=(raw.match(/\d+(?:[,.]\d+)?/g)||[]).length;
    const unknown=(raw.match(/unbekannte\s+übung|\?{2,}/gi)||[]).length;
    const days=(raw.match(/\bT(?:ag)?\s*\d+\b/gi)||[]).map(x=>Number((x.match(/\d+/)||[0])[0])).filter(Boolean);
    const warnings=[];
    if(exerciseLike.length<1)warnings.push('wenige Übungsnamen erkannt');
    if(unknown>1)warnings.push('zu viele unsichere Treffer');
    if(numbers>90)warnings.push('zu viele Zahlen statt Übungsstruktur');
    if(days.length&&Math.max(...days)>8)warnings.push('möglicherweise erfundene Tage');
    if(/(?:unbekannte\s+übung\s*,?\s*){2,}/i.test(raw))warnings.push('Unbekannte-Übung-Kaskade');
    return {ok:!warnings.length,exerciseCount:exerciseLike.length,numberCount:numbers,warnings,rawResult:!!result};
  }
  function createScanReadingCanvas(src){
    const canvas=scanCloneCanvas(src);
    const ctx=canvas.getContext('2d',{willReadFrequently:true});
    ctx.save();
    ctx.filter='contrast(1.12) brightness(1.04) saturate(.96)';
    ctx.drawImage(src,0,0);
    ctx.restore();
    return canvas;
  }
  function fillRedactionRects(ctx,rects){
    ctx.save();
    ctx.fillStyle='#fff';
    rects.forEach(r=>ctx.fillRect(Math.max(0,r[0]),Math.max(0,r[1]),Math.max(0,r[2]),Math.max(0,r[3])));
    ctx.restore();
  }
  function redactScanCanvasForExternalOcr(src){
    const canvas=scanCloneCanvas(src);
    const ctx=canvas.getContext('2d',{willReadFrequently:true});
    const w=canvas.width,h=canvas.height;
    const top=Math.round(h*.145);
    const bottom=Math.round(h*.065);
    const side=Math.round(w*.075);
    const wideSide=Math.round(w*.115);
    const rects=[[0,0,w,top],[0,h-bottom,w,bottom],[0,0,side,h],[w-side,0,side,h]];
    if(w>h)rects.push([w-wideSide,0,wideSide,h],[0,0,Math.round(w*.095),h]);
    fillRedactionRects(ctx,rects);
    canvas.dataset.redacted='true';
    canvas.dataset.redaction='white-randmask-v295';
    return canvas;
  }
  function canvasToGeminiInlineData(canvas){
    const dataUrl=canvas.toDataURL('image/jpeg',.72);
    return {mime_type:'image/jpeg',data:dataUrl.split(',')[1]||''};
  }
  function cleanGeminiScanText(text){
    let out=String(text||'').replace(/```(?:json|[a-z]+)?/gi,'').replace(/```/g,'').trim();
    if(!out)return '';
    const json=parseLooseJson(out);
    if(json.ok){
      const asText=scanResultToPlanText(json.json);
      if(asText)return asText;
    }
    out=out.split(/\n+/).map(line=>line.replace(/^\s*(?:[-*]|\d+[.)])\s*/,'').trim()).filter(Boolean).join(', ');
    out=out.replace(/\b(?:EX|ÜB|UE)\s*\d+\s*[:.)|\-–—]*\s*/gi,'');
    out=out.replace(/\s*;\s*/g,', ').replace(/\s*,\s*/g,', ').replace(/(?:,\s*){2,}/g,', ').replace(/\s+/g,' ').trim();
    if(/^keine auslesbaren/i.test(out))return '';
    return out;
  }
  function geminiScanResponseText(json){
    const candidates=Array.isArray(json&&json.candidates)?json.candidates:[];
    return candidates.map(candidate=>{
      const parts=candidate&&candidate.content&&Array.isArray(candidate.content.parts)?candidate.content.parts:[];
      return parts.map(part=>part&&part.text||'').join('\n');
    }).filter(Boolean).join('\n').trim();
  }
  function geminiScanPrompt(){
    return [
      'Du liest einen deutschen KGG/Physio-Papierplan als Foto.',
      'QR-Codes werden lokal gelesen; du bist nur Papierplan-Fallback.',
      'Ignoriere Patientendaten, Kopfzeilen, Randnotizen und Datenschutzmasken.',
      'Entferne EX1/EX2/UE1-Praefixe aus Übungsnamen.',
      'Gib nur übungsbezogene Inhalte aus: Übungsname, Seite links/rechts falls erkennbar, Last, Wdh oder Zeit.',
      'Keine Tage erfinden. Keine leeren Tabellenzeilen als Übungen ausgeben.',
      'Bei unsicheren Werten lieber null/unsicher statt raten.',
      'Bevorzugtes JSON: {"exercises":[{"name":"...","side":"BI oder LR","load":"","reps":"","time":"","uncertain":false}],"warnings":[]}',
      'Wenn JSON unsicher ist, gib zusätzlich klaren Text mit einer Übung pro Zeile aus.'
    ].join('\n');
  }
  function localGeminiKeys(){
    loadAdminSecrets();
    if(window.KGGAdmin&&typeof window.KGGAdmin.getGeminiKeysForLocalUse==='function')return window.KGGAdmin.getGeminiKeysForLocalUse().map(cleanSecret).filter(Boolean);
    return (adminSecrets.geminiKeys||[]).map(cleanSecret).filter(Boolean);
  }
  function currentLocalGeminiKey(){return localGeminiKeys()[0]||'';}

  /* ========================================================================
     KGG v308 QR STRUCTURED OUTPUT + CURRENT-LAYOUT CONTACT-SHEET SCAN START
     Integrationskandidat aus v306: TPL-BASIS-A-CLASSIC-L6-v2, EX1-EX6,
     T1-Zeilen-Crops -> Contact-Sheet -> ein Gemini-Call -> lokale Zuordnung.
     Später entfernbar/isolierbar, aber KEINE zweite KGGScan-Engine.
     ======================================================================== */
  const KGG_CURRENT_LAYOUT_ID='TPL-BASIS-A-CLASSIC-L6-v2';
  const KGG_CURRENT_LAYOUT_BOXES=[
    {ex:1,name:'Adduktion Maschine',x:.027,y:.134,w:.470,h:.225,measure:'Wdh'},
    {ex:2,name:'Ein-Beinpresse',x:.503,y:.134,w:.470,h:.225,measure:'Wdh'},
    {ex:3,name:'Ein-Beinpresse',x:.027,y:.385,w:.470,h:.225,measure:'Wdh'},
    {ex:4,name:'Ein-Beinpresse',x:.503,y:.385,w:.470,h:.225,measure:'Wdh'},
    {ex:5,name:'Copenhagen Plank',x:.027,y:.637,w:.470,h:.318,measure:'Sek.'},
    {ex:6,name:'Beinpresse',x:.503,y:.637,w:.470,h:.318,measure:'Wdh'}
  ];
  function kggClampRect(rect,w,h){
    const x=Math.max(0,Math.min(w-1,Math.round(rect.x)));
    const y=Math.max(0,Math.min(h-1,Math.round(rect.y)));
    const rw=Math.max(1,Math.min(w-x,Math.round(rect.w)));
    const rh=Math.max(1,Math.min(h-y,Math.round(rect.h)));
    return {x,y,w:rw,h:rh};
  }
  function kggCropCanvas(src,rect){
    const r=kggClampRect(rect,src.width,src.height);
```
