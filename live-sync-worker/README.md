# KGG Live-Sync Worker – Ticket 034

Lokaler, ausschliesslich synthetischer Relay-Prototyp. Der Default-Modus in
`wrangler.toml` ist `off`; die lokale Testkonfiguration nutzt explizit `test`
und eine kurze Test-TTL. Es gibt keinen Produktionsendpunkt und keinen
Cloudflare-Deploy-Schritt.

## Lokal prüfen

```powershell
npm ci
npm run typecheck
npm test
```

Die API ist in `src/worker.ts` dokumentiert und folgt den Pfaden aus
`ticket-034-protocol-v1.md`. Rollen-Tokens werden nur als SHA-256-Hash im
Durable Object gespeichert. WebSocket-Verbindungen werden mit der
Durable-Object-Hibernation-API angenommen; Tokens werden nur im ersten Frame
übertragen und nie in URLs verwendet.

Die Test-API nutzt diese synthetischen Hüllen:

- `POST /v1/sessions/reserve`: `{ "therapistTokenHash": "<base64url-sha256>" }`.
- `POST /v1/sessions/{code}/arm`: `Authorization: Bearer <token>` und `{ "joinProof": "<base64url-hmac>" }`.
- `GET /v1/sessions/{code}/challenge`: liefert `sessionId`, `sessionSalt`, `expiresAt` und `protocolVersion`.
- `POST /v1/sessions/{code}/join`: `{ "joinProof": "<base64url-hmac>", "patientTokenHash": "<base64url-sha256>" }`.
- `GET /v1/sessions/{code}/socket`: erstes WebSocket-Frame ist `{ "type": "auth", "role": "therapist|patient", "token": "<opaque>" }`.
- `DELETE /v1/sessions/{code}`: beendet die Sitzung und leert den gesamten DO-Speicher.

Die lokale Hibernation-Testumgebung unterstützt `jurisdiction("eu")` noch
nicht. Nur bei `LIVE_SYNC_MODE=test` verwendet der Testpfad deshalb eine
lokale Namespace-Emulation; in allen anderen Modi gibt es keinen Fallback.
