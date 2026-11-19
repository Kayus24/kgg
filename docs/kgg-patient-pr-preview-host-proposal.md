# Host-Vorschlag für #377

Diese Änderungsskizze gehört zur späteren Aktivierung. Ziel ist der verifizierte
UI-Lab-Host mit dem bestehenden Launcher und der bestehenden Dispatch-Registry.

```diff
  KGG_GITHUB_WORKFLOW_OPERATIONS
+ submitKggVerifiedPatientPrPreview
+   repository: Kayus24/kgg
+   workflow: kgg-patient-pr-preview.yml
+   ref: refs/heads/main
+   inputs: source_pr, expected_head_sha, verified_run_id
```

Alle drei Felder sind Pflicht. PR- und Run-ID sind positive Dezimalzahlen, der
Head ist ein vollständiger 40-stelliger hexadezimaler SHA. Die Route akzeptiert
keinen Workflow-Ref, keinen Zielhost, keinen Payload und keinen Modus vom
Aufrufer. Bei Dispatch bleibt der Status bis zur Prüfung des exakten Runs und
seines öffentlichen Ergebnisses ausstehend. Die bisherige Allowlist bleibt bis
zu einem gesondert autorisierten Host-Rollout aktiv.

Die Registrierung erfordert die gesonderte Freigabe für diesen Infrastruktur-PR.
Zur späteren Inbetriebnahme gehört das GitHub-Environment
`patient-pr-preview` in Kayus24/kgg mit ausschließlich `main` als zulässigem
Deployment-Branch und dem Environment-Secret
`KGG_PATIENT_PREVIEW_PUBLISH_TOKEN`, ausschließlich mit Contents-Write für
Kayus24/kgg-patient-preview. Vor Host-Opt-in Launcher und Registry sichern,
Vorschlags-Diff und Workflow-Ref prüfen und bei einem Fehlschlag den gesicherten
Launcher zurückspielen. Die bestehenden GPT- und Live-Aktionen behalten ihre
vorhandenen Gates.

Der Workflow verlangt einen offenen Same-Repo-PR mit `kgg-no-release` und
einen erfolgreichen, aktuellen Required-Gate-Run für den exakten PR-Head
gegen aktuelles Main. Er übernimmt bis zu vier Änderungen an vorhandenen
Patienten-Runtime-Dateien. Unterstützende Patienten-Tests und generierte
Quelldokumentation aus dem PR werden weder ausgeführt noch veröffentlicht.
Bei Remote-Erfolg mit ausstehendem Pages-Rollout den laufenden Stand unter
der veröffentlichten Meta-URL prüfen. Der unveränderliche Pfad verhindert
einen zweiten Push desselben PR-Heads.
