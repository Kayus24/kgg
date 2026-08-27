# KGG-TICKET-034: Live-Sync-Protokoll v1

Status: verbindlicher Architekturvertrag fuer den lokalen, ausschliesslich synthetischen Prototyp.

Basis-Commit: `04a5d3e59225985e4e536f25c1b7aea8b04690f1`
Preview-Port: `codex/preview-live-sync-qr-integration-20260825`

## Ziel und harte Grenzen

- Eine Therapeut:innen-App und genau eine bereits gekoppelte Patienten-App tauschen waehrend einer hoechstens zweistuendigen Sitzung Planstaende und Trainingsergebnisse aus.
- Der Relay-Server sieht zufaellige Kennungen, Ablaufzeiten, Groessen, kurzlebige Rollen-Tokens bei der Anmeldung, authentifizierte oeffentliche Sitzungsschluessel und kryptografisch geschuetzte Datenframes.
- Der Relay speichert von Rollen-Tokens nur SHA-256-Hashes. Oeffentliche Sitzungsschluessel und ihre Signaturen werden nur fluechtig an die verbundene Gegenseite weitergereicht und nicht gespeichert.
- Namen, Initialen, Geburtsdaten, Adressen, Diagnosen, Klartext-Planwerte, Klartext-Trainingsergebnisse, Kopplungsschluessel und private Sitzungsschluessel duerfen den Relay nie erreichen.
- `KGGDataStore.currentPlan` bleibt die einzige zentrale Plan-State-Quelle der Therapeut:innen-App.
- Bei fehlender oder fehlerhafter Kryptografie gibt es keinen unsicheren Fallback. Live-Sync bleibt aus; QR und Offline-Nutzung bleiben verfuegbar.
- Der Prototyp darf nur in `test` mit synthetischen Daten laufen. `production` bleibt bis zur externen Freigabedatei hart gesperrt.

## Planindividuelle Kopplung

Jeder geteilte Plan erhaelt eine eigene, nicht aus Patientendaten abgeleitete Kopplung:

- `pairingId`: 128 zufaellige Bits, Base64URL ohne Padding.
- `pairingSecret`: 256 zufaellige Bits, Base64URL ohne Padding.
- `keyVersion`: `1`.
- `createdAt`: ISO-8601-Zeitpunkt.

Der Schluessel wird nicht in KGGH2/KGGH3 eingebettet. Das bestehende Plan-/QR-Format bleibt unveraendert. Fuer Live-Sync gibt es einen getrennten, bewusst angezeigten lokalen Kopplungs-QR:

```text
KGGLIVEPAIR1:<base64url(utf8(canonical-json))>
```

Der JSON-Inhalt besteht nur aus `v`, `pairingId`, `pairingSecret`, `keyVersion` und `createdAt`. Er enthaelt keine Plan-ID aus dem fachlichen Bestand und keine Patient:innenbezeichnung. Der QR wird nicht gespeichert, geloggt, in Screenshots aufgenommen oder online uebertragen. Eine neue Kopplung ersetzt den alten Schluessel fuer diesen lokalen Plan.

Auf Android wird `pairingSecret` mit einem eigenen Android-Keystore-Schluessel geschuetzt. Release-/GitHub-Schluessel und Live-Sync-Schluessel bleiben getrennt. In der Patienten-PWA wird der Schluessel als nicht exportierbares Web-Crypto-Material in IndexedDB importiert. Fehlt sichere Speicherung, wird Live-Sync nicht angeboten.

## Sitzung und Schluesselableitung

Der planindividuelle Schluessel verschluesselt keine Nutzdaten direkt.

