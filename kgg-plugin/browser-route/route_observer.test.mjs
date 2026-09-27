import test from "node:test";
import assert from "node:assert/strict";
import { createRouteObserver, HEARTBEAT_ALARM, observationFromTab } from "./route_observer.mjs";

class FakeEvent {
  listeners = [];
  addListener(fn) { this.listeners.push(fn); }
  fire(...args) { this.listeners.forEach(fn => fn(...args)); }
}

function fakeChrome(initialTab) {
  let activeTab = initialTab;
  const calls = [];
  const api = {
    tabs: {
      query: async query => {
        calls.push(query);
        return activeTab ? [activeTab] : [];
      },
      onActivated: new FakeEvent(),
      onUpdated: new FakeEvent(),
    },
    windows: {
      WINDOW_ID_NONE: -1,
      onFocusChanged: new FakeEvent(),
    },
    runtime: {
      onStartup: new FakeEvent(),
      onInstalled: new FakeEvent(),
    },
    alarms: {
      created: [],
      create(name, options) { this.created.push({ name, options }); },
      onAlarm: new FakeEvent(),
    },
  };
  return {
    api,
    calls,
    setActiveTab(tab) { activeTab = tab; },
  };
}

const tick = () => new Promise(resolve => setTimeout(resolve, 0));

test("observationFromTab canonicalizes a direct ChatGPT chat", () => {
  assert.deepEqual(
    observationFromTab({ url: "https://chatgpt.com/c/abc?x=1" }, 10),
    {
      schema: "kgg-chatgpt-browser-route/v1",
      state: "verified",
      canonical_url: "https://chatgpt.com/c/abc",
      observed_at: 10,
    }
  );
});
test("start publishes active chat and deduplicates replay", async () => {
  const fake = fakeChrome({ active: true, url: "https://chatgpt.com/c/a" });
  const emitted = [];
  const observer = createRouteObserver(fake.api, {
    emit: async value => emitted.push(value),
    now: () => 100,
  });
  observer.start();
  await tick();

  assert.equal(emitted.length, 1);
  assert.equal(emitted[0].canonical_url, "https://chatgpt.com/c/a");
  await observer.refresh();
  assert.equal(emitted.length, 1);
  assert.deepEqual(fake.calls[0], { active: true, lastFocusedWindow: true });
});

test("active ChatGPT navigation updates the verified route", async () => {
  const fake = fakeChrome({ active: true, url: "https://chatgpt.com/c/a" });
  const emitted = [];
  const observer = createRouteObserver(fake.api, { emit: async v => emitted.push(v) });
  observer.start();
  await tick();

  fake.setActiveTab({ active: true, url: "https://chatgpt.com/c/b" });
  fake.api.tabs.onUpdated.fire(1, { url: "https://chatgpt.com/c/b" }, { active: true });
  await tick();

  assert.equal(emitted.at(-1).canonical_url, "https://chatgpt.com/c/b");
});
test("ChatGPT home or non-ChatGPT active tab clears the candidate", async () => {
  const fake = fakeChrome({ active: true, url: "https://chatgpt.com/c/a" });
  const emitted = [];
  const observer = createRouteObserver(fake.api, { emit: async v => emitted.push(v) });
  observer.start();
  await tick();

  fake.setActiveTab({ active: true, url: "https://chatgpt.com/" });
  fake.api.tabs.onUpdated.fire(1, { url: "https://chatgpt.com/" }, { active: true });
  await tick();
  assert.equal(emitted.at(-1).state, "unavailable");

  fake.setActiveTab({ active: true });
  fake.api.tabs.onActivated.fire({ tabId: 2, windowId: 1 });
  await tick();
  assert.equal(emitted.at(-1).state, "unavailable");
});

test("background tab updates never overwrite the active route", async () => {
  const fake = fakeChrome({ active: true, url: "https://chatgpt.com/c/a" });
  const emitted = [];
  const observer = createRouteObserver(fake.api, { emit: async v => emitted.push(v) });
  observer.start();
  await tick();

  fake.api.tabs.onUpdated.fire(99, { url: "https://chatgpt.com/c/wrong" }, { active: false });
  await tick();

  assert.equal(emitted.length, 1);
  assert.equal(emitted[0].canonical_url, "https://chatgpt.com/c/a");
});
test("losing browser focus fails closed", async () => {
  const fake = fakeChrome({ active: true, url: "https://chatgpt.com/c/a" });
  const emitted = [];
  const observer = createRouteObserver(fake.api, { emit: async v => emitted.push(v) });
  observer.start();
  await tick();

  fake.api.windows.onFocusChanged.fire(-1);
  await tick();

  assert.equal(emitted.at(-1).state, "unavailable");
  assert.equal(emitted.at(-1).canonical_url, null);
});

test("irrelevant active-tab update is a noop", async () => {
  const fake = fakeChrome({ active: true, url: "https://chatgpt.com/c/a" });
  const emitted = [];
  const observer = createRouteObserver(fake.api, { emit: async v => emitted.push(v) });
  observer.start();
  await tick();

  fake.api.tabs.onUpdated.fire(1, { audible: true }, { active: true });
  await tick();
  assert.equal(emitted.length, 1);
});

test("heartbeat refreshes unchanged active route", async () => {
  let now = 1_000;
  const fake = fakeChrome({ active: true, url: "https://chatgpt.com/c/a" });
  const emitted = [];
  const observer = createRouteObserver(fake.api, {
    emit: async value => emitted.push(value),
    now: () => now,
  });
  observer.start();
  await tick();

  assert.deepEqual(fake.api.alarms.created, [
    { name: HEARTBEAT_ALARM, options: { periodInMinutes: 0.5 } },
  ]);
  assert.equal(emitted.length, 1);

  now = 31_000;
  fake.api.alarms.onAlarm.fire({ name: HEARTBEAT_ALARM });
  await tick();

  assert.equal(emitted.length, 2);
  assert.equal(emitted[1].canonical_url, "https://chatgpt.com/c/a");
  assert.equal(emitted[1].observed_at, 31_000);
});
