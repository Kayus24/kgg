#!/usr/bin/env node
"use strict";

const path = require("path");
const { pathToFileURL } = require("url");
const { chromium } = require("playwright");

const ROOT = path.resolve(__dirname, "..");
const HTML_PATH = path.join(ROOT, "kgg-update", "index.html");
const HTML_URL = pathToFileURL(HTML_PATH).href;
const VIEWPORTS = [
  { width: 820, height: 1180 },
  { width: 1024, height: 768 },
  { width: 1280, height: 800 },
];

function fail(message) { throw new Error(message); }
function assert(value, message) { if (!value) fail(message); }
function hrefWithCode(code) {
  const url = new URL(HTML_URL);
  url.searchParams.set("cockpit", code);
  return url.toString();
}

async function seedAndOpen(page, viewport) {
  await page.setViewportSize(viewport);
  await page.addInitScript(() => {
    localStorage.setItem("kgg_pwa_install_prompt_seen_v1", "2026-09-08T00:00:00.000Z");
    localStorage.setItem("kgg_admin_local_secrets_v1", JSON.stringify({ version: 2, updatedAt: "2026-09-08T00:00:00.000Z", geminiKeys: ["browser-test"], mediaDropzoneEndpoint: "", mediaDropzoneUploadToken: "" }));
  });
  await page.goto(HTML_URL, { waitUntil: "domcontentloaded", timeout: 30000 });
  await page.waitForSelector("#kggTherapyCockpitButton", { state: "attached", timeout: 15000 });
  const code = await page.evaluate(() => {
    const api = window.KGGTherapyCockpit;
    const ids = api.registry.entries().slice(0, 3).map(entry => entry.id);
    const makeExercise = (id, offset) => ({
      id, sets: 2, previous: [[String(10 + offset), "12"], [String(11 + offset), "11"]],
      today: [[String(10 + offset), "12"], [String(11 + offset), "11"]],
    });
    return api.encode({ planId: "browser-plan", name: "Browser Müller", date: "2026-09-08", exercises: ids.map((id, index) => makeExercise(id, index)) });
  });
  await page.goto(hrefWithCode(code), { waitUntil: "domcontentloaded", timeout: 30000 });
  await page.waitForSelector("#kggTherapyCockpitRoot", { state: "attached", timeout: 15000 });
  await page.waitForFunction(() => document.body.classList.contains("kggTherapyCockpitOpen"), null, { timeout: 15000 });
  await page.waitForSelector('.kgg-tc-card[data-tc-card="0"]', { timeout: 15000 });
  return code;
}

async function inspectGeometry(page, viewport) {
  return page.evaluate(({ width, height }) => {
    const root = document.getElementById("kggTherapyCockpitRoot");
    const board = document.getElementById("kggTherapyCockpitBoard");
    const grid = document.querySelector(".kgg-tc-grid");
    const app = document.querySelector(".app");
    const rect = element => {
      if (!element) return null;
      const box = element.getBoundingClientRect();
      const style = getComputedStyle(element);
      return { left: Math.round(box.left), right: Math.round(box.right), top: Math.round(box.top), bottom: Math.round(box.bottom), width: Math.round(box.width), height: Math.round(box.height), display: style.display, visibility: style.visibility };
    };
    return {
      root: rect(root), board: rect(board), grid: rect(grid), app: rect(app),
      cards: document.querySelectorAll(".kgg-tc-card").length,
      columns: grid ? getComputedStyle(grid).gridTemplateColumns.split(" ").length : 0,
      boardOverflow: board ? board.scrollWidth - board.clientWidth : null,
      documentOverflow: document.documentElement.scrollWidth - width,
      viewport: { width, height },
    };
  }, viewport);
}

