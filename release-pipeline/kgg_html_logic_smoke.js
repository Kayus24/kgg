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
  if (!["all", "sync", "textblocks"].includes(out.suite)) {
    fail("--suite must be one of: all, sync, textblocks");
  }
  return out;
}

function readMainAppScript() {
  const html = fs.readFileSync(HTML_PATH, "utf8");
  const scripts = [...html.matchAll(/<script(?:\s[^>]*)?>([\s\S]*?)<\/script>/gi)].map((match) => match[1]);
  const main = scripts.find((script) => script.includes("const VERSION='KGG_GITHUB_UPDATE"));
  if (!main) fail("KGG main app script not found in kgg-update/index.html");
  const bootIndex = main.indexOf(BOOT_MARKER);
  if (bootIndex < 0) fail("KGG boot marker not found; update kgg_html_logic_smoke.js");
  return main.slice(0, bootIndex);
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

function textblockSuite() {
  return runInsideApp(`
    const input=document.__nodes.exerciseInput;
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
      'Kniebeuger Maschine',
      'Satz 1: 12 Wdh @ 25 kg',
      '',
      'Kniestrecker Maschine',
      'Satz 1: 12 Wdh @ 23 kg'
    ].join('\\n');
    syncPlanFromTextInput('logic_smoke_textblocks');
    const names=state.plan.map(ex=>ex.name);
    assert(state.plan.length===8,'structured text block should create 8 exercises, got '+state.plan.length+' '+names.join('|'));
    assert(!names.some(name=>/^Satz\\s+\\d/i.test(name)),'structured text block created Satz cards: '+names.join('|'));
    ['Beinpresse','Dips','Abduktion Maschine','Adduktion Maschine','Latziehen','Ergometer / Bike','Kniebeuger Maschine','Kniestrecker Maschine'].forEach(name=>{
      assert(names.includes(name),'missing structured exercise '+name+' in '+names.join('|'));
    });
    const legpress=state.plan.find(ex=>ex.name==='Beinpresse');
    assert(legpress.startMetric==='12','Beinpresse reps not preserved');
    assert(legpress.startLoad==='42','Beinpresse load not preserved');
    assert(legpress.weightUnit==='kg','Beinpresse kg unit not preserved');
    const add=state.plan.find(ex=>ex.name==='Adduktion Maschine');
    assert(add.startLoad==='2' && add.weightUnit==='bar','bar unit not preserved');
    const bike=state.plan.find(ex=>ex.name==='Ergometer / Bike');
    assert(bike.startMetric==='5 min' && bike.unit==='Zeit','time metric not preserved');
    assert(bike.startLoad==='80' && bike.weightUnit==='Watt','Watt unit not preserved');

    input.value='Beinpresse, Latziehen';
    syncPlanFromTextInput('logic_smoke_comma');
    const commaNames=state.plan.map(ex=>ex.name);
    assert(commaNames.length===2 && commaNames[0]==='Beinpresse' && commaNames[1]==='Latziehen','normal comma input regressed: '+commaNames.join('|'));

    const applyText=scanResultToApplyText({exercises:[{name:'Beinpresse',sets:[{reps:12,load:42},{reps:12,load:42},{reps:15,load:42}]},{name:'Dips',sets:[{reps:15,load:30}]}]});
    assert(applyText==='Beinpresse, Dips','structured scan apply text regressed: '+applyText);
    window.__results={suite:'textblocks',structuredNames:names,commaNames,applyText};
  `);
}

function main() {
  const args = parseArgs(process.argv.slice(2));
  if (args.help) {
    console.log("Usage: node release-pipeline/kgg_html_logic_smoke.js [--suite all|sync|textblocks]");
    return 0;
  }
  const results = {};
  if (args.suite === "all" || args.suite === "sync") results.sync = syncSuite();
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
