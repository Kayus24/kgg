const CACHE_NAME = 'kgg-handyplan-v6-numpad-ui-fix';
const COLLAPSE_SCRIPT = './collapse-cards.js';
const NUMPAD_UI_FIX = './numpad-ui-fix.js';
const APP_ASSETS = [
  './',
  './index.html',
  './manifest.json',
  './icon.svg',
  COLLAPSE_SCRIPT,
  NUMPAD_UI_FIX,
  'https://cdn.jsdelivr.net/npm/qrcode-generator@1.4.4/qrcode.js'
];

function isIndexRequest(request) {
  const url = new URL(request.url);
  if (url.origin !== self.location.origin) return false;
  return url.pathname.endsWith('/kgg/') || url.pathname.endsWith('/kgg/index.html');
}

async function injectModules(response) {
  try {
    let html = await response.clone().text();
    if (!html.includes('collapse-cards.js')) {
      html = html.replace('</body>', '<script src="./collapse-cards.js"></script></body>');
    }
    if (!html.includes('numpad-ui-fix.js')) {
      html = html.replace('</body>', '<script src="./numpad-ui-fix.js"></script></body>');
    }
    return new Response(html, {
      status: response.status,
      statusText: response.statusText,
      headers: {
        'Content-Type': 'text/html; charset=utf-8',
        'Cache-Control': 'no-cache'
      }
    });
  } catch (e) {
    return response;
  }
}

self.addEventListener('install', event => {
  event.waitUntil(
    caches.open(CACHE_NAME)
      .then(cache => cache.addAll(APP_ASSETS))
      .then(() => self.skipWaiting())
  );
});

self.addEventListener('activate', event => {
  event.waitUntil(
    caches.keys().then(keys => Promise.all(
      keys.filter(key => key !== CACHE_NAME).map(key => caches.delete(key))
    )).then(async () => {
      await self.clients.claim();
      const clients = await self.clients.matchAll({ type: 'window', includeUncontrolled: true });
      clients.forEach(client => client.postMessage({ type: 'APP_UPDATE_READY' }));
    })
  );
});

self.addEventListener('fetch', event => {
  if (event.request.method !== 'GET') return;

  if (isIndexRequest(event.request)) {
    event.respondWith(
      fetch(event.request, { cache: 'no-store' })
        .then(async response => {
          const copy = response.clone();
          caches.open(CACHE_NAME).then(cache => cache.put('./index.html', copy)).catch(() => {});
          return injectModules(response);
        })
        .catch(async () => {
          const cached = await caches.match('./index.html');
          return cached ? injectModules(cached) : Response.error();
        })
    );
    return;
  }

  event.respondWith(
    caches.match(event.request).then(cached => {
      if (cached) {
        fetch(event.request)
          .then(response => {
            const copy = response.clone();
            caches.open(CACHE_NAME).then(cache => cache.put(event.request, copy)).catch(() => {});
          })
          .catch(() => {});
        return cached;
      }
      return fetch(event.request)
        .then(response => {
          const copy = response.clone();
          caches.open(CACHE_NAME).then(cache => cache.put(event.request, copy)).catch(() => {});
          return response;
        })
        .catch(() => caches.match('./index.html'));
    })
  );
});
