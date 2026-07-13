#!/usr/bin/env node
"use strict";

const fs = require("fs");
const os = require("os");
const path = require("path");
const { pathToFileURL } = require("url");

const ROOT = path.resolve(__dirname, "..");
const HTML_PATH = path.resolve(process.env.KGG_UI_CONTRACT_HTML || path.join(ROOT, "kgg-update", "index.html"));
const CONTRACT_PATH = path.join(__dirname, "kgg_ui_contract.json");
const SCREENSHOT_DIR = path.resolve(
  process.env.KGG_SELFTEST_SCREENSHOT_DIR || path.join(ROOT, "tmp", "kgg-selftest", "ui-contract")
);
const STORAGE_KEY = "kgg_html_app_v2_state";
const CUSTOM_BANK_KEY = "kgg_html_app_v2_custom_exercise_bank";

function fail(message) {
  console.error(`ERROR: ${message}`);
  process.exit(1);
}

function loadContract() {
  const contract = JSON.parse(fs.readFileSync(CONTRACT_PATH, "utf8"));
  if (contract.schema !== 1 || !Array.isArray(contract.requiredIds) || !Array.isArray(contract.viewports)) {
    fail("UI contract must use schema 1 with requiredIds and viewports.");
  }
  return contract;
}

function assertSourceFunctions(contract) {
  const html = fs.readFileSync(HTML_PATH, "utf8");
  const missing = (contract.requiredSourceFunctions || []).filter((name) => {
    const escaped = name.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
    return !(new RegExp(`(?:async\\s+)?function\\s+${escaped}\\s*\\(`)).test(html);
  });
  if (missing.length) fail(`required source functions missing: ${missing.join(", ")}`);
}

function installBundledNodePath() {
  const candidates = [
    path.join(os.homedir(), ".cache", "codex-runtimes", "codex-primary-runtime", "dependencies", "node", "node_modules"),
  ];
  for (const entry of String(process.env.PATH || "").split(path.delimiter).filter(Boolean)) {
    if (entry.replace(/\\/g, "/").endsWith("/node_modules/.bin")) {
      candidates.push(path.dirname(entry));
    }
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
    fail(`Playwright is required for the UI contract: ${error.message}`);
  }
}

function exercises() {
  return ["Beinpresse", "Rudern", "Latziehen", "Kniebeuger Maschine", "Pallof Press", "Ergometer"].map(
    (name, index) => ({
      id: `p_ui_contract_${index + 1}`,
      localId: `p_ui_contract_${index + 1}`,
      name,
      sets: 3,
      side: "BI",
      unit: "Wdh",
      metricUnit: "Wdh",
      weightUnit: "kg",
      loadUnit: "kg",
      startMetric: "12",
      startLoad: String(20 + index * 5),
    })
  );
}

function customBank() {
  return [
    {
      id: "bank_ui_contract",
      name: "UI Vertragsuebung",
      aliases: "ui vertrag",
      custom: true,
      unit: "Wdh",
      weightUnit: "kg",
      media: [],
    },
  ];
}

async function assertVisibleAndClickable(page, selectors, viewportId) {
  for (const selector of selectors) {
    const locator = page.locator(selector).first();
    await locator.waitFor({ state: "visible", timeout: 15000 });
    const probe = await locator.evaluate((element) => {
      const rect = element.getBoundingClientRect();
      const x = Math.max(0, Math.min(innerWidth - 1, rect.left + rect.width / 2));
      const y = Math.max(0, Math.min(innerHeight - 1, rect.top + rect.height / 2));
      const top = document.elementFromPoint(x, y);
      return {
        rect: { left: rect.left, top: rect.top, right: rect.right, bottom: rect.bottom, width: rect.width, height: rect.height },
        viewport: { width: innerWidth, height: innerHeight },
        display: getComputedStyle(element).display,
        visibility: getComputedStyle(element).visibility,
        pointerEvents: getComputedStyle(element).pointerEvents,
        topMatches: !!(top && (top === element || element.contains(top) || top.contains(element))),
      };
    });
    if (
      probe.rect.width < 20 ||
      probe.rect.height < 20 ||
      probe.rect.right < 0 ||
      probe.rect.left > probe.viewport.width ||
      probe.rect.bottom < 0 ||
      probe.rect.top > probe.viewport.height ||
      probe.display === "none" ||
      probe.visibility === "hidden" ||
      probe.pointerEvents === "none" ||
      !probe.topMatches
    ) {
      fail(`${viewportId}: UI element is not safely usable: ${selector} ${JSON.stringify(probe)}`);
    }
  }
}

