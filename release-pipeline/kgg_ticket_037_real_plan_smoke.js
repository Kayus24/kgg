#!/usr/bin/env node
"use strict";

const path = require("path");
const { pathToFileURL } = require("url");
const { chromium } = require("playwright");

const ROOT = path.resolve(__dirname, "..");
const HTML_URL = pathToFileURL(path.join(ROOT, "kgg-update", "index.html")).href;
const PATIENT = "KGG Ticket 037 Testpatient";
const CANONICAL_APP_BLUE = "rgb(237, 245, 255)";
const VISIBILITY_CASES = [
  { id: "tablet-820", width: 820, height: 1180, mobile: false, cockpitButtonVisible: true },
  { id: "tablet-1024", width: 1024, height: 768, mobile: false, cockpitButtonVisible: true },
  { id: "tablet-1280", width: 1280, height: 800, mobile: false, cockpitButtonVisible: true },
  { id: "phone-390", width: 390, height: 844, mobile: true, cockpitButtonVisible: false },
  { id: "breakpoint-759", width: 759, height: 900, mobile: false, cockpitButtonVisible: false },
  { id: "breakpoint-760", width: 760, height: 900, mobile: false, cockpitButtonVisible: true },
];
const FLOW_CASES = VISIBILITY_CASES.filter(test => test.cockpitButtonVisible);

function assert(value, message) {
  if (!value) throw new Error(message);
}

function viewportOf(test) {
  return { width: test.width, height: test.height };
}

async function visible(locator) {
  return locator.isVisible().catch(() => false);
}

async function boot(browser, test) {
  const context = await browser.newContext({
    viewport: viewportOf(test),
    deviceScaleFactor: 1,
    hasTouch: true,
    isMobile: test.mobile,
    locale: "de-DE",
  });
  const page = await context.newPage();
  await page.addInitScript(() => {
    localStorage.setItem("kgg_pwa_install_prompt_seen_v1", "ticket-037");
  });
  await page.goto(HTML_URL, { waitUntil: "domcontentloaded", timeout: 30000 });
  await page.waitForSelector("#kggTherapyCockpitButton", { state: "attached", timeout: 15000 });
  await closeAllowedAdminModal(page);
  return { context, page };
}

async function addExerciseFromVisibleUi(page, name, expectedCount) {
  const addButton = page.locator("button.bankAddBtn").filter({ hasText: name }).first();
  if (!(await visible(addButton))) {
    const bankToggle = page.locator("#bankToggle");
    const bankContent = page.locator("#bankContent");
    if (await visible(bankToggle) && await bankContent.isHidden().catch(() => false)) {
      await closeAllowedAdminModal(page);
      await bankToggle.click();
    }
  }
  await addButton.waitFor({ state: "visible", timeout: 5000 });
  await closeAllowedAdminModal(page);
  await addButton.click();
  await page.waitForFunction(expected => {
    const store = window.KGGDataStore;
    const plan = store && typeof store.getCurrentPlan === "function" ? store.getCurrentPlan() : null;
    return document.querySelectorAll("#planList .planCard").length === expected &&
      !!plan && Array.isArray(plan.exercises) && plan.exercises.length === expected;
  }, expectedCount, { timeout: 5000 });
}

async function readPlanContract(page) {
  return page.evaluate(() => {
    const currentPlan = window.KGGDataStore.getCurrentPlan();
    const api = window.KGGTherapyCockpit;
    return {
      plan: currentPlan,
      contentKey: api.contentKey(api.fromPlan(currentPlan)),
      exerciseNames: currentPlan.exercises.map(ex => ex.name),
    };
  });
}

async function createNormalPlan(page, exerciseNames) {
  await closeAllowedAdminModal(page);
  const baseFields = page.locator("#baseFields");
  if (await baseFields.isHidden().catch(() => false)) await page.locator("#baseToggle").click();
  await page.locator("#patientName").waitFor({ state: "visible", timeout: 5000 });
  await page.locator("#patientName").fill(PATIENT);
  for (let index = 0; index < exerciseNames.length; index += 1) {
    await addExerciseFromVisibleUi(page, exerciseNames[index], index + 1);
  }
  return readPlanContract(page);
}

