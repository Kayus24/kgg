(function () {
  "use strict";

  var backend = window.localStorage;
  var ACTIVE_SESSION_KEY = "kgg_device_test_active_session_v404";
  var PREFIX_ROOT = "kgg_device_test_v404:";
  var SESSION_RE = /^kgg-test-[a-f0-9]{32}$/;

  function sessionFromPairing() {
    try {
      var token = new URLSearchParams(location.search).get("kggTest") || "";
      var match = /^KGGTEST1:([A-Za-z0-9_-]{1,4096})$/.exec(token);
      if (!match) return "";
      var value = match[1].replace(/-/g, "+").replace(/_/g, "/");
      while (value.length % 4) value += "=";
      var parsed = JSON.parse(decodeURIComponent(escape(atob(value))));
      return SESSION_RE.test(String(parsed && parsed.sessionId || "")) ? parsed.sessionId : "";
    } catch (error) {
      return "";
    }
  }

  var pairedSession = sessionFromPairing();
  var storedSession = backend.getItem(ACTIVE_SESSION_KEY) || "";
  var sessionId = pairedSession || (SESSION_RE.test(storedSession) ? storedSession : "unpaired");
  if (pairedSession) {
    backend.setItem(ACTIVE_SESSION_KEY, pairedSession);
    var keepPrefix = PREFIX_ROOT + pairedSession + ":";
    var stale = [];
    for (var staleIndex = 0; staleIndex < backend.length; staleIndex += 1) {
      var staleKey = backend.key(staleIndex) || "";
      if (staleKey.indexOf(PREFIX_ROOT) === 0 && staleKey.indexOf(keepPrefix) !== 0) stale.push(staleKey);
    }
    stale.forEach(function (key) { backend.removeItem(key); });
  }
  var prefix = PREFIX_ROOT + sessionId + ":";

  function cleanKey(key) {
    var value = String(key == null ? "" : key);
    if (!value || value.length > 240) throw new Error("device_test_storage_key_invalid");
    return value;
  }
  function logicalKeys() {
    var values = [];
    for (var index = 0; index < backend.length; index += 1) {
      var key = backend.key(index) || "";
      if (key.indexOf(prefix) === 0) values.push(key.slice(prefix.length));
    }
    return values.sort();
  }

  var api = {
    getItem: function (key) { return backend.getItem(prefix + cleanKey(key)); },
    setItem: function (key, value) { backend.setItem(prefix + cleanKey(key), String(value)); },
    removeItem: function (key) { backend.removeItem(prefix + cleanKey(key)); },
    clear: function () { logicalKeys().forEach(function (key) { backend.removeItem(prefix + key); }); },
    key: function (index) { return logicalKeys()[Math.max(0, Number(index) || 0)] || null; }
  };
  Object.defineProperty(api, "length", { enumerable: false, configurable: true, get: function () { return logicalKeys().length; } });

  var storage = new Proxy(api, {
    get: function (target, property) {
      if (typeof property === "symbol" || property in target) return Reflect.get(target, property);
      return target.getItem(property);
    },
    set: function (target, property, value) {
      if (property in target) return Reflect.set(target, property, value);
      target.setItem(property, value);
      return true;
    },
    deleteProperty: function (target, property) {
      if (property in target) return false;
      target.removeItem(property);
      return true;
    },
    ownKeys: function () { return logicalKeys(); },
    getOwnPropertyDescriptor: function (target, property) {
      if (property in target) return Object.getOwnPropertyDescriptor(target, property);
      if (target.getItem(property) === null) return undefined;
      return { enumerable: true, configurable: true, writable: true, value: target.getItem(property) };
    }
  });

  Object.defineProperty(window, "KGGDeviceTestStorage", {
    value: storage,
    configurable: false,
    enumerable: false,
    writable: false
  });
})();
