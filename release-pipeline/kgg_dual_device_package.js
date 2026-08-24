#!/usr/bin/env node
"use strict";

const fs = require("fs");
const os = require("os");
const path = require("path");

const ROOT = path.resolve(__dirname, "..");
const FIXTURE_SOURCE = path.join(ROOT, "android-wrapper", "app", "src", "preview", "assets", "android", "kgg_dual_device_fixtures.js");
const AGENT_SOURCE = path.join(ROOT, "device-test", "patient-device-test-agent.js");
const STORAGE_SOURCE = path.join(ROOT, "device-test", "patient-device-test-storage.js");
const QR_SOURCE = path.join(ROOT, "kgg-update", "src", "runtime", "qrcode-generator.html");
const ROOT_FILES = [
  "index.html",
  "update-recovery.html",
  "manifest-v64.webmanifest",
  "kgg-icon-192-v63.png",
  "kgg-icon-512-v63.png",
  "kgg-icon-maskable-512-v63.png",
  "numpad-ui-fix.js",
  "patient-version-label.js",
  "patient-plan-link-choice.js",
  "collapse-cards.js",
  "patient-card-progress.js",
  "patient-install-prompt.js",
  "patient-plan-replace-slot-fix.js",
  "patient-start-scan.js",
  "patient-qr-format.js",
  "patient-multiplan-db.js",
  "patient-plan-delete.js",
  "patient-card-settings.js",
  "patient-start-values-day1.js",
  "patient-day-history.js",
  "patient-media-retry-cache_v2.js",
  "patient-ui-micro-polish.js",
  "patient-pain-vertical-scale.js",
  "patient-install-guide.js",
  "patient-numpad-visibility-fix.js",
  "patient-extra-info-display.js",
  "patient-last-value-hints.js",
  "patient-set-summary-groups.js",
  "patient-qr-fullscreen.js",
  "patient-numpad-card-guard.js",
];

function fail(message) {
  throw new Error(message);
}

function parseArgs(argv) {
  const values = {};
  for (let index = 0; index < argv.length; index += 1) {
    if (argv[index] === "--self-test") {
      values.selfTest = true;
      continue;
    }
    if (!argv[index].startsWith("--") || index + 1 >= argv.length) fail("Ungültiges Argument: " + argv[index]);
    values[argv[index].slice(2).replace(/-([a-z])/g, (_, letter) => letter.toUpperCase())] = argv[++index];
  }
  return values;
}

function safeOutput(value) {
  const output = path.resolve(String(value || ""));
  const root = path.parse(output).root;
  if (!value || output === root || output === ROOT || ROOT.startsWith(output + path.sep)) fail("Unsicheres Ausgabeverzeichnis");
  return output;
}

function copyFile(relative, output) {
  const source = path.join(ROOT, relative);
  if (!fs.existsSync(source) || !fs.statSync(source).isFile()) fail("PWA-Datei fehlt: " + relative);
  const target = path.join(output, relative);
  fs.mkdirSync(path.dirname(target), { recursive: true });
  fs.copyFileSync(source, target);
}

function isolatePatientStorage(relative, output) {
  if (!/\.(?:html|js)$/i.test(relative)) return;
  const target = path.join(output, relative);
  let source = fs.readFileSync(target, "utf8");
  source = source.replace(/\bwindow\.localStorage\b|\blocalStorage\b/g, "window.KGGDeviceTestStorage");
  if (relative === "patient-plan-replace-slot-fix.js") {
    source = source
      .replace("const nativeSetItem=Storage.prototype.setItem;", "const nativeSetItem=window.KGGDeviceTestStorage.setItem;")
      .replace("Storage.prototype.setItem=function(key,value){", "window.KGGDeviceTestStorage.setItem=function(key,value){");
    if (source.includes("Storage.prototype.setItem") || !source.includes("window.KGGDeviceTestStorage.setItem=function")) {
      fail("Mehrplan-Speicherhook konnte nicht isoliert werden");
    }
  }
  fs.writeFileSync(target, source, "utf8");
}

