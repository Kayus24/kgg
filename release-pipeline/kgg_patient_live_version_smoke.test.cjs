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

// Virtualize only the VM's timers. setImmediate drains its real Promise microtasks;
// advancing 15000/2000ms never sleeps for either browser-operation deadline.
const flushMicrotasks = () => new Promise(resolve => setImmediate(resolve));
function manualClock() {
  let now = 0;
  let nextId = 1;
  const timers = new Map();
  return {
    setTimeout(callback, delay, ...args) {
      const id = nextId++;
      timers.set(id, { at: now + Number(delay || 0), callback, args });
      return id;
    },
    clearTimeout(id) { timers.delete(id); },
    get pending() { return timers.size; },
    async advance(milliseconds) {
      await flushMicrotasks();
      const target = now + milliseconds;
      for (;;) {
        const next = [...timers.entries()].filter(([, timer]) => timer.at <= target)
          .sort((a, b) => a[1].at - b[1].at || a[0] - b[0])[0];
        if (!next) break;
        const [id, timer] = next;
        now = timer.at;
        timers.delete(id);
        timer.callback(...timer.args);
        await flushMicrotasks();
      }
      now = target;
      await flushMicrotasks();
    },
  };
}
function deferred() {
  let resolve;
  const promise = new Promise(done => { resolve = done; });
  return { promise, resolve };
}
function observe(promise) {
  const state = { status: "pending" };
  const finished = promise.then(
    value => { state.status = "fulfilled"; state.value = value; },
    error => { state.status = "rejected"; state.error = error; },
  );
  return { state, finished };
}

