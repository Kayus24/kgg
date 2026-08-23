#!/usr/bin/env node
// Local/static smoke tests for KGG HTML logic.
// No browser, no emulator, no network, no GitHub mutation.

const fs = require("fs");
const path = require("path");
const vm = require("vm");

const ROOT = path.resolve(__dirname, "..");
const HTML_PATH = path.join(ROOT, "kgg-update", "index.html");
const ROOT_PATIENT_HTML_PATH = path.join(ROOT, "index.html");
const KGG_FFLATE_PATH = path.join(ROOT, "vendor", "fflate-0.8.3.js");
const KGG_FORMAT_PATH = path.join(ROOT, "patient-qr-format.js");
const BOOT_MARKER = "  /* KGG_LOGIC_SMOKE_BOOT_BOUNDARY */";

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
    "patient-qr",
    "patient-qr-critical",
    "version-types-critical",
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
  if (bootIndex !== normalizedMain.lastIndexOf(BOOT_MARKER)) fail("KGG boot marker must occur exactly once");
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
  const listeners = new Map();
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
    addEventListener(type, handler) {
      const handlers = listeners.get(type) || [];
      handlers.push(handler);
      listeners.set(type, handlers);
    },
    removeEventListener(type, handler) {
      const handlers = listeners.get(type) || [];
      listeners.set(type, handlers.filter((item) => item !== handler));
    },
    dispatchEvent(event) {
      const next = typeof event === "string" ? { type: event } : (event || {});
      next.target = next.target || this;
      next.currentTarget = this;
      (listeners.get(next.type) || []).slice().forEach((handler) => handler.call(this, next));
      return !next.defaultPrevented;
    },
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
  window.fflate = require(KGG_FFLATE_PATH);

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
    URL,
    MutationObserver,
    location: { href: "file://kgg-html-logic-smoke", hash: "" },
    alert() {},
    btoa(value) {
      return Buffer.from(String(value), "binary").toString("base64");
    },
    atob(value) {
      return Buffer.from(String(value), "base64").toString("binary");
    },
  };
  context.globalThis = context;
  return context;
}

