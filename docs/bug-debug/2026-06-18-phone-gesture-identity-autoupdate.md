# 2026-06-18 – Phone-Gesten-Fix + mini07 Identitäts-Fix + Auto-Update-Handoff

## Problem

Im Handy-Layout waren die Gesten der Übungskarten im aktuellen Plan fehlerhaft:

- Swipe links/rechts lief nicht sichtbar oder sprang zurück.
- Die Swipe-Animation wurde durch Phone-Scroll-CSS überschrieben.
- Drag/Reorder per Griff `⠿` war optisch unzuverlässig.
- Tablet war nicht betroffen.

Zusätzlich war nach dem Funktionsfix die interne Build-Identität veraltet: Der Dateiname war `KGG_APP_ADMIN_v400_mini06_phone_gesture_fix.html`, aber der interne Titel/Build-Text zeigte noch ältere mini03-Identität.

## Betroffene Version/Datei

- Ausgang: `KGG_APP_ADMIN_v400_mini06_phone_gesture_fix.html`
- Neue lokale Basis: `KGG_APP_ADMIN_v400_mini07_identity_fix.html`
- Ziel für Android-WebView-Auto-Update: `kgg-update/index.html`

## Ursache

Die Phone-Scroll-Stabilisierung setzte bei Touch-/Pointer-Bewegungen `body.is-scrolling`. In der Phone-CSS-Schicht wurden dabei Animationen und Transforms zu breit deaktiviert. Dadurch wurde auch `.planCard` getroffen.

Problematisch war insbesondere:

```css
body.is-scrolling ... .planCard {
  transform: none !important;
}
```

Die Swipe-Logik arbeitet aber aktiv mit:

```css
transform: translateX(var(--kgg-plan-swipe-x, 0px));
```

Dadurch bekam die Karte zwar Pointer-Events, die sichtbare Bewegung wurde aber vom Scroll-Guard neutralisiert.

## Lösung/Fix

Phone-only CSS-Patch ergänzt:

```css
@media (max-width:759px) {
  body.kggPlanCardSwiping .planCard.swipe-dragging,
  body.is-scrolling .planCard.swipe-dragging {
    transform: translateX(var(--kgg-plan-swipe-x, 0px)) !important;
    transition: none !important;
    will-change: transform, opacity;
  }

  body.kggPlanCardSwiping .planCard.swipe-removing,
  body.is-scrolling .planCard.swipe-removing {
    transform: translateX(var(--kgg-plan-swipe-x, 0px)) !important;
  }
}
```

Danach wurde als separater Mini-Patch nur die Identität korrigiert:

- `<title>`
- `VERSION`
- `KGG_BUILD_INFO`

Keine Layout-/Logikänderung im Identitäts-Fix.

## Android-WebView-Auto-Update-Handoff

Für den Android-Wrapper soll `KGG_APP_ADMIN_v400_mini07_identity_fix.html` als `kgg-update/index.html` veröffentlicht werden.

SHA-256 der lokal geprüften mini07-Datei:

```txt
3d510e1552c6cac704e419407dea30f8c03563abbbd66bdd776f00d7c2f77068
```

Hilfsscript im Repo:

```bash
python3 scripts/make_kgg_update_payload.py /path/to/KGG_APP_ADMIN_v400_mini07_identity_fix.html v400-mini07-identity-fix 1
```

Das Script erzeugt:

- `kgg-update/index.html`
- `kgg-update/version.json`

## Test / Abnahmekriterien

- [ ] Handy-Viewport 390×844 oder 400×844 testen.
- [ ] `matchMedia('(max-width:759px)').matches === true`.
- [ ] Mindestens zwei Übungen in den Plan legen.
- [ ] Karte links/rechts swipen: Karte muss sichtbar mitlaufen.
- [ ] Über Löschschwelle swipen: Karte muss entfernt werden.
- [ ] Griff `⠿` halten und Karte verschieben.
- [ ] Tablet-Viewport ab 760 px prüfen.
- [ ] Tablet-Layout darf unverändert bleiben.
- [ ] Android-Wrapper offline starten: lokale Asset-App muss laden.
- [ ] `versionCode` erhöhen und prüfen, ob neue `index.html` geladen wird.
- [ ] Falscher SHA-256 muss Update blockieren und Fallback behalten.

## Nicht anfassen

- PDF
- QR
- Patient-App
- Scan
- Parser
- Plan-State
- Storage
- Tablet-Layout
- Übungsdatenbank-Logik

## Folge-Risiken

- Wenn `body.is-scrolling` später wieder global auf `.planCard` erweitert wird, kann derselbe Fehler zurückkommen.
- Wenn `kgg-update/version.json` einen falschen SHA enthält, blockiert der Android-Wrapper das Update korrekt.
- Native Wrapper-Änderungen aktualisieren sich nicht über `kgg-update/index.html`; dafür braucht es ein neues APK.