async function closeAllowedAdminModal(page) {
  const modal = page.locator("#adminSecretsModal");
  for (let attempt = 0; attempt < 4; attempt += 1) {
    await page.waitForTimeout(attempt === 0 ? 900 : 250);
    if (await visible(modal)) {
      await modal.locator("#closeAdminSecrets").click();
      await modal.waitFor({ state: "hidden", timeout: 2000 });
    }
  }
}

async function waitForCockpitState(page, expectedCount) {
  await page.waitForFunction(expected => {
    const api = window.KGGTherapyCockpit;
    const state = api && api.getState ? api.getState() : null;
    return !!state && state.slotCount === expected && state.view === "cockpit" &&
      document.body.classList.contains("kggTherapyCockpitOpen");
  }, expectedCount, { timeout: 5000 });
}

async function waitForNormalState(page) {
  await page.waitForFunction(() => {
    const state = window.KGGTherapyCockpit.getState();
    return state.view === "normal" && !document.body.classList.contains("kggTherapyCockpitOpen");
  }, null, { timeout: 5000 });
}

async function readUiState(page) {
  return page.evaluate(() => {
    const toast = document.querySelector("#kggTherapyCockpitToast.show");
    const state = window.KGGTherapyCockpit.getState();
    state.renderedExerciseNames = Array.from(document.querySelectorAll("[data-tc-card]")).map(card =>
      Array.from(card.querySelectorAll(".kgg-tc-exercise-summary strong")).map(node => node.textContent.trim())
    );
    return {
      state,
      open: document.body.classList.contains("kggTherapyCockpitOpen"),
      errorCode: window.KGGTherapyCockpitLastErrorCode || "",
      toast: toast ? toast.textContent.trim() : "",
    };
  });
}

function assertSlotMatches(state, index, contract, message) {
  const slot = state.slots[index];
  assert(slot, `${message}: Slot ${index + 1} fehlt`);
  assert(slot.planId === contract.plan.id, `${message}: planId stimmt nicht`);
  assert(slot.contentKey === contract.contentKey, `${message}: contentKey stimmt nicht`);
  assert(slot.exerciseCount === contract.plan.exercises.length, `${message}: Übungsanzahl stimmt nicht`);
  assert(JSON.stringify(state.renderedExerciseNames[index]) === JSON.stringify(contract.exerciseNames), `${message}: konkrete Übungsidentitäten stimmen nicht`);
}

function assertNoPositiveError(result, message) {
  assert(result.errorCode !== "slots_full", `${message}: unerwarteter slots_full-Fehler`);
  assert(!result.toast, `${message}: unerwarteter Toast: ${result.toast}`);
}

async function openFinishDialog(page) {
  await closeAllowedAdminModal(page);
  await page.locator("#finishBtn").waitFor({ state: "visible", timeout: 5000 });
  await page.locator("#finishBtn").click();
  await page.locator("#shareModal.open").waitFor({ state: "visible", timeout: 5000 });
}

async function inspectFinishDialog(page) {
  return page.evaluate(() => {
    const visibleElement = element => {
      if (!element) return false;
      const style = getComputedStyle(element);
      const rect = element.getBoundingClientRect();
      return style.display !== "none" && style.visibility !== "hidden" && rect.width > 0 && rect.height > 0;
    };
    const choices = Array.from(document.querySelector("#finishChoices").children).map(el => el.id || el.className);
    const pdfRow = document.querySelector(".finishPdfRow");
    const cockpitRow = document.querySelector(".finishCockpitRow");
    const app = document.querySelector("#finishPatientBtn");
    const cockpitText = document.querySelector("#finishCockpitBtn");
    const cockpitGauge = document.querySelector("#finishCockpitGaugeBtn");
    const controlRects = ["finishPdfBtn", "finishLargePdfBtn", "finishPatientBtn", "finishCockpitBtn", "finishCockpitGaugeBtn", "finishCancelBtn"].reduce((rects, id) => {
      const element = document.querySelector(`#${id}`);
      if (element) {
        const rect = element.getBoundingClientRect();
        rects[id] = { left: rect.left, top: rect.top, right: rect.right, bottom: rect.bottom, width: rect.width, height: rect.height };
      }
      return rects;
    }, {});
    return {
      choices,
      pdfChildren: pdfRow ? Array.from(pdfRow.children).map(el => el.id) : [],
      cockpitChildren: cockpitRow ? Array.from(cockpitRow.children).map(el => el.id) : [],
      appVisible: visibleElement(app),
      appClass: app ? app.className : "",
      appBackground: app ? getComputedStyle(app).backgroundColor : "",
      pdfVisible: visibleElement(document.querySelector("#finishPdfBtn")),
      pdfLargeVisible: visibleElement(document.querySelector("#finishLargePdfBtn")),
      cockpitTextVisible: visibleElement(cockpitText),
      cockpitGaugeVisible: visibleElement(cockpitGauge),
      gaugeNestedInText: !!(cockpitText && cockpitText.querySelector(".finishGaugeIcon")),
      cockpitRowClass: cockpitRow ? cockpitRow.className : "",
      controlRects,
    };
  });
}