async function assertBaseContract(page, contract, viewportId) {
  const result = await page.evaluate(({ ids, globals, allowedDuplicates }) => {
    const allIds = Array.from(document.querySelectorAll("[id]")).map((node) => node.id);
    const duplicates = [...new Set(allIds.filter((id, index) => allIds.indexOf(id) !== index))]
      .filter((id) => !allowedDuplicates.includes(id));
    const missingIds = ids.filter((id) => document.querySelectorAll(`#${CSS.escape(id)}`).length !== 1);
    const missingGlobals = globals.filter((name) => typeof window[name] === "undefined");
    const store = window.KGGDataStore;
    const currentPlan = store && typeof store.getCurrentPlan === "function" ? store.getCurrentPlan() : null;
    return {
      duplicates,
      missingIds,
      missingGlobals,
      planCount: currentPlan && Array.isArray(currentPlan.exercises) ? currentPlan.exercises.length : -1,
      horizontalOverflow: Math.max(document.documentElement.scrollWidth, document.body.scrollWidth) - innerWidth,
      openModals: Array.from(document.querySelectorAll(".modal.open")).filter((node) => {
        const style = getComputedStyle(node);
        const rect = node.getBoundingClientRect();
        return style.display !== "none" && style.visibility !== "hidden" && rect.width > 0 && rect.height > 0;
      }).map((node) => node.id),
      bodyClass: document.body.className,
    };
  }, {
    ids: contract.requiredIds,
    globals: contract.requiredGlobals || [],
    allowedDuplicates: contract.allowedDuplicateIds || [],
  });
  if (result.duplicates.length) fail(`${viewportId}: duplicate DOM ids: ${result.duplicates.join(", ")}`);
  if (result.missingIds.length) fail(`${viewportId}: required ids missing/not unique: ${result.missingIds.join(", ")}`);
  if (result.missingGlobals.length) fail(`${viewportId}: required globals missing: ${result.missingGlobals.join(", ")}`);
  if (result.planCount !== exercises().length) fail(`${viewportId}: KGGDataStore.currentPlan has ${result.planCount} entries`);
  if (result.horizontalOverflow > 8) fail(`${viewportId}: horizontal overflow ${result.horizontalOverflow}px`);
  const unexpectedModals = result.openModals.filter((id) => !(contract.allowedBootOpenModals || []).includes(id));
  if (unexpectedModals.length) fail(`${viewportId}: unexpected modal opened on boot: ${unexpectedModals.join(", ")}`);
  return result;
}

async function exerciseCoreFlows(page, viewportId) {
  await page.locator("#baseToggle").click();
  await page.locator("#baseFields").waitFor({ state: "visible", timeout: 5000 });
  await page.locator("#baseToggle").click();

  const edit = page.locator("#planList [data-planedit]").first();
  await edit.scrollIntoViewIfNeeded();
  await edit.click();
  await page.locator("#editorModal.open").waitFor({ state: "visible", timeout: 5000 });
  const name = await page.locator("#editName").inputValue();
  if (!name) fail(`${viewportId}: editor opened without exercise name`);
  await page.locator("#closeEditor").click();
  await page.locator("#editorModal").waitFor({ state: "hidden", timeout: 5000 });

  if (await page.locator("#bankToggle").isVisible()) {
    await page.locator("#bankToggle").click();
    await page.locator("#bankContent").waitFor({ state: "visible", timeout: 5000 });
    if ((await page.locator("#bankContent .bankRow").count()) < 1) fail(`${viewportId}: exercise bank opened empty`);
    await page.locator("#bankToggle").click();
  }

  if (await page.locator("#recentToggle").isVisible()) {
    await page.locator("#recentToggle").click();
    await page.waitForTimeout(120);
    const open = await page.locator("#recentList").evaluate((node) => !node.classList.contains("hidden"));
    if (!open) fail(`${viewportId}: history button did not open history list`);
    await page.locator("#recentToggle").click();
  }

  if (await page.locator("#packageToggle").isVisible()) {
    await page.locator("#packageToggle").click();
    await page.waitForTimeout(120);
    const packageOpen = await page.evaluate(() => {
      const list = document.getElementById("packageList");
      const overlay = document.getElementById("tabletPackageOverlay");
      return (list && !list.classList.contains("hidden")) || (overlay && overlay.getAttribute("aria-hidden") === "false");
    });
    if (!packageOpen) fail(`${viewportId}: package button did not open a package view`);
  }
}

