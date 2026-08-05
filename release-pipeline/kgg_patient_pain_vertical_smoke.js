#!/usr/bin/env node
"use strict";

const fs = require("fs");
const path = require("path");
const vm = require("vm");

const ROOT = path.resolve(__dirname, "..");
const sourcePath = path.join(ROOT, "patient-pain-vertical-scale.js");
const source = fs.readFileSync(sourcePath, "utf8");
const browserSource = fs.readFileSync(path.join(ROOT, "release-pipeline/kgg_patient_pain_vertical_playwright.js"), "utf8");
const resourceManifest = JSON.parse(fs.readFileSync(path.join(ROOT, "docs/kgg-custom-gpt-resource-manifest.json"), "utf8"));

function assert(condition, message) { if (!condition) throw new Error(message); }

const window = { __KGG_TEST__: true };
const sandbox = {
  window,
  document: { readyState:"loading", addEventListener() {}, getElementById() { return null; } },
  localStorage: { getItem() { return null; } },
  MutationObserver: function MutationObserver() {},
  addEventListener() {},
  setTimeout,
  clearTimeout,
  requestAnimationFrame(callback) { callback(); },
  console,
};
vm.runInNewContext(source, sandbox, { filename:sourcePath });
const api = window.__kggPainVerticalTest;
assert(api, "vertical pain test API is missing");
assert(api.valueFromY(22,462,22)===10,"top must map to 10");
assert(api.valueFromY(22,462,462)===0,"bottom must map to 0");
assert(api.valueFromY(22,462,242)===5,"middle must map to 5");
assert(api.valueFromY(22,462,-100)===10,"values above the rail must clamp to 10");
assert(api.valueFromY(22,462,900)===0,"values below the rail must clamp to 0");
assert(api.currentText(false,0)==="–","unset pain must stay distinguishable from zero");
assert(api.currentText(true,0)==="0/10","selected zero must remain a real value");
assert(source.includes("Schmerzen bei der Übung?"),"German question label is missing");
assert(source.includes("Pain during exercise?"),"English question label is missing");
assert(source.includes("Schlimmster vorstellbarer Schmerz"),"maximum pain description is missing");
assert(source.includes("Gar kein Schmerz"),"minimum pain description is missing");
assert(source.includes("Worst imaginable pain")&&source.includes("No pain at all"),"English endpoint descriptions are missing");
assert(source.includes("const MODAL_ID='kggPainModal'"),"singleton modal contract is missing");
assert(source.includes("document.body.appendChild(overlay)"),"floating modal is not mounted under body");
assert(source.includes("backdrop-filter:blur(4px)"),"background blur is missing");
assert(source.includes("if(event.target===overlay)"),"backdrop-only close contract is missing");
assert(source.includes("body.style.position='fixed'"),"scroll lock contract is missing");
assert(source.includes("window.scrollTo(0,lock.scrollY)"),"scroll restoration contract is missing");
assert(source.includes("node.inert=true"),"background inert contract is missing");
assert(source.includes("card.querySelector('.kggSetPain')"),"set-pain mode exclusion is missing");
assert(source.includes("typeof setPain==='function'"),"existing exercise-pain commit handler is not reused");
assert(!source.includes("localStorage.setItem("),"vertical pain UI must not create a second storage writer");
assert(source.includes("pointercancel"),"pointer cancellation contract is missing");
assert(source.includes("rowHeight=rect.height/(MAX-MIN+1)"),"dynamic viewport mapping is missing");
assert(source.includes("aria-describedby"),"endpoint descriptions are not connected to the slider");
assert(source.includes("row.inert=true"),"hidden legacy controls are not made inert");
assert(source.includes("row.style.setProperty('display','none','important')"),"legacy pain row is not force-hidden");
assert(source.includes("restoreOriginal(state)"),"legacy pain fallback cannot be restored");
assert(!source.includes("setTimeout(()=>closeModal"),"modal must not auto-close after selecting a value");
assert(browserSource.includes('opening modal changed exercise-card height'),"browser test does not protect card height");
assert(browserSource.includes('Schlimmster vorstellbarer Schmerz'),"browser test does not verify maximum description");
assert(browserSource.includes('Gar kein Schmerz'),"browser test does not verify minimum description");
assert(browserSource.includes('modal auto-closed after choosing a value'),"browser test does not protect deliberate closing");
assert(browserSource.includes('closing modal did not restore scroll position'),"browser test does not protect scroll restoration");
assert(browserSource.includes('day change did not close pain modal'),"browser test does not protect day-change lifecycle");
assert(resourceManifest.patientProduction && resourceManifest.patientProduction.knowledge.length===4,"patient GPT resource manifest knowledge contract is incomplete");
assert(resourceManifest.patientProduction.knowledge.every(item=>/^[a-f0-9]{64}$/.test(item.sha256)),"patient GPT resource manifest contains an invalid digest");
console.log("Patient vertical pain floating modal smoke: PASS");