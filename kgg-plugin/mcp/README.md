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

`compare_visual_reference` compares the latest observed PNG against an
explicitly transferred artifact, an approved golden, or an earlier screenshot
from the same fixture. It requires matching viewport and device scale factor,
validates the reference hash, and returns deterministic pixel-diff evidence
with explicit thresholds and masks. A missing or unsafe reference is a typed
blocker; the server never discovers references from chat uploads or the
filesystem.

VC08 adds six bounded Flow operations: `save_flow`, `list_flows`, `get_flow`,
`run_flow`, `create_new_version`, and `deprecate_flow`. Built-in KGG Flows are
versioned and reviewable in the plugin; user-saved Flows are stored only as
synthetic, metadata-only JSON under the plugin-scoped local application-data
directory. Writes are atomic, namespaced by project/scope, and never overwrite
a published version. Flow steps use stable action IDs or accessibility
role/name descriptors; bounded coordinates are accepted only as documented
fallbacks, and arbitrary CSS/JavaScript, secrets, patient data, screenshots,
and live page contents are rejected.

VC09 adds the opt-in `record_screen` operation for short browser/HTML viewport
motion cases only. It requires the allowlisted real-browser host to advertise
`screen_recording` and `capture`, binds the run to the session/request/run ID,
enforces a hard maximum duration and frame interval, and always closes the
ephemeral page. The current host has no verified video transport, so the
operation returns a bounded `KEYFRAME_FALLBACK`: timestamped PNG keyframes with
SHA-256, content type, byte size, and session-bound retention. It exposes no
continuous recording, stores no video artifact, and fails closed when the host
capability is absent or a bound is invalid.

## VC12 migration boundary

The candidate is evaluated on three independent surfaces:

- A = existing Custom GPT (Production Control)
- B = ChatGPT + Plugin
- C = Codex + Plugin

`kgg_gpt_ab_compare.py` is a test/migration harness, not normal runtime.
`A/B/C full parity` is not claimed from local evidence: C-LOCAL evidence is
local real-browser evidence, C-STDIO is the synthetic package boundary, and a
missing external host is `NOT_OBSERVABLE`, never an inferred PASS; this is not a B/C host claim.

Migration eligibility is evaluated through the five bounded checks
`PARITY_PASS`, `SAFETY_PASS`, `EFFICIENCY_PASS`, `CROSS_SURFACE_PASS`, and
`STABILITY_PASS`. The measurement contract uses `NOT_MEASURED` for unavailable
values rather than fabricated zeroes. The evaluator is non-mutating and always
returns `release_allowed=false`; external Action dispatch, merge, deployment,
and replacement of the existing Custom GPT are outside this boundary.

Only synthetic test data is in scope. Raw evidence stays bound to its
session/request/run IDs and content hashes; tampering, stale identity, missing
bytes, sensitive fields, and unsafe references fail closed. The existing KGG
rollback path remains the recovery boundary, and a package-only result reports
`comparison_ready=false` until Fresh Main and surface evidence are independently
bound.