async function runViewport(page, viewport, code) {
  const geometry = await inspectGeometry(page, viewport);
  assert(geometry.root && geometry.root.display !== "none" && geometry.root.width === viewport.width && geometry.root.height === viewport.height, `overlay geometry failed: ${JSON.stringify(geometry)}`);
  assert(geometry.app && geometry.app.visibility === "hidden", `normal app was not hidden: ${JSON.stringify(geometry)}`);
  assert(geometry.cards === 1 && geometry.columns === 1, `initial slot/card geometry failed: ${JSON.stringify(geometry)}`);
  assert((geometry.boardOverflow || 0) <= 1 && (geometry.documentOverflow || 0) <= 1, `horizontal overflow at ${viewport.width}: ${JSON.stringify(geometry)}`);

  const second = await page.evaluate(() => {
    const api = window.KGGTherapyCockpit;
    const one = api.registry.entries()[3].id;
    return api.encode({ planId: "browser-plan-2", name: "Zweiter Slot", exercises: [{ id: one, sets: 1, previous: [["4", "8"]], today: [["4", "8"]] }] });
  });
  const third = await page.evaluate(() => {
    const api = window.KGGTherapyCockpit;
    const one = api.registry.entries()[4].id;
    return api.encode({ planId: "browser-plan-3", name: "Dritter Slot", exercises: [{ id: one, sets: 1, previous: [["5", "9"]], today: [["5", "9"]] }] });
  });
  await page.evaluate(({ second, third }) => { window.KGGTherapyCockpit.importCode(second); window.KGGTherapyCockpit.importCode(third); }, { second, third });
  await page.waitForFunction(() => document.querySelectorAll(".kgg-tc-card").length === 3, null, { timeout: 5000 });
  const three = await inspectGeometry(page, viewport);
  assert(three.columns === 3 && three.cards === 3, `three-slot grid failed: ${JSON.stringify(three)}`);
  assert((three.boardOverflow || 0) <= 1 && (three.documentOverflow || 0) <= 1, `three-slot overflow at ${viewport.width}: ${JSON.stringify(three)}`);

  await page.locator('.kgg-tc-card[data-tc-card="0"] .kgg-tc-card-toggle').first().click();
  await page.locator('.kgg-tc-card[data-tc-card="0"] .kgg-tc-field').first().click();
  await page.waitForSelector('.kgg-tc-card[data-tc-card="0"] .kgg-tc-pad', { state: "visible", timeout: 5000 });
  const keypad = await page.evaluate(() => ({
    open: document.querySelector('.kgg-tc-card[data-tc-card="0"] .kgg-tc-exercise.open') !== null,
    pads: document.querySelectorAll('.kgg-tc-card[data-tc-card="0"] .kgg-tc-pad').length,
    previousBackground: getComputedStyle(document.querySelector('.kgg-tc-card[data-tc-card="0"] .kgg-tc-prev')).backgroundColor,
    todayBackground: getComputedStyle(document.querySelector('.kgg-tc-card[data-tc-card="0"] .kgg-tc-field')).backgroundColor,
    scrollContainers: document.querySelectorAll('.kgg-tc-card[data-tc-card="0"] .kgg-tc-scroll').length,
  }));
  assert(keypad.open && keypad.pads === 1, `inline keypad did not open in card: ${JSON.stringify(keypad)}`);
  assert(keypad.previousBackground !== keypad.todayBackground && keypad.scrollContainers === 1, `previous/today styling or independent scroll container failed: ${JSON.stringify(keypad)}`);
  await page.locator('[data-tc-action="mode"][data-tc-field="metric"]').first().click();
  const metricMode = await page.evaluate(() => ({
    pad: document.querySelector('.kgg-tc-card[data-tc-card="0"] .kgg-tc-pad') !== null,
    metricActive: document.querySelector('.kgg-tc-card[data-tc-card="0"] .kgg-tc-pad-mode.active')?.getAttribute('data-tc-field'),
  }));
  assert(metricMode.pad && metricMode.metricActive === "metric", `kg/Wdh keypad mode switch failed: ${JSON.stringify(metricMode)}`);
  await page.locator('.kgg-tc-card[data-tc-card="0"] .kgg-tc-card-head').click();
  const outside = await page.evaluate(() => ({
    pad: document.querySelector('.kgg-tc-card[data-tc-card="0"] .kgg-tc-pad') !== null,
    open: document.querySelector('.kgg-tc-card[data-tc-card="0"] .kgg-tc-exercise.open') !== null,
  }));
  assert(!outside.pad && outside.open, `outside tap closed the card or left keypad open: ${JSON.stringify(outside)}`);

  await page.locator('[data-tc-action="normal"]').click();
  const normal = await page.evaluate(() => ({ open: document.body.classList.contains("kggTherapyCockpitOpen"), slots: window.KGGTherapyCockpit.getState().slotCount }));
  assert(!normal.open && normal.slots === 3, `normal-app switch lost slots: ${JSON.stringify(normal)}`);
  await page.locator("#kggTherapyCockpitButton").click();
  await page.waitForFunction(() => document.body.classList.contains("kggTherapyCockpitOpen"), null, { timeout: 5000 });
  const fullGuard = await page.evaluate(() => {
    const api = window.KGGTherapyCockpit;
    try {
      api.importCode(api.encode({ name: "Vierter", exercises: [{ id: api.registry.entries()[5].id, sets: 1, previous: [["1", "1"]], today: [["1", "1"]] }] }));
      return { code: "no-error", slots: api.getState().slotCount };
    } catch (error) { return { code: error.code, slots: api.getState().slotCount }; }
  });
  assert(fullGuard.code === "slots_full" && fullGuard.slots === 3, `fourth-slot guard failed: ${JSON.stringify(fullGuard)}`);

  await page.locator('[data-tc-action="remove"][data-tc-slot="1"]').click();
  const removed = await page.evaluate(() => ({ state: window.KGGTherapyCockpit.getState(), names: Array.from(document.querySelectorAll(".kgg-tc-card-title strong")).map(el => el.textContent) }));
  assert(removed.state.slotCount === 2 && removed.state.slots[1] === null && removed.names.includes("Browser Müller") && removed.names.includes("Dritter Slot"), `middle-slot removal failed: ${JSON.stringify(removed)}`);

  await page.locator('[data-tc-action="finish"][data-tc-slot="0"]').click();
  await page.waitForSelector("#kggTherapyCockpitOutputModal:not([hidden])", { timeout: 5000 });
  const output = await page.locator("#kggTherapyCockpitOutput").inputValue();
  assert(output.includes("Neuer Cockpit-Link") && output.includes("Browser Müller") && output.includes("https://kayus24.github.io/kgg/kgg-update/index.html?cockpit="), "finish output missing documentation/public link");
  await page.locator('[data-tc-action="output-close"]').click();
  const afterFinish = await page.evaluate(() => window.KGGTherapyCockpit.getState());
  assert(afterFinish.slotCount === 1, `finish did not release one slot: ${JSON.stringify(afterFinish)}`);
  await page.locator('[data-tc-action="finish"][data-tc-slot="2"]').click();
  await page.waitForSelector("#kggTherapyCockpitOutputModal:not([hidden])", { timeout: 5000 });
  await page.locator('[data-tc-action="output-close"]').click();
  const finalState = await page.evaluate(() => ({ state: window.KGGTherapyCockpit.getState(), body: document.body.classList.contains("kggTherapyCockpitOpen") }));
  assert(finalState.state.slotCount === 0 && !finalState.body, `last finish did not return to normal app: ${JSON.stringify(finalState)}`);

  // A reload simulates process loss for the RAM-only slot contract. The
  // query is removed after the first import, so a fresh document has no slot.
  const ramPage = await page.context().newPage();
  try {
    await ramPage.goto(hrefWithCode(code), { waitUntil: "domcontentloaded", timeout: 30000 });
    await ramPage.waitForFunction(() => document.body.classList.contains("kggTherapyCockpitOpen"), null, { timeout: 15000 });
    await ramPage.reload({ waitUntil: "domcontentloaded", timeout: 30000 });
    const afterReload = await ramPage.evaluate(() => ({ state: window.KGGTherapyCockpit.getState(), body: document.body.classList.contains("kggTherapyCockpitOpen") }));
    assert(afterReload.state.slotCount === 0 && !afterReload.body, `RAM-only reload boundary failed: ${JSON.stringify(afterReload)}`);
  } finally {
    await ramPage.close();
  }
  return { viewport, geometry, three, keypad, outside, removed, finalState, codeChars: code.length };
}

(async () => {
  const browser = await chromium.launch({ headless: true });
  const results = [];
  try {
    for (const viewport of VIEWPORTS) {
      const context = await browser.newContext({ viewport, deviceScaleFactor: 1, hasTouch: true, isMobile: false, locale: "de-DE" });
      const page = await context.newPage();
      const pageErrors = [];
      page.on("pageerror", error => pageErrors.push(error.message));
      try {
        const code = await seedAndOpen(page, viewport);
        const result = await runViewport(page, viewport, code);
        if (pageErrors.length) fail(`page error at ${viewport.width}: ${pageErrors.join(" | ")}`);
        results.push(result);
      } finally {
        await context.close();
      }
    }
  } finally {
    await browser.close();
  }
  console.log(JSON.stringify({ status: "PASS", viewports: results.map(result => result.viewport), checks: ["1/2/3 slots", "no overflow", "inline keypad", "outside tap", "view switch", "fourth guard", "middle removal", "finish roundtrip", "zero-slot return", "RAM-only reload boundary"] }, null, 2));
})().catch(error => { console.error(error.stack || error); process.exitCode = 1; });
