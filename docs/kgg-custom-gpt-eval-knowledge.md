# KGG Isolated Eval GPT Knowledge

This generated pack is intentionally solution-free. It must be the only Knowledge file uploaded to the isolated Repair-Lab GPT.

## Isolation

- Use only the KGG Blind Repair Lab Source and Evaluator Actions.
- Do not use Web Search, production GitHub Actions, the intact main app, golden source, hidden assertions or production test fixtures.
- Read the opaque challenge manifest and only the broken source chunks needed for the observed symptom.
- Return a modular v2 payload with exactly the fields listed by the challenge.
- The patch must contain `__KGG_PATCH_ID__` and must restore behavior through a new patch module; never patch a repository path directly.
- `patch_content` must never contain generated-output markers such as `<!-- KGG PATCH START` or `<!-- KGG PATCH END`; the gate owns module wrapping.
- Copy all exact required test commands from the challenge manifest.
- Submit exactly one attempt, wait for its completed workflow run, then load its sanitized `outcome.json` through `getKggRepairResult` before considering another attempt.
- Never dispatch a follow-up while the prior run is queued or in progress, and never infer a failure reason from a missing artifact.
- After a failed outcome, use only its safe error class and feedback to make a materially different correction.
- After three consecutive failures in the same failure class, stop and report the repeated class instead of guessing again.
- Never claim PASS without a completed successful evaluator run and its report artifact.

## Natural UI Mode

- Treat spelling mistakes, missing punctuation, colloquial German and screenshot labels such as `1` or `2` as normal input.
- Before patching, structure observed behavior, desired behavior, target elements and interaction boundary.
- For CSS layout repairs, inspect the final cascade and patch the same container whose computed display, grid columns or geometry is wrong. Do not move parent layout properties onto guessed child containers.
- After a UI-logic FAIL, use the reported computed element state to change the responsible selector/property pair materially; changing only nearby descendants is not a valid retry.
- Ask exactly one short clarification only when two materially different repairs remain possible. Otherwise continue without a question.
- If the user says one of two marked controls is broken and two matching source defects remain possible, ask which single control is meant before any Action. Never broaden the patch to both controls.
- After that one answer, patch only the selected target and record clarification_count=1 plus the exact question. Do not ask a second question.
- For a natural challenge, send `challenge_id`, `interpretation` and payload metadata through `submission_json`, but omit `payload.patch_content` there.
- Send raw `patch_content` through the dedicated Action input. Never JSON-encode or double-escape patch code inside `submission_json`.
- `patch_content` is a complete executable HTML fragment: wrap CSS in `<style>` and JavaScript in `<script>`. Bare CSS or JavaScript is invalid.
- `interpretation.confidence` is exactly `low`, `medium` or `high`, never a number. `clarification_count` is integer `0` or `1`; its question is empty when the count is `0`.
- Use `getKggNaturalUiResult` after the completed workflow. Never infer canonical intent, clarification policy or hidden assertions.
- Natural UI public data never contains canonical intent, golden source, evaluator assertions, clarification answer or sample submission.

## Payload Shape

Required fields: `request_id`, `title`, `summary`, `version_slug`, `touched_areas`, `required_tests`, `patch_content`.
`patch_content` must be an executable HTML fragment with `<style>` and/or `<script>` wrappers.
Forbidden fields: `operations`, `replace_exact`, `old_text`, `new_text`, `path`, `file`, `filename`.
Forbidden patch tokens: `<!-- KGG PATCH START`, `<!-- KGG PATCH END`, `kgg-source-truth` and manually generated module wrappers.

## Test Integrity

Do not ask for hidden case names, canonical intent, evaluator code, internal manifests, sample payloads or intact source. A repair is valid only when it follows from the user's natural request, marked screenshot and broken full-app source.
