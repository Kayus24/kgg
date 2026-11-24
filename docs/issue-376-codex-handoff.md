# Issue #376 — local Codex handoff

## Resume 2026-11-20: BLOCKED — Critical incomplete / Plugin-E2E NOT_RUN

Only writer in `C:\KI-Arbeit\kgg-ui-lab-issue-376` on
`DESKTOP-69P6967`; branch `codex/ui-lab-issue-376`, base/HEAD
`e3ec328ef7ae78c753044dbcd20580e4032e889f`. Fresh read-only GitHub inspection
confirmed the same SHA on main, no published #376 branch/PR, and no candidate
CI result. No overlapping published writer was found for the bridge files.
Chrome ownership by #371 could not be established; browser stress was deferred.
Focused checks used isolated headless Chromium contexts, without manipulating a
personal Chrome window/profile. No external write or activation was attempted.

All ten inherited dirty/untracked files were saved before editing in
`tmp/issue376/resume-20261120/initial-worktree.zip`, with `initial.patch` and
`initial-state.json`. The inherited bridge repairs, source-hash references,
native fixture/tests and actual-app exporter remain byte-identical to that
snapshot. The inherited failure test was extended; this handoff was updated.

### Reproduced React NumPad gate failure and minimal worker fix

The unchanged header test failed again with `Unexpected token '<'`.
A bounded diagnostic copy of that existing test recorded only the known QR
script request (maximum eight records; no raw response HTML):

- URL: `https://cdn.jsdelivr.net/npm/qrcode-generator@1.4.4/qrcode.js`.
- Browser network failure: `net::ERR_NETWORK_ACCESS_DENIED`, including the
  worker's fetch.
- Script response: 200, `text/html; charset=utf-8`,
  `fromServiceWorker: true`.
- Response SHA-256:
  `679f056f405db8fc1ab627b2d6a87cfe846de899523b00bc7bddaf906b50f77d`, exactly
  the unchanged actual `index.html`.
- The generic fetch catch in `service-worker.js` returns cached `./index.html`
  for that failed script request; parsing the HTML as JavaScript produces `<`.

Evidence: `ui-request-evidence.log` and `ui-request-diagnostic.cjs` in the resume
directory. Two preliminary diagnostic invocations used an incorrect document
root and are invalid diagnostic attempts, not additional product failures.
The historical failure's upstream network cause remains UNKNOWN; the denial
above was observed in this run only.

Two fix approaches were used, with no further recovery attempts planned:

1. Temporarily isolate the header context with `serviceWorkers: "block"`,
   matching its existing Grid context. This passed, but the required gates then
   reached the independent Per-Set-Pain browser test, which explicitly needs a
   controlling worker and failed with the same `<`. Its bounded diagnostic copy
   proved the same denied CDN fetch, HTML Content-Type, worker response and
   index-body hash (`pain-request-evidence.log`). The isolation change was
   **reverted**; the header test has no Git diff from HEAD (worktree line
   endings differ from the blob).
2. Fix only the now-proven worker fallback: the generic catch returns the HTML
   shell only for `request.mode === "navigate"`; failed uncached resources
   return `Response.error()`. Existing dedicated index, module, recovery,
   manifest and cached-resource branches are unchanged. No plan/UI/QR-format
   logic was changed. This is a local candidate, not an app release.

`test_kgg_service_worker_script_fallback.js` exercises the actual worker in a
Node VM: four failed resource destinations (script/style/image/fetch) cannot
receive HTML; offline document navigation still receives the exact cached
index; successful fetch returns JavaScript; absent cache does not invent HTML.
Seven cases pass after the fix. The original worker's three-case reproduction
is retained in `sw-fallback-final.log`; the fixed regression is
`sw-fallback-fixed.log`. The same seven-case regression fails against an
isolated copy of the HEAD worker (`sw-original-regression-red.log`, exit 1),
proving that the control detects the original defect. This adds no browser
pipeline or dependency. Its
injected network failure is explicitly distinguished from real-browser evidence
and historical unknowns.

### Current focused evidence

All paths below are under `tmp/issue376/resume-20261120/`.
Set `KGG_REAL_BROWSER=1` for the three browser suites and native exporter.

