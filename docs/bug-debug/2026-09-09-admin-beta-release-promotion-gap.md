# KGG-Ticket: Source-Merge wird nicht automatisch in der Admin-Beta sichtbar

Ticket-Metadaten: v1
Lifecycle: open
Evidence: PR #201, Main-SHA 4b16bab972d2ec029e41496e838c6a955a3b6cb6, v084, r0426/v065
Dependencies: none
Realtest: open
Last-Checked: 2026-09-09
Next-Action: Einen aktuellen Admin-Beta-Release aus dem geprüften Main-Stand über den vorgesehenen Release-Gate erzeugen und danach die Manifest-/Live-URL-Prüfung automatisieren.

## Problem

Ein erfolgreich nach `main` gemergter Admin-/Cockpit-Patch wird nicht automatisch in der installierten Admin-Beta-App sichtbar. Die normale Admin-Beta-App lädt ein unveränderliches Web-Artefakt aus dem kanonischen Update-Manifest. Ein Merge in `main` aktualisiert dieses Artefakt nicht automatisch.

Im betroffenen Fall ist der Cockpit-Startlink in `kgg-update` v084 enthalten. Die installierte Admin-Beta-App zeigt jedoch weiterhin Release `r0426` mit Version `1.0.65-source-control-char-guard`. Das Manifest verweist auf `therapist-app/releases/web/r0426/admin.html`; dort fehlt der v084-Button.

## Ursache

PR #201 trug bewusst das Label `kgg-no-release`. Dieses Label erlaubt einen Source-/Preview-Stand, ohne einen neuen Admin-Beta-Release vorzubereiten. Das Label ist keine Release-Freigabe. Dadurch waren Source und Test-Harness aktuell, während das unveränderliche Admin-Beta-Artefakt bei `r0426` blieb.

Ein erster Inbox-Kandidat für `r0427` wurde als PR #203 aus einem inzwischen veralteten Main-Stand erzeugt. Der Required Gate konnte die Prüfung wegen fehlender gemeinsamer Basis nach einem zwischenzeitlichen Main-Update nicht durchführen. Der Release-Weg muss deshalb den geprüften Main-SHA beim Erzeugen und beim Gate festhalten und bei SHA-Drift fail-closed einen neuen Kandidaten verlangen.

## Gewünschtes Verhalten

1. Nach einem Source-/Preview-Merge wird sichtbar ausgewiesen, dass die Admin-Beta noch auf dem letzten unveränderlichen Release steht.
2. Nach akzeptierter Test-App wird der Admin-Beta-Release ausschließlich über den vorgesehenen Gate-/Inbox-Weg erzeugt.
3. `therapist-app/android_update_manifest.json` bleibt die kanonische Quelle; `kgg_update_manifest.json` wird daraus deterministisch projiziert. Keine manuellen Manifest-Edits.
4. Vor dem Release werden Source-SHA, Release-ID, Version, Admin-HTML-Hash und Test-App-Stand zusammen geprüft.
5. Wenn sich `main` zwischen Kandidat und Gate ändert, wird der Kandidat automatisch verworfen oder sauber neu vom aktuellen `main` erzeugt; kein „no merge base“-Halbzustand.

## Akzeptanzkriterien

- [ ] Ein expliziter Admin-Beta-Release-Schritt zeigt vorab Source-Version und aktuell live geschaltetes `rNNNN`.
- [ ] Ein neuer Release wird nur nach der autorisierten Freigabe `Gut für Main` erzeugt.
- [ ] Admin- und Kolleg:innen-Artefakt werden aus exakt derselben geprüften HTML-Quelle gebaut.
- [ ] Nach dem Merge zeigt das kanonische Manifest auf das neue Release und die Admin-HTML liefert HTTP 200 mit dem erwarteten Versionsmarker.
- [ ] Die installierte Admin-Beta-App lädt nach Aktualisierung genau dieses neue Release.
- [ ] Ein Main-SHA-Wechsel während der Release-Vorbereitung führt zu einem eindeutigen, wiederholbaren Stop-/Retry-Handoff.
- [ ] Test-App, Admin-Beta und Source werden im Abschlussbericht getrennt ausgewiesen.
- [ ] Keine Patientendaten, Secrets oder Rohpayloads werden im Ticket oder Release-Status gespeichert.

## Abgrenzung

Dieses Ticket fordert keine Änderung der Patienten-App und keine neue APK, solange der externe Dokumentationslink nicht zusätzlich einen nativen Intent-/Wrapper-Fix benötigt. Der Android-App-Link-Realtest bleibt ein eigener Prüfpunkt.
