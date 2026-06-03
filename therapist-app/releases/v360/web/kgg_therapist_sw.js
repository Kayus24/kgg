const KGG_SW_VERSION = 'kgg-therapist-v360-sync-bundle-qr';
const KGG_CACHE = KGG_SW_VERSION + '-app-shell';
const KGG_SHELL = [
  './',
  './KGG_APP_ADMIN_v360_sync_bundle_qr.html',
  './KGG_APP_KOLLEGEN_v360_sync_bundle_qr.html',
  './kgg_therapist_manifest.webmanifest',
  './kgg_therapist_icon.svg'
];

self.addEventListener('install', event => {
  event.waitUntil(
    caches.open(KGG_CACHE)
      .then(cache => cache.addAll(KGG_SHELL))
      .then(() => self.skipWaiting())
  );
});

self.addEventListener('activate', event => {
  event.waitUntil(
    caches.keys()
      .then(keys => Promise.all(keys.filter(key => key.startsWith('kgg-therapist-') && key !== KGG_CACHE).map(key => caches.delete(key))))
      .then(() => self.clients.claim())
  );
});

self.addEventListener('fetch', event => {
  const request = event.request;
  if (request.method !== 'GET') return;
  event.respondWith(
    fetch(request)
      .then(response => {
        const copy = response.clone();
        caches.open(KGG_CACHE).then(cache => cache.put(request, copy)).catch(() => {});
        return response;
      })
      .catch(() => caches.match(request).then(cached => cached || caches.match('./KGG_APP_KOLLEGEN_v360_sync_bundle_qr.html')))
  );
});
