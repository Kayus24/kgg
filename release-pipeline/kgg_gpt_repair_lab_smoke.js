#!/usr/bin/env node
"use strict";

const fs = require("fs");
const os = require("os");
const path = require("path");
const { pathToFileURL } = require("url");

function parseArgs() {
  const args = process.argv.slice(2);
  const out = {};
  for (let index = 0; index < args.length; index += 1) {
    if (args[index] === "--html" && args[index + 1]) out.html = path.resolve(args[++index]);
    else if (args[index] === "--case" && args[index + 1]) out.caseName = String(args[++index]);
    else if (args[index] === "--screenshot" && args[index + 1]) out.screenshot = path.resolve(args[++index]);
    else if (args[index] === "--capture-only") out.captureOnly = true;
  }
  return out;
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
  process.env.NODE_PATH = [...existing, ...(process.env.NODE_PATH || "").split(path.delimiter)].filter(Boolean).join(path.delimiter);
  require("module").Module._initPaths();
}

function requirePlaywright() {
  installBundledNodePath();
  try {
    return require("playwright");
  } catch (error) {
    throw new Error(`Playwright missing: ${error && error.message ? error.message : error}`);
  }
}

function exercises() {
  return Array.from({ length: 8 }, (_, index) => ({
    id: `repair_plan_${index + 1}`,
    localId: `repair_plan_${index + 1}`,
    name: `Repair Uebung ${index + 1}`,
    sets: 3,
    side: "BI",
    unit: "Wdh",
    metricUnit: "Wdh",
    weightUnit: "kg",
    loadUnit: "kg",
    startMetric: "12",
    startLoad: String(index + 10),
  }));
}

function customBank() {
  return [{
    id: "repair_bank_thumb",
    name: "Repair Bild Uebung",
    sets: 3,
    side: "BI",
    unit: "Wdh",
    media: [{ id: "repair_missing_blob", type: "image", name: "repair.jpg" }],
  }];
}

async function seedContext(context, caseName) {
  await context.addInitScript(({ plan, bank, selectedCase }) => {
    localStorage.setItem("kgg_html_app_v2_state", JSON.stringify({
      plan,
      patient: { name: "Repair Lab", date: "2026-07-20", therapist: "Eval" },
      bankOpen: true,
      recent: [{ id: "repair_recent", name: "Repair Verlauf", date: "2026-07-20", exercises: plan.slice(0, 2) }],
      packages: [{ id: "repair_package", name: "Repair Paket", exercises: ["Repair Uebung 1"] }],
    }));
    localStorage.setItem("kgg_html_app_v2_custom_exercise_bank", JSON.stringify(bank));
    localStorage.setItem("kgg_admin_local_secrets_v1", JSON.stringify({ version: 2, updatedAt: "2026-07-20T00:00:00Z", geminiKeys: ["test-only"] }));
    localStorage.setItem("kgg_pwa_install_prompt_seen_v1", "2026-07-20T00:00:00Z");
    localStorage.setItem("kgg_tablet_layout_locked", "false");
    if (selectedCase === "tablet-scale-boundary") localStorage.setItem("kgg_tablet_left_col_width", "480px");
    else localStorage.removeItem("kgg_tablet_left_col_width");
    localStorage.setItem("kgg_tablet_ui_scale", selectedCase === "tablet-scale-persistence" ? "1.25" : "1");
  }, { plan: exercises(), bank: customBank(), selectedCase: caseName });
}

async function openApp(browser, htmlPath, caseName, pageErrors, requests) {
  const phoneCases = new Set(["phone-admin-menu", "phone-admin-duplicate", "phone-photo-menu", "bank-thumbnails", "clear-live-input", "phone-history-drawers", "phone-recent-drawer", "phone-menu-anchor", "phone-menu-visual-position"]);
  const phone = phoneCases.has(caseName);
  const context = await browser.newContext({
    viewport: phone ? { width: 390, height: 844 } : { width: 1180, height: 820 },
    deviceScaleFactor: phone ? 2 : 1,
    isMobile: phone,
    hasTouch: true,
    locale: "de-DE",
  });
  await context.route(/^https?:\/\//, async (route) => {
    requests.push(route.request().url());
    await route.fulfill({ status: 204, contentType: "application/json", body: "{}" });
  });
  await seedContext(context, caseName);
  const page = await context.newPage();
  page.on("pageerror", (error) => pageErrors.push(error.message));
  await page.goto(pathToFileURL(htmlPath).href, { waitUntil: "commit", timeout: 60000 });
  await page.waitForSelector("#scanHub", { state: "attached", timeout: 15000 });
  await page.waitForSelector("#planList .planCard[data-plan-id]", { timeout: 15000 });
  await page.waitForTimeout(800);
  return { context, page };
}

