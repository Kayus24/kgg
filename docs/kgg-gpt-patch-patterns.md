# KGG GPT Patch Patterns

Use these patterns to avoid repeating known KGG regressions.

## Forbidden Patterns

### global-touch-action

- Risk: Global touch or pointer rules can break swipe, scroll and drag/reorder flows.
- Avoid: Do not add broad `touch-action`, `pointer-events` or gesture rules on app-wide containers.
- Prefer: Limit gesture rules to the exact handle/control and run UI stability regression.

### modal-scoped-only-to-tablet

- Risk: Closed modals can leak into the phone document flow when hiding rules are scoped only to tablet classes.
- Avoid: Do not hide modal overlays only below `body.tabletLayoutCustom`.
- Prefer: Give the modal a global hidden base rule and then layer tablet-specific presentation separately.

### breakpoint-drift

- Risk: Phone and tablet UI can both become active if the 759/760 px split drifts.
- Avoid: Do not test breakpoints with browser zoom or change phone/tablet media queries incidentally.
- Prefer: Use real viewports: phone <=759 px, tablet >=760 px.

### debug-output-to-patient

- Risk: Patient-facing output must never expose raw JSON, Base64 or debug payloads.
- Avoid: Do not route debug pages or payload dumps into normal patient flows.
- Prefer: Keep debug output internal and preserve patient-safe rendering.

### side-effect-feature-touch

- Risk: Small UI fixes often become unsafe when they also touch QR, PDF, parser, scan or plan state.
- Avoid: Do not edit protected feature blocks unless Max explicitly asked for that area.
- Prefer: Make one scoped patch and list all untouched protected areas in the PR.

## Area Test Hints

- `debug`: Debug output must stay internal and never become patient-facing output.
- `drag-reorder`: Test drag/reorder and swipe/delete separately on phone and tablet.
- `general`: Use the risk-matched KGG test battery and keep unrelated features unchanged.
- `modal`: Verify closed modal is not in normal flow; verify explicit open/close.
- `parser-textblocks`: Run textblocks regression when parser/text-block behavior is touched.
- `pdf`: Use the risk-matched KGG test battery and keep unrelated features unchanged.
- `phone-layout`: Use real phone viewport <=759 px and run ui-stability regression.
- `qr-patient`: Do not touch QR/patient flow unless explicitly requested; run patient-qr critical when touched.
- `scan-camera`: Use the risk-matched KGG test battery and keep unrelated features unchanged.
- `sync`: Run sync regression when sync, bank, package or peer behavior is touched.
- `tablet-layout`: Use real tablet viewport >=760 px and run ui-stability regression.

## PR Reminder

- Include `base file used`, `changed file`, `changes`, `smoke test` and `risks`.
- Mention the matching bug-history lesson when one exists.
- Do not mark tests green unless GitHub or local output proves it.
