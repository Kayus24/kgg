# G08 – Security, Datenschutz und Autorisierung

## 1. Ziel

Der reale Plugin-/Browserpfad arbeitet mit minimalen Rechten, ausschließlich synthetischen Testdaten und fail-closed Grenzen für Navigation, Aktionen, Speicherung und externe Konsequenzen.

## 2. Warum dieses Gate erforderlich ist

Browsersteuerung kann sensible Oberflächen, Downloads oder externe Writes erreichen. Bestehende Repo-Gates decken diese neue Hostgrenze nicht automatisch vollständig ab.

## 3. Scope und Nicht-Ziele

In Scope: URL-/Origin-Allowlist, Session-Isolation, Lease, Aktionstypen, Limits, Screenshot-/Log-Sanitization, Auth und Audits. Keine Produktivpatientendaten.

## 4. Abhängigkeiten

G04-Design, `kgg-safety`, vorhandene Privacy-/Knowledge-Safety-Regeln und Consequence Gates.

## 5. Aktueller Stand

- `IMPLEMENTATION_STATUS=STRONG_EXISTING_REPO_RULES_BROWSER_RULES_UNPROVEN`
- `LIVE_EVIDENCE_STATUS=SYNTHETIC_ONLY_FOR_UI_LAB`
- `GATE_STATUS=PARTIAL`
- `EVIDENCE_LEVEL=E1_SYNTHETIC`
- `LAST_VERIFIED_BASE_SHA=2b8024e359bd0f65bcc5666b5e190d78a4b4ed6f`
- `LAST_VERIFIED_AT=2026-09-21`

## 6. Bestehende Evidence

KGG besitzt Schutzbereiche, Secret Scan, Write Gates, synthetische Testdatenregeln und getrennte Release-/Preview-Freigaben.

## 7. Lücke und Root Cause

Eine reale Browserbrücke existiert noch nicht; deshalb sind Origin-Schutz, Session-Lease, Screenshots, unerwartete Dialoge und Action-Limits am Realpfad unbelegt.

## 8. Kleinschrittiger Arbeitsplan

1. erlaubte Origins und Start-URLs festlegen.
2. Browserprofil pro Run isolieren und nach Run löschen.
3. Session-Lease, maximale Dauer und maximale Schritte erzwingen.
4. Toolaktionen in read-only, UI-mutating-local und external-consequence klassifizieren.
5. Dateiupload, Download, Clipboard, Kamera, Mikrofon, Popup und neue Origins standardmäßig sperren.
6. Screenshots/Logs auf Secrets und Patientendaten begrenzen/sanitizen.
7. Negativtests am echten Runner durchführen.

## 9. CONTROL_LOOP_GATE

- `GATE_ID=G08_BROWSER_SAFETY`
- `INPUT=Real-Runner, Allowlist, synthetische Testseite, Policy`
- `PROCEDURE=positive erlaubte Aktion plus definierte unerlaubte Aktionen ausführen`
- `PASS_CRITERIA=erlaubte Aktion funktioniert; jede unerlaubte Aktion stoppt mit stabiler Fehlerklasse und ohne Nebenwirkung`
- `FAIL_CRITERIA=Origin-Escape, persistente Sessiondaten, sensitive Evidence oder externe Aktion ohne Gate`
- `RETRY_RULE=kein identischer Retry bei Policyverletzung`
- `FALLBACK=Runner deaktivieren und Evidence sichern`
- `EVIDENCE_OUTPUT=BROWSER_SAFETY_REPORT_V1`
- `NEXT_ON_PASS=G10`
- `NEXT_ON_FAIL=Fix; bei Policyfrage G11 oder Human Gate`
- `INVALIDATION_TRIGGERS=neue Toolaktion, Origin, Auth, Storage oder Evidence-Art`

## 10. Tests

- unerlaubte Domain und Redirect.
- abgelaufene/falsche Lease.
- Max-Schritte/Timeout.
- Popup, Download, Clipboard und Filechooser.
- Secret-/Patienten-Canary.
- Write-/Releaseaktion ohne Consequence Gate.

## 11. Safety und Datenschutz

Dieses gesamte Gate ist die Safety-Grenze. Echte Patientendaten sind in Tests und Evidence strikt verboten.

## 12. Brother-GPT-Eskalation

Brother darf bei Policykonflikten nur strengere oder gleichwertige Lösungen empfehlen und niemals eine Freigabe erzeugen.

## 13. Abschlussartefakte

Browserpolicy, Negativtests, Auth-/Lease-Vertrag, Sanitization-Report und Incident-/Disable-Anleitung.

## 14. Beitragsherkunft

`CONTRIBUTION_SOURCE=HUMAN_AND_CODEX`, `REVIEW_STATUS=PENDING`.