async function pointer(page, selector, type, x, y, pointerId) {
  await page.evaluate(({ selector: selected, type: eventType, x: px, y: py, pointerId: id }) => {
    const target = selected === "document" ? document : document.querySelector(selected);
    if (!target) throw new Error(`pointer target missing: ${selected}`);
    target.dispatchEvent(new PointerEvent(eventType, {
      bubbles: true,
      cancelable: true,
      pointerId: id,
      pointerType: "touch",
      isPrimary: true,
      clientX: px,
      clientY: py,
      button: 0,
      buttons: eventType === "pointerup" ? 0 : 1,
    }));
  }, { selector, type, x, y, pointerId });
}

async function probe(page, caseName) {
  if (caseName === "phone-admin-duplicate") {
    await page.waitForSelector("#kggPhoneAdminMenu", { state: "visible", timeout: 7000 });
    const state = await page.evaluate(() => {
      const visible = Array.from(document.querySelectorAll(".kggPhoneAdminMenu")).filter((node) => {
        const style = getComputedStyle(node);
        const rect = node.getBoundingClientRect();
        return style.display !== "none" && style.visibility !== "hidden" && rect.width > 2 && rect.height > 2;
      });
      return {
        visibleMenus: visible.length,
        anchoredMenus: document.querySelectorAll("#createPanel .planHeader .kggPhoneAdminMenu").length,
      };
    });
    if (state.visibleMenus !== 1 || state.anchoredMenus !== 1) {
      throw new Error(`duplicate phone admin control remains: ${JSON.stringify(state)}`);
    }
    return state;
  }

  if (caseName === "phone-admin-menu" || caseName === "phone-menu-anchor") {
    await page.waitForSelector("#kggPhoneAdminMenu", { state: "visible", timeout: 7000 });
    const anchored = await page.locator("#createPanel .planHeader #kggPhoneAdminMenu").count();
    if (anchored !== 1) throw new Error("phone admin menu is not anchored in the plan header");
    await page.locator("#kggPhoneAdminMenuBtn").click();
    const open = await page.evaluate(() => {
      const panel = document.getElementById("kggPhoneAdminMenuPanel");
      return !!(panel && !panel.hidden && getComputedStyle(panel).display !== "none");
    });
    if (!open) throw new Error("phone admin menu did not open");
    return { anchored: true, opened: true };
  }

  if (caseName === "phone-menu-visual-position") {
    await page.waitForSelector("#kggPhoneAdminMenu", { state: "visible", timeout: 7000 });
    const state = await page.evaluate(() => {
      const menu = document.getElementById("kggPhoneAdminMenu");
      const header = document.querySelector("#createPanel.planMode .planHeader") || document.querySelector("#createPanel .planHeader");
      if (!menu || !header) return null;
      const m = menu.getBoundingClientRect();
      const h = header.getBoundingClientRect();
      return {
        menu: { left: m.left, right: m.right, top: m.top, bottom: m.bottom },
        header: { left: h.left, right: h.right, top: h.top, bottom: h.bottom },
        inside: m.left >= h.left - 4 && m.right <= h.right + 4 && m.top >= h.top - 4 && m.bottom <= h.bottom + 4,
      };
    });
    if (!state || !state.inside) throw new Error(`phone admin menu is visually outside the plan header: ${JSON.stringify(state)}`);
    return state;
  }

  if (caseName === "phone-photo-menu") {
    await page.waitForSelector("#phonePhotoMenuToggle", { state: "visible", timeout: 7000 });
    const inside = await page.locator("#scanBtn #phonePhotoMenuToggle").count();
    if (inside !== 1) throw new Error("photo toggle is not inside the scan button");
    await page.locator("#phonePhotoMenuToggle").click();
    const open = await page.evaluate(() => document.body.classList.contains("kggPhonePhotoMenuOpen"));
    if (!open) throw new Error("photo menu did not open");
    return { insideScan: true, opened: true };
  }

  if (caseName === "bank-thumbnails") {
    await page.waitForSelector('[data-bank-thumb-id="repair_missing_blob"]', { timeout: 7000 });
    const thumb = await page.locator('[data-bank-thumb-id="repair_missing_blob"]').evaluate((node) => {
      const rect = node.getBoundingClientRect();
      return { fallback: node.classList.contains("bankThumbFallback"), width: rect.width, height: rect.height };
    });
    if (!thumb.fallback || thumb.width < 24 || thumb.height < 24) throw new Error(`thumbnail fallback invalid: ${JSON.stringify(thumb)}`);
    return thumb;
  }

  if (caseName === "clear-live-input") {
    const input = page.locator("#exerciseInput");
    await input.fill("Repair Live Text");
    await input.dispatchEvent("input");
    await page.waitForTimeout(250);
    await page.locator("#clearInput").click();
    await page.waitForTimeout(250);
    const state = await page.evaluate(() => ({
      value: document.getElementById("exerciseInput").value,
      liveCards: Array.from(document.querySelectorAll("#planList .planCard")).filter((node) => node.textContent.includes("Repair Live Text")).length,
    }));
    if (state.value !== "" || state.liveCards !== 0) throw new Error(`clear input behavior failed: ${JSON.stringify(state)}`);
    return state;
  }

  if (caseName === "phone-history-drawers") {
    await page.locator("#recentToggle").click();
    await page.waitForFunction(() => !document.getElementById("recentList").classList.contains("hidden"), null, { timeout: 7000 });
    let state = await page.evaluate(() => ({ safe: document.body.classList.contains("kggPhoneDrawerSafeOpen"), text: document.getElementById("recentList").textContent }));
    if (!state.safe || !state.text.includes("Repair Verlauf")) throw new Error(`recent drawer failed: ${JSON.stringify(state)}`);
    await page.locator("#recentToggle").click();
    await page.locator("#packageToggle").click();
    await page.waitForFunction(() => !document.getElementById("packageList").classList.contains("hidden"), null, { timeout: 7000 });
    state = await page.evaluate(() => ({ safe: document.body.classList.contains("kggPhoneDrawerSafeOpen"), text: document.getElementById("packageList").textContent }));
    if (!state.safe || !state.text.includes("Repair Paket")) throw new Error(`package drawer failed: ${JSON.stringify(state)}`);
    return { recent: true, package: true };
  }

  if (caseName === "phone-recent-drawer") {
    await page.locator("#recentToggle").click();
    await page.waitForFunction(() => !document.getElementById("recentList").classList.contains("hidden"), null, { timeout: 7000 });
    const state = await page.evaluate(() => ({
      safe: document.body.classList.contains("kggPhoneDrawerSafeOpen"),
      text: document.getElementById("recentList").textContent,
      packageHidden: document.getElementById("packageList").classList.contains("hidden"),
    }));
    if (!state.safe || !state.text.includes("Repair Verlauf") || !state.packageHidden) {
      throw new Error(`recent drawer failed: ${JSON.stringify(state)}`);
    }
    return state;
  }

  if (caseName === "tablet-editor-layout") {
    await page.locator("#planList [data-planedit]").first().click();
    await page.waitForSelector("#editorModal.open .editorSheet", { timeout: 7000 });
    const layout = await page.locator("#editorModal .editorSheet").evaluate((sheet) => {
      const style = getComputedStyle(sheet);
      const rect = sheet.getBoundingClientRect();
      return { display: style.display, columns: style.gridTemplateColumns, width: rect.width };
    });
    if (layout.display !== "grid" || layout.columns.trim().split(/\s+/).length < 2 || layout.width < 760) {
      throw new Error(`tablet editor layout failed: ${JSON.stringify(layout)}`);
    }
    return layout;
  }

  if (caseName === "tablet-card-reorder") {
    const card = page.locator("#planList .planCard[data-plan-id]").first();
    const box = await card.boundingBox();
    if (!box) throw new Error("reorder card has no bounds");
    const x = box.x + box.width / 2;
    const y = box.y + box.height / 2;
    await pointer(page, "#planList .planCard[data-plan-id]", "pointerdown", x, y, 81);
    await page.waitForTimeout(330);
    const active = await page.locator("#planList .planCard.reorder-lifted").count();
    if (!active) throw new Error("tablet reorder did not start");
    await pointer(page, "document", "pointerup", x + 4, y + 4, 81);
    await page.waitForTimeout(300);
    const leaked = await page.evaluate(() => ({
      body: document.body.classList.contains("kggPlanCardReordering"),
      lifted: !!document.querySelector("#planList .reorder-lifted"),
      placeholder: !!document.querySelector("#planList .reorder-placeholder"),
    }));
    if (leaked.body || leaked.lifted || leaked.placeholder) throw new Error(`reorder cleanup leaked: ${JSON.stringify(leaked)}`);
    return leaked;
  }

  if (caseName === "tablet-scale-persistence") {
    const initial = await page.evaluate(() => ({
      css: getComputedStyle(document.documentElement).getPropertyValue("--kgg-tablet-ui-scale").trim(),
      stored: localStorage.getItem("kgg_tablet_ui_scale"),
      label: (document.getElementById("tabletScaleValue") || {}).textContent || "",
    }));
    if (Math.abs(Number(initial.css) - 1.25) > 0.01 || !initial.label.includes("125")) throw new Error(`stored tablet scale not restored: ${JSON.stringify(initial)}`);
    await page.locator("#tabletMenuBtn").click();
    await page.waitForFunction(() => document.body.classList.contains("tabletMenuOpen"), null, { timeout: 7000 });
    await page.locator("#tabletMenuLayoutBtn").click();
    await page.waitForFunction(() => document.body.classList.contains("tabletLayoutEditMode"), null, { timeout: 7000 });
    await page.locator("#tabletScalePlus").click();
    await page.waitForTimeout(200);
    const stored = await page.evaluate(() => Number(localStorage.getItem("kgg_tablet_ui_scale")));
    if (!(stored > 1.25)) throw new Error(`tablet scale update not persisted: ${stored}`);
    return { initial, stored };
  }

  if (caseName === "tablet-scale-boundary") {
    await page.locator("#tabletMenuBtn").click();
    await page.waitForFunction(() => document.body.classList.contains("tabletMenuOpen"), null, { timeout: 7000 });
    await page.locator("#tabletMenuLayoutBtn").click();
    await page.waitForFunction(() => document.body.classList.contains("tabletLayoutEditMode"), null, { timeout: 7000 });
    const before = await page.evaluate(() => ({
      left: getComputedStyle(document.documentElement).getPropertyValue("--kgg-tablet-left-col").trim(),
      scale: Number(getComputedStyle(document.documentElement).getPropertyValue("--kgg-tablet-ui-scale").trim()),
    }));
    await page.locator("#tabletSplitScalePlus").click();
    await page.waitForTimeout(250);
    const after = await page.evaluate(() => ({
      left: getComputedStyle(document.documentElement).getPropertyValue("--kgg-tablet-left-col").trim(),
      scale: Number(getComputedStyle(document.documentElement).getPropertyValue("--kgg-tablet-ui-scale").trim()),
      storedScale: Number(localStorage.getItem("kgg_tablet_ui_scale")),
    }));
    if (!(after.scale > before.scale) || after.left !== before.left || Math.abs(after.scale - after.storedScale) > 0.001) {
      throw new Error(`tablet scale changed column boundary: ${JSON.stringify({ before, after })}`);
    }
    return { before, after };
  }

  if (caseName === "tablet-layout-panel") {
    await page.locator("#tabletMenuBtn").click();
    await page.waitForFunction(() => document.body.classList.contains("tabletMenuOpen"), null, { timeout: 7000 });
    await page.locator("#tabletMenuLayoutBtn").click();
    await page.waitForTimeout(250);
    const state = await page.evaluate(() => {
      const panel = document.getElementById("tabletMenuLayoutPanel");
      return { edit: document.body.classList.contains("tabletLayoutEditMode"), hidden: !panel || panel.hidden };
    });
    if (!state.edit || state.hidden) throw new Error(`tablet layout panel failed: ${JSON.stringify(state)}`);
    return state;
  }

  throw new Error(`unknown Repair-Lab browser case: ${caseName}`);
}

