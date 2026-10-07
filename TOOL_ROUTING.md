# KGG Runtime Routing

Inherit shared dispatcher: `Kayus24/vibe-shared-knowledge/tool-routing/BASELINE.md`.

## Runtime dispatch
- **ChatGPT:** read `CHATGPT_TOOL_ROUTING.md`.
- **Codex:** read `CODEX_TOOL_ROUTING.md`.

Never apply ChatGPT plugin priorities to Codex. Never assume Codex-native browser/shell capabilities exist in ChatGPT.

## Source of truth
1. Fresh `main` and repository rules in `AGENTS.md`
2. `APP_BOUNDARIES.md`
3. Active source/manifests defined in `AGENTS.md` and `README.md`
4. `Kayus24/kgg-project-memory` only for durable decisions/rationale, never for live app state
5. Drive for long-running plans/benchmark logs, not live code state

## Gates
- No direct app/release/upload write to main.
- Preserve patient/admin boundary and protected areas.
- Run the test suites required by `AGENTS.md`.
- Use synthetic test data only.

## Directory routing
- `/`: project rules and cross-app contracts
- `kgg-update/src/**`: editable therapist/admin source
- `index.html`, `patient-*.js`, `collapse-cards.js`, PWA files: editable patient-app surface
- `kgg-plugin/**`: KGG plugin/UI-Lab implementation and contracts
- `android-wrapper/**`: native Android/WebView source
- `release-pipeline/**`: gates, release tools and test entry points
- `therapist-app/releases/**`: immutable historical release evidence; never patch basis
- `docs/**`: project documentation; distinguish active contracts from history
