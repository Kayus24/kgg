#!/usr/bin/env node
"use strict";

const fs = require("fs");
const http = require("http");
const path = require("path");
const { chromium } = require("playwright");

const runtimeRoot = path.resolve(process.argv[2] || "");
const REQUIRED_MODULES = [
  "collapse-cards.js",
  "patient-card-progress.js",
  "patient-install-guide.js",
  "patient-install-prompt.js",
  "patient-plan-replace-slot-fix.js",
  "patient-start-scan.js",
  "patient-multiplan-db.js",
  "patient-plan-delete.js",
  "patient-card-settings.js",
  "patient-start-values-day1.js",
  "patient-day-history.js",
  "patient-media-retry-cache_v2.js",
  "patient-ui-micro-polish.js",
  "patient-pain-vertical-scale.js",
  "numpad-ui-fix.js",
  "patient-numpad-visibility-fix.js",
  "patient-extra-info-display.js",
  "patient-last-value-hints.js",
  "patient-set-summary-groups.js",
  "patient-qr-fullscreen.js",
  "patient-numpad-card-guard.js",
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

function resolveFile(urlPath) {
  const relative = decodeURIComponent(urlPath.split("?")[0]).replace(/^\/+/, "") || "index.html";
  const target = path.resolve(runtimeRoot, relative);
  if (!target.startsWith(`${runtimeRoot}${path.sep}`) && target !== runtimeRoot) return null;
  if (!fs.existsSync(target) || !fs.statSync(target).isFile()) return null;
  return target;
}

async function setInputValue(input, value) {
  await input.evaluate((element, nextValue) => {
    element.value = String(nextValue);
    element.dispatchEvent(new Event("input", { bubbles: true }));
    element.dispatchEvent(new Event("change", { bubbles: true }));
  }, value);
}

async function setCardOpen(page, card, open) {
  const current = await card.evaluate((element) => element.classList.contains("kggOpen"));
  if (current !== open) await card.locator("h3").click();
  await page.waitForFunction(
    ({ wanted }) => Boolean(document.querySelector("#list .ex")?.classList.contains("kggOpen")) === wanted,
    { wanted: open },
    { timeout: 10000 }
  );
}

async function assertVisibleBadge(page, state, text) {
  await page.waitForFunction(
    ({ state, text }) => {
      const card = document.querySelector("#list .ex");
      const badge = card?.querySelector(".kggCardProgress");
      if (!card || !badge || card.classList.contains("kggOpen") || !document.body.classList.contains("kggAlwaysCollapsed")) return false;
      const style = getComputedStyle(badge);
      const box = badge.getBoundingClientRect();
      return badge.dataset.kggProgress === state && badge.textContent === text &&
        style.display !== "none" && box.width > 0 && box.height > 0;
    },
    { state, text },
    { timeout: 10000 }
  );
}

async function assertStaticModules(page) {
  const counts = await page.evaluate((modules) => {
    const names = Array.from(document.scripts)
      .map((script) => script.src ? new URL(script.src, location.href).pathname.split("/").pop() : "")
      .filter(Boolean);
    return Object.fromEntries(modules.map((name) => [name, names.filter((current) => current === name).length]));
  }, REQUIRED_MODULES);
  for (const module of REQUIRED_MODULES) {
    assert(counts[module] === 1, `first root load has ${counts[module] || 0} copies of ${module}`);
  }
}

async function main() {
  assert(runtimeRoot && fs.existsSync(path.join(runtimeRoot, "index.html")), "preview runtime root is missing index.html");
  const requests = [];
  const server = http.createServer((request, response) => {
    const file = resolveFile(request.url || "/");
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
    serviceWorkers: "block",
  });
  const page = await context.newPage();
  await page.addInitScript(() => {
    localStorage.setItem("kggInstallAsked", "1");
    Object.defineProperty(navigator, "mediaDevices", {
      configurable: true,
      value: { getUserMedia: () => Promise.reject(new Error("camera unavailable in first-load smoke")) },
    });
  });
  const pageErrors = [];
  page.on("pageerror", (error) => pageErrors.push(error.message));
  page.on("request", (request) => requests.push(request.url()));

  try {
    await page.goto(`http://127.0.0.1:${port}/`, { waitUntil: "networkidle" });
    await page.locator("#kggQrRescue").waitFor({ state: "visible" });
    await assertStaticModules(page);
    assert(await page.evaluate(() => Boolean(window.__kggStartScanVersion)), "patient scanner module did not initialize on first load");
    assert(await page.evaluate(() => Boolean(window.__kggPatientMultiPlanDbAddon)), "multi-plan module did not initialize on first load");
    assert(await page.evaluate(() => Boolean(window.__kggPlanDelete)), "plan deletion module did not initialize on first load");
    assert(await page.evaluate(() => Boolean(window.__kggCardProgress)), "card-progress module did not initialize on first load");
    assert(await page.evaluate(() => Boolean(window.__kggSetSummaryGroups)), "set-summary module did not initialize on first load");
    assert(await page.evaluate(() => Boolean(window.KGGPatientMediaRetryCache)), "media module did not initialize on first load");

    const scannerRequests = requests.filter((url) => url.includes("/patient-start-scan.js"));
    assert(scannerRequests.length === 1, `patient scanner loaded ${scannerRequests.length} times on fresh root load`);
    const geometry = await page.evaluate(() => ({
      viewportWidth: document.documentElement.clientWidth,
      documentWidth: document.documentElement.scrollWidth,
    }));
    assert(geometry.documentWidth <= geometry.viewportWidth, "first-load scanner rescue causes horizontal overflow");

    await page.locator("#kggQrRescue .scanBig").click();
    await page.locator("#kggLiveScan").waitFor({ state: "visible" });
    await page.locator("#kggLiveScanFallback").waitFor({ state: "visible" });
    await page.locator(".kggLiveScanClose").click();
    await page.locator("#kggLiveScan").waitFor({ state: "detached" });

    const plan = {
      i: "first-load-plan-74",
      t: "Erster vollständiger Plan",
      v: 1,
      d: 6,
      e: [["Abduktion Maschine mit langem Übungsnamen", 3, "B", "kg", "Wdh", "", ""]],
    };
    const payload = `KGGH2:${encodePlan(plan)}`;
    await page.goto(`http://127.0.0.1:${port}/?plan=${encodeURIComponent(payload)}`, { waitUntil: "networkidle" });
    await page.locator("#plan").waitFor({ state: "visible" });
    await assertStaticModules(page);

    const card = page.locator("#list .ex").first();
    await card.waitFor({ state: "visible" });
    await page.waitForFunction(() => document.body.classList.contains("kggAlwaysCollapsed"));
    await assertVisibleBadge(page, "open", "○ Offen");

    await setCardOpen(page, card, true);
    const inputs = card.locator(".set input.num");
    const inputCount = await inputs.count();
    assert(inputCount === 6, `three bilateral sets should expose six fields, got ${inputCount}`);
    await setInputValue(inputs.nth(0), "40");
    await setCardOpen(page, card, false);
    await assertVisibleBadge(page, "partial", "◐ Teilweise");

    await setCardOpen(page, card, true);
    for (let index = 1; index < inputCount; index += 1) {
      await setInputValue(inputs.nth(index), String(40 + index));
    }
    await setCardOpen(page, card, false);
    await assertVisibleBadge(page, "done", "✓ Bearbeitet");

    const thumbGeometry = await page.evaluate(() => {
      const target = document.querySelector("#list .ex");
      const title = target?.querySelector("h3");
      if (!target || !title) return null;
      target.classList.add("kggHasThumb", "kggThumbReady");
      let thumb = target.querySelector(".kggCardThumb");
      if (!thumb) {
        thumb = document.createElement("div");
        thumb.className = "kggCardThumb";
        thumb.innerHTML = '<img alt="" src="data:image/gif;base64,R0lGODlhAQABAIAAAAAAAP///ywAAAAAAQABAAACAUwAOw==">';
        target.appendChild(thumb);
      }
      const titleBox = title.getBoundingClientRect();
      const thumbBox = thumb.getBoundingClientRect();
      return {
        titleRight: titleBox.right,
        thumbLeft: thumbBox.left,
        titleOverflow: title.scrollWidth > title.clientWidth,
        thumbVisible: getComputedStyle(thumb).display !== "none" && thumbBox.width > 0,
      };
    });
    assert(thumbGeometry?.thumbVisible, "closed-card thumbnail is not visible in fresh runtime");
    assert(!thumbGeometry.titleOverflow, "long exercise name overflows beneath the thumbnail");
    assert(thumbGeometry.titleRight <= thumbGeometry.thumbLeft, "exercise title overlaps the thumbnail");

    await page.evaluate(() => {
      const api = window.KGGPatientMultiPlan;
      const state = api.ensureState();
      const second = JSON.parse(JSON.stringify(state.plans[0]));
      second.i = "first-load-plan-74-second";
      second.t = "Zweiter Plan";
      state.plans.push(second);
      state.active = 0;
      localStorage.setItem("kggPatientMultiPlansV1", JSON.stringify(state));
    });
    await page.locator("#kggActionFab").click();
    await page.locator("#kggBubblePlans").click();
    await page.locator("#kggPlanDeletePanel").waitFor({ state: "visible" });
    const deleteButtons = page.locator("#kggPlanDeletePanel .kggPlanDeleteBtn");
    assert(await deleteButtons.count() === 2, "every deletable plan needs its own red x");
    const deleteUi = await deleteButtons.evaluateAll((buttons) => buttons.map((button) => ({
      text: button.textContent,
      ariaLabel: button.getAttribute("aria-label"),
    })));
    assert(deleteUi.every((button) => button.text === "×" && button.ariaLabel), "plan delete controls are not accessible red x buttons");

    let confirmation = "";
    page.once("dialog", async (dialog) => {
      confirmation = dialog.message();
      await dialog.accept();
    });
    await deleteButtons.nth(1).click();
    await page.waitForFunction(() => {
      try {
        return JSON.parse(localStorage.getItem("kggPatientMultiPlansV1") || "{}").plans?.length === 1;
      } catch {
        return false;
      }
    });
    assert(confirmation.includes("Zweiter Plan"), "red x did not keep the plan-specific confirmation");

    await page.locator("#kggActionFab").click();
    await page.locator("#kggBubblePlans").click();
    await page.locator("#kggPlanDeletePanel").waitFor({ state: "visible" });
    assert(await page.locator("#kggPlanDeletePanel .kggPlanDeleteBtn").count() === 0, "last remaining plan must not be deletable");

    assert(pageErrors.length === 0, `fresh root runtime raised page errors: ${pageErrors.join(" | ")}`);
  } finally {
    await context.close();
    await browser.close();
    await new Promise((resolve) => server.close(resolve));
  }

  console.log(JSON.stringify({
    status: "PASS",
    runtimeRoot,
    serviceWorkerBlocked: true,
    staticModules: REQUIRED_MODULES.length,
    scannerLoadedOnce: true,
    progressCheckedForAllFields: true,
    redXPlanDeletionChecked: true,
  }));
}

main().catch((error) => {
  console.error(`KGG patient preview first-load smoke FAIL: ${error.stack || error.message}`);
  process.exitCode = 1;
});