| Exact command | Result | Log |
|---|---|---|
| `python -m unittest discover -s release-pipeline -p test_kgg_real_browser_bridge.py -v` | PASS 30/30 | `bridge-full.log` |
| `python -m unittest discover -s release-pipeline -p test_kgg_width_sweep.py -v` | PASS 8/8 | `width-full.log` |
| `python -m unittest discover -s release-pipeline -p test_kgg_visual_failure_evidence.py -v` | PASS 4/4 | `failure-final.log` |
| `python -m unittest discover -s release-pipeline -p test_kgg_native_visual_states.py -v` | PASS 2/2 | `native-state.log` |
| `python -m unittest discover -s release-pipeline -p test_kgg_plugin_candidate.py -v` | PASS 21/21 | `candidate-final.log` |
| `node release-pipeline/kgg_patient_react_numpad_header_playwright.js` | RED original worker; PASS original test after worker fix | `react-header-unchanged.log`, `react-header-worker-active.log` |
| `node release-pipeline/kgg_patient_per_set_pain_playwright.js` | PASS Legacy + React with active worker | `per-set-pain-worker-active.log` |
| `node release-pipeline/test_kgg_service_worker_script_fallback.js` | PASS 7/7; original worker RED | `sw-fallback-fixed.log`, `sw-original-regression-red.log` |
| `python release-pipeline/kgg_ui_lab_app_evidence.py --output tmp/issue376/resume-20261120/native-apps-fixed` | LOCAL_CAPTURE_VERIFIED 4/4 on final worker candidate | `native-apps-fixed.log`, `native-apps-fixed/manifest.json` |

The extended negative tests distinguish a real child-process exit
(`real_browser_process_failed`) from malformed JSON
(`real_browser_session_response_invalid`) and a genuinely waiting host
(`real_browser_timeout`). Both timeout and process failure retain exact bounded
FAIL evidence for initialize/observe/act/verify (eight subcases), close the
session, expose no screenshot/URL/form content and deny unauthorized access.
The denied actor cannot launch a host or add evidence. Native tests cover
hidden/open modals and the generic-policy negative control.

All eight final-candidate native PNGs were checked for magic, dimensions, SHA and distinct
before/after hashes, then visually inspected. Both widths show the actual
Patient NumPad and Therapist editor after a real click through the existing
Runtime/bridge. Remote exercise media is unavailable in the local sandbox.
These are synthetic local captures, **not installed-plugin E2E acceptance**.
Application HTML hashes are recorded in the manifest and remain unchanged.
The final capture source fingerprint is separately bound in `verification.json`;
`run-source-state.json` records all eleven code/reference file hashes.
`service-worker.js` changed from
`0a2e4f8b272ebb082d44d24ded25ec48ab92147bde7dbd008ca8fe4db2b81388` to
`0ac12dd994277e22bfdbd934f1329eeafcc95c4c80f363c365ec169d46973d06`.

### Required gates and remaining boundary

First required gate attempts both exited 1 at the Per-Set-Pain `<` failure
after the temporarily isolated header passed (`critical.log`,
`ui-stability-first.log`). Following gate checks were NOT_RUN. Final gate
attempt: `cmd /c release-pipeline\run-kgg-tests.cmd --suite ui-stability --level regression`
is **PASS / exit 0**, all 32 selected gate IDs completed
(`ui-stability-fixed.log`, `KGG test battery OK`).
Critical against the worker fix was **INTERRUPTED / incomplete, exit 1**
(`critical-fixed.log`); it is not PASS. It passed the original NumPad and
Per-Set-Pain failures and reached `ticket-037-real-plan-browser-critical`.
That existing runner function unconditionally executed
`npm --prefix release-pipeline ci --ignore-scripts`, reinstalling four pinned
local packages despite `KGG_SKIP_PLAYWRIGHT_INSTALL=1`. I missed this separate
preparation branch before starting the required command: it violated the user's
no-install constraint. No browser download occurred. The later
`run_patient_qr_v81_smoke` would unconditionally run npm ci again, so the gate
was interrupted with Ctrl-C to prevent a second install. No preparation flag,
fake npm, alternate runner or approval bypass was used to manufacture a PASS.
Thirty-nine Critical gate IDs completed before Ticket-037; the remaining ten
are NOT_RUN and the in-flight Ticket-037 result is UNKNOWN. Package
manifests/lockfiles and all candidate code hashes are
unchanged. No attempt was made to undo node_modules by destructive deletion.