async function assertFinishFocusOrder(page) {
  const expected = [
    "finishPdfBtn",
    "finishLargePdfBtn",
    "finishPatientBtn",
    "finishCockpitBtn",
    "finishCockpitGaugeBtn",
    "finishCancelBtn",
  ];
  await page.waitForFunction(() => document.activeElement && document.activeElement.id === "finishPdfBtn", null, { timeout: 5000 });
  const actual = [await page.evaluate(() => document.activeElement.id)];
  for (let index = 1; index < expected.length; index += 1) {
    await page.keyboard.press("Tab");
    actual.push(await page.evaluate(() => document.activeElement.id));
  }
  assert(JSON.stringify(actual) === JSON.stringify(expected), `Finish-Tab-Fokusfolge falsch: ${JSON.stringify(actual)}`);
  return actual;
}

async function runVisibility(browser, test) {
  const { context, page } = await boot(browser, test);
  try {
    const setup = await createNormalPlan(page, ["Abduktion Maschine"]);
    assert(setup.plan.patient.name === PATIENT, `${test.id}: Matrix-UI-Plan wurde nicht angelegt`);
    const button = page.locator("#kggTherapyCockpitButton");
    const actual = await visible(button);
    assert(actual === test.cockpitButtonVisible, `${test.id}: Rootbutton-Sichtbarkeit ${actual}, erwartet ${test.cockpitButtonVisible}`);
    await openFinishDialog(page);
    const dialog = await inspectFinishDialog(page);
    const allFinishControlsVisible = dialog.pdfVisible && dialog.pdfLargeVisible && dialog.appVisible && dialog.cockpitTextVisible && dialog.cockpitGaugeVisible;
    assert(allFinishControlsVisible, `${test.id}: Finish-Steuerelemente sind nicht vollständig sichtbar`);
    const outsideViewport = Object.entries(dialog.controlRects).filter(([, rect]) => rect.left < 0 || rect.top < 0 || rect.right > test.width || rect.bottom > test.height || rect.width <= 0 || rect.height <= 0);
    assert(outsideViewport.length === 0, `${test.id}: Finish-Steuerelement liegt außerhalb des Viewports: ${outsideViewport.map(([id]) => id).join(", ")}`);
    assert(dialog.appBackground === CANONICAL_APP_BLUE, `${test.id}: Matrix-App-Button ist nicht exakt kanonisch blau: ${dialog.appBackground}`);
    await page.locator("#finishCancelBtn").click();
    await page.locator("#shareModal.open").waitFor({ state: "hidden", timeout: 5000 });
    return {
      id: test.id,
      width: test.width,
      height: test.height,
      expectedRootButton: test.cockpitButtonVisible,
      actualRootButton: actual,
      finishControlsVisible: allFinishControlsVisible,
      finishControlsWithinViewport: true,
    };
  } finally {
    await context.close();
  }
}

async function runCompleteVisibilityMatrix(browser) {
  const test = { id: "matrix-complete-1024", width: 1024, height: 768, mobile: false };
  const { context, page } = await boot(browser, test);
  const root = page.locator("#kggTherapyCockpitButton");
  const finish = page.locator("#finishBtn");
  const snapshot = async label => ({ label, cockpit: await visible(root), finish: await visible(finish) });
  try {
    const states = [await snapshot("0/0")];
    assert(!states[0].cockpit && !states[0].finish, "Matrix 0/0 ist nicht verborgen/verborgen");
    await createNormalPlan(page, ["Abduktion Maschine"]);
    states.push(await snapshot(">=1/0"));
    assert(states[1].cockpit && states[1].finish, "Matrix >=1/0 ist nicht sichtbar/sichtbar");
    await root.click();
    await waitForCockpitState(page, 1);
    await page.locator('[data-tc-action="normal"]').click();
    await waitForNormalState(page);
    states.push(await snapshot(">=1/>=1"));
    assert(states[2].cockpit && states[2].finish, "Matrix >=1/>=1 ist nicht sichtbar/sichtbar");
    await page.locator("#planList .planDeleteBtn").first().click();
    await page.waitForFunction(() => window.KGGDataStore.getCurrentPlan().exercises.length === 0);
    states.push(await snapshot("0/>=1"));
    assert(states[3].cockpit && !states[3].finish, "Matrix 0/>=1 ist nicht sichtbar/verborgen");
    return states;
  } finally {
    await context.close();
  }
}

