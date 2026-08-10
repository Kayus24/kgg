#!/usr/bin/env node
"use strict";

const fs = require("fs");
const path = require("path");
const { pathToFileURL } = require("url");
const { chromium } = require("playwright");

const ROOT = path.resolve(__dirname, "..");
const HTML_PATH = path.join(ROOT, "kgg-update", "index.html");
const PATCH_ID = "kgg-v061-cross-app-live-qr-camera";
const TOTAL_TIMEOUT_MS = Number(process.env.KGG_CAMERA_QR_TOTAL_TIMEOUT_MS || 180000);
const CASE_TIMEOUT_MS = Number(process.env.KGG_CAMERA_QR_CASE_TIMEOUT_MS || 30000);
const CLOSE_TIMEOUT_MS = Number(process.env.KGG_CAMERA_QR_CLOSE_TIMEOUT_MS || 5000);

let activeBrowser = null;
const activeContexts = new Set();

function assert(condition, message) {
  if (!condition) throw new Error(message);
}

function log(message) {
  process.stdout.write(`[camera-qr] ${message}\n`);
}

function withTimeout(promise, timeoutMs, label) {
  let timer;
  const timeout = new Promise((_, reject) => {
    timer = setTimeout(() => reject(new Error(`${label} timed out after ${timeoutMs} ms`)), timeoutMs);
  });
  return Promise.race([Promise.resolve(promise), timeout]).finally(() => clearTimeout(timer));
}

async function closeQuietly(resource, label) {
  if (!resource) return;
  try {
    await withTimeout(resource.close(), CLOSE_TIMEOUT_MS, `${label} close`);
  } catch (error) {
    console.error(`[camera-qr] cleanup warning: ${error.message}`);
  }
}

async function stopPageTracks(page) {
  if (!page || page.isClosed()) return;
  try {
    await withTimeout(
      page.evaluate(() => {
        const streams = new Set();
        for (const media of document.querySelectorAll("video,audio")) {
          if (media.srcObject) streams.add(media.srcObject);
        }
        if (window.__kggAdminCameraTest && window.__kggAdminCameraTest.stream) {
          streams.add(window.__kggAdminCameraTest.stream);
        }
        for (const stream of streams) {
          if (stream && typeof stream.getTracks === "function") {
            for (const track of stream.getTracks()) track.stop();
          }
        }
      }),
      CLOSE_TIMEOUT_MS,
      "media-track cleanup"
    );
  } catch (error) {
    console.error(`[camera-qr] cleanup warning: ${error.message}`);
  }
}

async function closeContext(context, page, label) {
  await stopPageTracks(page);
  await closeQuietly(context, label);
  activeContexts.delete(context);
}

function encodePlan(plan) {
  return Buffer.from(JSON.stringify(plan), "utf8").toString("base64url");
}

const QR_RAW = `KGGH2:${encodePlan({
  i: "admin-live-camera-test",
  t: "Admin Live Camera Test",
  v: 1,
  d: 6,
  e: [["Rudern", 3, "B", "kg", "Wdh", "20", "12", "", "", "", "exercise"]],
})}`;

function cameraInitScript(mode, detectorRaw) {
  return `(() => {
    window.__kggAdminCameraTest = {
      mode: ${JSON.stringify(mode)},
      detectorRaw: ${JSON.stringify(detectorRaw || "")},
      constraints: null,
      detectorAttempts: 0,
      jsQrAttempts: 0,
      trackStops: 0,
      fallbackClicks: 0,
      manualFiles: []
    };
    const mediaDevices = {};
    Object.defineProperty(navigator, "mediaDevices", { configurable: true, value: mediaDevices });
    mediaDevices.getUserMedia = async (constraints) => {
      window.__kggAdminCameraTest.constraints = constraints;
      if (window.__kggAdminCameraTest.mode === "deny") {
        throw new DOMException("synthetic camera denial", "NotAllowedError");
      }
      const canvas = document.createElement("canvas");
      canvas.width = 1280;
      canvas.height = 720;
      const context = canvas.getContext("2d");
      context.fillStyle = "#f4f4f4";
      context.fillRect(0, 0, canvas.width, canvas.height);
      context.fillStyle = "#111";
      context.fillRect(360, 80, 560, 560);
      const stream = canvas.captureStream(8);
      stream.getTracks().forEach((track) => {
        const stop = track.stop.bind(track);
        track.stop = () => {
          window.__kggAdminCameraTest.trackStops += 1;
          stop();
        };
      });
      window.__kggAdminCameraTest.canvas = canvas;
      window.__kggAdminCameraTest.stream = stream;
      return stream;
    };
    if (${JSON.stringify(mode)} === "barcode") {
      Object.defineProperty(window, "BarcodeDetector", {
        configurable: true,
        value: class BarcodeDetectorTestDouble {
          static async getSupportedFormats() { return ["qr_code"]; }
          async detect() {
            window.__kggAdminCameraTest.detectorAttempts += 1;
            return window.__kggAdminCameraTest.detectorAttempts === 1
              ? [{ rawValue: window.__kggAdminCameraTest.detectorRaw }]
              : [];
          }
        }
      });
    } else {
      try { delete window.BarcodeDetector; } catch (error) { window.BarcodeDetector = undefined; }
    }
  })();`;
}

