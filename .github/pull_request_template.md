## Scope

- Surface: <!-- patient / therapist-admin / android / tooling-release / docs / shared contract -->
- Canonical source:
- User-visible behavior change: <!-- yes/no + short description -->
- Related PAT IDs / contracts: <!-- if applicable -->

## What changed

<!-- Keep this narrow. Separate unrelated cleanup/refactors. -->

## Safety boundaries

- [ ] Patient / therapist-admin boundary preserved.
- [ ] No new secret, credential, API-key, or patient-data exposure.
- [ ] No unintended storage / QR / PWA / Service Worker / Android contract change.
- [ ] Generated or historical artifacts were not used as the patch source.
- [ ] Fresh base/main state was checked before the change.

## Tests / evidence

Focused:
- [ ] <!-- command + result -->

Required broader gate:
- [ ] `cmd /c release-pipeline\run-kgg-tests.cmd --level critical`

For UI/HTML/layout:
- [ ] `cmd /c release-pipeline\run-kgg-tests.cmd --suite ui-stability --level regression`

Preview / real device:
- [ ] not required
- [ ] required and attached/described below

Evidence:
<!-- run links, screenshots/recordings, device/browser, known limitations -->

## Rollback

<!-- How to return to the known-good behavior without data migration or contract drift. -->

## Status

<!-- PASS / PARTIAL / BLOCKED / WAITING. Do not mark PASS without evidence. -->
