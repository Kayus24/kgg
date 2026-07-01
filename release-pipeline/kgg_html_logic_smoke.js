#!/usr/bin/env node
// Local/static smoke tests for KGG HTML logic.
// No browser, no emulator, no network, no GitHub mutation.

const fs = require("fs");
const path = require("path");
const vm = require("vm");

const ROOT = path.resolve(__dirname, "..");
const HTML_PATH = path.join(ROOT, "kgg-update", "index.html");
const BOOT_MARKER = [
  "  installKggV383UiFlowStability();",
  "  installKggV388AndroidFlowFixes();",
  "  load();",
].join("\n");

function fail(message) {
  throw new Error(message);
}

function assert(condition, message) {
  if (!condition) fail(message);
}

function parseArgs(argv) {
  const out = { suite: "all" };
  const validSuites = [
    "all",
    "sync",
    "sync-critical",
    "sync-regression",
    "native-sync",
    "native-sync-regression",
    "pdf",
    "pdf-critical",
    "textblocks",
    "textblocks-critical",
    "textblocks-regression",
  ];
  for (let i = 0; i < argv.length; i += 1) {
    const arg = argv[i];
    if (arg === "--suite") {
      out.suite = argv[i + 1] || "";
      i += 1;
    } else if (arg === "--help" || arg === "-h") {
      out.help = true;
    } else {
      fail(`Unknown argument: ${arg}`);
    }
  }
  if (!validSuites.includes(out.suite)) {
    fail(`--suite must be one of: ${validSuites.join(", ")}`);
  }
  return out;
}

function readMainAppScript() {
  const html = fs.readFileSync(HTML_PATH, "utf8");
  const scripts = [...html.matchAll(/<script(?:\s[^>]*)?>([\s\S]*?)<\/script>/gi)].map((match) => match[1]);
  const main = scripts.find((script) => script.includes("const VERSION='KGG_GITHUB_UPDATE"));
  if (!main) fail("KGG main app script not found in kgg-update/index.html");
  const normalizedMain = main.replace(/\r\n/g, "\n");
  const bootIndex = normalizedMain.indexOf(BOOT_MARKER);
  if (bootIndex < 0) fail("KGG boot marker not found; update kgg_html_logic_smoke.js");
  return normalizedMain.slice(0, bootIndex);
}

function classList() {
  const values = new Set();
  return {
    add(...items) {
      items.forEach((item) => values.add(String(item)));
    },
    remove(...items) {
      items.forEach((item) => values.delete(String(item)));
    },
    toggle(item, force) {
      const key = String(item);
      if (force === true) {
        values.add(key);
        return true;
      }
      if (force === false) {
        values.delete(key);
        return false;
      }
      if (values.has(key)) {
        values.delete(key);
        return false;
      }
      values.add(key);
      return true;
    },
    contains(item) {
      return values.has(String(item));
    },
  };
}

function fakeNode(id) {
  return {
    id,
    value: "",
    textContent: "",
    innerHTML: "",
    className: "",
    style: {
      setProperty() {},
      removeProperty() {},
    },
    dataset: {},
    classList: classList(),
    children: [],
    files: [],
    scrollHeight: 0,
    scrollTop: 0,
    selectionStart: 0,
    appendChild(child) {
      this.children.push(child);
      return child;
    },
    replaceChildren(...children) {
      this.children = children;
    },
    addEventListener() {},
    removeEventListener() {},
    setAttribute() {},
    removeAttribute() {},
    focus() {},
    blur() {},
    select() {},
    click() {},
    getBoundingClientRect() {
      return { top: 0, left: 0, right: 0, bottom: 0, width: 0, height: 0 };
    },
    querySelector() {
      return null;
    },
    querySelectorAll() {
      return [];
    },
  };
}

