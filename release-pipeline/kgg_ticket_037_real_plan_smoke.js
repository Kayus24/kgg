#!/usr/bin/env node
"use strict";

const path = require("path");
const { pathToFileURL } = require("url");
const { chromium } = require("playwright");

const ROOT = path.resolve(__dirname, "..");
const HTML_URL = pathToFileURL(path.join(ROOT, "kgg-update", "index.html")).href;
const PATIENT = "KGG Ticket 037 Testpatient";
const EXERCISE_ONLY_NAME = "Übungsplan ohne Patientendaten";
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

async function createExerciseOnlyPlan(page, exerciseNames) {
  await closeAllowedAdminModal(page);
  for (let index = 0; index < exerciseNames.length; index += 1) {
    await addExerciseFromVisibleUi(page, exerciseNames[index], index + 1);
  }
  return page.evaluate(fallbackName => {
    const plan = window.KGGDataStore.getCurrentPlan();
    const codecPlan = {
      ...plan,
      name: fallbackName,
      patient: { ...(plan.patient || {}), name: fallbackName },
    };
    const api = window.KGGTherapyCockpit;
    return {
      plan,
      contentKey: api.contentKey(api.fromPlan(codecPlan)),
      exerciseNames: plan.exercises.map(ex => ex.name),
    };
  }, EXERCISE_ONLY_NAME);
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
    let result = await readUiState(page);
    assert(result.state.slotCount === 1, "Direkter Mehrübungsimport erzeugte nicht genau Slot 1");
    assert(result.state.slots[0].name === PATIENT, "Direkter Mehrübungsimport verlor den Patientenbezug");
    assertSlotMatches(result.state, 0, contract, "Direkter Mehrübungsimport");
    assertNoPositiveError(result, "Direkter Mehrübungsimport");
    await page.locator('.kgg-tce-tool[data-tce-action="edit"][data-tce-slot="0"][data-tce-ex="0"]').click();
    await page.locator("#editorModal.open").waitFor({ state: "visible", timeout: 5000 });
    await page.locator("#editName").fill("Abduktion direkt bearbeitet");
    await page.locator("#saveExercise").click();
    await page.locator("#editorModal.open").waitFor({ state: "hidden", timeout: 5000 });
    await page.waitForFunction(() => {
      const plan = window.KGGDataStore.getCurrentPlan();
      return !!plan && plan.exercises[0] && plan.exercises[0].name === "Abduktion direkt bearbeitet";
    }, null, { timeout: 5000 });
    result = await readUiState(page);
    assert(result.state.slots[0].exerciseCount === 2, "Direkter Cockpit-Edit verlor eine Übung");
    assert(result.state.renderedExerciseNames[0][0] === "Abduktion direkt bearbeitet", "Direkter Cockpit-Edit aktualisierte Slot 1 nicht");
    await page.locator('.kgg-tce-tool[data-tce-action="edit"][data-tce-slot="0"][data-tce-ex="1"]').click();
    await page.locator("#editorModal.open").waitFor({ state: "visible", timeout: 5000 });
    await page.locator("#editSets").selectOption("3");
    await page.locator("#saveExercise").click();
    await page.waitForFunction(() => {
      const plan = window.KGGDataStore.getCurrentPlan();
      return !!plan && plan.exercises[1] && Number(plan.exercises[1].sets) === 3;
    }, null, { timeout: 5000 });
    result = await readUiState(page);
    assert(result.state.slots[0].exerciseCount === 2, "zweiter direkter Cockpit-Edit verlor eine Übung");
    return { exerciseNames: ["Abduktion direkt bearbeitet", contract.exerciseNames[1]], slotCount: result.state.slotCount, syncedToCurrentPlan: true, repeatedEditSync: true };
  } finally {
    await context.close();
  }
}

