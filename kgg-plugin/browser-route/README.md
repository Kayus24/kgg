# KGG ChatGPT browser route

Minimal local bridge for binding the active ChatGPT conversation URL to the
existing project-status checkpoint without exporting `openai/session`.

## Security boundary

The MV3 extension has only:
- `nativeMessaging`
- `alarms`
- host access to `https://chatgpt.com/*`

It has no content script and no `tabs`, `cookies`, `history`, `debugger`,
`storage`, `scripting`, or `<all_urls>` permission. It emits only the
canonical active `https://chatgpt.com/c/<id>` route or `unavailable`.

The manifest key pins extension ID:
`hpamfcbdlakklemljchpkfinmakjeada`.

## Local install

1. Load this directory as an unpacked extension in Chrome.
2. Run once in PowerShell:
   `powershell -NoProfile -ExecutionPolicy Bypass -File .\install_native_host.ps1`
3. Restart/reload the extension.

Dry-run without writes:
`powershell -NoProfile -ExecutionPolicy Bypass -File .\install_native_host.ps1 -PlanOnly`

Uninstall:
`powershell -NoProfile -ExecutionPolicy Bypass -File .\uninstall_native_host.ps1`

## Data flow

`active ChatGPT tab URL -> MV3 service worker -> Native Messaging -> local JSON state -> project_status_checkpoint`

The native host writes only:
- schema
- state
- canonical_url
- observed_at

No prompt, response, page DOM, cookie, history, auth token, or ChatGPT backend API
is part of this path.

## Test provenance

Implementation patterns were checked against:
- GoogleChrome/chrome-extensions-samples nativeMessaging sample
- dialoguesai/chatgpt-shadow-extension URL fixtures
- whg517/browser-bridge Native Messaging lifecycle/security model
- siraht/ChatGPTExporter extension validation patterns

No upstream project is vendored wholesale.
