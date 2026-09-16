# KGG Plugin Candidate MCP boundary

The candidate ships the Skills, source map, the three Phase 2 read-only parity
fixtures (`current_state`, `ticket_plan`, `safe_canary`), and a self-contained
stdio MCP server at `mcp/server.py`. Those fixture names are an evaluation
surface, not additional MCP tools. The repository adapter remains the
canonical contract boundary over `release-pipeline/kgg_ui_lab_contract.py`,
`kgg_ui_lab_session.py`, `kgg_ui_lab_evidence.py`, and `kgg_ui_lab_runtime.py`;
the installed server exposes the same fixed nine-tool catalog without needing
the repository checkout.

Each tool validates the complete request at the trusted
boundary, bind actor and lease to the session, use Fresh Main and application
SHAs, return append-only event and evidence references, and keep Bruder relay
local and user-confirmable. A missing or unavailable MCP capability is a
negative test case and must produce a typed blocker rather than a fallback to
unrestricted shell or browser control.