async function runContinuousCockpitLiveEdit(browser) {
  const test = { id: "continuous-live-edit-1024", width: 1024, height: 768, mobile: false };
  const { context, page } = await boot(browser, test);
  let freshContext;
  let freshPage;
  const pageErrors = [];
  page.on("pageerror", error => pageErrors.push(error.message));
  try {
    const initial = await createNormalPlan(page, ["Abduktion Maschine", "Adduktion Maschine"]);
    assert(initial.plan.exercises.length === 2, `${test.id}: normaler Ausgangsplan wurde nicht über die sichtbare UI aufgebaut`);
    const rootButton = page.locator("#kggTherapyCockpitButton");
    assert(await visible(rootButton), `${test.id}: sichtbarer Cockpit-Button fehlt`);
    await rootButton.click();
    await waitForCockpitState(page, 1);

    const initialSlot = await page.evaluate(() => window.KGGTherapyCockpit.getSlot(0));
    assert(initialSlot.name === PATIENT && initialSlot.exercises.length === 2, `${test.id}: Rootbutton erzeugte keinen vollständigen Slot 1`);

    // Werte ausschließlich über das sichtbare Cockpit-Numpad setzen. Diese Werte
    // dienen als Identitätsanker für Reorder, Löschen und den Link-Roundtrip.
    await page.locator('[data-tc-action="toggle"][data-tc-slot="0"][data-tc-ex="0"]').click();
    await page.locator('[data-tc-action="input"][data-tc-slot="0"][data-tc-ex="0"][data-tc-set="0"][data-tc-field="load"]').click();
    await page.locator('[data-tc-action="key"][data-tc-slot="0"][data-tc-ex="0"][data-tc-set="0"][data-tc-field="load"][data-tc-key="8"]').click();
    await page.locator('[data-tc-action="key"][data-tc-slot="0"][data-tc-ex="0"][data-tc-set="0"][data-tc-field="load"][data-tc-key="OK"]').click();
    await page.locator('[data-tc-action="input"][data-tc-slot="0"][data-tc-ex="0"][data-tc-set="0"][data-tc-field="metric"]').click();
    await page.locator('[data-tc-action="key"][data-tc-slot="0"][data-tc-ex="0"][data-tc-set="0"][data-tc-field="metric"][data-tc-key="1"]').click();
    await page.locator('[data-tc-action="key"][data-tc-slot="0"][data-tc-ex="0"][data-tc-set="0"][data-tc-field="metric"][data-tc-key="0"]').click();
    await page.locator('[data-tc-action="key"][data-tc-slot="0"][data-tc-ex="0"][data-tc-set="0"][data-tc-field="metric"][data-tc-key="OK"]').click();

    await page.locator('.kgg-tce-tool[data-tce-action="edit"][data-tce-slot="0"][data-tce-ex="0"]').click();
    await page.locator("#editorModal.open").waitFor({ state: "visible", timeout: 5000 });
    await page.locator("#editName").fill("Abduktion live final");
    await page.locator("#editSets").selectOption("4");
    await page.locator("#editLoad").fill("33");
    await page.locator("#editMetric").fill("12");
    await page.locator("#kggCockpitAddStage").click();
    await page.locator("[data-cockpit-stage-name]").last().fill("Schwerere Stufe");
    await page.locator("#kggCockpitAddStage").click();
    await page.locator("[data-cockpit-stage-name]").last().fill("Leichtere Stufe");
    await page.locator("#saveExercise").click();
    await page.locator("#editorModal.open").waitFor({ state: "hidden", timeout: 5000 });
    let edited = await page.evaluate(() => window.KGGTherapyCockpit.getSlot(0));
    assert(edited.exercises[0].name === "Abduktion live final" && edited.exercises[0].sets === 4 && edited.exercises[0].startLoad === "33" && edited.exercises[0].startMetric === "12", `${test.id}: Cockpit-Editor hat die Bearbeitung nicht gespeichert`);
    assert(edited.exercises[0].progressionVariants.length === 2, `${test.id}: Progressionsstufen wurden nicht gespeichert`);

    const stageSelect = page.locator('[data-tce-stage-switch="1"]').first();
    await stageSelect.evaluate(select => {
      const option = Array.from(select.options).find(item => item.textContent.trim() === "Leichtere Stufe");
      if (!option) throw new Error("visible progression stage option missing");
      select.value = option.value;
      select.dispatchEvent(new Event("change", { bubbles: true }));
    });
    await page.waitForTimeout(120);
    edited = await page.evaluate(() => window.KGGTherapyCockpit.getSlot(0));
    assert(edited.exercises[0].activeProgressionId === edited.exercises[0].progressionVariants[1].id, `${test.id}: Progressionsstufe ließ sich nicht wechseln`);

    await page.locator('.kgg-tce-add-card[data-tce-slot="0"]').click();
    await page.waitForSelector("#kggTceAddModal:not([hidden])", { timeout: 5000 });
    await page.locator("#kggTceAddModal .kgg-tce-bank-search").fill("Bridging");
    await page.locator('#kggTceAddModal [data-tce-bank-id]').first().click();
    await page.waitForSelector("#kggTceAddModal[hidden]", { state: "hidden", timeout: 5000 });
    let afterAdd = await page.evaluate(() => window.KGGTherapyCockpit.getSlot(0));
    assert(afterAdd.exercises.length === 3 && afterAdd.exercises[2].name === "Bridging", `${test.id}: Plus-Karte fügte keine Übung hinzu`);

    const handles = page.locator('.kgg-tc-card[data-tc-card="0"] .kgg-tce-drag');
    const sourceBox = await handles.nth(2).boundingBox();
    const targetBox = await handles.nth(0).boundingBox();
    assert(sourceBox && targetBox, `${test.id}: sichtbare Reorder-Handles fehlen`);
    await page.mouse.move(sourceBox.x + sourceBox.width / 2, sourceBox.y + sourceBox.height / 2);
    await page.mouse.down();
    await page.mouse.move(targetBox.x + targetBox.width / 2, targetBox.y - 18, { steps: 6 });
    await page.mouse.up();
    await page.waitForTimeout(250);
    const afterMove = await page.evaluate(() => window.KGGTherapyCockpit.getSlot(0));
    assert(afterMove.exercises.map(ex => ex.name).join("|") === "Bridging|Abduktion live final|Adduktion Maschine", `${test.id}: Cockpit-Reorder über sichtbaren Handle war falsch`);
    const movedEdited = afterMove.exercises[1];
    assert(movedEdited.today[0][0] === "8" && movedEdited.today[0][1] === "10" && movedEdited.activeProgressionId === movedEdited.progressionVariants[1].id, `${test.id}: Reorder verlor Werte oder Progressionsstufe`);

    const downwardSource = await page.locator('.kgg-tc-card[data-tc-card="0"] .kgg-tce-drag').nth(0).boundingBox();
    const downwardTarget = await page.locator('.kgg-tc-card[data-tc-card="0"] .kgg-tc-exercise').nth(2).boundingBox();
    assert(downwardSource && downwardTarget, `${test.id}: sichtbare Handles für den zweiten Reorder fehlen`);
    await page.evaluate(() => {
      const exercises = Array.from(document.querySelectorAll('.kgg-tc-card[data-tc-card="0"] .kgg-tc-exercise'));
      const source = exercises[0] && exercises[0].querySelector(".kgg-tce-drag");
      const target = exercises[2];
      if (!source || !target) throw new Error("downward reorder DOM target missing");
      const sourceRect = source.getBoundingClientRect();
      const targetRect = target.getBoundingClientRect();
      const emit = (type, targetNode, x, y) => targetNode.dispatchEvent(new PointerEvent(type, { bubbles: true, cancelable: true, pointerId: 91, pointerType: "mouse", isPrimary: true, button: 0, clientX: x, clientY: y }));
      emit("pointerdown", source, sourceRect.left + sourceRect.width / 2, sourceRect.top + sourceRect.height / 2);
      emit("pointermove", document, sourceRect.left + sourceRect.width / 2, targetRect.bottom + 24);
      emit("pointerup", document, sourceRect.left + sourceRect.width / 2, targetRect.bottom + 24);
    });
    await page.waitForTimeout(250);
    const afterDownwardMove = await page.evaluate(() => window.KGGTherapyCockpit.getSlot(0));
    assert(afterDownwardMove.exercises.map(ex => ex.name).join("|") === "Abduktion live final|Adduktion Maschine|Bridging", `${test.id}: Cockpit-Reorder nach unten war falsch: ${afterDownwardMove.exercises.map(ex => ex.name).join("|")}`);
    assert(afterDownwardMove.exercises[0].today[0][0] === "8" && afterDownwardMove.exercises[0].today[0][1] === "10", `${test.id}: Abwärts-Reorder verlor Werte`);

    await page.locator('.kgg-tce-tool[data-tce-action="edit"][data-tce-slot="0"][data-tce-ex="1"]').click();
    await page.locator("#editorModal.open").waitFor({ state: "visible", timeout: 5000 });
    page.once("dialog", dialog => dialog.accept());
    await page.locator("#deleteExercise").click();
    await page.waitForTimeout(300);
    const afterDelete = await page.evaluate(() => window.KGGTherapyCockpit.getSlot(0));
    assert(afterDelete.exercises.length === 2 && afterDelete.exercises.map(ex => ex.name).join("|") === "Abduktion live final|Bridging", `${test.id}: Cockpit-Löschen entfernte nicht nur die Zielübung`);
    assert(afterDelete.exercises[0].today[0][0] === "8" && afterDelete.exercises[0].today[0][1] === "10", `${test.id}: Löschen beschädigte den bearbeiteten Übungszustand`);

    await page.locator('[data-tc-action="finish"][data-tc-slot="0"]').click();
    await page.waitForSelector("#kggTherapyCockpitOutputModal:not([hidden])", { timeout: 5000 });
    const output = await page.locator("#kggTherapyCockpitOutput").inputValue();
    const linkMatch = output.match(/https:\/\/[^\s]+[?&]cockpit=[^\s]+/);
    assert(linkMatch, `${test.id}: Plan-fertig-Ausgabe enthält keinen neuen Cockpit-Link`);
    const generatedUrl = new URL(linkMatch[0]);
    assert(generatedUrl.searchParams.has("cockpit"), `${test.id}: erzeugter Link enthält keinen Cockpit-Parameter`);

    freshContext = await browser.newContext({ viewport: { width: 1024, height: 768 }, deviceScaleFactor: 1, hasTouch: true, isMobile: false, locale: "de-DE" });
    freshPage = await freshContext.newPage();
    freshPage.on("pageerror", error => pageErrors.push(error.message));
    await freshPage.addInitScript(() => { localStorage.setItem("kgg_pwa_install_prompt_seen_v1", "ticket-037-continuous-live-edit"); });
    const localRoundtripUrl = new URL(HTML_URL);
    localRoundtripUrl.search = generatedUrl.search;
    await freshPage.goto(localRoundtripUrl.toString(), { waitUntil: "domcontentloaded", timeout: 30000 });
    await waitForCockpitState(freshPage, 1);
    const imported = await freshPage.evaluate(() => ({ state: window.KGGTherapyCockpit.getState(), slot: window.KGGTherapyCockpit.getSlot(0) }));
    assert(imported.state.slotCount === 1 && imported.slot.name === PATIENT, `${test.id}: neuer Link importierte Slot 1/Patient nicht korrekt`);
    assert(imported.slot.exercises.map(ex => ex.name).join("|") === "Abduktion live final|Bridging", `${test.id}: neuer Link verlor Reihenfolge oder Löschung`);
    const importedEdited = imported.slot.exercises[0];
    assert(importedEdited.sets === 4 && importedEdited.startLoad === "33" && importedEdited.startMetric === "12" && importedEdited.today[0][0] === "8" && importedEdited.today[0][1] === "10", `${test.id}: neuer Link verlor bearbeitete Felder oder Werte`);
    assert(importedEdited.activeProgressionId === importedEdited.progressionVariants[1].id, `${test.id}: neuer Link verlor die aktive Progressionsstufe`);
    assert(!pageErrors.length, `${test.id}: Browserfehler: ${pageErrors.join(" | ")}`);
    return {
      id: test.id,
      slotCount: imported.state.slotCount,
      exerciseNames: imported.slot.exercises.map(ex => ex.name),
      editedExercise: { sets: importedEdited.sets, startLoad: importedEdited.startLoad, today: importedEdited.today, activeProgressionId: importedEdited.activeProgressionId },
      linkChars: linkMatch[0].length,
    };
  } finally {
    if (freshContext) await freshContext.close();
    await context.close();
  }
}

