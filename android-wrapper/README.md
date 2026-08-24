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
- Die JS-Krypto-Argumente für `sessionId`, `sessionSalt`, Public Keys, HMACs,
  Nonce, AAD, Plaintext und Ciphertext sind ungepaddete Base64URL-Bytes.
  Der Join-HMAC bindet `KGG-LIVE-JOIN-V1 || sessionId || sessionSalt`; das
  Peer-Angebot bindet `KGG-LIVE-ECDH-OFFER-V1 || pairingId || role ||
  sessionId || publicKey`. Die HKDF-Info ist fest auf
  `KGG-LIVE-SESSION-V1 || pairingId || sessionId || therapist || patient`
  gebunden.
- Die schwarze immersive Abdeckung ist ausschließlich in Debug/Test-Builds
  verfügbar und stellt Window-Flags, Helligkeit und UI-Zustand beim Ende,
  Pause oder Fehler wieder her.

Die JVM-Tests decken den provider-neutralen Crypto-Core, Wrapping-Roundtrip,
Falsch-Alias/Manipulation, HMAC-/ECDH-/HKDF-/AAD-/Nonce-Grenzen, Session-Close
und Origin-/Größenprüfung ab. Ein späterer Instrumentation-Test auf einem
echten Android-Gerät muss zusätzlich Android Keystore, SharedPreferences und
den Tab-S9-Blackout-Restore-Vertrag nachweisen, bevor eine Produktionsfreigabe
zulässig ist.