function localQrSource() {
  const wrapped = fs.readFileSync(QR_SOURCE, "utf8").trim();
  const match = /^<script>\s*([\s\S]*?)\s*<\/script>$/.exec(wrapped);
  if (!match || !match[1].includes("var qrcode=")) fail("Lokaler QR-Generator ist ungültig");
  return match[1] + "\n";
}

function buildPackage(args) {
  const output = safeOutput(args.output);
  const sourceSha = String(args.sourceSha || "").trim();
  const jobFile = path.resolve(String(args.jobFile || ""));
  if (!/^[a-f0-9]{40}$/.test(sourceSha)) fail("sourceSha ist ungültig");
  if (!fs.existsSync(jobFile)) fail("Job-Manifest fehlt");
  const job = JSON.parse(fs.readFileSync(jobFile, "utf8"));
  if (job.sourceSha !== sourceSha || !/^[a-f0-9]{64}$/.test(String(job.jobHash || ""))) fail("Job und Quellstand passen nicht zusammen");

  fs.rmSync(output, { recursive: true, force: true });
  fs.mkdirSync(output, { recursive: true });
  ROOT_FILES.forEach((relative) => {
    copyFile(relative, output);
    isolatePatientStorage(relative, output);
  });
  ["vendor/fflate-0.8.3.js", "vendor/jsqr-1.4.0.js"].forEach((relative) => copyFile(relative, output));
  fs.copyFileSync(FIXTURE_SOURCE, path.join(output, "kgg-dual-device-fixtures.js"));
  fs.copyFileSync(AGENT_SOURCE, path.join(output, "patient-device-test-agent.js"));
  fs.copyFileSync(STORAGE_SOURCE, path.join(output, "patient-device-test-storage.js"));
  fs.writeFileSync(path.join(output, "vendor", "qrcode-generator-1.5.2.js"), localQrSource(), "utf8");

  const indexPath = path.join(output, "index.html");
  let html = fs.readFileSync(indexPath, "utf8");
  const scannerTag = '<script src="./patient-start-scan.js?v=start-scan-v81-kgg-h3"></script>';
  const injected = '<script src="./kgg-dual-device-fixtures.js?v=v404-1"></script><script src="./patient-device-test-agent.js?v=v404-1"></script>' + scannerTag;
  if (!html.includes(scannerTag)) fail("Scanner-Einfügepunkt fehlt");
  html = html
    .replace("</head>", '<script src="./patient-device-test-storage.js?v=v404-1"></script></head>')
    .replace('<script src="https://cdn.jsdelivr.net/npm/qrcode-generator@1.4.4/qrcode.js"></script>', '<script src="./vendor/qrcode-generator-1.5.2.js?v=1.5.2"></script>')
    .replace(scannerTag, injected)
    .replace("<title>KGG Handyplan</title>", "<title>KGG Patienten-Test v404</title>")
    .replace("<h1>KGG Handyplan</h1>", "<h1>KGG Patienten-Test v404</h1>");
  fs.writeFileSync(indexPath, html, "utf8");

  const sourceWorker = fs.readFileSync(path.join(ROOT, "service-worker.js"), "utf8");
  let worker = sourceWorker
    .replace("kgg-handyplan-v81-kgg-h3-qr", "kgg-device-test-v404-" + sourceSha.slice(0, 12))
    .replace("const APP_VERSION = '81';", "const APP_VERSION = '404-device-test';")
    .replace(
      "const CORE_ASSETS = ['./index.html','./manifest.json','./manifest-v64.webmanifest','./kgg-icon-192-v63.png','./kgg-icon-512-v63.png'];",
      "const CORE_ASSETS = ['./index.html','./manifest.json','./manifest-v64.webmanifest','./kgg-icon-192-v63.png','./kgg-icon-512-v63.png','./kgg-dual-device-fixtures.js','./patient-device-test-storage.js','./patient-device-test-agent.js','./vendor/qrcode-generator-1.5.2.js'];",
    )
    .replace(
      "function isIndexRequest(request){const url=new URL(request.url);if(url.origin!==self.location.origin)return false;return url.pathname.endsWith('/kgg/')||url.pathname.endsWith('/kgg/index.html')}",
      "function isIndexRequest(request){const url=new URL(request.url);if(url.origin!==self.location.origin)return false;const scope=new URL(self.registration.scope).pathname;return url.pathname===scope||url.pathname===scope+'index.html'}",
    )
    .replace(
      "function isRecoveryRequest(request){const url=new URL(request.url);if(url.origin!==self.location.origin)return false;return url.pathname.endsWith('/kgg/update-recovery.html')}",
      "function isRecoveryRequest(request){const url=new URL(request.url);if(url.origin!==self.location.origin)return false;const scope=new URL(self.registration.scope).pathname;return url.pathname===scope+'update-recovery.html'}",
    );
  fs.writeFileSync(path.join(output, "service-worker.js"), worker, "utf8");

  const manifest = {
    id: "/kgg-patient-preview/device-test/",
    name: "KGG Patienten-Test v404",
    short_name: "KGG QR-Test",
    start_url: "./",
    scope: "./",
    display: "standalone",
    background_color: "#f4f7fb",
    theme_color: "#111827",
    icons: [
      { src: "kgg-icon-192-v63.png", sizes: "192x192", type: "image/png", purpose: "any" },
      { src: "kgg-icon-512-v63.png", sizes: "512x512", type: "image/png", purpose: "any" },
      { src: "kgg-icon-maskable-512-v63.png", sizes: "512x512", type: "image/png", purpose: "maskable" },
    ],
  };
  fs.writeFileSync(path.join(output, "manifest.json"), JSON.stringify(manifest, null, 2) + "\n", "utf8");
  fs.writeFileSync(path.join(output, "device-test-meta.json"), JSON.stringify({
    kind: "kgg_device_test_pwa_meta",
    schemaVersion: 1,
    sourceSha,
    jobHash: job.jobHash,
    requestId: job.requestId,
    syntheticOnly: true,
  }, null, 2) + "\n", "utf8");
  return { output, files: ROOT_FILES.length + 10, sourceSha, jobHash: job.jobHash };
}