async function runDirectMultiExercise(browser) {
  const test = { id: "direct-multi-1024", width: 1024, height: 768, mobile: false };
  const { context, page } = await boot(browser, test);
  try {
    const contract = await createNormalPlan(page, ["Abduktion Maschine", "Adduktion Maschine"]);
    assert(contract.plan.exercises.length === 2, "Mehrübungsplan wurde nicht über die normale UI aufgebaut");
    await page.locator("#kggTherapyCockpitButton").click();
    await waitForCockpitState(page, 1);
    const result = await readUiState(page);
    assert(result.state.slotCount === 1, "Direkter Mehrübungsimport erzeugte nicht genau Slot 1");
    assert(result.state.slots[0].name === PATIENT, "Direkter Mehrübungsimport verlor den Patientenbezug");
    assertSlotMatches(result.state, 0, contract, "Direkter Mehrübungsimport");
    assertNoPositiveError(result, "Direkter Mehrübungsimport");
    return { exerciseNames: contract.exerciseNames, slotCount: result.state.slotCount };
  } finally {
    await context.close();
  }
}

async function runPositive(browser, test) {
  const { context, page } = await boot(browser, test);
  try {
    const initial = await createNormalPlan(page, ["Abduktion Maschine"]);
    assert(initial.plan.patient.name === PATIENT, `${test.id}: UI setzte den Testpatienten nicht`);
    assert(initial.plan.exercises.length === 1, `${test.id}: initialer UI-Plan ist nicht genau eine Übung`);
    const initialState = await readUiState(page);
    assert(initialState.state.slotCount === 0, `${test.id}: positiver Test startet nicht mit null Slots`);

    const rootButton = page.locator("#kggTherapyCockpitButton");
    assert(await visible(rootButton), `${test.id}: sichtbarer Rootbutton fehlt`);
    await rootButton.dblclick({ delay: 25 });
    await waitForCockpitState(page, 1);
    let result = await readUiState(page);
    const slot1Contract = await readPlanContract(page);
    assert(result.state.slotCount === 1, `${test.id}: Root-Doppelklick erzeugte nicht genau Slot 1`);
    assert(result.state.slots.length === 3, `${test.id}: Cockpit-Slotstruktur ist nicht auf drei Slots begrenzt`);
    assert(result.state.slots[0].name === PATIENT, `${test.id}: Slot 1 verlor den Testpatienten`);
    assert(result.open, `${test.id}: Root-Doppelklick öffnete das Cockpit nicht`);
    assertSlotMatches(result.state, 0, slot1Contract, `${test.id}: Rootimport`);
    assertNoPositiveError(result, `${test.id}: Rootimport`);

    await page.locator('[data-tc-action="normal"]').click();
    await waitForNormalState(page);
    assert(await visible(rootButton), `${test.id}: Rootbutton ist nach Rückkehr nicht sichtbar`);
    await rootButton.click();
    await waitForCockpitState(page, 1);
    result = await readUiState(page);
    assert(result.state.slotCount === 1, `${test.id}: zweiter Root-Klick erzeugte einen weiteren Slot`);
    assertSlotMatches(result.state, 0, slot1Contract, `${test.id}: zweiter Root-Klick`);
    assertNoPositiveError(result, `${test.id}: zweiter Root-Klick`);

    await page.locator('[data-tc-action="normal"]').click();
    await waitForNormalState(page);
    await openFinishDialog(page);
    const dialog = await inspectFinishDialog(page);
    assert(JSON.stringify(dialog.choices) === JSON.stringify(["finishPdfRow", "finishPatientBtn", "finishCockpitRow", "finishCancelBtn"]), `${test.id}: Finish-DOM-Reihenfolge ist falsch`);
    assert(JSON.stringify(dialog.pdfChildren) === JSON.stringify(["finishPdfBtn", "finishLargePdfBtn"]), `${test.id}: PDF-Text/Brillenbutton sind nicht getrennt`);
    assert(JSON.stringify(dialog.cockpitChildren) === JSON.stringify(["finishCockpitBtn", "finishCockpitGaugeBtn"]), `${test.id}: Finish-Cockpit-Text/Gauge sind nicht getrennt`);
    assert(dialog.cockpitRowClass.split(/\s+/).includes("finishCockpitRow"), `${test.id}: finishCockpitRow fehlt`);
    assert(dialog.appVisible && dialog.appClass.split(/\s+/).includes("finishAppBtn"), `${test.id}: App-Button fehlt oder hat nicht die kanonische Klasse`);
    assert(dialog.appBackground === CANONICAL_APP_BLUE, `${test.id}: App-Button ist nicht exakt kanonisch blau: ${dialog.appBackground}`);
    assert(dialog.pdfVisible && dialog.pdfLargeVisible, `${test.id}: PDF-Text oder PDF-Brillenbutton fehlt`);
    assert(dialog.cockpitTextVisible && dialog.cockpitGaugeVisible && !dialog.gaugeNestedInText, `${test.id}: Cockpit-Text/Gauge sind nicht separat sichtbar`);
    const focusSequence = await assertFinishFocusOrder(page);
    await page.locator("#finishCancelBtn").click();
    await page.locator("#shareModal.open").waitFor({ state: "hidden", timeout: 5000 });

    await openFinishDialog(page);
    await page.locator("#finishCockpitBtn").click();
    await waitForCockpitState(page, 1);
    result = await readUiState(page);
    assert(result.state.slotCount === 1, `${test.id}: identischer Finish-Import dedupliziert nicht`);
    assertSlotMatches(result.state, 0, slot1Contract, `${test.id}: identischer Finish-Import`);
    assertNoPositiveError(result, `${test.id}: identischer Finish-Import`);

    await page.locator('[data-tc-action="normal"]').click();
    await waitForNormalState(page);
    const secondContractBefore = await readPlanContract(page);
    await addExerciseFromVisibleUi(page, "Adduktion Maschine", 2);
    const secondContract = await readPlanContract(page);
    assert(secondContract.plan.id === secondContractBefore.plan.id, `${test.id}: planId änderte sich trotz normaler UI-Änderung`);
    assert(secondContract.contentKey !== slot1Contract.contentKey, `${test.id}: UI-Änderung erzeugte keinen neuen contentKey`);
    await openFinishDialog(page);
    await page.locator("#finishCockpitBtn").click();
    await waitForCockpitState(page, 2);
    result = await readUiState(page);
    assert(result.state.slotCount === 2, `${test.id}: geänderter gleicher-planId-Import erzeugte nicht Slot 2`);
    assertSlotMatches(result.state, 0, slot1Contract, `${test.id}: Slot 1 nach Slot 2`);
    assertSlotMatches(result.state, 1, secondContract, `${test.id}: Slot 2`);
    assertNoPositiveError(result, `${test.id}: Slot-2-Import`);

    await page.locator('[data-tc-action="normal"]').click();
    await waitForNormalState(page);
    const thirdContractBefore = await readPlanContract(page);
    await addExerciseFromVisibleUi(page, "Beinpresse", 3);
    const thirdContract = await readPlanContract(page);
    assert(thirdContract.plan.id === thirdContractBefore.plan.id, `${test.id}: planId änderte sich vor Slot 3`);
    assert(thirdContract.contentKey !== secondContract.contentKey, `${test.id}: weiterer UI-Inhalt erzeugte keinen neuen contentKey`);
    await openFinishDialog(page);
    const gaugeButton = page.locator("#finishCockpitGaugeBtn");
    assert(await visible(gaugeButton), `${test.id}: separater Finish-Gaugebutton fehlt`);
    await gaugeButton.dblclick({ delay: 25 });
    await waitForCockpitState(page, 3);
    result = await readUiState(page);
    assert(result.state.slotCount === 3, `${test.id}: Gauge-Doppelklick erzeugte nicht genau Slot 3`);
    assert(result.state.slots.length === 3 && !result.state.slots[3], `${test.id}: Gauge-Doppelklick erzeugte Slot 4`);
    assertSlotMatches(result.state, 0, slot1Contract, `${test.id}: Slot 1 nach Slot 3`);
    assertSlotMatches(result.state, 1, secondContract, `${test.id}: Slot 2 nach Slot 3`);
    assertSlotMatches(result.state, 2, thirdContract, `${test.id}: Slot 3`);
    assert(result.errorCode !== "slots_full" && !result.toast.includes("slots_full"), `${test.id}: Gauge-Doppelklick zeigte slots_full-Toast`);

    await page.locator('[data-tc-action="normal"]').click();
    await waitForNormalState(page);
    assert(await visible(rootButton), `${test.id}: Rootbutton bei vollen Slots nicht sichtbar`);
    await rootButton.click();
    await waitForCockpitState(page, 3);
    result = await readUiState(page);
    assert(result.state.slotCount === 3 && result.state.slots.length === 3, `${test.id}: volle Slots kehrten nicht ins Cockpit zurück`);
    assertNoPositiveError(result, `${test.id}: Root-Rückkehr bei vollen Slots`);
    return {
      id: test.id,
      viewport: viewportOf(test),
      slotCount: result.state.slotCount,
      focusSequence,
      contentKeys: [slot1Contract.contentKey, secondContract.contentKey, thirdContract.contentKey],
    };
  } finally {
    await context.close();
  }
}