async function createPage(browser, mode, detectorRaw = "") {
  const context = await browser.newContext({ viewport: { width: 390, height: 844 }, serviceWorkers: "block" });
  activeContexts.add(context);
  let page = null;
  try {
    await context.route(/^https?:\/\//, async (route) => {
      await route.fulfill({ status: 204, contentType: "application/json", body: "{}" });
    });
    await context.addInitScript({ content: cameraInitScript(mode, detectorRaw) });
    page = await context.newPage();
    page.setDefaultTimeout(15000);
    page.setDefaultNavigationTimeout(30000);
    const pageErrors = [];
    page.on("pageerror", (error) => pageErrors.push(error.message));
    await page.goto(pathToFileURL(HTML_PATH).href, { waitUntil: "domcontentloaded", timeout: 30000 });
    await page.waitForFunction((patchId) => {
      return !!(
        window.KGGScan &&
        window.KGGScan.__kggLiveQrCameraInstalled &&
        window.KGG_PATCHES &&
        window.KGG_PATCHES[patchId]
      );
    }, PATCH_ID, { timeout: 15000 });
    assert(pageErrors.length === 0, `page boot errors: ${pageErrors.join(" | ")}`);
    return { context, page };
  } catch (error) {
    await closeContext(context, page, `failed ${mode} context`);
    throw error;
  }
}

async function runBarcodeCase(browser) {
  const { context, page } = await createPage(browser, "barcode", QR_RAW);
  try {
    // Never return the long-running scanner promise to Playwright. The page
    // assertions observe its result; page.evaluate itself must finish at once.
    await page.evaluate(() => { window.KGGScan.pick("camera"); });
    await page.waitForFunction(() => {
      const state = window.KGGScan.getState();
      return state.jobs.some((job) => job.type === "qr" && job.hasResult);
    }, null, { timeout: 10000 });
    await page.waitForFunction((patchId) => {
      const root = document.getElementById(`${patchId}-camera`);
      return !!(root && root.hidden && window.__kggAdminCameraTest.trackStops >= 1);
    }, PATCH_ID, { timeout: 10000 });
    const result = await page.evaluate((patchId) => ({
      test: window.__kggAdminCameraTest,
      state: window.KGGScan.getState(),
      overlayCount: document.querySelectorAll(`#${patchId}-camera`).length,
      overlayHidden: document.getElementById(`${patchId}-camera`).hidden,
      capabilities: window.KGGScan.getCameraCapabilities(),
    }), PATCH_ID);
    assert(result.test.detectorAttempts >= 1, "BarcodeDetector was not used");
    assert(result.test.fallbackClicks === 0, "automatic QR unexpectedly used the system camera fallback");
    assert(result.test.constraints.audio === false, "live camera requested audio");
    assert(result.test.constraints.video.facingMode.ideal === "environment", "rear camera was not requested");
    assert(!Object.prototype.hasOwnProperty.call(result.test.constraints.video, "zoom"), "live camera must not force zoom");
    assert(result.overlayCount === 1 && result.overlayHidden, "live camera overlay was duplicated or left open");
    assert(result.capabilities.webVideoCapture && result.capabilities.jsQR, "camera capability contract is incomplete");
    return { id: "barcode-detector-auto-transfer", status: "pass", decoderAttempts: result.test.detectorAttempts };
  } finally {
    await closeContext(context, page, "barcode context");
  }
}

async function runJsQrFallbackCase(browser) {
  const { context, page } = await createPage(browser, "jsqr");
  try {
    await page.evaluate((raw) => {
      window.jsQR = () => {
        window.__kggAdminCameraTest.jsQrAttempts += 1;
        return window.__kggAdminCameraTest.jsQrAttempts === 1 ? { data: raw } : null;
      };
      window.KGGScan.pick("camera");
    }, QR_RAW);
    await page.waitForFunction(() => {
      const state = window.KGGScan.getState();
      return state.jobs.some((job) => job.type === "qr" && job.hasResult);
    }, null, { timeout: 10000 });
    const result = await page.evaluate(() => ({ ...window.__kggAdminCameraTest }));
    assert(result.jsQrAttempts >= 1, "local jsQR fallback was not used without BarcodeDetector");
    assert(result.trackStops >= 1, "camera track was not stopped after jsQR success");
    return { id: "local-jsqr-auto-transfer", status: "pass", jsQrAttempts: result.jsQrAttempts };
  } finally {
    await closeContext(context, page, "jsQR context");
  }
}

