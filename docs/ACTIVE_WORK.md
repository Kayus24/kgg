# KGG – Active Work / Cross-Chat Coordination

> **Purpose:** Lightweight coordination index for parallel ChatGPT/Codex work. Not a second source of truth for code, deployment, tests or durable product decisions.
>
> **Status:** Coordination protocol proposed on 2026-10-08. Entries below are *discovered references*, not active locks or proof that a chat is still running.

## Authoritative sources (read in this order)
1. Fresh `main`, `AGENTS.md`, `TOOL_ROUTING.md`, `APP_BOUNDARIES.md`.
2. Actual GitHub branch/PR head, changed files, checks and relevant source/manifests.
3. `Kayus24/kgg-project-memory` for durable decisions/rationale only; follow its Memory Gate.
4. Google Drive for longer-running work plans, concept documents and evidence, **not** live code state.

## Working protocol for each chat/agent
1. **Start/resume:** Read this index and the relevant repo rules; refresh actual GitHub state. Never treat this file, ChatGPT memory or a prior chat statement as evidence of live progress.
2. **Claim scope:** Record workstream, branch/PR, intended files/areas, last *verified* checkpoint (with UTC time and SHA), next action, and possible overlap. Use your own branch/worktree. No exclusive lock is implied.
3. **Before editing shared paths:** Re-check latest GitHub changes and other workstreams; if overlap is real, coordinate sequencing or use separate changes and reconcile. Never overwrite another chat's uncommitted work.
4. **After a meaningful milestone:** Update only your workstream entry in a small docs-only PR (or in the PR body/linked issue to avoid competing writes to this file). Include exact evidence links and `verified_at`. Prefer PR/issue updates for frequent status changes; this index should stay short.
5. **On interruption/hang:** Record last GREEN, action in flight, outcome **UNKNOWN** until verified, and safe re-entry. Do not blindly repeat writes, merges, or deployments.
6. **Before merge:** Refresh branch and CI status; follow all `AGENTS.md` gates, preserve patient/therapist boundaries and require explicit approval for protected changes. A documentation note is never a test pass.
7. **Freshness:** Entries without fresh evidence are `STALE/UNKNOWN`, not `DONE`. Do not assume that another chat receives push notifications; each chat must re-read when resuming.

## Workstreams / discovery snapshot

| Workstream | Reference | Known at 2026-10-08 | Files/scope | Next verification |
| --- | --- | --- | --- | --- |
| React patient controller adapter | `patient/react-controller-adapter-20261007` | Branch name discovered; **activity/PR/checks UNKNOWN** | Patient React migration; exact changed files **UNKNOWN** | Inspect branch diff, PR, tests and ownership before touching patient UI |
| React patient island skeleton | `patient/react-island-skeleton-20261007` | Branch name discovered; **activity/PR/checks UNKNOWN** | Patient React migration; exact changed files **UNKNOWN** | Inspect branch diff and overlap with controller adapter |
| Patient feature protection | [Patient Feature & Regression Manifest](https://docs.google.com/document/d/17AA3z1oGFIxdywK52yEkUlvrDPIMoH9INlP2X_Xd-oE/edit) | Documentation gap identified; **implementation/test status UNKNOWN** | Optional per-exercise setting for per-set pain recording, its UI/state and regression coverage | Verify original setting and pre/post UI behavior; add feature contract + test on separate PR |
| Cross-chat coordination | `docs/cross-chat-coordination-20261008` | Documentation-only coordination change | This file only | Review PR, then adopt protocol in other chats |

## Product regression note: optional per-set pain
The patient app historically allowed enabling **pain recording separately for each set** through an option in an exercise submenu. This is a user-reported pre-migration behavior and must be verified against the relevant working baseline. Do not mistake general pain-scale smoke tests for coverage of this optional mode. React/UI migrations must preserve the setting's discoverability, enabled/disabled behavior, independent set values and persistence, subject to verified product contracts. **No claim of a passing regression test is made here.**

## Handoff template (copy into a PR or issue update)
- Workstream / responsible chat:
- Branch / PR:
- Intended or changed paths:
- Base SHA / head SHA:
- Last verified GREEN (UTC, evidence link):
- In-flight action / outcome (PASS, FAIL, UNKNOWN):
- Risks, overlapping workstreams and blockers:
- Next safe step:
- Test-app/preview link (when UI changes):