function createContext() {
  const nodes = {};
  const document = {
    __nodes: nodes,
    body: fakeNode("body"),
    activeElement: null,
    getElementById(id) {
      if (!this.__nodes[id]) this.__nodes[id] = fakeNode(id);
      return this.__nodes[id];
    },
    querySelector() {
      return null;
    },
    querySelectorAll() {
      return [];
    },
    createElement(tag) {
      return fakeNode(tag);
    },
    createTextNode(text) {
      return { textContent: String(text || "") };
    },
    addEventListener() {},
    removeEventListener() {},
  };

  const storage = new Map();
  const localStorage = {
    getItem(key) {
      return storage.has(key) ? storage.get(key) : null;
    },
    setItem(key, value) {
      storage.set(key, String(value));
    },
    removeItem(key) {
      storage.delete(key);
    },
    clear() {
      storage.clear();
    },
  };

  class MutationObserver {
    constructor() {}
    observe() {}
    disconnect() {}
  }

  const crypto = {
    getRandomValues(array) {
      for (let i = 0; i < array.length; i += 1) array[i] = i + 17;
      return array;
    },
  };

  const navigator = { userAgent: "kgg-node-smoke", language: "de-DE", onLine: true };
  const window = {
    document,
    localStorage,
    navigator,
    crypto,
    KGG_PATIENT_BASE_URL: "",
    addEventListener() {},
    removeEventListener() {},
    dispatchEvent() {},
    matchMedia() {
      return { matches: false, addEventListener() {}, removeEventListener() {} };
    },
  };

  Object.assign(window, { TextEncoder, TextDecoder });

  const context = {
    window,
    document,
    localStorage,
    navigator,
    crypto,
    console,
    setTimeout,
    clearTimeout,
    TextEncoder,
    TextDecoder,
    MutationObserver,
    location: { href: "file://kgg-html-logic-smoke", hash: "" },
    alert() {},
  };
  context.globalThis = context;
  return context;
}

function runInsideApp(testCode) {
  const context = createContext();
  vm.createContext(context);
  const source = `${readMainAppScript()}
  function assert(condition,message){ if(!condition) throw new Error(message||'assertion failed'); }
  render=function(){};
  save=function(){};
  persistCustomBank=function(){};
  persistDeletedBankIds=function(){};
  setScanStatus=function(message){ window.__scanStatus=message; };
  ${testCode}
})();`;
  vm.runInContext(source, context, { filename: "kgg-update/index.html#logic-smoke" });
  return context.window.__results || {};
}

function pdfCriticalSuite() {
  return runInsideApp(`
    assert(typeof attachKggPdfExerciseThumbnails==='function','PDF thumbnail attach helper missing');
    assert(typeof createKggPdfThumbnailDataUrl==='function','PDF thumbnail data URL helper missing');
    const snapshot=buildKggPdfSnapshot({exercises:[{id:'ex_plain',name:'Rudern',sets:3,unit:'Wdh',weightUnit:'kg'}],patient:{name:'Test'}}); 
    assert(snapshot.pages[0].slots[0].name==='Rudern','PDF snapshot exercise missing');
    assert(!snapshot.pages[0].slots[0].pdfThumbnail,'PDF snapshot should not invent thumbnails');
    const slot=normalizePdfExercise({id:'ex_img',name:'Single leg Press',sets:3,unit:'Wdh',weightUnit:'kg'},0,0,0);
    slot.pdfThumbnail={dataUrl:'data:image/jpeg;base64,/9j/2w==',mime:'image/jpeg',width:150,height:110};
    const calls=[];
    const doc={
      setLineWidth(value){calls.push(['lineWidth',value]);},
      setDrawColor(){},
      setTextColor(){},
      setFillColor(){},
      setFont(){},
      setFontSize(){},
      rect(x,y,w,h,style){calls.push(['rect',x,y,w,h,style||'']);},
      roundedRect(x,y,w,h){calls.push(['roundedRect',x,y,w,h]);},
      line(x1,y1,x2,y2){calls.push(['line',x1,y1,x2,y2]);},
      text(text,x,y,opts){calls.push(['text',String(text),x,y,opts&&opts.align||'']);},
      addImage(data,format,x,y,w,h){calls.push(['addImage',data,format,x,y,w,h]);}
    };
    drawKggExerciseBox(doc,slot,10,20,130,48);
    const imageCall=calls.find(call=>call[0]==='addImage');
    assert(!!imageCall,'PDF thumbnail was not drawn');
    assert(imageCall[2]==='JPEG','PDF thumbnail must be embedded as JPEG');
    assert(imageCall[3]>=10 && imageCall[3]+imageCall[5]<=140,'PDF thumbnail x bounds escaped card');
    assert(imageCall[4]>=20 && imageCall[4]+imageCall[6]<=68,'PDF thumbnail y bounds escaped card');
    assert(calls.some(call=>call[0]==='rect' && call[4]>0),'PDF exercise box/table rects missing');
    window.__results={suite:'pdf-critical',imageCall};
  `);
}

