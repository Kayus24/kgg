#!/usr/bin/env node
"use strict";

const fs = require("fs");
const path = require("path");
const { chromium } = require("playwright");

const ROOT = path.resolve(__dirname, "..");
const HTML_PATH = path.join(ROOT, "kgg-update", "index.html");
const STATION_SCRIPT = path.join(
  ROOT,
  "android-wrapper",
  "app",
  "src",
  "preview",
  "assets",
  "android",
  "kgg_device_test_station.js",
);
const SCREENSHOT_PATH = path.join(
  ROOT,
  "tmp",
  "kgg-device-test-station-browser.png",
);

function fail(message) {
  throw new Error(message);
}

async function main() {
  if (!fs.existsSync(HTML_PATH) || !fs.existsSync(STATION_SCRIPT)) {
    fail("Preview HTML or station script is missing");
  }
  const browser = await chromium.launch({ headless: true });
  const page = await browser.newPage({
    viewport: { width: 1180, height: 820 },
    hasTouch: true,
  });
  try {
    await page.goto("file://" + HTML_PATH.replace(/\\/g, "/"), {
      waitUntil: "domcontentloaded",
      timeout: 60000,
    });
    await page.evaluate(() => {
      window.KGGPreviewContext = {
        requestId: "tab-s9-browser-smoke",
        patchHash: "a".repeat(64),
        baseSha: "b".repeat(40),
        commitSha: "b".repeat(40),
        previewVersion: "0.2.13-v403-tab-s9-test-station",
      };
      window.KGGDeviceTestStation = {
        beginSession: () => JSON.stringify({
          ok: true,
          active: true,
          sessionId: "tab-s9-" + "c".repeat(32),
          startedAt: "2026-08-24T10:00:00Z",
          previewRequestId: "tab-s9-browser-smoke",
          previewVersion: "0.2.13-v403-tab-s9-test-station",
        }),
        getDeviceInfo: () => JSON.stringify({
          model: "synthetic",
          androidVersion: "15",
          webViewVersion: "synthetic",
          screen: { width: 1600, height: 2560, orientation: "landscape" },
        }),
        endSession: () => JSON.stringify({ ok: true, overallStatus: "passed" }),
        openReportIssue: () => true,
      };
    });
    await page.addScriptTag({ path: STATION_SCRIPT });
    const launcher = page.locator("#kgg-device-test-station button");
    if (await launcher.count() !== 1) fail("station launcher missing");
    if ((await launcher.textContent()).trim() !== "Tab-S9-Teststation") {
      fail("station launcher label mismatch");
    }
    await launcher.click();
    if (await page.locator("#kgg-device-test-station h2").count() !== 1) {
      fail("current-step-only view missing");
    }
    if ((await page.locator("#kgg-device-test-station h2").textContent()).trim() !== "Hochformat") {
      fail("first guided step mismatch");
    }
    if (await page.locator("#kgg-device-test-station button[data-status]").count() !== 3) {
      fail("mandatory status buttons mismatch");
    }
    await page.locator("#kgg-device-test-station button[data-status=passed]").click();
    if ((await page.locator("#kgg-device-test-station h2").textContent()).trim() !== "Querformat") {
      fail("guided step did not advance");
    }
    fs.mkdirSync(path.dirname(SCREENSHOT_PATH), { recursive: true });
    await page.screenshot({ path: SCREENSHOT_PATH, fullPage: false });
    console.log(JSON.stringify({
      ok: true,
      suite: "device-test-station-browser",
      firstStep: "Hochformat",
      nextStep: "Querformat",
      statusButtons: 3,
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
