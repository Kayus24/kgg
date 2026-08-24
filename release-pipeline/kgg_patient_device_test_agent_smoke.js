#!/usr/bin/env node
"use strict";

const crypto = require("crypto");
const fs = require("fs");
const http = require("http");
const path = require("path");
const { execFileSync } = require("child_process");
const { chromium } = require("playwright");

const ROOT = path.resolve(__dirname, "..");
const OUT = path.join(ROOT, "tmp", "patient-device-test-pwa");
const JOB_PATH = path.join(ROOT, "tmp", "patient-device-test-job.json");
const FIXTURE_SOURCE = path.join(ROOT, "android-wrapper", "app", "src", "preview", "assets", "android", "kgg_dual_device_fixtures.js");
const API = require(FIXTURE_SOURCE);

function fail(message) { throw new Error(message); }

function jobFixture() {
  const job = {
    kind: API.jobKind,
    schemaVersion: 1,
    sessionId: "kgg-test-" + "e".repeat(32),
    requestId: "patient-device-agent-smoke",
    sourceSha: "a".repeat(40),
    patchHash: "b".repeat(64),
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

function pairing(job, jobUrl) {
  return API.encodePairing({
    kind: API.pairingKind,
    schemaVersion: 1,
    sessionId: job.sessionId,
    requestId: job.requestId,
    sourceSha: job.sourceSha,
    jobHash: job.jobHash,
    profile: job.profile,
    jobUrl,
    patientPwaUrl: job.patientPwaUrl,
  });
}

function contentType(file) {
  if (file.endsWith(".html")) return "text/html; charset=utf-8";
  if (file.endsWith(".js")) return "text/javascript; charset=utf-8";
  if (file.endsWith(".json") || file.endsWith(".webmanifest")) return "application/json";
  if (file.endsWith(".png")) return "image/png";
  return "application/octet-stream";
}

function startServer() {
  return new Promise((resolve) => {
    const server = http.createServer((request, response) => {
      const clean = decodeURIComponent(new URL(request.url, "http://127.0.0.1").pathname).replace(/^\/+/, "") || "index.html";
      const file = path.resolve(OUT, clean);
      if (!file.startsWith(OUT + path.sep) || !fs.existsSync(file) || !fs.statSync(file).isFile()) {
        response.writeHead(404).end("not found");
        return;
      }
      response.writeHead(200, { "content-type": contentType(file), "cache-control": "no-store" });
      fs.createReadStream(file).pipe(response);
    });
    server.listen(0, "127.0.0.1", () => resolve(server));
  });
}

async function main() {
  const job = jobFixture();
  fs.mkdirSync(path.dirname(JOB_PATH), { recursive: true });
  fs.writeFileSync(JOB_PATH, JSON.stringify(job, null, 2) + "\n", "utf8");
  execFileSync("node", [
    path.join(ROOT, "release-pipeline", "kgg_dual_device_package.js"),
    "--source-sha", job.sourceSha,
    "--job-file", JOB_PATH,
    "--output", OUT,
  ], { cwd: ROOT, stdio: "pipe" });
  const server = await startServer();
  const port = server.address().port;
  const jobUrl = "https://raw.githubusercontent.com/Kayus24/kgg/gpt-preview/device-tests/patient-device-agent-smoke/job.json";
  const browser = await chromium.launch({ headless: true });
  const context = await browser.newContext({ viewport: { width: 412, height: 915 }, hasTouch: true, serviceWorkers: "block" });
  const page = await context.newPage();
  await page.addInitScript(() => {
    window.localStorage.setItem("kggCurrentPlanV1", "PERSONAL_SENTINEL");
  });
  await page.route(jobUrl, (route) => route.fulfill({ status: 200, contentType: "application/json", body: JSON.stringify(job) }));
  try {
    await page.goto(`http://127.0.0.1:${port}/?kggTest=${encodeURIComponent(pairing(job, jobUrl))}`, { waitUntil: "domcontentloaded", timeout: 60000 });
    await page.locator("#kgg-device-test-agent h2").filter({ hasText: "Oppo-Scanner" }).waitFor({ timeout: 15000 });
    if (!(await page.locator("#kgg-device-test-agent").innerText()).includes("h2-1-baseline")) fail("first scanner fixture missing");
    const preparation = await page.evaluate(() => {
      const meta = {
        decoder: "jsqr",
        recognitionMs: 850,
        qrWidthRatioPct: 42,
        distanceBand: "normal",
        frameWidth: 1280,
        frameHeight: 720,
        fpsBand: "10-plus",
        angleBand: "front",
        brightnessBand: "normal",
        blurBand: "sharp",
        testFrameStatus: "visible",
      };
      function fixtureCode(fixtureId) {
        const definition = window.KGGDualDeviceFixtures.fixtureById(fixtureId);
        const raw = window.KGGDualDeviceFixtures.syntheticPlan(definition);
        const code = definition.format === "KGGH3" ? window.KGGPlanFormat.encodeKggH3(raw) : window.KGGPlanFormat.encodeKggH2(raw);
        return { definition, code, expectedFingerprint: window.KGGDualDeviceFixtures.planFingerprint(raw) };
      }
      const first = fixtureCode("h2-1-baseline");
      const firstConsumed = window.KGGPatientDeviceTestObserver.consumeScan(first.code, meta);
      const second = fixtureCode("h2-7-legacy");
      const secondConsumed = window.KGGPatientDeviceTestObserver.consumeScan(second.code, meta);
      const product = fixtureCode("h3-7-normal");
      const productConsumed = window.KGGPatientDeviceTestObserver.consumeScan(product.code, meta);
      const testStorage = window.KGGDeviceTestStorage;
      const stateKey = Object.keys(testStorage).find((key) => key.startsWith("kgg_device_test_state_v404_"));
      return {
        firstConsumed,
        secondConsumed,
        productConsumed,
        productCode: product.code,
        expectedFingerprint: product.expectedFingerprint,
        state: JSON.parse(testStorage.getItem(stateKey)),
        body: document.querySelector("#kgg-device-test-agent").innerText,
      };
    });
    if (!preparation.firstConsumed || !preparation.secondConsumed) fail("capture-only fixture was passed to product import");
    if (preparation.productConsumed) fail("product fixture was consumed before the real product import");
    if (!preparation.body.includes("h3-7-normal")) fail("agent did not stop on the product import fixture");
    const serialized = JSON.stringify(preparation.state);
    if (serialized.includes("KGGH2:") || serialized.includes("SENTINEL-FIRST")) fail("raw QR or exercise names leaked into test state");
    const baselineTelemetry = preparation.state.telemetry["h2-1-baseline"];
    if (baselineTelemetry.exerciseCount !== 1 || baselineTelemetry.distanceBand !== "normal" || baselineTelemetry.testFrameStatus !== "visible") fail("bounded scan telemetry mismatch");

    await page.goto(`http://127.0.0.1:${port}/?plan=${encodeURIComponent(preparation.productCode)}`, { waitUntil: "domcontentloaded", timeout: 60000 });
    try {
      await page.waitForFunction(() => {
        const agent = document.querySelector("#kgg-device-test-agent");
        return agent && agent.innerText.includes("h3-12-normal");
      }, null, { timeout: 15000 });
    } catch (error) {
      const diagnostic = await page.evaluate(() => ({
        agent: document.querySelector("#kgg-device-test-agent") ? document.querySelector("#kgg-device-test-agent").innerText : "missing",
        error: String(window.__KGG_PLAN_FORMAT_ERROR || ""),
        rawKeys: Object.keys(window.localStorage),
        testKeys: window.KGGDeviceTestStorage ? Object.keys(window.KGGDeviceTestStorage) : [],
        saved: window.KGGDeviceTestStorage ? window.KGGDeviceTestStorage.getItem("kggCurrentPlanV1") : null,
      }));
      fail("product import did not advance: " + JSON.stringify(diagnostic));
    }
    const result = await page.evaluate(() => {
      const testStorage = window.KGGDeviceTestStorage;
      const stateKey = Object.keys(testStorage).find((key) => key.startsWith("kgg_device_test_state_v404_"));
      return {
        rawPersonal: window.localStorage.getItem("kggCurrentPlanV1"),
        stored: JSON.parse(testStorage.getItem("kggCurrentPlanV1") || "null"),
        state: JSON.parse(testStorage.getItem(stateKey)),
        visibleCards: document.querySelectorAll("#list .ex").length,
        body: document.querySelector("#kgg-device-test-agent").innerText,
        report: window.__kggPatientDeviceTestAgentTest.report(),
      };
    });
    if (result.rawPersonal !== "PERSONAL_SENTINEL") fail("test PWA changed non-test browser storage");
    if (!result.stored || !result.stored.plan || result.stored.plan.e.length !== 7 || result.visibleCards !== 7) fail("product plan was not stored and rendered completely");
    const productTelemetry = result.state.telemetry["h3-7-normal"];
    if (!productTelemetry || productTelemetry.storedFingerprint !== preparation.expectedFingerprint || productTelemetry.visibleExerciseCount !== 7) fail("product import telemetry mismatch: " + JSON.stringify({ expectedFingerprint: preparation.expectedFingerprint, productTelemetry, visibleCards: result.visibleCards }));
    const productTest = result.report.tests.find((test) => test.testId === "scan-h3-7-normal");
    const reportText = JSON.stringify(result.report);
    if (!productTest || productTest.status !== "passed" || result.report.role !== "scanner" || result.report.schemaVersion !== 2 || reportText.includes("KGGH2:") || reportText.includes("SENTINEL-FIRST")) fail("scanner report contract mismatch");
    fs.writeFileSync(path.join(ROOT, "tmp", "patient-device-test-report.json"), JSON.stringify(result.report, null, 2) + "\n", "utf8");

    const added = await page.evaluate(() => {
      const definition = window.KGGDualDeviceFixtures.fixtureById("h3-12-normal");
      const raw = window.KGGDualDeviceFixtures.syntheticPlan(definition);
      const ok = window.KGGPatientPlanSlots.addPlan(raw);
      const multi = JSON.parse(window.KGGDeviceTestStorage.getItem("kggPatientMultiPlansV1") || "null");
      const current = JSON.parse(window.KGGDeviceTestStorage.getItem("kggCurrentPlanV1") || "null");
      const replacement = window.KGGDualDeviceFixtures.syntheticPlan(window.KGGDualDeviceFixtures.fixtureById("h3-20-normal"));
      return {
        ok,
        planCount: multi && multi.plans ? multi.plans.length : 0,
        active: multi ? multi.active : -1,
        currentExercises: current && current.plan && current.plan.e ? current.plan.e.length : 0,
        replacementCode: window.KGGPlanFormat.encodeKggH3(replacement),
      };
    });
    if (!added.ok || added.planCount !== 2 || added.active !== 1 || added.currentExercises !== 12) fail("isolated add-plan path failed: " + JSON.stringify(added));

    await page.goto(`http://127.0.0.1:${port}/?plan=${encodeURIComponent(added.replacementCode)}`, { waitUntil: "domcontentloaded", timeout: 60000 });
    await page.locator("#kggPlanLinkChoiceReplace").waitFor({ timeout: 15000 });
    await page.locator("#kggPlanLinkChoiceReplace").click();
    await page.waitForFunction(() => {
      const current = JSON.parse(window.KGGDeviceTestStorage.getItem("kggCurrentPlanV1") || "null");
      const multi = JSON.parse(window.KGGDeviceTestStorage.getItem("kggPatientMultiPlansV1") || "null");
      return !document.querySelector("#kggPlanLinkChoiceBackdrop") && current && current.plan && current.plan.e.length === 20 && multi && multi.plans.length === 2;
    }, null, { timeout: 15000 });
    const cancelCode = await page.evaluate(() => {
      const raw = window.KGGDualDeviceFixtures.syntheticPlan(window.KGGDualDeviceFixtures.fixtureById("h3-7-normal"));
      return window.KGGPlanFormat.encodeKggH3(raw);
    });
    await page.goto(`http://127.0.0.1:${port}/?plan=${encodeURIComponent(cancelCode)}`, { waitUntil: "domcontentloaded", timeout: 60000 });
    await page.locator("#kggPlanLinkChoiceCancel").waitFor({ timeout: 15000 });
    await page.locator("#kggPlanLinkChoiceCancel").click();
    const choices = await page.evaluate(() => {
      const current = JSON.parse(window.KGGDeviceTestStorage.getItem("kggCurrentPlanV1") || "null");
      const multi = JSON.parse(window.KGGDeviceTestStorage.getItem("kggPatientMultiPlansV1") || "null");
      return {
        dialogOpen: !!document.querySelector("#kggPlanLinkChoiceBackdrop"),
        rawPersonal: window.localStorage.getItem("kggCurrentPlanV1"),
        planCount: multi && multi.plans ? multi.plans.length : 0,
        active: multi ? multi.active : -1,
        currentExercises: current && current.plan && current.plan.e ? current.plan.e.length : 0,
      };
    });
    if (choices.dialogOpen || choices.rawPersonal !== "PERSONAL_SENTINEL" || choices.planCount !== 2 || choices.active !== 1 || choices.currentExercises !== 20) fail("replace/cancel choice path failed: " + JSON.stringify(choices));
    await page.screenshot({ path: path.join(ROOT, "tmp", "patient-device-test-agent.png"), fullPage: false });
    console.log(JSON.stringify({ ok: true, suite: "patient-device-test-agent", isolatedStorage: true, importedExercises: 7, choices: ["add", "replace", "cancel"], next: "h3-12-normal", telemetry: productTelemetry }, null, 2));
  } finally {
    await context.close();
    await browser.close();
    await new Promise((resolve) => server.close(resolve));
  }
}

main().catch((error) => {
  console.error("ERROR: " + (error && error.stack ? error.stack : String(error)));
  process.exit(1);
});
