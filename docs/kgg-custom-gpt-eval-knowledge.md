# KGG Isolated Eval GPT Knowledge

This generated pack is intentionally solution-free. It must be the only Knowledge file uploaded to the isolated Repair-Lab GPT.

## Isolation

- Use only the KGG Blind Repair Lab Source and Evaluator Actions.
- Do not use Web Search, production GitHub Actions, the intact main app, golden source, hidden assertions or production test fixtures.
- Read the opaque challenge manifest and only the broken source chunks needed for the observed symptom.
- Return a modular v2 payload with exactly the fields listed by the challenge.
- The patch must contain `__KGG_PATCH_ID__` and must restore behavior through a new patch module; never patch a repository path directly.
- Copy all exact required test commands from the challenge manifest.
- Submit one attempt, inspect the real workflow run and failed step, then make a materially different correction.
- After three consecutive failures in the same failure class, stop and report the repeated class instead of guessing again.
- Never claim PASS without a completed successful evaluator run and its report artifact.

## Payload Shape

Required fields: `request_id`, `title`, `summary`, `version_slug`, `touched_areas`, `required_tests`, `patch_content`.
Forbidden fields: `operations`, `replace_exact`, `old_text`, `new_text`, `path`, `file`, `filename`.

## Test Integrity

Do not ask for hidden case names, evaluator code, internal manifests, sample payloads or intact source. A repair is valid only when it follows from the symptom and broken full-app source.