async function runExerciseOnly(browser) {
  const test = { id: "exercise-only-1024", width: 1024, height: 768, mobile: false };
  const { context, page } = await boot(browser, test);
  try {
    const contract = await createExerciseOnlyPlan(page, ["Abduktion Maschine", "Adduktion Maschine"]);
    assert(!contract.plan.patient.name && !contract.plan.name && !contract.plan.patientName, "Übungen-only-Setup enthält unerwartete Basisdaten");
    const rootButton = page.locator("#kggTherapyCockpitButton");
    assert(await visible(rootButton), "Übungen-only-Plan zeigt den Cockpit-Button nicht an");

    await rootButton.click();
    await waitForCockpitState(page, 1);
    let result = await readUiState(page);
    assert(result.state.slotCount === 1, "Übungen-only-Import erzeugte nicht Slot 1");
    assert(result.state.slots[0].name === EXERCISE_ONLY_NAME, "Übungen-only-Import verwendet nicht den neutralen Namen");
    assertSlotMatches(result.state, 0, contract, "Übungen-only-Import");
    assertNoPositiveError(result, "Übungen-only-Import");

    await page.locator('[data-tc-action="remove"][data-tc-slot="0"]').click();
    await waitForNormalState(page);
    await openFinishDialog(page);
    await page.locator("#finishCockpitBtn").click();
    await waitForCockpitState(page, 1);
    result = await readUiState(page);
    assert(result.state.slotCount === 1, "Übungen-only-Fertig-Import erzeugte nicht Slot 1");
    assert(result.state.slots[0].name === EXERCISE_ONLY_NAME, "Übungen-only-Fertig-Import verwendet nicht den neutralen Namen");
    assertSlotMatches(result.state, 0, contract, "Übungen-only-Fertig-Import");
    assertNoPositiveError(result, "Übungen-only-Fertig-Import");
    return { exerciseNames: contract.exerciseNames, slotCount: result.state.slotCount, fallbackName: EXERCISE_ONLY_NAME };
  } finally {
    await context.close();
  }
}