function syncSuite() {
  return runInsideApp(`
    document.__nodes.therapistName.value='Thera A';
    const beforeBankCount=bank.length;
    const doc=buildNativeExerciseBankSyncDocument();
    assert(doc.kind==='kgg_cross_data_safe_sync','sync export kind mismatch');
    assert(doc.version===2,'sync export version mismatch');
    assert(doc.privacy && doc.privacy.patients===false,'sync export must exclude patients');
    assert(doc.privacy && doc.privacy.secrets===false,'sync export must exclude secrets');
    assert(Array.isArray(doc.exerciseBank) && doc.exerciseBank.length>=beforeBankCount,'sync export missing exercise bank');
    ['apiKey','patientName','rawPayload','access_token','refresh_token'].forEach(key=>{
      let blocked=false;
      try{assertCrossDataSafeSyncDocument({kind:'kgg_cross_data_safe_sync',[key]:'blocked'});}
      catch(err){blocked=true;}
      assert(blocked,'sync safe document allowed forbidden key '+key);
    });
    const incoming={
      kind:'kgg_cross_data_safe_sync',
      version:2,
      exportedAt:new Date().toISOString(),
      roomId:'room_test',
      schema:'exercise-bank-packages-v2',
      scopes:['exerciseBank','packages'],
      privacy:{patients:false,secrets:false,debugPayloads:false,rawData:false},
      origin:{deviceId:'peer_x',therapistId:'peer_x',displayName:'Peer X',roomId:'room_test'},
      exerciseBank:[{id:'probe_ex',name:'Probe Spezial',aliases:'probe spezial',sets:3,unit:'Wdh',weightUnit:'bar',updatedAt:new Date().toISOString()}],
      packages:[{id:'pkg_probe',name:'Probe Paket',exercises:['Probe Spezial'],updatedAt:new Date().toISOString()}],
      tombstones:{exerciseBank:[]}
    };
    const result=mergeNativeExerciseBankSyncDocument(incoming,{allowUnfollowed:true});
    assert(result.bank.added>=1 || result.bank.updated>=1,'sync merge did not add/update exercise');
    assert(result.packages.added>=1 || result.packages.updated>=1,'sync merge did not add/update package');
    assert(!!bank.find(item=>item.name==='Probe Spezial'),'merged exercise not found in bank');
    assert(!!state.packages.find(item=>item.name==='Probe Paket'),'merged package not found');
    window.__results={suite:'sync',exported:doc.exerciseBank.length,merge:result};
  `);
}

function syncCriticalSuite() {
  return runInsideApp(`
    document.__nodes.therapistName.value='Thera A';
    const beforeBankCount=bank.length;
    const doc=buildNativeExerciseBankSyncDocument();
    assert(doc.kind==='kgg_cross_data_safe_sync','sync export kind mismatch');
    assert(doc.version===2,'sync export version mismatch');
    assert(doc.privacy && doc.privacy.patients===false,'sync export must exclude patients');
    assert(doc.privacy && doc.privacy.secrets===false,'sync export must exclude secrets');
    assert(Array.isArray(doc.exerciseBank) && doc.exerciseBank.length>=beforeBankCount,'sync export missing exercise bank');
    ['apiKey','patientName','rawPayload','access_token','refresh_token'].forEach(key=>{
      let blocked=false;
      try{assertCrossDataSafeSyncDocument({kind:'kgg_cross_data_safe_sync',[key]:'blocked'});}
      catch(err){blocked=true;}
      assert(blocked,'sync safe document allowed forbidden key '+key);
    });
    window.__results={suite:'sync-critical',exported:doc.exerciseBank.length};
  `);
}

