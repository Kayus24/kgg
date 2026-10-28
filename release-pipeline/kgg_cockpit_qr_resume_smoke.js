#!/usr/bin/env node
"use strict";

// Catches scan imports that lose plan identity, overwrite a therapist's edited
// cell/note, or restore stale values when an earlier activation link is opened.
// All patient names, notes and training values below are synthetic fixtures.
const assert = require("assert/strict");
const fs = require("fs");
const path = require("path");
const { pathToFileURL } = require("url");
const { chromium } = require("playwright");

const ROOT = path.resolve(__dirname, "..");
const HTML_URL = pathToFileURL(path.join(ROOT, "kgg-update", "index.html")).href;
const OUTPUT = path.join(ROOT, "tmp", "cockpit-qr-resume");
const DAY = "2026-10-26";
const PLAN_A = "synthetic-qr-resume-a";
const PLAN_B = "synthetic-qr-resume-b";
const PLAN_C = "synthetic-qr-resume-c";
const MANUAL_NOTES = "Synthetische Therapienotiz: Pause nach Satz 2.";

function qrCode(prefix, payload) {
  return prefix + ":" + Buffer.from(JSON.stringify(payload), "utf8").toString("base64url");
}

function fullPlan(planId, name = "Synthetischer QR Patient") {
  return qrCode("KGGH2", {
    v: 2, i: planId, d: 6,
    patient: { name, date: DAY },
    e: [["Abduktion", 2, "BI", "kg", "Wdh", "10", "8"]],
  });
}

function returnedPlan(planId, values = [["15", "9"], ["16", "10"]]) {
  return qrCode("KGGD1", {
    v: 1, i: planId, d: DAY,
    e: [["Abduktion", 2, "BI", "kg", "Wdh", values, "0"]],
  });
}

// Saved links use the public therapist URL. Keep the same payload while running
// the repository artifact locally, with stable localStorage origin semantics.
function localLink(link) {
  const source = new URL(link);
  const code = source.searchParams.get("cockpit") || source.searchParams.get("kggtc") || source.hash.slice(1);
  assert.match(code || "", /^KGGTC1:/, "saved link must contain a portable Cockpit code");
  const target = new URL(HTML_URL);
  target.searchParams.set("cockpit", code);
  return target.href;
}

