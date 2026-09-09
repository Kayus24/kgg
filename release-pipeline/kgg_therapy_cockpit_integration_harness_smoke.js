#!/usr/bin/env node
"use strict";

/* Browser verification for the human-facing integration harness. The harness
   itself loads the generated Admin source and reports the measured geometry. */
const fs = require("fs");
const http = require("http");
const path = require("path");
const { chromium } = require("playwright");

const ROOT = path.resolve(__dirname, "..");
const HARNESS_PATH = path.join(ROOT, "release-pipeline", "kgg_therapy_cockpit_integration_harness.html");
const MIME = { ".html": "text/html; charset=utf-8", ".js": "text/javascript; charset=utf-8", ".json": "application/json; charset=utf-8", ".css": "text/css; charset=utf-8" };

function assert(value, message) { if (!value) throw new Error(message); }
function safePath(requestUrl) {
  const pathname = decodeURIComponent(new URL(requestUrl, "http://127.0.0.1").pathname);
  const relative = pathname.replace(/^\/+/, "") || "release-pipeline/kgg_therapy_cockpit_integration_harness.html";
  const candidate = path.resolve(ROOT, relative);
  return candidate === ROOT || candidate.startsWith(ROOT + path.sep) ? candidate : null;
}
function startServer() {
  const server = http.createServer((request, response) => {
    const file = safePath(request.url);
    if (!file || !fs.existsSync(file) || fs.statSync(file).isDirectory()) { response.writeHead(404); response.end("not found"); return; }
    response.writeHead(200, { "Content-Type": MIME[path.extname(file).toLowerCase()] || "application/octet-stream", "Cache-Control": "no-store", "Access-Control-Allow-Origin": "*" });
    fs.createReadStream(file).pipe(response);
  });
  return new Promise(resolve => server.listen(0, "127.0.0.1", () => resolve(server)));
}

(async () => {
  assert(fs.existsSync(HARNESS_PATH), "integration harness HTML fehlt");
  const server = await startServer();
  const port = server.address().port;
  const browser = await chromium.launch({ headless: true });
  const context = await browser.newContext({ viewport: { width: 1440, height: 1000 }, locale: "de-DE" });
  const page = await context.newPage();
  const errors = [];
  page.on("pageerror", error => errors.push(error.message));
  try {
    await page.goto(`http://127.0.0.1:${port}/release-pipeline/kgg_therapy_cockpit_integration_harness.html`, { waitUntil: "domcontentloaded", timeout: 30000 });
    const results = [];
    for (const viewport of ["820x1180", "1024x768", "1280x800"]) {
      await page.locator(`[data-viewport="${viewport}"]`).click();
      await page.locator("#runAll").click();
      await page.waitForFunction(() => window.KGGCockpitIntegrationReport && window.KGGCockpitIntegrationReport.finishedAt, null, { timeout: 90000 });
      const result = await page.evaluate(() => window.KGGCockpitIntegrationReport);
      assert(result && result.pass === true, `Harness meldet FAIL bei ${viewport}: ${JSON.stringify(result)}`);
      assert(Array.isArray(result.checks) && result.checks.length >= 7, "Harness hat zu wenige Prüfungen ausgeführt");
      results.push({ viewport: result.viewport, checks: result.checks.map(item => item.label), snapshots: Object.keys(result.snapshots) });
      await page.evaluate(() => { window.KGGCockpitIntegrationReport = null; });
    }
    assert(errors.length === 0, `Harness page errors: ${errors.join(" | ")}`);
    console.log(JSON.stringify({ status: "PASS", harness: "kgg-therapy-cockpit-integration/v1", viewports: results }, null, 2));
  } finally {
    await context.close();
    await browser.close();
    await new Promise(resolve => server.close(resolve));
  }
})().catch(error => { console.error(error.stack || error); process.exitCode = 1; });
