#!/usr/bin/env node
"use strict";

const fs = require("fs");
const http = require("http");
const path = require("path");
const { chromium } = require("playwright");

const ROOT = path.resolve(__dirname, "..");

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

async function waitForControlledRuntime(page) {
  await page.evaluate(() => navigator.serviceWorker.ready);
  if (!(await page.evaluate(() => Boolean(navigator.serviceWorker.controller)))) {
    await page.reload({ waitUntil: "domcontentloaded" });
  }
  await page.waitForFunction(() => Boolean(navigator.serviceWorker && navigator.serviceWorker.controller), null, {
    timeout: 12000,
  });
  for (let attempt = 0; attempt < 3; attempt += 1) {
    await page.locator("#plan").waitFor({ state: "visible" });
    const hasRuntime = (await page.locator("#kgg-collapse-toggle").count()) > 0 &&
      (await page.locator("#kggAppVersion").count()) > 0 &&
      (await page.locator("#list .ex .kggCardProgress").count()) > 0;
    if (hasRuntime) {
      await page.locator("#kggAppVersion").waitFor({ state: "visible" });
      return;
    }
    await page.reload({ waitUntil: "domcontentloaded" });
  }
  const diagnostics = await page.evaluate(() => ({
    controlled: Boolean(navigator.serviceWorker && navigator.serviceWorker.controller),
    scripts: Array.from(document.scripts).map((script) => script.src).filter(Boolean),
    bodyClasses: document.body.className,
  }));
  throw new Error(`controlled patient runtime modules were not injected: ${JSON.stringify(diagnostics)}`);
}

async function setCardOpen(page, card, open) {
  const isOpen = await card.evaluate((element) => element.classList.contains("kggOpen"));
  if (isOpen !== open) await card.locator("h3").click();
  await page.waitForFunction(
    ({ open }) => Boolean(document.querySelector("#list .ex")?.classList.contains("kggOpen")) === open,
    { open }
  );
}

async function assertVisibleBadge(page, card, state, text) {
  const badge = card.locator(".kggCardProgress");
  await badge.waitFor({ state: "attached" });
  await page.waitForFunction(
    ({ state, text }) => {
      const card = document.querySelector("#list .ex");
      const badge = card && card.querySelector(".kggCardProgress");
      if (!card || !badge || card.classList.contains("kggOpen")) return false;
      const style = getComputedStyle(badge);
      const rect = badge.getBoundingClientRect();
      return badge.dataset.kggProgress === state && badge.textContent === text &&
        style.display !== "none" && style.visibility !== "hidden" && Number(style.opacity || "1") > 0 &&
        rect.width > 0 && rect.height > 0;
    },
    { state, text }
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
  const plan = {
    i: "progress-playwright-91",
    t: "Fortschritts-Sichtbarkeit",
    v: 1,
    d: 6,
    e: [["Beinpresse", 1, "B", "kg", "Wdh", "40", "10"]],
  };
  const payload = `KGGH2:${encodePlan(plan)}`;
  const url = `http://127.0.0.1:${port}/kgg/?plan=${encodeURIComponent(payload)}`;

  try {
    await page.goto(url, { waitUntil: "domcontentloaded" });
    await page.locator("#plan").waitFor({ state: "visible" });
    await waitForControlledRuntime(page);

    const workerVersion = await activeWorkerVersion(page);
    const visibleVersion = (await page.locator("#kggAppVersion").innerText()).replace(/^v/i, "");
    assert(workerVersion === expectedVersion, `active worker is v${workerVersion || "?"}, expected v${expectedVersion}`);
    assert(visibleVersion === workerVersion, `visible UI is v${visibleVersion || "?"}, worker is v${workerVersion || "?"}`);

    const card = page.locator("#list .ex").first();
    await card.waitFor({ state: "visible" });
    await setCardOpen(page, card, false);
    await assertVisibleBadge(page, card, "open", "○ Offen");

    await setCardOpen(page, card, true);
    const inputs = card.locator(".set input.num");
    assert((await inputs.count()) >= 2, "synthetic exercise exposes fewer than two normal fields");
    await inputs.nth(0).fill("10");
    await setCardOpen(page, card, false);
    await assertVisibleBadge(page, card, "partial", "◐ Teilweise");

    await setCardOpen(page, card, true);
    await inputs.nth(1).fill("12");
    await setCardOpen(page, card, false);
    await assertVisibleBadge(page, card, "done", "✓ Bearbeitet");

    await setCardOpen(page, card, true);
    await inputs.nth(0).fill("");
    await inputs.nth(1).fill("");
    const pain = card.locator(".pain input").first();
    if (await pain.count()) {
      await pain.evaluate((element) => {
        element.value = "7";
        element.dispatchEvent(new Event("input", { bubbles: true }));
        element.dispatchEvent(new Event("change", { bubbles: true }));
      });
    }
    await setCardOpen(page, card, false);
    await assertVisibleBadge(page, card, "open", "○ Offen");

    console.log(`Patient runtime/progress Playwright smoke: PASS (v${workerVersion})`);
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