Open local gate requirement: an existing supported installation-free Critical
invocation or separately scoped runner preparation fix is needed. This run
does not expand beyond the two fix approaches to alter unrelated runner logic.

Final hook guard, JS/Python syntax and `git diff --check` have passed
(`syntax-hook-diff-final.log`: four JS files, five Python files). The worktree-local
`tmp/issue376/git-safety.config` is selected only in the test process via
`GIT_CONFIG_GLOBAL`; no shared/global Git configuration was edited.
`KGG_SKIP_PLAYWRIGHT_INSTALL=1` prevents the Chromium download, but does **not**
prevent the unconditional npm preparation described above.

Plugin-E2E is **NOT_RUN / BLOCKED**: this candidate is not active in the
installed plugin. Full acceptance still needs separately authorized candidate
activation, an approved plugin-reachable synthetic native fixture and actual
plugin-returned screenshots/state evidence. Current instructions prohibit that
activation, publishing and plugin unlock. The historical external rejection
below is retained as history and was not retried or bypassed.

No reset, stash, commit, push, PR/Actions write, main edit, APK,
deployment, host-allowlist or plugin-access change was made. The unintended
local npm reinstall is explicitly recorded above. Candidate changes
remain an uncommitted local diff; shared `.git` is not a writable target.

### Saved candidate and evidence

`tmp/issue376/resume-20261120/candidate.patch` contains all twelve tracked and
untracked candidate files against HEAD. `candidate-worktree.zip` preserves their
exact bytes. `final-state.json` records file/archive hashes and preservation of
the eight unchanged inherited files; `verification.json` records exact checks,
gate boundaries and the final eight PNG hashes. The generated Chromium
`debug.log` was preserved as `chromium-debug.log` in that evidence directory.
No test or capture result is promoted to installed-plugin acceptance.

## Historical verification — 2026-11-18 (superseded locally above)

Verified 2026-11-18 on **DESKTOP-69P6967**. Worktree:
`C:\KI-Arbeit\kgg-ui-lab-issue-376`, branch `codex/ui-lab-issue-376`,
HEAD/base `e3ec328ef7ae78c753044dbcd20580e4032e889f`.
The candidate is **uncommitted and local**, with no push, merge, deployment,
plugin reconnect/reinstall, live runtime/tunnel restart or production change.
The original ChatGPT conversation has **not** been notified directly.
The authorized GitHub issue-comment attempt was also rejected before execution:
`MCP tool call requires approval, but approval policy is never`. No comment was
posted by this run, and no alternate write route was used. The prepared comment
is saved locally as `tmp/issue376/github-comment.txt` for manual handoff.

## Root cause and limits

The historical `real_browser_timeout` root cause is **UNKNOWN**. Neither issue
#376 nor the reachable session evidence supplied the original failing request,
browser stderr or artifacts. Do not attribute that incident to a missing module,
network delay or any other unproven cause.

Three independent defects were reproduced locally and minimally patched:

1. A persistent child host exiting without a JSON response left `_send` waiting
   until its deadline and reported `real_browser_timeout`. An EOF sentinel now
   wakes the waiter and reports `real_browser_process_failed`. A real child exit
   reproduced RED before the change and GREEN after it. No timeout was raised.
2. Browser initialization/observe/act/verify errors left no retrievable failure
   evidence. These phases now retain a bounded FAIL record with request/source,
   phase and error class; no screenshot is fabricated and no URL, page text,
   form values or browser storage is copied. Four injected timeout phases prove
   this evidence handoff; actor rejection still prevents launch/evidence access.
3. Native Patient/Therapist pages have no synthetic `data-kgg-state` marker.
   Their real PNGs changed after a real click, but the old state remained
   `lang-de`/`unknown`; the existing Runtime rejected the expected native state
   with `visual_expected_state_not_reached`. KGG-only, fixed DOM/visibility
   checks now recognize `patient-plan -> patient-numpad` and
   `therapist-plan -> therapist-editor`. Generic policy remains `unknown`.