async function runPhoneCockpitEntry(browser) {
  const test = { id: "phone-cockpit-entry-390", width: 390, height: 844, mobile: true };
  const { context, page } = await boot(browser, test);
  try {
    const initial = await createNormalPlan(page, ["Abduktion Maschine"]);
    const initialButton = page.locator("#kggTherapyCockpitButton");
    assert(!(await visible(initialButton)), `${test.id}: leerer Cockpit-State zeigt bereits den Handy-Einstieg`);

    const generatedLink = await page.evaluate(() => {
      const plan = window.KGGDataStore.getCurrentPlan();
      const api = window.KGGTherapyCockpit;
      return api.makeLink(api.fromPlan(plan));
    });
    const localRoundtripUrl = new URL(HTML_URL);
    localRoundtripUrl.search = new URL(generatedLink).search;
    await page.goto(localRoundtripUrl.toString(), { waitUntil: "domcontentloaded", timeout: 30000 });
    await waitForCockpitState(page, 1);
    await page.locator('[data-tc-action="normal"]').click();
    await waitForNormalState(page);

    const entry = page.locator("#kggTherapyCockpitButton");
    await entry.waitFor({ state: "visible", timeout: 5000 });
    const firstLayout = await page.evaluate(() => {
      const scan = document.querySelector("#scanBtn");
      const entry = document.querySelector("#kggTherapyCockpitButton");
      const scanRect = scan.getBoundingClientRect();
      const entryRect = entry.getBoundingClientRect();
      const overlap = !(scanRect.right <= entryRect.left || entryRect.right <= scanRect.left || scanRect.bottom <= entryRect.top || entryRect.bottom <= scanRect.top);
      return {
        parentId: entry.parentElement && entry.parentElement.id,
        text: entry.textContent.trim(),
        scanVisible: !!(scan.offsetWidth && scan.offsetHeight),
        entryVisible: !!(entry.offsetWidth && entry.offsetHeight),
        overlap,
      };
    });
    assert(firstLayout.parentId === "scanHub", `${test.id}: Cockpit-Einstieg liegt nicht direkt im schwebenden Scan-Dock`);
    assert(firstLayout.text === "Cockpit · 1 Plan", `${test.id}: falsche Zählung für einen geladenen Trainingsplan: ${firstLayout.text}`);
    assert(firstLayout.scanVisible && firstLayout.entryVisible && !firstLayout.overlap, `${test.id}: Scan- und Cockpit-Einstieg überlappen oder sind nicht sichtbar`);

    await entry.click();
    await waitForCockpitState(page, 1);
    await page.locator('[data-tc-action="normal"]').click();
    await waitForNormalState(page);
    await addExerciseFromVisibleUi(page, "Adduktion Maschine", 2);
    const secondLink = await page.evaluate(() => {
      const plan = window.KGGDataStore.getCurrentPlan();
      const api = window.KGGTherapyCockpit;
      return api.makeLink(api.fromPlan(plan));
    });
    await entry.click();
    await waitForCockpitState(page, 1);
    await page.locator('[data-tc-action="import-open"]').click();
    await page.locator("#kggTherapyCockpitImportInput").fill(secondLink);
    await page.locator('[data-tc-action="import-submit"]').click();
    await waitForCockpitState(page, 2);
    await page.locator('[data-tc-action="normal"]').click();
    await waitForNormalState(page);
    await entry.waitFor({ state: "visible", timeout: 5000 });
    const secondLabel = await entry.textContent();
    assert(secondLabel.trim() === "Cockpit · 2 Pläne", `${test.id}: falsche Zählung für zwei geladene Trainingspläne: ${secondLabel}`);
    return { id: test.id, firstLabel: firstLayout.text, secondLabel: secondLabel.trim(), parentId: firstLayout.parentId, noOverlap: !firstLayout.overlap };
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
  let continuousLiveEdit;
  let exerciseOnly;
  let phoneCockpitEntry;
  let negative;
  try {
    for (const test of VISIBILITY_CASES) visibility.push(await runVisibility(browser, test));
    completeVisibilityMatrix = await runCompleteVisibilityMatrix(browser);
    directMultiExercise = await runDirectMultiExercise(browser);
    continuousLiveEdit = await runContinuousCockpitLiveEdit(browser);
    exerciseOnly = await runExerciseOnly(browser);
    phoneCockpitEntry = await runPhoneCockpitEntry(browser);
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
      "normal UI plan with exercises only through root button and Finish action",
      "phone Cockpit entry appears only for loaded plans and counts loaded plans",
      "direct current-plan Cockpit edit sync and repeated edit sync",
      "continuous visible Cockpit add/edit/reorder/progression/delete/finish and fresh-link import",
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
    continuousLiveEdit,
    exerciseOnly,
    phoneCockpitEntry,
    flows,
    negative,
  }, null, 2));
})().catch(error => {
  console.error(error.stack || error);
  process.exitCode = 1;
});
