# Patient Storage v7 – beaufsichtigter Custom-GPT-Lauf

## Ausgangslage

- Basis: `origin/main` bei `a367c001c1c3db4a87652e36811a08a0b74ea870`.
- Auftrag an das private `KGG Patienten-App Update-Agent` GPT: Read-only-Diagnose und sicherer Entwurf, ohne Write, Preview, PR oder Livegang.
- Bestätigte Ursache: `ph()` bindet Plan-ID, Titel und Übungsstruktur in den Legacy-Speicherpräfix ein.

## Beobachteter Verlauf

1. Das GPT bestätigte die korrekte Basis-SHA, den Bereich `patient-interface` und die Ursache in `ph()`.
2. Es erkannte, dass Storage, Mehrplan, Scan und Löschen gemeinsam betrachtet werden müssen.
3. Der erste Lauf blieb beim wiederholten Prüfen lokaler Quelldateien ohne neues Ergebnis hängen und wurde kontrolliert gestoppt.
4. Im korrigierten Lauf ohne weitere Actions erklärte das GPT ausdrücklich: `kontrollierte Übernahme durch Codex erforderlich`.
5. Begründung des GPT: Der vollständige Fix ist nicht nachweisbar sicher in vier `replace_exact`-Operationen und unter dem Payload-Limit abzubilden.

## Fehlgriffe und Ineffizienzen

- Der erste GPT-Lauf verbrachte zu viel Zeit in wiederholten Read-/SHA-Prüfungen, obwohl Basis und Ursache bereits feststanden.
- Ein zunächst erwogener großer Kompatibilitätslayer direkt in `index.html` hätte zu hohe Kopplung und eine schwer prüfbare Initialisierungsreihenfolge erzeugt.
- Ein reiner `ph()`-Hotfix wäre unvollständig: keine verlässliche Legacy-Migration, kein Exercise-Remapping und keine sichere Mehrplan-/Löschisolation.
- Im ersten lokalen Regressionstest war Fall 9 fälschlich rot, weil der Test nach der Migration den automatisch geöffneten Tag T4 statt explizit T1 las. Die gespeicherten T1-Werte waren korrekt vorhanden. Der Test wurde präzisiert; der Runtime-Ansatz musste nicht geändert werden.
- Der erste `validate_only`-Dispatch (`patient-storage-v7-hotfix-20260729-r1`) verwendete eine auf der lokalen PowerShell/.NET-Version nicht verfügbare statische SHA-256-Methode. Dadurch wurde ein leerer `old_sha256` gesendet und das Gate lehnte den Payload erwartungsgemäß ab. Der Wiederholungslauf erzeugt den Hash kompatibel und validiert den Payload vor dem Dispatch lokal.

## Übernommener technischer Ansatz

- Isoliertes `patient-storage-v7.js` als einzige Zuständigkeit für stabile IDs, v7-Schlüssel, Migration, Remapping, Orphans, Dual-Write und planselektives Löschen.
- Kleine Adapter im bestehenden Index sowie in Mehrplan-, Scan- und Löschmodul.
- Indexbasierte UI-Aufrufe bleiben kompatibel; persistiert wird zusätzlich `activePlanId`.
- Neue Browserregression mit stabilen Fehler-Fingerprints, fünf frischen Profilen pro Runde und zwei vollständigen Runden.

## Später zu prüfende Verbesserungen

- Den Patient-GPT-Action-Vertrag um branchgebundene Read-/Validate-Fähigkeit erweitern, ohne Schreibrechte auf `main` zu öffnen.
- Das Vier-Operationen-Limit für querschnittliche Storage-Migrationen durch ein signiertes Modul-Updateverfahren ersetzen.
- Die bestehende Service-Worker-Modulinjektion langfristig von hartcodierten Query-Versionen auf eine zentrale Modulmanifest-Quelle umstellen.
- Nach einer bestätigten Übergangsversion separat entscheiden, wann Legacy-Dual-Write und alte Schlüssel kontrolliert entfernt werden dürfen.

## Separater GPT-Infrastrukturfund

- Ein Read-only-Canary nach dem Knowledge-Upload meldete `stale_context`, weil Editor-Snapshot und Live-Manifest Profil `1.0.2` verlangen, der Bootstrap sich aber noch als `patient-v1` bezeichnete.
- Die einzelne Bootstrap-Kennung wurde auf `1.0.2` korrigiert. Dieser Fund betrifft nur die private GPT-Konfiguration, nicht die Patientenspeicherung.
- Der wiederholte Canary las weiterhin korrekt die Live-Version `v69`, erkannte Profil `1.0.2` und meldete `arbeitsfähig`. Damit überschreibt das v70-Knowledge erwartungsgemäß nicht den Live-Main-Stand.