These are proven local defects, **not proof of the historical timeout cause**.
The existing `browser_host.js`, persistent host, Python bridge and Runtime are
reused; no second browser bridge or access-gate change was introduced.

## Installed ChatGPT plugin result

The actual `KGG UI Lab Private` connector returned Fresh Main and successfully
created `issue376-external-baseline-01`, actor `codex`, runner version `1.4.0`,
phone viewport 390x844, browser/capture/visual_loop/width_sweep capabilities.
`observe_visual_state`, request `issue376-observe-01`, was rejected **before
browser execution**:

> MCP tool call requires approval, but approval policy is never

Read-only reconciliation returned `ready`, event_count 0 and evidence `[]`.
This is **BLOCKED / NOT_RUN**, not a reproduced browser timeout. No alternate
connector, shell route or retry was used to bypass that approval boundary.
Record: `tmp/issue376/external-baseline.json`.

The stable installed runtime remains `ACTIVE_VERIFIED`, release
`0.5.0-20261026`, server `1.4.0`, active SHA
`00c634132b3a9988c0fb60a6429f11074c525a3176f6bd21b62b43a0ea031552`.
Its verified server SHA-256 is
`90f91614970a3b227d334a2964efb44dd21af541ed9d4176146890159306bec0`.
This candidate is **not active in the installed plugin**. Activating it requires
separate user approval. An approved plugin-reachable synthetic native-app fixture
is also needed for external native-app acceptance; the local ephemeral fixture
server was shut down after testing.

## Changed files

- `kgg-plugin/mcp/real_browser.py`: persistent-host EOF diagnosis.
- `kgg-plugin/mcp/server.py`: sanitized failure evidence at four browser phases.
- `kgg-plugin/mcp/browser_session_host.js`: fixed native KGG visual states.
- `kgg-plugin/references/architecture/source-hashes.json` and
  `kgg-plugin/references/source-map.md`: matching candidate source hashes;
  installed/live hashes were not changed.
- `release-pipeline/test_kgg_visual_failure_evidence.py`: 3 diagnostic/safety tests.
- `release-pipeline/test_kgg_native_visual_states.py` and
  `release-pipeline/kgg_ui_lab_native_state_fixture.html`: native visibility and
  generic-policy negative controls.
- `release-pipeline/kgg_ui_lab_app_evidence.py`: reproducible native-app evidence
  using the existing Runtime/bridge and transient synthetic storage/setup.
- This handoff document. No Patient or Therapist application bytes were edited.

## Tests and evidence

| Check | Result | Evidence under `tmp/issue376/` |
|---|---|---|
| Existing real-browser bridge/visual_loop, 30 tests | PASS | `bridge-final.log`, 179.052s |
| Existing width_sweep, 8 tests | PASS | `width-sweep.log` |
| EOF/four-phase failure evidence/denied actor, 3 tests | PASS | `diagnostic-green.log`; RED in `diagnostic-red-exit.log` |
| Native modal visibility and generic policy, 2 tests | PASS | `native-state-green.log` |
| Candidate parity/hash contract, 21 tests | PASS | `candidate-green.log` |
| Native actual apps, 4 cases / 8 PNGs | LOCAL PASS | `native-final.log`, `native-apps-final/manifest.json` |
| `run-kgg-tests.cmd --level critical` | FAIL | `critical-final.log`, existing React NumPad test |
| `run-kgg-tests.cmd --suite ui-stability --level regression` | FAIL | `ui-stability-final.log`, same existing test |
| Knowledge pack freshness / resource audit | PASS / TARGET_PASS | Local checks; no live synchronization claim |
| Hook guard `--check`, candidate hash checks | PASS | Process-local safe.directory config; shared git config unchanged |
| Installed ChatGPT observe/click/PNG retrieval/native matrix | NOT_RUN / BLOCKED | Approval denial above |
| GitHub CI / physical device / production-live app acceptance | UNKNOWN / NOT_RUN / NOT_RUN | No claim of coverage |

Width sweep covers no opt-in, denied actor/lease/bounds, timeout with later cases
NOT_RUN, missing PNG, wrong dimensions, shared deadline and fractional DPR.
The native-state RED was `visual_expected_state_not_reached`
(`native-state-red.log`). All eight final PNGs were visually inspected.

