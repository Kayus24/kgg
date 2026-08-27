# KGG-TICKET-034: Datenschutz- und Produktionssperre

## Verantwortlichkeit

Die Praxis ist voraussichtlich die verantwortliche Stelle. Max handelt als Arbeitnehmer im Auftrag der Praxis. Der Chef ist laut Max Datenschutzbeauftragter und hat den technischen Ansatz unter der Bedingung akzeptiert, dass abgefangene Transportdaten inhaltslos bleiben und die Datenschutzpflichten eingehalten werden.

Diese Datei ist technische Dokumentation und keine Rechtsberatung oder Zertifizierung.

## Technische Freigabevoraussetzungen

Alle Punkte muessen vor einem Produktionsbuild belegt sein:

- [ ] Ein eigener 256-Bit-Kopplungsschluessel pro geteiltem Plan.
- [ ] Kopplungsschluessel nur lokal per bewusstem QR, nie ueber Relay, Git, Logs oder Handoff.
- [ ] Plan-Kopplungen werden bei ausdruecklichem Entkoppeln, Planloeschung und App-Zuruecksetzen lokal vollstaendig entfernt. Ein normales Sitzungsende darf die weiter benoetigte Plan-Kopplung behalten.
- [ ] Frische ECDH- und AES-GCM-Sitzungsschluessel pro zweistuendiger Sitzung.
- [ ] Kein Name, Initial, Geburtsdatum, Adresse oder fachlicher Klartext beim Relay.
- [ ] Manipulation, falsches Geraet, Replay, Ablauf und Quota-Fehler schlagen geschlossen fehl.
- [ ] Sofortiges Sitzungsende und serverseitiges `deleteAll()` funktionieren.
- [ ] QR-/Offline-Fallback bleibt ohne Cloud nutzbar.
- [ ] Android-Keystore- und Web-Crypto-Speicherung sind getestet.
- [ ] Automatischer Klartext-/Secret-Scan ist gruen.
- [ ] Der echte Tab-S9-Test nutzt nur synthetische Daten.
- [ ] Der Produktionsendpunkt ist nach DPA- und Gesamtfreigabe fest vorgegeben; ein frei eingebbarer Produktionsendpunkt ist nicht erlaubt.

## Organisatorische Freigabevoraussetzungen

Die Praxis bewahrt die eigentliche Freigabe ausserhalb von Git auf. Sie dokumentiert mindestens:

- Verantwortliche Praxis und freigebende Person.
- Zweck und Rechtsgrundlage der Verarbeitung.
- Kategorien der Daten und betroffenen Personen.
- Cloudflare-Vertrag/DPA und Unterauftragnehmerpruefung.
- Speicherort, Metadatenrisiko und Zwei-Stunden-Loeschfrist.
- Ergebnis der Schwellenpruefung fuer eine Datenschutz-Folgenabschaetzung.
- Information der Patient:innen vor der freiwilligen Sitzung.
- Verfahren fuer Auskunft, Berichtigung, Sitzungsabbruch und lokale Aufbewahrung.
- Vorgehen bei einem Sicherheitsvorfall.

Die Patient:innenbestaetigung startet die konkrete Sitzung, ersetzt aber nicht automatisch die Rechtsgrundlage und macht Gesundheitsdaten nicht anonym.

## Freigabedatei

`production` verlangt eine lokale, nicht versionierte Datei `kgg-live-sync-privacy-approval.local.json`. Das Release-Gate akzeptiert sie nur mit diesen Wahrheitswerten:

```json
{
  "schemaVersion": 1,
  "controllerApproved": true,
  "legalBasisDocumented": true,
  "processorDpaReviewed": true,
  "dpiaDecisionDocumented": true,
  "patientNoticeApproved": true,
  "incidentProcessDocumented": true,
  "approvedAt": "YYYY-MM-DD",
  "approvalReference": "interne Referenz ohne Patientendaten"
}
```

Die echte Datei, Unterschrift, Namen und interne Unterlagen gehoeren nicht in dieses Repository.

## Harte Stop-Regel

Bei einem fehlenden Punkt bleibt `KGG_LIVE_SYNC_MODE=off`. Es gibt keinen manuellen Bypass, keinen Klartext-Fallback und keine automatische kostenpflichtige Alternative.

## Preview-/Debug-Grenze dieser Integration

Dieser Branch ist ausschließlich ein synthetischer Preview-/Debug-Kandidat. Der
Client akzeptiert im Testmodus nur lokale private HTTP-Relays (`localhost`,
Loopback oder private RFC-1918-Adressen); öffentliche HTTPS-Ziele,
`workers.dev`-Ziele und frei eintragbare Produktionsziele werden technisch
abgelehnt. Der Standard bleibt `off`, und es gibt keinen Produktionsendpunkt,
keine Cloudflare-Bereitstellung und keine lokale Freigabedatei im Repository.

Öffentliche KGGH2-/KGGH3-Patienten-QRs enthalten in diesem Preview-Stand keine
Patient:innen-, Geburts-, Therapeut:innen- oder Notizfelder. Der sichtbare
Plan-Titel ist generisch, und die öffentliche Plan-ID ist nur ein lokaler
Fingerprint. Die synthetischen Relay-Fixtures enthalten absichtliche
Canary-Werte; die Tests prüfen, dass sie weder in QR-Exports noch in Relay-
Speicher oder Logs erscheinen. Der HTML-Build verbietet außerdem extern
geladene Runtime-Skripte; Live-Sync-Code wird lokal aus dem Build geladen.

## Bekannte Lücken — ausdrücklich nicht produktionsreif

- Es gibt keinen echten Android-/Tab-S9-Instrumentationstest und keinen
  bereitgestellten Relay-Testdienst in dieser Arbeitsstrecke.
- Löschen, Ablauf und `deleteAll()` sind nur in den lokalen synthetischen
  Worker-/Memory-Relays nachgewiesen. Ein unabhängiger Backup-/Restore-Test
  für alle Geräte- und Browser-Speicher fehlt.
- Die lokale Ciphertext-Queue und das lokale Trainingsarchiv werden bei
  Fehlern best-effort bereinigt; eine forensische Wiederherstellungsprüfung
  oder zentrale Backup-Löschung ist nicht belegt.
- Die externe Datenschutzfreigabe, DPA-/DPIA-Prüfung, Patient:inneninformation
  und ein festgelegter Produktionsendpunkt fehlen weiterhin.

Daher darf dieser Stand nicht als produktionsreif, als echte
Patient:innenfreigabe oder als Nachweis einer Cloud-/Gerätefreigabe bezeichnet
werden.
