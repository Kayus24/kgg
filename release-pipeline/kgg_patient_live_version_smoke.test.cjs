"use strict";

// Replay the real release-smoke helpers without a browser or a network server.
const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");
const test = require("node:test");
const vm = require("node:vm");

const filename = path.join(__dirname, "kgg_patient_live_version_smoke.js");
const source = fs.readFileSync(filename, "utf8");
function extract(name) {
  const start = source.search(new RegExp(`^(?:async )?function ${name}\\(`, "m"));
  assert.notEqual(start, -1, `real helper ${name} must exist`);
  const tail = source.slice(start);
  const next = tail.slice(1).search(/\n(?:async )?function /);
  return next === -1 ? tail : tail.slice(0, next + 1);
}

function fixture({ active = "93", controller = "93", attachOnWait = "93", update, diagnosticsError } = {}) {
  const logs = [];
  let visible = "v93";
  let switchedController = undefined;
  let closed = false;
  let serverClosed = false;
  function worker(version) {
    return version === null ? null : {
      version,
      state: "activated",
      scriptURL: `https://example.invalid/service-worker.js?v=${version}`,
      postMessage(_message, ports) {
        queueMicrotask(() => ports[0].deliver({ data: { version } }));
      },
    };
  }
  const registration = { active: worker(active), update: update || (async () => {}) };
  const serviceWorker = {
    controller: worker(controller),
    ready: Promise.resolve(registration),
    getRegistration: async () => {
      if (diagnosticsError) throw diagnosticsError;
      return registration;
    },
  };
  const navigator = { serviceWorker };
  const document = { querySelector: () => ({ textContent: visible }) };
  const page = {
    goto: async () => {},
    evaluate: async (fn, arg) => fn(arg),
    async waitForFunction(fn, arg) {
      if (await fn(arg)) return;
      // A delayed clients.claim(): only an actual readiness wait may advance it.
      serviceWorker.controller = worker(attachOnWait);
      assert.equal(Boolean(await fn(arg)), true, "document never became ready");
    },
    locator(selector) {
      return {
        waitFor: async () => {},
        innerText: async () => selector === "#kggAppVersion" ? visible : "Jetzt aktualisieren",
        click: async () => {
          serviceWorker.controller = worker("94");
          registration.active = worker("94");
          visible = "v94";
        },
      };
    },
  };
  const context = { newPage: async () => page, close: async () => { closed = true; } };
  const sandbox = {
    navigator, document,
    console: { error: message => logs.push(message) },
    MessageChannel: class {
      constructor() {
        this.port1 = {};
        this.port2 = { deliver: event => this.port1.onmessage(event) };
      }
    },
    setTimeout, clearTimeout,
    stubExternalQr: async () => {},
    encodePlan: () => "synthetic-plan",
    startStaleRuntimeServer: () => ({
      server: { listen(_port, _host, done) { done(); }, address: () => ({ port: 1 }), close(done) { serverClosed = true; done(); } },
      setServeNew() { switchedController = serviceWorker.controller?.version ?? null; },
    }),
  };
  const helpers = vm.runInNewContext(
    ["assert", "activeWorkerVersion", "liveVersionEvidence", "verifyStaleClientUpdate"].map(extract).join("\n") +
      "\n({ activeWorkerVersion, verifyStaleClientUpdate });",
    sandbox,
    { filename },
  );
  return {
    helpers, page, navigator, registration, logs,
    browser: { newContext: async () => context },
    get switchedController() { return switchedController; },
    get closed() { return closed; },
    get serverClosed() { return serverClosed; },
  };
}

test("an active registration cannot stand in for a missing document controller", async () => {
  const f = fixture({ controller: null });
  assert.equal(await f.helpers.activeWorkerVersion(f.page), "");
});

test("document version comes from its old controller even when registration.active is newer", async () => {
  const f = fixture({ active: "94", controller: "93" });
  assert.equal(await f.helpers.activeWorkerVersion(f.page), "93");
});