async function runInvalidIdNegative(browser, test) {
  const { context, page } = await boot(browser, test);
  try {
    const setup = await createNormalPlan(page, ["Abduktion Maschine"]);
    await page.evaluate(plan => {
      const invalid = { ...plan.exercises[0], id: "!!", localId: "!!", sourceId: "!!", bankId: "!!" };
      window.KGGDataStore.setCurrentPlan({ ...plan, exercises: [invalid] }, "ticket_037_invalid_exercise_fixture");
    }, setup.plan);
    await closeAllowedAdminModal(page);
    await page.locator("#kggTherapyCockpitButton").click();
    await page.waitForFunction(() => document.querySelector("#kggTherapyCockpitToast.show"), null, { timeout: 5000 });
    const result = await readUiState(page);
    assert(result.state.slotCount === 0, "Invalid-ID-Fixture erzeugte einen Cockpit-Slot");
    assert(!result.open, "Invalid-ID-Fixture öffnete das Cockpit als Erfolg");
    assert(result.errorCode === "unknown_exercise_id", "Invalid-ID-Fixture lieferte nicht unknown_exercise_id");
    assert(result.toast.includes("(unknown_exercise_id)"), "Invalid-ID-Fixture zeigte keinen strukturierten Toast");
    return { id: test.id, errorCode: result.errorCode, slotCount: result.state.slotCount };
  } finally {
    await context.close();
  }
}

