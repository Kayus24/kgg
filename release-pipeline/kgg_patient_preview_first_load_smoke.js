#!/usr/bin/env node
"use strict";

const fs = require("fs");
const http = require("http");
const path = require("path");
const { chromium } = require("playwright");

const runtimeRoot = path.resolve(process.argv[2] || "");

function assert(condition, message) {
  if (!condition) throw new Error(message);
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
  await context.addInitScript(() => {
    Object.defineProperty(navigator, "mediaDevices", {
      configurable: true,
      value: { getUserMedia: () => Promise.reject(new Error("camera unavailable in first-load smoke")) },
    });
  });
  const page = await context.newPage();
  const pageErrors = [];
  page.on("pageerror", (error) => pageErrors.push(error.message));
  page.on("request", (request) => requests.push(request.url()));

  try {
    await page.goto(`http://127.0.0.1:${port}/`, { waitUntil: "networkidle" });
    await page.locator("#kggQrRescue").waitFor({ state: "visible" });
    assert((await page.locator("#kggPlanScanBtn").count()) === 1, "patient scanner header button was not created exactly once");
    assert(await page.evaluate(() => Boolean(window.__kggStartScanVersion)), "patient scanner module did not initialize on first load");
    const scannerRequests = requests.filter((url) => url.includes("/patient-start-scan.js"));
    assert(scannerRequests.length === 1, `patient scanner loaded ${scannerRequests.length} times on first load`);
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
    assert(pageErrors.length === 0, `first-load preview raised page errors: ${pageErrors.join(" | ")}`);
  } finally {
    await context.close();
    await browser.close();
    await new Promise((resolve) => server.close(resolve));
  }

  console.log(JSON.stringify({
    status: "PASS",
    runtimeRoot,
    scannerRequests: 1,
    rescueVisibleWithoutServiceWorker: true,
    cameraFallbackOpened: true,
  }));
}

main().catch((error) => {
  console.error(`KGG patient preview first-load smoke FAIL: ${error.stack || error.message}`);
  process.exitCode = 1;
});
