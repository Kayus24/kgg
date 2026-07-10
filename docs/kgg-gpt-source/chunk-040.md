# KGG Source Chunk 040

- Source: `kgg-update/index.html`
- Lines: 16801-17220

```html
        });
    }
    if (result.length === 0) {
        return null;
    }
    return result;
}
exports.locate = locate;
function findAlignmentPattern(matrix, alignmentPatternQuads, topRight, topLeft, bottomLeft) {
    var _a;
    // Now that we've found the three finder patterns we can determine the blockSize and the size of the QR code.
    // We'll use these to help find the alignment pattern but also later when we do the extraction.
    var dimension;
    var moduleSize;
    try {
        (_a = computeDimension(topLeft, topRight, bottomLeft, matrix), dimension = _a.dimension, moduleSize = _a.moduleSize);
    }
    catch (e) {
        return null;
    }
    // Now find the alignment pattern
    var bottomRightFinderPattern = {
        x: topRight.x - topLeft.x + bottomLeft.x,
        y: topRight.y - topLeft.y + bottomLeft.y,
    };
    var modulesBetweenFinderPatterns = ((distance(topLeft, bottomLeft) + distance(topLeft, topRight)) / 2 / moduleSize);
    var correctionToTopLeft = 1 - (3 / modulesBetweenFinderPatterns);
    var expectedAlignmentPattern = {
        x: topLeft.x + correctionToTopLeft * (bottomRightFinderPattern.x - topLeft.x),
        y: topLeft.y + correctionToTopLeft * (bottomRightFinderPattern.y - topLeft.y),
    };
    var alignmentPatterns = alignmentPatternQuads
        .map(function (q) {
        var x = (q.top.startX + q.top.endX + q.bottom.startX + q.bottom.endX) / 4;
        var y = (q.top.y + q.bottom.y + 1) / 2;
        if (!matrix.get(Math.floor(x), Math.floor(y))) {
            return;
        }
        var lengths = [q.top.endX - q.top.startX, q.bottom.endX - q.bottom.startX, (q.bottom.y - q.top.y + 1)];
        var size = sum(lengths) / lengths.length;
        var sizeScore = scorePattern({ x: Math.floor(x), y: Math.floor(y) }, [1, 1, 1], matrix);
        var score = sizeScore + distance({ x: x, y: y }, expectedAlignmentPattern);
        return { x: x, y: y, score: score };
    })
        .filter(function (v) { return !!v; })
        .sort(function (a, b) { return a.score - b.score; });
    // If there are less than 15 modules between finder patterns it's a version 1 QR code and as such has no alignmemnt pattern
    // so we can only use our best guess.
    var alignmentPattern = modulesBetweenFinderPatterns >= 15 && alignmentPatterns.length ? alignmentPatterns[0] : expectedAlignmentPattern;
    return { alignmentPattern: alignmentPattern, dimension: dimension };
}


/***/ })
/******/ ])["default"];
});
</script>
<!-- KGG PATCH END kgg-v021-embed-jsqr-gallery-decode lib -->

<style id="kgg-v024-rollback-v023-debug-breakage-guard-style">
/* KGG PATCH START: kgg-v024-rollback-v023-debug-breakage-guard-style */
#kggAdminDebugFab,
#kggAdminDebugBtn,
#kggAdminHubBtn,
.kggAdminDebugBtn,
.kggAdminHubBtn,
#kggDebugPanelOverlay,
.kggDebugPanelOverlay,
.kggDebugToast{
  display:none!important;
  visibility:hidden!important;
  opacity:0!important;
  pointer-events:none!important;
}
/* KGG PATCH END: kgg-v024-rollback-v023-debug-breakage-guard-style */
</style>
</head>
<body class="adminMode">
<div class="tabletSideBackdrop" id="tabletSideBackdrop" hidden></div>
  <aside class="tabletSideMenu" id="tabletSideMenu" aria-hidden="true">
    <div class="tabletSideMenuHead">
      <strong>Menue</strong>
      <button class="tabletMenuClose" id="tabletMenuClose" type="button" aria-label="Menue schliessen">&times;</button>
    </div>
    <nav class="tabletSideMenuGroup tabletSideMenuMain" aria-label="Tablet-Menue">
      <button class="tabletSideMenuAction tabletMenuNavAction" id="tabletMenuRecentBtn" type="button"><span class="tabletMenuActionIcon" aria-hidden="true">&#128337;</span><span>Letzte Pl&auml;ne</span></button>
      <button class="tabletSideMenuAction tabletMenuNavAction" id="tabletMenuPackagesBtn" type="button"><span class="tabletMenuActionIcon" aria-hidden="true">&#128230;</span><span>&Uuml;bungspakete</span></button>
      <button class="tabletSideMenuAction tabletMenuNavAction" id="tabletMenuTherapistShareBtn" type="button"><span class="tabletMenuActionIcon" aria-hidden="true">&#128188;</span><span>Therapeuten-App weitergeben</span></button>
      <button class="tabletSideMenuAction tabletMenuNavAction" id="tabletMenuLayoutBtn" type="button" aria-expanded="false"><span class="tabletMenuActionIcon" aria-hidden="true">&#9881;</span><span>Layout anpassen</span></button>
      <div class="tabletSideMenuLayoutPanel" id="tabletMenuLayoutPanel" hidden>
        <div class="tabletLayoutControls" id="tabletLayoutControls" aria-label="Tablet-Layout">
          <button class="tabletLockSwitch" id="tabletLayoutLockBtn" type="button" aria-pressed="true" aria-label="Layout fixiert">
            <span class="tabletLockIcon" aria-hidden="true">&#128274;</span>
            <span class="tabletSwitchTrack" aria-hidden="true"><span class="tabletSwitchKnob"></span></span>
            <span class="tabletLockText">Fix</span>
          </button>
          <div class="tabletLayoutFreeTools" id="tabletLayoutFreeTools" aria-label="Freies Tablet-Layout">
            <button id="tabletScalePlus" type="button" aria-label="UI groesser">+</button>
            <span class="tabletScaleValue" id="tabletScaleValue">100%</span>
            <button id="tabletLayoutReset" type="button" aria-label="Tablet-Layout zuruecksetzen">&#8634;</button>
            <button id="tabletScaleMinus" type="button" aria-label="UI kleiner">-</button>
          </div>
        </div>
      </div>
    </nav>
  </aside>
<div class="tabletPackageShade" id="tabletPackageShade" hidden></div>
<aside class="tabletPackageOverlay" id="tabletPackageOverlay" aria-hidden="true" aria-label="Uebungspakete">
  <div class="tabletPackageHead">
    <div class="tabletPackageTitle"><span aria-hidden="true">&#128230;</span><strong>&Uuml;bungspakete</strong></div>
    <button class="tabletPackageClose" id="tabletPackageClose" type="button" aria-label="Uebungspakete schliessen">&times;</button>
  </div>
  <label class="tabletPackageSearch"><span aria-hidden="true">&#128269;</span><input id="tabletPackageSearch" type="search" placeholder="Uebungspakete suchen ..." autocomplete="off"></label>
  <div class="tabletPackageCards" id="tabletPackageCards"></div>
</aside>
<div class="app">
  <div class="adminTestBanner">ADMIN-DATEI · v32 No Boot Redirect<small>Nur intern fuer Max/Admin. Nicht fuer Patient:innen verwenden. Keine API-Keys fest eingebaut.</small></div>
  <header class="topbar"><div class="topbarText"><h1>KGG Plan App <span class="stateBadge" id="stateBadge">Leerzustand</span></h1><small id="kggRuntimeVersion">Plain HTML/CSS/JS · offlinefähig · mobile-first</small><small class="kggBuildBadge" id="kggBuildBadge">Build wird geladen</small></div><button class="visionBtn" id="visionBtn" type="button" aria-pressed="false" aria-label="Großdruck-PDF umschalten">PDF A+</button></header>

  <section class="scanHub" id="scanHub">
    <button class="tabletMenuBtn" id="tabletMenuBtn" type="button" aria-label="Tablet-Menue oeffnen" aria-expanded="false"><span></span><span></span><span></span></button>
    <button class="scanBtn" id="scanBtn">📷 Plan scannen</button>
    <button class="syncQrBtn" id="syncQrBtn" type="button" aria-label="Sync-QR erzeugen" title="Sync-QR">QR</button>
    <input id="fileInput" class="nativeFileInput" type="file" accept="image/*" capture="environment">
    <input id="filePickerInput" class="nativeFileInput" type="file" accept="image/*,.jpg,.jpeg,.png,.webp" multiple>
    <div class="scanMeta filePickBtn" id="filePickBtn" role="button" tabindex="0" aria-label="Foto oder Datei auswählen">Foto / Datei <small id="scanStatus" class="hidden"></small></div>
    <button class="mutedBtn adminConfigBtn" id="adminConfigBtn" type="button">Admin-Konfig</button>
    <button class="mutedBtn sharedBankBtn" id="sharedBankBtn" type="button">Übungsdatenbank teilen</button>
    <div id="scanPreview" class="notice hidden"></div>
  </section>
  <div class="kggAdminMenuQrModal" id="kggAdminMenuQrModal" aria-hidden="true">
    <div class="kggAdminMenuQrSheet" role="dialog" aria-modal="true" aria-labelledby="kggAdminMenuQrTitle">
      <h2 id="kggAdminMenuQrTitle">QR</h2>
      <p class="kggAdminMenuQrHint" id="kggAdminMenuQrHint"></p>
      <div class="kggAdminMenuQrBox" id="kggAdminMenuQrBox"></div>
      <textarea class="kggAdminMenuQrLink" id="kggAdminMenuQrLink" readonly></textarea>
      <div class="kggAdminMenuQrButtons">
        <button type="button" id="kggAdminMenuQrCopy">kopieren</button>
        <button type="button" class="primary" id="kggAdminMenuQrOpen">oeffnen</button>
        <button type="button" id="kggAdminMenuQrPrint">QR drucken</button>
        <button type="button" id="kggAdminMenuQrClose">schliessen</button>
      </div>
    </div>
  </div>
  <div class="kggTherapistShareModal" id="kggTherapistShareModal" aria-hidden="true">
    <div class="kggTherapistShareSheet" role="dialog" aria-modal="true" aria-labelledby="kggTherapistShareTitle">
      <h2 id="kggTherapistShareTitle">Therapeuten-App weitergeben</h2>
      <p class="kggTherapistShareHint">QR fuer die Kolleg:innen-App/APK. Keine Sync-Daten, keine API-Keys.</p>
      <div class="kggTherapistShareChoices">
        <button type="button" id="therapistShareAppOnly"><b>Kolleg:innen-App APK</b><small>QR mit aktuellem Android-Download-Link fuer Kolleg:innen.</small></button>
      </div>
      <button type="button" class="mutedBtn" id="therapistShareCancel">Abbrechen</button>
    </div>
  </div>
  <div id="mobileScannedPlansDock" class="mobileScannedPlansDock hidden" aria-live="polite"></div>
  <div class="tabletLayoutResizeHandle" id="tabletLayoutResizeHandle" role="separator" aria-orientation="vertical" aria-label="Tablet-Spaltenbreite ziehen"><div class="tabletSplitScaleControl" id="tabletSplitScaleControl" aria-hidden="true"><button id="tabletSplitScalePlus" type="button" aria-label="UI groesser">+</button><span class="tabletSplitScaleValue" id="tabletSplitScaleValue">100%</span><button id="tabletSplitScaleMinus" type="button" aria-label="UI kleiner">-</button></div></div>

  <main class="panel" id="createPanel">
    <div class="planHeader">
      <h2 class="panelTitle" id="panelTitle">➕ Neuen Plan erstellen</h2>
      <button class="packageSaveBtn hidden" id="savePackageBtn" type="button" aria-label="Aktuellen Plan als Übungspaket speichern"><span class="packagePlus">+</span><span class="packageBox">📦</span></button>
    </div>
    <section class="inner">
      <button class="baseCard" id="baseToggle"><span>▶ 👤 Basisdaten</span><span class="mini" id="patientMini"></span></button>
      <div id="baseFields" class="hidden">
        <div class="grid2"><div class="field"><label>Patient/in</label><input id="patientName" placeholder="V. Nachname"></div><div class="field"><label>Datum</label><input id="planDate" type="date"></div></div>
        <div class="field"><label>Therapeut/in</label><input id="therapistName" placeholder="Name"></div>
        <div class="field"><label>Zusatzinfo</label><textarea id="planNotes" placeholder="Optional" style="min-height:78px;font-size:16px"></textarea></div>
      </div>

      <div id="rightPlanStack" class="rightPlanStack hidden" aria-live="polite">
        <div id="currentPlanBlock" class="planSection planSectionCurrent hidden">
          <button class="planSectionHeader" id="currentPlanToggle" type="button" aria-expanded="true">
            <span>✏️ Übungen im Plan</span><small id="currentPlanCount"></small>
          </button>
          <div class="planSectionBody">
            <div class="planList" id="planList"></div>
          </div>
        </div>
        <div id="scannedPlansBlock" class="planSection scanInboxBlock hidden">
          <button class="planSectionHeader" id="scannedPlansToggle" type="button" aria-expanded="false">
            <span>Gescannte Pläne</span><small id="scannedPlansCount"></small>
          </button>
          <div class="scanInboxList" id="scannedPlansList"></div>
        </div>
      </div>

      <div class="label" id="inputLabel">Übungen eingeben</div>
      <div id="dbTitle" class="dbTitle hidden" role="button" tabindex="0" aria-expanded="true">▼ 🏋️ Übungsdatenbank</div>
      <div class="inputWrap" id="inputWrap">
        <textarea id="exerciseInput" placeholder="Übungen, mit Komma getrennt" autocomplete="off" autocapitalize="none"></textarea>
        <button class="clearBtn" id="clearInput" aria-label="Text löschen">×</button>
        <div class="suggestion hidden" id="suggestion"></div>
      </div>

      <div class="bankArea" id="bankArea">
        <button class="drawerBtn" id="bankToggle"><span>▸ 🏋️ Übungsdatenbank</span></button>
        <div id="bankContent" class="hidden"></div>
      </div>
    </section>

    <div class="tools">
      <div class="planActions" id="planActions">
        <button class="primary finishBtn hidden" id="finishBtn" type="button">Fertig</button>
        <button class="drawerBtn" id="recentToggle"><span class="recentIcon">🕘</span><span class="recentText">Plan-Historie</span><span class="mini recentMini">öffnen</span></button>
      </div>
      <div id="recentList" class="hidden"></div>
      <div class="packageLayoutSlot" id="packageLayoutSlot">
        <button class="drawerBtn" id="packageToggle"><span>📦 Übungspakete anzeigen</span></button>
      </div>
      <div id="packageList" class="hidden"></div>
    </div>
  </main>

  <div class="bottomPad"></div>
</div>

<div class="footerActions">
  <button class="mutedBtn" id="exportBtn">JSON Export</button>
  <button class="mutedBtn" id="pdfBtn">PDF erzeugen</button>
  <button class="primary" id="patientBtn">Patienten-App / QR</button>
</div>

<div class="modal" id="editorModal"><div class="sheet editorSheet">
  <div class="editorHeader"><h2>Übung bearbeiten</h2><button class="iconBtn danger editorDeleteBtn" id="deleteExercise" type="button" aria-label="Übung löschen" title="Übung löschen">🗑️</button></div>
  <div class="field"><label>Name</label><input id="editName"></div>
  <div class="grid2">
    <div class="field"><label>Sätze</label><select id="editSets"><option value="1">1</option><option value="2">2</option><option value="3">3</option><option value="4">4</option><option value="5">5</option></select></div>
    <div class="field"><label>Ausführung</label><select id="editSide"><option value="BI">beidseitig</option><option value="LR">links/rechts getrennt</option></select></div>
  </div>
  <div class="grid2">
    <div class="field"><label>Einheit</label><select id="editUnit"><option value="kg">kg</option><option value="BW">BW</option><option value="Hub">Hub</option><option value="Stufe">Stufe</option><option value="Watt">Watt</option><option value="Stufe/Watt">Stufe/Watt</option><option value="bar">bar</option><option value="keine">keine</option></select></div>
    <div class="field"><label>Messwert</label><select id="editMeasure"><option value="wdh">Wdh</option><option value="zeit">Zeit</option></select></div>
  </div>
  <div class="notice editorStartHint">
    <b>Startvorschlag für Tag 1</b>
    <div class="grid2 editorStartGrid"><div class="field"><label>Startgewicht / Startstufe</label><input id="editLoad"></div><div class="field"><label>Start-Wdh / Startzeit</label><input id="editMetric"></div></div>
  </div>
  <div class="notice editorMediaBox">
    <div class="editorMediaHead">
      <div><b>Bild</b><small class="editorMediaStatus" id="editMediaStatus">Kein Bild.</small></div>
    </div>
    <div id="editMediaPreview" class="editorMediaPreview hidden"></div>
    <div class="editorMediaActions">
      <button class="mutedBtn" id="attachExerciseImage" type="button">Bild wählen</button>
      <button class="mutedBtn danger hidden" id="removeExerciseImage" type="button">Entfernen</button>
    </div>
    <input id="editMediaFile" class="hidden" type="file" accept="image/*">
  </div>
  <details class="notice editorAdvanced">
    <summary><b>Mehr</b></summary>
    <div class="grid2 editorAdvancedGrid"><div class="field"><label>Video-Link für Zuhause</label><input id="editVideoUrl" placeholder="https://..."></div><div class="field"><label>Button-Text</label><input id="editVideoLabel" placeholder="Video öffnen"></div></div>
  </details>
  <div class="editorActions"><button class="primary" id="saveExercise">Speichern</button></div>
  <button class="mutedBtn editorCancelBtn" id="closeEditor">Abbrechen</button>
</div></div>

<div class="modal" id="packageSaveModal"><div class="sheet">
  <h2>Übungspaket speichern</h2>
  <p class="notice">Aus aktuellem Plan.</p>
  <div class="field"><label>Paketname</label><input id="packageNameInput" placeholder="z. B. Knie Standard"></div>
  <div class="grid2"><button class="mutedBtn" id="cancelPackageSave" type="button">Abbrechen</button><button class="primary" id="confirmPackageSave" type="button">OK</button></div>
</div></div>

<div class="modal" id="bankDeleteModal"><div class="sheet">
  <h2>Übung löschen?</h2>
  <p class="notice"><b id="bankDeleteName"></b> endgültig löschen?</p>
  <div class="grid2"><button class="mutedBtn" id="cancelBankDelete" type="button">Nein</button><button class="primary" id="confirmBankDelete" type="button">Ja</button></div>
</div></div>

<div class="modal" id="shareModal"><div class="sheet">
  <p class="notice" id="finishNotice"></p>
  <div class="finishChoices" id="finishChoices">
    <div class="finishPdfRow">
      <button class="mutedBtn finishOutputBtn finishPdfBtn" id="finishPdfBtn" type="button"><span class="finishIcon" aria-hidden="true">📄</span><span>PDF erzeugen</span></button>
      <button class="mutedBtn finishPdfLargeBtn" id="finishLargePdfBtn" type="button" aria-label="Großdruck-PDF für Menschen mit Sehbeeinträchtigung">👓</button>
    </div>
    <button class="mutedBtn finishOutputBtn finishAppBtn" id="finishPatientBtn" type="button"><span class="finishIcon" aria-hidden="true">▦</span><span>App erzeugen</span></button>
    <button class="mutedBtn" id="finishCancelBtn" type="button">Abbrechen</button>
  </div>
  <div class="patientOutput hidden patientQrOutput" id="patientOutputBox">
    <b class="patientOutputTitle">Patient:innen</b>
    <p class="notice" id="patientShareNotice" style="margin-top:8px">Lokaler Test.</p>
    <a class="patientLink" id="patientAppLink" href="#" target="_blank" rel="noopener">Patienten-App öffnen</a>
    <button class="mutedBtn" style="width:100%;margin-top:8px" id="copyPatientLink" type="button">Link kopieren</button>
    <textarea class="patientLinkCopyField hidden" id="patientLinkCopyField" readonly aria-label="Patienten-Link zum manuellen Kopieren"></textarea>
    <div class="qrBox" id="patientQrBox"><span class="qrStatus">QR wird vorbereitet …</span></div>
    <div class="qrStatus" id="patientQrStatus"></div>
  </div>
  <details class="apiBox" id="debugPayloadBox">
    <summary>⚙️ Debug/Test: Roh-Payload intern anzeigen</summary>
    <p><b>Nicht für Patient:innen.</b> Dieser Bereich ist nur intern/therapeutisch/entwicklerisch zum Testen.</p>
    <textarea id="shareText" style="min-height:150px;font-size:13px"></textarea>
    <button class="mutedBtn" style="width:100%;margin-top:8px" id="copyShare">Debug-Payload kopieren</button>
  </details>
  <button class="mutedBtn hidden" style="width:100%;margin-top:8px" id="closeShare">Schließen</button>
</div></div>

<div class="modal" id="largePdfModal"><div class="sheet">
  <h2>Großdruck-PDF</h2>
  <p class="notice">Großdruck-PDF erzeugen?</p>
  <div class="grid2"><button class="mutedBtn" id="cancelLargePdf" type="button">Abbrechen</button><button class="primary" id="confirmLargePdf" type="button">PDF erzeugen</button></div>
</div></div>

<div class="modal" id="longMediaConfirmModal"><div class="sheet">
  <h2>24-Stunden-Code?</h2>
  <p class="notice">24h-Code erstellen? Bilddateien bleiben länger abrufbar.</p>
  <div class="grid2"><button class="mutedBtn" id="cancelLongMediaShare" type="button">Abbrechen</button><button class="primary" id="confirmLongMediaShare" type="button">Ja, erstellen</button></div>
</div></div>

<div class="modal" id="installPromptModal"><div class="sheet">
  <h2 id="installPromptTitle">App installieren?</h2>
  <p class="notice" id="installPromptText">Installieren und lokale Daten über Updates behalten.</p>
  <div class="grid2"><button class="mutedBtn" id="dismissInstallPrompt" type="button">Später</button><button class="primary" id="acceptInstallPrompt" type="button">Installieren</button></div>
</div></div>

<div class="modal" id="adminSecretsModal"><div class="sheet">
  <h2>Admin-Konfig</h2>
  <p class="notice">Codes bleiben nur lokal auf diesem Geraet. In dieser Admin-Testdatei sind keine API-Keys fest eingebaut.</p>
  <div class="field"><label>Gemini API-Key 1</label><input id="adminGeminiKey1" type="password" autocomplete="off" spellcheck="false"></div>
  <div class="field"><label>Gemini API-Key 2</label><input id="adminGeminiKey2" type="password" autocomplete="off" spellcheck="false"></div>
  <div class="field"><label>Medien-Dropzone URL</label><input id="adminMediaDropzoneEndpoint" type="url" autocomplete="off" spellcheck="false" placeholder="https://...workers.dev"></div>
  <div class="field"><label>Medien Upload-Code</label><input id="adminMediaDropzoneUploadToken" type="password" autocomplete="off" spellcheck="false"></div>
  <span class="secretStatus" id="adminSecretStatus">Keine lokalen Codes gespeichert.</span>
  <div class="adminCodePackageTools">
    <button class="mutedBtn wide" id="loadAdminSafeFile" type="button">Admin-Safe-Datei laden</button>
    <button class="mutedBtn" id="importAdminCodePackage" type="button">Code-Paket einfuegen</button>
    <button class="mutedBtn" id="exportAdminCodePackage" type="button">Code-Paket kopieren</button>
    <button class="mutedBtn wide" id="downloadAdminSafeFile" type="button">Admin-Safe-Datei speichern</button>
  </div>
  <input id="adminSafeFileInput" class="hidden" type="file" accept=".kggsafe,.bin,.txt,.json,text/plain,application/json,application/octet-stream,*/*">
  <div class="adminPackageHint">Admin-Safe-Dateien bleiben lokal und gehoeren nicht in GitHub, Chat oder Patient:innen-Ausgabe.</div>
  <div class="grid2" style="margin-top:12px"><button class="mutedBtn danger" id="clearAdminSecrets" type="button">Löschen</button><button class="primary" id="saveAdminSecrets" type="button">Lokal speichern</button></div>
  <button class="mutedBtn" id="closeAdminSecrets" type="button" style="width:100%;margin-top:8px">Schließen</button>
</div></div>

<div class="modal" id="sharedBankModal"><div class="sheet">
  <h2>Übungsdatenbank teilen</h2>
  <p class="notice">Nur Übungsdaten. Keine Patientendaten, keine Codes. Import löscht nichts.</p>
  <textarea class="sharedBankText" id="sharedBankText" spellcheck="false"></textarea>
  <input id="sharedBankFile" class="hidden" type="file" accept="application/json,.json">
  <span class="secretStatus" id="sharedBankStatus"></span>
  <div class="grid2" style="margin-top:12px"><button class="mutedBtn" id="copySharedBank" type="button">Export kopieren</button><button class="mutedBtn" id="pickSharedBankFile" type="button">Import-Datei</button></div>
  <div class="grid2" style="margin-top:8px"><button class="mutedBtn" id="closeSharedBank" type="button">Schließen</button><button class="primary" id="applySharedBank" type="button">Import übernehmen</button></div>
</div></div>

<div class="modal" id="syncPairModal"><div class="sheet syncPairSheet">
  <h2>Sync koppeln</h2>
  <p class="notice">Diesen QR auf weiteren Android-Geraeten mit <b>Plan scannen</b> einlesen. Alle Geraete im selben Sync-Raum schreiben eigene Dateien und koennen ausgewaehlte Therapeut:innen automatisch lesen. Keine Patientendaten, keine API-Keys.</p>
  <div class="qrBox syncPairQrBox" id="syncPairQrBox"><span class="qrStatus">QR wird vorbereitet ...</span></div>
  <span class="syncPairStatus" id="syncPairStatus"></span>
  <div class="syncPeerList hidden" id="syncPeerList"></div>
  <div class="syncDiagnostics hidden" id="syncDiagnostics"></div>
  <input class="hidden" id="syncImportInput" type="file" accept="application/json,.json">
  <div class="syncPairActions"><button class="mutedBtn" id="copySyncPairCode" type="button">Code kopieren</button><button class="mutedBtn" id="testNativeSyncBtn" type="button">Sync testen</button><button class="mutedBtn" id="downloadSyncFileBtn" type="button">Sync-Datei speichern</button><button class="mutedBtn" id="importSyncFileBtn" type="button">Sync-Datei importieren</button><button class="primary" id="closeSyncPairModal" type="button">Schliessen</button></div>
</div></div>

<div class="modal" id="pdfPreviewModal"><div class="sheet pdfPreviewSheet">
  <h2>PDF fertig</h2>
  <p class="notice" id="pdfPreviewNotice">PDF erzeugt.</p>
  <div class="pdfPreviewMobileBridge hidden" id="pdfPreviewMobileBridge">
    <button class="primary" id="openPdfPreviewMobileBridge" type="button">PDF öffnen</button>
    <small>Öffnet im Geräte-PDF-Viewer.</small>
  </div>
  <div class="pdfPreviewFallback hidden" id="pdfPreviewFallback">
    <div>Vorschau leer?<small>PDF trotzdem erzeugt.</small></div>
    <button class="mutedBtn" id="openPdfPreviewFallback" type="button">PDF öffnen</button>
  </div>
  <iframe class="pdfPreviewFrame" id="pdfPreviewFrame" title="PDF-Vorschau"></iframe>
  <div class="grid2"><button class="primary" id="printPdfPreview" type="button">Drucken</button><button class="mutedBtn" id="downloadPdfPreview" type="button">Herunterladen</button></div>
  <button class="mutedBtn" id="openPdfPreviewTab" type="button">Neues Fenster</button>
  <button class="mutedBtn" id="closePdfPreview" type="button">Schließen</button>
</div></div>

<script>
(function(){
  'use strict';
  function openSourceMediaDb(){
    return new Promise((resolve,reject)=>{
      const req=indexedDB.open('kgg_media_v1',1);
      req.onupgradeneeded=()=>{const db=req.result; if(!db.objectStoreNames.contains('encryptedBlobs'))db.createObjectStore('encryptedBlobs',{keyPath:'id'});};
      req.onsuccess=()=>resolve(req.result);
      req.onerror=()=>reject(req.error||new Error('Admin-Test-Medien-Speicher nicht verfuegbar'));
    });
  }
  async function getSourceMediaBlob(id){
    const db=await openSourceMediaDb();
    return new Promise((resolve,reject)=>{
      const tx=db.transaction('encryptedBlobs','readonly');
      const req=tx.objectStore('encryptedBlobs').get(id);
      req.onsuccess=()=>resolve(req.result&&req.result.blob||null);
      req.onerror=()=>reject(req.error||new Error('Admin-Test-Bild nicht gefunden'));
    });
  }
  window.KGGMediaUploadAdapter={
    name:'admin-test-mock-upload-adapter',
    isMock:true,
    async upload(blob,context){
      const manifest=context&&context.manifest||{};
      const id=manifest.id||('test_'+Date.now());
      const ttlSeconds=Number(context&&context.ttlSeconds)||300;
      return {
        downloadUrl:'https://admin-test.invalid/kgg-media/'+encodeURIComponent(id)+'.bin',
        storage:'admin-test-indexeddb',
        expiresAt:new Date(Date.now()+ttlSeconds*1000).toISOString()
      };
    },
    scheduleDelete(media,options){
      const delayMs=Number(options&&options.delayMs)||300000;
      setTimeout(()=>{console.info('ADMIN TEST media expired',media&&media.id);},delayMs);
    },
    delete(media){console.info('ADMIN TEST media deleted',media&&media.id);}
  };
  window.KGGPatientMediaFetchAdapter={
    async fetch(media){
      const blob=await getSourceMediaBlob(media&&media.id);
      if(!blob)throw new Error('Admin-Test-Bild nicht im lokalen Speicher gefunden');
      return blob;
    }
  };
```
