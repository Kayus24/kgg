# KGG Codex Tool Routing

Applies only when the active agent is **Codex**.

Inherit: `Kayus24/vibe-shared-knowledge/tool-routing/CODEX_BASELINE.md`.

## KGG-specific hierarchy
1. Read `AGENTS.md`, `TOOL_ROUTING.md`, `APP_BOUNDARIES.md`, then only the smallest relevant source files.
2. Use local Git/worktree state as the implementation truth; inspect diffs before editing.
3. Use repository-native search and shell first (`rg`, Git, existing scripts).
4. Reproduce the issue locally before patching whenever possible.
5. Make the smallest patch and preserve existing hooks/contracts.
6. Run the narrowest relevant KGG test, then the required regression gate from `AGENTS.md`.

## Browser/UI work
- For therapist/admin or patient web UI inspection, **use Codex's own browser first**.
- For local development, run the local/dev preview and inspect it in the Codex in-app browser.
- Use Codex Developer Mode/full CDP access when approved for console, network, DOM/page state, paint/performance or flicker debugging.
- Use repository Playwright/E2E tests when deterministic evidence is required.
- Use the Codex Chrome extension only when the task specifically needs the user's existing Chrome profile/session/tabs/extensions.

## Android work
- For Android/WebView/device-only behavior, use local Android SDK/ADB/emulator tooling through Codex shell.
- Use `android-wrapper/**` and `release-pipeline/**` as the project-native Android/build surface.
- Browser-only evidence cannot certify Android-only behavior.

## External web/docs
- For a webpage or official documentation that must be inspected, use Codex's own browser.
- Prefer repository docs and official upstream sources before community material.
- **Do not route web tasks to Firecrawl by default.**
- ChatGPT plugins such as Firecrawl, TinyFish, Consensus, KGG UI Lab or OpenArt are not inherited into Codex.

## Stop rule
If an external MCP/tool is not explicitly configured for Codex in this project, do not assume it exists just because ChatGPT can use it.