(async () => {
  const browser = await chromium.launch({ headless: true });
  const visibility = [];
  const flows = [];
  let completeVisibilityMatrix;
  let directMultiExercise;
  let negative;
  try {
    for (const test of VISIBILITY_CASES) visibility.push(await runVisibility(browser, test));
    completeVisibilityMatrix = await runCompleteVisibilityMatrix(browser);
    directMultiExercise = await runDirectMultiExercise(browser);
    for (const test of FLOW_CASES) flows.push(await runPositive(browser, test));
    negative = await runInvalidIdNegative(browser, FLOW_CASES.find(test => test.width === 1024) || FLOW_CASES[0]);
  } finally {
    await browser.close();
  }
  console.log(JSON.stringify({
    status: "PASS",
    ticket: "KGG-TICKET-037",
    checks: [
      "complete root-button visibility matrix",
      "normal UI plan plus visible root-button double-click to slot 1",
      "second root click navigates without duplicating slot 1",
      "identical Finish text import deduplication",
      "same planId with normal UI content change to slot 2",
      "separate Finish Gauge import to slot 3",
      "third-import double-click has no slot 4 and no slots_full toast",
      "full slots root return",
      "contentKey equals api.contentKey(api.fromPlan(currentPlan))",
      "Finish DOM, canonical App blue, and real tab focus order",
      "invalid exercise ID fail-closed fixture",
    ],
    visibilityMatrix: visibility,
    completeVisibilityMatrix,
    directMultiExercise,
    flows,
    negative,
  }, null, 2));
})().catch(error => {
  console.error(error.stack || error);
  process.exitCode = 1;
});
