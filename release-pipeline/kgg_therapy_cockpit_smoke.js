#!/usr/bin/env node
"use strict";

/* Focused, browser-free contract test for the v082 cockpit module.
   The DOM view is exercised separately by the UI stability station; this
   smoke keeps the codec and RAM slot contract deterministic in CI as well. */
const fs = require("fs");
const path = require("path");
const vm = require("vm");

const root = path.resolve(__dirname, "..");
const sourcePath = path.join(root, "kgg-update", "src", "patches", "v082-therapy-cockpit.html");
const source = fs.readFileSync(sourcePath, "utf8");
const match = source.match(/<script\b[^>]*id="kgg-therapy-cockpit-script"[^>]*>([\s\S]*?)<\/script>/i);
if (!match) throw new Error("cockpit script module not found");

const window = {
  location: { href: "https://example.test/index.html?v=82" },
  KGG_PATCHES: {},
  addEventListener() {},
  dispatchEvent() {},
};
const document = {
  readyState: "loading",
  body: null,
  title: "KGG Test",
  addEventListener() {},
  getElementById() { return null; },
};
const context = {
  window,
  document,
  TextEncoder,
  TextDecoder,
  URL,
  URLSearchParams,
  Uint8Array,
  Array,
  Object,
  Number,
  String,
  Math,
  Date,
  JSON,
  Error,
  RegExp,
  unescape,
  encodeURIComponent,
  decodeURIComponent,
  btoa: value => Buffer.from(value, "binary").toString("base64"),
  atob: value => Buffer.from(value, "base64").toString("binary"),
  navigator: {},
  setTimeout,
  clearTimeout,
  console,
};
vm.createContext(context);
vm.runInContext(match[1], context, { filename: sourcePath });
const api = window.KGGTherapyCockpit;
if (!api) throw new Error("cockpit API not exposed");

function assert(condition, message) {
  if (!condition) throw new Error(message);
}
function expectCode(fn, expected) {
  try {
    fn();
  } catch (error) {
    assert(error && error.code === expected, `expected ${expected}, got ${error && error.code}`);
    return;
  }
  throw new Error(`expected error ${expected}`);
}
function exercise(id, index) {
  return {
    id,
    sets: 3,
    side: index % 2 ? "LR" : "BI",
    loadUnit: "kg",
    metricUnit: "Wdh",
    previous: [[String(10 + index), "12"], [String(11 + index), "11"], [String(12 + index), "10"]],
    today: [[String(10 + index), "12"], [String(11 + index), "11"], [String(12 + index), "10"]],
  };
}
const entries = api.registry.entries();
const ids = entries.map(entry => entry.id);
assert(entries.length >= 18, "canonical exercise registry is incomplete");
assert(new Set(ids).size === ids.length, "exercise IDs must be unique");
assert(ids.every(id => /^[0-9A-Za-z]{2}$/.test(id)), "exercise IDs must be exactly two Base62 characters");

// Keep the size probes honest even when the current canonical bank contains
// fewer than the largest supported plan. Synthetic registry entries model
// user-defined exercises and still exercise the same stable-ID contract.
const base62 = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz";
const probeEntries = entries.slice();
const idForIndex = index => base62[Math.floor(index / 62)] + base62[index % 62];
for (let index = probeEntries.length; index < 40; index += 1) {
  const id = idForIndex(62 + index);
  const name = `Probe Übung ${index + 1}`;
  api.registry.register(name, id, { sets: 3, metricUnit: "Wdh", loadUnit: "kg" });
  probeEntries.push({ id, name, canonical: true });
}

const five = entries.slice(0, 5).map((entry, index) => exercise(entry.id, index));
const payload = { planId: "plan-roundtrip", name: "Marta Müller", date: "2026-09-08", exercises: five };
const code = api.encode(payload);
assert(code.startsWith("KGGTC1:"), "codec prefix missing");
assert(!code.includes("Marta") && !code.includes("Müller"), "display name leaked into link");
const decoded = api.decode(code);
assert(decoded.name === payload.name, "obfuscated name did not roundtrip");
assert(decoded.exercises.length === 5, "exercise count did not roundtrip");
assert(decoded.exercises[1].side === "LR", "side mode did not roundtrip");
assert(decoded.exercises[4].previous[2][0] === "16", "previous value did not roundtrip");

const link = api.makeLink(payload, "https://example.test/index.html?v=82");
assert(link.includes("cockpit="), "link query parameter missing");
assert(api.decode(link).name === payload.name, "full URL import failed");
const originalHref = window.location.href;
window.location.href = "file:///data/user/0/de.kgg.app/files/web/kgg_android_current.html";
const localLink = api.makeLink(payload);
window.location.href = originalHref;
assert(localLink.startsWith("https://kayus24.github.io/kgg/kgg-update/index.html?"), "local wrapper links must use the public cockpit base");