function fixture({ active = "93", controller = "93", attachOnWait = "93", update,
  diagnosticsError, ready, diagnostics, clock } = {}) {
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
    ready: ready || Promise.resolve(registration),
    getRegistration: async () => {
      if (diagnosticsError) throw diagnosticsError;
      if (diagnostics) return diagnostics;
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
    setTimeout: clock ? clock.setTimeout : setTimeout,
    clearTimeout: clock ? clock.clearTimeout : clearTimeout,
    stubExternalQr: async () => {},
    encodePlan: () => "synthetic-plan",
    startStaleRuntimeServer: () => ({
      server: { listen(_port, _host, done) { done(); }, address: () => ({ port: 1 }), close(done) { serverClosed = true; done(); } },
      setServeNew() { switchedController = serviceWorker.controller?.version ?? null; },
    }),
  };
  const helpers = vm.runInNewContext(
    ["assert", "withDeadline", "activeWorkerVersion", "liveVersionEvidence", "verifyStaleClientUpdate"].map(extract).join("\n") +
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

test("a never-resolving registration update rejects at the 15s Node deadline and cleans up", async () => {
  const clock = manualClock();
  const pending = deferred();
  const f = fixture({ clock, update: () => pending.promise });
  const verification = observe(f.helpers.verifyStaleClientUpdate(f.browser, "94"));
  try {
    await clock.advance(14999);
    assert.equal(f.switchedController, "93", "real helper must reach ready/update first");
    assert.equal(verification.state.status, "pending", "normal pending update must still be awaited");
    await clock.advance(1);
    assert.deepEqual({ status: verification.state.status, contextClosed: f.closed, serverClosed: f.serverClosed },
      { status: "rejected", contextClosed: true, serverClosed: true },
      "verification and cleanup must finish after the update deadline");
    assert.match(String(verification.state.error), /timeout|timed out|deadline/i);
    assert.equal(clock.pending, 0, "completed failure must leave no deadline timer");
  } finally {
    // Let the unchanged helper finish even when the RED assertion finds it pending.
    pending.resolve();
    await verification.finished;
  }
});

test("a never-resolving serviceWorker.ready shares the 15s Node deadline and cleans up", async () => {
  const clock = manualClock();
  const pending = deferred();
  const f = fixture({ clock, ready: pending.promise });
  const verification = observe(f.helpers.verifyStaleClientUpdate(f.browser, "94"));
  try {
    await clock.advance(14999);
    assert.equal(f.switchedController, "93", "real helper must reach ready/update first");
    assert.equal(verification.state.status, "pending");
    await clock.advance(1);
    assert.deepEqual({ status: verification.state.status, contextClosed: f.closed, serverClosed: f.serverClosed },
      { status: "rejected", contextClosed: true, serverClosed: true },
      "verification and cleanup must finish even when ready never resolves");
    assert.match(String(verification.state.error), /timeout|timed out|deadline/i);
    assert.equal(clock.pending, 0);
  } finally {
    pending.resolve(f.registration);
    await verification.finished;
  }
});

test("never-resolving diagnostics expire at 2s without replacing the original update error or cleanup", async () => {
  const clock = manualClock();
  const pending = deferred();
  const failure = new Error("synthetic original update rejection before hung diagnostics");
  const f = fixture({ clock, diagnostics: pending.promise, update: async () => { throw failure; } });
  const verification = observe(f.helpers.verifyStaleClientUpdate(f.browser, "94"));
  try {
    await clock.advance(1999);
    assert.equal(f.switchedController, "93", "real helper must attempt the update first");
    assert.equal(verification.state.status, "pending", "diagnostics retain their bounded opportunity");
    await clock.advance(1);
    assert.deepEqual({ status: verification.state.status, contextClosed: f.closed, serverClosed: f.serverClosed },
      { status: "rejected", contextClosed: true, serverClosed: true },
      "hung diagnostics must not leave original failure and cleanup pending");
    assert.equal(verification.state.error, failure);
    assert.ok(f.logs.includes('STALE_CLIENT_UPDATE_STATE {"unavailable":true}'));
    assert.equal(clock.pending, 0);
  } finally {
    pending.resolve(f.registration);
    await verification.finished;
  }
});

test("hung update and diagnostics finish at 17s with the original update timeout and cleanup", async () => {
  const clock = manualClock();
  const update = deferred();
  const diagnostics = deferred();
  const f = fixture({ clock, update: () => update.promise, diagnostics: diagnostics.promise });
  const verification = observe(f.helpers.verifyStaleClientUpdate(f.browser, "94"));
  try {
    await clock.advance(14999);
    assert.equal(f.switchedController, "93");
    assert.equal(verification.state.status, "pending");
    await clock.advance(1);
    assert.equal(verification.state.status, "pending", "diagnostics retain their separate 2s deadline");
    await clock.advance(1999);
    assert.equal(verification.state.status, "pending");
    await clock.advance(1);
    assert.deepEqual({ status: verification.state.status, contextClosed: f.closed, serverClosed: f.serverClosed },
      { status: "rejected", contextClosed: true, serverClosed: true });
    assert.match(String(verification.state.error), /STALE_CLIENT_UPDATE: timed out after 15000ms/);
    assert.doesNotMatch(String(verification.state.error), /STALE_CLIENT_UPDATE_DIAGNOSTICS/);
    assert.ok(f.logs.includes('STALE_CLIENT_UPDATE_STATE {"unavailable":true}'));
    assert.equal(clock.pending, 0);
  } finally {
    update.resolve();
    diagnostics.resolve(f.registration);
    await verification.finished;
  }
});

test("an update that resolves before its deadline still succeeds and clears all deadline timers", async () => {
  const clock = manualClock();
  const pending = deferred();
  const f = fixture({ clock, update: () => pending.promise });
  const verification = observe(f.helpers.verifyStaleClientUpdate(f.browser, "94"));
  try {
    await clock.advance(14999);
    assert.equal(verification.state.status, "pending");
    pending.resolve();
    await verification.finished;
    assert.equal(verification.state.status, "fulfilled");
    assert.equal(verification.state.value.updated.worker, "94");
    assert.equal(f.closed, true);
    assert.equal(f.serverClosed, true);
    assert.equal(clock.pending, 0, "successful verification must cancel its deadline timer");
  } finally {
    pending.resolve();
    await verification.finished;
  }
});
