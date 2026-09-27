import { canonicalChatgptUrl } from "./url_contract.mjs";

export const OBSERVATION_SCHEMA = "kgg-chatgpt-browser-route/v1";
export const HEARTBEAT_ALARM = "kgg-chatgpt-route-heartbeat";

export function observationFromTab(tab, observedAt) {
  const canonicalUrl = canonicalChatgptUrl(tab?.url ?? tab?.pendingUrl ?? null);
  return {
    schema: OBSERVATION_SCHEMA,
    state: canonicalUrl ? "verified" : "unavailable",
    canonical_url: canonicalUrl,
    observed_at: observedAt,
  };
}

export function createRouteObserver(chromeApi, options) {
  const emit = options.emit;
  const now = options.now ?? (() => Date.now());
  let lastKey = null;
  let current = null;

  async function publish(next, { force = false } = {}) {
    const key = `${next.state}|${next.canonical_url ?? ""}`;
    current = next;
    if (!force && key === lastKey) return false;
    lastKey = key;
    await emit(next);
    return true;
  }
  async function refresh({ force = false } = {}) {
    const tabs = await chromeApi.tabs.query({
      active: true,
      lastFocusedWindow: true,
    });
    return publish(observationFromTab(tabs[0], now()), { force });
  }

  async function clear() {
    return publish(observationFromTab(null, now()));
  }

  function onActivated() {
    void refresh();
  }

  function onUpdated(_tabId, changeInfo, tab) {
    if (!tab?.active) return;
    if (
      changeInfo.url === undefined &&
      changeInfo.status !== "loading" &&
      changeInfo.status !== "complete"
    ) {
      return;
    }
    void refresh();
  }
  function onFocusChanged(windowId) {
    if (windowId === chromeApi.windows.WINDOW_ID_NONE) {
      void clear();
      return;
    }
    void refresh();
  }

  function start() {
    chromeApi.tabs.onActivated.addListener(onActivated);
    chromeApi.tabs.onUpdated.addListener(onUpdated);
    chromeApi.windows.onFocusChanged.addListener(onFocusChanged);
    chromeApi.runtime.onStartup.addListener(() => void refresh({ force: true }));
    chromeApi.runtime.onInstalled.addListener(() => void refresh({ force: true }));
    if (chromeApi.alarms) {
      chromeApi.alarms.create(HEARTBEAT_ALARM, { periodInMinutes: 0.5 });
      chromeApi.alarms.onAlarm.addListener(alarm => {
        if (alarm?.name === HEARTBEAT_ALARM) {
          void refresh({ force: true });
        }
      });
    }
    void refresh({ force: true });
  }

  return {
    start,
    refresh,
    clear,
    current: () => current,
  };
}
