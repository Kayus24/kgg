# Cockpit nach Patienten-QR wiederaufnehmen

Auftrag: Beim Patienten-QR-Scan einen anklickbaren Cockpit-Aktivierungslink
erzeugen. Das Cockpit zeigt Plan und letzte Werte, erlaubt Notizen und erhaelt
therapeutische Eingaben mit Vorrang gegenueber spaeteren Scans.

Basis: origin/main 58edea8, Therapeut:innenquelle v128, Admin r0436. Nur die
Therapeut:innenquelle wird geaendert. Patienten-QR-Bytes und Kamera/Decoder
bleiben unveraendert. KGGDataStore.currentPlan bleibt die normale Planquelle.

Umsetzung: vorhandenen portablen Cockpit-Snapshot-Link erweitern, optional mit
Notizen und Herkunftsmarkern fuer einzelne manuell bearbeitete Felder. Alte Links
bleiben lesbar. Ein lokaler, nach exakter Plan-ID getrennter Wiederaufnahmestand
ergaenzt erneute Scans und verhindert das Zuruecksetzen durch einen alten Link.
Kein Server und keine zweite normale Planverwaltung. Ein reiner RAM-Ansatz
erfuellt die Wiederaufnahme nicht; ein neues Cloud-Backend ist nicht noetig.

Der gemeinsame erfolgreiche Scan-Anschluss reicht nur validierte Patientenplaene
weiter. Vollplan-QR und Rueckgabe-QR werden getrennt normalisiert. Ohne stabile
Plan-ID keine automatische Zusammenfuehrung. Namen sind keine Identitaet.
Gleiche Plan-ID verwendet einen vorhandenen Slot erneut; andere IDs bleiben
getrennt. Erst vollstaendig validieren, dann Zustand und Ausgabe aktualisieren.

Die Zusammenfuehrung aktualisiert unberuehrte QR-Felder. Explizit manuelle
Feldwerte (einschliesslich 0 und bewusst geleerter Werte), Notizen und manuelle
Uebungsanpassungen haben Vorrang. Notizen werden als Text behandelt. Bei einem
neuen Geraet gilt der gespeicherte Link-Snapshot; lokale spaetere Eintraege werden
nicht ohne neuen Link geraeteuebergreifend synchronisiert.

Max hat am 2026-10-26 ausdruecklich bestaetigt, dass gespeicherte Eintraege auch
auf anderen Geraeten funktionieren sollen. Der aktuelle Stand wird deshalb im
neuen Abschlusslink transportiert; Werte, Notizen und manuelle Prioritaet sind
im Test mit getrennten Browserkontexten nachgewiesen.

Nachweis: produktiver Scan-Einstieg mit synthetischen Vollplan-/Rueckgabe-QRs,
sichtbarer Link, Cockpit-Numpad und Notiz, Abschluss, Reload/alter Link, erneuter
Scan, zweiter Browserkontext, Plantrennung, volle Slots und ungueltige Daten.
Danach Critical, UI-Stability und bestehende Cockpit-Vertraege. Kein Push,
Merge, Release, APK oder Deploy ohne separate Freigabe.

## Veroeffentlichungsfreigabe

Max hat nach dem geprueften v129-Teststand am 2026-10-26 mit "ja freigabe go"
Push, PR, Merge und Veroeffentlichung freigegeben. Ziel ist der bestehende
Admin-Web-Kanal r0437; HTML SHA256 bleibt
`a3685d915366c8bf53afa21f6bc5087a1b027b42de739530325d65ba3b13cd88`.
Die regulaeren Commit- und GitHub-Gates bleiben verbindlich.
