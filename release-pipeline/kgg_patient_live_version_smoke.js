#!/usr/bin/env node
"use strict";

const fs = require("fs");
const http = require("http");
const path = require("path");
const { chromium } = require("playwright");

const expectedVersion = String(process.argv[2] || "").replace(/^v/i, "");
const liveUrl = process.argv[3] || "https://kayus24.github.io/kgg/";
const runtimeRoot = path.resolve(process.argv[4] || path.resolve(__dirname, ".."));
const localOnly = process.argv[5] === "--local-only";

function assert(condition, message) {
  if (!condition) throw new Error(message);
}

function encodePlan(plan) {
  return Buffer.from(JSON.stringify(plan), "utf8").toString("base64url");
}

function contentType(filename) {
  const extension = path.extname(filename).toLowerCase();
  return {
    ".html": "text/html; charset=utf-8",
    ".js": "text/javascript; charset=utf-8",
    ".json": "application/json; charset=utf-8",
    ".webmanifest": "application/manifest+json; charset=utf-8",
    ".png": "image/png",
    ".svg": "image/svg+xml",
  }[extension] || "application/octet-stream";
}

function currentRuntimeVersion() {
  const source = fs.readFileSync(path.join(runtimeRoot, "service-worker.js"), "utf8");
  const match = source.match(/const APP_VERSION = '([0-9]+)';/);
  assert(match, "runtime service worker is missing APP_VERSION");
  return match[1];
}

function legacyRuntimeText(filename, source, currentVersion, staleVersion) {
  if (filename === "service-worker.js") {
    return source
      .replace(`const APP_VERSION = '${currentVersion}';`, `const APP_VERSION = '${staleVersion}';`)
      .replace(new RegExp(`v${currentVersion}`, "g"), `v${staleVersion}`)
      .replaceAll(`patient-version-label.js?v=${currentVersion}`, `patient-version-label.js?v=${staleVersion}`);
  }
  if (filename === "patient-version-label.js" || filename === "update-recovery.html") {
    return source.replace(`const RELEASE='${currentVersion}';`, `const RELEASE='${staleVersion}';`);
  }
  if (filename === "index.html") {
    return source.replaceAll(`patient-version-label.js?v=${currentVersion}`, `patient-version-label.js?v=${staleVersion}`);
  }
  return source;
}

function localWorkerText(source) {
  return source.replace(
    "'https://cdn.jsdelivr.net/npm/qrcode-generator@1.4.4/qrcode.js'",
    "'./patient-qr-format.js'",
  );
}

async function stubExternalQr(context) {
  await context.route("**/qrcode-generator@1.4.4/qrcode.js*", (route) => route.fulfill({
    status: 200,
    contentType: "text/javascript",
    body: "",
  }));
}

function startStaleRuntimeServer(currentVersion, staleVersion) {
  let serveNew = false;
  const server = http.createServer((request, response) => {
    const pathname = decodeURIComponent(new URL(request.url || "/", "http://local").pathname);
    if (!pathname.startsWith("/kgg/")) {
      response.writeHead(404);
      response.end("not found");
      return;
    }
    const relative = pathname.slice("/kgg/".length) || "index.html";
    const target = path.resolve(runtimeRoot, relative);
    if (!target.startsWith(`${runtimeRoot}${path.sep}`) || !fs.existsSync(target) || !fs.statSync(target).isFile()) {
      response.writeHead(404);
      response.end("not found");
      return;
    }
    const filename = path.basename(target);
    const source = fs.readFileSync(target, "utf8");
    const runtimeSource = filename === "service-worker.js" ? localWorkerText(source) : source;
    const body = serveNew ? runtimeSource : legacyRuntimeText(filename, runtimeSource, currentVersion, staleVersion);
    response.writeHead(200, {
      "Content-Type": contentType(target),
      "Cache-Control": "no-store",
      "Service-Worker-Allowed": "/",
    });
    response.end(body);
  });
  return {
    server,
    setServeNew() {
      serveNew = true;
    },
  };
}

async function activeWorkerVersion(page) {
  return page.evaluate(async () => {
    if (!("serviceWorker" in navigator)) return "";
    const registration = await navigator.serviceWorker.ready;
    const worker = registration.active || navigator.serviceWorker.controller;
    if (!worker || typeof MessageChannel === "undefined") return "";
    return new Promise((resolve) => {
      const channel = new MessageChannel();
      const timer = setTimeout(() => resolve(""), 2000);
      channel.port1.onmessage = (event) => {
        clearTimeout(timer);
        resolve(event.data && event.data.version ? String(event.data.version) : "");
      };
      worker.postMessage({ type: "GET_APP_VERSION" }, [channel.port2]);
    });
  });
}

async function liveVersionEvidence(page) {
  return {
    visible: await page.locator("#kggAppVersion").innerText().catch(() => ""),
    worker: await activeWorkerVersion(page),
  };
}