function nativeSyncSuite() {
  return runInsideApp(`
    localStorage.setItem('kgg_sync_pair_device_id_v1','self_device');
    localStorage.setItem('kgg_sync_pair_follow_config_v1',JSON.stringify({
      therapistId:'self_device',
      syncRoomId:'room_native_smoke',
      followedTherapists:[{
        therapistId:'peer_allowed',
        deviceId:'peer_allowed',
        displayName:'Peer Allowed',
        roomId:'room_native_smoke',
        autoDownload:true,
        scopes:['exerciseBank','packages']
      }]
    }));
    document.__nodes.therapistName.value='Self Device';
    const exported=buildNativeExerciseBankSyncDocument();
    assert(exported.kind==='kgg_cross_data_safe_sync','native export kind mismatch');
    assert(exported.roomId==='room_native_smoke','native export room mismatch');
    assert(exported.origin.deviceId==='self_device','native export self origin mismatch');
    assert(exported.privacy.patients===false && exported.privacy.secrets===false,'native export privacy mismatch');

    const now=new Date().toISOString();
    function peerDoc(deviceId,name,loadUnit){
      return {
        kind:'kgg_cross_data_safe_sync',
        version:2,
        exportedAt:now,
        roomId:'room_native_smoke',
        schema:'exercise-bank-packages-v2',
        scopes:['exerciseBank','packages'],
        privacy:{patients:false,secrets:false,debugPayloads:false,rawData:false},
        origin:{deviceId,therapistId:deviceId,displayName:name,roomId:'room_native_smoke'},
        exerciseBank:[{id:'ex_'+deviceId,name:name+' Uebung',aliases:name,sets:3,unit:'Wdh',weightUnit:loadUnit,updatedAt:now}],
        packages:[{id:'pkg_'+deviceId,name:name+' Paket',exercises:[name+' Uebung'],updatedAt:now}],
        tombstones:{exerciseBank:[]}
      };
    }
    const self=peerDoc('self_device','Self','kg');
    const skipped=peerDoc('peer_skipped','Peer Skipped','kg');
    const allowed=peerDoc('peer_allowed','Peer Allowed','bar');
    const mesh={kind:'kgg_cross_data_safe_sync_mesh',version:1,roomId:'room_native_smoke',peers:[self,skipped,allowed]};
    const result=mergeNativeExerciseBankSyncDocument(mesh);
    assert(result.mesh.seen===3,'mesh seen mismatch');
    assert(result.mesh.merged===1,'mesh should merge exactly one followed peer, got '+result.mesh.merged);
    assert(result.mesh.skipped>=2,'mesh should skip self and unfollowed peer');
    assert(!!bank.find(item=>item.name==='Peer Allowed Uebung'),'followed peer exercise not merged');
    assert(!bank.find(item=>item.name==='Peer Skipped Uebung'),'unfollowed peer exercise should not merge');
    assert(!!state.packages.find(item=>item.name==='Peer Allowed Paket'),'followed peer package not merged');

    const allowAll=mergeNativeExerciseBankSyncDocument({kind:'kgg_cross_data_safe_sync_mesh',version:1,roomId:'room_native_smoke',peers:[skipped]},{allowUnfollowed:true});
    assert(allowAll.mesh.merged===1,'allowUnfollowed mesh should merge skipped peer');
    assert(!!bank.find(item=>item.name==='Peer Skipped Uebung'),'allowUnfollowed peer exercise not merged');

    const tombstone={
      kind:'kgg_cross_data_safe_sync',
      version:2,
      exportedAt:now,
      roomId:'room_native_smoke',
      schema:'exercise-bank-packages-v2',
      scopes:['exerciseBank','packages'],
      privacy:{patients:false,secrets:false,debugPayloads:false,rawData:false},
      origin:{deviceId:'peer_allowed',therapistId:'peer_allowed',displayName:'Peer Allowed',roomId:'room_native_smoke'},
      exerciseBank:[],
      packages:[],
      tombstones:{exerciseBank:[{id:'ex_peer_allowed',deleted:true,updatedAt:now}]}
    };
    const tombstoneResult=mergeNativeExerciseBankSyncDocument(tombstone);
    assert(tombstoneResult.tombstones.removed>=1,'tombstone did not remove existing exercise');
    assert(!bank.find(item=>item.id==='ex_peer_allowed'),'tombstoned exercise still exists');

    ['apiKey','patientName','rawPayload','access_token','refresh_token','base64Payload'].forEach(key=>{
      const bad=peerDoc('bad_'+key,'Bad '+key,'kg');
      bad[key]='blocked';
      let blocked=false;
      try{mergeNativeExerciseBankSyncDocument(bad,{allowUnfollowed:true});}
      catch(err){blocked=true;}
      assert(blocked,'native sync accepted forbidden key '+key);
    });

    window.__results={suite:'native-sync',exported:exported.exerciseBank.length,mesh:result.mesh,tombstones:tombstoneResult.tombstones};
  `);
}