1. Die Therapeut:innen-App reserviert eine Sitzung beim Relay.
2. Der Relay erzeugt `sessionId` (128 zufaellige Bits), `sessionSalt` (256 zufaellige Bits), einen achtstelligen Dezimalcode und `expiresAt = serverNow + 2h`.
3. Die Therapeut:innen-App berechnet den Join-Beweis `HMAC-SHA-256(pairingSecret, "KGG-LIVE-JOIN-V1" || sessionId || sessionSalt)`.
4. Der Relay speichert nur diesen Beweis und Token-Hashes.
5. Die Patienten-App erhaelt Code, `sessionId` und `sessionSalt`, berechnet denselben Beweis und wird nur bei konstantzeitlichem Gleichstand zugelassen.
6. Beide Endpunkte erzeugen fuer diese Sitzung ein fluechtiges ECDH-P-256-Schluesselpaar.
7. Jeder oeffentliche ECDH-Schluessel wird mit `HMAC(pairingSecret, "KGG-LIVE-ECDH-OFFER-V1" || pairingId || role || sessionId || publicKey)` authentifiziert. Der Relay leitet diese Anmeldung nur an eine bereits authentifizierte Gegenseite derselben Sitzung weiter und speichert sie nicht. Die Gegenseite verwirft sie bei falscher Signatur.
8. Beide Seiten leiten den gemeinsamen AES-256-GCM-Sitzungsschluessel per HKDF-SHA-256 ab. Der feste Kontext ist exakt `KGG-LIVE-SESSION-V1 || pairingId || sessionId || expiresAtEpochMillis || therapist || patient`; `expiresAtEpochMillis` stammt aus dem unveraenderten kanonischen Relay-Wert.
9. Fluechtige private ECDH-Schluessel werden nach Ende oder Ablauf verworfen.

Damit sind passiv abgefangene Netzwerkdaten ohne Endgeraeteschluessel nicht lesbar. Eine spaetere Offenlegung des planindividuellen Kopplungsschluessels allein soll alte Sitzungsinhalte nicht entschluesseln koennen.

## Relay-API

Lokaler und spaeterer Cloudflare-Worker verwenden dieselbe API:

- `GET /health`: nur Version, Modus und Serverzeit.
- `POST /v1/sessions/reserve`: reserviert eine noch nicht aktive Sitzung; Client liefert nur den Hash des zufaelligen Therapeut:innen-Tokens.
- `POST /v1/sessions/{code}/arm`: setzt den Join-Beweis; Autorisierung ueber den Therapeut:innen-Token im `Authorization`-Header.
- `GET /v1/sessions/{code}/challenge`: liefert `sessionId`, `sessionSalt`, `expiresAt` und Protokollversion.
- `POST /v1/sessions/{code}/join`: vergleicht Join-Beweis konstantzeitlich und registriert den Hash eines zufaelligen Patient:innen-Tokens.
- `GET /v1/sessions/{code}/socket`: WebSocket-Upgrade. Das erste Frame muss innerhalb von fuenf Sekunden mit dem Rollen-Token authentifizieren. Tokens stehen nie in URLs.
- `DELETE /v1/sessions/{code}`: verlangt den sitzungsgebundenen Therapeut:innen-Token als `Authorization: Bearer <token>`, schliesst WebSockets, loescht Alarm und ruft `deleteAll()` auf.

Der Code dient nur zum Routing. Er ist ohne Kopplungsschluessel kein Zugangsbeweis.

## Relay-Grenzen

- Eine Therapeut:innen- und eine Patient:innen-Rolle pro Sitzung; Wiederverbindung ersetzt nur die alte Verbindung derselben Rolle.
- Hoechstens 400 akzeptierte Datenframes pro Sitzung.
- Hoechstens 64 KiB pro Frame und 5 MiB verschluesselter Rueckstand.
- Hoechstens fuenf falsche Join-Versuche; danach ist die Sitzung gesperrt.
- Keine fachlichen Inhalte oder Request-Bodies loggen.
- Rollen-Tokens nur im Arbeitsspeicher pruefen und nur gehasht speichern. Authentifizierte oeffentliche Sitzungsschluessel nur fluechtig weiterleiten und nie als Rueckstand speichern.
- Abgelaufene Sitzungen antworten immer geschlossen und loeschen ihren Speicher.
- Cloudflare Durable Object mit `jurisdiction("eu")` und WebSocket Hibernation; ueber Nacht nur lokale Emulation, keine Bereitstellung.

