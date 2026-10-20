#!/usr/bin/env node
"use strict";

const path = require("path");
const fs = require("fs");
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

async function verifyDeleteUndoAndPhoneDock(browser) {
  const normalContext = await browser.newContext({ viewport: { width: 1280, height: 800 }, locale: "de-DE" });
  const normalPage = await normalContext.newPage();
  const normalErrors = [];
  normalPage.on("pageerror", error => normalErrors.push(error.message));
  await normalPage.addInitScript(() => {
    const exercise = (id, name) => ({ id, localId: id, name, sets: 2, unit: "Wdh", metricUnit: "Wdh", weightUnit: "kg", loadUnit: "kg", side: "BI", previous: [], today: [], progressionVariants: [], media: [] });
    localStorage.setItem("kgg_pwa_install_prompt_seen_v1", "2026-09-08T00:00:00.000Z");
    localStorage.setItem("kgg_html_app_v2_state", JSON.stringify({
      planId: "normal-owner-a", createdAt: "2026-09-08T00:00:00.000Z", patient: { name: "Patient Alpha", date: "2026-09-08", therapist: "" },
      plan: [exercise("normal-a", "Normal Alpha"), exercise("normal-b", "Normal Beta"), exercise("normal-c", "Normal Gamma")],
      recent: [{ name: "Recent Plan Beta", patient: { name: "Patient Beta", date: "2026-09-07", therapist: "" }, exercises: [exercise("recent-beta", "Recent Beta Exercise")] }],
    }));
  });
  try {
    await normalPage.goto(HTML_URL, { waitUntil: "domcontentloaded", timeout: 30000 });
    await normalPage.waitForFunction(() => document.querySelectorAll("#planList .planCard").length === 3 && document.querySelector("#planList").dataset.kggPlanDeleteUndoBound === "1", null, { timeout: 15000 });
    const deleteSize = await normalPage.locator("#planList [data-del]").first().evaluate(button => ({ width: button.getBoundingClientRect().width, height: button.getBoundingClientRect().height, type: button.type }));
    assert(deleteSize.width >= 44 && deleteSize.height >= 44 && deleteSize.type === "button", `normal delete target did not meet the 44px button contract: ${JSON.stringify(deleteSize)}`);
    await normalPage.locator("#planList [data-del]").first().evaluate(button => button.click());
    await normalPage.waitForFunction(() => document.querySelectorAll("#planList .planCard").length === 2, null, { timeout: 3000 });
    await normalPage.waitForSelector("#kggSharedUndoToast.is-visible", { timeout: 3000 });
    await normalPage.locator("#kggSharedUndoToast button").evaluate(button => button.click());
    await normalPage.waitForFunction(() => document.querySelectorAll("#planList .planCard").length === 3, null, { timeout: 3000 });

    await normalPage.locator("#planList [data-del]").first().evaluate(button => button.click());
    await normalPage.waitForFunction(() => document.querySelectorAll("#planList .planCard").length === 2, null, { timeout: 3000 });
    await normalPage.locator("#recentToggle").evaluate(button => button.click());
    await normalPage.waitForSelector("#recentList [data-recent-index='0']", { timeout: 3000 });
    await normalPage.locator("#recentList [data-recent-index='0']").evaluate(button => button.click());
    await normalPage.waitForFunction(() => document.querySelectorAll("#planList .planCard").length === 1 && document.querySelector("#planList .planName")?.textContent.includes("Recent Beta"), null, { timeout: 3000 });
    await normalPage.locator("#kggSharedUndoToast button").evaluate(button => button.click());
    const afterPlanSwitchUndo = await normalPage.evaluate(() => Array.from(document.querySelectorAll("#planList .planName")).map(node => node.textContent.trim()));
    assert(afterPlanSwitchUndo.length === 1 && afterPlanSwitchUndo[0] === "Recent Beta Exercise", `normal-plan Undo crossed into a restored plan: ${JSON.stringify(afterPlanSwitchUndo)}`);
    assert(normalErrors.length === 0, `normal delete/undo path raised a page error: ${normalErrors.join(" | ")}`);
  } finally {
    await normalContext.close();
  }

  const cockpitContext = await browser.newContext({ viewport: { width: 1024, height: 768 }, locale: "de-DE" });
  const cockpitPage = await cockpitContext.newPage();
  try {
    await cockpitPage.goto(HTML_URL, { waitUntil: "domcontentloaded", timeout: 30000 });
    await cockpitPage.waitForFunction(() => !!window.KGGTherapyCockpit, null, { timeout: 15000 });
    const codes = await cockpitPage.evaluate(() => {
      const api = window.KGGTherapyCockpit;
      const idA = api.registry.entries()[0].id, idB = api.registry.entries()[3].id;
      const encode = (planId, name, id) => api.encode({ planId, name, exercises: [{ id, sets: 1, previous: [["5", "8"]], today: [["5", "8"]] }] });
      return { oldCode: encode("undo-old-owner", "Old owner", idA), newCode: encode("undo-new-owner", "New owner", idB) };
    });
    await cockpitPage.evaluate(code => window.KGGTherapyCockpit.importCode(code), codes.oldCode);
    await cockpitPage.waitForSelector('.kgg-tc-card[data-tc-card="0"] .kgg-tce-tool[data-tce-action="delete"]', { timeout: 5000 });
    await cockpitPage.locator('.kgg-tc-card[data-tc-card="0"] .kgg-tce-tool[data-tce-action="delete"]').evaluate(button => button.click());
    await cockpitPage.waitForTimeout(20);
    await cockpitPage.evaluate(() => window.KGGTherapyCockpit.remove(0));
    await cockpitPage.evaluate(code => window.KGGTherapyCockpit.importCode(code), codes.newCode);
    await cockpitPage.waitForTimeout(240);
    const delayedReuse = await cockpitPage.evaluate(() => ({ name: window.KGGTherapyCockpit.getState().slots[0]?.name, count: window.KGGTherapyCockpit.getSlot(0)?.exercises.length }));
    assert(delayedReuse.name === "New owner" && delayedReuse.count === 1, `delayed Cockpit delete affected a reused slot: ${JSON.stringify(delayedReuse)}`);

    await cockpitPage.locator('.kgg-tc-card[data-tc-card="0"] .kgg-tce-tool[data-tce-action="delete"]').evaluate(button => button.click());
    await cockpitPage.waitForSelector("#kggSharedUndoToast.is-visible", { timeout: 3000 });
    await cockpitPage.locator("#kggSharedUndoToast button").evaluate(button => button.click());
    const sameOwnerUndo = await cockpitPage.evaluate(() => window.KGGTherapyCockpit.getSlot(0)?.exercises.length);
    assert(sameOwnerUndo === 1, `Cockpit Undo did not restore the same owner: ${sameOwnerUndo}`);

    await cockpitPage.locator('.kgg-tc-card[data-tc-card="0"] .kgg-tce-tool[data-tce-action="delete"]').evaluate(button => button.click());
    await cockpitPage.waitForSelector("#kggSharedUndoToast.is-visible", { timeout: 3000 });
    await cockpitPage.evaluate(() => window.KGGTherapyCockpit.remove(0));
    await cockpitPage.evaluate(code => window.KGGTherapyCockpit.importCode(code), codes.oldCode);
    await cockpitPage.locator("#kggSharedUndoToast button").evaluate(button => button.click());
    const staleOwnerUndo = await cockpitPage.evaluate(() => ({ name: window.KGGTherapyCockpit.getState().slots[0]?.name, count: window.KGGTherapyCockpit.getSlot(0)?.exercises.length }));
    assert(staleOwnerUndo.name === "Old owner" && staleOwnerUndo.count === 1, `Cockpit Undo crossed into a different patient slot: ${JSON.stringify(staleOwnerUndo)}`);
  } finally {
    await cockpitContext.close();
  }

  const phoneContext = await browser.newContext({ viewport: { width: 390, height: 844 }, screen: { width: 390, height: 844 }, isMobile: true, hasTouch: true, deviceScaleFactor: 1, locale: "de-DE" });
  const phonePage = await phoneContext.newPage();
  try {
    await phonePage.addInitScript(() => {
      const exercise = { id: "phone-normal", localId: "phone-normal", name: "Normaler Plan", sets: 1, unit: "Wdh", metricUnit: "Wdh", weightUnit: "kg", loadUnit: "kg", side: "BI", previous: [], today: [], media: [] };
      localStorage.setItem("kgg_pwa_install_prompt_seen_v1", "2026-09-08T00:00:00.000Z");
      localStorage.setItem("kgg_html_app_v2_state", JSON.stringify({ planId: "phone-plan", createdAt: "2026-09-08T00:00:00.000Z", patient: { name: "Phone Patient", date: "2026-09-08", therapist: "" }, plan: [exercise], recent: [] }));
    });
    await phonePage.goto(HTML_URL, { waitUntil: "domcontentloaded", timeout: 30000 });
    await phonePage.waitForFunction(() => !!window.KGGTherapyCockpit, null, { timeout: 15000 });
    const code = await phonePage.evaluate(() => window.KGGTherapyCockpit.encode({ planId: "phone-cockpit", name: "Phone Cockpit", exercises: [{ id: window.KGGTherapyCockpit.registry.entries()[0].id, sets: 1, previous: [["4", "8"]], today: [["4", "8"]] }] }));
    await phonePage.evaluate(value => window.KGGTherapyCockpit.importCode(value), code);
    await phonePage.waitForFunction(() => document.body.classList.contains("kggPhoneCockpitOpen") && document.getElementById("kggPhoneCockpitDock")?.getBoundingClientRect().height >= 44, null, { timeout: 5000 });
    const openDock = await phonePage.evaluate(() => ({
      viewport: { width: innerWidth, height: innerHeight, orientation: screen.orientation?.type || "" },
      buttonCount: document.querySelectorAll("#kggTherapyCockpitButton").length,
      finishCount: document.querySelectorAll("#finishBtn").length,
      cockpitParent: document.getElementById("kggTherapyCockpitButton")?.parentElement?.id,
      finishParent: document.getElementById("finishBtn")?.parentElement?.id,
      finishHidden: document.getElementById("finishBtn")?.classList.contains("hidden"),
      cameraVisible: getComputedStyle(document.getElementById("kggPhoneCockpitCamera")).display !== "none",
      saveVisible: !document.getElementById("kggPhoneCockpitSaveAll").hidden && getComputedStyle(document.getElementById("kggPhoneCockpitSaveAll")).display !== "none",
      rootWidth: document.getElementById("kggTherapyCockpitRoot").getBoundingClientRect().width,
    }));
    assert(openDock.viewport.width === 390 && openDock.rootWidth === 390 && openDock.buttonCount === 1 && openDock.finishCount === 1 && openDock.cockpitParent === "kggPhoneCockpitDock" && openDock.finishParent === "planActions" && openDock.cameraVisible && openDock.saveVisible, `portrait phone dock/navigation layout failed: ${JSON.stringify(openDock)}`);
    await phonePage.screenshot({path:path.join(ROOT,"tmp/review/cockpit-phone.png")});
    await phonePage.locator('[data-tc-action="import-open"]').evaluate(button => button.click());
    await phonePage.waitForSelector('#kggTherapyCockpitImportModal:not([hidden])');
    assert(await phonePage.locator('#kggPhoneCockpitDock').evaluate(element => getComputedStyle(element).display === 'none'), 'phone dock obscured the import modal');
    await phonePage.locator('[data-tc-action="import-cancel"]').evaluate(button => button.click());
    await phonePage.evaluate(() => { window.__cameraCalls = []; window.KGGScan.pick = kind => window.__cameraCalls.push(kind); document.getElementById("kggPhoneCockpitCamera").click(); });
    const cameraCall = await phonePage.evaluate(() => window.__cameraCalls.slice());
    assert(cameraCall.length === 1 && cameraCall[0] === "camera", `Cockpit camera action did not reuse the existing scan button: ${JSON.stringify(cameraCall)}`);
    await phonePage.locator("#kggTherapyCockpitButton").evaluate(button => button.click());
    await phonePage.waitForFunction(() => !document.body.classList.contains("kggTherapyCockpitOpen") && document.getElementById("kggTherapyCockpitButton").textContent === "Cockpit", null, { timeout: 3000 });
    assert(!(await phonePage.locator("#kggPhoneCockpitCamera").isVisible()), "Cockpit camera action remained visible in the normal app view");
    assert(await phonePage.locator('#finishBtn').evaluate(button => button.parentElement.id === 'kggPhoneCockpitDock'), 'normal phone Finish button did not return to dock');
    await phonePage.locator("#finishBtn").evaluate(button => button.click());
    await phonePage.waitForSelector("#shareModal.open", { timeout: 3000 });
    await phonePage.locator("#closeShare").evaluate(button => button.click());
    await phonePage.setViewportSize({ width: 820, height: 1180 });
    await phonePage.waitForFunction(() => !document.body.classList.contains("kggPhoneCockpitOpen") && document.getElementById('finishBtn')?.parentElement?.id === 'planActions' && document.getElementById('kggTherapyCockpitButton')?.parentElement?.id === 'baseToggle', null, { timeout: 3000 });
    const restoredParents = await phonePage.evaluate(() => ({ finish: document.getElementById("finishBtn")?.parentElement?.id, cockpit: document.getElementById("kggTherapyCockpitButton")?.parentElement?.id }));
    assert(restoredParents.finish === "planActions" && restoredParents.cockpit === "baseToggle" && !(await phonePage.locator('#kggPhoneCockpitCamera').isVisible()), `phone-to-tablet resize did not restore the original app controls: ${JSON.stringify(restoredParents)}`);
  } finally {
    await phoneContext.close();
  }
  return { normalDeleteUndo: "same-owner pass; restored-plan stale-owner rejected", cockpitDeleteUndo: "same-owner pass; delayed slot reuse and stale-owner undo rejected", phoneDock: "portrait nav, camera delegate, finish action and resize restoration pass" };
}

