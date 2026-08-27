# KGG Android Wrapper v2

Quellprojekt fuer die einmalig neu zu installierenden Admin- und Kolleg:innen-APKs. Danach werden HTML-Releases ueber die getrennten Kanaele in `therapist-app/android_update_manifest.json` geladen.

Der Admin-Flavor enthaelt zusaetzlich die native Release-Zentrale. GitHub-Tokens werden nur im Android Keystore gespeichert und niemals an die WebView weitergereicht. Der Kolleg:innen-Flavor kann keine Release-Aktionen aufrufen.

Ab v395 ist die GitHub-Verbindung nur noch der Komfortweg. Der stabile Handy-Standard ist:

1. Aktuelle HTML in der Admin-App speichern.
2. GitHub-Mobile-Inbox oeffnen.
3. HTML auf den Branch `mobile-inbox` hochladen.
4. GitHub Actions erzeugt den geprueften Admin-Beta-Release.

Buildvarianten:

- `assembleAdminDebug`
- `assembleKollegenDebug`

## Native KGGLiveKey bridge

`KGGLiveKey` ist eine eigene, von der Release-/GitHub-Bridge getrennte
WebView-Schnittstelle. Sie wird nur nach dem Laden der exakt gebundenen
lokalen KGG-Datei eingebunden und bei Navigation, Fehler, Pause oder Ende
geschlossen.

- Pairings werden pro streng begrenztem lokalen Plan-Schlüssel verwaltet.
  `createPairing` und `rotatePairing` liefern das QR-Paket jeweils nur bei der
  bewussten Erzeugung/Rotation; ein Export bestehender Secrets existiert nicht.
- Der Pairing-State liegt ausschließlich als AES-GCM-Ciphertext in privaten
  SharedPreferences. Der Wrapping-Key liegt unter einem eigenen
  Android-Keystore-Alias. Bei fehlender oder beschädigter Kryptografie bleibt
  `available=false`; es gibt keinen Klartext-Fallback.
- ECDH P-256, HKDF-SHA-256, Join-HMAC und AES-256-GCM verwenden nur flüchtiges
  Sessionmaterial. AAD, Nonces, Base64URL-Eingaben und Größen werden strikt
  validiert.
- Beim erfolgreichen Session-Key-Ableiten muss der Client die serverseitige
  Ablaufzeit als begrenzten ISO-8601-UTC-Wert `expiresAt` (z. B.
  `2026-08-25T12:34:56.789Z`, maximal 40 Zeichen) übergeben. Native akzeptiert
  nur eine noch nicht abgelaufene Zeit innerhalb der nächsten zwei Stunden und
  bindet die daraus berechnete Epoch-Millisekunde zusätzlich in die HKDF-Info.
  Vor jeder Verschlüsselung/Entschlüsselung wird die native Wallclock- und
  monotone Ablaufgrenze geprüft; bei Ablauf werden Schlüssel, ECDH-Zustand und
  Replay-Daten atomar gelöscht. Pro Sitzung sind höchstens 400 erfolgreiche
  Frames erlaubt. Eine eingehende GCM-Nonce wird erst nach erfolgreicher
  Authentifizierung verbraucht und kann danach nicht erneut entschlüsseln.
- Die JS-Krypto-Argumente für `sessionId`, `sessionSalt`, Public Keys, HMACs,
  Nonce, AAD, Plaintext und Ciphertext sind ungepaddete Base64URL-Bytes.
  Der Join-HMAC bindet `KGG-LIVE-JOIN-V1 || sessionId || sessionSalt`; das
  Peer-Angebot bindet `KGG-LIVE-ECDH-OFFER-V1 || pairingId || role ||
  sessionId || publicKey`. Die HKDF-Info ist fest auf
  `KGG-LIVE-SESSION-V1 || pairingId || sessionId || expiresAtEpochMillis || therapist || patient`
  (ASCII-Dezimaldarstellung der nativen Epoch-Millisekunde).
  gebunden.
- Die schwarze immersive Abdeckung ist ausschließlich in Debug/Test-Builds
  verfügbar und stellt Window-Flags, Helligkeit und UI-Zustand beim Ende,
  Pause oder Fehler wieder her.

