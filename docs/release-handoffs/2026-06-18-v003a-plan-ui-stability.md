# 2026-06-18 – v003a Plan UI Stability Handoff

## Entscheidung

Nicht die originale `KGG_GitHub_Update_v003_plan_ui_stability.zip` deployen.

Grund: Die originale v003 enthält zwar den funktionalen Plan-UI-Stability-Patch, trägt intern aber alte Build-Identität:

- `<title>` zeigt noch `mini03`
- `VERSION` zeigt noch `v399`
- `KGG_BUILD_INFO.release` zeigt noch `v399`

Das würde den vorherigen mini07-Identitäts-Fix zurückdrehen.

## Sichere Datei

Stattdessen verwenden:

```txt
KGG_GitHub_Update_v003a_plan_ui_stability_identity_safe.zip
```

In v003a wurde nur die Identität korrigiert. Der funktionale v003-Patch bleibt enthalten.

## Enthaltene Ziel-Dateien

```txt
kgg-update/index.html
kgg-update/version.json
```

## version.json aus v003a

```json
{
  "versionCode": 3,
  "versionName": "1.0.2-plan-ui-stability",
  "indexUrl": "index.html",
  "sha256": "41474ecfa202ce040b6de34de3bac33a5b9b0ab56d12f174bc75dbdf761abc6e",
  "notes": "GitHub update: phone-only Plan UI stability; fixes card flicker, tap lift/reorder layout creep, and keeps movement inside Übungen im Plan. Identity-safe rebuild: title/VERSION/KGG_BUILD_INFO corrected so v003 does not revert the mini07 identity fix."
}
```

## SHA-256

```txt
kgg-update/index.html
41474ecfa202ce040b6de34de3bac33a5b9b0ab56d12f174bc75dbdf761abc6e
```

## Codex/Git-Befehl

Von Repo-Root auf Branch `chatgpt/mini07-identity-autoupdate`:

```bash
git checkout chatgpt/mini07-identity-autoupdate
unzip /path/to/KGG_GitHub_Update_v003a_plan_ui_stability_identity_safe.zip -d /tmp/kgg-v003a
mkdir -p kgg-update
cp /tmp/kgg-v003a/kgg-update/index.html kgg-update/index.html
cp /tmp/kgg-v003a/kgg-update/version.json kgg-update/version.json
sha256sum kgg-update/index.html
cat kgg-update/version.json
git add kgg-update/index.html kgg-update/version.json
git commit -m "Fix phone plan card flicker and layout creep"
git push
```

Erwartete Ausgabe bei `sha256sum`:

```txt
41474ecfa202ce040b6de34de3bac33a5b9b0ab56d12f174bc75dbdf761abc6e  kgg-update/index.html
```

## Testplan

Phone:

- Viewport 390×844 oder 400×844.
- Mindestens zwei Übungen in den Plan legen.
- Übungskarte antippen: Nur Karte/Planbereich darf reagieren, darunterliegende UI darf nicht nach unten creepen.
- Übung per Griff `⠿` verschieben: Nur Karten im Plan sollen sich bewegen.
- Vertikal scrollen: Plan-Karten dürfen nicht flackern.
- Swipe links/rechts muss weiter funktionieren.

Tablet:

- Viewport ab 760 px.
- Tablet-Layout muss unverändert bleiben.
- Plan-Karten verschieben prüfen.

Android-WebView:

- App komplett schließen und neu öffnen.
- Wrapper muss `versionCode: 3` sehen.
- SHA muss passen.
- Bei falschem SHA muss alte Version erhalten bleiben.

## Nicht anfassen

- PDF
- QR
- Patient-App
- Scan
- Parser
- Plan-State
- Storage
- Tablet-Layout
