# KGG Custom GPT Negative Examples

## JSON als normaler Markdown-Text

Falsch:

```text
{ "patch_content": "<script>var id=\"__KGG_PATCH_ID__\";</script>" }
```

Ausserhalb eines `json`-Codeblocks kann Markdown `__KGG_PATCH_ID__` als Hervorhebung interpretieren und die Unterstriche verlieren. Ein sichtbarer JSON-aehnlicher Text ist zudem kein Nachweis fuer parsebares JSON.

Richtig ist genau ein `json`-Codeblock mit gueltigem JSON, dem bytegenauen Platzhalter und vollstaendigen Testkommandos.

## Patch-ID als Array registriert

Falsch:

```js
window.KGG_PATCHES = window.KGG_PATCHES || [];
window.KGG_PATCHES.push(PATCH_ID);
```

Das verletzt den KGG-Patchvertrag. Richtig ist ein Objekt-Eintrag unter `window.KGG_PATCHES[PATCH_ID]`, damit Gate und Verhaltenstests die Installation eindeutig nachweisen koennen.

## Alter index.html-Payload

```json
{
  "request_id": "tablet-splitter",
  "operations": [
    {
      "path": "kgg-update/index.html",
      "old_text": "...",
      "new_text": "..."
    }
  ]
}
```

Reject: `operations`, `old_text`, `new_text` und `path` sind v1. `kgg-update/index.html` ist generated output. Nutze `patch_content`.

## Alias-Feld file

```json
{
  "request_id": "tablet-splitter",
  "file": "kgg-update/index.html",
  "patch_content": "..."
}
```

Reject: Der GPT darf keinen Datei- oder Repository-Pfad bestimmen. Das Gate erzeugt `kgg-update/src/patches/vNNN-<slug>.html`.

## Geschuetztes Wort im Kommentar

```json
{
  "patch_content": "<script id=\"__KGG_PATCH_ID__\">/* keine API-Key Aenderung */</script>"
}
```

Reject: Guard-Tokens sind auch in Kommentaren verboten. Schutzbereiche in der Antwort beschreiben, nicht im Patch.

## Komplette HTML statt Fragment

```json
{
  "patch_content": "<!doctype html><html><body>...</body></html>"
}
```

Reject: `patch_content` ist nur ein Modulfragment. Das Gate baut die End-HTML.

## Manuelle Versionierung

```json
{
  "patch_content": "<script>const VERSION='KGG_GITHUB_UPDATE_v999_bad';</script>"
}
```

Reject: Version, Build-Info, Changelog und Source-Truth gehoeren dem Gate.

## Fehlende Tests

```json
{
  "request_id": "tablet-splitter",
  "title": "Tablet Splitter",
  "summary": "Layout",
  "version_slug": "tablet-splitter",
  "touched_areas": ["Tablet-Layout"],
  "required_tests": [],
  "patch_content": "<script id=\"__KGG_PATCH_ID__\"></script>"
}
```

Reject: UI-Payload braucht `critical` plus `ui-stability regression`.

## Roter Run plus meta 404

Wenn der GitHub-Run rot ist und `meta.json` 404 liefert, ist das kein “wartet noch”.
Erst failed step und Log melden, dann keinen Preview-Erfolg behaupten.

## Test-App-Fail

Wenn Max in der Test-App sagt “sieht falsch aus”, ist das `human_preview_fail`.
Kein PR, kein Admin-Beta, kein Main. Lesson/Regression ergaenzen und wieder `validate_only`.