async function seedAndOpen(page, viewport) {
  await page.setViewportSize(viewport);
  await page.addInitScript(() => {
    localStorage.setItem("kgg_pwa_install_prompt_seen_v1", "2026-09-08T00:00:00.000Z");
    localStorage.setItem("kgg_admin_local_secrets_v1", JSON.stringify({ version: 2, updatedAt: "2026-09-08T00:00:00.000Z", geminiKeys: ["browser-test"], mediaDropzoneEndpoint: "", mediaDropzoneUploadToken: "" }));
  });
  await page.goto(HTML_URL, { waitUntil: "domcontentloaded", timeout: 30000 });
  await page.waitForSelector("#kggTherapyCockpitButton", { state: "attached", timeout: 15000 });
  await verifyDirectPlanImportFromCurrentPlan(page);
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

async function verifySeamHandle(page, viewport) {
  const button = page.locator('#kggTherapyCockpitButton');
  await page.waitForFunction(() => !!window.KGG_PATCHES?.['kgg-v107-cockpit-seam-pull-handle']);
  await page.waitForFunction(() => Math.abs(document.getElementById('kggTherapyCockpitButton').getBoundingClientRect().left-document.getElementById('kggTherapyCockpitRoot').getBoundingClientRect().left)<=2);
  const before = await page.evaluate(() => JSON.stringify(window.KGGTherapyCockpit.getState().slots));
  const root = await page.locator('#kggTherapyCockpitRoot').boundingBox();
  const grip = await button.boundingBox();
  assert(Math.abs(grip.x - root.x) <= 2 && grip.width >= 44, `handle is not on Cockpit side of seam: ${JSON.stringify({root,grip})}`);
  const shell = await page.locator('.kgg-tc-shell').boundingBox();
  assert(Math.abs(shell.x-root.x)<=1 && Math.abs(shell.width-root.width)<=1, `Cockpit still reserves the removed full-height handle stripe: ${JSON.stringify({shell,root,grip})}`);
  const gripHit = await button.evaluate(node => {
    const rect = node.getBoundingClientRect();
    const target = document.elementFromPoint(rect.x+rect.width/2, rect.y+rect.height/2);
    return target === node || node.contains(target);
  });
  assert(gripHit, "floating seam handle is not hit-testable");
  const x = grip.x + 20, y = grip.y + 20;
  // Short pull and vertical motion must settle, without closing or changing plans.
  for (const delta of [{x:20,y:0},{x:0,y:80}]) {
    await page.mouse.move(x,y); await page.mouse.down(); await page.waitForTimeout(90);
    await page.mouse.move(x+delta.x,y+delta.y,{steps:4}); await page.mouse.up();
    assert(await page.evaluate(() => document.body.classList.contains('kggTherapyCockpitOpen') && !document.body.classList.contains('kggTcSeamDragging')), 'short/vertical pull did not settle');
  }
  await page.mouse.move(x,y); await page.mouse.down(); await page.waitForTimeout(90);
  const distance = Math.max(60,root.width*.4);
  await page.mouse.move(x+distance,y,{steps:8});
  const cover = await page.locator('.app').boundingBox();
  const dragState = await page.evaluate(() => ({classes:document.body.className,cover:document.body.style.getPropertyValue('--kgg-cockpit-cover-width'),seam:document.body.style.getPropertyValue('--kgg-cockpit-seam'),parent:document.getElementById('kggTherapyCockpitButton').parentElement.id}));
  assert(Math.abs(cover.width-(root.x+distance))<=2, `main app did not follow pull: ${JSON.stringify({cover,root,distance,dragState})}`);
  await page.mouse.up();
  await page.waitForFunction(() => !document.body.classList.contains('kggTherapyCockpitOpen'));
  const after = await page.evaluate(() => JSON.stringify(window.KGGTherapyCockpit.getState().slots));
  assert(before===after, 'view pull changed Cockpit slots');
  await page.evaluate(() => window.KGGTherapyCockpit.open());
  await page.waitForTimeout(550);
  assert(await page.evaluate(() => document.body.classList.contains('kggTherapyCockpitOpen')), 'Cockpit could not reopen after pull');
}

async function verifyDirectPlanImportFromCurrentPlan(page) {
  await page.evaluate(() => {
    const store = window.KGGDataStore;
    if (!store || typeof store.setCurrentPlan !== "function") throw new Error("KGGDataStore fehlt für den Startlink-Test");
    store.setCurrentPlan({
      id: "browser-start-plan",
      title: "Cockpit-Starttest",
      patient: { name: "Browser Start" },
      exercises: [{ name: "Abduktion Maschine", sourceId: "abd", sets: 2, startLoad: "7", startMetric: "10" }],
    }, "browser_start_link_test");
  });
  await page.locator("#kggTherapyCockpitButton").click();
  await page.waitForSelector('.kgg-tc-card[data-tc-card="0"]', { timeout: 5000 });
  const imported = await page.evaluate(() => {
    const state = window.KGGTherapyCockpit.getState();
    const card = document.querySelector('.kgg-tc-card[data-tc-card="0"]');
    return {
      state,
      patient: state.slots[0]?.name || "",
      exercise: card?.querySelector(".kgg-tc-exercise-summary strong")?.textContent?.trim() || "",
      empty: !!document.querySelector(".kgg-tc-empty"),
    };
  });
  assert(imported.state.slotCount === 1 && imported.patient === "Browser Start", `direct plan import did not create slot 1: ${JSON.stringify(imported)}`);
  assert(imported.exercise === "Abduktion Maschine" && !imported.empty, `direct plan import did not preserve the exercise: ${JSON.stringify(imported)}`);
}

async function inspectGeometry(page, viewport) {
  return page.evaluate(({ width, height }) => {
    const root = document.getElementById("kggTherapyCockpitRoot");
    const shell = document.querySelector(".kgg-tc-shell");
    const header = document.querySelector(".kgg-tc-header");
    const board = document.getElementById("kggTherapyCockpitBoard");
    const footer = document.querySelector(".kgg-tc-footer");
    const footerAction = document.querySelector(".footerActions");
    const grid = document.querySelector(".kgg-tc-grid");
    const app = document.querySelector(".app");
    const rect = element => {
      if (!element) return null;
      const box = element.getBoundingClientRect();
      const style = getComputedStyle(element);
      return { left: Math.round(box.left), right: Math.round(box.right), top: Math.round(box.top), bottom: Math.round(box.bottom), width: Math.round(box.width), height: Math.round(box.height), cssWidth: style.width, minWidth: style.minWidth, boxSizing: style.boxSizing, paddingLeft: style.paddingLeft, paddingRight: style.paddingRight, zoom: style.zoom, offsetWidth: element.offsetWidth, clientWidth: element.clientWidth, transform: style.transform, display: style.display, visibility: style.visibility };
    };
    return {
      root: rect(root), shell: rect(shell), header: rect(header), board: rect(board), footer: rect(footer), footerAction: rect(footerAction), grid: rect(grid), app: rect(app),
      headerOverflow: header ? header.scrollWidth - header.clientWidth : null,
      footerOverflow: footer ? footer.scrollWidth - footer.clientWidth : null,
      cards: document.querySelectorAll(".kgg-tc-card").length,
      columns: grid ? getComputedStyle(grid).gridTemplateColumns.split(" ").length : 0,
      boardOverflow: board ? board.scrollWidth - board.clientWidth : null,
      documentOverflow: document.documentElement.scrollWidth - width,
      clientWidth: document.documentElement.clientWidth,
      innerWidth: window.innerWidth,
      dpr: window.devicePixelRatio,
      bodyZoom: getComputedStyle(document.body).zoom,
      bodyClasses: document.body.className,
      appInlineStyle: app?.getAttribute("style") || "",
      appWidthRules: Array.from(document.styleSheets).flatMap(sheet => { try { return Array.from(sheet.cssRules); } catch (_) { return []; } }).filter(rule => rule.selectorText && rule.selectorText.includes(".app") && rule.style?.width).map(rule => ({ selector: rule.selectorText, width: rule.style.width, important: rule.style.getPropertyPriority("width"), matches: (()=>{try{return app.matches(rule.selectorText)}catch(_){return false}})() })).slice(-20),
      viewport: { width, height },
    };
  }, viewport);
}

async function runViewport(page, viewport, code) {
  const geometry = await inspectGeometry(page, viewport);
  assert(geometry.root && geometry.root.display !== "none" && Math.abs(geometry.root.width - viewport.width / 3) <= 2 && geometry.root.height === viewport.height, `one-slot third geometry failed: ${JSON.stringify(geometry)}`);
  assert(geometry.app && geometry.app.visibility === "visible" && Math.abs(geometry.app.width - viewport.width * 2 / 3) <= 2, `normal app did not keep two thirds: ${JSON.stringify(geometry)}`);
  assert(geometry.shell && geometry.header && geometry.board && geometry.footer && [geometry.shell, geometry.header, geometry.board, geometry.footer].every(rect => rect.width <= geometry.root.width + 1 && rect.right <= geometry.root.right + 1), `cockpit shell/header/board/footer exceeded its one-third region: ${JSON.stringify(geometry)}`);
  assert((geometry.headerOverflow || 0) <= 1 && (geometry.footerOverflow || 0) <= 1, `cockpit header/footer content overflowed: ${JSON.stringify(geometry)}`);
  assert(geometry.footerAction && geometry.footerAction.visibility === "visible" && geometry.footerAction.width <= geometry.app.width + 1, `normal app save/export actions are unavailable in split view: ${JSON.stringify(geometry)}`);
  assert(geometry.cards === 1 && geometry.columns === 1, `initial slot/card geometry failed: ${JSON.stringify(geometry)}`);
  assert((geometry.boardOverflow || 0) <= 1 && (geometry.documentOverflow || 0) <= 1, `horizontal overflow at ${viewport.width}: ${JSON.stringify(geometry)}`);

  await page.locator('.kgg-tc-card[data-tc-card="0"] .kgg-tc-card-toggle').first().click();
  await page.locator('.kgg-tc-card[data-tc-card="0"] .kgg-tc-field[data-tc-field="load"]').first().click();
  await page.waitForSelector('.kgg-tc-card[data-tc-card="0"] .kgg-tc-pad', { state: "visible", timeout: 5000 });
  const setLayout = await page.evaluate(() => {
    const row = document.querySelector('.kgg-tc-card[data-tc-card="0"] .kgg-tc-set-row');
    const card = document.querySelector('.kgg-tc-card[data-tc-card="0"]');
    const box = element => { const rect = element.getBoundingClientRect(); return { top: rect.top, right: rect.right, bottom: rect.bottom }; };
    return {
      row: box(row),
      set: box(row.querySelector(".kgg-tc-set-no")),
      previous: box(row.querySelector(".kgg-tc-prev")),
      load: box(row.querySelector('.kgg-tc-field[data-tc-field="load"]')),
      metric: box(row.querySelector('.kgg-tc-field[data-tc-field="metric"]')),
      pad: box(row.querySelector(".kgg-tc-pad")),
      units: Array.from(row.querySelectorAll(".kgg-tc-field-unit")).map(element => element.textContent.trim()),
      previousUnits: Array.from(row.querySelectorAll(".kgg-tc-prev-unit")).map(element => element.textContent.trim()),
      previousUnitFont: Math.min(...Array.from(row.querySelectorAll(".kgg-tc-prev-unit")).map(element => parseFloat(getComputedStyle(element).fontSize))),
      fieldUnitFont: Math.min(...Array.from(row.querySelectorAll(".kgg-tc-field-unit")).map(element => parseFloat(getComputedStyle(element).fontSize))),
      previousValueFont: Math.min(...Array.from(row.querySelectorAll(".kgg-tc-prev-value")).map(element => parseFloat(getComputedStyle(element).fontSize))),
      card: box(card),
    };
  });
  const rowTops = [setLayout.set.top, setLayout.previous.top, setLayout.load.top, setLayout.metric.top];
  assert(Math.max(...rowTops) - Math.min(...rowTops) <= 2, `set values did not stay on one row: ${JSON.stringify(setLayout)}`);
  assert(setLayout.pad.top > setLayout.metric.bottom - 1, `inline keypad did not sit below the set row: ${JSON.stringify(setLayout)}`);
  assert(setLayout.units.includes("kg") && setLayout.units.includes("Wdh") && setLayout.previousUnits.includes("kg") && setLayout.previousUnits.includes("Wdh"), `visible value units are incomplete: ${JSON.stringify(setLayout)}`);
  assert(setLayout.previousUnitFont >= 12 && setLayout.fieldUnitFont >= 12 && setLayout.previousValueFont >= 12, `supporting values/units fell below the 12px minimum: ${JSON.stringify(setLayout)}`);
  assert(Math.max(setLayout.set.right, setLayout.previous.right, setLayout.load.right, setLayout.metric.right, setLayout.pad.right) <= setLayout.card.right + 1, `set values overflowed the patient card: ${JSON.stringify(setLayout)}`);
  await page.locator('.kgg-tc-card[data-tc-card="0"] .kgg-tc-pad [data-tc-key="C"]').click();
  await page.locator('.kgg-tc-card[data-tc-card="0"] .kgg-tc-pad [data-tc-key="7"]').click();
  await page.locator('.kgg-tc-card[data-tc-card="0"] .kgg-tc-pad [data-tc-key="OK"]').click();
  const committed = await page.evaluate(() => ({
    value: window.KGGTherapyCockpit.getSlot(0).exercises[0].today[0][0],
    label: document.querySelector('.kgg-tc-card[data-tc-card="0"] .kgg-tc-field[data-tc-field="load"]')?.getAttribute("aria-label"),
  }));
  assert(committed.value === "7" && committed.label === "Heute 7 kg", `inline input did not retain the visible unit/value: ${JSON.stringify(committed)}`);

  await page.setViewportSize({ width: 390, height: 844 });
  await page.waitForFunction(() => !document.body.classList.contains("kggTcTabletSplit"), null, { timeout: 3000 });
  const phoneRestore = await page.evaluate(() => ({
    rootWidth: document.getElementById("kggTherapyCockpitRoot").getBoundingClientRect().width,
    rootHasTabletClass: document.body.classList.contains("kggTcTabletSplit"),
    prevWrapped: document.querySelector(".kgg-tc-prev").classList.contains("kgg-v096-pair"),
    fieldWrapped: !!document.querySelector(".kgg-tc-field .kgg-tc-field-unit"),
    prevText: document.querySelector(".kgg-tc-prev").textContent,
  }));
  assert(!phoneRestore.rootHasTabletClass && Math.abs(phoneRestore.rootWidth - 390) <= 1 && !phoneRestore.prevWrapped && !phoneRestore.fieldWrapped && phoneRestore.prevText.includes(" / "), `tablet-to-phone resize did not restore the existing compact row markup: ${JSON.stringify(phoneRestore)}`);
  await page.setViewportSize(viewport);
  await page.waitForFunction(() => document.body.classList.contains("kggTcTabletSplit"), null, { timeout: 3000 });
  await page.waitForFunction(() => !!document.querySelector(".kgg-tc-field-unit"), null, { timeout: 3000 });
  const reviewDir = path.join(ROOT, "tmp", "review");
  fs.mkdirSync(reviewDir, { recursive: true });
  await page.screenshot({ path: path.join(reviewDir, `cockpit-${viewport.width}-one-slot.png`), fullPage: false });

  const observerStability = await page.evaluate(async () => {
    let classMutations = 0;
    const layoutState = () => ["kggTcTabletSplit", "kggTcSlots1", "kggTcSlots2", "kggTcSlots3"].map(name => document.body.classList.contains(name) ? name : "").join("|");
    const before = layoutState();
    const observer = new MutationObserver(records => { classMutations += records.length; });
    observer.observe(document.body, { attributes: true, attributeFilter: ["class"] });
    await new Promise(resolve => setTimeout(resolve, 250));
    observer.disconnect();
    return { classMutations, slotCount: document.body.dataset.kggTcSlotCount, before, after: layoutState() };
  });
  assert(observerStability.classMutations <= 6 && observerStability.slotCount === "1" && observerStability.before === observerStability.after, `tablet layout observer did not settle: ${JSON.stringify(observerStability)}`);

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
  await page.evaluate(second => window.KGGTherapyCockpit.importCode(second), second);
  await page.waitForFunction(() => document.body.dataset.kggTcSlotCount === "2", null, { timeout: 5000 });
  const two = await inspectGeometry(page, viewport);
  assert(Math.abs(two.root.width - viewport.width * 2 / 3) <= 2 && Math.abs(two.app.width - viewport.width / 3) <= 2, `two-slot regions are not one third each: ${JSON.stringify(two)}`);
  assert(two.cards === 2 && two.columns === 2 && two.app.visibility === "visible", `two-slot grid/app state failed: ${JSON.stringify(two)}`);
  assert(two.board && two.board.width <= two.root.width + 1 && (two.documentOverflow || 0) <= 1, `two-slot cockpit overflowed: ${JSON.stringify(two)}`);
  assert(two.header.width <= two.root.width + 1 && two.footer.width <= two.root.width + 1 && two.footerAction.width <= two.app.width + 1, `two-slot split header/footer/actions exceeded their panes: ${JSON.stringify(two)}`);

  await page.evaluate(third => window.KGGTherapyCockpit.importCode(third), third);
  await page.waitForFunction(() => document.querySelectorAll(".kgg-tc-card").length === 3, null, { timeout: 5000 });
  const three = await inspectGeometry(page, viewport);
  assert(Math.abs(three.root.width - viewport.width) <= 1 && three.app.display === "none", `three-slot cockpit did not take the full tablet: ${JSON.stringify(three)}`);
  assert(three.columns === 3 && three.cards === 3, `three-slot grid failed: ${JSON.stringify(three)}`);
  assert((three.boardOverflow || 0) <= 1 && (three.documentOverflow || 0) <= 1, `three-slot overflow at ${viewport.width}: ${JSON.stringify(three)}`);
  await page.screenshot({ path: path.join(ROOT, "tmp", "review", `cockpit-${viewport.width}-three-slots.png`), fullPage: false });

  if (!await page.locator('.kgg-tc-card[data-tc-card="0"] .kgg-tc-exercise.open').count()) {
    await page.locator('.kgg-tc-card[data-tc-card="0"] .kgg-tc-card-toggle').first().click();
  }
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

  await verifySeamHandle(page, viewport);

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
  await verifySeamHandle(page, viewport);

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
  let deleteUndoAndPhoneDock;
  try {
    for (const viewport of VIEWPORTS) {
      const context = await browser.newContext({ viewport, deviceScaleFactor: 1, hasTouch: true, isMobile: false, locale: "de-DE" });
      const page = await context.newPage();
      const pageErrors = [];
      page.on("pageerror", error => pageErrors.push(error.message));
      try {
        const code = await seedAndOpen(page, viewport);
        await verifySeamHandle(page, viewport);
        const result = await runViewport(page, viewport, code);
        if (pageErrors.length) fail(`page error at ${viewport.width}: ${pageErrors.join(" | ")}`);
        results.push(result);
      } finally {
        await context.close();
      }
    }
    deleteUndoAndPhoneDock = await verifyDeleteUndoAndPhoneDock(browser);
    console.log(JSON.stringify({ deleteUndoAndPhoneDock }, null, 2));
  } finally {
    await browser.close();
  }
  console.log(JSON.stringify({ status: "PASS", viewports: results.map(result => result.viewport), screenshots: "tmp/review/cockpit-*-one-slot.png and cockpit-*-three-slots.png", checks: ["1/2/3 slots", "no overflow", "header/footer pane bounds", "visible normal-app actions", "12px support text", "tablet-to-phone resize restoration", "inline keypad", "outside tap", "view switch", "fourth guard", "middle removal", "finish roundtrip", "zero-slot return", "RAM-only reload boundary"] }, null, 2));
})().catch(error => { console.error(error.stack || error); process.exitCode = 1; });
