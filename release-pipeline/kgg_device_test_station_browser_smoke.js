#!/usr/bin/env node
"use strict";

const crypto = require("crypto");
const fs = require("fs");
const path = require("path");
const { chromium } = require("playwright");

const ROOT = path.resolve(__dirname, "..");
const HTML_PATH = path.join(ROOT, "kgg-update", "index.html");
const FIXTURE_SCRIPT = path.join(ROOT, "android-wrapper", "app", "src", "preview", "assets", "android", "kgg_dual_device_fixtures.js");
const STATION_SCRIPT = path.join(ROOT, "android-wrapper", "app", "src", "preview", "assets", "android", "kgg_device_test_station.js");
const SCREENSHOT_PATH = path.join(ROOT, "tmp", "kgg-dual-device-station-browser.png");
const API = require(FIXTURE_SCRIPT);

function fail(message) { throw new Error(message); }

function makeJob() {
  const job = {
    kind: API.jobKind,
    schemaVersion: 1,
    sessionId: "kgg-test-" + "c".repeat(32),
    requestId: "dual-device-browser-smoke",
    sourceSha: "b".repeat(40),
    patchHash: "d".repeat(64),
    jobHash: "0".repeat(64),
    patientPwaUrl: "https://kayus24.github.io/kgg-patient-preview/device-test/",
    profile: "quick",
    recipeVersion: API.version,
    createdAt: new Date(Date.now() - 60_000).toISOString(),
    expiresAt: new Date(Date.now() + 60 * 60 * 1000).toISOString(),
    fixtures: API.fixturesForProfile("quick"),
    syntheticOnly: true,
  };
  job.jobHash = crypto.createHash("sha256").update(API.jobHashInput(job), "utf8").digest("hex");
  return job;
}

async function main() {
  const job = makeJob();
  const jobUrl = "https://raw.githubusercontent.com/Kayus24/kgg/gpt-preview/device-tests/dual-device-browser-smoke/job.json";
  const browser = await chromium.launch({ headless: true });
  const page = await browser.newPage({ viewport: { width: 1180, height: 820 }, hasTouch: true });
  await page.route(jobUrl, (route) => route.fulfill({ status: 200, contentType: "application/json", body: JSON.stringify(job) }));
  try {
    await page.goto("file://" + HTML_PATH.replace(/\\/g, "/"), { waitUntil: "domcontentloaded", timeout: 60000 });
    await page.evaluate(({ job, jobUrl }) => {
      window.KGGPreviewContext = {
        requestId: job.requestId,
        patchHash: job.patchHash,
        baseSha: job.sourceSha,
        commitSha: job.sourceSha,
        previewVersion: "0.2.14-v404-dual-device-qr-test",
        deviceTestSessionId: job.sessionId,
        deviceTestJobHash: job.jobHash,
        deviceTestJobUrl: jobUrl,
        patientPwaUrl: job.patientPwaUrl,
        deviceTestProfile: job.profile,
      };
      window.KGGDeviceTestStation = {
        beginSession: () => JSON.stringify({
          ok: true,
          active: true,
          sessionId: job.sessionId,
          startedAt: new Date().toISOString(),
          previewRequestId: job.requestId,
          previewVersion: "0.2.14-v404-dual-device-qr-test",
          jobHash: job.jobHash,
          profile: job.profile,
        }),
        getDeviceInfo: () => JSON.stringify({ class: "android-tablet", runtime: "synthetic", screen: { width: 1600, height: 2560, orientation: "landscape" }, wakeLock: "active" }),
        endSession: () => JSON.stringify({ ok: true, overallStatus: "passed" }),
        openReportIssue: () => true,
      };
    }, { job, jobUrl });
    await page.addScriptTag({ path: FIXTURE_SCRIPT });
    await page.addScriptTag({ path: STATION_SCRIPT });
    const launcher = page.locator("#kgg-device-test-station button");
    if ((await launcher.count()) !== 1 || (await launcher.textContent()).trim() !== "Teststation laden") fail("v404 launcher missing");
    await launcher.click();
    await page.locator("#kgg-device-test-station h2").filter({ hasText: "Oppo mit Test verbinden" }).waitFor({ timeout: 10000 });
    if ((await page.locator("#kgg-device-test-station .qr-stage img").count()) !== 1) fail("pairing QR missing");
    if ((await page.locator("#kgg-device-test-station .marker").count()) !== 4) fail("test-frame markers missing");
    if ((await page.locator("#kgg-device-test-station button[data-status]").count()) !== 3) fail("status buttons missing");
    await page.locator("#kgg-device-test-station button[data-status=passed]").click();
    await page.locator("#kgg-device-test-station h2").filter({ hasText: "h2-1-baseline" }).waitFor();
    fs.mkdirSync(path.dirname(SCREENSHOT_PATH), { recursive: true });
    await page.screenshot({ path: SCREENSHOT_PATH, fullPage: false });
    console.log(JSON.stringify({ ok: true, suite: "dual-device-station-browser", firstStep: "pairing", nextStep: "h2-1-baseline", screenshot: SCREENSHOT_PATH }, null, 2));
  } finally {
    await browser.close();
  }
}

main().catch((error) => {
  console.error("ERROR: " + (error && error.stack ? error.stack : String(error)));
  process.exit(1);
});
