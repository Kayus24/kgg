# Codex-Fortsetzung – Custom-GPT-Synchronisierung

Stand: 2026-08-21

- Admin-GPT: `g-6a45fba0f3408191ac1fb2c987a2e960`, privat, vier kanonische Knowledge-Dateien und beide Actions sichtbar.
- Lokaler Produktionsaudit: `TARGET_PASS`; Snapshot steht bewusst auf `target-pending-live-editor-sync`, weil die Operations-Knowledge-Datei nach der letzten Änderung extern erneut hochgeladen/verifiziert werden muss.
- `LIVE_PASS` darf erst nach echter Editorprüfung gesetzt werden.
- Patient-GPT bleibt bis zur externen Knowledge-Synchronisierung `stale_context`/nicht verlässlich nutzbar.
- Keine Memory-Statusänderung, kein Preview-Dispatch und keine Secrets.

Nächster Schritt: im externen Editor nur die vier kanonischen Patient-/Admin-Ressourcen abgleichen, danach lokal Snapshot und strikten Live-Audit prüfen.
