# KGG ChatGPT Tool Routing

Applies only when the active agent is **ChatGPT**.

Inherit: `Kayus24/vibe-shared-knowledge/tool-routing/CHATGPT_BASELINE.md`.

## KGG-specific hierarchy
- Repo/PR/CI/live SHA: **GitHub**
- KGG visual/UI capture, observation, replay: **KGG UI Lab Private -> deterministic UI tests/Playwright**
- Persistent KGG UI bug: **Superpowers -> KGG UI Lab evidence -> local tests -> Context7 -> Stack Overflow edge case**
- Real Android/WebView/permission/camera/keyboard behavior: **Test Android Apps/ADB**, after ordinary web/UI causes are excluded
- Local build/test/scripts: **Remote Desktop Commander**
- Framework/API docs: **Context7 -> official upstream/GitHub -> Firecrawl Developer Search -> Stack Overflow edge case**
- External public web research/source retrieval: **Firecrawl Search/Scrape**
- Independent simple public browser check: **Firecrawl Interact**
- Long/authenticated external browser flow: **TinyFish only when Firecrawl/structured tools are insufficient**
- Editable design artifact: **Figma**
- Scientific evidence: **Consensus**; Firecrawl Paper Research for primary/full-text retrieval when needed
- Generated non-patient visual asset: **OpenArt**, synthetic only

## ChatGPT-only exclusions
- Vercel unless KGG deliberately becomes a Vercel project
- Game Studio for ordinary KGG UI work
- tldraw as primary implementation/design surface while host binding is unreliable
- Code Tytor as sole reviewer
- Legacy KGG Update Agents as first choice once UI Lab + repo-native path covers the task

## Runtime boundary
These plugin/connector priorities are **not Codex instructions**. Codex must use `CODEX_TOOL_ROUTING.md`.
