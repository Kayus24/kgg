#!/usr/bin/env node
"use strict";

const fs = require("fs");
const http = require("http");
const path = require("path");
const { chromium } = require("playwright");

const ROOT = path.resolve(__dirname, "..");
const FIRST_LOAD_GLOBALS = [
  "__kggStartScanVersion",
  "__kggPatientMultiPlanDbAddon",
  "__kggPlanDelete",
  "__kggCardProgress",
  "__kggSetSummaryGroups",
  "KGGPatientMediaRetryCache",
];
const FIRST_LOAD_MODULES = [
  "patient-plan-link-choice.js",
  "patient-start-scan.js",
  "patient-multiplan-db.js",
  "patient-plan-delete.js",
  "patient-card-progress.js",
  "patient-set-summary-groups.js",
  "patient-media-retry-cache_v2.js",
  "patient-version-label.js",
];

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

function safeFile(urlPath) {
  const pathname = decodeURIComponent(urlPath.split("?")[0]).replace(/^\/+/, "");
  const relative = pathname.replace(/^kgg\/?/, "") || "index.html";
  const target = path.resolve(ROOT, relative);
  if (!target.startsWith(`${ROOT}${path.sep}`) && target !== ROOT) return null;
  if (!fs.existsSync(target) || !fs.statSync(target).isFile()) return null;
  return target;
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

function trackFreshLoadNavigation(page) {
  const evidence = {
    mainDocumentNavigations: 0,
    documentNavigationsBeforeRuntime: [],
    runtimeReady: false,
  };
  page.on("request", (request) => {
    if (!request.isNavigationRequest() || request.frame() !== page.mainFrame()) return;
    evidence.mainDocumentNavigations += 1;
    if (evidence.mainDocumentNavigations > 1 && !evidence.runtimeReady) {
      evidence.documentNavigationsBeforeRuntime.push(request.url());
    }
  });
  return evidence;
}

async function waitForFreshControlledRuntime(page, navigationEvidence) {
  try {
    await page.waitForFunction(
      ({ globals, modules }) => {
        const names = Array.from(document.scripts)
          .map((script) => script.src ? new URL(script.src, location.href).pathname.split("/").pop() : "")
          .filter(Boolean);
        const allModules = modules.every((module) => names.filter((name) => name === module).length === 1);
        const allGlobals = globals.every((name) => Boolean(window[name]));
        const plan = document.querySelector("#plan");
        return Boolean(
          navigator.serviceWorker && navigator.serviceWorker.controller &&
          allModules && allGlobals &&
          plan && !plan.classList.contains("hide") &&
          document.querySelector("#kgg-collapse-toggle") &&
          document.querySelector("#kggAppVersion") &&
          document.querySelector("#list .ex .kggCardProgress")
        );
      },
      { globals: FIRST_LOAD_GLOBALS, modules: FIRST_LOAD_MODULES },
      { timeout: 12000 }
    );
  } catch (error) {
    const diagnostics = await page.evaluate(() => ({
      controlled: Boolean(navigator.serviceWorker && navigator.serviceWorker.controller),
      scripts: Array.from(document.scripts).map((script) => script.src).filter(Boolean),
      bodyClasses: document.body.className,
    }));
    throw new Error(`fresh controlled patient GPT runtime was not ready without a reload: ${JSON.stringify({ navigationEvidence, diagnostics, cause: error.message })}`);
  }
  navigationEvidence.runtimeReady = true;
  assert(
    navigationEvidence.mainDocumentNavigations === 1 && navigationEvidence.documentNavigationsBeforeRuntime.length === 0,
    `fresh controlled patient GPT runtime navigated or reloaded before readiness: ${JSON.stringify(navigationEvidence)}`
  );
  const navigationTypes = await page.evaluate(() => performance.getEntriesByType("navigation").map((entry) => entry.type));
  assert(
    navigationTypes.length === 1 && navigationTypes[0] === "navigate",
    `fresh controlled patient GPT runtime must have one initial navigation, never a reload: ${JSON.stringify(navigationTypes)}`
  );
  return { ...navigationEvidence, navigationTypes };
}

async function main() {
  const server = http.createServer((request, response) => {
    const file = safeFile(request.url || "/");
    if (!file) {
      response.writeHead(404, { "Content-Type": "text/plain; charset=utf-8" });
      response.end("not found");
      return;
    }
    response.writeHead(200, {
      "Content-Type": contentType(file),
      "Cache-Control": "no-store",
      "Service-Worker-Allowed": "/",
    });
    fs.createReadStream(file).pipe(response);
  });
  await new Promise((resolve) => server.listen(0, "127.0.0.1", resolve));
  const { port } = server.address();
  const browser = await chromium.launch({ headless: true });
  const context = await browser.newContext({
    viewport: { width: 390, height: 844 },
    serviceWorkers: "allow",
  });
  const page = await context.newPage();
  const navigationEvidence = trackFreshLoadNavigation(page);
  const plan = {
    i: "patient-gpt-browser-smoke",
    t: "Synthetischer Browser-Test",
    v: 1,
    d: 6,
    e: [
      ["Beinpresse", 2, "B", "kg", "Wdh", "40", "10"],
      ["Rudern", 2, "LR", "kg", "Wdh", "15", "12"],
    ],
  };
  const url = `http://127.0.0.1:${port}/kgg/?plan=${encodeURIComponent(`KGGH2:${encodePlan(plan)}`)}`;

  try {
    await page.goto(url, { waitUntil: "domcontentloaded" });
    const firstLoadEvidence = await waitForFreshControlledRuntime(page, navigationEvidence);
    assert((await page.locator("#title").innerText()) === plan.t, "synthetic plan title was not rendered");
    assert((await page.locator(".ex").count()) === 2, "synthetic exercises were not rendered");

    const firstCard = page.locator(".ex").first();
    if (!(await firstCard.evaluate((card) => card.classList.contains("kggOpen")))) {
      await firstCard.locator("h3").click();
      await page.waitForFunction(() => document.querySelector(".ex")?.classList.contains("kggOpen"));
    }
    const firstInput = page.locator(".num").first();
    await firstInput.click();
    await page.locator("#pad").waitFor({ state: "visible" });
    await page.locator("#pad .padGrid button", { hasText: "7" }).click();
    await page.locator("#pad .padOk").click();
    assert((await firstInput.inputValue()).endsWith("7"), "numpad value was not committed");

    const bodyText = await page.locator("body").innerText();
    assert(!bodyText.includes("KGGH2:"), "raw KGGH2 payload leaked into normal patient output");
    assert(!bodyText.includes('"storageVersion"'), "raw storage JSON leaked into normal patient output");

    const workerVersion = await activeWorkerVersion(page);
    assert(/^[0-9]+$/.test(workerVersion), "active service worker did not report a numeric version");
    const versionLabelCount = await page.locator("#kggAppVersion").count();
    if (!versionLabelCount) {
      const diagnostics = await page.evaluate(() => ({
        controlled: Boolean(navigator.serviceWorker && navigator.serviceWorker.controller),
        scripts: Array.from(document.scripts).map((script) => script.src).filter(Boolean),
      }));
      throw new Error(`patient version label was not injected: ${JSON.stringify(diagnostics)}`);
    }
    assert(
      (await page.locator("#kggAppVersion").innerText()) === `v${workerVersion}`,
      "visible patient version differs from the active service worker"
    );

    const recovery = await context.newPage();
    await recovery.goto(`http://127.0.0.1:${port}/kgg/update-recovery.html`, {
      waitUntil: "domcontentloaded",
    });
    assert(
      (await recovery.locator("body").innerText()).includes("KGG Update reparieren"),
      "update recovery page did not render"
    );
    await recovery.close();
    console.log(JSON.stringify({
      status: "PASS",
      test: "patient-gpt-browser",
      version: workerVersion,
      freshControlledNoReload: true,
      mainDocumentNavigations: firstLoadEvidence.mainDocumentNavigations,
      navigationTypes: firstLoadEvidence.navigationTypes,
    }));
  } finally {
    await context.close();
    await browser.close();
    await new Promise((resolve) => server.close(resolve));
  }
}

main().catch((error) => {
  console.error(`Patient GPT browser smoke failed: ${error.message}`);
  process.exitCode = 1;
});