function selfTest() {
  const temp = fs.mkdtempSync(path.join(os.tmpdir(), "kgg-device-test-package-"));
  try {
    const sourceSha = "a".repeat(40);
    const jobFile = path.join(temp, "job.json");
    fs.writeFileSync(jobFile, JSON.stringify({ sourceSha, jobHash: "b".repeat(64), requestId: "package-self-test" }), "utf8");
    const result = buildPackage({ output: path.join(temp, "out"), sourceSha, jobFile });
    const html = fs.readFileSync(path.join(result.output, "index.html"), "utf8");
    if (!html.includes("patient-device-test-agent.js") || !html.includes("KGG Patienten-Test v404")) fail("Test-Agent wurde nicht eingebaut");
    if (!html.includes("patient-device-test-storage.js") || !html.includes("qrcode-generator-1.5.2.js") || html.includes("cdn.jsdelivr.net")) fail("Isolierter Offline-Start ist unvollständig");
    const copiedProductSources = ROOT_FILES.filter((relative) => /\.(?:html|js)$/i.test(relative)).map((relative) => fs.readFileSync(path.join(result.output, relative), "utf8")).join("\n");
    if (/\b(?:window\.)?localStorage\b/.test(copiedProductSources)) fail("Produkt-Speicher ist in der Test-PWA nicht isoliert");
    const storage = fs.readFileSync(path.join(result.output, "patient-device-test-storage.js"), "utf8");
    if (!storage.includes("kgg_device_test_v404:") || !storage.includes("KGGDeviceTestStorage")) fail("Test-Speicher-Adapter fehlt");
    const worker = fs.readFileSync(path.join(result.output, "service-worker.js"), "utf8");
    if (!worker.includes("kgg-device-test-v404-") || !worker.includes("patient-device-test-agent.js") || !worker.includes("patient-device-test-storage.js")) fail("Test-PWA-Cache ist unvollständig");
    console.log(JSON.stringify({ ok: true, suite: "dual-device-package", files: result.files }));
  } finally {
    fs.rmSync(temp, { recursive: true, force: true });
  }
}

try {
  const args = parseArgs(process.argv.slice(2));
  const result = args.selfTest ? selfTest() : buildPackage(args);
  if (result) console.log(JSON.stringify({ ok: true, ...result }));
} catch (error) {
  console.error("ERROR: " + (error && error.message ? error.message : String(error)));
  process.exit(1);
}
