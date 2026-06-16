# KGG UI Flow Contract

Diese Datei ist die kompakte Schutzlinie fuer Admin-/Layout-Patches. Vor UI-Arbeit zusammen mit `KGG_REGRESSION_MEMORY.md` und der Tablet-Golden-Source-of-Truth lesen.

## Grundregeln

- Admin-App ist die Haupt-App.
- Neue UI-Aenderungen laufen zuerst ueber Test-Lab-HTMLs, nicht ueber Release-Dateien.
- Jede Codeaenderung bekommt eine neue Ziel-HTML, damit Backtracking moeglich bleibt.
- Keine grossen Mischfixes: Tablet, Handy, Plan-Karten, Einheiten und Admin-Module getrennt halten.
- `KGGDataStore.currentPlan` bleibt die zentrale Plan-State-Quelle.

## Nicht Nebenbei Anfassen

- PDF-Erzeugung
- QR/Patient:innen-App
- Scan/OCR
- Parser
- Medien-/Upload-Core
- API-Key-Logik
- Android/APK-Build

## Layout-Gates

- Tablet ab `760px`: zweispaltig, Datenbank/A-Z links, Plan rechts.
- Tablet leer: Sidebar darf offen starten, Planbereich bleibt sichtbar mit Empty-State.
- Tablet aktiv: Sidebar schliesst automatisch einmal und bleibt danach manuell steuerbar.
- Handy unter `760px`: keine gequetschte Tablet-Seitenleiste, keine abgeschnittene A-Z-/Scroll-Zone.
- Plan-Actions duerfen Plan-Karten nicht ueberdecken.

## Test-Gates

- Lokale HTML mit `?qa=1` oder passendem QA-Parameter laden.
- Console auf Errors pruefen.
- Build-Badge/Dateiname pruefen, kein GitHub-/Service-Worker-Ruecksprung.
- Pflicht-Viewports: `390x844`, `800x1280`, `1280x800`, `900x700`.
- Pflicht-Eingabe: `Beinpresse 3x12, Rudern 3x10, Latzug 45 kg 3x15`.
- Bei mehreren Plan-Karten jedes Zahnrad testen: Modalname muss exakt zur Karte passen.
