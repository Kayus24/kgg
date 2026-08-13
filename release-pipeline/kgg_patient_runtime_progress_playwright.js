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

function read(relative) {
  return fs.readFileSync(path.join(ROOT, relative), "utf8");
}

function sourceVersionContract() {
  const worker = read("service-worker.js");
  const label = read("patient-version-label.js");
  const recovery = read("update-recovery.html");
  const workerMatch = worker.match(/const APP_VERSION = '([0-9]+)';/);
  const labelMatch = label.match(/const RELEASE='([0-9]+)';/);
  const recoveryMatch = recovery.match(/const RELEASE='([0-9]+)';/);
  assert(workerMatch, "service worker APP_VERSION is missing");
  assert(labelMatch, "patient UI RELEASE is missing");
  assert(recoveryMatch, "recovery RELEASE is missing");
  const version = workerMatch[1];
  assert(labelMatch[1] === version, `UI release v${labelMatch[1]} differs from worker v${version}`);
  assert(recoveryMatch[1] === version, `recovery release v${recoveryMatch[1]} differs from worker v${version}`);
  assert(
    worker.includes(`./patient-version-label.js?v=${version}`),
    "worker does not inject the UI version module with its own version"
  );
  return version;
}

function encodePlan(plan) {
  return Buffer.from(JSON.stringify(plan), "utf8").toString("base64url");
}

function contentType(filename) {
  return {
    ".html": "text/html; charset=utf-8",
    ".js": "text/javascript; charset=utf-8",
    ".json": "application/json; charset=utf-8",
    ".webmanifest": "application/manifest+json; charset=utf-8",
    ".png": "image/png",
  }[path.extname(filename).toLowerCase()] || "application/octet-stream";
}

function safeFile(urlPath) {
  const pathname = decodeURIComponent(String(urlPath || "/").split("?")[0]).replace(/^\/+/, "");
  const relative = pathname.replace(/^kgg\/?/, "") || "index.html";
  const target = path.resolve(ROOT, relative);
  if (!target.startsWith(`${ROOT}${path.sep}`) && target !== ROOT) return null;
  if (!fs.existsSync(target) || !fs.statSync(target).isFile()) return null;
  return target;
}

async function activeWorkerVersion(page) {
  return page.evaluate(async () => {
    const registration = await navigator.serviceWorker.ready;
    const worker = navigator.serviceWorker.controller || registration.active;
    if (!worker || typeof MessageChannel === "undefined") return "";
    return new Promise((resolve) => {
      const channel = new MessageChannel();
      const timer = setTimeout(() => resolve(""), 2500);
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
      globals: Object.fromEntries([
        "__kggStartScanVersion",
        "__kggPatientMultiPlanDbAddon",
        "__kggPlanDelete",
        "__kggCardProgress",
        "__kggSetSummaryGroups",
        "KGGPatientMediaRetryCache",
      ].map((name) => [name, Boolean(window[name])])),
      bodyClasses: document.body.className,
    }));
    throw new Error(`fresh controlled patient runtime was not ready without a reload: ${JSON.stringify({ navigationEvidence, diagnostics, cause: error.message })}`);
  }
  navigationEvidence.runtimeReady = true;
  assert(
    navigationEvidence.mainDocumentNavigations === 1 && navigationEvidence.documentNavigationsBeforeRuntime.length === 0,
    `fresh controlled PWA navigated or reloaded before required runtime was ready: ${JSON.stringify(navigationEvidence)}`
  );
  const navigationTypes = await page.evaluate(() => performance.getEntriesByType("navigation").map((entry) => entry.type));
  assert(
    navigationTypes.length === 1 && navigationTypes[0] === "navigate",
    `fresh controlled PWA must have one initial navigation, never a reload: ${JSON.stringify(navigationTypes)}`
  );
  return { ...navigationEvidence, navigationTypes };
}

async function setCardOpen(page, card, open) {
  const isOpen = await card.evaluate((element) => element.classList.contains("kggOpen"));
  if (isOpen !== open) await card.locator("h3").click();
  await page.waitForFunction(
    ({ open }) => Boolean(document.querySelector("#list .ex")?.classList.contains("kggOpen")) === open,
    { open }
  );
}

async function setInputValue(input, value) {
  await input.evaluate((element, nextValue) => {
    element.value = nextValue;
    element.dispatchEvent(new Event("input", { bubbles: true }));
    element.dispatchEvent(new Event("change", { bubbles: true }));
  }, String(value));
}

