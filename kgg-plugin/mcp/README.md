# KGG Plugin Candidate MCP boundary

The candidate ships the Skills, source map, the three Phase 2 read-only parity
fixtures (`current_state`, `ticket_plan`, `safe_canary`), and a self-contained
stdio MCP server at `mcp/server.py`. Those fixture names are an evaluation
surface, not additional MCP tools. The repository adapter remains the
canonical contract boundary over `release-pipeline/kgg_ui_lab_contract.py`,
`kgg_ui_lab_session.py`, `kgg_ui_lab_evidence.py`, and `kgg_ui_lab_runtime.py`;
the installed server exposes the same fixed bounded tool catalog without needing
the repository checkout.

Each tool validates the complete request at the trusted
boundary, bind actor and lease to the session, use Fresh Main and application
SHAs, return append-only event and evidence references, and keep Bruder relay
local and user-confirmable. A missing or unavailable MCP capability is a
negative test case and must produce a typed blocker rather than a fallback to
unrestricted shell or browser control.

When `KGG_REAL_BROWSER=1` is explicitly enabled and the runner advertises
`visual_loop`, `observe_visual_state` and `execute_visual_action` keep one
ephemeral page alive for exactly one bounded observe/decide/act/verify cycle.
The decision is supplied by the calling agent; the bridge never invents a
model decision. The default remains synthetic and the real host fails closed
when Playwright or the session helper is unavailable.
