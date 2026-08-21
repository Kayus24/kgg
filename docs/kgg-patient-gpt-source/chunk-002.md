# KGG Patient Source Chunk 002

- Source file: `service-worker.js`
- Characters: 1-7199
- Full source SHA-256: `08393115cb4c49927c39801a3052642aa01ab82b351b5d27a149657b015b91e1`

```
const CACHE_NAME = 'kgg-handyplan-v79-plan-rename';
const APP_VERSION = '79';
const CACHE_PREFIX = 'kgg-handyplan-';
const RECOVERY_PATH = './update-recovery.html';
const NUMPAD_UI_FIX_SCRIPT = './numpad-ui-fix.js?v=scroll-stable-1';
const VERSION_LABEL_SCRIPT = './patient-version-label.js?v=79';
const COLLAPSE_SCRIPT = './collapse-cards.js?v=plan-update-label-2-progress-visible';
const CARD_PROGRESS_SCRIPT = './patient-card-progress.js?v=card-progress-2-complete-fields';
const INSTALL_PROMPT_SCRIPT = './patient-install-prompt.js?v=install-prompt-1-shared-reference';
const PLAN_REPLACE_SLOT_SCRIPT = './patient-plan-replace-slot-fix.js?v=active-slot-1';
const START_SCAN_SCRIPT = './patient-start-scan.js?v=plan-replace-1';
const JSQR_SCRIPT = './vendor/jsqr-1.4.0.js';
const MULTIPLAN_DB_SCRIPT = './patient-multiplan-db.js?v=lossless-media-plans-1';
const PLAN_DELETE_SCRIPT = './patient-plan-delete.js?v=plan-delete-3-red-x-rename';
const CARD_SETTINGS_SCRIPT = './patient-card-settings.js?v=card-settings-2-no-thumb-padding';
const START_VALUES_SCRIPT = './patient-start-values-day1.js?v=start-values-day1-1';
const DAY_HISTORY_SCRIPT = './patient-day-history.js?v=plan-dialog-title-1';
const MEDIA_SCRIPT = './patient-media-retry-cache_v2.js?v=thumb-layout-2-safe-text';
const UI_MICRO_POLISH_SCRIPT = './patient-ui-micro-polish.js?v=unit-labels-pain-fit-1';
const PAIN_VERTICAL_SCRIPT = './patient-pain-vertical-scale.js?v=exercise-pain-vertical-2-compact-modal';
const INSTALL_GUIDE_SCRIPT = './patient-install-guide.js?v=install-guide-v2-query-plan-ios';
const NUMPAD_VISIBILITY_SCRIPT = './patient-numpad-visibility-fix.js?v=stay-open-switch-1';
const EXTRA_INFO_SCRIPT = './patient-extra-info-display.js?v=extra-info-filter-1';
const LAST_VALUE_HINTS_SCRIPT = './patient-last-value-hints.js?v=last-value-button-shimmer-1';
const SET_SUMMARY_GROUPS_SCRIPT = './patient-set-summary-groups.js?v=set-summary-groups-2-range-label';
const QR_FULLSCREEN_SCRIPT = './patient-qr-fullscreen.js?v=qr-fullscreen-1';
const NUMPAD_CARD_GUARD_SCRIPT = './patient-numpad-card-guard.js?v=numpad-input-switch-1';
const CORE_ASSETS = ['./index.html','./manifest.json','./manifest-v64.webmanifest','./kgg-icon-192-v63.png','./kgg-icon-512-v63.png'];
const APP_ASSETS = ['./','./kgg-icon-maskable-512-v63.png',NUMPAD_UI_FIX_SCRIPT,VERSION_LABEL_SCRIPT,COLLAPSE_SCRIPT,CARD_PROGRESS_SCRIPT,INSTALL_PROMPT_SCRIPT,PLAN_REPLACE_SLOT_SCRIPT,START_SCAN_SCRIPT,JSQR_SCRIPT,MULTIPLAN_DB_SCRIPT,PLAN_DELETE_SCRIPT,CARD_SETTINGS_SCRIPT,START_VALUES_SCRIPT,DAY_HISTORY_SCRIPT,MEDIA_SCRIPT,UI_MICRO_POLISH_SCRIPT,PAIN_VERTICAL_SCRIPT,INSTALL_GUIDE_SCRIPT,NUMPAD_VISIBILITY_SCRIPT,EXTRA_INFO_SCRIPT,LAST_VALUE_HINTS_SCRIPT,SET_SUMMARY_GROUPS_SCRIPT,QR_FULLSCREEN_SCRIPT,NUMPAD_CARD_GUARD_SCRIPT,'https://cdn.jsdelivr.net/npm/qrcode-generator@1.4.4/qrcode.js'];
function isIndexRequest(request){const url=new URL(request.url);if(url.origin!==self.location.origin)return false;return url.pathname.endsWith('/kgg/')||url.pathname.endsWith('/kgg/index.html')}
function isRecoveryRequest(request){const url=new URL(request.url);if(url.origin!==self.location.origin)return false;return url.pathname.endsWith('/kgg/update-recovery.html')}
function injectModules(response){return response}
self.addEventListener('install',event=>{event.waitUntil((async()=>{const cache=await caches.open(CACHE_NAME);await cache.addAll(CORE_ASSETS);await Promise.allSettled(APP_ASSETS.map(asset=>cache.add(asset)))})())});
self.addEventListener('message',event=>{const data=event.data||{};if(data.type==='SKIP_WAITING'){event.waitUntil(self.skipWaiting());return}if(data.type==='GET_APP_VERSION'&&event.ports&&event.ports[0]){event.ports[0].postMessage({type:'APP_VERSION',version:APP_VERSION});return}if(data.type==='GET_UPDATE_DIAGNOSTICS'&&event.ports&&event.ports[0]){event.ports[0].postMessage({type:'UPDATE_DIAGNOSTICS',version:APP_VERSION,cacheName:CACHE_NAME,scope:self.registration.scope,recoveryPath:RECOVERY_PATH})}});
self.addEventListener('activate',event=>{event.waitUntil(caches.keys().then(keys=>Promise.all(keys.filter(key=>key.startsWith(CACHE_PREFIX)&&key!==CACHE_NAME).map(key=>caches.delete(key)))).then(()=>self.clients.claim()))});
self.addEventListener('fetch',event=>{if(event.request.method!=='GET')return;if(isRecoveryRequest(event.request)){event.respondWith(fetch(event.request,{cache:'no-store'}));return}if(isIndexRequest(event.request)){event.respondWith(fetch(event.request,{cache:'no-store'}).then(async response=>{const copy=response.clone();caches.open(CACHE_NAME).then(cache=>cache.put('./index.html',copy)).catch(()=>{});return injectModules(response)}).catch(async()=>{const cached=await caches.match('./index.html');return cached?injectModules(cached):Response.error()}));return}const url=new URL(event.request.url);if(url.pathname.endsWith('/manifest.json')||url.pathname.endsWith('/manifest-v64.webmanifest')||url.pathname.endsWith('/kgg-icon-192-v63.png')||url.pathname.endsWith('/kgg-icon-512-v63.png')||url.pathname.endsWith('/kgg-icon-maskable-512-v63.png')){event.respondWith(fetch(event.request,{cache:'no-store'}).then(response=>{const copy=response.clone();caches.open(CACHE_NAME).then(cache=>cache.put(event.request,copy)).catch(()=>{});return response}).catch(()=>caches.match(event.request)));return}if(url.pathname.endsWith('/collapse-cards.js')||url.pathname.endsWith('/patient-card-progress.js')||url.pathname.endsWith('/patient-install-prompt.js')||url.pathname.endsWith('/patient-plan-replace-slot-fix.js')||url.pathname.endsWith('/patient-plan-delete.js')||url.pathname.endsWith('/numpad-ui-fix.js')||url.pathname.endsWith('/patient-version-label.js')||url.pathname.endsWith('/patient-start-scan.js')||url.pathname.endsWith('/patient-multiplan-db.js')||url.pathname.endsWith('/patient-card-settings.js')||url.pathname.endsWith('/patient-start-values-day1.js')||url.pathname.endsWith('/patient-day-history.js')||url.pathname.endsWith('/patient-media-retry-cache_v2.js')||url.pathname.endsWith('/patient-ui-micro-polish.js')||url.pathname.endsWith('/patient-pain-vertical-scale.js')||url.pathname.endsWith('/patient-install-guide.js')||url.pathname.endsWith('/patient-numpad-visibility-fix.js')||url.pathname.endsWith('/patient-extra-info-display.js')||url.pathname.endsWith('/patient-last-value-hints.js')||url.pathname.endsWith('/patient-set-summary-groups.js')||url.pathname.endsWith('/patient-qr-fullscreen.js')||url.pathname.endsWith('/patient-numpad-card-guard.js')){event.respondWith(fetch(event.request,{cache:'no-store'}).then(response=>{const copy=response.clone();caches.open(CACHE_NAME).then(cache=>cache.put(event.request,copy)).catch(()=>{});return response}).catch(()=>caches.match(event.request)));return}event.respondWith(caches.match(event.request).then(cached=>{if(cached){fetch(event.request).then(response=>{const copy=response.clone();caches.open(CACHE_NAME).then(cache=>cache.put(event.request,copy)).catch(()=>{})}).catch(()=>{});return cached}return fetch(event.request).then(response=>{const copy=response.clone();caches.open(CACHE_NAME).then(cache=>cache.put(event.request,copy)).catch(()=>{});return response}).catch(()=>caches.match('./index.html'))}))});
```
