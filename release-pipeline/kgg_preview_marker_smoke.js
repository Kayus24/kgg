#!/usr/bin/env node
"use strict";

const fs = require("fs");
const os = require("os");
const path = require("path");
const { pathToFileURL } = require("url");

const ROOT = path.resolve(__dirname, "..");
const HTML_PATH = path.resolve(process.argv[2] || "");
const SCREENSHOT_DIR = path.join(ROOT, "tmp", "kgg-preview-marker");
const VIEWPORTS = [
  { id: "phone-small", width: 360, height: 800 },
  { id: "phone-standard", width: 390, height: 844 },
  { id: "phone-high-density-shape", width: 720, height: 1280 },
  { id: "tablet-landscape", width: 1180, height: 820 },
];

function fail(message) {
  throw new Error(message);
}

function installBundledNodePath() {
  const candidates = [
    path.join(os.homedir(), ".cache", "codex-runtimes", "codex-primary-runtime", "dependencies", "node", "node_modules"),
  ];
  for (const entry of String(process.env.PATH || "").split(path.delimiter).filter(Boolean)) {
    if (entry.replace(/\\/g, "/").endsWith("/node_modules/.bin")) candidates.push(path.dirname(entry));
  }
  const existing = candidates.filter((candidate) => fs.existsSync(candidate));
  if (!existing.length) return;
  const current = process.env.NODE_PATH ? process.env.NODE_PATH.split(path.delimiter) : [];
  process.env.NODE_PATH = [...existing, ...current].filter(Boolean).join(path.delimiter);
  require("module").Module._initPaths();
}

function requirePlaywright() {
  installBundledNodePath();
  try {
    return require("playwright");
  } catch (error) {
    fail(`Playwright is required for the Preview marker smoke: ${error.message}`);
  }
}

function sameRect(left, right) {
  for (const key of ["x", "y", "width", "height"]) {
    if (Math.abs(Number(left[key]) - Number(right[key])) > 0.25) return false;
  }
  return true;
}

async function markerState(page) {
  return page.evaluate(() => {
    const marker = document.getElementById("kgg-gpt-preview-banner");
    const toggle = document.getElementById("kgg-gpt-preview-toggle");
    const details = document.getElementById("kgg-gpt-preview-details");
    const app = document.getElementById("fixture-app");
    if (!marker || !toggle || !details || !app) return { missing: true };
    const markerRect = marker.getBoundingClientRect();
    const appRect = app.getBoundingClientRect();
    const style = getComputedStyle(marker);
    const detailsStyle = getComputedStyle(details);
    return {
      missing: false,
      markerRect: { x: markerRect.x, y: markerRect.y, width: markerRect.width, height: markerRect.height },
      appRect: { x: appRect.x, y: appRect.y, width: appRect.width, height: appRect.height },
      position: style.position,
      markerText: toggle.textContent.trim().replace(/\s+/g, " "),
      expanded: toggle.getAttribute("aria-expanded"),
      detailsDisplay: detailsStyle.display,
      detailsText: details.textContent.trim().replace(/\s+/g, " "),
      bodyScrollWidth: document.body.scrollWidth,
      documentScrollWidth: document.documentElement.scrollWidth,
      viewportWidth: window.innerWidth,
    };
  });
}