test("an ordinary controlled document still returns its exact version", async () => {
  const f = fixture();
  assert.equal(await f.helpers.activeWorkerVersion(f.page), "93");
});

test("a browser without service workers has no controller-version evidence", async () => {
  const f = fixture();
  delete f.navigator.serviceWorker;
  assert.equal(await f.helpers.activeWorkerVersion(f.page), "");
});

test("stale runtime switches only after delayed old-document control", async () => {
  const f = fixture({ controller: null });
  const result = await f.helpers.verifyStaleClientUpdate(f.browser, "94");
  assert.equal(f.switchedController, "93");
  assert.equal(result.stale.worker, "93");
  assert.equal(result.updated.worker, "94");
  assert.equal(f.closed, true);
});

test("an unclaimed document cannot switch the stale runtime", async () => {
  const f = fixture({ controller: null, attachOnWait: null });
  await assert.rejects(f.helpers.verifyStaleClientUpdate(f.browser, "94"), /document never became ready/);
  assert.equal(f.switchedController, undefined);
  assert.equal(f.closed, true);
});

test("a visible old label cannot certify the wrong document controller", async () => {
  const f = fixture({ active: "93", controller: "92" });
  await assert.rejects(f.helpers.verifyStaleClientUpdate(f.browser, "94"), /stale client.*worker|stale client.*controller/i);
  assert.equal(f.switchedController, undefined);
  assert.equal(f.closed, true);
});

test("update rejection logs all worker states while preserving the original error and cleanup", async () => {
  const failure = new Error("synthetic registration.update failure");
  const f = fixture({ update: async () => { throw failure; } });
  f.registration.waiting = { state: "installed", scriptURL: "https://example.invalid/waiting.js" };
  f.registration.installing = { state: "installing", scriptURL: "https://example.invalid/installing.js" };
  await assert.rejects(f.helpers.verifyStaleClientUpdate(f.browser, "94"), error => error === failure);
  const prefix = "STALE_CLIENT_UPDATE_STATE ";
  const line = f.logs.find(message => message.startsWith(prefix));
  assert.ok(line, "failure must include worker-state diagnostics");
  assert.deepEqual(JSON.parse(line.slice(prefix.length)), {
    controller: { state: "activated", scriptURL: "https://example.invalid/service-worker.js?v=93" },
    active: { state: "activated", scriptURL: "https://example.invalid/service-worker.js?v=93" },
    waiting: f.registration.waiting,
    installing: f.registration.installing,
  });
  assert.equal(f.closed, true);
  assert.equal(f.serverClosed, true);
});

test("a diagnostic exception cannot replace the original update error or prevent cleanup", async () => {
  const failure = new Error("synthetic original update failure");
  const f = fixture({
    update: async () => { throw failure; },
    diagnosticsError: new Error("synthetic diagnostics unavailable"),
  });
  await assert.rejects(f.helpers.verifyStaleClientUpdate(f.browser, "94"), error => error === failure);
  assert.ok(f.logs.includes('STALE_CLIENT_UPDATE_STATE {"unavailable":true}'));
  assert.equal(f.closed, true);
  assert.equal(f.serverClosed, true);
});

test("a pending registration update cannot complete the stale-client verification", async () => {
  let resolveUpdate;
  const update = new Promise(resolve => { resolveUpdate = resolve; });
  const f = fixture({ update: () => update });
  let completed = false;
  const result = f.helpers.verifyStaleClientUpdate(f.browser, "94").then(value => { completed = true; return value; });
  await new Promise(resolve => setImmediate(resolve));
  const completedBeforeUpdate = completed;
  resolveUpdate();
  const evidence = await result;
  assert.equal(completedBeforeUpdate, false);
  assert.equal(evidence.updated.worker, "94");
  assert.equal(f.closed, true);
});
