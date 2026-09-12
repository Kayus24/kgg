<!-- KGG PATCH START kgg-v082-therapy-cockpit -->
<!-- Therapie-Cockpit fuer begleitete Plaene -->
<style id="kgg-therapy-cockpit-style">
  /* KGG Therapie-Cockpit v1: full-screen tablet view, no persistent patient data. */
  #kggTherapyCockpitRoot{display:none;position:fixed;inset:0;z-index:2147481000;box-sizing:border-box;background:#eef2f7;color:#17233a;font:15px/1.35 system-ui,-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif;}
  body.kggTherapyCockpitOpen #kggTherapyCockpitRoot{display:block;}
  body.kggTherapyCockpitOpen .app,body.kggTherapyCockpitOpen .footerActions,body.kggTherapyCockpitOpen .tabletSideMenu,body.kggTherapyCockpitOpen .tabletSideBackdrop,body.kggTherapyCockpitOpen .tabletPackageOverlay,body.kggTherapyCockpitOpen .tabletPackageShade{visibility:hidden!important;pointer-events:none!important;}
  .kgg-tc-shell{height:100%;min-height:0;display:grid;grid-template-rows:auto minmax(0,1fr) auto;overflow:hidden;background:linear-gradient(180deg,#f8fafc 0%,#eef2f7 100%);}
  .kgg-tc-header{display:flex;align-items:center;gap:12px;min-height:64px;padding:10px max(14px,env(safe-area-inset-left,0px)) 10px max(14px,env(safe-area-inset-right,0px));padding-left:max(14px,env(safe-area-inset-left,0px));padding-right:max(14px,env(safe-area-inset-right,0px));background:#fff;border-bottom:1px solid #dbe3ee;box-shadow:0 2px 9px rgba(24,42,73,.08);}
  .kgg-tc-title{min-width:0;flex:1;display:flex;align-items:center;gap:9px;}
  .kgg-tc-title strong{font-size:clamp(18px,2.2vw,25px);letter-spacing:-.02em;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;}
  .kgg-tc-title small{color:#64748b;white-space:nowrap;}
  .kgg-tc-actions{display:flex;align-items:center;gap:8px;flex-wrap:wrap;justify-content:flex-end;}
  .kgg-tc-btn{appearance:none;border:1px solid #cbd5e1;border-radius:11px;background:#fff;color:#1e293b;min-height:44px;padding:8px 13px;font:700 14px/1 system-ui,sans-serif;cursor:pointer;touch-action:manipulation;}
  .kgg-tc-btn:hover{background:#f8fafc;}
  .kgg-tc-btn:focus-visible,.kgg-tc-field:focus-visible,.kgg-tc-card-toggle:focus-visible{outline:3px solid #8bc5ff;outline-offset:2px;}
  .kgg-tc-btn.primary{border-color:#2563eb;background:#2563eb;color:#fff;box-shadow:0 2px 6px rgba(37,99,235,.22);}
  .kgg-tc-btn.danger{border-color:#fecaca;color:#b91c1c;background:#fff7f7;}
  .kgg-tc-board{min-height:0;overflow:auto;padding:14px max(14px,env(safe-area-inset-right,0px)) 16px max(14px,env(safe-area-inset-left,0px));}
  .kgg-tc-grid{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:12px;align-items:stretch;min-height:100%;}
  .kgg-tc-grid.one{grid-template-columns:minmax(0,1fr);}
  .kgg-tc-grid.two{grid-template-columns:repeat(2,minmax(0,1fr));}
  .kgg-tc-card{min-width:0;min-height:0;display:flex;flex-direction:column;overflow:hidden;background:#fff;border:1px solid #d8e1ec;border-top:5px solid var(--tc-color,#2563eb);border-radius:15px;box-shadow:0 3px 12px rgba(23,35,58,.08);}
  .kgg-tc-card-head{display:flex;gap:8px;align-items:flex-start;padding:12px 12px 10px;border-bottom:1px solid #e5eaf1;}
  .kgg-tc-avatar{flex:0 0 38px;width:38px;height:38px;border-radius:12px;display:grid;place-items:center;color:#fff;background:var(--tc-color,#2563eb);font-weight:800;font-size:17px;}
  .kgg-tc-card-title{min-width:0;flex:1;}
  .kgg-tc-card-title strong{display:block;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;font-size:16px;}
  .kgg-tc-card-title small{display:block;margin-top:2px;color:#64748b;font-size:12px;}
  .kgg-tc-card-tools{display:flex;gap:4px;align-items:center;}
  .kgg-tc-icon-btn{width:40px;height:40px;padding:0;border:1px solid #d9e2ec;border-radius:10px;background:#fff;color:#475569;font-size:19px;cursor:pointer;touch-action:manipulation;}
  .kgg-tc-progress{height:6px;margin:0 12px 10px;background:#e7edf4;border-radius:9px;overflow:hidden;}
  .kgg-tc-progress span{display:block;height:100%;width:0;background:var(--tc-color,#2563eb);border-radius:inherit;transition:width .16s ease;}
  .kgg-tc-card-body{min-height:0;flex:1;display:flex;flex-direction:column;}
  .kgg-tc-scroll{min-height:0;overflow:auto;padding:0 10px 12px;overscroll-behavior:contain;}
  .kgg-tc-exercise{border:1px solid #e0e7ef;border-radius:12px;margin:8px 0;background:#fbfdff;overflow:visible;}
  .kgg-tc-exercise.open{border-color:#bfd5ed;background:#fff;box-shadow:0 2px 7px rgba(30,64,95,.07);}
  .kgg-tc-card-toggle{display:flex;align-items:center;gap:9px;width:100%;min-height:58px;padding:9px 10px;border:0;background:transparent;color:inherit;text-align:left;cursor:pointer;touch-action:manipulation;}
  .kgg-tc-thumb{flex:0 0 38px;width:38px;height:38px;border-radius:9px;display:grid;place-items:center;background:#dcecff;color:#2563eb;font-weight:800;overflow:hidden;}
  .kgg-tc-thumb img{width:100%;height:100%;object-fit:cover;display:block;}
  .kgg-tc-exercise-summary{min-width:0;flex:1;}
  .kgg-tc-exercise-summary strong{display:block;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;font-size:14px;}
  .kgg-tc-exercise-summary small{display:block;color:#64748b;font-size:11px;margin-top:2px;}
  .kgg-tc-chevron{color:#64748b;font-size:19px;line-height:1;}
  .kgg-tc-exercise-detail{padding:0 9px 10px;}
  .kgg-tc-values-head,.kgg-tc-set-row{display:grid;grid-template-columns:34px minmax(0,1fr) minmax(0,1fr);gap:7px;align-items:center;}
  .kgg-tc-values-head{padding:0 0 5px;color:#64748b;font-size:10px;font-weight:800;letter-spacing:.04em;text-transform:uppercase;}
  .kgg-tc-values-head span:nth-child(2){color:#94a3b8;}
  .kgg-tc-values-head span:nth-child(3){color:#2563eb;}
  .kgg-tc-set-row{padding:5px 0;border-top:1px solid #edf1f5;}
  .kgg-tc-set-no{color:#64748b;font-size:12px;font-weight:700;}
  .kgg-tc-prev{min-height:40px;display:flex;align-items:center;justify-content:center;padding:4px 5px;border-radius:8px;background:#eef1f4;color:#8a96a5;font-size:13px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;}
  .kgg-tc-field{min-width:0;min-height:42px;padding:5px 6px;border:1px solid #bfdbfe;border-radius:9px;background:#fff;color:#0f172a;font:700 14px/1.1 system-ui,sans-serif;text-align:center;cursor:pointer;touch-action:manipulation;}
  .kgg-tc-field.active{border-color:#2563eb;box-shadow:0 0 0 3px rgba(37,99,235,.16);background:#eff6ff;}
  .kgg-tc-field.empty{color:#94a3b8;font-weight:600;}
  .kgg-tc-pad{grid-column:2 / 4;margin:5px 0 3px;padding:7px;border:1px solid #bfdbfe;border-radius:11px;background:#eff6ff;}
  .kgg-tc-pad-head{display:flex;align-items:center;justify-content:space-between;gap:8px;margin-bottom:6px;color:#1d4ed8;font-size:11px;font-weight:800;}
  .kgg-tc-pad-modes{display:flex;gap:5px;}
  .kgg-tc-pad-mode{min-height:30px;padding:4px 8px;border:1px solid #bfdbfe;border-radius:7px;background:#fff;color:#1d4ed8;font:700 11px/1 system-ui,sans-serif;cursor:pointer;touch-action:manipulation;}
  .kgg-tc-pad-mode.active{background:#2563eb;color:#fff;border-color:#2563eb;}
  .kgg-tc-pad-keys{display:grid;grid-template-columns:repeat(5,minmax(0,1fr));gap:5px;}
  .kgg-tc-key{min-height:39px;padding:5px 3px;border:1px solid #cbd5e1;border-radius:8px;background:#fff;color:#17233a;font:700 15px/1 system-ui,sans-serif;cursor:pointer;touch-action:manipulation;}
  .kgg-tc-key.action{color:#1d4ed8;background:#f8fbff;}
  .kgg-tc-card-foot{display:flex;gap:7px;align-items:center;padding:9px 12px;border-top:1px solid #e5eaf1;background:#fbfdff;}
  .kgg-tc-card-foot .kgg-tc-btn{flex:1;min-width:0;}
  .kgg-tc-empty{display:grid;place-items:center;min-height:100%;padding:30px;text-align:center;color:#64748b;}
  .kgg-tc-empty-box{max-width:460px;padding:25px;border:1px dashed #b8c7d9;border-radius:16px;background:#fff;box-shadow:0 2px 8px rgba(23,35,58,.05);}
  .kgg-tc-empty-box strong{display:block;color:#334155;font-size:18px;margin-bottom:7px;}
  .kgg-tc-notice{margin:0 0 10px;padding:9px 11px;border-radius:9px;background:#fff7ed;border:1px solid #fed7aa;color:#9a3412;font-size:13px;}
  .kgg-tc-footer{display:flex;align-items:center;justify-content:space-between;gap:10px;min-height:52px;padding:7px max(14px,env(safe-area-inset-left,0px));padding-left:max(14px,env(safe-area-inset-left,0px));padding-right:max(14px,env(safe-area-inset-right,0px));background:#fff;border-top:1px solid #dbe3ee;}
  .kgg-tc-footer small{color:#64748b;}
  .kgg-tc-entry{display:none;}
  .kgg-tc-modal{position:fixed;inset:0;z-index:2;display:grid;place-items:center;padding:16px;background:rgba(15,23,42,.45);}
  .kgg-tc-modal[hidden]{display:none;}
  .kgg-tc-sheet{width:min(650px,100%);max-height:min(88dvh,720px);overflow:auto;padding:18px;border-radius:16px;background:#fff;box-shadow:0 18px 55px rgba(15,23,42,.28);}
  .kgg-tc-sheet h2{margin:0 0 5px;font-size:20px;}
  .kgg-tc-sheet p{margin:0 0 12px;color:#64748b;}
  .kgg-tc-input,.kgg-tc-output{display:block;width:100%;box-sizing:border-box;border:1px solid #cbd5e1;border-radius:10px;padding:10px 11px;background:#fff;color:#0f172a;font:14px/1.4 system-ui,sans-serif;}
  .kgg-tc-input{min-height:90px;resize:vertical;}
  .kgg-tc-output{min-height:190px;resize:vertical;white-space:pre-wrap;}
  .kgg-tc-modal-actions{display:flex;gap:8px;justify-content:flex-end;flex-wrap:wrap;margin-top:12px;}
  .kgg-tc-toast{position:fixed;left:50%;bottom:max(18px,env(safe-area-inset-bottom,0px));z-index:2147482000;transform:translate(-50%,12px);opacity:0;pointer-events:none;max-width:min(560px,calc(100vw - 28px));padding:10px 14px;border-radius:10px;background:#17233a;color:#fff;font:700 13px/1.3 system-ui,sans-serif;box-shadow:0 6px 18px rgba(15,23,42,.25);transition:opacity .16s ease,transform .16s ease;}
  .kgg-tc-toast.show{opacity:1;transform:translate(-50%,0);}
  @media (min-width:760px){
    .kgg-tc-entry.kgg-tc-entry-ready{display:inline-flex;align-items:center;justify-content:center;flex:0 0 auto;min-width:78px;min-height:40px;height:40px;padding:5px 8px;border:1px solid #2563eb;border-radius:9px;background:#eff6ff;color:#1d4ed8;font:800 11px/1 system-ui,sans-serif;cursor:pointer;touch-action:manipulation;white-space:nowrap;}
    .kgg-tc-entry.kgg-tc-entry-ready:hover{background:#dbeafe;}
  }
  @media (min-width:760px) and (max-width:920px){
    /* Keep the nested entry from intercepting the base-data toggle hit target. */
    .kgg-tc-entry.kgg-tc-entry-ready{transform:translateX(calc(100% + 10px));}
  }
  @media (max-width:759px){
    .kgg-tc-grid,.kgg-tc-grid.one,.kgg-tc-grid.two{grid-template-columns:minmax(0,1fr);}
    .kgg-tc-header{align-items:flex-start;flex-wrap:wrap;}
    .kgg-tc-title{flex-basis:100%;}
    .kgg-tc-actions{width:100%;justify-content:stretch;}
    .kgg-tc-actions .kgg-tc-btn{flex:1;}
  }
</style>
<script id="kgg-therapy-cockpit-script">
(function(){
  "use strict";
  var PATCH_ID="kgg-v082-therapy-cockpit";
  var PREFIX="KGGTC1:";
  var PUBLIC_BASE="https://kayus24.github.io/kgg/kgg-update/index.html";
  var MAX_SLOTS=3;
  var MAX_EXERCISES=40;
  var MAX_CODE_CHARS=30000;
  var BASE62="0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz";
  var COLORS=["#2563eb","#0f766e","#c2410c"];
  var REGISTRY_ENTRIES=[
    ["01","abd","Abduktion Maschine","abd,abduktion,abductor,abduktor,hüft abduktion",3,"Wdh","kg"],
    ["02","add","Adduktion Maschine","add,adduktion,adduktor,adductor,hüft adduktion",3,"Wdh","kg"],
    ["03","legpress","Beinpresse","beinpresse,bein presse,leg press,presse",3,"Wdh","kg"],
    ["04","bridge","Bridging","bridge,bridging,beckenheben,glute bridge",3,"Wdh","kg"],
    ["05","copenhagen","Copenhagen Plank","copenhagen,adduktoren plank",3,"Zeit","keine"],
    ["06","bike","Ergometer / Bike","fahrrad,bike,ergometer,warmup,cardio,rad",1,"Zeit","Stufe/Watt"],
    ["07","fire","Fire Hydrants","fire hydrant,hydrants,vierfüßler abduktion",3,"Wdh","kg"],
    ["08","hipthrust","Hip Thrust","hip thrust,glute thrust",3,"Wdh","kg"],
    ["09","legcurl","Kniebeuger Maschine","kniebeuger,leg curl,hamstring curl,beinbeuger",3,"Wdh","kg"],
    ["0A","kneeext","Kniestrecker Maschine","kniestrecker,knieextension,beinstrecker,leg extension,knei ext",3,"Wdh","kg"],
    ["0B","row","Rudern","rudern,seated row,kabelrudern,ruderzug",3,"Wdh","kg"],
    ["0C","lat","Latziehen","latziehen,latzug,lat pulldown,pulldown,lat",3,"Wdh","kg"],
    ["0D","pallof","Pallof Press","pallof,pallof press,anti rotation",3,"Wdh","kg"],
    ["0E","plank","Plank","plank,blank,unterarmstütz,stütz",3,"Zeit","keine"],
    ["0F","squat","Squat","squat,kniebeuge,kniebeugen",3,"Wdh","kg"],
    ["0G","rdl","Romanian Deadlift","romanian deadlift,rdl,dead lift",3,"Wdh","kg"],
    ["0H","deadlift","Wadenheben","wadenheben,calf raise",3,"Wdh","kg"],
    ["0J","shoulder","Schulterpresse","schulter presse,shoulder press",3,"Wdh","kg"]
  ];
  var byId=Object.create(null),byKey=Object.create(null);
  function normalize(value){return String(value==null?"":value).toLowerCase().replace(/[ä]/g,"ae").replace(/[ö]/g,"oe").replace(/[ü]/g,"ue").replace(/[ß]/g,"ss").replace(/[^a-z0-9]+/g," ").trim();}
  function key(value){return normalize(value).replace(/\s+/g,"");}
  REGISTRY_ENTRIES.forEach(function(row){
    var item={id:row[0],key:row[1],name:row[2],aliases:row[3].split(","),sets:row[4],metricUnit:row[5],loadUnit:row[6],canonical:true};
    byId[item.id]=item;
    [item.key,item.name].concat(item.aliases).forEach(function(alias){var k=key(alias);if(k&&!byKey[k])byKey[k]=item;});
  });
  function registryLookup(value){
    var text=String(value==null?"":value).trim();
    if(byId[text])return byId[text];
    return byKey[key(text)]||null;
  }
  function stableIdForName(name){
    var numeric=parseInt(fnv(key(name)),36)>>>0,index=numeric%3844;
    return BASE62.charAt(Math.floor(index/62))+BASE62.charAt(index%62);
  }
  function ensureDerived(name,metadata){
    var cleanName=String(name||"").trim(),existing=registryLookup(cleanName);if(existing)return existing;
    var id=stableIdForName(cleanName),occupied=byId[id];
    if(occupied&&key(occupied.name)!==key(cleanName))throw error("exercise_id_collision");
    registerCanonical(cleanName,id,metadata||{});
    return byId[id];
  }
  function registerCanonical(name,id,metadata){
    var cleanName=String(name||"").trim();
    var cleanId=String(id||"").trim();
    if(cleanId.length!==2||cleanId.split("").some(function(ch){return BASE62.indexOf(ch)<0;}))throw error("exercise_id_invalid");
    if(!cleanName||cleanName.length>80)throw error("exercise_name_invalid");
    var existing=byId[cleanId],existingName=existing&&key(existing.name);
    if(existing&&existingName!==key(cleanName))throw error("exercise_id_conflict");
    var found=registryLookup(cleanName);
    if(found&&found.id!==cleanId)throw error("exercise_id_conflict");
    var item=existing||{id:cleanId,key:key(cleanName),name:cleanName,aliases:[],sets:3,metricUnit:"Wdh",loadUnit:"kg",canonical:true};
    if(metadata&&metadata.sets)item.sets=Math.max(1,Math.min(8,Number(metadata.sets)||3));
    if(metadata&&metadata.metricUnit)item.metricUnit=String(metadata.metricUnit).slice(0,12);
    if(metadata&&metadata.loadUnit)item.loadUnit=String(metadata.loadUnit).slice(0,12);
    if(!existing){byId[cleanId]=item;byKey[item.key]=item;}
    return {id:item.id,name:item.name,canonical:true};
  }
  function error(code,message){var err=new Error(message||code);err.code=code;return err;}
  function utf8(value){
    var text=String(value==null?"":value);
    if(typeof TextEncoder!=="undefined")return new TextEncoder().encode(text);
    var encoded=unescape(encodeURIComponent(text)),out=new Uint8Array(encoded.length);
    for(var i=0;i<encoded.length;i++)out[i]=encoded.charCodeAt(i);
    return out;
  }
  function fromUtf8(bytes){
    if(typeof TextDecoder!=="undefined")return new TextDecoder().decode(bytes);
    var text="";for(var i=0;i<bytes.length;i++)text+=String.fromCharCode(bytes[i]);
    return decodeURIComponent(escape(text));
  }
  function b64Encode(bytes){
    var binary="";
    for(var i=0;i<bytes.length;i+=0x8000)binary+=String.fromCharCode.apply(null,bytes.subarray(i,i+0x8000));
    return btoa(binary).replace(/\+/g,"-").replace(/\//g,"_").replace(/=+$/g,"");
  }
  function b64Decode(value){
    var text=String(value||"");
    if(!/^[A-Za-z0-9_-]+$/.test(text)||text.length%4===1)throw error("invalid_base64");
    var padded=text.replace(/-/g,"+").replace(/_/g,"/");while(padded.length%4)padded+="=";
    var binary;try{binary=atob(padded);}catch(e){throw error("invalid_base64");}
    var bytes=new Uint8Array(binary.length);for(var i=0;i<binary.length;i++)bytes[i]=binary.charCodeAt(i);return bytes;
  }
  function fnv(value){
    var bytes=utf8(value),hash=2166136261;
    for(var i=0;i<bytes.length;i++){hash^=bytes[i];hash=Math.imul(hash,16777619)>>>0;}
    return hash.toString(36);
  }
  /* Name masking is reversible non-cleartext obfuscation, not cryptographic confidentiality. */
  function obfuscateName(name){var bytes=utf8(name),masked=new Uint8Array(bytes.length);for(var i=0;i<bytes.length;i++)masked[i]=bytes[i]^0x5a;return b64Encode(masked);}
  function revealName(value){var masked=b64Decode(value),bytes=new Uint8Array(masked.length);for(var i=0;i<masked.length;i++)bytes[i]=masked[i]^0x5a;return fromUtf8(bytes);}
  function cleanName(value){var text=String(value==null?"":value).trim();if(!text||text.length>80)throw error("name_invalid");return text;}
  function cleanPlanId(value){var text=String(value==null?"":value).trim();if(text.length>80)throw error("plan_id_invalid");return text;}
  function cleanDate(value){var text=String(value||"").slice(0,10);return /^\d{4}-\d{2}-\d{2}$/.test(text)?text:new Date().toISOString().slice(0,10);}
  function cleanValue(value){
    if(value==null||value==="")return "";
    var text=String(value).trim().replace(",",".");
    if(text.length>12||!/^(?:\d{1,6}(?:\.\d{0,2})?|\.\d{1,2})$/.test(text))throw error("value_out_of_range");
    return text;
  }
  function cleanUnit(value,fallback){var text=String(value||fallback||"").trim().slice(0,12);if(!text||/[^\wÄÖÜäöüß+\/-]/.test(text))return String(fallback||"").slice(0,12);return text;}
  function cleanSetCount(value){var count=Number(value);if(!Number.isFinite(count))count=3;return Math.max(1,Math.min(8,Math.round(count)));}
  function valuePair(value){
    if(Array.isArray(value))return [cleanValue(value[0]),cleanValue(value[1])];
    if(value&&typeof value==="object")return [cleanValue(value.load!=null?value.load:value.l),cleanValue(value.metric!=null?value.metric:value.r)];
    return ["",""];
  }
  function valueArray(source,count,fallback){
    var list=Array.isArray(source)?source:[];
    var out=[];for(var i=0;i<count;i++)out.push(valuePair(list[i]||fallback||["","" ]));return out;
  }
  function exerciseInput(item){
    var raw=item||{},reference=raw.id||raw.exerciseId||raw.sourceId||raw.bankId||"",ref=registryLookup(reference||raw.name);
    if(!ref&&raw.name&&(!reference||String(reference).length!==2))ref=ensureDerived(raw.name,raw);
    if(!ref)throw error("unknown_exercise_id");
    var sets=cleanSetCount(raw.sets||ref.sets),prevSource=raw.previous||raw.prev||raw.lastValues||raw.cockpitPrevious||raw.scanSets;
    var fallback=[raw.startLoad||raw.load||"",raw.startMetric||raw.metric||""];
    var previous=valueArray(prevSource,sets,fallback),today=valueArray(raw.today||raw.current||raw.cockpitToday,sets,previous[0]);
    var todayProvided=Array.isArray(raw.today)||Array.isArray(raw.current)||Array.isArray(raw.cockpitToday);
    if(!todayProvided)today=previous.map(function(pair){return pair.slice();});
    return {id:ref.id,name:ref.name,sets:sets,side:String(raw.side||raw.sides||"BI")==="LR"?"LR":"BI",loadUnit:cleanUnit(raw.loadUnit||raw.weightUnit,ref.loadUnit),metricUnit:cleanUnit(raw.metricUnit||raw.unit,ref.metricUnit),previous:previous,today:today};
  }
  function encodePayload(input){
    var source=input||{},items=Array.isArray(source.exercises)?source.exercises:[];
    if(!items.length||items.length>MAX_EXERCISES)throw error("exercise_count_invalid");
    var ids=Object.create(null),encodedExercises=items.map(function(item){
      var ex=exerciseInput(item);if(ids[ex.id])throw error("duplicate_exercise_id");ids[ex.id]=true;
      return {i:ex.id,s:ex.sets,q:ex.side,u:ex.loadUnit,m:ex.metricUnit,p:ex.previous,t:ex.today};
    });
    var body={v:1,p:cleanPlanId(source.planId||source.id||""),n:obfuscateName(cleanName(source.name||source.patientName||"")),d:cleanDate(source.date),e:encodedExercises};
    var payload={v:body.v,p:body.p,n:body.n,d:body.d,e:body.e,h:fnv(JSON.stringify(body))};
    var code=PREFIX+b64Encode(utf8(JSON.stringify(payload)));
    if(code.length>MAX_CODE_CHARS)throw error("link_too_large");
    return code;
  }
  function validateValueList(value,count){
    if(!Array.isArray(value)||value.length!==count)throw error("set_structure_invalid");
    return value.map(function(pair){if(!Array.isArray(pair)||pair.length!==2)throw error("set_structure_invalid");return [cleanValue(pair[0]),cleanValue(pair[1])];});
  }
  function decodeCode(code){
    var text=String(code||"").trim();if(/^https?:\/\//i.test(text))text=extractCode(text)||"";
    if(text.slice(0,PREFIX.length).toUpperCase()!==PREFIX)throw error("invalid_format");
    var body=text.slice(PREFIX.length);if(!body||body.length>MAX_CODE_CHARS)throw error("invalid_format");
    var parsed;try{parsed=JSON.parse(fromUtf8(b64Decode(body)));}catch(e){throw error("invalid_payload");}
    if(!parsed||parsed.v!==1||typeof parsed.h!=="string"||!Array.isArray(parsed.e)||parsed.e.length<1||parsed.e.length>MAX_EXERCISES)throw error("invalid_payload");
    var unsigned={v:parsed.v,p:String(parsed.p||""),n:String(parsed.n||""),d:String(parsed.d||""),e:parsed.e};
    if(fnv(JSON.stringify(unsigned))!==parsed.h)throw error("integrity_failed");
    var name;try{name=cleanName(revealName(parsed.n));}catch(e){throw error("name_decode_failed");}
    var ids=Object.create(null),exercises=parsed.e.map(function(raw){
      if(!raw||typeof raw.i!=="string"||raw.i.length!==2||!byId[raw.i])throw error("unknown_exercise_id");
      if(ids[raw.i])throw error("duplicate_exercise_id");ids[raw.i]=true;
      var ref=byId[raw.i],sets=cleanSetCount(raw.s);if(sets!==Number(raw.s))throw error("set_structure_invalid");
      if(raw.q!=="BI"&&raw.q!=="LR")throw error("set_structure_invalid");
      return {id:raw.i,name:ref.name,sets:sets,side:raw.q,loadUnit:cleanUnit(raw.u,ref.loadUnit),metricUnit:cleanUnit(raw.m,ref.metricUnit),previous:validateValueList(raw.p,sets),today:validateValueList(raw.t,sets)};
    });
    return {version:1,planId:cleanPlanId(parsed.p),name:name,date:cleanDate(parsed.d),exercises:exercises};
  }
  function extractCode(value){
    var text=String(value||"").trim();if(text.slice(0,PREFIX.length).toUpperCase()===PREFIX)return text;
    try{var url=new URL(text,window.location.href),candidate=url.searchParams.get("cockpit")||url.searchParams.get("kggtc");if(candidate){candidate=decodeURIComponent(candidate);if(candidate.slice(0,PREFIX.length).toUpperCase()===PREFIX)return candidate;}var hash=String(url.hash||"").replace(/^#/,"");if(hash.slice(0,PREFIX.length).toUpperCase()===PREFIX)return hash;}catch(e){}
    return "";
  }
  function makeLink(payload,base){
    var code,url,explicitBase=base!=null&&String(base).trim()!=="",baseValue=explicitBase?String(base):String(window.location&&window.location.href||"");
    if(typeof payload==="string"){
      code=extractCode(payload)||String(payload||"");
      decodeCode(code);
    }else code=encodePayload(payload);
    try{url=new URL(baseValue||PUBLIC_BASE);}catch(e){if(explicitBase)throw error("link_base_invalid");url=new URL(PUBLIC_BASE);}
    if(url.protocol!=="http:"&&url.protocol!=="https:"){if(explicitBase)throw error("link_base_invalid");url=new URL(PUBLIC_BASE);}
    url.searchParams.set("cockpit",code);url.hash="";return url.toString();
  }
  function buildFromPlan(plan){
    var source=plan||{},patient=source.patient||{};return {planId:source.id||"",name:patient.name||source.name||"",date:patient.date||new Date().toISOString().slice(0,10),exercises:(Array.isArray(source.exercises)?source.exercises:[]).map(exerciseInput)};
  }
  function contentKey(input){
    var source=input||{},items=Array.isArray(source.exercises)?source.exercises.map(exerciseInput):[],canonical={planId:cleanPlanId(source.planId||source.id||""),name:cleanName(source.name||source.patientName||""),date:cleanDate(source.date),exercises:items.map(function(ex){return {id:ex.id,sets:ex.sets,side:ex.side,loadUnit:ex.loadUnit,metricUnit:ex.metricUnit,previous:ex.previous,today:ex.today};})};
    return fnv(JSON.stringify(canonical));
  }
  function bankEntryWithCockpitId(item){
    if(!item||!item.name)return item;
    var explicit=String(item.cockpitId||item.cockpitExerciseId||"").trim(),ref=explicit&&byId[explicit];
    if(explicit){
      if(explicit.length!==2||explicit.split("").some(function(ch){return BASE62.indexOf(ch)<0;}))throw error("exercise_id_invalid");
      if(!ref)throw error("unknown_exercise_id");
      if(key(ref.name)!==key(item.name))throw error("exercise_id_collision");
    }else ref=registryLookup(item.name)||ensureDerived(item.name,item);
    return Object.assign({},item,{cockpitId:ref.id});
  }
  function hydrateRegistryFromBank(){
    var shared=window.KGGSharedBank;
    if(!shared||typeof shared.exportPayload!=="function")return;
    try{var payload=shared.exportPayload()||{};if(Array.isArray(payload.exercises))payload.exercises.forEach(function(item){bankEntryWithCockpitId(item);});}catch(e){if(e&&e.code==="exercise_id_collision")window.KGGTherapyCockpitRegistryWarning=e.code;}
  }
  function installBankRegistryHooks(){
    hydrateRegistryFromBank();
    var shared=window.KGGSharedBank;
    if(shared&&!shared.__kggTherapyCockpitWrapped){
      if(typeof shared.exportPayload==="function"){var exportBank=shared.exportPayload;shared.exportPayload=function(){var payload=exportBank.apply(this,arguments)||{};if(Array.isArray(payload.exercises))payload.exercises=payload.exercises.map(bankEntryWithCockpitId);return payload;};}
      if(typeof shared.merge==="function"){var mergeBank=shared.merge;shared.merge=function(raw){var value=raw;if(raw&&typeof raw==="object"&&Array.isArray(raw.exercises))value=Object.assign({},raw,{exercises:raw.exercises.map(bankEntryWithCockpitId)});return mergeBank.call(this,value);};}
      shared.__kggTherapyCockpitWrapped=true;
    }
    var nativeSync=window.KGGNativeExerciseSync;
    if(nativeSync&&!nativeSync.__kggTherapyCockpitWrapped){
      if(typeof nativeSync.build==="function"){var buildSync=nativeSync.build;nativeSync.build=function(){var doc=buildSync.apply(this,arguments)||{};if(Array.isArray(doc.exerciseBank))doc=Object.assign({},doc,{exerciseBank:doc.exerciseBank.map(bankEntryWithCockpitId)});return doc;};}
      if(typeof nativeSync.merge==="function"){var mergeSync=nativeSync.merge;nativeSync.merge=function(raw,options){var value=raw;if(raw&&typeof raw==="object"&&Array.isArray(raw.exerciseBank))value=Object.assign({},raw,{exerciseBank:raw.exerciseBank.map(bankEntryWithCockpitId)});return mergeSync.call(this,value,options);};}
      nativeSync.__kggTherapyCockpitWrapped=true;
    }
  }
  var slots=[null,null,null],activeInput=null,currentView="normal",root=null,board=null,notice="",toastTimer=null;
  function htmlEscape(value){return String(value==null?"":value).replace(/[&<>"']/g,function(ch){return {"&":"&amp;","<":"&lt;",">":"&gt;","\"":"&quot;","'":"&#39;"}[ch];});}
  function initials(name){return String(name||"?").trim().split(/\s+/).slice(0,2).map(function(x){return x.charAt(0);}).join("").toUpperCase()||"?";}
  function slotCount(){return slots.reduce(function(total,slot){return total+(slot?1:0);},0);}
  function firstFreeSlot(){for(var i=0;i<MAX_SLOTS;i++)if(!slots[i])return i;return -1;}
  function slotProgress(slot){var total=0,done=0;(slot&&slot.exercises||[]).forEach(function(ex){(ex.today||[]).forEach(function(pair){total+=2;if(pair[0])done++;if(pair[1])done++;});});return total?Math.round(done/total*100):0;}
  function normalizeSlot(decoded){return {planId:decoded.planId,name:decoded.name,date:decoded.date,exercises:decoded.exercises.map(function(ex){return {id:ex.id,name:ex.name,sets:ex.sets,side:ex.side,loadUnit:ex.loadUnit,metricUnit:ex.metricUnit,previous:ex.previous.map(function(p){return p.slice();}),today:ex.today.map(function(p){return p.slice();})};}),contentKey:contentKey(decoded),openExercise:null,lastCompletion:null};}
  function payloadFromSlot(slot,useTodayAsPrevious){return {planId:slot.planId,name:slot.name,date:new Date().toISOString().slice(0,10),exercises:slot.exercises.map(function(ex){return {id:ex.id,sets:ex.sets,side:ex.side,loadUnit:ex.loadUnit,metricUnit:ex.metricUnit,previous:(useTodayAsPrevious?ex.today:ex.previous).map(function(p){return p.slice();}),today:ex.today.map(function(p){return p.slice();})};})};}
  function valuesLabel(pair,ex){var load=pair&&pair[0]||"–",metric=pair&&pair[1]||"–";return load+" "+(ex.loadUnit||"")+" / "+metric+" "+(ex.metricUnit||"");}
  function mediaMarkup(ex){var current=ex&&ex.media&&Array.isArray(ex.media)?ex.media[0]:null;if(current&&current.downloadUrl&&/^data:image\//i.test(current.downloadUrl))return '<img alt="" src="'+htmlEscape(current.downloadUrl)+'">';return htmlEscape(initials(ex&&ex.name));}
  function renderPad(slotIndex,exerciseIndex,setIndex,field,ex){
    var fieldName=field==="load"?(ex.loadUnit||"kg"):(ex.metricUnit||"Wdh"),html='<div class="kgg-tc-pad" data-tc-pad="1"><div class="kgg-tc-pad-head"><span>Wert eingeben · '+htmlEscape(fieldName)+'</span><span class="kgg-tc-pad-modes">';
    html+='<button type="button" class="kgg-tc-pad-mode '+(field==="load"?"active":"")+'" data-tc-action="mode" data-tc-slot="'+slotIndex+'" data-tc-ex="'+exerciseIndex+'" data-tc-set="'+setIndex+'" data-tc-field="load">'+htmlEscape(ex.loadUnit||"kg")+'</button>';
    html+='<button type="button" class="kgg-tc-pad-mode '+(field==="metric"?"active":"")+'" data-tc-action="mode" data-tc-slot="'+slotIndex+'" data-tc-ex="'+exerciseIndex+'" data-tc-set="'+setIndex+'" data-tc-field="metric">'+htmlEscape(ex.metricUnit||"Wdh")+'</button></span></div><div class="kgg-tc-pad-keys">';
    ["1","2","3","4","5","6","7","8","9","0",",","⌫","C","–","OK"].forEach(function(keyValue){var cls=(keyValue===","||keyValue==="⌫"||keyValue==="C"||keyValue==="–"||keyValue==="OK")?" action":"";html+='<button type="button" class="kgg-tc-key'+cls+'" data-tc-action="key" data-tc-key="'+htmlEscape(keyValue)+'" data-tc-slot="'+slotIndex+'" data-tc-ex="'+exerciseIndex+'" data-tc-set="'+setIndex+'" data-tc-field="'+field+'">'+htmlEscape(keyValue)+'</button>';});
    return html+'</div></div>';
  }
  function renderExercise(slot,slotIndex,ex,exerciseIndex){
    var open=slot.openExercise===exerciseIndex,summary=(ex.today||[]).map(function(pair){return valuesLabel(pair,ex);}).join(" · ");
    var html='<article class="kgg-tc-exercise '+(open?"open":"")+'"><button type="button" class="kgg-tc-card-toggle" data-tc-action="toggle" data-tc-slot="'+slotIndex+'" data-tc-ex="'+exerciseIndex+'"><span class="kgg-tc-thumb" aria-hidden="true">'+mediaMarkup(ex)+'</span><span class="kgg-tc-exercise-summary"><strong>'+htmlEscape(ex.name)+'</strong><small>'+ex.sets+' Sätze · '+htmlEscape(ex.side==="LR"?"links/rechts":"beidseitig")+(summary?" · "+htmlEscape(summary):"")+'</small></span><span class="kgg-tc-chevron" aria-hidden="true">'+(open?"⌃":"⌄")+'</span></button>';
    if(open){
      html+='<div class="kgg-tc-exercise-detail"><div class="kgg-tc-values-head"><span>Satz</span><span>Vorwert</span><span>Heute</span></div>';
      for(var setIndex=0;setIndex<ex.sets;setIndex++){
        var prev=ex.previous[setIndex]||["",""];var today=ex.today[setIndex]||["",""];html+='<div class="kgg-tc-set-row"><span class="kgg-tc-set-no">S'+(setIndex+1)+'</span><span class="kgg-tc-prev" aria-label="Vorwert">'+htmlEscape(valuesLabel(prev,ex))+'</span>';
        ["load","metric"].forEach(function(field){var val=field==="load"?today[0]:today[1],active=activeInput&&activeInput.slot===slotIndex&&activeInput.exercise===exerciseIndex&&activeInput.set===setIndex&&activeInput.field===field;html+='<button type="button" class="kgg-tc-field '+(active?"active ":"")+(val?"":"empty")+'" data-tc-action="input" data-tc-slot="'+slotIndex+'" data-tc-ex="'+exerciseIndex+'" data-tc-set="'+setIndex+'" data-tc-field="'+field+'" aria-label="Heute '+htmlEscape(field==="load"?(ex.loadUnit||"kg"):(ex.metricUnit||"Wdh"))+'">'+htmlEscape(val||"—")+'</button>';if(active)html+=renderPad(slotIndex,exerciseIndex,setIndex,field,ex);});
        html+='</div>';
      }
      html+='</div>';
    }
    return html+'</article>';
  }
