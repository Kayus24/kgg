#!/usr/bin/env node
"use strict";

// Exercise the actual worker fetch handler without a second browser harness.
const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");
const vm = require("node:vm");
const crypto = require("node:crypto");
const root = path.resolve(__dirname, "..");
const scriptUrl = "https://cdn.jsdelivr.net/npm/qrcode-generator@1.4.4/qrcode.js";
const indexBytes = fs.readFileSync(path.join(root, "index.html"));
const workerBytes = fs.readFileSync(path.join(root, "service-worker.js"));
const sha = bytes => crypto.createHash("sha256").update(bytes).digest("hex");

async function dispatch({networkFails, cachedIndex, destination = "script", mode = "no-cors"}) {
  const handlers = {}, cacheLookups = [];
  const requestUrl = mode === "navigate" ? "http://127.0.0.1:8765/" : scriptUrl;
  const cache = {put: async () => {}};
  const context = {
    URL, Response,
    self: {
      location: {origin: "http://127.0.0.1:8765"},
      addEventListener: (name, handler) => { handlers[name] = handler; }
    },
    fetch: async () => {
      if (networkFails) throw new TypeError("injected offline fetch");
      return new Response("globalThis.syntheticQrLoaded = true;", {
        headers: {"Content-Type": "text/javascript"}
      });
    },
    caches: {
      open: async () => cache,
      match: async key => {
        cacheLookups.push(typeof key === "string" ? key : key.url);
        if (key === "./index.html" && cachedIndex) {
          return new Response(indexBytes, {headers: {"Content-Type": "text/html; charset=utf-8"}});
        }
      }
    }
  };
  vm.runInNewContext(workerBytes.toString("utf8"), context, {filename: "service-worker.js"});
  let result;
  handlers.fetch({
    request: {url: requestUrl, method: "GET", destination, mode},
    respondWith: promise => { result = promise; }
  });
  return {response: await result, cacheLookups};
}

(async () => {
  for (const destination of ["script", "style", "image", ""]) {
    const failed = await dispatch({networkFails: true, cachedIndex: true, destination});
    assert.equal(failed.response.type, "error", destination);
    assert.equal(failed.response.status, 0, destination);
    assert.equal(failed.response.headers.get("content-type"), null, destination);
    assert.equal(await failed.response.text(), "", destination);
    assert.deepEqual(failed.cacheLookups, [scriptUrl], destination);
  }

  const navigation = await dispatch({networkFails: true, cachedIndex: true, destination: "document", mode: "navigate"});
  assert.equal(navigation.response.status, 200);
  assert.match(navigation.response.headers.get("content-type"), /^text\/html/);
  assert.equal(sha(Buffer.from(await navigation.response.text())), sha(indexBytes));
  assert.deepEqual(navigation.cacheLookups, ["http://127.0.0.1:8765/", "./index.html"]);

  const success = await dispatch({networkFails: false, cachedIndex: true});
  assert.equal(success.response.headers.get("content-type"), "text/javascript");
  new vm.Script(await success.response.text());
  assert.deepEqual(success.cacheLookups, [scriptUrl]);

  const missing = await dispatch({networkFails: true, cachedIndex: false, destination: "document", mode: "navigate"});
  assert.equal(missing.response, undefined);
  console.log(JSON.stringify({
    status: "PASS", mode: "service_worker_vm_regression", cases: 7,
    request: {url: scriptUrl, destination: "script"},
    fallback: {navigation_only: true, body_sha256: sha(indexBytes)},
    worker_sha256: sha(workerBytes),
    controls: ["script_style_image_fetch_fail_without_html", "navigation_keeps_cached_html", "successful_fetch_returns_javascript", "missing_index_does_not_invent_html"],
    upstream_failure_reason: "INJECTED_ONLY_NOT_ESTABLISHED_FOR_HISTORICAL_BROWSER"
  }, null, 2));
})().catch(error => { console.error(error); process.exitCode = 1; });