async function assertVisibleBadge(page, card, state, text) {
  const badge = card.locator(".kggCardProgress");
  await badge.waitFor({ state: "attached" });
  await page.waitForFunction(
    ({ state, text }) => {
      const card = document.querySelector("#list .ex");
      const badge = card && card.querySelector(".kggCardProgress");
      if (!card || !badge || card.classList.contains("kggOpen") || !document.body.classList.contains("kggAlwaysCollapsed")) return false;
      const style = getComputedStyle(badge);
      const rect = badge.getBoundingClientRect();
      return badge.dataset.kggProgress === state && badge.textContent === text &&
        style.display !== "none" && style.visibility !== "hidden" && Number(style.opacity || "1") > 0 &&
        rect.width > 0 && rect.height > 0;
    },
    { state, text },
    { timeout: 10000 }
  );
  const details = await badge.evaluate((element) => {
    const style = getComputedStyle(element);
    const rect = element.getBoundingClientRect();
    return {
      text: element.textContent,
      state: element.dataset.kggProgress,
      display: style.display,
      visibility: style.visibility,
      opacity: style.opacity,
      width: rect.width,
      height: rect.height,
    };
  });
  assert(details.state === state, `progress state is ${details.state}, expected ${state}`);
  assert(details.text === text, `progress label is ${details.text}, expected ${text}`);
  assert(details.display !== "none" && details.visibility !== "hidden", `progress badge is hidden: ${JSON.stringify(details)}`);
  assert(details.width > 0 && details.height > 0, `progress badge has no visible box: ${JSON.stringify(details)}`);
}

async function main() {
  const expectedVersion = sourceVersionContract();
  const server = http.createServer((request, response) => {
    const file = safeFile(request.url);
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
    i: "progress-playwright-91",
    t: "Fortschritts-Sichtbarkeit",
    v: 1,
    d: 6,
    e: [["Beinpresse", 3, "B", "kg", "Wdh", "", ""]],
  };
  const payload = `KGGH2:${encodePlan(plan)}`;
  const url = `http://127.0.0.1:${port}/kgg/?plan=${encodeURIComponent(payload)}`;

  try {
    await page.goto(url, { waitUntil: "domcontentloaded" });
    const firstLoadEvidence = await waitForFreshControlledRuntime(page, navigationEvidence);

    const workerVersion = await activeWorkerVersion(page);
    const visibleVersion = (await page.locator("#kggAppVersion").innerText()).replace(/^v/i, "");
    assert(workerVersion === expectedVersion, `active worker is v${workerVersion || "?"}, expected v${expectedVersion}`);
    assert(visibleVersion === workerVersion, `visible UI is v${visibleVersion || "?"}, worker is v${workerVersion || "?"}`);

    const card = page.locator("#list .ex").first();
    await card.waitFor({ state: "visible" });
    const inputs = card.locator(".set input.num");
    const inputCount = await inputs.count();
    assert(inputCount === 6, `three bilateral sets must expose six normal fields, got ${inputCount}`);
    for (let index = 0; index < inputCount; index += 1) {
      await setInputValue(inputs.nth(index), "");
    }
    await page.waitForFunction(() => document.body.classList.contains("kggAlwaysCollapsed"));
    await setCardOpen(page, card, false);
    await assertVisibleBadge(page, card, "open", "○ Offen");

    await setCardOpen(page, card, true);
    await setInputValue(inputs.nth(0), "10");
    await setCardOpen(page, card, false);
    await assertVisibleBadge(page, card, "partial", "◐ Teilweise");

    await setCardOpen(page, card, true);
    await setInputValue(inputs.nth(1), "12");
    await setCardOpen(page, card, false);
    await assertVisibleBadge(page, card, "partial", "◐ Teilweise");

    await setCardOpen(page, card, true);
    for (let index = 2; index < inputCount; index += 1) {
      await setInputValue(inputs.nth(index), String(12 + index));
    }
    await setCardOpen(page, card, false);
    await assertVisibleBadge(page, card, "done", "✓ Bearbeitet");

    await setCardOpen(page, card, true);
    for (let index = 0; index < inputCount; index += 1) {
      await setInputValue(inputs.nth(index), "");
    }
    const pain = card.locator(".pain input").first();
    if (await pain.count()) await setInputValue(pain, "7");
    await setCardOpen(page, card, false);
    await assertVisibleBadge(page, card, "open", "○ Offen");

    console.log(JSON.stringify({
      status: "PASS",
      test: "patient-runtime-progress",
      version: workerVersion,
      freshControlledNoReload: true,
      mainDocumentNavigations: firstLoadEvidence.mainDocumentNavigations,
      navigationTypes: firstLoadEvidence.navigationTypes,
      requiredGlobals: FIRST_LOAD_GLOBALS.length,
      requiredModules: FIRST_LOAD_MODULES.length,
    }));
  } finally {
    await context.close();
    await browser.close();
    await new Promise((resolve) => server.close(resolve));
  }
}

main().catch((error) => {
  console.error(`Patient runtime/progress Playwright smoke failed: ${error.stack || error.message}`);
  process.exitCode = 1;
});
