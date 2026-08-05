#!/usr/bin/env node
"use strict";

const fs = require("fs");
const path = require("path");
const vm = require("vm");

const ROOT = path.resolve(__dirname, "..");
const sourcePath = path.join(ROOT, "patient-pain-vertical-scale.js");
const source = fs.readFileSync(sourcePath, "utf8");

function assert(condition, message) {
  if (!condition) throw new Error(message);
}

const window = { __KGG_TEST__: true };
const sandbox = {
  window,
  document: {
    readyState: "loading",
    addEventListener() {},
    getElementById() { return null; },
  },
  localStorage: { getItem() { return null; } },
  MutationObserver: function MutationObserver() {},
  addEventListener() {},
  setTimeout,
  clearTimeout,
  requestAnimationFrame(callback) { callback(); },
  console,
};
vm.runInNewContext(source, sandbox, { filename: sourcePath });
const api = window.__kggPainVerticalTest;
assert(api, "vertical pain test API is missing");
assert(api.valueFromY(22, 462, 22) === 10, "top must map to 10");
assert(api.valueFromY(22, 462, 462) === 0, "bottom must map to 0");
assert(api.valueFromY(22, 462, 242) === 5, "middle must map to 5");
assert(api.valueFromY(22, 462, -100) === 10, "values above the rail must clamp to 10");
assert(api.valueFromY(22, 462, 900) === 0, "values below the rail must clamp to 0");
assert(api.currentText(false, 0, false) === "–", "unset pain must stay distinguishable from zero");
assert(api.currentText(true, 0, false) === "0/10", "selected zero must remain a real value");
assert(api.currentText(true, 10, true) === "10/10", "English current value is wrong");
assert(source.includes("Schmerzen bei der Übung"), "German exercise-pain label is missing");
assert(source.includes("Pain during exercise"), "English exercise-pain label is missing");
assert(source.includes("card.querySelector('.kggSetPain')"), "set-pain mode exclusion is missing");
assert(source.includes("typeof setPain==='function'"), "existing exercise-pain commit handler is not reused");
assert(!source.includes("localStorage.setItem("), "vertical pain UI must not create a second storage writer");
assert(source.includes("pointercancel"), "pointer cancellation contract is missing");
assert(source.includes("aria-orientation','vertical'"), "vertical slider accessibility contract is missing");
assert(source.includes("row.inert=true"), "hidden legacy controls are not made inert");
console.log("Patient vertical pain smoke: PASS");