async function prepareVisualState(page, caseName) {
  if (caseName === "tablet-editor-layout") {
    await page.locator("#planList [data-planedit]").first().click();
    await page.waitForSelector("#editorModal.open .editorSheet", { timeout: 7000 });
  } else if (caseName === "tablet-scale-boundary" || caseName === "tablet-layout-panel") {
    await page.locator("#tabletMenuBtn").click();
    await page.waitForFunction(() => document.body.classList.contains("tabletMenuOpen"), null, { timeout: 7000 });
    await page.locator("#tabletMenuLayoutBtn").click();
    await page.waitForTimeout(300);
  }
}

async function addProblemAnnotations(page, caseName) {
  const selectors = {
    "tablet-editor-layout": ["#editorModal .editorSheet"],
    "phone-admin-duplicate": [".kggNaturalDuplicate"],
    "phone-menu-anchor": ["#kggPhoneAdminMenu"],
    "phone-menu-visual-position": ["#kggPhoneAdminMenu"],
    "tablet-scale-boundary": ["#tabletSplitScaleControl"],
    "tablet-layout-panel": ["#tabletMenuLayoutBtn"],
    "phone-recent-drawer": ["#recentToggle", "#packageToggle"],
  }[caseName] || [];
  await page.evaluate(({ selected }) => {
    document.querySelectorAll("[data-natural-ui-annotation]").forEach((node) => node.remove());
    selected.forEach((selector, index) => {
      const node = document.querySelector(selector);
      if (!node) return;
      const rect = node.getBoundingClientRect();
      const ring = document.createElement("div");
      ring.dataset.naturalUiAnnotation = "1";
      ring.style.cssText = [
        "position:fixed",
        `left:${Math.max(2, rect.left - 10)}px`,
        `top:${Math.max(2, rect.top - 10)}px`,
        `width:${Math.max(36, rect.width + 20)}px`,
        `height:${Math.max(36, rect.height + 20)}px`,
        "border:6px solid #f4c400",
        "border-radius:48%",
        `transform:rotate(${index % 2 ? -4 : 3}deg)`,
        "box-sizing:border-box",
        "pointer-events:none",
        "z-index:2147483646",
        "filter:drop-shadow(0 1px 1px rgba(0,0,0,.18))",
      ].join(";");
      const label = document.createElement("span");
      label.textContent = String(index + 1);
      label.style.cssText = [
        "position:absolute",
        "left:-18px",
        "top:-28px",
        "font:900 28px/1 Arial,sans-serif",
        "color:#f4c400",
        "text-shadow:0 1px 1px rgba(0,0,0,.22)",
      ].join(";");
      ring.appendChild(label);
      document.body.appendChild(ring);
    });
  }, { selected: selectors });
}

