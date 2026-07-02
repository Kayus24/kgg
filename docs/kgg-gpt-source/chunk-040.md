# KGG Source Chunk 040

- Source: `kgg-update/index.html`
- Lines: 16801-17220

```html
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
})();
</script>

<script>
/*! qrcode-generator 1.5.2 | MIT License | Copyright (c) Kazuhiko Arase | https://kazuhikoarase.github.io/qrcode-generator/ */
var qrcode=function(){function i(t,r){function a(t,r){l=function(t){for(var r=new Array(t),e=0;e<t;e+=1){r[e]=new Array(t);for(var n=0;n<t;n+=1)r[e][n]=null}return r}(h=4*u+17),e(0,0),e(h-7,0),e(0,h-7),i(),o(),s(t,r),7<=u&&g(t),null==n&&(n=v(u,f,c)),d(n,r)}var u=t,f=p[r],l=null,h=0,n=null,c=[],x={},e=function(t,r){for(var e=-1;e<=7;e+=1)if(!(t+e<=-1||h<=t+e))for(var n=-1;n<=7;n+=1)r+n<=-1||h<=r+n||(l[t+e][r+n]=0<=e&&e<=6&&(0==n||6==n)||0<=n&&n<=6&&(0==e||6==e)||2<=e&&e<=4&&2<=n&&n<=4)},o=function(){for(var t=8;t<h-8;t+=1)null==l[t][6]&&(l[t][6]=t%2==0);for(var r=8;r<h-8;r+=1)null==l[6][r]&&(l[6][r]=r%2==0)},i=function(){for(var t=M.getPatternPosition(u),r=0;r<t.length;r+=1)for(var e=0;e<t.length;e+=1){var n=t[r],o=t[e];if(null==l[n][o])for(var i=-2;i<=2;i+=1)for(var a=-2;a<=2;a+=1)l[n+i][o+a]=-2==i||2==i||-2==a||2==a||0==i&&0==a}},g=function(t){for(var r=M.getBCHTypeNumber(u),e=0;e<18;e+=1){var n=!t&&1==(r>>e&1);l[Math.floor(e/3)][e%3+h-8-3]=n}for(e=0;e<18;e+=1){n=!t&&1==(r>>e&1);l[e%3+h-8-3][Math.floor(e/3)]=n}},s=function(t,r){for(var r=f<<3|r,e=M.getBCHTypeInfo(r),n=0;n<15;n+=1){var o=!t&&1==(e>>n&1);n<6?l[n][8]=o:n<8?l[n+1][8]=o:l[h-15+n][8]=o}for(n=0;n<15;n+=1){o=!t&&1==(e>>n&1);n<8?l[8][h-n-1]=o:n<9?l[8][15-n-1+1]=o:l[8][15-n-1]=o}l[h-8][8]=!t},d=function(t,r){for(var e=-1,n=h-1,o=7,i=0,a=M.getMaskFunction(r),u=h-1;0<u;u-=2)for(6==u&&--u;;){for(var f,c,g=0;g<2;g+=1)null==l[n][u-g]&&(f=!1,i<t.length&&(f=1==(t[i]>>>o&1)),c=a(n,u-g),l[n][u-g]=f=c?!f:f,-1==--o&&(i+=1,o=7));if((n+=e)<0||h<=n){n-=e,e=-e;break}}},v=function(t,r,e){for(var n=L.getRSBlocks(t,r),o=D(),i=0;i<e.length;i+=1){var a=e[i];o.put(a.getMode(),4),o.put(a.getLength(),M.getLengthInBits(a.getMode(),t)),a.write(o)}for(var u=0,i=0;i<n.length;i+=1)u+=n[i].dataCount;if(o.getLengthInBits()>8*u)throw"code length overflow. ("+o.getLengthInBits()+">"+8*u+")";for(o.getLengthInBits()+4<=8*u&&o.put(0,4);o.getLengthInBits()%8!=0;)o.putBit(!1);for(;;){if(o.getLengthInBits()>=8*u)break;if(o.put(236,8),o.getLengthInBits()>=8*u)break;o.put(17,8)}for(var f=o,c=n,g=0,l=0,h=0,s=new Array(c.length),d=new Array(c.length),v=0;v<c.length;v+=1){var w=c[v].dataCount,p=c[v].totalCount-w,l=Math.max(l,w),h=Math.max(h,p);s[v]=new Array(w);for(var y=0;y<s[v].length;y+=1)s[v][y]=255&f.getBuffer()[y+g];g+=w;var w=M.getErrorCorrectPolynomial(p),B=m(s[v],w.getLength()-1).mod(w);d[v]=new Array(w.getLength()-1);for(y=0;y<d[v].length;y+=1){var k=y+B.getLength()-d[v].length;d[v][y]=0<=k?B.getAt(k):0}}for(var C=0,y=0;y<c.length;y+=1)C+=c[y].totalCount;for(var A=new Array(C),b=0,y=0;y<l;y+=1)for(v=0;v<c.length;v+=1)y<s[v].length&&(A[b]=s[v][y],b+=1);for(y=0;y<h;y+=1)for(v=0;v<c.length;v+=1)y<d[v].length&&(A[b]=d[v][y],b+=1);return A},w=(x.addData=function(t,r){var e=null;switch(r=r||"Byte"){case"Numeric":e=C(t);break;case"Alphanumeric":e=A(t);break;case"Byte":e=b(t);break;case"Kanji":e=S(t);break;default:throw"mode:"+r}c.push(e),n=null},x.isDark=function(t,r){if(t<0||h<=t||r<0||h<=r)throw t+","+r;return l[t][r]},x.getModuleCount=function(){return h},x.make=function(){if(u<1){for(var t=1;t<40;t++){for(var r=L.getRSBlocks(t,f),e=D(),n=0;n<c.length;n++){var o=c[n];e.put(o.getMode(),4),e.put(o.getLength(),M.getLengthInBits(o.getMode(),t)),o.write(e)}for(var i=0,n=0;n<r.length;n++)i+=r[n].dataCount;if(e.getLengthInBits()<=8*i)break}u=t}a(!1,function(){for(var t=0,r=0,e=0;e<8;e+=1){a(!0,e);var n=M.getLostPoint(x);(0==e||n<t)&&(t=n,r=e)}return r}())},x.createTableTag=function(t,r){t=t||2;for(var e=(e=(e=(e="")+'<table style="'+" border-width: 0px; border-style: none;")+" border-collapse: collapse;"+(" padding: 0px; margin: "+(r=void 0===r?4*t:r)+"px;"))+'">'+"<tbody>",n=0;n<x.getModuleCount();n+=1){e+="<tr>";for(var o=0;o<x.getModuleCount();o+=1)e=(e=(e=(e+='<td style=" border-width: 0px; border-style: none; border-collapse: collapse;')+" padding: 0px; margin: 0px; width: "+t+"px;")+" height: "+t+"px; background-color: ")+(x.isDark(n,o)?"#000000":"#ffffff")+';"/>';e+="</tr>"}return e=e+"</tbody>"+"</table>"},x.createSvgTag=function(t,r,e,n){for(var o,i,a={},u=("object"==typeof arguments[0]&&(t=(a=arguments[0]).cellSize,r=a.margin,e=a.alt,n=a.title),t=t||2,r=void 0===r?4*t:r,(e="string"==typeof e?{text:e}:e||{}).text=e.text||null,e.id=e.text?e.id||"qrcode-description":null,(n="string"==typeof n?{text:n}:n||{}).text=n.text||null,n.id=n.text?n.id||"qrcode-title":null,x.getModuleCount()*t+2*r),f="l"+t+",0 0,"+t+" -"+t+",0 0,-"+t+"z ",c=(c=(c=(c=(c=(c=(c="")+'<svg version="1.1" xmlns="http://www.w3.org/2000/svg"'+(a.scalable?"":' width="'+u+'px" height="'+u+'px"'))+(' viewBox="0 0 '+u+" "+u+'" ')+' preserveAspectRatio="xMinYMin meet"')+(n.text||e.text?' role="img" aria-labelledby="'+w([n.id,e.id].join(" ").trim())+'"':"")+">")+(n.text?'<title id="'+w(n.id)+'">'+w(n.text)+"</title>":""))+(e.text?'<description id="'+w(e.id)+'">'+w(e.text)+"</description>":""))+'<rect width="100%" height="100%" fill="white" cx="0" cy="0"/>'+'<path d="',g=0;g<x.getModuleCount();g+=1)for(i=g*t+r,o=0;o<x.getModuleCount();o+=1)x.isDark(g,o)&&(c+="M"+(o*t+r)+","+i+f);return c=c+'" stroke="transparent" fill="black"/>'+"</svg>"},x.createDataURL=function(e,t){e=e||2,t=void 0===t?4*e:t;var r=x.getModuleCount()*e+2*t,n=t,o=r-t;return T(r,r,function(t,r){return n<=t&&t<o&&n<=r&&r<o?(t=Math.floor((t-n)/e),r=Math.floor((r-n)/e),x.isDark(r,t)?0:1):1})},x.createImgTag=function(t,r,e){t=t||2,r=void 0===r?4*t:r;var n=x.getModuleCount()*t+2*r,o=(o=(o=(o=(o=(o="")+"<img"+' src="')+x.createDataURL(t,r)+'"')+' width="'+n)+'"'+' height="')+n+'"';return e&&(o=(o+=' alt="')+w(e)+'"'),o+="/>"},function(t){for(var r="",e=0;e<t.length;e+=1){var n=t.charAt(e);switch(n){case"<":r+="&lt;";break;case">":r+="&gt;";break;case"&":r+="&amp;";break;case'"':r+="&quot;";break;default:r+=n}}return r});return x.createASCII=function(t,r){if((t=t||1)<2){var e=r;e=void 0===e?2:e;for(var n,o,i,a,u=+x.getModuleCount()+2*e,f=e,c=u-e,g={"██":"█","█ ":"▀"," █":"▄","  ":" "},l={"██":"▀","█ ":"▀"," █":" ","  ":" "},h="",s=0;s<u;s+=2){for(o=Math.floor(s-f),i=Math.floor(s+1-f),n=0;n<u;n+=1)a="█",f<=n&&n<c&&f<=s&&s<c&&x.isDark(o,Math.floor(n-f))&&(a=" "),f<=n&&n<c&&f<=s+1&&s+1<c&&x.isDark(i,Math.floor(n-f))?a+=" ":a+="█",h+=(e<1&&c<=s+1?l:g)[a];h+="\n"}return u%2&&0<e?h.substring(0,h.length-u-1)+Array(1+u).join("▀"):h.substring(0,h.length-1)}--t,r=void 0===r?2*t:r;for(var d,v,w,p=x.getModuleCount()*t+2*r,y=r,B=p-r,k=Array(t+1).join("██"),C=Array(t+1).join("  "),A="",b="",M=0;M<p;M+=1){for(v=Math.floor((M-y)/t),b="",d=0;d<p;d+=1)w=1,b+=(w=y<=d&&d<B&&y<=M&&M<B&&x.isDark(v,Math.floor((d-y)/t))?0:w)?k:C;for(v=0;v<t;v+=1)A+=b+"\n"}return A.substring(0,A.length-1)},x.renderTo2dContext=function(t,r){r=r||2;for(var e=x.getModuleCount(),n=0;n<e;n++)for(var o=0;o<e;o++)t.fillStyle=x.isDark(n,o)?"black":"white",t.fillRect(n*r,o*r,r,r)},x}i.stringToBytes=(i.stringToBytesFuncs={default:function(t){for(var r=[],e=0;e<t.length;e+=1){var n=t.charCodeAt(e);r.push(255&n)}return r}}).default,i.createStringToBytes=function(f,c){var o=function(){function t(){var t=r.read();if(-1==t)throw"eof";return t}for(var r=I(f),e=0,n={};;){var o=r.read();if(-1==o)break;var i=t(),a=t(),u=t();n[String.fromCharCode(o<<8|i)]=a<<8|u,e+=1}if(e!=c)throw e+" != "+c;return n}(),i="?".charCodeAt(0);return function(t){for(var r=[],e=0;e<t.length;e+=1){var n=t.charCodeAt(e);n<128?r.push(n):"number"==typeof(n=o[t.charAt(e)])?(255&n)==n?r.push(n):(r.push(n>>>8),r.push(255&n)):r.push(i)}return r}};var r,e=1,a=2,n=4,u=8,p={L:1,M:0,Q:3,H:2},o=0,f=1,c=2,g=3,l=4,h=5,s=6,d=7,M=(r=[[],[6,18],[6,22],[6,26],[6,30],[6,34],[6,22,38],[6,24,42],[6,26,46],[6,28,50],[6,30,54],[6,32,58],[6,34,62],[6,26,46,66],[6,26,48,70],[6,26,50,74],[6,30,54,78],[6,30,56,82],[6,30,58,86],[6,34,62,90],[6,28,50,72,94],[6,26,50,74,98],[6,30,54,78,102],[6,28,54,80,106],[6,32,58,84,110],[6,30,58,86,114],[6,34,62,90,118],[6,26,50,74,98,122],[6,30,54,78,102,126],[6,26,52,78,104,130],[6,30,56,82,108,134],[6,34,60,86,112,138],[6,30,58,86,114,142],[6,34,62,90,118,146],[6,30,54,78,102,126,150],[6,24,50,76,102,128,154],[6,28,54,80,106,132,158],[6,32,58,84,110,136,162],[6,26,54,82,110,138,166],[6,30,58,86,114,142,170]],(t={}).getBCHTypeInfo=function(t){for(var r=t<<10;0<=v(r)-v(1335);)r^=1335<<v(r)-v(1335);return 21522^(t<<10|r)},t.getBCHTypeNumber=function(t){for(var r=t<<12;0<=v(r)-v(7973);)r^=7973<<v(r)-v(7973);return t<<12|r},t.getPatternPosition=function(t){return r[t-1]},t.getMaskFunction=function(t){switch(t){case o:return function(t,r){return(t+r)%2==0};case f:return function(t,r){return t%2==0};case c:return function(t,r){return r%3==0};case g:return function(t,r){return(t+r)%3==0};case l:return function(t,r){return(Math.floor(t/2)+Math.floor(r/3))%2==0};case h:return function(t,r){return t*r%2+t*r%3==0};case s:return function(t,r){return(t*r%2+t*r%3)%2==0};case d:return function(t,r){return(t*r%3+(t+r)%2)%2==0};default:throw"bad maskPattern:"+t}},t.getErrorCorrectPolynomial=function(t){for(var r=m([1],0),e=0;e<t;e+=1)r=r.multiply(m([1,w.gexp(e)],0));return r},t.getLengthInBits=function(t,r){if(1<=r&&r<10)switch(t){case e:return 10;case a:return 9;case n:case u:return 8;default:throw"mode:"+t}else if(r<27)switch(t){case e:return 12;case a:return 11;case n:return 16;case u:return 10;default:throw"mode:"+t}else{if(!(r<41))throw"type:"+r;switch(t){case e:return 14;case a:return 13;case n:return 16;case u:return 12;default:throw"mode:"+t}}},t.getLostPoint=function(t){for(var r=t.getModuleCount(),e=0,n=0;n<r;n+=1)for(var o=0;o<r;o+=1){for(var i=0,a=t.isDark(n,o),u=-1;u<=1;u+=1)if(!(n+u<0||r<=n+u))for(var f=-1;f<=1;f+=1)o+f<0||r<=o+f||0==u&&0==f||a==t.isDark(n+u,o+f)&&(i+=1);5<i&&(e+=3+i-5)}for(n=0;n<r-1;n+=1)for(o=0;o<r-1;o+=1){var c=0;t.isDark(n,o)&&(c+=1),t.isDark(n+1,o)&&(c+=1),t.isDark(n,o+1)&&(c+=1),t.isDark(n+1,o+1)&&(c+=1),0!=c&&4!=c||(e+=3)}for(n=0;n<r;n+=1)for(o=0;o<r-6;o+=1)t.isDark(n,o)&&!t.isDark(n,o+1)&&t.isDark(n,o+2)&&t.isDark(n,o+3)&&t.isDark(n,o+4)&&!t.isDark(n,o+5)&&t.isDark(n,o+6)&&(e+=40);for(o=0;o<r;o+=1)for(n=0;n<r-6;n+=1)t.isDark(n,o)&&!t.isDark(n+1,o)&&t.isDark(n+2,o)&&t.isDark(n+3,o)&&t.isDark(n+4,o)&&!t.isDark(n+5,o)&&t.isDark(n+6,o)&&(e+=40);for(var g=0,o=0;o<r;o+=1)for(n=0;n<r;n+=1)t.isDark(n,o)&&(g+=1);return e+=10*(Math.abs(100*g/r/r-50)/5)},t);function v(t){for(var r=0;0!=t;)r+=1,t>>>=1;return r}var w=function(){for(var r=new Array(256),e=new Array(256),t=0;t<8;t+=1)r[t]=1<<t;for(t=8;t<256;t+=1)r[t]=r[t-4]^r[t-5]^r[t-6]^r[t-8];for(t=0;t<255;t+=1)e[r[t]]=t;var n={glog:function(t){if(t<1)throw"glog("+t+")";return e[t]},gexp:function(t){for(;t<0;)t+=255;for(;256<=t;)t-=255;return r[t]}};return n}();function m(n,o){if(void 0===n.length)throw n.length+"/"+o;var r=function(){for(var t=0;t<n.length&&0==n[t];)t+=1;for(var r=new Array(n.length-t+o),e=0;e<n.length-t;e+=1)r[e]=n[e+t];return r}(),i={getAt:function(t){return r[t]},getLength:function(){return r.length},multiply:function(t){for(var r=new Array(i.getLength()+t.getLength()-1),e=0;e<i.getLength();e+=1)for(var n=0;n<t.getLength();n+=1)r[e+n]^=w.gexp(w.glog(i.getAt(e))+w.glog(t.getAt(n)));return m(r,0)},mod:function(t){if(i.getLength()-t.getLength()<0)return i;for(var r=w.glog(i.getAt(0))-w.glog(t.getAt(0)),e=new Array(i.getLength()),n=0;n<i.getLength();n+=1)e[n]=i.getAt(n);for(n=0;n<t.getLength();n+=1)e[n]^=w.gexp(w.glog(t.getAt(n))+r);return m(e,0).mod(t)}};return i}function y(){function e(t){a+=String.fromCharCode(function(t){if(t<0);else if(t<26)return 65+t;else if(t<52)return 97+(t-26);else if(t<62)return 48+(t-52);else if(t==62)return 43;else if(t==63)return 47;throw"n:"+t}(63&t))}var n=0,o=0,i=0,a="",t={writeByte:function(t){for(n=n<<8|255&t,o+=8,i+=1;6<=o;)e(n>>>o-6),o-=6},flush:function(){if(0<o&&(e(n<<6-o),o=n=0),i%3!=0)for(var t=3-i%3,r=0;r<t;r+=1)a+="="},toString:function(){return a}};return t}function B(t,r){var n=t,o=r,s=new Array(t*r),i=function(t){for(var r=1<<t,e=1+(1<<t),n=t+1,o=d(),i=0;i<r;i+=1)o.add(String.fromCharCode(i));o.add(String.fromCharCode(r)),o.add(String.fromCharCode(e));var a,u,f,t=x(),c=(a=t,f=u=0,{write:function(t,r){if(t>>>r!=0)throw"length over";for(;8<=u+r;)a.writeByte(255&(t<<u|f)),r-=8-u,t>>>=8-u,u=f=0;f|=t<<u,u+=r},flush:function(){0<u&&a.writeByte(f)}}),g=(c.write(r,n),0),l=String.fromCharCode(s[g]);for(g+=1;g<s.length;){var h=String.fromCharCode(s[g]);g+=1,o.contains(l+h)?l+=h:(c.write(o.indexOf(l),n),o.size()<4095&&(o.size()==1<<n&&(n+=1),o.add(l+h)),l=h)}return c.write(o.indexOf(l),n),c.write(e,n),c.flush(),t.toByteArray()},d=function(){var r={},e=0,n={add:function(t){if(n.contains(t))throw"dup key:"+t;r[t]=e,e+=1},size:function(){return e},indexOf:function(t){return r[t]},contains:function(t){return void 0!==r[t]}};return n};return t={setPixel:function(t,r,e){s[r*n+t]=e},write:function(t){t.writeString("GIF87a"),t.writeShort(n),t.writeShort(o),t.writeByte(128),t.writeByte(0),t.writeByte(0),t.writeByte(0),t.writeByte(0),t.writeByte(0),t.writeByte(255),t.writeByte(255),t.writeByte(255),t.writeString(","),t.writeShort(0),t.writeShort(0),t.writeShort(n),t.writeShort(o),t.writeByte(0);for(var r=i(2),e=(t.writeByte(2),0);255<r.length-e;)t.writeByte(255),t.writeBytes(r,e,255),e+=255;t.writeByte(r.length-e),t.writeBytes(r,e,r.length-e),t.writeByte(0),t.writeString(";")}}}k=[[1,26,19],[1,26,16],[1,26,13],[1,26,9],[1,44,34],[1,44,28],[1,44,22],[1,44,16],[1,70,55],[1,70,44],[2,35,17],[2,35,13],[1,100,80],[2,50,32],[2,50,24],[4,25,9],[1,134,108],[2,67,43],[2,33,15,2,34,16],[2,33,11,2,34,12],[2,86,68],[4,43,27],[4,43,19],[4,43,15],[2,98,78],[4,49,31],[2,32,14,4,33,15],[4,39,13,1,40,14],[2,121,97],[2,60,38,2,61,39],[4,40,18,2,41,19],[4,40,14,2,41,15],[2,146,116],[3,58,36,2,59,37],[4,36,16,4,37,17],[4,36,12,4,37,13],[2,86,68,2,87,69],[4,69,43,1,70,44],[6,43,19,2,44,20],[6,43,15,2,44,16],[4,101,81],[1,80,50,4,81,51],[4,50,22,4,51,23],[3,36,12,8,37,13],[2,116,92,2,117,93],[6,58,36,2,59,37],[4,46,20,6,47,21],[7,42,14,4,43,15],[4,133,107],[8,59,37,1,60,38],[8,44,20,4,45,21],[12,33,11,4,34,12],[3,145,115,1,146,116],[4,64,40,5,65,41],[11,36,16,5,37,17],[11,36,12,5,37,13],[5,109,87,1,110,88],[5,65,41,5,66,42],[5,54,24,7,55,25],[11,36,12,7,37,13],[5,122,98,1,123,99],[7,73,45,3,74,46],[15,43,19,2,44,20],[3,45,15,13,46,16],[1,135,107,5,136,108],[10,74,46,1,75,47],[1,50,22,15,51,23],[2,42,14,17,43,15],[5,150,120,1,151,121],[9,69,43,4,70,44],[17,50,22,1,51,23],[2,42,14,19,43,15],[3,141,113,4,142,114],[3,70,44,11,71,45],[17,47,21,4,48,22],[9,39,13,16,40,14],[3,135,107,5,136,108],[3,67,41,13,68,42],[15,54,24,5,55,25],[15,43,15,10,44,16],[4,144,116,4,145,117],[17,68,42],[17,50,22,6,51,23],[19,46,16,6,47,17],[2,139,111,7,140,112],[17,74,46],[7,54,24,16,55,25],[34,37,13],[4,151,121,5,152,122],[4,75,47,14,76,48],[11,54,24,14,55,25],[16,45,15,14,46,16],[6,147,117,4,148,118],[6,73,45,14,74,46],[11,54,24,16,55,25],[30,46,16,2,47,17],[8,132,106,4,133,107],[8,75,47,13,76,48],[7,54,24,22,55,25],[22,45,15,13,46,16],[10,142,114,2,143,115],[19,74,46,4,75,47],[28,50,22,6,51,23],[33,46,16,4,47,17],[8,152,122,4,153,123],[22,73,45,3,74,46],[8,53,23,26,54,24],[12,45,15,28,46,16],[3,147,117,10,148,118],[3,73,45,23,74,46],[4,54,24,31,55,25],[11,45,15,31,46,16],[7,146,116,7,147,117],[21,73,45,7,74,46],[1,53,23,37,54,24],[19,45,15,26,46,16],[5,145,115,10,146,116],[19,75,47,10,76,48],[15,54,24,25,55,25],[23,45,15,25,46,16],[13,145,115,3,146,116],[2,74,46,29,75,47],[42,54,24,1,55,25],[23,45,15,28,46,16],[17,145,115],[10,74,46,23,75,47],[10,54,24,35,55,25],[19,45,15,35,46,16],[17,145,115,1,146,116],[14,74,46,21,75,47],[29,54,24,19,55,25],[11,45,15,46,46,16],[13,145,115,6,146,116],[14,74,46,23,75,47],[44,54,24,7,55,25],[59,46,16,1,47,17],[12,151,121,7,152,122],[12,75,47,26,76,48],[39,54,24,14,55,25],[22,45,15,41,46,16],[6,151,121,14,152,122],[6,75,47,34,76,48],[46,54,24,10,55,25],[2,45,15,64,46,16],[17,152,122,4,153,123],[29,74,46,14,75,47],[49,54,24,10,55,25],[24,45,15,46,46,16],[4,152,122,18,153,123],[13,74,46,32,75,47],[48,54,24,14,55,25],[42,45,15,32,46,16],[20,147,117,4,148,118],[40,75,47,7,76,48],[43,54,24,22,55,25],[10,45,15,67,46,16],[19,148,118,6,149,119],[18,75,47,31,76,48],[34,54,24,34,55,25],[20,45,15,61,46,16]],(t={}).getRSBlocks=function(t,r){var e=function(t,r){switch(r){case p.L:return k[4*(t-1)+0];case p.M:return k[4*(t-1)+1];case p.Q:return k[4*(t-1)+2];case p.H:return k[4*(t-1)+3];default:return}}(t,r);if(void 0===e)throw"bad rs block @ typeNumber:"+t+"/errorCorrectionLevel:"+r;for(var n,o,i=e.length/3,a=[],u=0;u<i;u+=1)for(var f=e[3*u+0],c=e[3*u+1],g=e[3*u+2],l=0;l<f;l+=1)a.push((n=g,void 0,(o={}).totalCount=c,o.dataCount=n,o));return a};var k,t,L=t,D=function(){var e=[],n=0,o={getBuffer:function(){return e},getAt:function(t){var r=Math.floor(t/8);return 1==(e[r]>>>7-t%8&1)},put:function(t,r){for(var e=0;e<r;e+=1)o.putBit(1==(t>>>r-e-1&1))},getLengthInBits:function(){return n},putBit:function(t){var r=Math.floor(n/8);e.length<=r&&e.push(0),t&&(e[r]|=128>>>n%8),n+=1}};return o},C=function(t){var r=e,n=t,t={getMode:function(){return r},getLength:function(t){return n.length},write:function(t){for(var r=n,e=0;e+2<r.length;)t.put(o(r.substring(e,e+3)),10),e+=3;e<r.length&&(r.length-e==1?t.put(o(r.substring(e,e+1)),4):r.length-e==2&&t.put(o(r.substring(e,e+2)),7))}},o=function(t){for(var r=0,e=0;e<t.length;e+=1)r=10*r+i(t.charAt(e));return r},i=function(t){if("0"<=t&&t<="9")return t.charCodeAt(0)-"0".charCodeAt(0);throw"illegal char :"+t};return t},A=function(t){var r=a,n=t,t={getMode:function(){return r},getLength:function(t){return n.length},write:function(t){for(var r=n,e=0;e+1<r.length;)t.put(45*o(r.charAt(e))+o(r.charAt(e+1)),11),e+=2;e<r.length&&t.put(o(r.charAt(e)),6)}},o=function(t){if("0"<=t&&t<="9")return t.charCodeAt(0)-"0".charCodeAt(0);if("A"<=t&&t<="Z")return t.charCodeAt(0)-"A".charCodeAt(0)+10;switch(t){case" ":return 36;case"$":return 37;case"%":return 38;case"*":return 39;case"+":return 40;case"-":return 41;case".":return 42;case"/":return 43;case":":return 44;default:throw"illegal char :"+t}};return t},b=function(t){var r=n,e=i.stringToBytes(t),t={getMode:function(){return r},getLength:function(t){return e.length},write:function(t){for(var r=0;r<e.length;r+=1)t.put(e[r],8)}};return t},S=function(t){var r=u,e=i.stringToBytesFuncs.SJIS;if(!e)throw"sjis not supported.";var n=e("å‹");if(2!=n.length||38726!=(n[0]<<8|n[1]))throw"sjis not supported.";var o=e(t),n={getMode:function(){return r},getLength:function(t){return~~(o.length/2)},write:function(t){for(var r=o,e=0;e+1<r.length;){var n=(255&r[e])<<8|255&r[e+1];if(33088<=n&&n<=40956)n-=33088;else{if(!(57408<=n&&n<=60351))throw"illegal char at "+(e+1)+"/"+n;n-=49472}t.put(n=192*(n>>>8&255)+(255&n),13),e+=2}if(e<r.length)throw"illegal char at "+(e+1)}};return n},x=function(){var e=[],o={writeByte:function(t){e.push(255&t)},writeShort:function(t){o.writeByte(t),o.writeByte(t>>>8)},writeBytes:function(t,r,e){r=r||0,e=e||t.length;for(var n=0;n<e;n+=1)o.writeByte(t[n+r])},writeString:function(t){for(var r=0;r<t.length;r+=1)o.writeByte(t.charCodeAt(r))},toByteArray:function(){return e},toString:function(){var t="";t+="[";for(var r=0;r<e.length;r+=1)0<r&&(t+=","),t+=e[r];return t+="]"}};return o},I=function(t){var e=t,n=0,o=0,i=0,t={read:function(){for(;i<8;){if(n>=e.length){if(0==i)return-1;throw"unexpected end of file./"+i}var t=e.charAt(n);if(n+=1,"="==t)return i=0,-1;t.match(/^\s$/)||(o=o<<6|a(t.charCodeAt(0)),i+=6)}var r=o>>>i-8&255;return i-=8,r}},a=function(t){if(65<=t&&t<=90)return t-65;if(97<=t&&t<=122)return t-97+26;if(48<=t&&t<=57)return t-48+52;if(43==t)return 62;if(47==t)return 63;throw"c:"+t};return t},T=function(t,r,e){for(var n=B(t,r),o=0;o<r;o+=1)for(var i=0;i<t;i+=1)n.setPixel(i,o,e(i,o));for(var a=x(),u=(n.write(a),y()),f=a.toByteArray(),c=0;c<f.length;c+=1)u.writeByte(f[c]);return u.flush(),"data:image/gif;base64,"+u};return i}();qrcode.stringToBytesFuncs["UTF-8"]=function(t){for(var r=t,e=[],n=0;n<r.length;n++){var o=r.charCodeAt(n);o<128?e.push(o):o<2048?e.push(192|o>>6,128|63&o):o<55296||57344<=o?e.push(224|o>>12,128|o>>6&63,128|63&o):(n++,o=65536+((1023&o)<<10|1023&r.charCodeAt(n)),e.push(240|o>>18,128|o>>12&63,128|o>>6&63,128|63&o))}return e},function(t){"function"==typeof define&&define.amd?define([],t):"object"==typeof exports&&(module.exports=t())}(function(){return qrcode});
</script>

<script>
(function(){'use strict';
  const VERSION='KGG_GITHUB_UPDATE_v056_patient_qr_root_query';
  window.KGG_ROLLOUT_PROFILE='admin';
  const SAFE_SOURCE_NOTE='Based on clean v2 app candidate. Legacy v155 is reference only; no hardcoded API keys. Textfeld ist Master; DB-Vorschlaege werden erst nach Auswahl uebernommen. Grossdruck ist ein PDF-Modus.';
  const PDF_RUNTIME_FINGERPRINT='PDF_ENGINE: TEMPLATE_MATCH_V1_RUNTIME_GUARD';
  const KGG_BUILD_INFO={release:'v056',buildTime:'2026-07-02T00:00:00+02:00',buildCode:'github-update-v056-patient-qr-root-query',htmlFile:'kgg-update/index.html'};
  // Feste Patienten-App-Basis-URL. Leer/ueberschreiben nur fuer lokalen Testmodus.
  const KGG_PATIENT_LATEST_BASE_URL='https://kayus24.github.io/kgg/';
  const patientBaseUrl=(window.KGG_PATIENT_BASE_URL||KGG_PATIENT_LATEST_BASE_URL).trim();
  const GEMINI_SCAN_MODEL='gemini-2.5-flash';
  const $=id=>document.getElementById(id);
  const storageKey='kgg_html_app_v2_state';
  const customBankKey='kgg_html_app_v2_custom_exercise_bank';
  const deletedBankKey='kgg_html_app_v2_deleted_exercise_bank_ids';
  const pwaInstallPromptSeenKey='kgg_pwa_install_prompt_seen_v1';
  const pwaServiceWorkerUrl='kgg_therapist_sw.js';

  const kggUpdateManifestUrl='https://kayus24.github.io/kgg/therapist-app/kgg_update_manifest.json';
  const kggAutoUpdateCheckMs=30*60*1000;
  const kggAutoUpdateSessionKey='kgg_auto_update_target_v1';
  const adminSecretsKey='kgg_admin_local_secrets_v1';
  let deferredInstallPrompt=null;
  let adminSecrets={geminiKeys:[],mediaDropzoneEndpoint:'',mediaDropzoneUploadToken:'',updatedAt:''};
  const norm=s=>String(s||'').toLowerCase().replace(/[ä]/g,'ae').replace(/[ö]/g,'oe').replace(/[ü]/g,'ue').replace(/[ß]/g,'ss').replace(/[^a-z0-9]+/g,' ').trim();
  const compact=s=>norm(s).replace(/\s+/g,'');
  const bank=[
    ['abd','Abduktion Maschine','abd,abduktion,abductor,abduktor,hüft abduktion',3,'Wdh','kg'],['add','Adduktion Maschine','add,adduktion,adduktor,adductor,hüft adduktion',3,'Wdh','kg'],['legpress','Beinpresse','beinpresse,bein presse,leg press,presse',3,'Wdh','kg'],['bridge','Bridging','bridge,bridging,beckenheben,glute bridge',3,'Wdh','kg'],['copenhagen','Copenhagen Plank','copenhagen,adduktoren plank',3,'Zeit','keine'],['bike','Ergometer / Bike','fahrrad,bike,ergometer,warmup,cardio,rad',1,'Zeit','Stufe/Watt'],['fire','Fire Hydrants','fire hydrant,hydrants,vierfüßler abduktion',3,'Wdh','kg'],['hipthrust','Hip Thrust','hip thrust,glute thrust',3,'Wdh','kg'],['legcurl','Kniebeuger Maschine','kniebeuger,leg curl,hamstring curl,beinbeuger',3,'Wdh','kg'],['kneeext','Kniestrecker Maschine','kniestrecker,knieextension,beinstrecker,leg extension,knei ext',3,'Wdh','kg'],['row','Rudern','rudern,seated row,kabelrudern,ruderzug',3,'Wdh','kg'],['lat','Latziehen','latziehen,latzug,lat pulldown,pulldown,lat',3,'Wdh','kg'],['pallof','Pallof Press','pallof,pallof press,anti rotation',3,'Wdh','kg'],['plank','Plank','plank,blank,unterarmstütz,stütz',3,'Zeit','keine'],['squat','Squat','squat,kniebeuge,kniebeugen',3,'Wdh','kg'],['rdl','Romanian Deadlift','romanian deadlift,rdl,dead lift',3,'Wdh','kg'],['deadlift','Wadenheben','wadenheben,calf raise',3,'Wdh','kg'],['shoulder','Schulterpresse','schulter presse,shoulder press',3,'Wdh','kg']
  ].map(a=>({id:a[0],name:a[1],aliases:a[2],sets:a[3],unit:a[4],weightUnit:a[5]}));
  let state={plan:[],recent:[],packages:[{id:'pkg1',name:'Knie Standard',exercises:['Beinpresse','Kniebeuger Maschine','Kniestrecker Maschine']},{id:'pkg2',name:'Rücken Standard',exercises:['Rudern','Latziehen','Pallof Press']}],patient:{},bankOpen:false,editId:null,sortMenuId:null,reorderSuppressClick:false,largePdfMode:false,textSyncing:false};
  let bankSelectMode='replaceActive';
  let deletedBankIds=new Set();
  let pendingBankDeleteId=null;
  let bankSwipeSuppressClickUntil=0;
  const MEDIA_UPLOAD_TTL_SECONDS=300;
  const MEDIA_UPLOAD_LONG_TTL_SECONDS=86400;
  const MEDIA_LONG_PRESS_MS=5000;
  const MEDIA_RETRY_SECONDS=240;
  const MEDIA_IMAGE_MAX_DIM=1280;
  const MEDIA_IMAGE_QUALITY=.78;
  const mediaDbName='kgg_media_v1';
  const mediaStoreName='encryptedBlobs';
  let mediaDbPromise=null;
  let patientShareTtlSeconds=MEDIA_UPLOAD_TTL_SECONDS;
  let lastPatientSharePlanSnapshot=null;
  let lastPatientMediaBundleManifest=null;
  let copyPatientLinkSuppressClickUntil=0;
  const mediaDropzoneRuntimeTokens={};

  // v2 Plan-State-Adapter: KGGDataStore.currentPlan ist die zentrale Planquelle.
  // state.plan bleibt als bestehender UI-/Legacy-Spiegel erhalten.
  function makeLocalId(){return 'p_'+Date.now()+'_'+Math.random().toString(36).slice(2,8)}
  function makeMediaId(){return 'media_'+Date.now()+'_'+Math.random().toString(36).slice(2,10)}
  function getMediaDropzoneSetting(key){
    try{return String(window[key]||localStorage.getItem(key)||'').trim();}catch(e){return String(window[key]||'').trim();}
  }
  function cleanMediaDropzoneEndpoint(value){return String(value||'').trim().replace(/\/+$/,'');}
  function cleanMediaDropzoneId(value){return String(value||'').replace(/[^a-zA-Z0-9._-]/g,'').slice(0,96);}
  function initMediaDropzoneUploadAdapter(){
    const endpoint=cleanMediaDropzoneEndpoint(getMediaDropzoneSetting('KGG_MEDIA_DROPZONE_ENDPOINT')||getMediaDropzoneSetting('kggMediaDropzoneEndpoint'));
    window.KGGMediaDropzone={
      setEndpoint(url){try{localStorage.setItem('kggMediaDropzoneEndpoint',cleanMediaDropzoneEndpoint(url));}catch(e){}},
      setUploadToken(token){try{localStorage.setItem('kggMediaDropzoneUploadToken',String(token||'').trim());}catch(e){}},
      clear(){try{localStorage.removeItem('kggMediaDropzoneEndpoint');localStorage.removeItem('kggMediaDropzoneUploadToken');}catch(e){}}
    };
    if(!endpoint)return;
    if(window.KGGMediaUploadAdapter&&!window.KGGMediaUploadAdapter.isMock)return;
    window.KGGMediaUploadAdapter={
      name:'kgg-media-dropzone-kv-v1',
      isMock:false,
      async upload(blob,context){
        const manifest=context&&context.manifest||{};
        const id=cleanMediaDropzoneId(manifest.id)||makeMediaId();
        const ttlSeconds=Math.max(60,Math.min(MEDIA_UPLOAD_LONG_TTL_SECONDS,Number(context&&context.ttlSeconds)||MEDIA_UPLOAD_TTL_SECONDS));
        const token=getMediaDropzoneSetting('KGG_MEDIA_DROPZONE_UPLOAD_TOKEN')||getMediaDropzoneSetting('kggMediaDropzoneUploadToken');
        const headers={'Content-Type':'application/octet-stream','X-KGG-Media-Id':id,'X-KGG-Media-Mime':manifest.mime||'application/octet-stream','X-KGG-Media-Bytes':String(blob&&blob.size||0)};
        if(token)headers['X-KGG-Upload-Token']=token;
        const res=await fetch(endpoint+'/upload?ttl='+encodeURIComponent(ttlSeconds),{method:'POST',headers,body:blob,cache:'no-store'});
        if(!res.ok)throw new Error('Medien-Upload fehlgeschlagen ('+res.status+').');
        const data=await res.json();
        if(data&&data.id&&data.deleteToken)mediaDropzoneRuntimeTokens[data.id]=data.deleteToken;
        return data;
      },
      scheduleDelete(media,options){
        const delay=Math.max(1000,Number(options&&options.delayMs)||((Number(media&&media.ttlSeconds)||MEDIA_UPLOAD_TTL_SECONDS)*1000));
        setTimeout(()=>{this.delete(media);},delay);
      },
      async delete(media){
        const id=cleanMediaDropzoneId(media&&media.id);
        if(!id)return false;
        const deleteToken=(media&&media.deleteToken)||mediaDropzoneRuntimeTokens[id]||'';
        const deleteUrl=(media&&media.deleteUrl)||endpoint+'/media/'+encodeURIComponent(id);
        try{
          const res=await fetch(deleteUrl,{method:'DELETE',headers:{'Content-Type':'application/json'},body:JSON.stringify({deleteToken}),cache:'no-store'});
          return res.ok||res.status===404||res.status===410;
        }catch(err){console.warn('Media delete fehlgeschlagen:',err);return false;}
      }
    };
```