const sizes = {};
for (const count of [5, 10, 20, 40]) {
  const plan = { ...payload, exercises: probeEntries.slice(0, count).map((entry, index) => exercise(entry.id, index)) };
  const sample = api.encode(plan);
  sizes[count] = { rawPayloadBytes: Buffer.byteLength(sample.slice(7), "utf8"), linkChars: api.makeLink(plan, "https://example.test/index.html?v=82").length };
  assert(plan.exercises.length === count && api.decode(sample).exercises.length === count, `size probe ${count} failed`);
}

const encodedPayload = JSON.parse(Buffer.from(code.slice(7).replace(/-/g, "+").replace(/_/g, "/") + "==", "base64").toString("utf8"));
encodedPayload.p = "tampered-plan";
const tampered = "KGGTC1:" + Buffer.from(JSON.stringify(encodedPayload), "utf8").toString("base64").replace(/\+/g, "-").replace(/\//g, "_").replace(/=+$/g, "");
expectCode(() => api.decode(tampered), "integrity_failed");
expectCode(() => api.encode({ name: "Test", exercises: [{ id: "zz", sets: 1 }] }), "unknown_exercise_id");

const derived = api.registry.derive("Kabelzug Spezial", { sets: 2, metricUnit: "Wdh", loadUnit: "kg" });
assert(/^[0-9A-Za-z]{2}$/.test(derived.id), "derived exercise ID is not Base62");
assert(api.registry.derive("Kabelzug Spezial").id === derived.id, "derived exercise ID is not deterministic");

const custom = api.registry.register("Kabelzug Anders", "zZ", { sets: 2, metricUnit: "Wdh", loadUnit: "kg" });
assert(custom.id === "zZ", "canonical registration did not retain the supplied ID");
const customCode = api.encode({ name: "Test", exercises: [{ id: "zZ", sets: 2, previous: [["5", "10"], ["6", "9"]], today: [["5", "10"], ["6", "9"]] }] });
assert(api.decode(customCode).exercises[0].id === "zZ", "registered custom exercise did not roundtrip");

let storedPlan = { id: "plan-hook", patient: { name: "Hook" }, exercises: [{ name: "Abduktion Maschine", sourceId: "abd" }] };
window.KGGDataStore = {
  getCurrentPlan: () => JSON.parse(JSON.stringify(storedPlan)),
  setCurrentPlan: plan => { storedPlan = JSON.parse(JSON.stringify(plan)); return storedPlan; },
};
api.importCode(api.encode({ planId: "plan-hook", name: "Hook", exercises: [{ id: "01", sets: 1, previous: [["2", "6"]], today: [["3", "7"]] }] }));
const hookResult = api.finish(0);
assert(hookResult && storedPlan.exercises[0].lastTraining[0].load === "3", "safe normal-plan completion hook did not receive today's value");
delete window.KGGDataStore;

api.importCode(code);
assert(api.getState().slotCount === 1 && api.getState().view === "cockpit", "first slot import failed");
api.close();
assert(api.getState().slotCount === 1 && api.getState().view === "normal", "view switch lost RAM slot");
api.importCode(api.encode({ ...payload, planId: "plan-2", name: "Jonas J", exercises: five.slice(0, 1) }));
api.importCode(api.encode({ ...payload, planId: "plan-3", name: "Lea L", exercises: five.slice(0, 1) }));
assert(api.getState().slotCount === 3, "three slots did not fill independently");
expectCode(() => api.importCode(code), "slots_full");
api.remove(1);
assert(api.getState().slotCount === 2 && !api.getState().slots[1], "middle slot removal changed the wrong slot");
const finished = api.finish(0);
assert(finished && finished.link && finished.text.includes("Neuer Cockpit-Link"), "finish did not create documentation output");
const next = api.decode(finished.link);
assert(next.exercises[0].previous[0][0] === decoded.exercises[0].today[0][0], "finish link did not promote today to previous");
assert(api.getState().slotCount === 1, "finish did not release exactly one slot");

const staticText = source.toLowerCase();
assert(!staticText.includes("localstorage") && !staticText.includes("sessionstorage") && !staticText.includes("indexeddb"), "cockpit patch introduced persistent patient storage");
console.log(JSON.stringify({ status: "PASS", patchId: api.patchId, registryEntries: entries.length, sizes, remainingSlots: api.getState().slotCount }, null, 2));
