# Bugfix-Doku: Mobile Share-Modal fällt in den normalen Handy-Flow

Stand: v400 mini03 Analyse

## Kurzfassung

Im Handy-Layout (< 760 px) werden die Elemente des Dialogs „Therapeuten-App weitergeben“ sichtbar im normalen Seitenfluss angezeigt:

- Überschrift „Therapeuten-App weitergeben“
- Hinweis „Waehle, was der QR-Code enthalten soll.“
- Auswahlbuttons „Nur App“, „App + API-Key“, „Nur API-Key“

Diese Elemente gehören nicht in den normalen Handy-Flow. Sie sollen nur erscheinen, wenn das Share-Modal aktiv geöffnet wird.

## Betroffene Datei

`KGG_APP_ADMIN_v400_mini03_menu_handle_layout_persist.html`

Hinweis: Der Screenshot zeigte v399, aber v400 mini03 ist die neuere Arbeitsbasis. Deshalb nicht v399 als Hauptbasis patchen.

## Beobachtung im Code

### HTML-Block

Der Dialog liegt als eigenes Modal im DOM:

```html
<div class="kggTherapistShareModal" id="kggTherapistShareModal" aria-hidden="true">
  <div class="kggTherapistShareSheet" role="dialog" aria-modal="true" aria-labelledby="kggTherapistShareTitle">
    <h2 id="kggTherapistShareTitle">Therapeuten-App weitergeben</h2>
    <p class="kggTherapistShareHint">Waehle, was der QR-Code enthalten soll.</p>
    <div class="kggTherapistShareChoices">
      ...
    </div>
  </div>
</div>
```

In der lokalen v400-Datei lag dieser Block um Zeile ca. 4928.

### Fehlerursache

Die versteckende/positionierende Modal-Regel ist zu eng scoped:

```css
body.tabletLayoutCustom .kggTherapistShareModal {
  position: fixed !important;
  inset: 0 !important;
  display: none !important;
  place-items: center !important;
  z-index: 1320 !important;
  background: rgba(7,16,39,.35) !important;
  padding: 18px !important;
  box-sizing: border-box !important;
}
body.tabletLayoutCustom .kggTherapistShareModal.isOpen {
  display: grid !important;
}
```

Diese Regel greift nur, wenn `body.tabletLayoutCustom` aktiv ist. Im Handy-Layout fehlt diese Klasse bzw. der Tablet-Kontext. `aria-hidden="true"` versteckt visuell nichts. Dadurch kann der Modal-Block im Handy-Layout als normaler Seiteninhalt sichtbar werden.

## Zielzustand

- Handy-Layout: `#kggTherapistShareModal` ist standardmäßig komplett unsichtbar und nimmt keinen Platz ein.
- Tablet-Layout: bestehende Funktion bleibt unverändert.
- Dialog öffnet sich weiterhin über den Tablet-Menüpunkt „Therapeuten-App weitergeben“.
- Keine Änderung an QR-Core, API-Key-Transfer, PDF, Parser, Scan-Core oder Patient-App-Payload.

## Empfohlener Mini-Patch

Die Modal-Grundregel muss global gelten, nicht nur unter `body.tabletLayoutCustom`.

```css
/* Mobile-safe base rule: Share-Modal darf nie im normalen Flow sichtbar sein. */
.kggTherapistShareModal {
  position: fixed !important;
  inset: 0 !important;
  display: none !important;
  place-items: center !important;
  z-index: 1320 !important;
  background: rgba(7,16,39,.35) !important;
  padding: 18px !important;
  box-sizing: border-box !important;
}

.kggTherapistShareModal.isOpen {
  display: grid !important;
}

.kggTherapistShareSheet {
  width: min(92vw, 440px) !important;
  display: grid !important;
  gap: 12px !important;
  background: #fff !important;
  color: #071027 !important;
  border: 2px solid #111827 !important;
  border-radius: 20px !important;
  padding: 16px !important;
  box-shadow: 0 22px 70px rgba(7,16,39,.24) !important;
}

.kggTherapistShareChoices {
  display: grid !important;
  gap: 10px !important;
}

.kggTherapistShareChoices button {
  min-height: 62px !important;
  padding: 10px 12px !important;
  border: 1px solid #dce3eb !important;
  border-radius: 14px !important;
  background: #fff !important;
  text-align: left !important;
  box-shadow: 0 4px 14px rgba(7,16,39,.08) !important;
}

.kggTherapistShareChoices b {
  display: block !important;
  font-size: 16px !important;
}

.kggTherapistShareChoices small {
  display: block !important;
  margin-top: 3px !important;
  color: #657386 !important;
  font-weight: 800 !important;
  line-height: 1.25 !important;
}
```

Optional: Die alte Tablet-spezifische Regel kann bestehen bleiben, aber die globale Regel muss nach Möglichkeit später im CSS stehen oder mindestens gleich spezifisch sein. Besser: Tablet-Regel nicht duplizieren, sondern auf die globale Basisregel reduzieren.

## Akzeptanztests

1. Viewport 390 x 844 px öffnen.
2. Prüfen: „Therapeuten-App weitergeben“ und die drei Optionen sind nicht im normalen Handy-Flow sichtbar.
3. Viewport 390 x 844 px: `document.getElementById('kggTherapistShareModal').getBoundingClientRect().height` soll im geschlossenen Zustand 0 oder das Element `display:none` haben.
4. Modal gezielt öffnen: `openKggTherapistShareModal()`.
5. Prüfen: Overlay erscheint, Buttons sind weiß/gerundet, keine nativen grauen Blöcke.
6. Modal schließen: `closeKggTherapistShareModal()`.
7. Tablet-Viewport >760 px prüfen: Menüpunkt „Therapeuten-App weitergeben“ öffnet weiterhin das Modal.
8. QR-/API-Key-Funktionen nicht anfassen und nicht neu implementieren.

## Nicht anfassen

- QR-Core
- API-Key-Transfer-Logik
- PDF-Core
- Parser
- Scan-Core
- Patient-App-Payload
- Plan-State
- `.scanHub` / obere Scanbox, da das ein separater UI-Flow-Punkt ist

## Codex-Hinweis

Nur CSS-Fix für `kggTherapistShareModal` und `kggTherapistShareChoices`. Keine Layout-Umbauten nebenbei. Keine neue Funktionalität.