import test from "node:test";
import assert from "node:assert/strict";
import { sendRouteObservation } from "./native_bridge.mjs";

const observation = {
  schema: "kgg-chatgpt-browser-route/v1",
  state: "verified",
  canonical_url: "https://chatgpt.com/c/abc",
  observed_at: 1,
};

test("native bridge accepts host ack", async () => {
  const chromeApi = {
    runtime: { sendNativeMessage: async () => ({ ok: true }) },
  };
  assert.deepEqual(await sendRouteObservation(chromeApi, observation), { ok: true });
});

test("native bridge contains host rejection", async () => {
  const chromeApi = {
    runtime: { sendNativeMessage: async () => ({ ok: false, error: "bad" }) },
  };
  assert.deepEqual(
    await sendRouteObservation(chromeApi, observation),
    { ok: false, error: "native_host_rejected" }
  );
});

test("native bridge contains missing host", async () => {
  const chromeApi = {
    runtime: { sendNativeMessage: async () => { throw new Error("missing"); } },
  };
  assert.deepEqual(
    await sendRouteObservation(chromeApi, observation),
    { ok: false, error: "native_host_unavailable" }
  );
});