async function runPermissionFallbackCase(browser) {
  const { context, page } = await createPage(browser, "deny");
  try {
    await page.evaluate(() => {
      const input = document.getElementById("fileInput");
      input.addEventListener("click", (event) => {
        event.preventDefault();
        window.__kggAdminCameraTest.fallbackClicks += 1;
      });
      window.KGGScan.pick("camera");
    });
    await page.waitForFunction(() => window.__kggAdminCameraTest.fallbackClicks === 1, null, { timeout: 10000 });
    const result = await page.evaluate((patchId) => ({
      fallbackClicks: window.__kggAdminCameraTest.fallbackClicks,
      overlayHidden: document.getElementById(`${patchId}-camera`).hidden,
    }), PATCH_ID);
    assert(result.fallbackClicks === 1, "permission denial did not fall back exactly once");
    assert(result.overlayHidden, "permission denial left the live camera overlay open");
    return { id: "permission-system-camera-fallback", status: "pass" };
  } finally {
    await closeContext(context, page, "permission context");
  }
}

async function runManualCaptureCase(browser) {
  const { context, page } = await createPage(browser, "manual");
  try {
    await page.evaluate(() => {
      window.jsQR = () => null;
      window.KGGScan.handleInput = async (input, kind) => {
        const files = Array.from(input.files || []);
        window.__kggAdminCameraTest.manualFiles = files.map((file) => ({ name: file.name, type: file.type, size: file.size, kind }));
        return {};
      };
      window.KGGScan.pick("camera");
    });
    await page.waitForFunction((patchId) => {
      const video = document.querySelector(`#${patchId}-camera video`);
      return !!(video && video.videoWidth > 0 && video.videoHeight > 0);
    }, PATCH_ID, { timeout: 10000 });
    await page.locator(".kggLiveQrShutter").click({ timeout: 10000 });
    await page.waitForFunction(() => window.__kggAdminCameraTest.manualFiles.length === 1, null, { timeout: 10000 });
    const result = await page.evaluate(() => ({ ...window.__kggAdminCameraTest }));
    assert(result.manualFiles[0].kind === "camera", "manual shutter did not use the camera input route");
    assert(result.manualFiles[0].type === "image/jpeg" && result.manualFiles[0].size > 0, "manual shutter did not create a JPEG file");
    assert(result.trackStops >= 1, "camera track was not stopped after manual capture");
    return { id: "manual-paper-shutter", status: "pass", fileSize: result.manualFiles[0].size };
  } finally {
    await closeContext(context, page, "manual context");
  }
}

async function runCase(label, callback) {
  log(`start ${label}`);
  const result = await withTimeout(callback(), CASE_TIMEOUT_MS, label);
  log(`pass ${label}`);
  return result;
}

async function main() {
  assert(fs.existsSync(HTML_PATH), `generated Admin HTML missing: ${HTML_PATH}`);
  const html = fs.readFileSync(HTML_PATH, "utf8");
  for (const token of [
    PATCH_ID,
    "window.KGGScan={",
    "async handleQrRaw(raw,source)",
    "webVideoCaptureVersion",
    "LIVE_VARIANTS",
    "object-fit:contain",
  ]) {
    assert(html.includes(token), `camera/QR source contract missing: ${token}`);
  }

  log(`launch browser; hard timeout ${TOTAL_TIMEOUT_MS} ms`);
  activeBrowser = await chromium.launch({ headless: true });
  try {
    const results = [];
    results.push(await runCase("barcode-detector-auto-transfer", () => runBarcodeCase(activeBrowser)));
    results.push(await runCase("local-jsqr-auto-transfer", () => runJsQrFallbackCase(activeBrowser)));
    results.push(await runCase("permission-system-camera-fallback", () => runPermissionFallbackCase(activeBrowser)));
    results.push(await runCase("manual-paper-shutter", () => runManualCaptureCase(activeBrowser)));
    process.stdout.write(`${JSON.stringify({ status: "pass", patchId: PATCH_ID, results }, null, 2)}\n`);
  } finally {
    for (const context of Array.from(activeContexts)) {
      await closeContext(context, null, "remaining context");
    }
    await closeQuietly(activeBrowser, "browser");
    activeBrowser = null;
  }
}

const hardWatchdog = setTimeout(() => {
  console.error(`ERROR: Admin camera/QR smoke exceeded hard timeout of ${TOTAL_TIMEOUT_MS} ms`);
  // Forced exit prevents lingering Playwright or Chromium handles from keeping
  // the enclosing Python battery alive forever.
  process.exit(124);
}, TOTAL_TIMEOUT_MS);

main()
  .then(() => {
    clearTimeout(hardWatchdog);
    process.exit(0);
  })
  .catch((error) => {
    clearTimeout(hardWatchdog);
    console.error(`ERROR: ${error.stack || error.message}`);
    process.exit(1);
  });
