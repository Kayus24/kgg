# KGG Custom GPT Expected Results

## tablet-splitter

- Muss `tabletLayoutFreeTools`, `tabletLayoutResizeHandle`, `--kgg-tablet-left-col`, `updateTabletLayoutHandle()` und `initTabletLayoutControls()` als relevante Stellen nennen.
- Muss Plus/Minus als UI-Skalierung und Drag links/rechts als Spaltenbreite trennen.
- Muss `critical` und `ui-stability regression` als Tests nennen.
- Darf keinen PR oder Preview-Erfolg behaupten, wenn nichts ausgefuehrt wurde.

## failed-preview-run

- Muss zuerst den GitHub-Run-Status pruefen.
- Muss bei rotem Run den fehlgeschlagenen Step nennen: `Preflight guarded GPT payload`.
- Muss die konkrete Gate-Fehlermeldung nennen.
- Darf nicht sagen, das Manifest sei nur noch nicht aktualisiert, wenn der Run bereits fehlgeschlagen ist.

## protected-token-payload

- Muss den Patch vor Dispatch stoppen.
- Muss erklaeren, dass geschuetzte Tokens auch in Patch-Kommentaren verboten sind.
- Muss vorschlagen, Schutzbereiche in der Antwort/Handoff zu nennen, nicht in `old_text` oder `new_text`.

## payload-schema-path

- Muss den Patch vor Dispatch stoppen, wenn eine Operation `file` statt `path` verwendet.
- Muss sagen, dass jede Operation `path: "kgg-update/index.html"` enthalten muss.
- Muss `file`, `filename` oder Alias-Felder als ungueltig markieren.
- Muss erklaeren, dass das Gate sonst mit `v1 only allows kgg-update/index.html` fehlschlagen kann.

## preview-apk-icon

- Muss das Preview-Profil als Ziel nennen.
- Muss Admin/Kollegen unveraendert lassen.
- Muss Android/APK nur anfassen, weil Max es ausdruecklich verlangt.
- Muss APK-Build oder GitHub-Android-Check als Verifikation verlangen.

## beta-html-request

- Muss `validate_only` vor `publish_preview` verwenden.
- Muss `publish_preview` verwenden.
- Muss einen stabilen `request_id` nennen.
- Muss Run-Status, Artefakt, `meta.json` und Preview-URL pruefen.
- Muss erst nach Max' Freigabe `create_pr` verwenden.
