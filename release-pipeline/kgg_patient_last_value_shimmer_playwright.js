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
  if ((!target.startsWith(`${ROOT}${path.sep}`) && target !== ROOT) || !fs.existsSync(target) || !fs.statSync(target).isFile()) return null;
  return target;
}

function sourceContract() {
  const hints = fs.readFileSync(path.join(ROOT, "patient-last-value-hints.js"), "utf8");
  const index = fs.readFileSync(path.join(ROOT, "index.html"), "utf8");
  const worker = fs.readFileSync(path.join(ROOT, "service-worker.js"), "utf8");
  const selector = "#padLast.kggPatientApplyShimmer";
  assert(hints.includes("const V='last-value-hints-v4-apply-shimmer';"), "shimmer module version marker is missing");
  assert(hints.includes("window.__kggLastValueHintsPatchedV4"), "shimmer module patch guard was not versioned");
  assert(hints.includes(selector), "shimmer must target only #padLast");
  assert(hints.includes("@media (prefers-reduced-motion:reduce)"), "reduced-motion opt-out is missing");
  assert(hints.includes("b.classList.add('kggPatientApplyShimmer')"), "enabled apply state does not opt into the shimmer");
  assert(hints.includes("b.classList.remove('kggPatientApplyShimmer')"), "disabled apply state does not remove the shimmer");
  assert(!hints.includes("button::after"), "shimmer selector must not target generic buttons");
  const script = "./patient-last-value-hints.js?v=last-value-button-shimmer-1";
  assert((index.match(new RegExp(script.replace(/[.?]/g, "\\$&"), "g")) || []).length === 1, "index must load the shimmer module exactly once");
  assert(worker.includes(script), "service worker must cache-bust the shimmer module");
}

async function openCard(page, index) {
  await page.evaluate((cardIndex) => {
    const card = document.querySelectorAll("#list .ex")[cardIndex];
    if (card && !card.classList.contains("kggOpen")) card.click();
  }, index);
  await page.waitForFunction((cardIndex) => Boolean(document.querySelectorAll("#list .ex")[cardIndex]?.classList.contains("kggOpen")), index);
}

async function main() {
  sourceContract();
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
  const context = await browser.newContext({ viewport: { width: 390, height: 844 }, serviceWorkers: "block" });
  const page = await context.newPage();
  const plan = {
    i: "last-value-shimmer-playwright",
    t: "Vorwert übernehmen",
    v: 1,
    d: 6,
    e: [
      ["Beinpresse", 2, "B", "kg", "Wdh"],
      ["Rudern", 1, "B", "kg", "Wdh"],
    ],
  };
  const payload = `KGGH2:${encodePlan(plan)}`;
  const url = `http://127.0.0.1:${port}/kgg/?plan=${encodeURIComponent(payload)}`;

  try {
    await page.goto(url, { waitUntil: "domcontentloaded" });
    await page.waitForFunction(() => window.__kggLastValueHints === "last-value-hints-v4-apply-shimmer");
    await page.locator("#list .ex").first().waitFor({ state: "visible" });
    const apply = page.locator("#padLast");
    await openCard(page, 0);
    await page.locator("#list .ex").nth(0).locator(".set input.num").first().click();
    await page.locator("#pad").waitFor({ state: "visible" });
    const before = await apply.evaluate((button) => {
      const rect = button.getBoundingClientRect();
      return { disabled: button.disabled, shimmer: button.classList.contains("kggPatientApplyShimmer"), width: rect.width, height: rect.height };
    });
    assert(before.disabled && !before.shimmer, "empty previous-value button must stay disabled and still");
    await page.evaluate(() => closePad(false));

    await page.evaluate(() => put(0, 1, "B", "a", "42"));
    const secondSetWeight = page.locator("#list .ex").nth(0).locator(".set input.num").nth(2);
    await secondSetWeight.click();
    await page.locator("#pad").waitFor({ state: "visible" });
    await apply.waitFor({ state: "visible" });

    const active = await apply.evaluate((button) => {
      const rect = button.getBoundingClientRect();
      const shimmer = getComputedStyle(button, "::after");
      const marked = [...document.querySelectorAll(".kggPatientApplyShimmer")].map((element) => element.id);
      const otherAnimated = [...document.querySelectorAll("button")]
        .filter((element) => element !== button && getComputedStyle(element, "::after").animationName.includes("kggPatientApplyShimmer"))
        .map((element) => element.id || element.textContent.trim());
      return {
        tag: button.tagName,
        type: button.getAttribute("type"),
        onclick: button.getAttribute("onclick"),
        disabled: button.disabled,
        text: button.textContent,
        marked,
        otherAnimated,
        width: rect.width,
        height: rect.height,
        animationName: shimmer.animationName,
        animationDuration: shimmer.animationDuration,
        pointerEvents: shimmer.pointerEvents,
      };
    });
    assert(active.tag === "BUTTON" && active.onclick === "padUseLast()", "apply button semantics changed");
    assert(!active.disabled && active.text.includes("42") && !active.text.includes("kein Vorwert"), "previous value no longer enables the apply button");
    assert(active.marked.length === 1 && active.marked[0] === "padLast", `shimmer escaped the apply button: ${JSON.stringify(active.marked)}`);
    assert(active.otherAnimated.length === 0, `shimmer animates another button: ${JSON.stringify(active.otherAnimated)}`);
    assert(active.animationName === "kggPatientApplyShimmer" && active.animationDuration === "5.8s", "apply shimmer animation contract is missing");
    assert(active.pointerEvents === "none", "shimmer overlay must not intercept the button tap");
    assert(Math.abs(active.width - before.width) < 0.1 && Math.abs(active.height - before.height) < 0.1, "shimmer changed button layout");
    await apply.click();
    assert((await page.locator("#padVal").innerText()) === "42", "apply button no longer transfers the previous value");

    await page.emulateMedia({ reducedMotion: "reduce" });
    const reduced = await apply.evaluate((button) => {
      const shimmer = getComputedStyle(button, "::after");
      return { display: shimmer.display, animationName: shimmer.animationName };
    });
    assert(reduced.display === "none" && reduced.animationName === "none", `reduced motion must disable shimmer: ${JSON.stringify(reduced)}`);

    await page.evaluate(() => closePad(false));
    await page.locator("#list .ex").nth(0).locator(".set input.num").nth(1).click();
    const disabled = await apply.evaluate((button) => ({ disabled: button.disabled, shimmer: button.classList.contains("kggPatientApplyShimmer") }));
    assert(disabled.disabled && !disabled.shimmer, "button shimmer remains active without a prior value");
    console.log("Patient last-value apply shimmer Playwright smoke: PASS");
  } finally {
    await context.close();
    await browser.close();
    await new Promise((resolve) => server.close(resolve));
  }
}

main().catch((error) => {
  console.error(`Patient last-value apply shimmer Playwright smoke failed: ${error.stack || error.message}`);
  process.exitCode = 1;
});
