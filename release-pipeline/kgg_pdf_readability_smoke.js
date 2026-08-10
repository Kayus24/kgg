#!/usr/bin/env node
// Grossdruck PDF readability smoke.
// Generates real PDFs, renders pages with Poppler and creates blurred myopia previews.

const fs = require("fs");
const path = require("path");
const vm = require("vm");
const { spawnSync } = require("child_process");

const ROOT = path.resolve(__dirname, "..");
const HTML_PATH = path.join(ROOT, "kgg-update", "index.html");
const OUT_DIR = path.join(ROOT, "tmp", "pdfs", "grossdruck-readability");
const BOOT_MARKER = [
  "  installKggV383UiFlowStability();",
  "  installKggV388AndroidFlowFixes();",
  "  load();",
].join("\n");

const THUMBNAIL_JPEG =
  "data:image/jpeg;base64,/9j/4AAQSkZJRgABAQAAAQABAAD/2wBDAP//////////////////////////////////////////////////////////////////////////////////////2wBDAf//////////////////////////////////////////////////////////////////////////////////////wAARCAABAAEDASIAAhEBAxEB/8QAFQABAQAAAAAAAAAAAAAAAAAAAAX/xAAUEAEAAAAAAAAAAAAAAAAAAAAA/9oADAMBAAIQAxAAAAH/xAAUEAEAAAAAAAAAAAAAAAAAAAAA/9oACAEBAAEFAqf/xAAUEQEAAAAAAAAAAAAAAAAAAAAA/9oACAEDAQE/ASP/xAAUEQEAAAAAAAAAAAAAAAAAAAAA/9oACAECAQE/ASP/xAAUEAEAAAAAAAAAAAAAAAAAAAAA/9oACAEBAAY/Ar//xAAUEAEAAAAAAAAAAAAAAAAAAAAA/9oACAEBAAE/IV//2gAMAwEAAgADAAAAEP/EFBQRAQAAAAAAAAAAAAAAAAAAARD/2gAIAQMBAT8QH//EFBQRAQAAAAAAAAAAAAAAAAAAARD/2gAIAQIBAT8QH//EFBQRAQAAAAAAAAAAAAAAAAAAARD/2gAIAQEAAT8QH//Z";

function fail(message) {
  throw new Error(message);
}

function assert(condition, message) {
  if (!condition) fail(message);
}