async function verifyRemoteLive(browser) {
  const context = await browser.newContext({ serviceWorkers: "allow" });
  await stubExternalQr(context);
  const page = await context.newPage();
  const plan = {
    i: "live-version-smoke",
    t: "KGG synthetischer Live-Versions-Test",
    v: 1,
    d: 6,
    e: [["Synthetische Live-Version-Uebung", 1, "B", "kg", "Wdh", "1", "2"]],
  };
  const url = `${liveUrl}${liveUrl.includes("?") ? "&" : "?"}verify=live-client-${Date.now()}&plan=${encodeURIComponent(`KGGH2:${encodePlan(plan)}`)}`;
  await page.goto(url, { waitUntil: "domcontentloaded", timeout: 30000 });
  await page.locator("#title").waitFor({ state: "visible", timeout: 30000 });
  let evidence = null;
  for (let attempt = 1; attempt <= 12; attempt += 1) {
    evidence = await liveVersionEvidence(page);
    if (evidence.visible === `v${expectedVersion}` && evidence.worker === expectedVersion) {
      await context.close();
      return { ...evidence, attempts: attempt };
    }
    await page.waitForTimeout(500);
  }
  await context.close();
  throw new Error(`LIVE_CLIENT_VERSION_MISMATCH: ${JSON.stringify({ expected: expectedVersion, observed: evidence })}`);
}

async function verifyStaleClientUpdate(browser, currentVersion) {
  const staleVersion = String(Math.max(0, Number(currentVersion) - 1));
  assert(staleVersion !== currentVersion, "runtime version must be greater than zero for stale-client test");
  const runtime = startStaleRuntimeServer(currentVersion, staleVersion);
  await new Promise((resolve) => runtime.server.listen(0, "127.0.0.1", resolve));
  const port = runtime.server.address().port;
  const context = await browser.newContext({ serviceWorkers: "allow" });
  await stubExternalQr(context);
  const page = await context.newPage();
  const plan = {
    i: "stale-client-version-smoke",
    t: "KGG synthetischer Cache-Update-Test",
    v: 1,
    d: 6,
    e: [["Synthetische Cache-Uebung", 1, "B", "kg", "Wdh", "1", "2"]],
  };
  try {
    await page.goto(`http://127.0.0.1:${port}/kgg/?plan=${encodeURIComponent(`KGGH2:${encodePlan(plan)}`)}`, {
      waitUntil: "domcontentloaded",
      timeout: 30000,
    });
    await page.locator("#title").waitFor({ state: "visible", timeout: 30000 });
    const staleEvidence = await liveVersionEvidence(page);
    assert(staleEvidence.visible === `v${staleVersion}`, `stale client did not expose v${staleVersion}: ${JSON.stringify(staleEvidence)}`);

    runtime.setServeNew();
    await page.evaluate(() => {
      navigator.serviceWorker.ready.then((registration) => registration.update().catch(() => {}));
    });
    await page.locator("#kggUpdateGate").waitFor({ state: "visible", timeout: 15000 });
    assert((await page.locator("#kggUpdateGate").innerText()).includes("Jetzt aktualisieren"), "stale client did not show update action");
    await page.locator("#kggUpdateGateButton").click();
    await page.waitForFunction(
      (version) => document.querySelector("#kggAppVersion")?.textContent === `v${version}`,
      currentVersion,
      { timeout: 15000 },
    );
    const updatedEvidence = await liveVersionEvidence(page);
    assert(updatedEvidence.visible === `v${currentVersion}`, `stale client update kept old visible version: ${JSON.stringify(updatedEvidence)}`);
    assert(updatedEvidence.worker === currentVersion, `stale client update kept old worker: ${JSON.stringify(updatedEvidence)}`);
    return { stale: staleEvidence, updated: updatedEvidence };
  } finally {
    await context.close();
    await new Promise((resolve) => runtime.server.close(resolve));
  }
}

async function main() {
  assert(/^\d+$/.test(expectedVersion), "expected patient version must be numeric");
  const currentVersion = currentRuntimeVersion();
  assert(currentVersion === expectedVersion, `runtime version ${currentVersion} does not match expected ${expectedVersion}`);
  const browser = await chromium.launch({ headless: true });
  try {
    const remote = localOnly ? null : await verifyRemoteLive(browser);
    const staleClient = await verifyStaleClientUpdate(browser, currentVersion);
    console.log(JSON.stringify({
      status: "PASS",
      test: "patient-live-client-version",
      expectedVisibleVersion: `v${expectedVersion}`,
      remoteFreshClient: remote,
      staleClientUpdate: staleClient,
      boundedVersionChecks: 12,
    }, null, 2));
  } finally {
    await browser.close();
  }
}

main().catch((error) => {
  console.error(`KGG patient live version smoke FAIL: ${error.stack || error.message}`);
  process.exitCode = 1;
});
