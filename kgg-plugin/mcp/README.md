# KGG Plugin Candidate MCP boundary

The candidate ships the Skills, source map, the three Phase 2 read-only parity
fixtures (`current_state`, `ticket_plan`, `safe_canary`), and a self-contained
stdio MCP server at `mcp/server.py`. Those fixture names are an evaluation
surface, not additional MCP tools. The repository adapter remains the
canonical contract boundary over `release-pipeline/kgg_ui_lab_contract.py`,
`kgg_ui_lab_session.py`, `kgg_ui_lab_evidence.py`, and `kgg_ui_lab_runtime.py`;
the installed server exposes bounded tools without needing the repository checkout.

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
model decision. One narrow native patient continuation is allowed after a
verified `patient-plan` -> `patient-card-open` click: the response exposes a
fresh `next_observation` bound to the same page, and exactly one further
click/tap must verify `patient-numpad`. Both steps require changed screenshots;
wrong targets, stale observation IDs and unchanged clicks fail closed. All
other actions still close after one cycle. The default remains synthetic and
the real host fails closed when Playwright or the session helper is unavailable.

For ChatGPT Fast clients unable to inspect image tool parts, the same observation
also returns `observation.controls`: up to 24 visible, enabled, uniquely
identified buttons from fixed `data-kgg-action` markers or the existing
`kggLangSwitch` language toggle. Labels are stable action IDs, not page text,
patient names, input values, URLs or arbitrary accessibility content. Prefer
`execute_visual_action` with an exact observed label and fresh observation ID;
the real browser rechecks uniqueness, visibility and enabled state before
clicking. Ambiguous/hidden/disabled targets fail closed. Retain screenshot
evidence for verification; a metadata-only result is not visual understanding.
For this multi-step path, call `observe_visual_state` then
`execute_visual_action`, not a new one-shot `capture_screenshot` request.
The source change does not activate the installed ChatGPT plugin automatically.

Version 0.2.0 adds public `back` and `reload` decisions and saved Flow steps.
Back requires an existing permitted history entry. Main-frame redirects outside
the permitted origin are blocked. Reload may preserve the state only after
the browser confirms navigation and produces a fresh screenshot artifact.

Version 0.3.0 adds opt-in `KGG_GITHUB_READS=1` on the trusted PC host. It uses
the existing GitHub CLI keyring login; no credential is exported or packaged.
`get_kgg_action_capabilities` declares all 30 canonical Action definitions;
`run_kgg_action` binds their GET routes with exact parameter validation and
blocks every POST with `external_gate_required`. Existing Action workflows
remain the write boundary. The callable adapter also works with the repository's
`KggCompatibilityShim`. A declaration is not evidence of external write parity.
`get_kgg_resource` reads fixed Main resources. `get_current_state` reads live
Main when enabled; `get_ticket_state` reads a GitHub issue summary, explicitly
distinguished from Memory ticket IDs. Memory ticket analysis starts from the
Memory index and a relevant bounded pack. Disabled hosts remain synthetic.

Version 0.4.0 integrates these preserved candidates on current Main and adds
real `run_width_sweep` captures when the trusted host opts into the browser.
Each of up to ten validated viewports gets an isolated page, PNG hash and
state evidence. The entire sweep has a 30-second deadline and an 8-MiB image
budget; failure preserves completed evidence and marks remaining widths
`NOT_RUN`. A successful sweep verifies `capture_only`; `visual_comparison`
remains `NOT_RUN` until approved references are compared separately. Without
real-browser opt-in it remains `PREVIEW_ONLY`.

The installed ChatGPT endpoint requires a separate approved package/runtime
activation and fresh catalog check. Local tests do not establish ChatGPT on
physical phone/tablet, cold-PC reconnect, or protected KGG write/release parity.
The existing Update-Agents remain the production fallback until those gates
are independently accepted. The package contains no credentials.

Version0.5.0 adds the explicit write-annotated `dispatch_kgg_workflow` tool
(server1.4.0,24 tools). The existing `run_kgg_action` stays read-only and rejects
all POST routes. Workflow dispatch is disabled by default. The trusted host may
set `KGG_GITHUB_WORKFLOW_OPERATIONS` to a comma-separated list of canonical
operations in addition to `KGG_GITHUB_READS=1`. A tool payload or `actor=max`
cannot change that host policy. Device tests and editor certification require
their actual separate device/editor authorization and evidence.

