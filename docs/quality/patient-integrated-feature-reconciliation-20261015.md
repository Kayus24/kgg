# Patient feature reconciliation ? integrated candidate

All 111 original IDs are retained. A mapping is not a PASS. See matching acceptance.json execution evidence.

| ID | Feature | Proof groups | Existing regression | Disposition |
|---|---|---|---|---|
| PAT-IMPORT-001 | KGGH2/QR-/URL-Plan laden | scan | - | AUTOMATED_SCOPE_PENDING_EXECUTION |
| PAT-IMPORT-002 | Defekter/inkompatibler Plan fail-safe | scan | - | AUTOMATED_SCOPE_PENDING_EXECUTION |
| PAT-STATE-001 | Eine führende Trainings-/Persistence-Wahrheit | - | - | UNRESOLVED_COMPARISON_OR_DEVICE_REVIEW |
| PAT-STATE-002 | Werte pro Tag/Satz/Seite erhalten | parity | - | AUTOMATED_SCOPE_PENDING_EXECUTION |
| PAT-STATE-003 | Planwechsel/Import setzt Runtime-Defaults sauber | offline | - | AUTOMATED_SCOPE_PENDING_EXECUTION |
| PAT-UI-001 | ALT/NEU-Ansichtsschalter | adaptive | - | AUTOMATED_SCOPE_PENDING_EXECUTION |
| PAT-UI-002 | Adaptive/Compact Set View | adaptive | - | AUTOMATED_SCOPE_PENDING_EXECUTION |
| PAT-UI-003 | 3 Sätze gleichzeitig auf Phone | adaptive | - | AUTOMATED_SCOPE_PENDING_EXECUTION |
| PAT-UI-004 | 1/2/3/4+ Sätze | adaptive | - | AUTOMATED_SCOPE_PENDING_EXECUTION |
| PAT-UI-005 | Beidseitige Satzkapseln | adaptive | - | AUTOMATED_SCOPE_PENDING_EXECUTION |
| PAT-UI-006 | LR-Satzkapseln Re oben / Li unten | - | - | UNRESOLVED_COMPARISON_OR_DEVICE_REVIEW |
| PAT-UI-007 | Karte bleibt inhaltsgetrieben kompakt | - | - | UNRESOLVED_COMPARISON_OR_DEVICE_REVIEW |
| PAT-UI-008 | Kein horizontaler Body-Overflow | adaptive | - | AUTOMATED_SCOPE_PENDING_EXECUTION |
| PAT-UI-009 | Large-UI ohne redundante dritte Zoom-Box im Compact-Modus | adaptive | - | AUTOMATED_SCOPE_PENDING_EXECUTION |
| PAT-UI-010 | Large-UI vergrößert reale Wertefelder | adaptive | - | AUTOMATED_SCOPE_PENDING_EXECUTION |
| PAT-UNIT-001 | Dynamische Last-/Metrik-Units | unit | - | AUTOMATED_SCOPE_PENDING_EXECUTION |
| PAT-UNIT-002 | Kein Phantomfeld bei inaktiver Unit | unit | - | AUTOMATED_SCOPE_PENDING_EXECUTION |
| PAT-UNIT-003 | Single-Field nutzt volle Fläche | adaptive | - | AUTOMATED_SCOPE_PENDING_EXECUTION |
| PAT-UNIT-004 | Vorschlagswert und Unit gemeinsam grau / Istwert gemeinsam schwarz | - | - | UNRESOLVED_COMPARISON_OR_DEVICE_REVIEW |
| PAT-UNIT-005 | Aktiver Feldrahmen nutzt gleiche Akzentfarbe | - | - | UNRESOLVED_COMPARISON_OR_DEVICE_REVIEW |
| PAT-UNIT-006 | Lange/Custom Units ohne Zahlenüberdeckung | - | - | UNRESOLVED_COMPARISON_OR_DEVICE_REVIEW |
| PAT-UNIT-007 | Unit-Wechsel lässt Altwerte fachlich inaktiv | settings | - | AUTOMATED_SCOPE_PENDING_EXECUTION |
| PAT-NUM-001 | Bestehendes NumPad bleibt einzige Engine | - | - | UNRESOLVED_COMPARISON_OR_DEVICE_REVIEW |
| PAT-NUM-002 | Pair-Feldwechsel bleibt offen/blinkfrei | parity | - | AUTOMATED_SCOPE_PENDING_EXECUTION |
| PAT-NUM-003 | OK committet / Abbrechen nicht | parity | - | AUTOMATED_SCOPE_PENDING_EXECUTION |
| PAT-NUM-004 | Dirty Manual Buffer bleibt bei Transfer erhalten | parity | - | AUTOMATED_SCOPE_PENDING_EXECUTION |
| PAT-NUM-005 | Unberührtes leeres Feld wird nicht als 0 gespeichert | parity | - | AUTOMATED_SCOPE_PENDING_EXECUTION |
| PAT-PREV-001 | Vorwert-Hinweise / Shimmer | - | - | UNRESOLVED_COMPARISON_OR_DEVICE_REVIEW |
| PAT-PREV-002 | Einzelnen Vorwert übernehmen | parity | - | AUTOMATED_SCOPE_PENDING_EXECUTION |
| PAT-PREV-003 | Beide Vorwerte über Mitte 'Übernehmen' | parity | - | AUTOMATED_SCOPE_PENDING_EXECUTION |
| PAT-PREV-004 | Nach Einzelübernahme nur fehlender Wert mittig | parity | - | AUTOMATED_SCOPE_PENDING_EXECUTION |
| PAT-PREV-005 | Auto-Close nur bei fachlicher Vollständigkeit | - | kgg_patient_compact_transfer_playwright.js | EXISTING_REGRESSION_NOT_DIRECT_COMPARISON |
| PAT-PREV-006 | Single-Field Auto-Close | - | kgg_patient_compact_transfer_playwright.js | EXISTING_REGRESSION_NOT_DIRECT_COMPARISON |
| PAT-PREV-007 | LR-Side-Isolation | parity | - | AUTOMATED_SCOPE_PENDING_EXECUTION |
| PAT-PREV-008 | Vorwert folgt passendem Satz/Seite aus vorherigem Training | - | kgg_patient_last_value_shimmer_playwright.js | EXISTING_REGRESSION_NOT_DIRECT_COMPARISON |
| PAT-PAIN-001 | Schmerz 0–10 funktional unverändert | - | - | UNRESOLVED_COMPARISON_OR_DEVICE_REVIEW |
| PAT-PAIN-002 | Compact Schmerz-Pill/Trigger | - | - | UNRESOLVED_COMPARISON_OR_DEVICE_REVIEW |
| PAT-PAIN-003 | Pain-Modal verändert Layout nicht dauerhaft | - | - | UNRESOLVED_COMPARISON_OR_DEVICE_REVIEW |
| PAT-PAIN-004 | Wahlweise Schmerz pro Satz über das Übungs-Untermenü | pain | - | AUTOMATED_SCOPE_PENDING_EXECUTION |
| PAT-PROG-001 | Card Progress zählt nur aktive Felder | unit | - | AUTOMATED_SCOPE_PENDING_EXECUTION |
| PAT-START-001 | Startwerte Tag 1 nur für aktive Units | unit | - | AUTOMATED_SCOPE_PENDING_EXECUTION |
| PAT-START-002 | Startwert-Scan / AutoFill respektiert Feldsemantik | unit | - | AUTOMATED_SCOPE_PENDING_EXECUTION |
| PAT-SUM-001 | Set Summary zeigt reale Felder/Units | unit | - | AUTOMATED_SCOPE_PENDING_EXECUTION |
| PAT-HIST-001 | Day History zeigt reale Felder/Units | unit, days | - | AUTOMATED_SCOPE_PENDING_EXECUTION |
| PAT-COMP-001 | Completion/Finish ignoriert inaktive Felder | unit | - | AUTOMATED_SCOPE_PENDING_EXECUTION |
| PAT-FIN-001 | Finish-/Abschlussflow | days | - | AUTOMATED_SCOPE_PENDING_EXECUTION |
| PAT-MEDIA-001 | Quellenbewusster Medienkatalog | - | kgg_patient_media_sources_playwright.js | EXISTING_REGRESSION_NOT_DIRECT_COMPARISON |
| PAT-MEDIA-002 | RepDB-Mappings | - | kgg_patient_media_sources_playwright.js | EXISTING_REGRESSION_NOT_DIRECT_COMPARISON |
| PAT-MEDIA-003 | Workout Guide Mappings | - | kgg_patient_media_sources_playwright.js | EXISTING_REGRESSION_NOT_DIRECT_COMPARISON |
| PAT-MEDIA-004 | Everkinetic-Fallback | - | kgg_patient_media_sources_playwright.js | EXISTING_REGRESSION_NOT_DIRECT_COMPARISON |
| PAT-MEDIA-005 | Start/Peak bzw. Single-Main korrekt | - | kgg_patient_media_sources_playwright.js | EXISTING_REGRESSION_NOT_DIRECT_COMPARISON |
| PAT-MEDIA-006 | Bild-Decoding / Nicht-Leerbild / Fallback | media | - | AUTOMATED_SCOPE_PENDING_EXECUTION |
| PAT-MEDIA-007 | Attribution und Source-Metadaten | - | kgg_patient_media_sources_playwright.js | EXISTING_REGRESSION_NOT_DIRECT_COMPARISON |
| PAT-MEDIA-008 | Bilder verändern Satzlayout nicht | firstload | - | AUTOMATED_SCOPE_PENDING_EXECUTION |
| PAT-PWA-001 | PWA Contract | offline | - | AUTOMATED_SCOPE_PENDING_EXECUTION |
| PAT-PWA-002 | Direkter First Load ohne Reload | firstload | - | AUTOMATED_SCOPE_PENDING_EXECUTION |
| PAT-PWA-003 | Update Recovery | - | kgg_patient_english_compatibility_playwright.js, kgg_update_recovery_smoke.py | EXISTING_REGRESSION_NOT_DIRECT_COMPARISON |
| PAT-STOR-001 | Plan-/Trainingspersistenz über Reload | unit, days, offline | - | AUTOMATED_SCOPE_PENDING_EXECUTION |
| PAT-STOR-002 | Preview und Live Storage isoliert | - | kgg_patient_preview_storage_isolation_smoke.js | EXISTING_REGRESSION_NOT_DIRECT_COMPARISON |
| PAT-PWA-004 | Preview Cache/Noindex-Schutz | - | kgg_patient_gpt_write_gate.py | EXISTING_REGRESSION_NOT_DIRECT_COMPARISON |
| PAT-LANG-001 | DE/EN Unit-Normalisierung | - | kgg_patient_english_playwright.js | EXISTING_REGRESSION_NOT_DIRECT_COMPARISON |
| PAT-INT-001 | Drag/Tap/Keyboard bleiben bedienbar | - | kgg_test_battery.py | EXISTING_REGRESSION_NOT_DIRECT_COMPARISON |
| PAT-LEG-001 | Legacy/Normal/Large UI geschützt | adaptive | - | AUTOMATED_SCOPE_PENDING_EXECUTION |
| PAT-IOS-001 | iOS-Large-Pad-Force-Pfad kompatibel | - | kgg_ios_start_smoke.js, kgg_patient_set_view_adaptive_smoke.js | EXISTING_REGRESSION_NOT_DIRECT_COMPARISON |
| PAT-THUMB-001 | Lokale Thumbnail-Geometrie | firstload | - | AUTOMATED_SCOPE_PENDING_EXECUTION |
| PAT-DEL-001 | Rotes X / Plan- oder Übungslöschung | manage | - | AUTOMATED_SCOPE_PENDING_EXECUTION |
| PAT-SEC-001 | Unit-Text darf kein HTML/XSS ausführen | - | - | ACTIVE_PROBE_TOOL_BLOCKED |
| PAT-SEC-002 | Keine Secrets im Client/Preview | - | kgg_secret_scan.py | EXISTING_REGRESSION_NOT_DIRECT_COMPARISON |
| PAT-TEST-001 | Patient UI Stability Regression | - | kgg_test_battery.py | EXISTING_REGRESSION_NOT_DIRECT_COMPARISON |
| PAT-TEST-002 | Critical Gate / Hook Guard / diff check | - | kgg_hook_guard.py, kgg_test_battery.py | EXISTING_REGRESSION_NOT_DIRECT_COMPARISON |
| PAT-TEST-003 | Generated Patient-GPT-Ressourcen nur bei Sourceänderung regenerieren | - | kgg_patient_gpt_resources.py | EXISTING_REGRESSION_NOT_DIRECT_COMPARISON |
| PAT-TEST-004 | Browser-Evidence ohne force-click | - | kgg_patient_ui_parity_capture.js | EXISTING_REGRESSION_NOT_DIRECT_COMPARISON |
| PAT-DAY-001 | Trainingstag T1…Tn wechseln | days | - | AUTOMATED_SCOPE_PENDING_EXECUTION |
| PAT-DAY-002 | Abgeschlossene Tage markieren und nach finalem QR fortschalten | days | - | AUTOMATED_SCOPE_PENDING_EXECUTION |
| PAT-DAY-003 | Offenes Training nach Reload wiederherstellen | days | - | AUTOMATED_SCOPE_PENDING_EXECUTION |
| PAT-DAY-004 | Kontinuierlicher Plan vs. feste Trainingstage | days | - | AUTOMATED_SCOPE_PENDING_EXECUTION |
| PAT-DAY-005 | „Weitere Tage hinzufügen“ | days | - | AUTOMATED_SCOPE_PENDING_EXECUTION |
| PAT-COLLAPSE-001 | Übungskarten ein-/ausklappen | firstload | - | AUTOMATED_SCOPE_PENDING_EXECUTION |
| PAT-MULTI-001 | Plan-Aktionsmenü | manage | - | AUTOMATED_SCOPE_PENDING_EXECUTION |
| PAT-MULTI-002 | Zusätzlichen zweiten/weiteren Plan hinzufügen | link | - | AUTOMATED_SCOPE_PENDING_EXECUTION |
| PAT-MULTI-003 | Zwischen gespeicherten Plänen wechseln | days | - | AUTOMATED_SCOPE_PENDING_EXECUTION |
| PAT-MULTI-004 | Planverwaltung / aktive Plananzeige | manage | - | AUTOMATED_SCOPE_PENDING_EXECUTION |
| PAT-MULTI-005 | Plan umbenennen | manage | - | AUTOMATED_SCOPE_PENDING_EXECUTION |
| PAT-MULTI-006 | Plan löschen | manage | - | AUTOMATED_SCOPE_PENDING_EXECUTION |
| PAT-LINK-001 | Neuer Plan-Link bei bestehendem Plan: hinzufügen / ersetzen / abbrechen | link | - | AUTOMATED_SCOPE_PENDING_EXECUTION |
| PAT-SCAN-001 | Aktuellen Plan per QR aktualisieren | scan-fallback | - | AUTOMATED_SCOPE_PENDING_EXECUTION |
| PAT-SCAN-002 | Plan bewusst ersetzen | link | - | AUTOMATED_SCOPE_PENDING_EXECUTION |
| PAT-SCAN-003 | Scanner-Fallbacks: Live-Kamera, Foto/Datei, Plan-Link, Retry, Schließen | scan-fallback | - | AUTOMATED_SCOPE_PENDING_EXECUTION |
| PAT-SCAN-004 | Start ohne Plan: Plan erneut öffnen / Rescue | scan-fallback | - | AUTOMATED_SCOPE_PENDING_EXECUTION |
| PAT-DB-001 | Patientenseitige Übungsdatenbank öffnen/suchen | db | - | AUTOMATED_SCOPE_PENDING_EXECUTION |
| PAT-DB-002 | Übung aus lokaler Datenbank in Plan holen | db | - | AUTOMATED_SCOPE_PENDING_EXECUTION |
| PAT-SETTINGS-001 | „Übung anpassen“ / patientenseitige Übungseinstellungen | settings | - | AUTOMATED_SCOPE_PENDING_EXECUTION |
| PAT-SETTINGS-002 | Seitenwerte kontrolliert kopieren | settings | - | AUTOMATED_SCOPE_PENDING_EXECUTION |
| PAT-EXTRA-001 | Zusatzinfo/Notiz an Übung anzeigen | - | kgg_patient_english_compatibility_playwright.js | EXISTING_REGRESSION_NOT_DIRECT_COMPARISON |
| PAT-MEDIA-009 | Übungsbild vergrößern / Lightbox | firstload | - | AUTOMATED_SCOPE_PENDING_EXECUTION |
| PAT-MEDIA-010 | Medienquelle/Lizenz sichtbar zuordenbar | - | kgg_patient_media_sources_playwright.js | EXISTING_REGRESSION_NOT_DIRECT_COMPARISON |
| PAT-MEDIA-011 | Medien Retry/Cache/Prefetch | media | - | AUTOMATED_SCOPE_PENDING_EXECUTION |
| PAT-PROGRESSION-001 | Progressionsvarianten/Stufen auswählen | progression | - | AUTOMATED_SCOPE_PENDING_EXECUTION |
| PAT-PROGRESSION-002 | Progressionsauswahl und erfolgreiche Nutzung bleiben konsistent | progression | - | AUTOMATED_SCOPE_PENDING_EXECUTION |
| PAT-QR-001 | Aktuelle Werte als Zwischenstands-QR | days | - | AUTOMATED_SCOPE_PENDING_EXECUTION |
| PAT-QR-002 | Training beenden & finalen QR anzeigen | days | - | AUTOMATED_SCOPE_PENDING_EXECUTION |
| PAT-QR-003 | QR-Payload kopieren mit Fallback | - | - | UNRESOLVED_COMPARISON_OR_DEVICE_REVIEW |
| PAT-QR-004 | QR-Vollbild | days | - | AUTOMATED_SCOPE_PENDING_EXECUTION |
| PAT-INSTALL-001 | Startbildschirm/PWA-Hilfe | - | kgg_patient_install_capability_playwright.js | EXISTING_REGRESSION_NOT_DIRECT_COMPARISON |
| PAT-INSTALL-002 | Planlink/Standalone-Recovery | - | kgg_patient_install_capability_playwright.js, kgg_ios_start_smoke.js | EXISTING_REGRESSION_NOT_DIRECT_COMPARISON |
| PAT-UPD-001 | Sichtbare App-Version | offline | - | AUTOMATED_SCOPE_PENDING_EXECUTION |
| PAT-UPD-002 | Update-Banner und sichere Aktivierung | - | kgg_patient_english_compatibility_playwright.js | EXISTING_REGRESSION_NOT_DIRECT_COMPARISON |
| PAT-UPD-003 | Update-Recovery-Seite | - | kgg_update_recovery_smoke.py | EXISTING_REGRESSION_NOT_DIRECT_COMPARISON |
| PAT-LANG-002 | Vollständige Laufzeit-i18n für Status-/Fehlermeldungen | - | kgg_patient_english_playwright.js, kgg_patient_english_compatibility_playwright.js | EXISTING_REGRESSION_NOT_DIRECT_COMPARISON |
| PAT-AUDIT-001 | Browseraudit muss auf gepinntem Preview-Stand laufen | - | kgg_patient_integrated_acceptance.py | EXISTING_REGRESSION_NOT_DIRECT_COMPARISON |
| PAT-AUDIT-002 | TinyFish-/Browser-Agent-Befund gegen reproduzierbaren Browser-/Testlauf gegenprüfen | - | kgg_patient_integrated_acceptance.py | EXISTING_REGRESSION_NOT_DIRECT_COMPARISON |