## Verschluesseltes Frame

Der Relay darf nur dieses aeussere Format sehen:

```json
{
  "v": 1,
  "messageId": "128-bit-random-base64url",
  "sender": "therapist|patient",
  "sequence": 1,
  "nonce": "96-bit-random-base64url",
  "ciphertext": "base64url",
  "createdAt": "ISO-8601"
}
```

AES-GCM Additional Authenticated Data bindet mindestens `v`, `sessionId`, `messageId`, `sender` und `sequence`. Pro Sitzungsschluessel darf kein Nonce wiederverwendet werden. Empfangene Kombinationen aus Absender, Sequenz, Nachrichten-ID und Nonce werden auf Replay geprueft.

Der verschluesselte Inhalt hat einen der Typen:

- `plan_snapshot`: vollstaendiger fachlicher Planstand mit `planRevision` und stabilen Uebungs-IDs.
- `training_events`: unveraenderliche Ereignisse mit eigener Ereignis-ID und `basePlanRevision`.
- `receipt`: hoechster bestaetigter Relay-Cursor und angewandte IDs.
- `close`: absichtliches Sitzungsende.

## Zusammenfuehrungsregeln

- Therapeut:in besitzt Uebung, Reihenfolge, Anleitung, Zielsaetze, Zielwiederholungen, Seite und Zielwerte.
- Patient:in besitzt tatsaechlich ausgefuehrte Werte, Schmerz, Abschlussstatus und Erfassungszeitpunkt.
- Plan-Snapshots ersetzen nur therapeutisch besessene Felder.
- Trainingsergebnisse werden ueber stabile Uebungs- und Ereignis-IDs idempotent angefuegt.
- Entfernte Uebungen werden im aktiven Plan archiviert; vorhandene Trainingsergebnisse bleiben erhalten.
- Ein ungueltiges, unvollstaendiges oder nicht authentifiziertes Frame veraendert keinen lokalen State.

## Betriebsmodi

- `off`: kein Live-Sync-Codepfad aktiv; Standard fuer alle normalen Builds.
- `test`: nur synthetische Daten, sichtbarer Testhinweis, lokaler oder ausdruecklich erlaubter Test-Endpunkt.
- `production`: nur mit nicht eingecheckter Freigabedatei und bestandenem Release-Gate.

Der Quellstand enthaelt niemals einen aktiven Produktionsendpunkt, Cloudflare-Token oder eine Freigabedatei.
Der Preview-Client akzeptiert im Testmodus ausschliesslich lokale private
HTTP-Relays; oeffentliche HTTPS- und Produktionsziele sind technisch gesperrt.
Oeffentliche KGGH2-/KGGH3-QR-Exports enthalten keine Patienten-, Geburts-,
Therapeuten- oder Notizfelder. Die synthetischen Exporttests verwenden
Canary-Werte und pruefen deren Abwesenheit im dekodierten QR und im Relay.

## Stop-Regeln

Der Live-Sync-Teil wird gestoppt und nicht fuer echte Daten freigegeben, wenn eine der folgenden Aussagen nicht nachgewiesen werden kann:

- Netzwerkaufzeichnung, Relay-Speicher und Anwendungslogs enthalten keinen lesbaren Plan- oder Trainingswert.
- Relay oder falsches Geraet koennen kein akzeptiertes Nutzdatenframe erzeugen.
- Nonce-Wiederverwendung und Replay werden ausgeschlossen.
- Fehler oder fehlende Web-Crypto-Unterstuetzung fuehren sicher zu `off`, niemals zu Klartext.
- Sitzungsspeicher wird bei Ende und Ablauf vollstaendig geloescht.
- Produktionsmodus kann ohne lokale Datenschutzfreigabe nicht gebaut werden.
