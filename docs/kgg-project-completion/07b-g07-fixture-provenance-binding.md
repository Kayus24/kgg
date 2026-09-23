# G07b – Fixture-Provenance-Bindung

Dieses Addendum verhindert, dass ein beliebiger Dienst auf einem erlaubten
Localhost-Port als KGG-Synthetic-Fixture gewertet wird.

## Verbindliche Zielbindung vor jeder B-Observation

Eine G07-B-Observation ist nur zulässig, wenn alle folgenden Werte vor dem
Browserstart statisch gebunden und read-only verifiziert sind:

```text
EXPECTED_URL=<exakte kanonische HTTPS-URL oder lokal verifizierte KGG-URL>
SOURCE_REPOSITORY=Kayus24/kgg
FIXTURE_IDENTIFIER=<exakter Preview-/Fixture-Identifier>
SYNTHETIC_PROVENANCE=SYNTHETIC_ONLY|verifizierbare synthetische Quelle
EXPECTED_NON_SENSITIVE_MARKERS=<mindestens ein überprüfbarer Marker>
```

`127.0.0.1:<port>/kgg-patient-preview` ist allein keine ausreichende
Fixture-Bindung. Eine lokale URL darf nur verwendet werden, wenn der laufende
Prozess, der Quellpfad und die erwartete Fixture-Kennung unabhängig mit
`SOURCE_REPOSITORY` und `SYNTHETIC_PROVENANCE` übereinstimmen.

## CONTROL_LOOP_GATE: FIXTURE_BINDING_CHECK

1. URL exakt gegen `EXPECTED_URL` vergleichen.
2. Serverprozess und Quellrepository read-only feststellen.
3. HTML-/Build-Marker und Fixture-Identifier prüfen.
4. Dateninputs auf fest kodierte synthetische Werte, Storage, Query-Parameter,
   APIs und Produktionsquellen prüfen.
5. Nur bei vollständiger Übereinstimmung `FIXTURE_BINDING=PASS` setzen.

Bei Abweichung:

```text
FIXTURE_BINDING=FAIL
FIXTURE_SOURCE_MISMATCH
NO_OBSERVE
NO_ACTION
```

Ein erfolgreicher Browserstart oder Screenshot hebt diesen Fail-Closed-Status
nicht auf.

## Evidence-Trennung

Ein Lauf gegen ein falsches Ziel darf als technische Evidence für die
Erreichbarkeit des Browserpfads erhalten bleiben. Sein Bildinhalt und jede
fachliche UI-/Safety-/Comparator-Aussage bleiben jedoch
`QUARANTINED_NON_COUNTABLE`.

## Aktueller Befund (2026-09-23)

Der Lauf gegen `http://127.0.0.1:4173/kgg-patient-preview` erreichte eine
separate `check-in-timer`-App. Deshalb lautet der Befund
`FIXTURE_SOURCE_MISMATCH` / `PROVENANCE_NOT_ESTABLISHED`.
Die kanonische KGG-Preview ist statisch bekannt, wurde in diesem Envelope aber
nicht erneut beobachtet. Ein neuer Lauf benötigt daher das separate Gate
`POST_PROVENANCE_FIX_OBSERVE_ONLY` und darf ausschließlich
`start_ui_session → observe_visual_state` ohne Action ausführen.
