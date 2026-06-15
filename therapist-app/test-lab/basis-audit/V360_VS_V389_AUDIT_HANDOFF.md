# KGG Basis-Audit: v360/v366 stabilere HTML vs v389

Status: Team-Info / Entscheidungsgrundlage, kein Patch-Auftrag.

## Anlass

Der letzte Vorschlag war zu generisch. Max will keine abstrakten Codex-Prompts, sondern eine konkrete, im GitHub-Testbereich liegende Informationsuebergabe, damit das Team sauber entscheiden kann, ob v389 wirklich weiter repariert werden soll oder ob eine aeltere stabilere HTML die bessere neue Basis ist.

## Wichtige Warnung

Die hochgeladene Referenzdatei ist aelter als v389. Sie heisst:

`KGG_APP_KOLLEGEN_v360_sync_bundle_qr (1).html`

Im Dateititel identifiziert sie sich intern als:

`KGG App Kollegen v366 Mobile Floating History Packages`

Sie darf nicht blind als neue Hauptbasis gesetzt werden. Sie ist zuerst Audit-/Vergleichsbasis.

## Warum dieses Audit notwendig ist

Die aktuelle v389/APK wirkt inzwischen stark verpatcht und erzeugt laufend neue UI-Folgefehler:

- Drag & Drop der Plan-Karten schlecht sichtbar
- Karte bleibt nicht sauber unter dem Finger
- Karte poppt zu weit nach oben
- Chaos-/Lueckenfeld im Planbereich
- ganzer Block `Uebungen im Plan` jittert
- Swipe/Drag/DB/Modal/Tablet-Probleme vermischen sich
- Tablet-Seitenmenue ist trotz neuerer Version broken

Max' Einschätzung:

Eine aeltere HTML war in der Kern-UI wahrscheinlich deutlich stabiler. Es ist moeglich, dass die meisten wichtigen App-Funktionen dort bereits vorhanden sind und vor allem spaetere Module fehlen.

## Vermutlich fehlende oder spaeter hinzugekommene Module in der alten HTML

Wahrscheinlich fehlen oder sind dort noch nicht voll integriert:

1. Paketbank
2. Uebungsdatenbank / Bank-Sync
3. Export / Import
4. Tablet-Seitenmenue / Tablet-Layout

Wichtig: Das Tablet-Seitenmenue ist in v389 ebenfalls broken. Es ist daher kein starkes Argument fuer v389 als Basis.

## Zentrale Frage

Nicht nach Versionsnummer entscheiden.

Die echte Frage lautet:

> Welche Datei ist funktional vollstaendig genug und strukturell am wenigsten kaputt?

Moegliche Ergebnisse:

- Ergebnis A: v389 bleibt Basis, weil die alte Datei zu viele Kernfunktionen nicht enthaelt.
- Ergebnis B: Die alte v360/v366-Datei wird neue Arbeitsbasis, weil sie die Kern-App stabiler traegt und nur modular nachziehbare Features fehlen.

## Vergleichspunkte Kern-App

Bitte alte v360/v366-Referenz gegen v389 vergleichen:

- Plan erstellen
- Uebungen hinzufuegen
- Uebungskarten anzeigen
- Drag & Drop
- Swipe / Loeschen
- Textfeld unter den Karten
- Vorschlagsbereich / Uebungsdatenbank-Position
- Speichern / Plan-State
- QR / Patientenausgabe
- PDF
- Scan
- Verlauf / Plan-Historie
- Pakete / Uebungspakete
- Offline-/PWA-Verhalten
- Android/WebView-Kompatibilitaet

## Vergleichspunkte spaetere Module

- Paketbank
- Uebungsdatenbank / Bank-Sync
- Export / Import
- Tablet-Seitenmenue
- Admin/Tablet/A-Z
- Build-/Versionsanzeige

## Bewertung je Punkt

Fuer jeden Punkt bitte nicht nur vorhanden/fehlt bewerten, sondern:

- vorhanden und stabil
- vorhanden, aber kaputt
- fehlt, aber modular nachziehbar
- fehlt und kritisch
- aus alter Version uebernehmen
- aus v389 behalten
- spaeter separat neu bauen

## Team-Verdict vor dem Audit

v389 darf nicht automatisch als beste Basis gelten, nur weil sie neuer ist.

Wenn die alte HTML 80-90 Prozent der wichtigen Kernfunktionen stabil enthaelt und hauptsaechlich Paketbank/Bank/Export/Tablet-Seitenmenue fehlen, dann ist es vermutlich effizienter, die alte stabile Datei zu modernisieren, statt v389 weiter zu entwirren.

Wenn die alte Datei wichtige Kernintegrationen wie QR, Patientenausgabe, PDF, Scan oder Plan-State nicht brauchbar enthaelt, bleibt v389 eher Basis, aber nur ueber frische Testkopien und kleine Einzelpatches.

## Nicht anfassen waehrend des Audits

- Release-Dateien
- Haupt-App-Dateien
- APK-Buildsystem
- PDF-Core
- QR-Core
- Patienten-App
- Scan-Core
- Parser
- Export-/Import-Core

Dieses Audit ist nur Entscheidungsgrundlage.

## Erwartetes GitHub-Ergebnis

Eine kurze Markdown-Tabelle unter `therapist-app/test-lab/basis-audit/`, z. B.:

| Bereich | v360/v366 Referenz | v389 | Bewertung | Empfehlung |
|---|---|---|---|---|
| Drag/Drop | stabiler? | broken? | offen | pruefen |
| QR/Patient-App | vorhanden? | vorhanden | offen | Basisentscheidung |
| Paketbank | fehlt? | vorhanden? | modular | spaeter nachziehen |
| Export/Import | fehlt? | vorhanden? | modular | spaeter nachziehen |
| Tablet-Menue | fehlt/broken? | broken | eigenes Ticket | nicht basisentscheidend |

## Entscheidung nach dem Audit

Max entscheidet danach:

A) v389 bleibt Basis und wird ueber Test-Lab-Patches repariert.

oder

B) v360/v366 wird neue stabile Arbeitsbasis und fehlende Module werden kontrolliert nachgezogen.