async function makePage(browser, contextOptions = {}) {
  const context = await browser.newContext({
    viewport: { width: 1280, height: 900 }, locale: "de-DE",
    hasTouch: true, serviceWorkers: "block",
    ...contextOptions,
  });
  await context.route(/^https?:\/\//, route => route.fulfill({ status: 204, body: "" }));
  await context.addInitScript(() => {
    localStorage.setItem("kgg_pwa_install_prompt_seen_v1", "2026-10-26T00:00:00.000Z");
  });
  const page = await context.newPage();
  page.setDefaultTimeout(10000);
  const errors = [];
  page.on("pageerror", error => errors.push(error.message));
  return { context, page, errors };
}

async function open(page, href = HTML_URL) {
  await page.goto(href, { waitUntil: "domcontentloaded", timeout: 30000 });
  await page.waitForFunction(() => !!window.KGGScan && !!window.KGGTherapyCockpit);
  // Fresh admin contexts intentionally have no real API key. Their existing
  // 700ms setup prompt is unrelated to this QR flow; dismiss it before typing.
  await page.waitForSelector("#adminSecretsModal.open", { state: "attached" });
  await page.locator("#closeAdminSecrets").evaluate(button => button.click());
}

async function scan(page, raw) {
  return page.evaluate(async value => {
    const accepted = await window.KGGScan.handleQrRaw(value, "synthetic-qr-resume-test");
    const jobs = window.scanJobsState || [];
    const latest = jobs[jobs.length - 1];
    return { accepted, cockpit: latest?.result?.cockpit || null };
  }, raw);
}

async function slot(page, index) {
  return page.evaluate(value => window.KGGTherapyCockpit.getSlot(value), index);
}

async function cockpitSnapshot(page) {
  return page.evaluate(() => ({
    slots: Array.from({ length: window.KGGTherapyCockpit.maxSlots }, (_, index) => window.KGGTherapyCockpit.getSlot(index)),
    plan: window.KGGDataStore.getCurrentPlan(),
  }));
}

async function closeOutput(page) {
  if (await page.locator("#kggTherapyCockpitOutputModal").isVisible()) {
    await page.locator('[data-tc-action="output-close"]').click();
  }
}

async function screenshot(page, name) {
  await page.screenshot({ path: path.join(OUTPUT, name + ".png"), fullPage: true });
}

async function setLoadWithNumpad(page, value, setIndex = 0) {
  const field = page.locator('[data-tc-action="input"][data-tc-slot="0"][data-tc-ex="0"][data-tc-set="' + setIndex + '"][data-tc-field="load"]');
  if (!(await field.count())) {
    await page.locator('[data-tc-action="toggle"][data-tc-slot="0"][data-tc-ex="0"]').click();
  }
  await field.click();
  for (const key of ["C", ...String(value), "OK"]) {
    await page.locator('[data-tc-action="key"][data-tc-slot="0"][data-tc-key="' + key + '"]').click();
  }
}

async function verifyIndependentPortableEdits(browser) {
  const older = await makePage(browser);
  const newer = await makePage(browser);
  try {
    await open(older.page);
    const initial = await scan(older.page, fullPlan("synthetic-portable-union", "Synthetischer Portabler Plan"));
    await closeOutput(older.page);
    await older.page.evaluate(() => window.KGGTherapyCockpit.open());
    await setLoadWithNumpad(older.page, "25");
    await older.page.locator('textarea[data-tc-notes]').first().fill("Synthetische aeltere Notiz");
    await older.page.locator('textarea[data-tc-notes]').first().blur();
    const olderLink = await older.page.evaluate(() => window.KGGTherapyCockpit.makeLink(window.KGGTherapyCockpit.getSlot(0)));
    const olderTime = (await slot(older.page, 0)).editedAt;

    await open(newer.page, localLink(initial.cockpit.link));
    await setLoadWithNumpad(newer.page, "19", 1);
    assert.ok((await slot(newer.page, 0)).editedAt > olderTime, "independent second-cell edit must be newer for the portable-link conflict test");
    let newerLink = await newer.page.evaluate(() => window.KGGTherapyCockpit.makeLink(window.KGGTherapyCockpit.getSlot(0)));
    await open(older.page, localLink(newerLink));
    let combined = await slot(older.page, 0);
    assert.deepEqual(combined.exercises[0].today, [["25", "8"], ["19", "8"]], "newer portable link must retain independent older manual cells");
    assert.equal(combined.notes, "Synthetische aeltere Notiz", "newer link without manual notes must retain the older therapist note");

    await setLoadWithNumpad(newer.page, "30");
    await newer.page.locator('textarea[data-tc-notes]').first().fill("Synthetische neuere Notiz");
    await newer.page.locator('textarea[data-tc-notes]').first().blur();
    newerLink = await newer.page.evaluate(() => window.KGGTherapyCockpit.makeLink(window.KGGTherapyCockpit.getSlot(0)));
    await open(older.page, localLink(newerLink));
    combined = await slot(older.page, 0);
    assert.deepEqual(combined.exercises[0].today, [["30", "8"], ["19", "8"]], "when both portable links manually edit the same cell, the newer edit must win");
    assert.equal(combined.notes, "Synthetische neuere Notiz", "when both links manually edit notes, the newer note must win");
    await older.page.evaluate(link => window.KGGTherapyCockpit.importCode(link), olderLink);
    assert.equal(await older.page.evaluate(() => window.KGGTherapyCockpit.getState().slotCount), 1, "opening an older link after portable merge must reuse the same slot");
    assert.deepEqual((await slot(older.page, 0)).exercises[0].today, [["30", "8"], ["19", "8"]], "an older portable link must not undo a newer manual-cell conflict resolution");
    await screenshot(older.page, "11-independent-portable-edit-union");
    assert.deepEqual(older.errors, [], "portable union must not raise page errors");
    assert.deepEqual(newer.errors, [], "independent portable editing must not raise page errors");
  } finally {
    await older.context.close();
    await newer.context.close();
  }
}

async function verifyPhoneActivationSelectsScannedPatient(browser) {
  const phone = await makePage(browser, {
    viewport: { width: 390, height: 844 }, screen: { width: 390, height: 844 },
    isMobile: true, deviceScaleFactor: 1,
  });
  try {
    const { page } = phone;
    await open(page);
    const first = await scan(page, fullPlan("synthetic-phone-qr-a", "Synthetischer Handy A"));
    assert.equal(first.cockpit?.slot, 0, "first phone scan must occupy slot zero");
    assert.equal(await page.evaluate(() => window.KGGTherapyCockpit.getState().view), "normal", "phone QR scan must not switch into the Cockpit");
    assert.equal(await page.locator("#kggTherapyCockpitOutputModal").isVisible(), false, "phone QR scan must not open a Cockpit modal");
    await page.evaluate(() => { window.KGGTherapyCockpit.open(); window.KGGTherapyCockpit.selectSlot(0); });
    await page.waitForSelector('.kgg-tce-active-card[data-tc-card="0"]');
    const second = await scan(page, fullPlan("synthetic-phone-qr-b", "Synthetischer Handy B"));
    assert.equal(second.cockpit?.slot, 1, "second phone scan must occupy slot one");
    await page.evaluate(() => window.KGGTherapyCockpit.selectSlot(1));
    const activeCard = page.locator('.kgg-tce-active-card[data-tc-card="1"]');
    await activeCard.waitFor({ state: "visible" });
    assert.equal(await page.locator(".kgg-tce-active-card").count(), 1, "phone must display one active patient card");
    assert.equal(await activeCard.locator(".kgg-tc-card-title strong").innerText(), "Synthetischer Handy B", "activation must select the newly scanned patient's card");
    const notes = activeCard.locator('textarea[data-tc-notes="1"]');
    assert.equal(await notes.isVisible(), true, "newly scanned patient's notes must be reachable on phone");
    await notes.fill("Synthetische Handy-B-Notiz");
    await notes.blur();
    assert.equal((await slot(page, 1)).notes, "Synthetische Handy-B-Notiz", "phone notes must belong to the scanned patient");
    assert.equal((await slot(page, 0)).notes, "", "editing the second phone patient must not alter the first patient's notes");
    // Mobile Chromium can still be settling the visual viewport after textarea blur.
    // Require the real active card to fit before taking the final geometry sample.
    // Persistent overflow remains a failure rather than widening the tolerance.
    await page.waitForFunction(() => {
      const card = document.querySelector('.kgg-tce-active-card[data-tc-card="1"]');
      if (!card) return false;
      const rect = card.getBoundingClientRect();
      return document.documentElement.scrollWidth <= innerWidth + 1 &&
        document.body.scrollWidth <= innerWidth + 1 &&
        rect.left >= -1 && rect.right <= innerWidth + 1;
    }, null, { timeout: 4000, polling: "raf" });
    const geometry = await activeCard.evaluate(card => {
      const rect = card.getBoundingClientRect();
      return { viewport: innerWidth, documentWidth: document.documentElement.scrollWidth, bodyWidth: document.body.scrollWidth, left: rect.left, right: rect.right };
    });
    assert.ok(geometry.documentWidth <= geometry.viewport + 1 && geometry.bodyWidth <= geometry.viewport + 1 && geometry.left >= -1 && geometry.right <= geometry.viewport + 1, "phone activation must not introduce horizontal overflow: " + JSON.stringify(geometry));
    await screenshot(page, "12-phone-second-patient-activation");
    assert.deepEqual(phone.errors, [], "phone activation must not raise page errors");
  } catch (error) {
    await screenshot(phone.page, "phone-activation-failure").catch(() => {});
    throw error;
  } finally {
    await phone.context.close();
  }
}

async function verifyCustomLeftRightPortableLink(browser) {
  const source = await makePage(browser);
  const portable = await makePage(browser);
  const sideNames = ["Synthetische Seitzug-Uebung (links)", "Synthetische Seitzug-Uebung (rechts)"];
  const initialValues = [[["15", "9"], ["16", "10"]], [["18", "11"], ["19", "12"]]];
  try {
    await open(source.page);
    const imported = await scan(source.page, qrCode("KGGD1", {
      v: 1, i: "synthetic-custom-lr-portable", d: DAY,
      e: [["Synthetische Seitzug-Uebung", 2, "LR", "kg", "Wdh", [["15", "9", "18", "11"], ["16", "10", "19", "12"]], "0"]],
    }));
    assert.equal(imported.cockpit?.slot, 0, "custom left/right return QR must activate a Cockpit slot");
    const initial = await slot(source.page, 0);
    assert.deepEqual(initial.exercises.map(exercise => exercise.name), sideNames, "left/right return QR must create explicitly labelled side exercises");
    assert.deepEqual(initial.exercises.map(exercise => exercise.today), initialValues, "left/right import must preserve all four values of both sets");
    const sourceIds = initial.exercises.map(exercise => exercise.id);
    assert.notEqual(sourceIds[0], sourceIds[1], "derived side exercises must have separate identities");
    await closeOutput(source.page);
    await source.page.evaluate(() => window.KGGTherapyCockpit.open());
    await setLoadWithNumpad(source.page, "25");
    await source.page.locator('[data-tc-action="finish"][data-tc-slot="0"]').click();
    await source.page.waitForSelector("#kggTherapyCockpitOutputModal:not([hidden])");
    const documentation = await source.page.locator("#kggTherapyCockpitOutput").inputValue();
    const finishLink = documentation.match(/https?:\/\/[^\s]+[?&]cockpit=[^\s]+/)?.[0];
    assert.ok(finishLink, "custom left/right plan must export a portable finish link");

    await open(portable.page);
    const beforeImport = await portable.page.evaluate(names => names.map(name => window.KGGTherapyCockpit.registry.lookup(name)), sideNames);
    assert.deepEqual(beforeImport, [null, null], "fresh context must not already know the custom side exercises");
    await open(portable.page, localLink(imported.cockpit.link));
    const activationRestored = await slot(portable.page, 0);
    assert.deepEqual(activationRestored.exercises.map(exercise => exercise.id), sourceIds, "old activation link must reconstruct the derived side IDs in a fresh registry");
    assert.deepEqual(activationRestored.exercises.map(exercise => exercise.today), initialValues, "old activation link must restore both original sides and all set values");
    await open(portable.page, localLink(finishLink));
    const finishRestored = await slot(portable.page, 0);
    assert.deepEqual(finishRestored.exercises.map(exercise => exercise.id), sourceIds, "new finish link must retain stable derived IDs after a fresh document load");
    assert.deepEqual(finishRestored.exercises.map(exercise => exercise.name), sideNames, "new finish link must retain explicit left/right labels");
    assert.deepEqual(finishRestored.exercises.map(exercise => exercise.today), [[["25", "9"], ["16", "10"]], [["18", "11"], ["19", "12"]]], "new finish link must restore the manual left edit while preserving every right-side value");
    assert.deepEqual(finishRestored.exercises.map(exercise => exercise.previous), [[["25", "9"], ["16", "10"]], [["18", "11"], ["19", "12"]]], "left/right finish link must promote both sides to the next previous values");
    const labels = portable.page.locator('.kgg-tc-card[data-tc-card="0"] .kgg-tc-exercise-summary strong');
    const summaries = portable.page.locator('.kgg-tc-card[data-tc-card="0"] .kgg-tc-exercise-summary small');
    assert.equal(await labels.nth(0).isVisible(), true, "left-side exercise title must be rendered visibly");
    assert.equal(await labels.nth(1).isVisible(), true, "right-side exercise title must be rendered visibly");
    assert.match(await labels.nth(0).innerText(), /^links · /, "left-side label must precede the long exercise name so truncation cannot hide it");
    assert.match(await labels.nth(1).innerText(), /^rechts · /, "right-side label must precede the long exercise name so truncation cannot hide it");
    assert.match(await summaries.nth(0).innerText(), /^2 Sätze · links(?: ·|$)/, "left-side summary must identify the side instead of calling it bilateral");
    assert.match(await summaries.nth(1).innerText(), /^2 Sätze · rechts(?: ·|$)/, "right-side summary must identify the side instead of calling it bilateral");
    await portable.page.locator('[data-tc-action="toggle"][data-tc-slot="0"][data-tc-ex="1"]').click();
    await screenshot(portable.page, "13-custom-left-right-derived-portable-link");
    assert.deepEqual(source.errors, [], "custom left/right import and finish must not raise page errors");
    assert.deepEqual(portable.errors, [], "fresh derived-registry import must not raise page errors");
  } catch (error) {
    await screenshot(portable.page, "custom-left-right-failure").catch(() => {});
    throw error;
  } finally {
    await source.context.close();
    await portable.context.close();
  }
}

async function main() {
  fs.mkdirSync(OUTPUT, { recursive: true });
  const browser = await chromium.launch({ headless: true });
  const original = await makePage(browser);
  let portable = null;
  let storageCase = null;
  let storagePortable = null;
  let phase = "initial patient scan";
  try {
    const { page } = original;
    await open(page);
    const first = await scan(page, fullPlan(PLAN_A));
    assert.equal(first.accepted?.accepted, true, "valid full-plan QR must be accepted by the real scanner");
    assert.ok(first.cockpit?.link, "successful patient QR scan must attach job.result.cockpit with an activation link");
    assert.equal(first.cockpit.slot, 0, "first scanned plan must occupy the first slot");
    const activationLink = first.cockpit.link;
    assert.equal(await page.evaluate(() => window.KGGTherapyCockpit.getState().view), "normal", "QR scan must not automatically open the Cockpit");
    assert.equal(await page.locator("#kggTherapyCockpitOutputModal").isVisible(), false, "QR scan must not interrupt the normal scan workflow with a modal");
    assert.equal(await page.evaluate(() => document.body.classList.contains("kggTherapyCockpitOpen")), false, "normal therapist view must remain visible");
    assert.equal(new URL(activationLink).pathname, "/kgg/kgg-update/index.html", "generated link must match the native app's allowed deep-link path");
    assert.match(new URL(activationLink).searchParams.get("cockpit") || "", /^KGGTC1:z/, "automatic Cockpit link must be compressed");
    const codecCompatibility = await page.evaluate(link => {
      const code = new URL(link).searchParams.get("cockpit");
      const url64 = code.slice("KGGTC1:z".length);
      const base64 = url64.replace(/-/g, "+").replace(/_/g, "/");
      const packed = Uint8Array.from(atob(base64), char => char.charCodeAt(0));
      const originalBytes = window.fflate.inflateSync(packed);
      let binary = "";
      for (const byte of originalBytes) binary += String.fromCharCode(byte);
      const oldCode = "KGGTC1:" + btoa(binary).replace(/\+/g, "-").replace(/\//g, "_").replace(/=+$/, "");
      return {
        oldId: window.KGGTherapyCockpit.decode(oldCode).planId,
        newId: window.KGGTherapyCockpit.decode(code).planId,
        oldChars: oldCode.length, newChars: code.length,
      };
    }, activationLink);
    assert.equal(codecCompatibility.oldId, PLAN_A, "legacy uncompressed links must remain readable");
    assert.equal(codecCompatibility.newId, PLAN_A, "compressed links must decode to the same plan");
    assert.ok(codecCompatibility.newChars < codecCompatibility.oldChars, "compressed code must be shorter than the legacy code");
    const scanText = await page.locator("#kggScanInboxField0").inputValue();
    assert.equal(scanText.endsWith("Cockpit-Link:\n" + activationLink), true, "normal scan result text must end with the Cockpit link");
    assert.ok(scanText.includes("Abduktion"), "scan result must still contain the usual patient exercise text");
    assert.equal((await slot(page, 0)).planId, PLAN_A, "scan must retain the QR plan identity");
    await screenshot(page, "01-scan-activation-link");

    phase = "visible therapist edits";
    await open(page, localLink(activationLink));
    await closeOutput(page);
    await setLoadWithNumpad(page, "25");
    assert.equal((await slot(page, 0)).exercises[0].today[0][0], "25", "visible numpad must edit the first load cell");
    const notes = page.locator('textarea[data-tc-notes]').first();
    assert.equal(await notes.isVisible(), true, "therapist notes must be editable in the scanned slot");
    await notes.fill(MANUAL_NOTES);
    await notes.blur();
    await page.waitForFunction(value => window.KGGTherapyCockpit.getSlot(0)?.notes === value, MANUAL_NOTES);
    await screenshot(page, "02-manual-load-and-notes");

    phase = "finish link export";
    await page.locator('[data-tc-action="finish"][data-tc-slot="0"]').click();
    await page.waitForSelector("#kggTherapyCockpitOutputModal:not([hidden])");
    const output = await page.locator("#kggTherapyCockpitOutput").inputValue();
    const exportedLink = output.match(/https?:\/\/[^\s]+[?&]cockpit=[^\s]+/)?.[0];
    assert.ok(exportedLink, "finish documentation must include the reusable Cockpit link");
    assert.ok(output.includes(MANUAL_NOTES), "finish documentation must retain therapist notes");
    assert.ok(output.startsWith("Abduktion\nS1: "), "documentation must start directly with the first exercise and sets");
    assert.ok(!output.includes("KGG Therapie-Cockpit") && !output.includes("Patient: ") && !output.includes("Plan fertig"), "documentation must omit heading, patient placeholder, and completion preamble");
    assert.ok(!output.includes("Planquelle nicht übernommen"), "technical plan-source status must never pollute copied patient documentation");
    assert.ok(output.trimEnd().endsWith("Neuer Cockpit-Link:\n" + exportedLink), "portable Cockpit link must be the final documentation line");
    const transferWarning = await page.locator("#kggTherapyCockpitOutputModal p").innerText();
    assert.match(transferWarning, /Planquelle nicht übernommen/i, "failed plan-source transfer must remain clearly visible in the app, outside copied text");
    await screenshot(page, "03-finish-documentation");

    phase = "old activation link and fresh return scan";
    await open(page, localLink(activationLink));
    let resumed = await slot(page, 0);
    assert.equal(resumed.exercises[0].today[0][0], "25", "an old activation link must not reset a locally edited load");
    assert.equal(resumed.exercises[0].previous[0][0], "25", "finishing must promote today's load to the local resume baseline");
    assert.equal(resumed.notes, MANUAL_NOTES, "an old activation link must not reset locally edited notes");
    const second = await scan(page, returnedPlan(PLAN_A));
    assert.equal(second.cockpit?.slot, 0, "return QR must reuse the same plan slot");
    resumed = await slot(page, 0);
    assert.deepEqual(resumed.exercises[0].today, [["25", "9"], ["16", "10"]], "manual first load must win while untouched loads and metrics follow the fresh QR");
    assert.equal(resumed.notes, MANUAL_NOTES, "return QR must retain therapist notes");
    assert.equal(await page.evaluate(() => window.KGGTherapyCockpit.getState().slotCount), 1, "repeat scanning must not duplicate the patient slot");
    await screenshot(page, "04-old-link-resumed-and-return-merged");
    await closeOutput(page);

    phase = "portable finish link in a fresh browser context";
    portable = await makePage(browser);
    await open(portable.page, localLink(exportedLink));
    const restored = await slot(portable.page, 0);
    assert.equal(restored.exercises[0].today[0][0], "25", "portable finish link must restore the edited load without local history");
    assert.equal(restored.notes, MANUAL_NOTES, "portable finish link must restore notes without local history");
    await scan(portable.page, returnedPlan(PLAN_A));
    const restoredMerged = await slot(portable.page, 0);
    assert.deepEqual(restoredMerged.exercises[0].today, [["25", "9"], ["16", "10"]], "portable manual-cell markers must survive a later return scan");
    assert.equal(restoredMerged.notes, MANUAL_NOTES, "portable manual-note priority must survive a later return scan");
    await screenshot(portable.page, "05-portable-link-fresh-context");

    phase = "different plan identity and three occupied slots";
    const beforeOther = await slot(page, 0);
    const other = await scan(page, fullPlan(PLAN_B));
    assert.equal(other.cockpit?.slot, 1, "different plan ID with the same patient name must use a different slot");
    assert.deepEqual(await slot(page, 0), beforeOther, "another plan's QR must not mutate the edited plan");
    await closeOutput(page);
    const third = await scan(page, fullPlan(PLAN_C, "Synthetischer Dritter"));
    assert.equal(third.cockpit?.slot, 2, "third plan must fill the remaining slot");
    const slotB = await slot(page, 1);
    const slotC = await slot(page, 2);
    await closeOutput(page);
    const fullRepeat = await scan(page, returnedPlan(PLAN_A, [["19", "11"], ["20", "12"]]));
    assert.equal(fullRepeat.cockpit?.slot, 0, "same plan must reuse its slot even when all three slots are occupied");
    assert.equal(await page.evaluate(() => window.KGGTherapyCockpit.getState().slotCount), 3, "same-plan refresh must preserve three occupied slots");
    assert.deepEqual((await slot(page, 0)).exercises[0].today, [["25", "11"], ["20", "12"]], "full-slot refresh must keep manual priority and update untouched cells");
    assert.deepEqual(await slot(page, 1), slotB, "same-plan refresh must isolate the second patient");
    assert.deepEqual(await slot(page, 2), slotC, "same-plan refresh must isolate the third patient");
    const repeatedLink = await page.evaluate(link => window.KGGTherapyCockpit.importCode(link), fullRepeat.cockpit.link);
    assert.equal(repeatedLink.slot, 0, "reopening a link for an occupied exact plan ID must reuse its slot");
    assert.equal(await page.evaluate(() => window.KGGTherapyCockpit.getState().slotCount), 3, "same-link reuse must work with all three slots full");
    const partial = await scan(page, returnedPlan(PLAN_A, [["", ""], ["", "13"]]));
    assert.equal(partial.cockpit?.slot, 0, "partial return QR must retain the existing plan slot");
    assert.deepEqual((await slot(page, 0)).exercises[0].today, [["25", "11"], ["20", "13"]], "blank incoming QR cells must supplement existing values instead of clearing them");
    await screenshot(page, "06-three-slots-same-plan-refresh");
    await closeOutput(page);

    phase = "missing identity and malformed QR rejection";
    const beforeInvalid = await cockpitSnapshot(page);
    await scan(page, fullPlan(""));
    assert.deepEqual(await cockpitSnapshot(page), beforeInvalid, "QR without stable plan ID must not change Cockpit or currentPlan");
    const rejected = await scan(page, "not-a-kgg-code");
    assert.equal(rejected.accepted?.type, "invalidQr", "malformed QR must be rejected by the real scanner");
    assert.deepEqual(await cockpitSnapshot(page), beforeInvalid, "invalid QR must not mutate Cockpit or currentPlan");
    const noId = await page.evaluate(() => {
      try {
        window.KGGTherapyCockpit.importPatientPlan({ planId: "", name: "Synthetisch ohne ID", exercises: [{ name: "Abduktion", sets: 2 }] });
        return false;
      } catch (error) { return true; }
    });
    assert.equal(noId, true, "direct patient-plan import must fail closed without a plan ID");
    assert.deepEqual(await cockpitSnapshot(page), beforeInvalid, "rejected direct import must leave state unchanged");

    phase = "independent portable manual edits";
    await verifyIndependentPortableEdits(browser);

    phase = "phone activation selects newly scanned patient";
    await verifyPhoneActivationSelectsScannedPatient(browser);

    phase = "custom left/right portable registry restore";
    await verifyCustomLeftRightPortableLink(browser);

    phase = "visible persistence warning and portable recovery";
    storageCase = await makePage(browser);
    const storagePage = storageCase.page;
    await open(storagePage);
    const storageImport = await scan(storagePage, fullPlan("synthetic-qr-storage-failure", "Synthetischer Speicherpatient"));
    assert.equal(storageImport.cockpit?.slot, 0, "storage scenario must start with a successfully imported plan");
    await closeOutput(storagePage);
    await storagePage.evaluate(() => window.KGGTherapyCockpit.open());
    await storagePage.evaluate(() => {
      const originalSetItem = Storage.prototype.setItem;
      Storage.prototype.setItem = function (key, value) {
        if (String(key).startsWith("kgg_cockpit_resume_v1:")) {
          throw new DOMException("Synthetic storage quota failure", "QuotaExceededError");
        }
        return originalSetItem.call(this, key, value);
      };
    });
    await setLoadWithNumpad(storagePage, "35");
    const storageNotes = "Synthetische Notiz trotz Speicherfehler.";
    await storagePage.locator('textarea[data-tc-notes]').first().fill(storageNotes);
    await storagePage.locator('textarea[data-tc-notes]').first().blur();
    await storagePage.waitForFunction(value => window.KGGTherapyCockpit.getSlot(0)?.notes === value, storageNotes);
    const persistenceStatus = storagePage.locator("#kggTherapyCockpitStatus");
    assert.equal(await persistenceStatus.isVisible(), true, "storage failure warning must remain visible during edits");
    const warning = await persistenceStatus.innerText();
    assert.match(warning, /nicht.*gespeichert/i, "later storage failure must explicitly say that edits were not saved");
    assert.match(warning, /(?:neuen|aktuellen|neuesten).*link|link.*(?:neu|aktuell)/i, "warning must identify the new current link as the recovery path");
    assert.match(warning, /speichern/i, "warning must instruct the therapist to save that link");
    await screenshot(storagePage, "09-storage-failure-visible-warning");
    await storagePage.locator('[data-tc-action="finish"][data-tc-slot="0"]').click();
    await storagePage.waitForSelector("#kggTherapyCockpitOutputModal:not([hidden])");
    const storageOutput = await storagePage.locator("#kggTherapyCockpitOutput").inputValue();
    const recoveryLink = storageOutput.match(/https?:\/\/[^\s]+[?&]cockpit=[^\s]+/)?.[0];
    assert.ok(recoveryLink, "failed local saving must still allow exporting the latest portable link");
    storagePortable = await makePage(browser);
    await open(storagePortable.page, localLink(recoveryLink));
    const recovered = await slot(storagePortable.page, 0);
    assert.equal(recovered.exercises[0].today[0][0], "35", "new portable link must recover a manual load despite failed local saving");
    assert.equal(recovered.notes, storageNotes, "new portable link must recover notes despite failed local saving");
    assert.equal(recovered.exercises[0].previous[0][0], "35", "finish export must promote today's load to previous even when local saving fails");
    await screenshot(storagePortable.page, "10-storage-failure-portable-recovery");
    assert.deepEqual(original.errors, [], "primary browser flow must not raise page errors");
    assert.deepEqual(portable.errors, [], "fresh-context portable flow must not raise page errors");
    assert.deepEqual(storageCase.errors, [], "storage failure must be handled without uncaught page errors");
    assert.deepEqual(storagePortable.errors, [], "portable recovery must not raise page errors");
    const result = {
      status: "PASS", checks: ["real KGGH2/KGGD1 scanner", "scan text and compact link without auto-open", "visible numpad edit", "manual notes", "old link resume", "finish promotes today to previous", "fresh QR merge per cell", "portable finish link and priority", "independent portable manual-cell union and newer conflicts", "same-name plan isolation", "same-plan QR and link reuse at three slots", "partial blank QR supplements values", "missing identity and invalid QR are side-effect free", "phone activation selects scanned patient without overflow", "custom left/right values and derived registry survive old and new portable links", "visible storage failure warning", "portable recovery without local saving"],
      screenshots: path.relative(ROOT, OUTPUT),
    };
    fs.writeFileSync(path.join(OUTPUT, "result.json"), JSON.stringify(result, null, 2) + "\n");
    console.log(JSON.stringify(result, null, 2));
  } catch (error) {
    await screenshot(original.page, "failure").catch(() => {});
    const failure = { status: "FAIL", phase, message: error.message };
    fs.writeFileSync(path.join(OUTPUT, "result.json"), JSON.stringify(failure, null, 2) + "\n");
    throw new Error(phase + ": " + error.message, { cause: error });
  } finally {
    await original.context.close();
    if (portable) await portable.context.close();
    if (storageCase) await storageCase.context.close();
    if (storagePortable) await storagePortable.context.close();
    await browser.close();
  }
}

main().catch(error => { console.error(error.stack || error); process.exitCode = 1; });
