# KGG Plugin Candidate source map

This candidate deliberately keeps the existing Custom GPT as Production
Control. Skills are the reusable coordination layer; the UI Lab remains the
deterministic runtime and trusted boundary.

| Candidate surface | Canonical repository source | Snapshot SHA-256 | Responsibility |
| --- | --- | --- | --- |
| `kgg-supervisor` | `docs/kgg-ui-lab-v1-goal-prompt.md`, `docs/kgg-custom-gpt-goal-prompt.md` | `acb020319cf38870f3cd54bd5ab3018a3fbd0351f0361fad677d4bd0eb628f82`, `ab4d39cbb2a413bd9f2ad69115a1717766366ffbc0b30ebe24c8d788a4ca2cd4` | scope, phase order, source-of-truth discipline, metric-provenance gate, local Production-Control preflight before external runs |
| `kgg-operations` | `docs/kgg-custom-gpt-knowledge-operations.md`, `docs/kgg-ui-lab-v1-contracts.md` | `c33e37c73947f7a16fddfe3af03ddfc71676443e3d2de8f10b781c2c357066c1`, `895fc790a61b719cc2510bf07c73a703659ec053306844f2eb57509ab8cba016` | small-ticket workflow and runtime handoff |
| `kgg-testing` | `docs/kgg-custom-gpt-knowledge-testing.md`, `release-pipeline/kgg_test_battery.py` | `526435598da7fdf5a2081588cf18103c839389ea81fc8109ab8e7142a6348688`, `6c6121b47816414ebb0ac5c6daa74b61a51986182a06458f5839c023b104fc5b` | red/green/replay and regression loops |
| `kgg-safety` | `docs/kgg-custom-gpt-knowledge-safety.md`, `release-pipeline/kgg_ui_lab_contract.py` | `886d16e8b5776ad41979fb2d075c28e9b4eb24341026b4b70b64b40d669c1af6`, `4ea5e4a411b7b6efceb256023d3d2cc56ceb9fbf3003869600e48a2ad8076cd7` | privacy, authorization, provenance gates |
| `kgg-escalation` | `release-pipeline/kgg_ui_lab_runtime.py`, `release-pipeline/kgg_brain_relay_worker.py` | `b3c845b02341b0773a4a922c98feb6f3085993cf7c2e76f58c4da221fa54154f`, `33aa926607e46fa0525dff72637c6d1976562c6227ef6134ce6077b18b57b4bf` | bounded Bruder fallback |
| UI-Lab adapter | `release-pipeline/kgg_ui_lab_browser.py`, `release-pipeline/kgg_ui_lab_mcp_adapter.py` | `6d5657202b5c871c3f9ebe04c2dac64d81ea55d635da17bf53d7a66b50e6ba21`, `7c06f98b63b09dd23d1d88a5a5a3126941485436336a218a7829cc27fd0b253d` | semantic browser and fixed MCP tool catalog |
| Quick-Flow certificates | `release-pipeline/kgg_ui_lab_quick_flows.py` | `5396cb1d29425c9d8d171bcb1068f43ab4f922b32692f17cd82f2aff541e5d3d` | exactly three initial flows |
| Phase 2 parity fixtures | `release-pipeline/kgg_plugin_candidate_parity.py` | `d07fecf269ea01fa0a7026aab6e2b3949f0d3dff5248b4b4189358d040e84960` | read-only `current_state`, `ticket_plan`, `safe_canary` |
| Candidate installation gate | `release-pipeline/kgg_plugin_candidate_gate.py` | `8c641dbdfc054e9c715ea09dc0c599102be9cf5656d1527b02da75a2c98e1b3d` | accepts a Codex build cachebuster while enforcing the semantic base version |
| Migration-gate evaluator | `release-pipeline/kgg_ui_lab_migration_gate.py` | `5c9c3381a30ebcf3e8c04073ffa755bf2eafebecaf5045d2e7804cb033aeec59` | fail-closed five-gate eligibility result; `--report` evaluates the supplied JSON and verifies optional evidence-file hashes |
| Fault-injection matrix | `release-pipeline/kgg_ui_lab_fault_injection.py` | `bbe25511f71a79e09f5bad018ee4f56648e757400e51d529a1eb25a4a98d3911` | 23 named bounded failure scenarios with expected/actual evidence fields |
| Surface metric pilot | `release-pipeline/kgg_ui_lab_surface_metrics.py` | `8a86431bd4db20d79482bb3985cf8eb24e3140dfad3f763728aedf02b2fc72e1` | complete local Candidate read-only metric payload with independent result and diagnosis evidence |
| Surface comparison harness | `release-pipeline/kgg_gpt_ab_compare.py` | `9938b7c430e6da67fa9470027534106996f48b8e31a9ec8cc2980a92b84acbf9` | fail-closed A/B/C metrics, exact-field rejection, hexadecimal Fresh-Main SHA equality and replacement guard including root-cause quality |
| Measurement envelope | `release-pipeline/kgg_gpt_measurement.py`, `docs/kgg-ui-lab-v1-measurement-envelope.md`, `docs/kgg-custom-gpt-action-api-openapi.yaml`, `docs/kgg-custom-gpt-action-schema.md` | `baa12d914a60222f219850c8b5dc3b6a14fbe815e5dee5f23df35abfe0d1cc9c`, `0c77253cc0c5512e84742d53d32fe1f0020bccc53cf3d79dd973d4d20f994b0d`, `73f4d0436c4c68c0ef8a2ccf416b3006c7eb357e8fa676ddeaf3c71430ca9d3a`, `53dd8358ac51bac3c7873f79467cd13ea28ea631a84fcf16a627177116d06954` | tamper-evident, content-hashed field-level provenance and explicit read-only result-artifact reconciliation; missing metrics remain bounded failure |
| Production-Control preflight | `release-pipeline/kgg_production_control_preflight.py`, `docs/kgg-ui-lab-v1-production-control-readonly-contract.json` | `b284cee2e07229045618bef21c55116ffc1babef738b7c50c30a583f68e3bb6d`, `cc8ba42694322e8f091583766c26a41ecb64d40ba40f72f80e8cc89b135733ae` | local fail-closed capability and structured dated external-editor-evidence check before any external model run; explicit no-dispatch/runner profiles |

