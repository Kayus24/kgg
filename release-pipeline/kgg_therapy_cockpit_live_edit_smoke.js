#!/usr/bin/env node
"use strict";

const path = require("path");
const { pathToFileURL } = require("url");
const { chromium } = require("playwright");

const ROOT = path.resolve(__dirname, "..");
const HTML_URL = pathToFileURL(path.join(ROOT, "kgg-update", "index.html")).href;

function fail(message) { throw new Error(message); }
function assert(value, message) { if (!value) fail(message); }
function codeUrl(code) { const url = new URL(HTML_URL); url.searchParams.set("cockpit", code); return url.toString(); }
function exercise(id, offset) {
  return { id, sets: 2, side: "BI", loadUnit: "kg", metricUnit: "Wdh", previous: [[String(10 + offset), "12"], [String(11 + offset), "11"]], today: [[String(10 + offset), "12"], [String(11 + offset), "11"]] };
}

async function waitForEditUi(page) {
  await page.waitForSelector('.kgg-tc-card[data-tc-card="0"] .kgg-tce-add-card', { state: "visible", timeout: 5000 });
  await page.waitForSelector(".kgg-tce-mobile-nav", { state: "visible", timeout: 5000 });
}

(async () => {
  const browser = await chromium.launch({ headless: true });
  const context = await browser.newContext({ viewport: { width: 820, height: 1180 }, deviceScaleFactor: 1, hasTouch: true, isMobile: false, locale: "de-DE" });
  let page = await context.newPage();
  const pageErrors = [];
  page.on("pageerror", error => pageErrors.push(error.message));
  await page.addInitScript(() => {
    localStorage.setItem("kgg_pwa_install_prompt_seen_v1", "cockpit-live-edit");
  });
  try {
    await page.goto(HTML_URL, { waitUntil: "domcontentloaded", timeout: 30000 });
    const initial = await page.evaluate(() => {
      const api = window.KGGTherapyCockpit;
      const entries = api.registry.entries();
      const code = api.encode({ planId: "live-edit-plan", name: "Live Edit Patient", date: "2026-09-13", exercises: entries.slice(0, 2).map((entry, index) => ({ id: entry.id, sets: 2, previous: [[String(10 + index), "12"], [String(11 + index), "11"]], today: [[String(10 + index), "12"], [String(11 + index), "11"]] })) });
      return { code, secondId: entries[2].id };
    });
    await page.close();
    page = await context.newPage();
    page.on("pageerror", error => pageErrors.push(error.message));
    await page.addInitScript(() => {
      localStorage.setItem("kgg_pwa_install_prompt_seen_v1", "cockpit-live-edit");
    });
    await page.goto(codeUrl(initial.code), { waitUntil: "domcontentloaded", timeout: 30000 });
    await page.waitForFunction(() => document.body.classList.contains("kggTherapyCockpitOpen"), null, { timeout: 15000 });

    await page.waitForSelector('.kgg-tc-card[data-tc-card="0"] .kgg-tce-add-card', { state: "visible", timeout: 5000 });
    const tabletBefore = await page.evaluate(() => ({
      visibleCards: Array.from(document.querySelectorAll(".kgg-tc-card")).filter(card => getComputedStyle(card).display !== "none").length,
      addCards: document.querySelectorAll(".kgg-tce-add-card").length,
      mobileNavAbsent: !document.querySelector(".kgg-tce-mobile-nav"),
      boardFits: document.querySelector("#kggTherapyCockpitBoard").scrollWidth <= document.querySelector("#kggTherapyCockpitBoard").clientWidth + 1,
    }));
    assert(tabletBefore.visibleCards === 1 && tabletBefore.addCards === 1 && tabletBefore.mobileNavAbsent && tabletBefore.boardFits, `tablet Cockpit edit UI missing: ${JSON.stringify(tabletBefore)}`);

    await page.setViewportSize({ width: 390, height: 844 });
    await page.waitForTimeout(500);
    await waitForEditUi(page);

    const mobileBefore = await page.evaluate(() => ({
      nav: !!document.querySelector(".kgg-tce-mobile-nav"),
      visibleCards: Array.from(document.querySelectorAll(".kgg-tc-card")).filter(card => getComputedStyle(card).display !== "none").length,
      addCards: document.querySelectorAll(".kgg-tce-add-card").length,
      slot: window.KGGTherapyCockpit.getSlot(0),
    }));
    assert(mobileBefore.nav && mobileBefore.visibleCards === 1 && mobileBefore.addCards === 1, `mobile active-card UI missing: ${JSON.stringify(mobileBefore)}`);
    assert(mobileBefore.slot.exercises.length === 2, "initial live-edit slot did not contain two exercises");

    await page.locator('.kgg-tce-tool[data-tce-action="edit"][data-tce-slot="0"][data-tce-ex="0"]').click();
    await page.waitForSelector("#editorModal.open", { timeout: 5000 });
    await page.locator("#editName").fill("Abduktion live bearbeitet");
    await page.locator("#editSets").selectOption("4");
    await page.locator("#editSide").selectOption("LR");
    await page.locator("#editUnit").selectOption("Watt");
    await page.locator("#editMeasure").selectOption("wdh");
    await page.locator("#editLoad").fill("22");
    await page.locator("#editMetric").fill("14");
    await page.locator(".editorAdvanced summary").click();
    await page.locator("#editVideoUrl").fill("https://example.invalid/cockpit-video");
    await page.locator("#editVideoLabel").fill("Anleitung öffnen");
    await page.locator("#kggCockpitAddStage").click();
    await page.locator('[data-cockpit-stage-name]').last().fill("Schwerere Stufe");
    await page.locator('[data-cockpit-stage-source]').last().selectOption({ label: "Bridging" });
    await page.locator("#kggCockpitAddStage").click();
    await page.locator('[data-cockpit-stage-name]').last().fill("Alternative Stufe");
    await page.locator('[data-cockpit-stage-up="1"]').click();
    await page.locator('[data-cockpit-stage-remove="0"]').click();
    await page.locator("#kggCockpitAddStage").click();
    await page.locator('[data-cockpit-stage-name]').last().fill("Leichtere Stufe");
    await page.locator("#saveExercise").click();
    await page.waitForSelector("#editorModal.open", { state: "hidden", timeout: 5000 });
    const edited = await page.evaluate(() => window.KGGTherapyCockpit.getSlot(0));
    assert(edited.exercises[0].name === "Abduktion live bearbeitet" && edited.exercises[0].sets === 4 && edited.exercises[0].side === "LR" && edited.exercises[0].loadUnit === "Watt" && edited.exercises[0].startLoad === "22" && edited.exercises[0].startMetric === "14" && edited.exercises[0].videoUrl === "https://example.invalid/cockpit-video" && edited.exercises[0].videoLabel === "Anleitung öffnen", `shared editor fields did not persist: ${JSON.stringify(edited.exercises[0])}`);
    assert(edited.exercises[0].progressionVariants.length === 2 && edited.exercises[0].progressionVariants[0].name === "Schwerere Stufe" && edited.exercises[0].progressionVariants[0].sourceName === "Bridging" && edited.exercises[0].progressionVariants[1].name === "Leichtere Stufe", `progression stage edit, reorder or bank association did not persist: ${JSON.stringify(edited.exercises[0].progressionVariants)}`);

    await page.locator('.kgg-tce-tool[data-tce-action="edit"][data-tce-slot="0"][data-tce-ex="0"]').click();
    await page.waitForSelector("#editorModal.open", { timeout: 5000 });
    const reopened = await page.evaluate(() => ({ name: document.querySelector("#editName").value, sets: document.querySelector("#editSets").value, side: document.querySelector("#editSide").value, loadUnit: document.querySelector("#editUnit").value, startLoad: document.querySelector("#editLoad").value, video: document.querySelector("#editVideoUrl").value, stages: Array.from(document.querySelectorAll("[data-cockpit-stage-name]")).map(input => input.value) }));
    assert(reopened.name === "Abduktion live bearbeitet" && reopened.sets === "4" && reopened.side === "LR" && reopened.loadUnit === "Watt" && reopened.startLoad === "22" && reopened.video === "https://example.invalid/cockpit-video" && JSON.stringify(reopened.stages) === JSON.stringify(["Schwerere Stufe", "Leichtere Stufe"]), `shared editor did not reopen persisted fields: ${JSON.stringify(reopened)}`);
    await page.locator("#closeEditor").click();
    await page.waitForSelector("#editorModal.open", { state: "hidden", timeout: 5000 });

    await page.locator('[data-tce-stage-switch="1"]').evaluate(select => {
      const option = Array.from(select.options).find(item => item.textContent.trim() === "Leichtere Stufe");
      if (!option) throw new Error("visible progression stage option missing");
      select.value = option.value;
      select.dispatchEvent(new Event("change", { bubbles: true }));
    });
    await page.waitForTimeout(120);
    const switched = await page.evaluate(() => window.KGGTherapyCockpit.getSlot(0));
    assert(switched.exercises[0].activeProgressionId === switched.exercises[0].progressionVariants[1].id, `progression switch did not persist: ${JSON.stringify(switched.exercises[0])}`);
    const invalidStage = await page.evaluate(() => {
      const api = window.KGGTherapyCockpit;
      const before = api.getSlot(0);
      const next = JSON.parse(JSON.stringify(before));
      next.exercises[0].activeProgressionId = "not-a-real-stage";
      try { api.updateSlot(0, next, "test_invalid_progression"); return { code: null, after: api.getSlot(0) }; }
      catch (error) { return { code: error.code, after: api.getSlot(0), before }; }
    });
    assert(invalidStage.code === "progression_id_invalid" && JSON.stringify(invalidStage.after) === JSON.stringify(invalidStage.before), `invalid progression stage was not rejected fail-closed: ${JSON.stringify(invalidStage)}`);

    await page.locator('.kgg-tce-add-card[data-tce-slot="0"]').click();
    await page.waitForSelector("#kggTceAddModal:not([hidden])", { timeout: 5000 });
    await page.locator("#kggTceAddModal .kgg-tce-bank-search").fill("Bridging");
    await page.locator('#kggTceAddModal [data-tce-bank-id]').first().click();
    await page.waitForSelector("#kggTceAddModal[hidden]", { state: "hidden", timeout: 5000 });
    const added = await page.evaluate(() => window.KGGTherapyCockpit.getSlot(0));
    assert(added.exercises.length === 3 && added.exercises[2].name === "Bridging", `plus-card add failed: ${JSON.stringify(added)}`);

    const handles = page.locator('.kgg-tc-card[data-tc-card="0"] .kgg-tce-drag');
    const sourceBox = await handles.nth(1).boundingBox();
    const targetBox = await handles.nth(0).boundingBox();
    assert(sourceBox && targetBox, "reorder handles are not visible");
    await page.mouse.move(sourceBox.x + sourceBox.width / 2, sourceBox.y + sourceBox.height / 2);
    await page.mouse.down();
    await page.mouse.move(targetBox.x + targetBox.width / 2, targetBox.y - 18, { steps: 6 });
    await page.waitForFunction(() => {
      return !!document.querySelector(".kgg-tc-exercise.reorder-lifted") &&
        !!document.querySelector(".reorder-placeholder") &&
        !!document.querySelector(".reorder-gap-before, .reorder-gap-after");
    }, null, { timeout: 2000 });
    const dragStates = await page.evaluate(() => ({ lifted: !!document.querySelector(".kgg-tc-exercise.reorder-lifted"), placeholder: !!document.querySelector(".reorder-placeholder"), gap: !!document.querySelector(".reorder-gap-before, .reorder-gap-after") }));
    assert(dragStates.lifted && dragStates.placeholder && dragStates.gap, `shared reorder states missing during pointer drag: ${JSON.stringify(dragStates)}`);
    await page.mouse.up();
    await page.waitForTimeout(250);
    const reordered = await page.evaluate(() => window.KGGTherapyCockpit.getSlot(0));
    assert(reordered.exercises[0].name === "Adduktion Maschine" && reordered.exercises[1].name === "Abduktion live bearbeitet" && reordered.exercises[2].name === "Bridging", `pointer reorder failed: ${JSON.stringify(reordered)}`);

    const touchStates = await page.evaluate(() => {
      const exercises = Array.from(document.querySelectorAll('.kgg-tc-card[data-tc-card="0"] .kgg-tc-exercise'));
      const source = exercises[2].querySelector(".kgg-tce-drag");
      const sourceRect = source.getBoundingClientRect();
      const firstRect = exercises[0].getBoundingClientRect();
      const event = (type, target, x, y) => target.dispatchEvent(new PointerEvent(type, { bubbles: true, cancelable: true, pointerId: 77, pointerType: "touch", isPrimary: true, button: 0, clientX: x, clientY: y }));
      event("pointerdown", source, sourceRect.left + sourceRect.width / 2, sourceRect.top + sourceRect.height / 2);
      event("pointermove", document, sourceRect.left + sourceRect.width / 2, firstRect.top - 16);
      return { lifted: !!document.querySelector(".kgg-tc-exercise.reorder-lifted"), placeholder: !!document.querySelector(".reorder-placeholder"), gap: !!document.querySelector(".reorder-gap-before, .reorder-gap-after"), pointerType: "touch" };
    });
    assert(touchStates.lifted && touchStates.placeholder && touchStates.gap && touchStates.pointerType === "touch", `touch reorder states missing: ${JSON.stringify(touchStates)}`);
    await page.evaluate(() => document.dispatchEvent(new PointerEvent("pointerup", { bubbles: true, cancelable: true, pointerId: 77, pointerType: "touch", isPrimary: true, button: 0, clientX: 100, clientY: 80 })));
    await page.waitForTimeout(250);
    const touchReordered = await page.evaluate(() => window.KGGTherapyCockpit.getSlot(0));
    assert(touchReordered.exercises[0].name === "Bridging" && touchReordered.exercises[1].name === "Adduktion Maschine" && touchReordered.exercises[2].name === "Abduktion live bearbeitet", `touch reorder failed: ${JSON.stringify(touchReordered)}`);

    const editedRoundtrip = await page.evaluate(() => {
      const api = window.KGGTherapyCockpit;
      const current = api.getSlot(0);
      const decoded = api.decode(api.encode(current));
      return { decoded, edited: decoded.exercises.find(ex => ex.name === "Abduktion live bearbeitet") };
    });
    assert(editedRoundtrip.edited && editedRoundtrip.edited.sets === 4 && editedRoundtrip.edited.side === "LR" && editedRoundtrip.edited.loadUnit === "Watt" && editedRoundtrip.edited.startLoad === "22" && editedRoundtrip.edited.startMetric === "14" && editedRoundtrip.edited.videoLabel === "Anleitung öffnen" && editedRoundtrip.edited.activeProgressionId === editedRoundtrip.edited.progressionVariants[1].id, `full edited slot data did not survive codec roundtrip: ${JSON.stringify(editedRoundtrip.edited)}`);

    await page.locator('.kgg-tce-tool[data-tce-action="edit"][data-tce-slot="0"][data-tce-ex="2"]').click();
    await page.waitForSelector("#editorModal.open", { timeout: 5000 });
    page.once("dialog", dialog => dialog.dismiss());
    await page.locator("#deleteExercise").click();
    await page.waitForTimeout(80);
    const cancelledDelete = await page.evaluate(() => window.KGGTherapyCockpit.getSlot(0));
    assert(cancelledDelete.exercises.length === 3 && cancelledDelete.exercises[2].name === "Abduktion live bearbeitet", `delete cancel removed an exercise: ${JSON.stringify(cancelledDelete)}`);
    page.once("dialog", dialog => dialog.accept());
    await page.locator("#deleteExercise").click();
    await page.waitForTimeout(250);
    const deletedFromEditor = await page.evaluate(() => window.KGGTherapyCockpit.getSlot(0));
    assert(deletedFromEditor.exercises.length === 2 && deletedFromEditor.exercises.every(ex => ex.name !== "Abduktion live bearbeitet"), `shared editor delete failed: ${JSON.stringify(deletedFromEditor)}`);
    await page.waitForSelector("#editorModal.open", { state: "hidden", timeout: 5000 });

    page.once("dialog", dialog => dialog.accept());
    await page.locator('.kgg-tce-tool[data-tce-action="delete"][data-tce-slot="0"][data-tce-ex="0"]').click();
    await page.waitForTimeout(300);
    const deleted = await page.evaluate(() => window.KGGTherapyCockpit.getSlot(0));
    assert(deleted.exercises.length === 1 && deleted.exercises[0].name === "Adduktion Maschine", `direct delete failed: ${JSON.stringify(deleted)}`);

    const roundtrip = await page.evaluate(() => {
      const api = window.KGGTherapyCockpit;
      const current = api.getSlot(0);
      const code = api.encode(current);
      const decoded = api.decode(code);
      return { decoded, codeChars: code.length };
    });
    assert(roundtrip.decoded.exercises.length === 1, "edited slot data did not survive codec roundtrip");

    const secondCode = await page.evaluate(() => {
      const api = window.KGGTherapyCockpit;
      const entry = api.registry.entries()[5];
      return api.encode({ planId: "second-live-edit-plan", name: "Zweiter Live-Edit Slot", date: "2026-09-13", exercises: [{ id: entry.id, sets: 1, previous: [["", ""]], today: [["", ""]] }] });
    });
    await page.locator('[data-tc-action="import-open"]').click();
    await page.waitForSelector("#kggTherapyCockpitImportModal:not([hidden])", { timeout: 5000 });
    await page.locator("#kggTherapyCockpitImportInput").fill(secondCode);
    await page.locator('#kggTherapyCockpitImportModal [data-tc-action="import-submit"]').click();
    await page.waitForFunction(() => window.KGGTherapyCockpit.getState().slotCount === 2, null, { timeout: 5000 });
    await page.locator('.kgg-tce-slot-tab[data-tce-slot="1"]').click();
    await page.waitForTimeout(120);
    const isolatedBefore = await page.evaluate(() => ({
      visibleCards: Array.from(document.querySelectorAll(".kgg-tc-card")).filter(card => getComputedStyle(card).display !== "none").map(card => card.dataset.tcCard),
      slot0: window.KGGTherapyCockpit.getSlot(0),
      slot1: window.KGGTherapyCockpit.getSlot(1),
    }));
    assert(JSON.stringify(isolatedBefore.visibleCards) === JSON.stringify(["1"]), `mobile slot navigation selected more than one card: ${JSON.stringify(isolatedBefore)}`);
    assert(isolatedBefore.slot0.exercises.length === 1 && isolatedBefore.slot1.exercises.length === 1 && isolatedBefore.slot1.name === "Zweiter Live-Edit Slot", `slot isolation setup failed: ${JSON.stringify(isolatedBefore)}`);

    await page.locator('.kgg-tce-add-card[data-tce-slot="1"]').click();
    await page.waitForSelector("#kggTceAddModal:not([hidden])", { timeout: 5000 });
    await page.locator("#kggTceAddModal .kgg-tce-bank-search").fill("Copenhagen");
    await page.locator('#kggTceAddModal [data-tce-bank-id]').first().click();
    await page.waitForSelector("#kggTceAddModal[hidden]", { state: "hidden", timeout: 5000 });
    const isolatedAfter = await page.evaluate(() => ({ slot0: window.KGGTherapyCockpit.getSlot(0), slot1: window.KGGTherapyCockpit.getSlot(1) }));
    assert(isolatedAfter.slot0.exercises.length === 1 && isolatedAfter.slot1.exercises.length === 2 && isolatedAfter.slot1.exercises[1].name === "Copenhagen Plank", `slot edit leaked across patients: ${JSON.stringify(isolatedAfter)}`);
    await page.locator('.kgg-tce-mobile-arrow[data-tce-action="previous"]').click();
    await page.waitForTimeout(120);
    const previousSlot = await page.evaluate(() => ({ active: document.querySelector('.kgg-tce-slot-tab.active')?.dataset.tceSlot, visible: Array.from(document.querySelectorAll(".kgg-tc-card")).filter(card => getComputedStyle(card).display !== "none").map(card => card.dataset.tcCard) }));
    assert(previousSlot.active === "0" && JSON.stringify(previousSlot.visible) === JSON.stringify(["0"]), `mobile previous navigation failed: ${JSON.stringify(previousSlot)}`);
    assert(!pageErrors.length, `page errors: ${pageErrors.join(" | ")}`);
    console.log(JSON.stringify({ status: "PASS", checks: ["mobile active slot", "tablet multi-card", "shared editor full fields", "progression add/rename/switch", "progression bank association", "progression reorder/delete", "invalid progression rejection", "plus add", "pointer reorder states", "touch reorder states", "delete cancel/confirm", "codec roundtrip", "slot isolation", "mobile slot navigation"], finalExerciseNames: deleted.exercises.map(ex => ex.name), codeChars: roundtrip.codeChars }, null, 2));
  } finally {
    await context.close();
    await browser.close();
  }
})().catch(error => { console.error(error.stack || error); process.exitCode = 1; });
