---
name: kgg-project-status
description: Keep substantive KGG/Vibe coding runs enrolled in project-status telemetry and correlate ChatGPT sessions without guessing conversation URLs.
---

# KGG project status

Use this skill for substantive multi-step coding work that belongs to a known
KGG/Vibe project.

## Project identity

Use a `project_id` only when it is explicit in the canonical project/status
documents or an established project mapping. Do not reinterpret a UI-Lab Flow
`project`, an arbitrary cwd, a ticket number, or a ChatGPT session ID as a
telemetry `project_id`.

## START / RESUME

At the first meaningful coding step, call `project_status_checkpoint` with:

- stable `project_id`;
- human-readable `project_name`;
- `state=running`;
- a short current `step`;
- canonical HTTPS `source` when known.

The tool prepares an intent only; it does not write GitHub. Apply the returned
`status_issue` through the connected GitHub app against
`Kayus24/project-status-telemetry`:

1. inspect open Issues and match only `schema: project-status/v1` plus the exact
   `project_id`;
2. zero matches: create the returned title/body;
3. exactly one match: update that same Issue only when the body/title changed;
4. more than one match: fail closed, report the duplicate Issue numbers, and do
   not guess which one to close.

Never claim that enrollment happened until the GitHub write actually succeeds.

## CHECKPOINT / WAITING / BLOCKED / PAUSED / FAILED

Use `project_status_checkpoint` only on meaningful state or step changes, not
every tool call or heartbeat. Apply the returned status intent using the same
zero/one/many matching rule.

## COMPLETE

Call `project_status_checkpoint` with `state=complete`. Apply the final body to
the one matching active status Issue, then close that Issue as completed. Do not
close a run merely because a chat or Codex session ended.

## ChatGPT route correlation

The MCP host may provide `_meta["openai/session"]`. The checkpoint tool treats
it only as an opaque `session_ref`.

When the returned `chatgpt_route.publish` is true, upsert one separate route
Issue matched by:

- `schema: project-route/v1`;
- exact `project_id`;
- `surface: chatgpt`.

Use the returned deterministic route title/body. A `correlation_only` route is
never a clickable ChatGPT URL. Never transform, concatenate, decode, or guess a
`session_ref` into `chatgpt.com/c/...`.

A verified `open_url` belongs to the separate route-verification gate and may
only be published after positive verification.

## Safety

Do not place prompts, responses, transcripts, patient data, credentials,
authorization headers, tokens, or unrelated ChatGPT metadata in status or route
Issues. If the GitHub app or session metadata is unavailable, preserve the
coding work and report the missing telemetry/route step honestly; do not invent
success.
