# KGG-TICKET-034: Datenschutz- und Produktionssperre

## Verantwortlichkeit

Die Praxis ist voraussichtlich die verantwortliche Stelle. Max handelt als Arbeitnehmer im Auftrag der Praxis. Der Chef ist laut Max Datenschutzbeauftragter und hat den technischen Ansatz unter der Bedingung akzeptiert, dass abgefangene Transportdaten inhaltslos bleiben und die Datenschutzpflichten eingehalten werden.

Diese Datei ist technische Dokumentation und keine Rechtsberatung oder Zertifizierung.

## Technische Freigabevoraussetzungen

Alle Punkte muessen vor einem Produktionsbuild belegt sein:

- [ ] Ein eigener 256-Bit-Kopplungsschluessel pro geteiltem Plan.
- [ ] Kopplungsschluessel nur lokal per bewusstem QR, nie ueber Relay, Git, Logs oder Handoff.
- [ ] Frische ECDH- und AES-GCM-Sitzungsschluessel pro zweistuendiger Sitzung.
- [ ] Kein Name, Initial, Geburtsdatum, Adresse oder fachlicher Klartext beim Relay.
- [ ] Manipulation, falsches Geraet, Replay, Ablauf und Quota-Fehler schlagen geschlossen fehl.
- [ ] Sofortiges Sitzungsende und serverseitiges `deleteAll()` funktionieren.
- [ ] QR-/Offline-Fallback bleibt ohne Cloud nutzbar.
- [ ] Android-Keystore- und Web-Crypto-Speicherung sind getestet.
- [ ] Automatischer Klartext-/Secret-Scan ist gruen.
- [ ] Der echte Tab-S9-Test nutzt nur synthetische Daten.

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

