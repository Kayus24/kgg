# KGG Tool Routing

Inherit: `Kayus24/vibe-shared-knowledge/tool-routing/BASELINE.md`.

## Source of truth
1. Fresh `main` and repository rules in `AGENTS.md`
2. `APP_BOUNDARIES.md`
3. Active source/manifests defined in `AGENTS.md` and `README.md`
4. `Kayus24/kgg-project-memory` only for durable decisions/rationale, never for live app state
5. Drive for long-running plans/benchmark logs, not live code state

## Preferred hierarchy by task
- Repo/PR/CI/live SHA: **GitHub**
- KGG visual/UI capture, observation, replay: **KGG UI Lab Private -> deterministic UI tests/Playwright**
- Persistent KGG UI bug: **Superpowers workflow -> KGG UI Lab evidence -> local tests -> Context7 -> Stack Overflow edge case**
- Real Android/WebView/permission/camera/keyboard behavior: **Test Android Apps/ADB**, after excluding ordinary web/UI causes
- Local build/test/scripts: **Remote Desktop Commander**
- Framework/API docs: **Context7 -> official upstream/GitHub -> Firecrawl Developer Search -> Stack Overflow edge case**
- External public web research/source retrieval: **Firecrawl Search/Scrape** as the default external-web layer
- Independent simple public browser check: **Firecrawl Interact**
- Long/authenticated external browser flow: **TinyFish only when Firecrawl/structured tools are insufficient**
- Editable UI/design artifact: **Figma**
- Scientific evidence questions supporting content/clinical background: **Consensus**; do not let research tools modify product truth
- Generated non-patient visual asset: **OpenArt**, synthetic only

## Avoid / do not route here
- Vercel unless KGG is deliberately moved to a Vercel project
- Game Studio for ordinary KGG UI work
- tldraw as primary implementation/design surface while host binding is unreliable
- Code Tytor as the only reviewer
- Legacy KGG Update Agents as first choice once UI Lab + repo-native path covers the task

## Gates
- No direct app/release/upload write to main.
- Preserve patient/admin boundary and protected areas.
- Run the test suites required by `AGENTS.md`.
- Use synthetic test data only.
## Directory routing
- `/`: project rules and cross-app contracts; read `AGENTS.md`, `APP_BOUNDARIES.md`, `TOOL_ROUTING.md` before broad work.
- `kgg-update/src/**`: editable therapist/admin source. Use for admin implementation work.
- `index.html`, `patient-*.js`, `collapse-cards.js`, PWA files: editable patient-app surface. Keep separate from admin work.
- `kgg-plugin/**`: KGG plugin/UI-Lab implementation and contracts.
- `android-wrapper/**`: native Android/WebView source; use only for Android-specific tasks.
- `release-pipeline/**`: gates, release tools and test entry points; use for verification/release work.
- `therapist-app/releases/**`: immutable historical release evidence; read for regression/hash/history, never as patch basis.
- `docs/**`: project documentation; distinguish active contracts from history before treating a document as instruction.
