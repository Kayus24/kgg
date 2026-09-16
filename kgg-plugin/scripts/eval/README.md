# KGG Plugin Candidate evaluation harness

The candidate is evaluated against the immutable source map, the three
read-only parity fixtures (`current_state`, `ticket_plan`, `safe_canary`), and
the UI-Lab contracts before any surface comparison. The release-pipeline
battery is the current executable harness; this directory reserves the
plugin-local entry point for the later A/B runner. A comparison must report
Fresh Main, source hashes, tool availability, actor/lease results, Quick-Flow
evidence, retries, and the five migration gates. It must not silently
substitute a missing MCP, hook, or browser capability with unrestricted shell
control.
