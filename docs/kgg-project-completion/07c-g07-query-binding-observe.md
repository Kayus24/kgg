# G07 – Query-gebundene Real-Browser-Observation

## Ergebnis

Der einmalige `POST_QUERY_BINDING_OBSERVE_ONLY_V3`-Lauf ist für Surface B
erfolgreich abgeschlossen. Die kanonische synthetische Fixture wurde über die
autoritative `meta.url` einschließlich Plan-Query gebunden. `start_ui_session`
war `PASS`; genau eine `observe_visual_state`-Observation lief auf
`real_browser`, ohne Fallback oder Aktion.

Gebundene Evidence:

- Fresh Main: `b3800e5e1301e37763a780d5d1a5f7438337c5a8`
- Preview-SHA: `66e212fc2dba849a56bc7709c098c9400930937a`
- Observation-ID: `11f449f88a8639eb2b2cd14eef2f00f83eae02146c2880203109841b1b093d8c`
- Screenshot-ID: `kgg-visual--v3-20260923-01`
- Screenshot-SHA-256: `ab6f694d5a3bbe10daf2ab10fdce9a426911ef081ac8e3c125683588a9d29bbe`

Alle erwarteten nicht-sensitiven Marker waren sichtbar: `KGG synthetischer
Testplan`, `Beinpresse`, `Rudern` und `2 Sätze`.

## Bruder-GPT-Bewertung

`DECISION=CONTINUE`. Der vorherige Blocker war kein Browser-, Plugin- oder
Renderingfehler, sondern `PATH_ONLY_WITHOUT_PLAN_QUERY`. Der Bruder empfiehlt,
keine identische Observation zu wiederholen und zuerst die Evidence zu
reconciliieren. V3 darf als erster belastbarer
`B_REAL_HOST_READ_ONLY_OBSERVATION_E3 + PROVENANCE_VERIFIED`-Nachweis geführt
werden.

## Grenzen

Der Lauf beweist noch keine Aktion, keine Zustandsänderung, keine
`Observe → Decide → Act → Verify`-Schleife und keinen Quick Flow. Deshalb
bleiben `G05=PARTIAL`, `G06=PARTIAL`, `PRODUCTION_CONTROL=PILOT_INCOMPLETE`,
`A_B=NOT_COMPARABLE` und `replacement_eligible=false` unverändert. Die früheren
V1/V2-Läufe bleiben historisch bzw. quarantänisiert und werden nicht mit V3
vermischt.

## Nächster zulässiger Schritt

Zuerst ausschließlich Evidence-Reconciliation. Ein funktionaler Folgeschritt
ist nur über ein neues, separat gebundenes `ACTION_THEN_VERIFY`-Gate zulässig:
eine harmlose reversible Aktion auf derselben synthetischen Fixture und danach
genau eine Verify-Observation. Das ist ein neuer kausaler Capability-Test, kein
Retry des Observe-Laufs.