The required broad tests stop at `kgg_patient_react_numpad_header_playwright.js`
line 351: `SyntaxError: Unexpected token '<'`. A bounded diagnostic copy of that
unchanged test (`ui-diagnostic.log`) observed the external
`https://cdn.jsdelivr.net/npm/qrcode-generator@1.4.4/qrcode.js` response containing
Patient HTML with status 200. The unchanged Service Worker generic fetch failure
fallback (`service-worker.js:43`) can return cached `./index.html` for this script.
The fallback explains the observed parse error; the upstream fetch failure reason
was not established. This path uses none of the changed bridge modules.
No Service Worker/QR/application fix was made under this issue. The broad gates
remain FAIL; checks after the stopping test are NOT_RUN.

## Local native-app PNGs

These are real **headless Playwright Chromium**, not a mock or screenshot from an
Android device: provisioned Playwright 1.62.1, Chromium 151.0.7922.34,
`chromium-1234/chrome-win64/chrome.exe`. DPR 1. Each post-click image differs from
its initial image and passed PNG magic, dimensions and SHA-256 validation via the
existing Runtime. Synthetic plans only. Patient media placeholders indicate that
remote exercise-media loading was not validated.

Files reside in `tmp/issue376/native-apps-final/`. These local PNGs do **not**
establish ChatGPT transport retrievability or installed-plugin PASS.

| File | SHA-256 |
|---|---|
| patient-390x844-initial.png | `2421dbae663d1b73b2d12a10f682575c24598e5e30e0b4f21f122032df2d707f` |
| patient-390x844-post-click.png | `bb9bc71de0db81ec98d6605678af70e74344008a3ed0d4c0f56703916437620a` |
| patient-820x1180-initial.png | `e4596cd96740116df7a6446ca814846bf720cd3bf23129f80d3e839e88930fff` |
| patient-820x1180-post-click.png | `426e3864ceb691a5dcfa1dffa4993f172d09eb5affa921289d0a1bd64235426e` |
| therapist-390x844-initial.png | `0c45f2f1863ad85c1f73892b362dfca1925d8e4a7dd02cf1eaa4d377c83c0ba6` |
| therapist-390x844-post-click.png | `8de295ae3057760d9896f9a02db3a4450725f6262945dcf987e8e1fd1f622aeb` |
| therapist-820x1180-initial.png | `12f74282ab071ff2e3a2fe145d121d8841ba8a68ad8b78ed504a0f94c692ee01` |
| therapist-820x1180-post-click.png | `66907c213c1bc705868fc430d5b8cfa011c4b469d772a2ef036aa7bad8f4b8e8` |

Source HEAD is the base SHA above. Application SHA-256 values:

- `index.html`: `679f056f405db8fc1ab627b2d6a87cfe846de899523b00bc7bddaf906b50f77d`
- `kgg-update/index.html`: `46a384ce5933d9e4ad002ed8d168465800a88bdf273cbf46fcf7e6176befb122`

Therapist source is the current worktree candidate v137, not automatically the
published Admin/colleague APK. No production-live acceptance is claimed.

## Reproduce locally

Use the existing provisioned Node, Python, Playwright and cached Chromium; do not
restart or modify the installed host. From this worktree in PowerShell:

```powershell
$env:KGG_REAL_BROWSER = '1'
python -m unittest discover -s release-pipeline -p test_kgg_visual_failure_evidence.py -v
python -m unittest discover -s release-pipeline -p test_kgg_native_visual_states.py -v
python -m unittest discover -s release-pipeline -p test_kgg_real_browser_bridge.py -v
python -m unittest discover -s release-pipeline -p test_kgg_width_sweep.py -v
python -m unittest discover -s release-pipeline -p 'test_kgg_plugin_candidate*.py' -v
python release-pipeline/kgg_ui_lab_app_evidence.py --output tmp/issue376/native-retest
```

The final command creates a loopback-only transient HTTP server, serves the
unchanged actual applications with an in-memory synthetic setup script, obtains
coordinates from the existing safe exercise/editor controls, observes, clicks via
the existing Runtime, verifies native modal visibility and exports returned PNG
bytes. It closes the browser sessions and HTTP server. It does not publish an
external fixture or modify the installed plugin. No synthetic state markers are
injected into the actual applications.

