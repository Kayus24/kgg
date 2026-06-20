# 2026-06-20 – v011 Tablet-Layout nach Rollback weiter kaputt wegen versionCode/Cache

## Triage
Mini-Patch / UI-Flow / Source-of-Truth-Entscheidung.

## Problem
Nach dem v011-Update war das Tablet-Layout sichtbar kaputt. Der direkte Rollback auf den Stand vor v011 stellte `kgg-update/index.html` und `kgg-update/version.json` zwar im Repository wieder her, die installierte App zeigte aber weiter den kaputten v011-Stand.

Sichtbar in der App:
- Toast: `KGG Update: aktuell (1.0.9-restore-lkg-qr-gallery-decode)`
- Tablet-Layout blieb kaputt, obwohl `main` bereits auf den Stand vor v011 zurückgesetzt war.

## Betroffene Version/Datei
- Kaputte Version: `1.0.9-restore-lkg-qr-gallery-decode`
- Vorher guter Stand: `1.0.7-patch-retention-changelog-guard`
- Betroffene Dateien im Ablauf:
  - `kgg-update/index.html`
  - `kgg-update/version.json`
  - `update-inbox/patch.py`
  - `update-inbox/release.json`

## Reproduktion
1. v011 über Update-Inbox ausrollen.
2. Tablet-App öffnen.
3. Tablet-Layout ist kaputt.
4. Repo auf Commit vor v011 zurücksetzen.
5. App erneut öffnen.
6. App bleibt trotzdem auf v011, weil lokaler Updater/Cache den vorher gesehenen `versionCode` nicht durch niedrigeren Code ersetzt.

## Ursache
Der Rollback im Repository war korrekt, aber die installierte App hatte lokal bereits `versionCode 10` / `1.0.9-restore-lkg-qr-gallery-decode` gesehen.

Der zurückgesetzte Manifest-Stand hatte wieder `versionCode 9`. Dadurch nahm die App den Rollback nicht als neues Update an oder blieb durch Service-Worker/WebView-Cache auf der kaputten Datei.

Kurz: Bei PWA/WebView-Updates darf ein Rollback nicht einfach einen niedrigeren `versionCode` verwenden. Ein Rollback muss als neues Update mit höherem `versionCode` ausgeliefert werden.

## Lösung/Fix
1. Kaputten v011-Stand gesichert:
   - Branch: `backup/broken-v011-before-rollback`
2. `main` zuerst auf den Commit vor v011 zurückgesetzt:
   - guter Stand: `c2a259cca21c3681b56f3933fc0977efcd465fac`
3. Danach `kgg-update/version.json` erneut erhöht, damit die installierte App den guten Stand wieder lädt:
   - `versionCode`: `20`
   - `versionName`: `1.0.20-stable`
   - `indexUrl`: `index.html?v=20`
   - `sha256`: `ff81621997d2007fdb776c71688c4dfc1b2d052439efeead796cf98cee888eb1`

## Test / Abnahmekriterien
- [x] Tablet-App komplett schließen.
- [x] App neu öffnen.
- [x] App lädt nicht mehr den kaputten v011-Stand.
- [x] Tablet-Layout funktioniert wieder laut Max-Screenshot/Rückmeldung.
- [ ] Galerie-QR separat neu testen, wenn ein neuer QR-Fix vorbereitet wird.
- [ ] Kamera-Scan separat neu testen, wenn ein neuer QR-Fix vorbereitet wird.

## Nicht anfassen
- PDF
- QR-Erzeugung
- Patienten-App
- Scan-Kamera
- Parser
- Android-Wrapper
- Tablet-Layout
- Plan-State
- Storage

## Regel für zukünftige Rollbacks
Wenn eine installierte PWA/WebView-App bereits eine kaputte Version gesehen hat, muss ein Rollback als neues Update ausgeliefert werden:

- `versionCode` höher als die kaputte Version setzen.
- `indexUrl` mit Cache-Buster ausliefern, z. B. `index.html?v=<neuerCode>`.
- `sha256` muss zur tatsächlich ausgelieferten guten `index.html` passen.
- Nicht nur GitHub-Commit zurücksetzen und `versionCode` senken.

## Folge-Risiken
- Service Worker / WebView / PWA-Cache kann alte HTML weiter halten.
- Direkter Rollback auf niedrigeren `versionCode` wirkt lokal nicht zuverlässig.
- Update-Inbox-Patches können trotz Repo-Rollback in installierten Apps sichtbar bleiben, bis ein höherer Manifest-Code ausgeliefert wird.

## Merksatz
Rollback für installierte App = alter guter Code + neuer höherer `versionCode` + Cache-Buster.