function textblockCriticalSuite() {
  return runInsideApp(`
    const input=document.__nodes.exerciseInput;
    input.value=[
      'Beinpresse',
      'Satz 1: 12 Wdh @ 42 kg',
      'Satz 2: 12 Wdh @ 42 kg',
      '',
      'Dips',
      'Satz 1: 15 Wdh @ 30 kg',
      '',
      'Kniebeuger Maschine - Tag 1 1. Satz: 35 kg @ 12 Wdh Schmerz: 1/10'
    ].join('\\n');
    syncPlanFromTextInput('logic_smoke_textblocks_critical');
    const names=state.plan.map(ex=>ex.name);
    assert(state.plan.length===3,'critical text block should create 3 exercises, got '+state.plan.length+' '+names.join('|'));
    assert(names.includes('Beinpresse') && names.includes('Dips') && names.includes('Kniebeuger Maschine'),'critical text block missed expected exercises: '+names.join('|'));
    assert(!names.some(name=>/^(Satz\\s+\\d|S\\d|\\d+\\)|Schmerz|Tag\\s*\\d+)/i.test(name)),'critical text block created Satz/Schmerz cards: '+names.join('|'));
    const storePlan=window.KGGDataStore.getCurrentPlan();
    assert(storePlan && Array.isArray(storePlan.exercises),'KGGDataStore.currentPlan missing exercises');
    assert(storePlan.exercises.length===state.plan.length,'KGGDataStore.currentPlan not synced with state.plan');
    const legpress=state.plan.find(ex=>ex.name==='Beinpresse');
    const storeLegpress=storePlan.exercises.find(ex=>ex.name==='Beinpresse');
    assert(legpress && storeLegpress,'Beinpresse missing in state or store');
    assert(legpress.startMetric==='12','Beinpresse reps not preserved');
    assert(legpress.startLoad==='42','Beinpresse load not preserved');
    assert(legpress.weightUnit==='kg' && storeLegpress.weightUnit==='kg','Beinpresse kg unit not preserved');
    const curl=state.plan.find(ex=>ex.name==='Kniebeuger Maschine');
    assert(curl && curl.startMetric==='12' && curl.startLoad==='35' && curl.weightUnit==='kg','load-before-reps Satz format not preserved');
    window.__results={suite:'textblocks-critical',names};
  `);
}

