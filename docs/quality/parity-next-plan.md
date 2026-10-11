# Bounded continuation – automated acceptance evidence

Base: main 3b8aac1 (per-set pain #304 already merged); existing automation PR #303.
Scope: tests and review tooling only. Do not change app sources or prior number-entry semantics.

1. Merge fresh main into the existing PR branch, preserving PAT-PAIN-004 and its regression. No duplicate pain feature or framework.
2. Add independent expected-result assertions to the existing Legacy/React recorder. Capture visible controls, center transfer, left/right isolation, no-load seconds, and persistence after reload. Pair equality alone is not a correctness oracle.
3. Keep normal-motion videos, include checkpoint timestamps and a short per-frame pad-open/scroll observation of the kg/Wdh switch. Static screenshot normalization remains separate.
4. Add Node built-in tests for Gemini handoff (no real network), then require explicit upload approval, validate missing credentials/schema errors, request 5 video frames/second and bind the review to the source report.
5. Reuse Chromium and WebKit with bounded runs and durable logs. Update report gallery/coverage; no claim of complete app coverage, no Gemini PASS from a dry run.
6. Commit/push one verified batch to #303, report exact CI status without endless polling. No merge or paid external call in this task.

Real Gemini call remains blocked until a valid key and explicit approved upload configuration are provided in GitHub's protected environment. Never paste secrets into chat.
