# Textfield Jitter Test

Ziel:
Jitter beim Bedienen des Uebungs-Textfeldes isoliert testen, ohne Haupt-App oder v389-Release-Dateien zu veraendern.

Ausloeser laut Video 54168.mp4:
- Textfeld ist fokussiert.
- Android-Tastatur ist offen.
- Beim Tippen aktualisieren sich Textfeld, Vorschlag/DB-Treffer und Live-Plan-Karten gleichzeitig.
- Sichtbar entstehen vertikale Spruenge im Bereich aktueller Plan/Textfeld/untere Aktionen.

Hypothesen:
1. Auto-Resize des Textfelds veraendert bei jedem Input die Hoehe und triggert Layout-Reflow.
2. Live-Draft-Karte im Plan wird bei jedem Buchstaben neu gerendert und verschiebt den Planbereich.
3. DB-Vorschlag/Top-Treffer wird bei jedem Buchstaben eingeblendet/aktualisiert und veraendert die Hoehe unter dem Textfeld.
4. Phone-Keyboard-/Sticky-Logik versucht gleichzeitig, das Textfeld sichtbar zu halten und verursacht Scroll-/Position-Korrekturen.
5. render() macht zu viel auf einmal: Textfeld, Planliste, Bank, Suggestions, Keyboard-Inset.

Teststrategie:
- Testseite misst Layout-Spruenge beim Tippen.
- Varianten vergleichen:
  A: v389-aehnlich aggressiv: AutoResize + LiveDraft + BankPreview sofort.
  B: stabilisiert: feste Textfeldhoehe waehrend Fokus + debounced Render + reservierter Preview-Platz.

Nicht anfassen:
- PDF
- QR
- Patienten-App
- Scan-Core
- Parser
- v389 Original