function textblockSuite() {
  return runInsideApp(`
    const input=document.__nodes.exerciseInput;
    function byName(name){
      return state.plan.find(ex=>ex.name===name);
    }
    function storeByName(name){
      const plan=window.KGGDataStore.getCurrentPlan();
      return (plan.exercises||[]).find(ex=>ex.name===name);
    }
    function assertPlanUnit(name, expected){
      const ex=byName(name);
      assert(!!ex,'missing exercise '+name+' in state.plan');
      const storeEx=storeByName(name);
      assert(!!storeEx,'missing exercise '+name+' in KGGDataStore.currentPlan');
      if(expected.metric!==undefined)assert(ex.startMetric===expected.metric,name+' metric mismatch: '+ex.startMetric);
      if(expected.load!==undefined)assert((ex.startLoad||'')===expected.load,name+' load mismatch: '+ex.startLoad);
      if(expected.unit!==undefined)assert((ex.unit||ex.metricUnit||'')===expected.unit,name+' unit mismatch: '+(ex.unit||ex.metricUnit));
      if(expected.weightUnit!==undefined){
        assert(ex.weightUnit===expected.weightUnit,name+' weightUnit mismatch: '+ex.weightUnit);
        assert(ex.loadUnit===expected.weightUnit,name+' loadUnit mismatch: '+ex.loadUnit);
        assert(storeEx.weightUnit===expected.weightUnit,name+' store weightUnit mismatch: '+storeEx.weightUnit);
        assert(storeEx.loadUnit===expected.weightUnit,name+' store loadUnit mismatch: '+storeEx.loadUnit);
        assert(formatExerciseTextLine(ex).includes(expected.weightUnit),name+' formatted text lost unit: '+formatExerciseTextLine(ex));
        assert(exerciseMeta(ex).includes(expected.weightUnit),name+' meta lost unit: '+exerciseMeta(ex));
      }
      if(expected.review!==undefined)assert(!!ex.needsReview===expected.review,name+' review mismatch: '+ex.needsReview);
    }
    input.value=[
      'Beinpresse',
      'Satz 1: 12 Wdh @ 42 kg',
      'Satz 2: 12 Wdh @ 42 kg',
      'Satz 3: 15 Wdh @ 42 kg',
      '',
      'Dips',
      'Satz 1: 15 Wdh @ 30 kg',
      'Satz 2: 12 Wdh @ 30 kg',
      'Satz 3: 12 Wdh @ 0 kg',
      '',
      'Abduktion Maschine',
      'Satz 1: 12 Wdh @ 27 kg',
      'Satz 2: 12 Wdh @ 27 kg',
      'Satz 3: 12 Wdh @ 27 kg',
      '',
      'Adduktion Maschine',
      'Satz 1: 12 Wdh @ 2 bar',
      'Satz 2: 12 Wdh @ 2 bar',
      'Satz 3: 12 Wdh @ 2 bar',
      '',
      'Latziehen',
      'Satz 1: 12 Wdh @ 30 kg',
      'Satz 2: 12 Wdh @ 30 kg',
      'Satz 3: 12 Wdh @ 30 kg',
      '',
      'Ergometer / Bike',
      'Satz 1: 5 min @ 80 Watt',
      '',
      'Rudern',
      'Satz 1: 12 Wdh @ 8 Hub',
      '',
      'Plank',
      'Satz 1: 60 sek @ keine',
      '',
      'Laufband',
      'S1: 10 min @ 6 km/h',
      '',
      'Mobilität',
      '1. Satz 30 sec @ 90 Grad',
      '',
      'Balance',
      '1) 45 time @ Level 3',
      '',
      'Dehnung',
      'Satz 1 - 60 Zeit @ RPE 4',
      '',
      'Sprungtest',
      'Satz 1: 8 reps @ 35 cm',
      '',
      'Bike',
      'Satz 1: 5 min @ 70 rpm',
      '',
      'Kniebeuger Maschine',
      'Satz 1: 12 Wdh @ 25 kg',
      '',
      'Kniestrecker Maschine',
      'Satz 1: 12 Wdh @ 23 kg'
    ].join('\\n');
    syncPlanFromTextInput('logic_smoke_textblocks');
    const names=state.plan.map(ex=>ex.name);
    assert(state.plan.length===16,'structured text block should create 16 exercises, got '+state.plan.length+' '+names.join('|'));
    assert(!names.some(name=>/^(Satz\\s+\\d|S\\d|\\d+\\))/i.test(name)),'structured text block created Satz cards: '+names.join('|'));
    ['Beinpresse','Dips','Abduktion Maschine','Adduktion Maschine','Latziehen','Ergometer / Bike','Rudern','Plank','Laufband','Mobilität','Balance','Dehnung','Sprungtest','Bike','Kniebeuger Maschine','Kniestrecker Maschine'].forEach(name=>{
      assert(names.includes(name),'missing structured exercise '+name+' in '+names.join('|'));
    });
    const legpress=byName('Beinpresse');
    assert(legpress.startMetric==='12','Beinpresse reps not preserved');
    assert(legpress.startLoad==='42','Beinpresse load not preserved');
    assert(legpress.weightUnit==='kg','Beinpresse kg unit not preserved');
    const add=byName('Adduktion Maschine');
    assert(add.startLoad==='2' && add.weightUnit==='bar','bar unit not preserved');
    const bike=byName('Ergometer / Bike');
    assert(bike.startMetric==='5 min' && bike.unit==='Zeit','time metric not preserved');
    assert(bike.startLoad==='80' && bike.weightUnit==='Watt','Watt unit not preserved');
    assertPlanUnit('Rudern',{metric:'12',load:'8',unit:'Wdh',weightUnit:'Hub',review:false});
    assertPlanUnit('Plank',{metric:'60 sek',load:'',unit:'Zeit',weightUnit:'keine',review:false});
    assertPlanUnit('Laufband',{metric:'10 min',load:'6',unit:'Zeit',weightUnit:'km/h',review:true});
    assertPlanUnit('Mobilität',{metric:'30 sec',load:'90',unit:'Zeit',weightUnit:'Grad',review:true});
    assertPlanUnit('Balance',{metric:'45 time',load:'3',unit:'Zeit',weightUnit:'Level',review:true});
    assertPlanUnit('Dehnung',{metric:'60 Zeit',load:'4',unit:'Zeit',weightUnit:'RPE',review:true});
    assertPlanUnit('Sprungtest',{metric:'8',load:'35',unit:'Wdh',weightUnit:'cm',review:true});
    assertPlanUnit('Bike',{metric:'5 min',load:'70',unit:'Zeit',weightUnit:'rpm',review:true});

    input.value='Beinpresse, Latziehen';
    syncPlanFromTextInput('logic_smoke_comma');
    const commaNames=state.plan.map(ex=>ex.name);
    assert(commaNames.length===2 && commaNames[0]==='Beinpresse' && commaNames[1]==='Latziehen','normal comma input regressed: '+commaNames.join('|'));

    input.value='Latziehen 12x30kg, Laufband 10 min @ 6 km/h, Plank 60 sek @ keine';
    syncPlanFromTextInput('logic_smoke_inline_units');
    assertPlanUnit('Latziehen',{metric:'12',load:'30',unit:'Wdh',weightUnit:'kg',review:false});
    assertPlanUnit('Laufband',{metric:'10 min',load:'6',unit:'Zeit',weightUnit:'km/h',review:true});
    assertPlanUnit('Plank',{metric:'60 sek',load:'',unit:'Zeit',weightUnit:'keine',review:false});

    input.value=[
      'Beinpresse - Tag 1',
      '',
      '1. Satz: 15 kg @ 12 Wdh',
      '',
      '2. Satz: 15 kg @ 7 Wdh',
      '',
      '3. Satz: 10 kg @ 10 Wdh',
      '',
      'Schmerz: 3/10',
      '',
      'Kniebeuger Maschine - Tag 1 1. Satz: 35 kg @ 12 Wdh 2. Satz: 35 kg @ 12 Wdh 3. Satz: 35 kg @ 12 Wdh Schmerz: 1/10',
      '',
      'Singel Leg to Stand - Tag 1 1. Satz: 61 HÃ¶he @ 12 Wdh 2. Satz: 61 HÃ¶he @ 12 Wdh 3. Satz: 61 HÃ¶he @ 10 Wdh Schmerz: 2/10',
      '',
      'Romanian Deadlift - Tag 1',
      '',
      '1. Satz: 8 kg @ 10 Wdh',
      '',
      '2. Satz: 8 kg @ 10 Wdh',
      '',
      '3. Satz: 8 kg @ 8 Wdh',
      '',
      'Schmerz: 2/10'
    ].join('\\n');
    syncPlanFromTextInput('logic_smoke_real_schmerz_tag_block');
    const realNames=state.plan.map(ex=>ex.name);
    assert(realNames.length===4,'real Schmerz/Tag block should create 4 exercises, got '+realNames.length+' '+realNames.join('|'));
    ['Beinpresse','Kniebeuger Maschine','Singel Leg to Stand','Romanian Deadlift'].forEach(name=>{
      assert(realNames.includes(name),'real Schmerz/Tag block missing '+name+' in '+realNames.join('|'));
    });
    assert(!realNames.some(name=>/^(?:\\d+\\.\\s*)?Satz|^Schmerz|^Tag\\s*\\d+/i.test(name)),'real Schmerz/Tag block created junk cards: '+realNames.join('|'));
    assertPlanUnit('Beinpresse',{metric:'12',load:'15',unit:'Wdh',weightUnit:'kg'});
    assertPlanUnit('Kniebeuger Maschine',{metric:'12',load:'35',unit:'Wdh',weightUnit:'kg'});
    assertPlanUnit('Singel Leg to Stand',{metric:'12',load:'61',unit:'Wdh',weightUnit:'HÃ¶he',review:true});
    assertPlanUnit('Romanian Deadlift',{metric:'10',load:'8',unit:'Wdh',weightUnit:'kg',review:true});

    const applyText=scanResultToApplyText({exercises:[{name:'Beinpresse',sets:[{reps:12,load:42},{reps:12,load:42},{reps:15,load:42}]},{name:'Dips',sets:[{reps:15,load:30}]}]});
    assert(applyText==='Beinpresse, Dips','structured scan apply text regressed: '+applyText);
    window.__results={suite:'textblocks',structuredNames:names,commaNames,applyText};
  `);
}