function readAppPrelude() {
  const html = fs.readFileSync(HTML_PATH, "utf8");
  const scripts = [...html.matchAll(/<script(\s[^>]*)?>([\s\S]*?)<\/script>/gi)]
    .filter((match) => {
      const attrs = String(match[1] || "");
      const typeMatch = attrs.match(/\btype=["']?([^"'\s>]+)/i);
      if (!typeMatch) return true;
      return /(?:java|ecma)script/i.test(typeMatch[1]);
    })
    .map((match) => match[2]);
  const chunks = [];
  let foundMain = false;
  for (const script of scripts) {
    if (script.includes("const VERSION='KGG_GITHUB_UPDATE")) {
      const normalized = script.replace(/\r\n/g, "\n");
      const bootIndex = normalized.indexOf(BOOT_MARKER);
      if (bootIndex < 0) fail("KGG boot marker not found; update kgg_pdf_readability_smoke.js");
      chunks.push(normalized.slice(0, bootIndex));
      foundMain = true;
      break;
    }
    chunks.push(script.replace(/\r\n/g, "\n"));
  }
  if (!foundMain) fail("KGG main app script not found in kgg-update/index.html");
  return chunks.join("\n;\n");
}

function classList() {
  const values = new Set();
  return {
    add(...items) { items.forEach((item) => values.add(String(item))); },
    remove(...items) { items.forEach((item) => values.delete(String(item))); },
    toggle(item, force) {
      const key = String(item);
      if (force === true) { values.add(key); return true; }
      if (force === false) { values.delete(key); return false; }
      if (values.has(key)) { values.delete(key); return false; }
      values.add(key);
      return true;
    },
    contains(item) { return values.has(String(item)); },
  };
}

function fakeNode(id) {
  return {
    id,
    value: "",
    textContent: "",
    innerHTML: "",
    className: "",
    href: "",
    download: "",
    style: { setProperty() {}, removeProperty() {} },
    dataset: {},
    classList: classList(),
    children: [],
    files: [],
    scrollHeight: 0,
    scrollTop: 0,
    selectionStart: 0,
    appendChild(child) { this.children.push(child); return child; },
    replaceChildren(...children) { this.children = children; },
    addEventListener() {},
    removeEventListener() {},
    setAttribute() {},
    removeAttribute() {},
    focus() {},
    blur() {},
    select() {},
    click() {},
    remove() {},
    getBoundingClientRect() { return { top: 0, left: 0, right: 0, bottom: 0, width: 0, height: 0 }; },
    querySelector() { return null; },
    querySelectorAll() { return []; },
  };
}

function createContext() {
  const nodes = {};
  const document = {
    __nodes: nodes,
    body: fakeNode("body"),
    documentElement: fakeNode("html"),
    activeElement: null,
    getElementById(id) {
      if (!this.__nodes[id]) this.__nodes[id] = fakeNode(id);
      return this.__nodes[id];
    },
    querySelector() { return null; },
    querySelectorAll() { return []; },
    createElement(tag) { return fakeNode(tag); },
    createTextNode(text) { return { textContent: String(text || "") }; },
    addEventListener() {},
    removeEventListener() {},
  };
  const localStorage = {
    getItem() { return null; },
    setItem() {},
    removeItem() {},
    clear() {},
  };
  class MutationObserver { observe() {} disconnect() {} }
  const crypto = {
    getRandomValues(array) {
      for (let i = 0; i < array.length; i += 1) array[i] = (i * 17 + 23) & 255;
      return array;
    },
  };
  const navigator = { userAgent: "kgg-pdf-readability-smoke", language: "de-DE", onLine: true };
  const screen = { width: 1024, height: 1366, orientation: { type: "portrait-primary" } };
  const objectUrls = new Map();
  const window = {
    document,
    localStorage,
    navigator,
    crypto,
    screen,
    innerWidth: 1024,
    innerHeight: 1366,
    devicePixelRatio: 1,
    KGG_PATIENT_BASE_URL: "",
    addEventListener() {},
    removeEventListener() {},
    dispatchEvent() {},
    matchMedia() { return { matches: false, addEventListener() {}, removeEventListener() {} }; },
  };
  const URLShim = Object.assign(URL, {
    createObjectURL(value) {
      const key = "blob:kgg-readability-" + objectUrls.size;
      objectUrls.set(key, value);
      return key;
    },
    revokeObjectURL(key) { objectUrls.delete(key); },
  });
  Object.assign(window, { TextEncoder, TextDecoder, URL: URLShim, Blob });
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
    URL: URLShim,
    Blob,
    screen,
    MutationObserver,
    location: { href: "file://kgg-pdf-readability-smoke", hash: "", search: "" },
    alert() {},
    requestAnimationFrame(callback) { return setTimeout(() => callback(Date.now()), 16); },
    cancelAnimationFrame(handle) { clearTimeout(handle); },
    btoa(value) { return Buffer.from(String(value), "binary").toString("base64"); },
    atob(value) { return Buffer.from(String(value), "base64").toString("binary"); },
  };
  context.globalThis = context;
  return context;
}

function runInsideApp(testCode) {
  const context = createContext();
  vm.createContext(context);
  const source = `${readAppPrelude()}
  function assert(condition,message){ if(!condition) throw new Error(message||'assertion failed'); }
  render=function(){};
  save=function(){};
  persistCustomBank=function(){};
  persistDeletedBankIds=function(){};
  setScanStatus=function(message){ window.__scanStatus=message; };
  ${testCode}
})();`;
  vm.runInContext(source, context, { filename: "kgg-update/index.html#pdf-readability-smoke" });
  return context.window.__results || {};
}

function exerciseSet(count) {
  const names = [
    "Beinpresse sitzend kontrollierte Knieachse",
    "Kniestrecker Maschine langsam ohne Schwung",
    "Rudern am Kabelzug aufrecht mit Schulterblattzug",
    "Seitheben Kurzhantel beidseitig sauber",
    "Latziehen weiter Griff zur Brust",
    "Fahrrad Ergometer Intervall moderat",
    "Bauch gegen Blutdruckmanschette",
    "Kreuzheben Technik leicht mit Stange",
    "Step-up flache Stufe Knie stabil",
  ];
  return names.slice(0, count).map((name, index) => ({
    id: `readability_${index + 1}`,
    name,
    sets: 3,
    side: index % 3 === 0 ? "LR" : "BI",
    unit: "Wdh",
    metricUnit: "Wdh",
    weightUnit: "kg",
    loadUnit: "kg",
    startLoad: String(15 + index * 5),
    startMetric: String(8 + (index % 4)),
    machine: index % 2 === 0 ? "Matrix" : "Technogym",
  }));
}

function buildCase(caseDef) {
  const exercises = exerciseSet(caseDef.count);
  const testCode = `
    const plan={id:${JSON.stringify(caseDef.id)},title:'Grossdruck Lesbarkeit',patient:{name:'Kurzsicht Test',date:'2026-07-07',therapist:'KGG'},exercises:${JSON.stringify(exercises)}};
    const snapshot=buildKggPdfSnapshot(plan,{layout:'large-single-row'});
    const slots=(snapshot.pages||[]).flatMap(page=>page.slots||page.exercises||[]);
    slots.forEach((slot,idx)=>{
      if(slot && !slot.empty && ${caseDef.withImages ? "true" : "false"}){
        slot.pdfThumbnail={kind:'kgg-pdf-exercise-thumbnail',sourceId:'smoke-'+idx,mime:'image/jpeg',width:150,height:110,dataUrl:${JSON.stringify(THUMBNAIL_JPEG)}};
        slot.hasPdfThumbnail=true;
      }
    });
    snapshot.thumbnailCount=slots.filter(slot=>slot&&slot.pdfThumbnail).length;
    snapshot.thumbnailMode=${JSON.stringify(caseDef.withImages ? "readability-smoke-inline-jpeg" : "none")};
    function makeMeasureDoc(){
      const calls=[];
      let page=1,currentFontSize=10,currentFontStyle='normal';
      return {
        calls,
        internal:{pageSize:{width:210,height:297,getWidth:()=>210,getHeight:()=>297}},
        addPage(){page++;calls.push({op:'addPage',page});return this;},
        setFont(_family,style){currentFontStyle=style||'normal';calls.push({op:'font',page,style:currentFontStyle});return this;},
        setFontSize(size){currentFontSize=Number(size)||currentFontSize;calls.push({op:'fontSize',page,size:currentFontSize,style:currentFontStyle});return this;},
        setLineWidth(value){calls.push({op:'lineWidth',page,value:Number(value)||0});return this;},
        setDrawColor(){return this;},
        setTextColor(){return this;},
        setFillColor(){return this;},
        rect(x,y,w,h,style){calls.push({op:'rect',page,x,y,w,h,style:style||''});return this;},
        roundedRect(x,y,w,h){calls.push({op:'roundedRect',page,x,y,w,h});return this;},
        line(x1,y1,x2,y2){calls.push({op:'line',page,x1,y1,x2,y2});return this;},
        text(text,x,y,opts){calls.push({op:'text',page,text:String(text==null?'':text),x,y,size:currentFontSize,style:currentFontStyle,align:opts&&opts.align||''});return this;},
        addImage(data,format,x,y,w,h){calls.push({op:'addImage',page,data:String(data||'').slice(0,32),format,x,y,w,h});return this;}
      };
    }
    const measureDoc=makeMeasureDoc();
    drawKggPdfLayoutV1(measureDoc,snapshot);
    const JsPdfCtor=(window.jspdf&&window.jspdf.jsPDF)||window.jsPDF;
    assert(!!JsPdfCtor,'Offline jsPDF runtime missing');
    const doc=new JsPdfCtor({orientation:'portrait',unit:'mm',format:'a4'});
    drawKggPdfLayoutV1(doc,snapshot);
    assert(typeof doc._buildPdf==='function','Offline PDF builder missing');
    window.__results={caseId:${JSON.stringify(caseDef.id)},snapshot,calls:measureDoc.calls,pdfBinary:doc._buildPdf()};
  `;
  return runInsideApp(testCode);
}

function min(values) {
  return values.length ? Math.min(...values) : 0;
}

function analyzeCase(result, caseDef) {
  const calls = result.calls || [];
  const texts = calls.filter((call) => call.op === "text");
  const images = calls.filter((call) => call.op === "addImage");
  const titleSizes = texts
    .filter((call) => /^EX[0-9]+\b/.test(call.text))
    .map((call) => call.size);
  const metaSizes = texts
    .filter((call) => /(S.tze|Saetze|Sätze|Wiederholungen|Startlast|Startwert|beidseitig|links\/rechts)/i.test(call.text))
    .filter((call) => !/^T1-T6\b/.test(call.text))
    .filter((call) => !/^#EX\|/.test(call.text))
    .map((call) => call.size);
  const tableSizes = texts
    .filter((call) => /^(Satz [123]|S[123]|Tag|T[1-6]|kg|Wdh|li kg|li Wdh|re kg|re Wdh|Schmerz|1-10)$/i.test(call.text.trim()))
    .map((call) => call.size);

  const failures = [];
  const titleMin = min(titleSizes);
  const metaMin = min(metaSizes);
  const tableMin = min(tableSizes);
  if (titleMin < 14) failures.push(`Uebungsname zu klein: ${titleMin}pt < 14pt`);
  if (metaMin < 8.5) failures.push(`Meta-Zeile zu klein: ${metaMin}pt < 8.5pt`);
  if (tableMin < 7) failures.push(`Tabellenlabels zu klein: ${tableMin}pt < 7pt`);
  if (caseDef.withImages && images.length < Math.min(caseDef.count, 3)) {
    failures.push(`Bilder fehlen: ${images.length} addImage-Aufrufe`);
  }
  for (const image of images) {
    if (image.x < 0 || image.y < 0 || image.x + image.w > 210 || image.y + image.h > 297) {
      failures.push(`Bild ausserhalb A4: ${JSON.stringify(image)}`);
    }
    if (image.w < 30 || image.h < 20) {
      failures.push(`Bild zu klein: ${Math.round(image.w * 10) / 10}x${Math.round(image.h * 10) / 10}mm`);
    }
    const overlaps = texts.filter((text) =>
      text.page === image.page &&
      text.y >= image.y - 1 &&
      text.y <= image.y + image.h + 1 &&
      text.x >= image.x - 2
    );
    if (overlaps.length) failures.push(`Text/Bild-Ueberlappung nahe Seite ${image.page}: ${overlaps[0].text}`);
  }
  const pageCount = result.snapshot && result.snapshot.pageCount || 0;
  const expectedPages = Math.ceil(caseDef.count / 3);
  if (pageCount !== expectedPages) failures.push(`Unerwartete Seitenzahl: ${pageCount}, erwartet ${expectedPages}`);

  return {
    id: caseDef.id,
    titleMin,
    metaMin,
    tableMin,
    imageCount: images.length,
    pageCount,
    expectedPages,
    failures,
  };
}

function writeBinaryString(file, value) {
  const text = String(value || "");
  const bytes = Buffer.alloc(text.length);
  for (let i = 0; i < text.length; i += 1) bytes[i] = text.charCodeAt(i) & 255;
  fs.writeFileSync(file, bytes);
}

function resolveTool(envName, names) {
  if (process.env[envName] && fs.existsSync(process.env[envName])) return process.env[envName];
  const bundled = path.join(
    process.env.USERPROFILE || process.env.HOME || "",
    ".cache",
    "codex-runtimes",
    "codex-primary-runtime",
    "dependencies",
    "bin"
  );
  const nativePopplerBin = path.join(
    process.env.USERPROFILE || process.env.HOME || "",
    ".cache",
    "codex-runtimes",
    "codex-primary-runtime",
    "dependencies",
    "native",
    "poppler",
    "Library",
    "bin"
  );
  if (process.platform === "win32") {
    for (const name of names) {
      const base = name.replace(/\.cmd$/i, "").replace(/\.exe$/i, "");
      const candidate = path.join(nativePopplerBin, `${base}.exe`);
      if (fs.existsSync(candidate)) return candidate;
    }
  }
  for (const name of names) {
    const candidate = path.join(bundled, process.platform === "win32" && !name.endsWith(".cmd") ? `${name}.cmd` : name);
    if (fs.existsSync(candidate)) return candidate;
  }
  for (const name of names) {
    const probe = spawnSync(process.platform === "win32" ? "where.exe" : "which", [name], { encoding: "utf8" });
    if (probe.status === 0) {
      const first = probe.stdout.split(/\r?\n/).find(Boolean);
      if (first) return first.trim();
    }
  }
  fail(`Missing tool ${names.join("/")} (set ${envName})`);
}

function quoteCmdArg(value) {
  return `"${String(value).replace(/"/g, '""')}"`;
}

function quotePowerShellArg(value) {
  return `'${String(value).replace(/'/g, "''")}'`;
}

function runTool(args) {
  const useCmdWrapper = process.platform === "win32" && /\.cmd$/i.test(args[0]);
  const proc = useCmdWrapper
    ? spawnSync("powershell.exe", [
        "-NoProfile",
        "-ExecutionPolicy",
        "Bypass",
        "-Command",
        "& " + args.map(quotePowerShellArg).join(" "),
      ], { encoding: "utf8" })
    : spawnSync(args[0], args.slice(1), { encoding: "utf8" });
  if (proc.status !== 0) {
    throw new Error(`Command failed ${proc.status}: ${args.join(" ")}\n${proc.error ? proc.error.message + "\n" : ""}${proc.stdout || ""}${proc.stderr || ""}`);
  }
  return proc.stdout || "";
}

function tokenReader(buffer) {
  let offset = 0;
  function skip() {
    while (offset < buffer.length) {
      const byte = buffer[offset];
      if (byte === 35) {
        while (offset < buffer.length && buffer[offset] !== 10) offset += 1;
      } else if (byte === 9 || byte === 10 || byte === 13 || byte === 32) {
        offset += 1;
      } else {
        break;
      }
    }
  }
  return {
    next() {
      skip();
      const start = offset;
      while (offset < buffer.length && ![9, 10, 13, 32].includes(buffer[offset])) offset += 1;
      return buffer.slice(start, offset).toString("ascii");
    },
    dataOffset() {
      skip();
      return offset;
    },
  };
}

function readPpm(file) {
  const buffer = fs.readFileSync(file);
  const reader = tokenReader(buffer);
  const magic = reader.next();
  if (magic !== "P6") fail(`Unsupported PPM ${file}: ${magic}`);
  const width = Number(reader.next());
  const height = Number(reader.next());
  const max = Number(reader.next());
  const offset = reader.dataOffset();
  if (!width || !height || max !== 255) fail(`Unsupported PPM header ${file}`);
  return { width, height, data: buffer.subarray(offset, offset + width * height * 3) };
}

function writeBmp(file, image) {
  const { width, height, data } = image;
  const rowSize = Math.ceil((width * 3) / 4) * 4;
  const pixelBytes = rowSize * height;
  const headerSize = 54;
  const out = Buffer.alloc(headerSize + pixelBytes);
  out.write("BM", 0, "ascii");
  out.writeUInt32LE(out.length, 2);
  out.writeUInt32LE(headerSize, 10);
  out.writeUInt32LE(40, 14);
  out.writeInt32LE(width, 18);
  out.writeInt32LE(height, 22);
  out.writeUInt16LE(1, 26);
  out.writeUInt16LE(24, 28);
  out.writeUInt32LE(pixelBytes, 34);
  for (let y = 0; y < height; y += 1) {
    const srcY = height - 1 - y;
    const row = headerSize + y * rowSize;
    for (let x = 0; x < width; x += 1) {
      const src = (srcY * width + x) * 3;
      const dst = row + x * 3;
      out[dst] = data[src + 2];
      out[dst + 1] = data[src + 1];
      out[dst + 2] = data[src];
    }
  }
  fs.writeFileSync(file, out);
}

function downscaleAverage(image, factor) {
  const width = Math.max(1, Math.round(image.width * factor));
  const height = Math.max(1, Math.round(image.height * factor));
  const data = Buffer.alloc(width * height * 3);
  for (let y = 0; y < height; y += 1) {
    const y0 = Math.floor(y / factor);
    const y1 = Math.max(y0 + 1, Math.floor((y + 1) / factor));
    for (let x = 0; x < width; x += 1) {
      const x0 = Math.floor(x / factor);
      const x1 = Math.max(x0 + 1, Math.floor((x + 1) / factor));
      const sums = [0, 0, 0];
      let count = 0;
      for (let sy = y0; sy < y1 && sy < image.height; sy += 1) {
        for (let sx = x0; sx < x1 && sx < image.width; sx += 1) {
          const src = (sy * image.width + sx) * 3;
          sums[0] += image.data[src];
          sums[1] += image.data[src + 1];
          sums[2] += image.data[src + 2];
          count += 1;
        }
      }
      const dst = (y * width + x) * 3;
      data[dst] = Math.round(sums[0] / count);
      data[dst + 1] = Math.round(sums[1] / count);
      data[dst + 2] = Math.round(sums[2] / count);
    }
  }
  return { width, height, data };
}

function upscaleNearest(image, width, height) {
  const data = Buffer.alloc(width * height * 3);
  for (let y = 0; y < height; y += 1) {
    const sy = Math.min(image.height - 1, Math.floor((y / height) * image.height));
    for (let x = 0; x < width; x += 1) {
      const sx = Math.min(image.width - 1, Math.floor((x / width) * image.width));
      const src = (sy * image.width + sx) * 3;
      const dst = (y * width + x) * 3;
      data[dst] = image.data[src];
      data[dst + 1] = image.data[src + 1];
      data[dst + 2] = image.data[src + 2];
    }
  }
  return { width, height, data };
}

function boxBlur(image, radius) {
  if (radius <= 0) return image;
  const data = Buffer.alloc(image.data.length);
  for (let y = 0; y < image.height; y += 1) {
    for (let x = 0; x < image.width; x += 1) {
      const sums = [0, 0, 0];
      let count = 0;
      for (let yy = Math.max(0, y - radius); yy <= Math.min(image.height - 1, y + radius); yy += 1) {
        for (let xx = Math.max(0, x - radius); xx <= Math.min(image.width - 1, x + radius); xx += 1) {
          const src = (yy * image.width + xx) * 3;
          sums[0] += image.data[src];
          sums[1] += image.data[src + 1];
          sums[2] += image.data[src + 2];
          count += 1;
        }
      }
      const dst = (y * image.width + x) * 3;
      data[dst] = Math.round(sums[0] / count);
      data[dst + 1] = Math.round(sums[1] / count);
      data[dst + 2] = Math.round(sums[2] / count);
    }
  }
  return { width: image.width, height: image.height, data };
}

function myopia(image, factor, blurRadius) {
  return boxBlur(upscaleNearest(downscaleAverage(image, factor), image.width, image.height), blurRadius);
}

function renderPdf(caseDir, pdfPath, pdftoppm, pdfinfo) {
  const prefix = path.join(caseDir, "page");
  const info = runTool([pdfinfo, pdfPath]);
  runTool([pdftoppm, "-r", "110", pdfPath, prefix]);
  const ppms = fs.readdirSync(caseDir).filter((name) => /^page-\d+\.ppm$/.test(name)).sort();
  const pages = [];
  for (const ppmName of ppms) {
    const pageNo = Number(ppmName.match(/page-(\d+)\.ppm/)[1]);
    const ppmPath = path.join(caseDir, ppmName);
    const image = readPpm(ppmPath);
    const normal = `page-${pageNo}-normal.bmp`;
    const moderate = `page-${pageNo}-myopia-moderate.bmp`;
    const strong = `page-${pageNo}-myopia-strong.bmp`;
    writeBmp(path.join(caseDir, normal), image);
    writeBmp(path.join(caseDir, moderate), myopia(image, 0.55, 1));
    writeBmp(path.join(caseDir, strong), myopia(image, 0.38, 2));
    pages.push({ pageNo, normal, moderate, strong, width: image.width, height: image.height });
  }
  return { info, pages };
}

function htmlEscape(value) {
  return String(value == null ? "" : value)
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;");
}

function writeReport(results) {
  const sections = results.map((item) => {
    const rows = item.pages.map((page) => `
      <h3>Seite ${page.pageNo}</h3>
      <div class="grid">
        <figure><img src="${item.id}/${page.normal}" alt="${item.id} Seite ${page.pageNo} normal"><figcaption>normal</figcaption></figure>
        <figure><img src="${item.id}/${page.moderate}" alt="${item.id} Seite ${page.pageNo} moderat kurzsichtig"><figcaption>moderat kurzsichtig</figcaption></figure>
        <figure><img src="${item.id}/${page.strong}" alt="${item.id} Seite ${page.pageNo} stark kurzsichtig"><figcaption>stark kurzsichtig</figcaption></figure>
      </div>`).join("");
    return `
      <section class="${item.failures.length ? "fail" : "pass"}">
        <h2>${htmlEscape(item.id)} - ${item.failures.length ? "FAIL" : "PASS"}</h2>
        <p>Titel ${item.titleMin}pt, Meta ${item.metaMin}pt, Tabellenlabels ${item.tableMin}pt, Bilder ${item.imageCount}, Seiten ${item.pageCount}/${item.expectedPages}</p>
        ${item.failures.length ? `<ul>${item.failures.map((failure) => `<li>${htmlEscape(failure)}</li>`).join("")}</ul>` : ""}
        ${rows}
      </section>`;
  }).join("");
  const html = `<!doctype html>
<html lang="de">
<meta charset="utf-8">
<title>KGG Grossdruck Readability Smoke</title>
<style>
body{font-family:Arial,sans-serif;margin:24px;background:#f5f7fb;color:#111827}
section{background:white;border:1px solid #d7dde8;border-radius:10px;padding:16px;margin:0 0 24px}
.pass{border-color:#1b8f4d}.fail{border-color:#c62828}
.grid{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:12px}
figure{margin:0;border:1px solid #d7dde8;background:#fff;padding:8px}
img{width:100%;height:auto;display:block}
figcaption{font-weight:700;margin-top:6px}
li{margin:4px 0}
</style>
<h1>KGG Grossdruck Readability Smoke</h1>
<p>Moderat und stark verschwommene Varianten simulieren kurzsichtige Lesbarkeit ohne perfekte Brille.</p>
${sections}
</html>
`;
  fs.writeFileSync(path.join(OUT_DIR, "index.html"), html, "utf8");
}

function main() {
  const pdftoppm = resolveTool("KGG_PDFTOPPM", ["pdftoppm", "pdftoppm.cmd"]);
  const pdfinfo = resolveTool("KGG_PDFINFO", ["pdfinfo", "pdfinfo.cmd"]);
  fs.rmSync(OUT_DIR, { recursive: true, force: true });
  fs.mkdirSync(OUT_DIR, { recursive: true });

  const cases = [
    { id: "short-3", count: 3, withImages: true },
    { id: "long-6", count: 6, withImages: true },
    { id: "overflow-9", count: 9, withImages: true },
    { id: "missing-image-3", count: 3, withImages: false },
  ];
  const results = [];
  for (const caseDef of cases) {
    const caseDir = path.join(OUT_DIR, caseDef.id);
    fs.mkdirSync(caseDir, { recursive: true });
    const result = buildCase(caseDef);
    const pdfPath = path.join(caseDir, `${caseDef.id}.pdf`);
    writeBinaryString(pdfPath, result.pdfBinary);
    const analysis = analyzeCase(result, caseDef);
    const render = renderPdf(caseDir, pdfPath, pdftoppm, pdfinfo);
    results.push({ ...analysis, pages: render.pages, pdfInfo: render.info });
  }
  fs.writeFileSync(path.join(OUT_DIR, "report.json"), JSON.stringify(results, null, 2) + "\n", "utf8");
  writeReport(results);

  const failures = results.flatMap((item) => item.failures.map((failure) => `${item.id}: ${failure}`));
  if (failures.length) {
    console.error(failures.join("\n"));
    console.error(`Readability report: ${path.join(OUT_DIR, "index.html")}`);
    process.exit(1);
  }
  console.log(JSON.stringify({
    suite: "pdf-readability-critical",
    report: path.join(OUT_DIR, "index.html"),
    cases: results.map((item) => ({
      id: item.id,
      titleMin: item.titleMin,
      metaMin: item.metaMin,
      tableMin: item.tableMin,
      imageCount: item.imageCount,
      pages: item.pageCount,
    })),
  }, null, 2));
}

main();