The six non-consequential workflows and Memory `validate_only` can be enabled
individually. Main/Snapshot PR workflows and Memory `apply` remain externally
gated: model-supplied approval phrases are not a trusted human-approval record.
Only canonical Main schemas and fixed workflow paths are accepted. HTTP204
means `dispatch_accepted`, never a completed validation, preview or release.
Reconcile the exact request ID, source SHA, run and result artifact through the
existing read operations. Repeated/unknown requests are latched for the process
lifetime; after a restart reconcile GitHub state before any new dispatch.

The package icon reuses a previously generated KGG training-and-target motif.
Its `composerIcon` and `logo` are package-relative PNG assets. The existing
private ChatGPT listing is a separate remote plugin and must be updated and
visually checked through its own Edit Plugin connection; changing this package
does not silently update that listing.

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

## Local patient authoring for #377

Use the already authorized Private Desktop Commander session on Max's PC for
the local authoring step. Verify the host, exclusive worktree, full HEAD SHA
and current UI Lab capabilities before any write. Reproduce the problem with
synthetic data and keep the focused test unchanged for GREEN and replay.

From that worktree, use `python release-pipeline/kgg_patient_gpt_write_gate.py`
with these mode arguments:

| Step | Arguments | Result |
| --- | --- | --- |
| Preflight | `--mode local_preflight --payload-file <worktree-json>` | Patient target, synthetic scope, HEAD and patch SHA-256, with a blank confirmation field |
| Start | `--mode local_prepare --payload-file <worktree-json> --local-approval-file <worktree-json>` | Local job, PID, deadline and paths to the baseline and candidate after validation |
| Status | `--mode local_status --local-job <request-id>` | Short, hash-checked job status |
| Evidence | `--mode local_evidence --local-job <request-id>` | Status and baseline/candidate byte hashes |

The confirmation file is the `confirmation` object from preflight with
`approval_phrase` set to `Zulassen` after Max explicitly authorizes that exact
local patch. The JSON binds the operator confirmation to the payload. Access to the command
and worktree is governed by Private Desktop Commander.

Use `dc_start_process` with the absolute script and input paths and a short
tool timeout. Its PID identifies the session for `dc_read_process_output`.
Read status by request ID when stdout is unavailable. An existing request ID
returns its original receipt. If the deadline passes without a terminal
receipt, treat `UNKNOWN` as requiring reconciliation through the existing
process and result handoff. A failed or unknown job stays reserved. A targeted
correction uses a new request ID and the same focused test.

`COMPLETE` covers local authoring. For the #377 synthetic settings-button
case, start the browser loop with a fresh approved request instead of running
`local_prepare` first. Use the browser runner's `preflight` command with
the same base SHA, schema, attempt and payload. It returns the confirmation
object and result file path before starting any process. With the same
authorized PDC host and absolute paths,
run `python release-pipeline/kgg_patient_local_test.py start --base-sha <full-sha>
--schema kgg.patient-local-test/v1 --attempt 1 --payload-file <file>
--approval-file <file>`. The input names
`playwright-card-settings-accessible-name` as its only focused test and limits
the patch to `patient-card-settings.js`. This profile reproduces RED on the
Git baseline before authoring, then runs the same browser script in fresh
contexts for GREEN and replay. Its PASS covers those three phases.

The `start` receipt contains the local worker PID, job/run IDs, deadline,
and absolute `result_file`. Use `status` or `evidence` with the same
`--base-sha` and `--attempt` to reconcile output. The worker writes
`result.json` first, then a compact `notice.md` ending in `ENDE notice`.
For an already authorized gptflow handoff, register that canonical notice
path once as the existing PDC `result_file`. PDC owns destination
verification, delivery and deduplication. Use the verified Kgg aps Lead's
exact URL or registered self-marker. Check the gptflow job through
`chatgpt_send_status`. With no verified destination or a disconnected
extension, preserve the checkpoint and reconcile by ID. The notice
wakes the Lead, who reads and checks the evidence independently.

Only a reproduced candidate assertion failure permits the next attempt
with a different patch, fresh authoring approval and the same browser
script. Review the failed action and diagnose its cause before retrying.
Attempts 1 through 3 are reserved once per source SHA in this profile.
Continue with the existing risk-based regression and required gates.
Before authoring, check the remote preview action's current capability and
confirm that its PR and authorization requirements can be met. For a
remote isolated preview, verify an authorized PR and its required CI for
the exact SHA, then use the existing verified patient PR preview action.
The HTML-only Admin preview uses its separate verified PR workflow.
Keep `NOT_RUN` for phases without evidence.

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