function main() {
  const args = parseArgs(process.argv.slice(2));
  if (args.help) {
    console.log("Usage: node release-pipeline/kgg_html_logic_smoke.js [--suite all|sync|sync-critical|sync-regression|native-sync|native-sync-regression|pdf|pdf-critical|textblocks|textblocks-critical|textblocks-regression]");
    return 0;
  }
  const results = {};
  if (args.suite === "sync-critical") results.syncCritical = syncCriticalSuite();
  if (args.suite === "textblocks-critical") results.textblocksCritical = textblockCriticalSuite();
  if (args.suite === "pdf-critical") results.pdfCritical = pdfCriticalSuite();
  if (args.suite === "sync-regression") results.sync = syncSuite();
  if (args.suite === "native-sync-regression") results.nativeSync = nativeSyncSuite();
  if (args.suite === "textblocks-regression") results.textblocks = textblockSuite();
  if (args.suite === "all" || args.suite === "sync") results.sync = syncSuite();
  if (args.suite === "all" || args.suite === "native-sync") results.nativeSync = nativeSyncSuite();
  if (args.suite === "all" || args.suite === "pdf") results.pdf = pdfCriticalSuite();
  if (args.suite === "all" || args.suite === "textblocks") results.textblocks = textblockSuite();
  console.log(JSON.stringify({ ok: true, suite: args.suite, results }, null, 2));
  return 0;
}

try {
  process.exitCode = main();
} catch (err) {
  console.error(`ERROR: ${err && err.message ? err.message : err}`);
  process.exitCode = 1;
}
