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
  const requestId = "dual-device-browser-smoke";
  const job = {
    kind: API.jobKind,
    schemaVersion: 1,
    sessionId: "kgg-test-" + "c".repeat(32),
    requestId,
    sourceSha: "b".repeat(40),
    patchHash: "d".repeat(64),
    jobHash: "0".repeat(64),
    patientPwaUrl: "https://kayus24.github.io/kgg-patient-preview/device-test/" + requestId + "/12345-1/",
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
  const manifestUrl = "https://raw.githubusercontent.com/Kayus24/kgg/gpt-preview/previews/index.json";
  const jobUrl = "https://raw.githubusercontent.com/Kayus24/kgg/gpt-preview/device-tests/" + job.requestId + "/job.json";
  const previewUrl = "https://raw.githubusercontent.com/Kayus24/kgg/gpt-preview/previews/" + job.requestId + "/admin.html";
  const pwaMetaUrl = job.patientPwaUrl + "device-test-meta.json";
  const latest = {
    kind: "kgg_gpt_preview",
    sourceType: "existing-main",
    requestId: job.requestId,
    patchHash: job.patchHash,
    sourceSha: job.sourceSha,
    baseSha: job.sourceSha,
    commitSha: job.sourceSha,
    baseVersionCode: 81,
    rolloutCode: 200,
    title: "Pinned main device test",
    summary: "Browser regression fixture",
    versionName: "1.0.81-browser-smoke",
    createdAt: new Date().toISOString(),
    url: previewUrl,
    sha256: "e".repeat(64),
    deviceTestJobUrl: jobUrl,
  };
  const manifest = { kind: "kgg_gpt_preview_manifest", version: 1, previews: [latest], latest };
  const staleApkContextA = {
    requestId: "apk-context-a",
    patchHash: "1".repeat(64),
    baseSha: "a".repeat(40),
    commitSha: "a".repeat(40),
    previewVersion: "0.2.14-v404-dual-device-qr-test",
    deviceTestSessionId: "kgg-test-" + "a".repeat(32),
    deviceTestJobHash: "2".repeat(64),
    deviceTestJobUrl: "https://raw.githubusercontent.com/Kayus24/kgg/gpt-preview/device-tests/apk-context-a/job.json",
    patientPwaUrl: "https://kayus24.github.io/kgg-patient-preview/device-test/apk-context-a/12344-1/",
    deviceTestProfile: "full",
  };
  let pwaMeta = {
    kind: "kgg_device_test_pwa_meta",
    schemaVersion: 1,
    sourceSha: staleApkContextA.commitSha,
    jobHash: staleApkContextA.deviceTestJobHash,
    requestId: staleApkContextA.requestId,
    syntheticOnly: true,
  };

  const browser = await chromium.launch({ headless: true });
  const page = await browser.newPage({ viewport: { width: 1180, height: 820 }, hasTouch: true });
  await page.route(manifestUrl, (route) => route.fulfill({ status: 200, contentType: "application/json", body: JSON.stringify(manifest) }));
  await page.route(jobUrl, (route) => route.fulfill({ status: 200, contentType: "application/json", body: JSON.stringify(job) }));
  await page.route(pwaMetaUrl, (route) => route.fulfill({ status: 200, contentType: "application/json", body: JSON.stringify(pwaMeta) }));
  try {
    await page.goto("file://" + HTML_PATH.replace(/\\/g, "/"), { waitUntil: "domcontentloaded", timeout: 60000 });
    await page.evaluate(({ job, staleApkContextA }) => {
      window.KGGPreviewContext = staleApkContextA;
      window.__runtimeContextSeen = null;
      window.KGGDeviceTestStation = {
        beginSession: (runtimeContextJson) => {
          const runtimeContext = JSON.parse(String(runtimeContextJson || "{}"));
          window.__runtimeContextSeen = runtimeContext;
          return JSON.stringify({
            ok: true,
            active: true,
            sessionId: runtimeContext.sessionId,
            startedAt: new Date().toISOString(),
            previewRequestId: runtimeContext.requestId,
            previewVersion: "0.2.14-v404-dual-device-qr-test",
            jobHash: runtimeContext.jobHash,
            profile: runtimeContext.profile,
            contextSource: "dynamic-preview-manifest",
          });
        },
        getDeviceInfo: () => JSON.stringify({ class: "android-tablet", runtime: "synthetic", screen: { width: 1600, height: 2560, orientation: "landscape" }, wakeLock: "active" }),
        endSession: () => JSON.stringify({ ok: true, overallStatus: "passed" }),
        openReportIssue: () => true,
      };
    }, { job, staleApkContextA });
    await page.addScriptTag({ path: FIXTURE_SCRIPT });
    await page.addScriptTag({ path: STATION_SCRIPT });
    let launcher = page.locator("#kgg-device-test-station button");
    if ((await launcher.count()) !== 1 || (await launcher.textContent()).trim() !== "Teststation laden") fail("v404 launcher missing");

    await launcher.click();
    await page.locator("#kgg-device-test-station h2").filter({ hasText: "Teststation blockiert" }).waitFor({ timeout: 10000 });
    if ((await page.evaluate(() => window.__runtimeContextSeen)) !== null) fail("native session started while patient PWA still belonged to run A");
    const warning = (await page.locator("#kgg-device-test-station .warning").textContent()) || "";
    if (!warning.includes("Patient-Test-PWA und Testauftrag stammen nicht aus demselben Lauf")) fail("cross-repo PWA mismatch was not reported");

    pwaMeta = {
      kind: "kgg_device_test_pwa_meta",
      schemaVersion: 1,
      sourceSha: job.sourceSha,
      jobHash: job.jobHash,
      requestId: job.requestId,
      syntheticOnly: true,
    };
    await page.locator("#kgg-device-test-station button").filter({ hasText: "Erneut versuchen" }).click();
    await page.locator("#kgg-device-test-station h2").filter({ hasText: "Oppo mit Test verbinden" }).waitFor({ timeout: 10000 });

    const runtimeContextSeen = await page.evaluate(() => window.__runtimeContextSeen);
    if (!runtimeContextSeen) fail("dynamic runtime context was not passed to native bridge");
    if (runtimeContextSeen.requestId !== job.requestId) fail("installed APK reused stale request A instead of B");
    if (runtimeContextSeen.sourceSha !== job.sourceSha) fail("installed APK reused stale source SHA A instead of B");
    if (runtimeContextSeen.sessionId !== job.sessionId) fail("installed APK reused stale session A instead of B");
    if (runtimeContextSeen.jobHash !== job.jobHash) fail("installed APK reused stale job hash A instead of B");
    if (runtimeContextSeen.jobUrl !== jobUrl) fail("installed APK did not use current job URL B");
    if (runtimeContextSeen.requestId === staleApkContextA.requestId || runtimeContextSeen.sourceSha === staleApkContextA.commitSha) fail("stale APK context A leaked into run B");
    if (!job.patientPwaUrl.includes("/" + job.requestId + "/12345-1/")) fail("patient PWA URL is not immutable per run");

    if ((await page.locator("#kgg-device-test-station .qr-stage img").count()) !== 1) fail("pairing QR missing");
    if ((await page.locator("#kgg-device-test-station .marker").count()) !== 4) fail("test-frame markers missing");
    if ((await page.locator("#kgg-device-test-station button[data-status]").count()) !== 3) fail("status buttons missing");
    await page.locator("#kgg-device-test-station button[data-status=passed]").click();
    await page.locator("#kgg-device-test-station h2").filter({ hasText: "h2-1-baseline" }).waitFor();
    fs.mkdirSync(path.dirname(SCREENSHOT_PATH), { recursive: true });
    await page.screenshot({ path: SCREENSHOT_PATH, fullPage: false });
    console.log(JSON.stringify({
      ok: true,
      suite: "dual-device-station-browser",
      regression: "apk-context-a-to-preview-job-b",
      pwaMismatchBlocked: true,
      immutablePatientPwa: true,
      staleRequest: staleApkContextA.requestId,
      activeRequest: runtimeContextSeen.requestId,
      activeSourceSha: runtimeContextSeen.sourceSha,
      activeSessionId: runtimeContextSeen.sessionId,
      activeJobHash: runtimeContextSeen.jobHash,
      activeJobUrl: runtimeContextSeen.jobUrl,
      patientPwaUrl: job.patientPwaUrl,
      firstStep: "pairing",
      nextStep: "h2-1-baseline",
      screenshot: SCREENSHOT_PATH,
    }, null, 2));
  } finally {
    await browser.close();
  }
}

main().catch((error) => {
  console.error("ERROR: " + (error && error.stack ? error.stack : String(error)));
  process.exit(1);
});