| Installed MCP transport | `kgg-plugin/.codex-plugin/plugin.json`, `kgg-plugin/.mcp.json`, `kgg-plugin/mcp/server.py`, `kgg-plugin/mcp/real_browser.py`, `kgg-plugin/mcp/browser_host.js`, `kgg-plugin/mcp/browser_session_host.js`, `kgg-plugin/scripts/eval/validate_candidate.py` | `298af877cde291adb50d8a7a97701ec6a4e9143b341df9992a1ee77cd030df0f`, `6b56eca8caa1c12966783e72fd2354819ef6dc8e0ea662026e472a889954aa73`, `b24aaf9d798b94e27b20def6be0bd62d329ce4d0cf4fcc0e96908832f5134766`, `635f3a44dcda6088e7e7f3121e0dc6c89f02465a17a2d73e7630083daf285220`, `980570b3cca92eaf5d21d50547e2d2dc12dab9bf9614b92d24f397d573cc779a`, `3b8ace58a93bffaa157fedeb670472f4c966107e9ff814a4750a5574d3b1e7a6`, `de41f19337e50ea9b86db078c2fed7e9f2af7b779feeaa905d6525a2539f1fc8` | self-contained stdio MCP server with a fail-closed, opt-in Playwright host bridge; default remains synthetic and in-memory, while trusted local real-browser, visual-loop, drift-fallback and navigation-guard runs return hashed screenshot evidence only from local KGG origins or the allowlisted GitHub Pages paths |

The future MCP adapter must expose only contract-shaped operations such as
session creation, runner selection, Quick Flow execution, evidence validation,
and local handoff enqueueing. The installed candidate additionally contains a
self-contained stdio MCP transport exposing the same bounded operations. It keeps
state in memory and must not expose arbitrary shell, editor, live, merge, or
external-message writes. Host capability differences (Codex hooks, ChatGPT
apps/actions, and browser availability) are measured in the comparison phase;
they are not inferred from this static candidate.

The hashes are a candidate snapshot, not proof that Fresh Main or the external
Custom GPT editor currently carries the same bytes. A comparison run must
recompute them and fail closed on drift.