async function runViewport(browser, contract, viewport) {
  const externalRequests = [];
  const pageErrors = [];
  const consoleErrors = [];
  const context = await browser.newContext({
    viewport: { width: viewport.width, height: viewport.height },
    deviceScaleFactor: 1,
    isMobile: !!viewport.mobile,
    hasTouch: !!viewport.touch,
    locale: "de-DE",
  });
  try {
    await context.route(/^https?:\/\//, async (route) => {
      externalRequests.push(route.request().url());
      await route.fulfill({ status: 204, contentType: "application/json", body: "{}" });
    });
    await context.addInitScript(({ storageKey, bankKey, plan, bank }) => {
      localStorage.setItem(storageKey, JSON.stringify({
        plan,
        patient: { name: "UI Vertrag", date: "2026-07-13", therapist: "KGG Selbsttest" },
        bankOpen: false,
        recent: [{ id: "recent_contract", name: "Testplan", plan: plan.slice(0, 2) }],
        packages: [{ id: "pkg_contract", name: "Testpaket", exercises: ["Beinpresse", "Rudern"] }],
      }));
      localStorage.setItem(bankKey, JSON.stringify(bank));
      localStorage.setItem("kgg_pwa_install_prompt_seen_v1", new Date().toISOString());
    }, { storageKey: STORAGE_KEY, bankKey: CUSTOM_BANK_KEY, plan: exercises(), bank: customBank() });

    const page = await context.newPage();
    page.on("pageerror", (error) => pageErrors.push(error.message));
    page.on("console", (message) => {
      if (message.type() === "error") consoleErrors.push(message.text());
    });
    const url = pathToFileURL(HTML_PATH).href;
    await page.goto(url, { waitUntil: "domcontentloaded", timeout: 60000 });
    await page.waitForSelector("#planList .planCard[data-plan-id]", { timeout: 15000 });
    await page.waitForTimeout(600);
    if (page.url() !== url) fail(`${viewport.id}: app navigated away during boot`);
    if (pageErrors.length) fail(`${viewport.id}: page errors: ${pageErrors.join(" | ")}`);
    if (consoleErrors.length) fail(`${viewport.id}: console errors: ${consoleErrors.join(" | ")}`);

    const base = await assertBaseContract(page, contract, viewport.id);
    await page.evaluate((allowed) => {
      for (const id of allowed) document.getElementById(id)?.classList.remove("open");
    }, contract.allowedBootOpenModals || []);
    await assertVisibleAndClickable(page, viewport.visible || [], viewport.id);
    await exerciseCoreFlows(page, viewport.id);
    await page.evaluate(() => document.querySelectorAll(".modal.open").forEach((node) => node.classList.remove("open")));
    fs.mkdirSync(SCREENSHOT_DIR, { recursive: true });
    const screenshot = path.join(SCREENSHOT_DIR, `${viewport.id}.png`);
    await page.screenshot({ path: screenshot, fullPage: false });
    return {
      id: viewport.id,
      viewport: { width: viewport.width, height: viewport.height },
      externalRequests: externalRequests.length,
      screenshot,
      bodyClass: base.bodyClass,
    };
  } finally {
    await context.close();
  }
}

async function main() {
  if (!fs.existsSync(HTML_PATH)) fail(`HTML file not found: ${HTML_PATH}`);
  const contract = loadContract();
  assertSourceFunctions(contract);
  const { chromium } = requirePlaywright();
  const browser = await chromium.launch({ headless: true });
  try {
    const results = [];
    for (const viewport of contract.viewports) results.push(await runViewport(browser, contract, viewport));
    fs.mkdirSync(SCREENSHOT_DIR, { recursive: true });
    fs.writeFileSync(path.join(SCREENSHOT_DIR, "ui-contract-report.json"), JSON.stringify({ schema: 1, results }, null, 2) + "\n", "utf8");
    console.log(JSON.stringify({ ok: true, suite: "ui-contract", results }, null, 2));
  } finally {
    await browser.close();
  }
}

main().catch((error) => fail(error && error.stack ? error.stack : String(error)));