function runInsideApp(testCode) {
  const context = createContext();
  vm.createContext(context);
  vm.runInContext(fs.readFileSync(KGG_FORMAT_PATH, "utf8"), context, { filename: "patient-qr-format.js#logic-smoke" });
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

function versionTypesCriticalSuite() {
  return runInsideApp(`
    const sourceMarker=VERSION;
    const sourceCode=parseKggSourceVersionCode(sourceMarker);
    assert(Number.isSafeInteger(sourceCode)&&sourceCode>0,'current source marker was not parsed');
    assert(parseKggSourceVersionCode('v064')===null,'bare Android-shaped version leaked into source parser');
    assert(parseKggSourceVersionCode('r0424')===null,'web release leaked into source parser');
    assert(parseKggSourceVersionCode('1.0.64-test')===null,'SemVer leaked into source parser');

    assert(parseKggWebReleaseId('r0424')===424,'web release r0424 was not parsed');
    ['r424','v401','1.0.64-test',sourceMarker].forEach(value=>assert(parseKggWebReleaseId(value)===null,'foreign value accepted as web release: '+value));

    assert(parseKggAndroidShellVersion('v401')===401,'Android shell v401 was not parsed');
    ['401','r0424','1.0.64-test',sourceMarker].forEach(value=>assert(parseKggAndroidShellVersion(value)===null,'foreign value accepted as Android shell: '+value));
    assert(parseKggNativeShellCode(401)===401,'numeric native shell was not parsed');
    assert(parseKggNativeShellCode('401')===401,'numeric-string native shell was not parsed');
    assert(parseKggNativeShellCode('v401')===null,'manifest shell leaked into native shell code');

    assert(!!parseKggVersionName('1.0.64-typed-update-versions'),'KGG SemVer was not parsed');
    ['r0424','v401',sourceMarker,'1.0.064-bad'].forEach(value=>assert(parseKggVersionName(value)===null,'foreign/invalid value accepted as SemVer: '+value));
    assert(compareKggVersionNames('1.0.100-next','1.0.99-old')===1,'SemVer numeric comparison regressed');
    assert(compareKggVersionNames('1.0.64-a','1.0.64-b')===0,'KGG labels must not reorder equal SemVer cores');
    assert(compareKggVersionNames('r0425','1.0.64-a')===null,'cross-type comparison must fail closed');

    const sourceNode=document.getElementById('kgg-source-truth');
    const setSourceTruth=(code,versionName)=>{sourceNode.textContent=JSON.stringify({currentVersion:{versionCode:code,versionName}});};
    const currentVersionName='1.0.'+sourceCode+'-logic-smoke';
    setSourceTruth(sourceCode,currentVersionName);
    assert(currentKggVersionIdentity().sourceCode===sourceCode,'consistent source identity was rejected');
    setSourceTruth(sourceCode-1,currentVersionName);
    assert(currentKggVersionIdentity()===null,'source metadata drift did not fail closed');
    setSourceTruth(sourceCode,currentVersionName);

    window.KGG_ROLLOUT_PROFILE='admin';
    const webManifest={
      latestAdminReleaseId:'r0425',
      latestAdminVersion:'1.0.'+(sourceCode+1)+'-next',
      adminUrl:'https://kayus24.github.io/kgg/therapist-app/releases/web/r0425/admin.html',
      releaseNotes:'next web release'
    };
    const webTarget=githubUpdateTargetFromManifest(webManifest);
    assert(webTarget&&webTarget.version===webManifest.latestAdminVersion&&webTarget.webReleaseId==='r0425','newer typed web target missing');
    assert(githubUpdateTargetFromManifest({...webManifest,latestAdminVersion:'1.0.'+sourceCode+'-other'})===null,'equal SemVer core created an update');
    assert(githubUpdateTargetFromManifest({...webManifest,latestAdminVersion:'1.0.'+(sourceCode-1)+'-old'})===null,'older SemVer created an update');
    assert(githubUpdateTargetFromManifest({...webManifest,latestAdminReleaseId:'v402'})===null,'Android shell accepted as web release');
    assert(githubUpdateTargetFromManifest({...webManifest,latestAdminReleaseId:'',adminUrl:'https://example.invalid/no-release/admin.html'})===null,'missing web release identity did not fail closed');
    assert(githubUpdateTargetFromManifest({...webManifest,latestAdminVersion:'r9999'})===null,'web release ID was interpreted as SemVer');
    assert(githubUpdateTargetFromManifest({...webManifest,latestAdminReleaseId:'r0426'})===null,'web release ID/URL mismatch did not fail closed');
    assert(githubUpdateTargetFromManifest({...webManifest,adminUrl:'https://kayus24.github.io/kgg/therapist-app/releases/web/r0425/colleague.html'})===null,'colleague URL accepted for Admin profile');

    window.KGG_ROLLOUT_PROFILE='colleague';
    const colleagueTarget=githubUpdateTargetFromManifest({
      latestVersion:'r0398',
      latestColleagueReleaseId:'r0398',
      latestColleagueVersion:'1.0.'+(sourceCode+1)+'-colleague-next',
      colleagueUrl:'https://kayus24.github.io/kgg/therapist-app/releases/web/r0398/colleague.html'
    });
    assert(colleagueTarget&&colleagueTarget.webReleaseId==='r0398'&&colleagueTarget.url.endsWith('/colleague.html'),'colleague profile target mapping regressed');

    window.KGG_ROLLOUT_PROFILE='admin';
    const channelTarget=githubUpdateTargetFromManifest({channels:{admin:{
      profile:'admin',releaseId:'r0425',versionName:'1.0.'+(sourceCode+1)+'-channel-next',
      url:'https://kayus24.github.io/kgg/therapist-app/releases/web/r0425/admin.html',notes:'channel target'
    }}});
    assert(channelTarget&&channelTarget.webReleaseId==='r0425','canonical channel target mapping regressed');
    assert(githubUpdateTargetFromManifest({channels:{admin:{
      profile:'colleague',releaseId:'r0425',versionName:'1.0.'+(sourceCode+1)+'-channel-next',
      url:'https://kayus24.github.io/kgg/therapist-app/releases/web/r0425/admin.html'
    }}})===null,'wrong channel profile did not fail closed');

    window.KGGAndroidApp={updateStatus(){return JSON.stringify({currentShellVersion:401});}};
    const apkManifest={
      latestAndroidShellVersion:'v402',
      latestAdminAndroidApkUrl:'https://kayus24.github.io/kgg/therapist-app/releases/v402/android/KGG_ANDROID_ADMIN_v402.apk',
      latestAdminAndroidApkSha256:'a'.repeat(64),
      releaseNotes:'next shell'
    };
    const apkTarget=androidApkUpdateTargetFromManifest(apkManifest);
    assert(apkTarget&&apkTarget.version==='v402'&&apkTarget.androidShellVersion==='v402','newer Android shell target missing');
    assert(androidApkUpdateTargetFromManifest({...apkManifest,latestAndroidShellVersion:'v401'})===null,'equal Android shell created an update');
    assert(androidApkUpdateTargetFromManifest({...apkManifest,latestAndroidShellVersion:'r0425'})===null,'web release accepted as Android shell');
    assert(androidApkUpdateTargetFromManifest({...apkManifest,latestAndroidShellVersion:'1.0.402'})===null,'SemVer accepted as Android shell');
    assert(androidApkUpdateTargetFromManifest({...apkManifest,latestAndroidShellVersion:'',latestWebVersion:'v999'})===null,'latestWebVersion replaced a missing Android shell');
    assert(androidApkUpdateTargetFromManifest({...apkManifest,latestAdminAndroidApkSha256:''})===null,'missing APK SHA did not fail closed');
    assert(androidApkUpdateTargetFromManifest({...apkManifest,latestAdminAndroidApkUrl:'https://kayus24.github.io/kgg/therapist-app/releases/v403/android/KGG_ANDROID_ADMIN_v403.apk'})===null,'APK URL shell mismatch did not fail closed');
    assert(androidApkUpdateTargetFromManifest({...apkManifest,latestAdminAndroidApkUrl:'https://kayus24.github.io/kgg/therapist-app/releases/v402/android/KGG_ANDROID_KOLLEGEN_v402.apk'})===null,'colleague APK accepted for Admin profile');
    window.__results={suite:'version-types-critical',sourceCode,webReleaseId:webTarget.webReleaseId,androidShell:apkTarget.androidShellVersion};
  `);
}

function pdfCriticalSuite() {
  return runInsideApp(`
    assert(typeof attachKggPdfExerciseThumbnails==='function','PDF thumbnail attach helper missing');
    assert(typeof createKggPdfThumbnailDataUrl==='function','PDF thumbnail data URL helper missing');
    const snapshot=buildKggPdfSnapshot({exercises:[{id:'ex_plain',name:'Rudern',sets:3,unit:'Wdh',weightUnit:'kg'}],patient:{name:'Test'}}); 
    assert(snapshot.pages[0].slots[0].name==='Rudern','PDF snapshot exercise missing');
    assert(!snapshot.pages[0].slots[0].pdfThumbnail,'PDF snapshot should not invent thumbnails');
    const numberedPlan={exercises:Array.from({length:9},(_,index)=>({id:'ex_'+index,name:'Uebung '+(index+1),sets:3,unit:'Wdh',weightUnit:'kg'}))};
    const classicNumbered=buildKggPdfSnapshot(numberedPlan);
    assert(classicNumbered.pages.length===2,'classic PDF page split missing');
    assert(classicNumbered.pages[0].slots[0].exNo==='EX1','classic PDF first exercise number wrong');
    assert(classicNumbered.pages[1].slots[0].exNo==='EX7','classic PDF page-two number restarted');
    assert(classicNumbered.pages[1].slots[0].globalIndex===7,'classic PDF page-two global index wrong');
    assert(classicNumbered.pages[1].exRange==='EX7-EX9','classic PDF page-two range wrong');
    const largeNumbered=buildKggPdfSnapshot(numberedPlan,{layout:'large-single-row'});
    assert(largeNumbered.pages.length===3,'large-print PDF page split missing');
    assert(largeNumbered.pages[0].slots[2].exNo==='EX3','large-print PDF page-one number wrong');
    assert(largeNumbered.pages[1].slots[0].exNo==='EX4','large-print PDF page-two number restarted');
    assert(largeNumbered.pages[1].slots[2].exNo==='EX6','large-print PDF page-two sequence wrong');
    assert(largeNumbered.pages[1].exRange==='EX4-EX6','large-print PDF page-two range wrong');
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

function patientQrCriticalSuite() {
  const therapistHtml = fs.readFileSync(HTML_PATH, "utf8");
  const rootPatientHtml = fs.readFileSync(ROOT_PATIENT_HTML_PATH, "utf8");
  assert(rootPatientHtml.includes("function parseQueryPlan()"), "root patient app must parse ?plan query links directly");
  assert(rootPatientHtml.includes("new URLSearchParams(location.search)"), "root patient app must read location.search");
  assert(rootPatientHtml.includes("source:source||'link'"), "root patient app should persist the plan source");
  assert(rootPatientHtml.includes("planSource='query'"), "root patient app must prioritize query-plan imports over stored plans");
  assert(!rootPatientHtml.includes("media-inline-bundle-7"), "root patient app still references old media-inline-bundle-7 cache marker");
  assert(therapistHtml.includes('id="patientRootFallback"') && therapistHtml.includes('id="patientRootAppAddress"'), "therapist output must offer the payload-free public app-address fallback");
  return runInsideApp(`
    assert(typeof buildPatientShareFromCurrentPlan==='function','patient share builder missing');
    assert(typeof makeKggH2ShareUrl==='function','KGGH2 share URL helper missing');
    assert(typeof makeKggH3ShareUrl==='function','KGGH3 share URL helper missing');
    assert(window.KGGPlanFormat&&typeof window.KGGPlanFormat.decodePlanText==='function','local KGGH3 codec missing in therapist app');
    assert(typeof KGG_PATIENT_LATEST_BASE_URL==='string','latest patient base constant missing');
    assert(KGG_PATIENT_LATEST_BASE_URL==='https://kayus24.github.io/kgg/','unexpected latest patient base URL: '+KGG_PATIENT_LATEST_BASE_URL);
    assert(patientBaseUrl===KGG_PATIENT_LATEST_BASE_URL,'patientBaseUrl default does not use latest base');
    assert(typeof patientRootAppUrl==='function','small public app-address fallback helper missing');
    assert(patientRootAppUrl()===KGG_PATIENT_LATEST_BASE_URL && !patientRootAppUrl().includes('?plan='),'app-address fallback must contain no personal plan payload');
    assert(!patientBaseUrl.includes('media-inline-bundle-7'),'old patient root bundle leaked into default patient base URL');
    const plan={
      id:'patient_qr_smoke',
      updatedAt:'2026-07-01T00:00:00.000Z',
      patient:{name:'QR Test',date:'2026-07-01'},
      exercises:[ensureUiExerciseShape({id:'ex_qr_1',localId:'ex_qr_1',name:'Rudern',sets:3,unit:'Wdh',weightUnit:'kg',startMetric:'12',startLoad:'30'})]
    };
    const share=buildPatientShareFromCurrentPlan(plan,{ttlSeconds:3600});
    assert(share.shareable===true,'patient share should be shareable with latest public base');
    assert(share.url.startsWith('https://kayus24.github.io/kgg/?plan=KGGH3%3A'),'new patient URL must use KGGH3: '+share.url);
    assert(!share.url.includes('kgg-update/index.html'),'patient URL must not use therapist/update HTML path: '+share.url);
    assert(!share.url.includes('/therapist-app/'),'patient URL must not use therapist release path: '+share.url);
    assert(!share.url.includes('/releases/'),'patient URL must not use immutable therapist release path: '+share.url);
    assert(!share.url.includes('media-inline-bundle-7'),'patient URL still points to old root bundle: '+share.url);
    const parsed=new URL(share.url);
    const generatedCode=parsed.searchParams.get('plan');
    assert(/^KGGH3:/i.test(generatedCode),'generated patient URL has no KGGH3 code');
    const decoded=convertKggH2PayloadToPatientPayload(window.KGGPlanFormat.decodePlanText(generatedCode).raw);
    assert(decoded.plan.length===1 && decoded.plan[0].name==='Rudern','patient QR payload decode mismatch');
    const legacy=makeKggH2ShareUrl(patientBaseUrl,share.publicPayload);
    assert(legacy.includes('?plan=KGGH2%3A'),'legacy KGGH2 helper must remain available');
    const legacyCode=new URL(legacy).searchParams.get('plan');
    assert(convertKggH2PayloadToPatientPayload(window.KGGPlanFormat.decodePlanText(legacyCode).raw).plan[0].name==='Rudern','legacy KGGH2 decode mismatch');
    window.__results={suite:'patient-qr-critical',base:patientBaseUrl,urlPrefix:share.url.split('?')[0],format:'KGGH3',exercise:decoded.plan[0].name};
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

    save=function(){localStorage.setItem(storageKey,JSON.stringify(state));};
    const hybridText=[
      'Beinpresse, Dips, Abduktion Maschine, Adduktion Maschine, Latziehen',
      'Satz 1: 12 Wdh @ 30 kg',
      'Satz 2: 12 Wdh @ 30 kg'
    ].join(String.fromCharCode(10));
    const hybridNames=['Beinpresse','Dips','Abduktion Maschine','Adduktion Maschine','Latziehen'];
    input.value=hybridText;
    syncPlanFromTextInput('logic_smoke_textblocks_hybrid_live_master');
    assert(state.plan.length===hybridNames.length,'hybrid text collapsed state.plan to '+state.plan.length+' exercise(s)');
    assert(hybridNames.every(name=>state.plan.some(ex=>ex.name===name)),'hybrid text lost state.plan exercise(s): '+state.plan.map(ex=>ex.name).join('|'));
    const hybridStore=window.KGGDataStore.getCurrentPlan();
    assert(hybridStore && hybridStore.exercises.length===hybridNames.length,'hybrid text collapsed KGGDataStore.currentPlan');
    assert(hybridNames.every(name=>hybridStore.exercises.some(ex=>ex.name===name)),'hybrid text lost store exercise(s)');
    const persistedState=JSON.parse(localStorage.getItem(storageKey)||'{}');
    assert(Array.isArray(persistedState.plan) && persistedState.plan.length===hybridNames.length,'hybrid text persisted a collapsed plan');

    const richPlan=JSON.parse(JSON.stringify(state.plan));
    richPlan[0].media=[{id:'logic_smoke_media',type:'image',name:'beinpresse.jpg'}];
    localStorage.setItem(storageKey,JSON.stringify({...state,plan:richPlan,planText:hybridText}));
    state={...state,plan:[],planText:'',liveDraftId:null};
    load();
    assert(restorePlanFromSavedLiveText()===true,'matching saved planText was not recognised at boot');
    assert(state.plan[0].media[0].id==='logic_smoke_media','matching saved planText discarded rich saved plan state');

    const staleExercise=JSON.parse(JSON.stringify(state.plan[0]));
    localStorage.setItem(storageKey,JSON.stringify({...state,plan:[staleExercise],planText:hybridText}));
    state={...state,plan:[],planText:'',liveDraftId:null};
    window.KGGDataStore.setCurrentPlan({exercises:[staleExercise]},'logic_smoke_boot_stale_store');
    let bootRecoverySaveCalls=0;
    const saveBeforeBootRecovery=save;
    save=function(){bootRecoverySaveCalls+=1;localStorage.setItem(storageKey,JSON.stringify(state));};
    load();
    assert(restorePlanFromSavedLiveText()===true,'saved valid planText was not restored at boot');
    assert(bootRecoverySaveCalls===1,'valid boot recovery did not persist exactly once');
    const repairedBootState=JSON.parse(localStorage.getItem(storageKey)||'{}');
    assert(Array.isArray(repairedBootState.plan)&&repairedBootState.plan.length===hybridNames.length,'valid boot recovery did not persist the repaired full plan');
    syncStatePlanToStore('logic_smoke_boot_saved_live_text');
    restoreSavedLiveTextInput();
    assert(state.plan.length===hybridNames.length,'saved valid planText did not repair collapsed boot state');
    assert(hybridNames.every(name=>state.plan.some(ex=>ex.name===name)),'saved valid planText lost boot exercise(s)');
    assert(window.KGGDataStore.getCurrentPlan().exercises.length===hybridNames.length,'saved valid planText did not repair KGGDataStore.currentPlan');
    assert(input.value===hybridText,'saved valid planText was overwritten at boot');

    // A second boot reads the repaired local state directly and must not
    // repeat a recovery save.
    state={...state,plan:[],planText:'',liveDraftId:null};
    bootRecoverySaveCalls=0;
    load();
    assert(restorePlanFromSavedLiveText()===true,'repaired saved planText was not recognised after reboot');
    assert(bootRecoverySaveCalls===0,'matching repaired boot state was persisted again');
    assert(state.plan.length===hybridNames.length,'reboot lost the repaired full plan');

    const incompleteText='Beinpresse, Dip';
    const lastValidPlan=JSON.parse(JSON.stringify(state.plan));
    localStorage.setItem(storageKey,JSON.stringify({...state,plan:lastValidPlan,planText:incompleteText}));
    state={...state,plan:[staleExercise],planText:'',liveDraftId:null};
    window.KGGDataStore.setCurrentPlan({exercises:[staleExercise]},'logic_smoke_boot_incomplete_store');
    bootRecoverySaveCalls=0;
    load();
    assert(restorePlanFromSavedLiveText()===true,'saved incomplete planText was not recognised at boot');
    assert(bootRecoverySaveCalls===0,'incomplete boot text must not persist a fallback state');
    const incompletePersistedState=JSON.parse(localStorage.getItem(storageKey)||'{}');
    assert(incompletePersistedState.planText===incompleteText,'incomplete boot text was changed in localStorage');
    assert(Array.isArray(incompletePersistedState.plan)&&incompletePersistedState.plan.length===hybridNames.length,'incomplete boot text rewrote the last valid local plan');
    syncStatePlanToStore('logic_smoke_boot_incomplete_live_text');
    restoreSavedLiveTextInput();
    assert(state.plan.length===hybridNames.length,'saved incomplete planText destroyed the last valid structured plan');
    assert(window.KGGDataStore.getCurrentPlan().exercises.length===hybridNames.length,'saved incomplete planText overwrote KGGDataStore.currentPlan');
    assert(input.value===incompleteText,'saved incomplete planText was overwritten at boot');
    save=saveBeforeBootRecovery;

    const outputPlan=getCurrentPlanForOutput('logic_smoke_textblocks_hybrid_output');
    assert(outputPlan.exercises.length===hybridNames.length,'output state collapsed hybrid plan');
    const pdfSnapshot=buildKggPdfSnapshot(outputPlan);
    const pdfNames=pdfSnapshot.pages.flatMap(page=>page.slots.filter(slot=>!slot.empty).map(slot=>slot.name));
    assert(hybridNames.every(name=>pdfNames.includes(name)),'PDF snapshot lost hybrid exercise(s): '+pdfNames.join('|'));
    const patientShare=buildPatientShareFromCurrentPlan(outputPlan,{ttlSeconds:3600});
    assert(patientShare.payload.plan.length===hybridNames.length,'patient share lost hybrid exercise(s)');
    assert(hybridNames.every(name=>patientShare.payload.plan.some(ex=>ex.name===name)),'patient share names lost hybrid exercise(s)');

    input.value='Beinpresse, D';
    syncPlanFromTextInput('logic_smoke_textblocks_partial_name');
    assert(state.plan.length===hybridNames.length,'short partial name destroyed the last valid plan');
    assert(window.KGGDataStore.getCurrentPlan().exercises.length===hybridNames.length,'short partial name destroyed currentPlan');
    assert(input.value==='Beinpresse, D','short partial name should remain editable text');
    input.value='Beinpresse, Dip';
    syncPlanFromTextInput('logic_smoke_textblocks_known_partial_name');
    assert(state.plan.length===hybridNames.length,'known partial name destroyed the last valid plan');
    assert(window.KGGDataStore.getCurrentPlan().exercises.length===hybridNames.length,'known partial name destroyed currentPlan');
    assert(JSON.parse(localStorage.getItem(storageKey)||'{}').plan.length===hybridNames.length,'known partial name persisted a reduced plan');
    assert(JSON.parse(localStorage.getItem(storageKey)||'{}').planText==='Beinpresse, Dip','partial live text was not retained for the next boot');

    input.value='Dips, Dips Neu, Beinpresse';
    syncPlanFromTextInput('logic_smoke_textblocks_dips_coexist');
    assert(state.plan.map(ex=>ex.name).join('|')==='Dips|Dips Neu|Beinpresse','Dips and Dips Neu cannot coexist: '+state.plan.map(ex=>ex.name).join('|'));
    const dipsId=state.plan[0].localId;
    const dipsNeuId=state.plan[1].localId;
    const legpressId=state.plan[2].localId;
    assert(dipsId!==dipsNeuId,'Dips and Dips Neu reused one exercise identity');
    input.value='Dips Neu, Dips, Beinpresse';
    syncPlanFromTextInput('logic_smoke_textblocks_dips_reorder');
    assert(state.plan.map(ex=>ex.name).join('|')==='Dips Neu|Dips|Beinpresse','Dips/Dips Neu reorder was blocked: '+state.plan.map(ex=>ex.name).join('|'));
    assert(state.plan[0].localId===dipsNeuId&&state.plan[1].localId===dipsId&&state.plan[2].localId===legpressId,'Dips/Dips Neu reorder changed exercise identities');
    input.value='Dips Neu umbenannt, Dips, Beinpresse';
    syncPlanFromTextInput('logic_smoke_textblocks_dips_rename');
    assert(state.plan.map(ex=>ex.name).join('|')==='Dips Neu umbenannt|Dips|Beinpresse','Dips/Dips Neu rename was blocked: '+state.plan.map(ex=>ex.name).join('|'));
    assert(state.plan[0].localId===dipsNeuId&&state.plan[1].localId===dipsId,'Dips/Dips Neu rename changed exercise identities');
    input.value='Dips, Beinpresse';
    syncPlanFromTextInput('logic_smoke_textblocks_dips_delete');
    assert(state.plan.map(ex=>ex.name).join('|')==='Dips|Beinpresse','Dips/Dips Neu delete was blocked: '+state.plan.map(ex=>ex.name).join('|'));
    assert(state.plan[0].localId===dipsId&&state.plan[1].localId===legpressId,'Dips/Dips Neu delete changed remaining exercise identities');
    input.value='Dips, Beinpresse, ';
    syncPlanFromTextInput('logic_smoke_textblocks_dips_trailing_comma');
    input.value='Dip, Beinpresse, ';
    input.dispatchEvent({type:'input',inputType:'deleteContentBackward',data:null});
    assert(state.plan.map(ex=>ex.name).join('|')==='Dips|Beinpresse','temporary Dips to Dip edit destroyed the valid structured plan');
    assert(state.planText==='Dip, Beinpresse, ','temporary short edit did not remain live text');
    assert(window.KGGDataStore.getCurrentPlan().exercises[0].name==='Dips','temporary short edit overwrote KGGDataStore');
    input.dispatchEvent({type:'change'});
    assert(state.plan.map(ex=>ex.name).join('|')==='Dip|Beinpresse','deliberate final Dips to Dip rename was blocked');
    assert(state.plan[0].localId===dipsId&&state.plan[1].localId===legpressId,'deliberate short rename changed remaining exercise identities');
    const committedShortRename=JSON.parse(localStorage.getItem(storageKey)||'{}');
    assert(committedShortRename.planText==='Dip, Beinpresse, ','deliberate short rename did not persist live text');
    assert(committedShortRename.plan[0].name==='Dip','deliberate short rename did not persist the structured plan');
    state={...state,plan:[],planText:'',liveDraftId:null};
    load();
    assert(restorePlanFromSavedLiveText()===true,'final short rename was not recognised after reboot');
    assert(state.plan.map(ex=>ex.name).join('|')==='Dip|Beinpresse','final short rename reverted after reboot');
    window.__results={suite:'textblocks-critical',names,hybridNames};
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
    console.log("Usage: node release-pipeline/kgg_html_logic_smoke.js [--suite all|sync|sync-critical|sync-regression|native-sync|native-sync-regression|pdf|pdf-critical|patient-qr|patient-qr-critical|version-types-critical|textblocks|textblocks-critical|textblocks-regression]");
    return 0;
  }
  const results = {};
  if (args.suite === "sync-critical") results.syncCritical = syncCriticalSuite();
  if (args.suite === "textblocks-critical") results.textblocksCritical = textblockCriticalSuite();
  if (args.suite === "pdf-critical") results.pdfCritical = pdfCriticalSuite();
  if (args.suite === "patient-qr-critical") results.patientQrCritical = patientQrCriticalSuite();
  if (args.suite === "all" || args.suite === "version-types-critical") results.versionTypesCritical = versionTypesCriticalSuite();
  if (args.suite === "sync-regression") results.sync = syncSuite();
  if (args.suite === "native-sync-regression") results.nativeSync = nativeSyncSuite();
  if (args.suite === "textblocks-regression") results.textblocks = textblockSuite();
  if (args.suite === "all" || args.suite === "sync") results.sync = syncSuite();
  if (args.suite === "all" || args.suite === "native-sync") results.nativeSync = nativeSyncSuite();
  if (args.suite === "all" || args.suite === "pdf") results.pdf = pdfCriticalSuite();
  if (args.suite === "all" || args.suite === "patient-qr") results.patientQr = patientQrCriticalSuite();
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
