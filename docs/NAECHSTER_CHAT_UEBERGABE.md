# Übergabe für neuen Chat

Projekt: KGG-/Physio-App im Repo `Kayus24/kgg`.

## Ziel

Stabile lokale/PWA-basierte KGG-Trainingsplan-App mit Patienten-App und später sauber getrennter Therapeut:innen-App.

## Wichtigster Arbeitsmodus

Nicht mehr blind komplette HTML-Dateien patchen.

Vor jeder Änderung zuerst:

1. betroffene Funktion finden
2. geplante Änderung erklären
3. nicht betroffene Bereiche nennen
4. danach nur kleinen Patch liefern
5. Pflicht-Test aus `docs/PFLICHTTEST_NACH_PATCH.md` ausführen

## Wichtige Dateien

- `README.md` – aktueller Repo-Zweck
- `docs/CHATGPT_PATCH_REGELN.md` – Regeln für sichere Patches
- `docs/PFLICHTTEST_NACH_PATCH.md` – kurze Testliste nach jeder Änderung
- `docs/VERSIONSLOG.md` – Speicherstände und Fehlerstände dokumentieren

## Kernproblem bisher

Die App wurde zu groß für Canvas/Einzeldatei-Patches. Risiko: ChatGPT repariert eine Stelle, zerstört aber ungesehen Kamera, Galerie, PDF, QR oder Scan-Flow.

## Kamera/Galerie-Regel

Kamera und Galerie müssen denselben Scan-Flow benutzen. Nach jedem Foto/Bild muss dieselbe Folgefrage erscheinen:

1. Seite anhängen
2. weiteren Plan scannen
3. fertig

## Nächster sinnvoller Schritt

Die aktuell beste funktionierende HTML/App-Version ins Repo hochladen. Danach als stabilen Stand markieren und erst dann gezielt weiterarbeiten.
