#!/usr/bin/env node
"use strict";

const fs = require("fs");
const http = require("http");
const path = require("path");
const { chromium } = require("playwright");

const liveRoot = path.resolve(process.argv[2] || "");
const previewRoot = path.resolve(process.argv[3] || "");
const requestId = String(process.argv[4] || path.basename(previewRoot)).toLowerCase();
const secondRequestId = requestId === "preview-two" ? "preview-three" : "preview-two";

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

function safeTarget(root, relative) {
  const target = path.resolve(root, relative);
  if (!target.startsWith(`${root}${path.sep}`) && target !== root) return null;
  if (!fs.existsSync(target) || !fs.statSync(target).isFile()) return null;
  return target;
}

function resolveFile(urlPath) {
  const pathname = decodeURIComponent(new URL(urlPath, "http://local").pathname);
  const livePrefix = "/kgg/";
  const previewPrefix = "/kgg-patient-preview/previews/";
  if (pathname.startsWith(livePrefix)) {
    return safeTarget(liveRoot, pathname.slice(livePrefix.length) || "index.html");
  }
  if (pathname.startsWith(previewPrefix)) {
    const remainder = pathname.slice(previewPrefix.length);
    const match = remainder.match(/^([a-z0-9][a-z0-9-]{5,63})\/(.*)$/i);
    if (!match) return null;
    return safeTarget(previewRoot, match[2] || "index.html");
  }
  return null;
}

async function loadPlan(page, url, expectedTitle) {
  await page.goto(url, { waitUntil: "networkidle" });
  await page.locator("#title").waitFor({ state: "visible" });
  assert((await page.locator("#title").innerText()) === expectedTitle, `expected ${expectedTitle}`);
}

async function scopeEvidence(page) {
  return page.evaluate(() => ({
    scope: window.__KGG_STORAGE_SCOPE__ || null,
    currentPlanStored: localStorage.getItem("kggCurrentPlanV1") !== null,
    visibleKeys: Array.from({ length: localStorage.length }, (_, index) => localStorage.key(index)).sort(),
  }));
}

async function main() {
  assert(fs.existsSync(path.join(liveRoot, "index.html")), "live runtime root is missing index.html");
  assert(fs.existsSync(path.join(previewRoot, "index.html")), "preview runtime root is missing index.html");
  assert(fs.existsSync(path.join(previewRoot, "patient-storage-scope.js")), "preview runtime is missing storage scope helper");

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
  const origin = `http://127.0.0.1:${port}`;
  const browser = await chromium.launch({ headless: true });
  const context = await browser.newContext({ serviceWorkers: "allow" });
  const livePlan = {
    i: "live-storage-sentinel",
    t: "KGG LIVE STORAGE SENTINEL",
    v: 1,
    d: 6,
    e: [["Synthetische Live-Uebung", 1, "B", "kg", "Wdh", "1", "2"]],
  };
  const previewPlan = {
    i: "preview-storage-one",
    t: "KGG PREVIEW STORAGE TEST ONE",
    v: 1,
    d: 6,
    e: [["Synthetische Preview-Uebung Eins", 1, "B", "kg", "Wdh", "3", "4"]],
  };
  const secondPreviewPlan = {
    i: "preview-storage-two",
    t: "KGG PREVIEW STORAGE TEST TWO",
    v: 1,
    d: 6,
    e: [["Synthetische Preview-Uebung Zwei", 1, "B", "kg", "Wdh", "5", "6"]],
  };
  const encode = (plan) => encodeURIComponent(`KGGH2:${encodePlan(plan)}`);
  const live = await context.newPage();
  const previewOne = await context.newPage();
  const previewTwo = await context.newPage();

  try {
    await loadPlan(live, `${origin}/kgg/?plan=${encode(livePlan)}`, livePlan.t);
    await live.evaluate(() => localStorage.setItem("kggLiveStorageSentinel", "preserve"));
    const liveBefore = await scopeEvidence(live);
    assert(!liveBefore.scope, "live runtime unexpectedly installed preview storage scope");

    await loadPlan(
      previewOne,
      `${origin}/kgg-patient-preview/previews/${requestId}/?plan=${encode(previewPlan)}`,
      previewPlan.t,
    );
    const firstPreview = await scopeEvidence(previewOne);
    assert(firstPreview.scope?.kind === "preview", "preview storage scope did not initialize");
    assert(firstPreview.scope.requestId === requestId, "preview storage scope request id mismatch");
    assert(firstPreview.scope.prefix === `preview:${requestId}:`, "preview storage namespace mismatch");
    assert(firstPreview.currentPlanStored, "preview plan was not stored in its namespace");

    await loadPlan(
      previewTwo,
      `${origin}/kgg-patient-preview/previews/${secondRequestId}/?plan=${encode(secondPreviewPlan)}`,
      secondPreviewPlan.t,
    );
    const secondPreview = await scopeEvidence(previewTwo);
    assert(secondPreview.scope?.prefix === `preview:${secondRequestId}:`, "second preview namespace mismatch");

    await previewOne.reload({ waitUntil: "networkidle" });
    assert((await previewOne.locator("#title").innerText()) === previewPlan.t, "preview reload lost its own plan");
    await live.reload({ waitUntil: "networkidle" });
    assert((await live.locator("#title").innerText()) === livePlan.t, "live reload changed existing live plan");

    const storageState = await context.storageState();
    const localStorage = storageState.origins.find((entry) => entry.origin === origin)?.localStorage || [];
    const physicalKeys = localStorage.map((entry) => entry.name).sort();
    assert(physicalKeys.includes("kggCurrentPlanV1"), "live storage key was not preserved");
    assert(physicalKeys.includes(`preview:${requestId}:kggCurrentPlanV1`), "first preview key was not namespaced");
    assert(physicalKeys.includes(`preview:${secondRequestId}:kggCurrentPlanV1`), "second preview key was not namespaced");
    assert(
      physicalKeys
        .filter((key) => key.includes("kggCurrentPlanV1") && key !== "kggCurrentPlanV1")
        .every((key) => key.startsWith("preview:")),
      "preview wrote an unscoped current plan",
    );

    console.log(JSON.stringify({
      status: "PASS",
      test: "patient-preview-storage-isolation",
      livePlanPreserved: true,
      previewPlanReloadPreserved: true,
      requestScopedPreviewNamespaces: [requestId, secondRequestId],
      physicalKeyNamesChecked: physicalKeys.filter((key) => key === "kggCurrentPlanV1" || key.endsWith(":kggCurrentPlanV1")),
    }, null, 2));
  } finally {
    await context.close();
    await browser.close();
    await new Promise((resolve) => server.close(resolve));
  }
}

main().catch((error) => {
  console.error(`KGG patient preview storage isolation smoke FAIL: ${error.stack || error.message}`);
  process.exitCode = 1;
});