async function runViewport(browser, viewport) {
  const context = await browser.newContext({
    viewport: { width: viewport.width, height: viewport.height },
    isMobile: viewport.width <= 720,
    hasTouch: true,
  });
  const page = await context.newPage();
  try {
    await page.goto(pathToFileURL(HTML_PATH).href, { waitUntil: "domcontentloaded", timeout: 30000 });
    const collapsed = await markerState(page);
    if (collapsed.missing) fail(`${viewport.id}: Preview marker fixture is incomplete`);
    if (collapsed.position !== "fixed") fail(`${viewport.id}: marker position is ${collapsed.position}, expected fixed`);
    if (collapsed.markerRect.width > 92.25 || collapsed.markerRect.height > 24.25) {
      fail(`${viewport.id}: collapsed marker is too large: ${JSON.stringify(collapsed.markerRect)}`);
    }
    if (collapsed.markerRect.x < 0 || collapsed.markerRect.y < 0
        || collapsed.markerRect.x + collapsed.markerRect.width > viewport.width + 0.25
        || collapsed.markerRect.y + collapsed.markerRect.height > viewport.height + 0.25) {
      fail(`${viewport.id}: collapsed marker is outside the viewport`);
    }
    const expectedMarkerText = `TEST ${String.fromCharCode(183)} aaaa`;
    if (collapsed.markerText !== expectedMarkerText) {
      fail(`${viewport.id}: unexpected collapsed marker text: ${collapsed.markerText}`);
    }
    if (collapsed.expanded !== "false" || collapsed.detailsDisplay !== "none") {
      fail(`${viewport.id}: marker details must start closed`);
    }
    if (collapsed.bodyScrollWidth > collapsed.viewportWidth || collapsed.documentScrollWidth > collapsed.viewportWidth) {
      fail(`${viewport.id}: collapsed marker creates horizontal overflow`);
    }

    const withoutMarker = await page.evaluate(() => {
      const marker = document.getElementById("kgg-gpt-preview-banner");
      const app = document.getElementById("fixture-app");
      marker.style.setProperty("display", "none", "important");
      const rect = app.getBoundingClientRect();
      const result = { x: rect.x, y: rect.y, width: rect.width, height: rect.height };
      marker.style.setProperty("display", "block", "important");
      return result;
    });
    if (!sameRect(collapsed.appRect, withoutMarker)) {
      fail(`${viewport.id}: marker changes app geometry`);
    }

    for (const selector of ["#menu", "#scanner", "#dock"]) {
      await page.click(selector);
      const clicks = await page.getAttribute(selector, "data-clicks");
      if (clicks !== "1") fail(`${viewport.id}: ${selector} was not clickable with marker closed`);
    }

    await page.click("#kgg-gpt-preview-toggle");
    const opened = await markerState(page);
    if (opened.expanded !== "true" || opened.detailsDisplay === "none") {
      fail(`${viewport.id}: marker details did not open`);
    }
    for (const expected of ["Preview marker browser fixture", "preview-marker-browser-fixture", "a".repeat(64)]) {
      if (!opened.detailsText.includes(expected)) fail(`${viewport.id}: marker details missing ${expected}`);
    }
    if (!sameRect(collapsed.appRect, opened.appRect)) fail(`${viewport.id}: open details change app geometry`);
    if (opened.bodyScrollWidth > opened.viewportWidth || opened.documentScrollWidth > opened.viewportWidth) {
      fail(`${viewport.id}: open details create horizontal overflow`);
    }
    fs.mkdirSync(SCREENSHOT_DIR, { recursive: true });
    const detailsScreenshot = path.join(SCREENSHOT_DIR, `${viewport.id}-details.png`);
    await page.screenshot({ path: detailsScreenshot, fullPage: false });

    await page.mouse.click(Math.floor(viewport.width / 2), Math.floor(viewport.height / 2));
    const closedOutside = await markerState(page);
    if (closedOutside.expanded !== "false" || closedOutside.detailsDisplay !== "none") {
      fail(`${viewport.id}: outside click did not close marker details`);
    }
    await page.click("#menu");
    const menuClicksAfterClose = await page.getAttribute("#menu", "data-clicks");
    if (menuClicksAfterClose !== "2") fail(`${viewport.id}: menu was not clickable after closing marker details`);
    await page.click("#kgg-gpt-preview-toggle");
    await page.keyboard.press("Escape");
    const closedEscape = await markerState(page);
    if (closedEscape.expanded !== "false" || closedEscape.detailsDisplay !== "none") {
      fail(`${viewport.id}: Escape did not close marker details`);
    }

    const screenshot = path.join(SCREENSHOT_DIR, `${viewport.id}.png`);
    await page.screenshot({ path: screenshot, fullPage: false });
    return { id: viewport.id, viewport, markerRect: collapsed.markerRect, screenshot, detailsScreenshot };
  } finally {
    await context.close();
  }
}

async function main() {
  if (!HTML_PATH || !fs.existsSync(HTML_PATH)) fail(`Preview marker HTML fixture not found: ${HTML_PATH}`);
  const { chromium } = requirePlaywright();
  const browser = await chromium.launch({ headless: true });
  try {
    const results = [];
    for (const viewport of VIEWPORTS) results.push(await runViewport(browser, viewport));
    console.log(JSON.stringify({ ok: true, suite: "preview-marker", results }, null, 2));
  } finally {
    await browser.close();
  }
}

main().catch((error) => {
  console.error(`ERROR: ${error && error.stack ? error.stack : String(error)}`);
  process.exit(1);
});
