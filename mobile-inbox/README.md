# KGG Mobile-Inbox

Dies ist der einfache Handy-Weg ohne Codex:

1. In der Admin-App **Aktuelle HTML speichern**.
2. In GitHub den Branch `mobile-inbox` öffnen.
3. Die gespeicherte HTML-Datei in diesen Ordner hochladen.
4. GitHub Actions erzeugt daraus automatisch einen geprüften Admin-Beta-Release über Branch + Pull Request.
5. Nach dem Test kann die aktuelle Admin-Beta über die Action **Promote latest KGG Admin beta** für Kolleg:innen freigegeben werden.

Wichtig: Keine Patientendaten, keine API-Keys und keine Secrets in diese HTML-Datei schreiben.