For required broad tests the existing hook guard must pass. A process-local
`GIT_CONFIG_GLOBAL=tmp/issue376/git-safety.config` provided the worktree's
safe.directory entry without altering shared git configuration. Existing
`KGG_SKIP_PLAYWRIGHT_INSTALL=1` avoids a redundant browser download when running
the UI suite. The first UI attempt was interrupted during that redundant install;
the final completed attempts and their FAIL results are recorded above.

## Exact ChatGPT re-test sequence

Use the installed **KGG UI Lab Private** tool surface in the original ChatGPT
conversation, in an environment that can authorize its browser action. Do not
reconnect, reinstall or restart the live host as part of the test. If the same
approval rejection occurs, stop, read status/evidence once and report BLOCKED.

1. `get_current_state({"actor":"codex"})`; use its actual Fresh Main SHA as S.
2. `start_ui_session({"session": SESSION})`, with this full session template;
   replace NOW/EXPIRY with current UTC and +30 minutes, S with that SHA, and use
   fresh unique session/request IDs (letters, digits and hyphens):

```json
{"schema":"kgg-ui-lab/session/v1","session_id":"issue376-chatgpt-retest-01","request_id":"issue376-chatgpt-start-01","status":"created","active_actor":"codex","lease":{"owner":"codex","issued_at":"NOW","expires_at":"EXPIRY"},"runner":{"runner_id":"issue376-chatgpt","version":"1.4.0","browser_revision":"host-selected-unverified","capabilities":["browser","capture","visual_loop","width_sweep"]},"app":{"name":"admin","url":"https://kayus24.github.io/kgg/release-pipeline/kgg_ui_lab_real_fixture.html","main_sha":"S","preview_sha":null},"device_profile":"custom","viewport":{"width":390,"height":844,"device_scale_factor":1},"quick_flow":{"name":"screenshot-evidence","version":"1.0.0"},"timeout":{"timeout_ms":30000,"cleanup_on_cancel":true},"artifacts":[]}
```

3. `observe_visual_state({"request": R})`, where R is:

```json
{"schema":"kgg-ui-lab/request/v1","session_id":"issue376-chatgpt-retest-01","request_id":"issue376-chatgpt-observe-01","actor":"codex","operation":"observe_visual_state","main_sha":"S","payload_sha256":"aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"}
```

To re-test the original `capture_screenshot` entry point as well, first create a
separate fresh session with the same template and a new session/request ID, then
call `capture_screenshot({"request": R})` with that session ID, a fresh request ID
and `operation:"capture_screenshot"`. Require real-browser PNG content and verify
its SHA/dimensions. Reconcile once and stop on an approval denial; do not proceed
to the dependent visual-loop calls in that case.

4. Retrieve/view the returned **PNG content**, verify its hash, dimensions and
   `real_browser` mode. A `memory://` reference alone is not retrievable evidence.
   With O = the actual returned observation ID, call `execute_visual_action` with
   request R using a fresh `request_id`, `operation:"execute_visual_action"`, and:

```json
{"operation":"click","label":"tablet-splitter-control","observation_id":"O","expected_state_after":"scale-drag-state"}
```

5. Retrieve/view the second returned PNG and verify distinct hashes/states, then
   `get_test_evidence({"actor":"codex","session_id":"issue376-chatgpt-retest-01"})`
   and `get_session_status` with those same two arguments.
6. `run_width_sweep({"actor":"codex","session_id":"issue376-chatgpt-retest-01","viewports":["390x844","820x1180"]})`;
   retrieve the actual PNG content and verify dimensions and hashes.

This exact existing-fixture sequence proves **transport only**, not native app
acceptance. After separately approved candidate activation and an approved,
plugin-reachable synthetic fixture for each actual app, repeat steps 1–5 for
Patient and Therapist at 390x844 and 820x1180. Set `app.name` to `patient`/`admin`
and use the approved native fixture URL; choose click coordinates from each
actual returned screenshot, expecting `patient-numpad`/`therapist-editor`.
Do not invent a native fixture URL or reuse local-only PNGs as external evidence.
Only four real native before/after pairs returned through the installed ChatGPT
plugin can satisfy issue #376's full acceptance criterion.