Der Transport für `KGGLiveKey` ist ausschließlich die gepinnte AndroidX-
WebMessage-Bridge `androidx.webkit:webkit:1.17.0`. Das JS-Objekt heißt
`window.KGGLiveKey`; es wird vor der Navigation registriert. Da die lokale
`file:`-Seite keinen engen `sourceOrigin`-Wert zulässt, wird bei der
Registrierung nur technisch notwendiges `*` verwendet. Jeder Callback lehnt
zuerst `isMainFrame=false` ab und prüft danach die aktuelle Hauptframe-URL mit
`KggLiveBridgePolicy` auf genau die vertrauenswürdige lokale KGG-Datei; nur
Query- oder Hash-Abweichungen sind erlaubt. `about:blank`, `blob:`, PDF-/andere
Unterframes und jede untrusted Hauptframe verlieren. Bei Navigation weg von
der Datei wird die native Sitzung geschlossen. Die anderen bestehenden
`KGGAndroidSync`, `KGGAndroidApp`, `KGGAndroidPdf`- und Release-Bridges bleiben
unverändert.

Der exakte asynchrone Vertrag ist:

```json
{"version":1,"requestId":"bounded-id","op":"operation","args":{}}
```

`requestId` ist 1–64 Zeichen aus `[A-Za-z0-9._~-]`; `version` muss `1` sein.
Das Objekt darf ausschließlich `version`, `requestId`, `op` und `args`
enthalten. Jede Anfrage erhält genau eine Antwort über
`JavaScriptReplyProxy.postMessage()` und im WebView über
`window.KGGLiveKey.onmessage`/`addEventListener("message", ...)`:

```json
{"version":1,"requestId":"bounded-id","ok":true,"result":{}}
{"version":1,"requestId":"bounded-id","ok":false,"error":"generic_code"}
```

Fehlercodes enthalten keine sensiblen Details. Die Operations-Allowlist und
ihre exakt erlaubten Argumentfelder sind:

- `getCapabilities {}`; `hasPairing|createPairing|rotatePairing|deletePairing`
  jeweils `{planKey}`; `computeJoinHmac` `{planKey,sessionId,sessionSalt}`.
- `verifyPeerOffer` `{planKey,localRole,sessionId,offer}`.
- `createEphemeralKeyPair` `{curve,planKey,sessionId,role}`. `curve` ist
  `P-256`; die Antwort enthält `publicKey`, `pairingId`,
  `pairingBinding` und einen begrenzten `privateKeyHandle`, aber niemals den
  privaten Schlüssel.
- `deriveSessionKey` `{curve,planKey,sessionId,sessionSalt,pairingId,
  pairingBinding,privateKeyHandle,peerPublicKey,role,expiresAt}`. Der Adapter
  rekonstruiert daraus intern das authentifizierte Peer-Angebot und verwendet
  ausschließlich den nativen flüchtigen Handle. `expiresAt` ist exakt der
  Relay-Wert im UTC-ISO-Format `YYYY-MM-DDTHH:mm:ss.SSSZ`, noch gültig und
  höchstens zwei Stunden entfernt; er wird nativ geprüft und in die HKDF-
  Sitzungsbindung aufgenommen.
- `encryptFrame` `{planKey,sessionId,aad,plaintext}` und `decryptFrame`
  `{planKey,sessionId,nonce,aad,ciphertext}`. Bytefelder sind ungepaddete
  Base64URL-Strings; AAD wird unverändert authentifiziert. `closeSession {}`
  schließt über denselben Frame-/URL-Guard. Debug-only sind zusätzlich
  `enableBlackout {}` und `disableBlackout {}`.

`planKey` ist die bewusst begrenzte native Adapterergänzung, weil der aktuelle
  Pairing-Speicher mehrere Planindizes unterstützt. Der kanonische Root-Client
  verwendet dafür einen Promise-Adapter, der die dokumentierten Operationen
  1:1 auf diese Tabelle abbildet. Bei fehlender
  `WEB_MESSAGE_LISTENER`-Unterstützung oder fehlgeschlagener Registrierung
  bleibt nur Live-Sync aus (`available=false`/kein Listener); QR-, Offline-,
  PDF- und normale App-Flows bleiben aktiv. Eine synchrone
  `addJavascriptInterface`-Kompatibilität für `KGGLiveKey` existiert nicht.

Die JVM-Tests decken den provider-neutralen Crypto-Core, Wrapping-Roundtrip,
Falsch-Alias/Manipulation, HMAC-/ECDH-/HKDF-/AAD-/Nonce-Grenzen, Session-Close
und die Frame-/Transport-Grenze ab. Ein späterer Instrumentation-Test auf einem
echten Android-Gerät muss zusätzlich Android Keystore, SharedPreferences und
die echte WebMessageListener-/WebView-Navigation, den Android Keystore,
SharedPreferences und den Tab-S9-Blackout-Restore-Vertrag nachweisen, bevor eine Produktionsfreigabe
zulässig ist.