async function main() {
  const watchdog = setTimeout(() => {
    console.error(JSON.stringify({ status: "FAIL", error: "browser probe watchdog exceeded 110 seconds" }));
    process.exit(124);
  }, 110000);
  const args = parseArgs();
  if (!args.html || !args.caseName) throw new Error("--html and --case are required");
  if (!fs.existsSync(args.html)) throw new Error(`HTML missing: ${args.html}`);
  const { chromium } = requirePlaywright();
  const browser = await chromium.launch({ headless: true });
  const pageErrors = [];
  const requests = [];
  let context;
  try {
    const opened = await openApp(browser, args.html, args.caseName, pageErrors, requests);
    context = opened.context;
    if (args.captureOnly) {
      await prepareVisualState(opened.page, args.caseName);
      await addProblemAnnotations(opened.page, args.caseName);
      if (!args.screenshot) throw new Error("--capture-only requires --screenshot");
      fs.mkdirSync(path.dirname(args.screenshot), { recursive: true });
      await opened.page.screenshot({ path: args.screenshot, fullPage: false });
      console.log(JSON.stringify({ status: "PASS", case: args.caseName, captureOnly: true, blockedExternalRequests: requests.length }));
      return;
    }
    const result = await probe(opened.page, args.caseName);
    if (pageErrors.length) throw new Error(`page errors: ${pageErrors.join(" | ")}`);
    if (args.screenshot) {
      fs.mkdirSync(path.dirname(args.screenshot), { recursive: true });
      await opened.page.screenshot({ path: args.screenshot, fullPage: true });
    }
    console.log(JSON.stringify({ status: "PASS", case: args.caseName, result, blockedExternalRequests: requests.length }));
  } finally {
    if (context) await context.close();
    await browser.close();
    clearTimeout(watchdog);
  }
}

main().catch((error) => {
  console.error(JSON.stringify({ status: "FAIL", error: error && error.message ? error.message : String(error) }));
  process.exit(1);
});
