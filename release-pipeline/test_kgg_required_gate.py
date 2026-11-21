#!/usr/bin/env python3
"""Exercise the real CI Bash contracts without browsers, Git writes or YAML deps."""

from __future__ import annotations

import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import tempfile
import textwrap
import unittest


ROOT = Path(__file__).resolve().parents[1]
REQUIRED = ROOT / ".github/workflows/kgg-required-gate.yml"
PARITY = ROOT / ".github/workflows/kgg-patient-ui-parity.yml"
SHA = "a" * 40
RUNTIME_IDENTITY = "kgg-update/src/runtime/fixture-identity.html"


def block(text: str, heading: str) -> str:
    """Read one indentation-delimited block; unsupported YAML fails explicitly."""
    lines = text.splitlines()
    matches = [i for i, line in enumerate(lines) if line == heading]
    if len(matches) != 1:
        raise AssertionError(f"Expected exactly one YAML heading: {heading!r}")
    start = matches[0]
    indent = len(heading) - len(heading.lstrip())
    end = start + 1
    while end < len(lines):
        line = lines[end]
        if line.strip() and len(line) - len(line.lstrip()) <= indent:
            break
        end += 1
    return "\n".join(lines[start:end]) + "\n"


def step(text: str, name: str) -> str:
    return block(text, f"      - name: {name}")


def script(text: str, name: str) -> str:
    part = step(text, name)
    match = re.search(r"^        run: \|\n((?:          .*\n|\n)+)", part, re.M)
    if match:
        return textwrap.dedent(match.group(1))
    match = re.search(r"^        run: (.+)$", part, re.M)
    if match:
        return match.group(1) + "\n"
    raise AssertionError(f"Missing executable run block in {name!r}")


def run_bash(body: str, directory: Path, **values: str) -> subprocess.CompletedProcess[str]:
    bash = shutil.which("bash")
    if bash is None:
        raise AssertionError("Bash is required, matching the CI shell contract")
    env = dict(os.environ)
    for name in ("BASH_ENV", "ENV"):
        env.pop(name, None)
    env.update(values)
    return subprocess.run(
        [bash, "--noprofile", "--norc", "-e", "-o", "pipefail", "-s"],
        input=body,
        cwd=directory,
        env=env,
        text=True,
        capture_output=True,
        timeout=15,
    )


def outputs(path: Path) -> dict[str, str]:
    return dict(line.split("=", 1) for line in path.read_text().splitlines()) if path.exists() else {}


class ScopeTests(unittest.TestCase):
    def classify(self, paths: list[str]) -> dict[str, str]:
        body = script(REQUIRED.read_text(), "Classify pull request scope")
        body = body.replace("${{ github.base_ref }}", "main")
        self.assertNotIn("${{", body, "New Actions expressions need an explicit fixture binding")
        # Only external input boundaries are replaced. Every classifier/grep runs unchanged.
        boundary = r'''
git() {
  case "$1" in
    fetch) return 0 ;;
    diff) cat "$KGG_SCOPE_FIXTURE" ;;
    *) echo "Unexpected fixture git command: $*" >&2; return 91 ;;
  esac
}
python() {
  if [[ "$*" == "release-pipeline/build_therapist_source.py --print-source-role runtimeIdentity" ]]; then
    printf '%s\n' "$KGG_RUNTIME_IDENTITY"
  else
    echo "Unexpected fixture Python command: $*" >&2; return 92
  fi
}
'''
        with tempfile.TemporaryDirectory(prefix="kgg-gate-scope-") as tmp:
            directory = Path(tmp)
            (directory / "patient-ui").mkdir()
            (directory / "patient-ui/package.json").write_text("{}\n")
            changed = directory / "fixture-paths.txt"
            changed.write_text("".join(path + "\n" for path in paths))
            result = run_bash(
                boundary + body,
                directory,
                RUNNER_TEMP=tmp,
                GITHUB_OUTPUT=str(directory / "outputs"),
                KGG_SCOPE_FIXTURE=str(changed),
                KGG_RUNTIME_IDENTITY=RUNTIME_IDENTITY,
            )
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            return outputs(directory / "outputs")

    def test_import_source_and_own_regression_select_ui_and_acceptance(self) -> None:
        for path in (
            "patient-plan-replace-slot-fix.js",
            "release-pipeline/kgg_patient_import_session_values_playwright.js",
        ):
            with self.subTest(path=path):
                flags = self.classify([path])
                self.assertEqual(flags["ui_or_html"], "true")
                self.assertEqual(flags.get("patient_acceptance_required"), "true")

    def test_patient_runtime_react_and_future_patient_paths_are_conservative(self) -> None:
        for path in (
            "index.html",
            "service-worker.js",
            "patient-future-feature.js",
            "patient-ui/src/FutureWidget.tsx",
            "patient-react-dist/kgg-patient-ui.js",
            "collapse-cards.js",
            "numpad-ui-fix.js",
        ):
            with self.subTest(path=path):
                flags = self.classify([path])
                self.assertEqual(flags["ui_or_html"], "true")
                self.assertEqual(flags.get("patient_acceptance_required"), "true")

    def test_acceptance_inputs_and_test_edits_select_both_engines(self) -> None:
        for path in (
            "release-pipeline/kgg_patient_integrated_acceptance.py",
            "release-pipeline/kgg_patient_full_acceptance_report.test.mjs",
            "release-pipeline/test_kgg_patient_existing_release.py",
            "release-pipeline/patient-integrated-suites.json",
            "release-pipeline/patient-scan-fixtures/new-fixture.json",
            "release-pipeline/kgg_ticket_015_browser_smoke.js",
            "release-pipeline/package-lock.json",
            "release-pipeline/test_kgg_required_gate.py",
            ".github/workflows/kgg-patient-ui-parity.yml",
            ".github/workflows/kgg-required-gate.yml",
            "docs/quality/patient-react-parity.md",
        ):
            with self.subTest(path=path):
                self.assertEqual(self.classify([path]).get("patient_acceptance_required"), "true")

    def test_pwa_only_changes_still_require_acceptance(self) -> None:
        for path in ("manifest-v96.webmanifest", "update-recovery.html", "kgg-icon-192.png"):
            with self.subTest(path=path):
                self.assertEqual(self.classify([path]).get("patient_acceptance_required"), "true")

    def test_unrelated_docs_do_not_select_extra_browsers(self) -> None:
        flags = self.classify(["docs/meeting-notes.md"])
        self.assertEqual(flags["ui_or_html"], "false")
        self.assertEqual(flags.get("patient_acceptance_required"), "false")
        self.assertEqual(flags["patient_react"], "false")

    def test_admin_changes_keep_existing_scope_without_patient_matrix(self) -> None:
        flags = self.classify([RUNTIME_IDENTITY])
        self.assertEqual(flags["admin_camera_qr"], "true")
        self.assertEqual(flags["ui_or_html"], "true")
        self.assertEqual(flags.get("patient_acceptance_required"), "false")

    def test_pipeline_only_and_react_existing_flags_remain(self) -> None:
        self.assertEqual(self.classify(["release-pipeline/other_tool.py"])["pipeline_only"], "true")
        flags = self.classify(["patient-ui/src/FutureWidget.tsx"])
        self.assertEqual(flags["pipeline_only"], "false")
        self.assertEqual(flags["patient_react"], "true")
        self.assertEqual(flags["patient_set_view"], "true")

    def test_drive_sync_source_tests_and_gate_dependencies_select_e2e(self) -> None:
        for path in (
            "kgg-update/index.html",
            "kgg-update/src/runtime/fixture-identity.html",
            "kgg-update/src/runtime/nested/future-runtime.js",
            "kgg-update/src/parts.json",
            "kgg-update/src/patches/custom-bank.html",
            "kgg-update/src/patches/new-library.js",
            "kgg-update/src/patches/drive-sync.html",
            "kgg-update/src/patches/exercise-editor.html",
            "release-pipeline/kgg_drive_sync_e2e.js",
            "release-pipeline/kgg_drive_sync_ui_latency.test.js",
            "release-pipeline/test_kgg_drive_sync_future.py",
            ".github/workflows/kgg-required-gate.yml",
            "release-pipeline/test_kgg_required_gate.py",
            "release-pipeline/package.json",
            "release-pipeline/package-lock.json",
        ):
            with self.subTest(path=path):
                self.assertEqual(self.classify([path]).get("drive_sync"), "true")

    def test_unrelated_paths_do_not_select_extra_drive_sync_run(self) -> None:
        for path in (
            "docs/meeting-notes.md",
            "index.html",
            "patient-ui/src/FutureWidget.tsx",
            "kgg-update/index.html.backup",
            "kgg-update/src/runtime-other/other.js",
            "kgg-update/src/patches/unrelated-layout.html",
            "release-pipeline/other_tool.py",
            "release-pipeline/kgg_test_battery.py",
        ):
            with self.subTest(path=path):
                self.assertEqual(self.classify([path]).get("drive_sync"), "false")


class CompletionTests(unittest.TestCase):
    def complete(self, **changes: str) -> subprocess.CompletedProcess[str]:
        values = {
            "SCOPE_RESULT": "success",
            "CORE_RESULT": "success",
            "BROWSER_REQUIRED": "true",
            "BROWSER_RESULT": "success",
            "ACCEPTANCE_REQUIRED": "true",
            "ACCEPTANCE_RESULT": "success",
            "ACCEPTANCE_ACCEPTED": "true",
            "DRIVE_SYNC_REQUIRED": "true",
            "DRIVE_SYNC_COMPLETED": "true",
        }
        values.update(changes)
        with tempfile.TemporaryDirectory(prefix="kgg-gate-completion-") as tmp:
            return run_bash(
                script(REQUIRED.read_text(), "Require successful core and every applicable browser regression"),
                Path(tmp),
                GITHUB_STEP_SUMMARY=str(Path(tmp) / "summary"),
                **values,
            )

    def test_success_and_explicit_not_applicable_pass(self) -> None:
        self.assertEqual(self.complete().returncode, 0)
        self.assertEqual(self.complete(
            BROWSER_REQUIRED="false", BROWSER_RESULT="skipped",
            ACCEPTANCE_REQUIRED="false", ACCEPTANCE_RESULT="skipped", ACCEPTANCE_ACCEPTED="",
            DRIVE_SYNC_REQUIRED="false", DRIVE_SYNC_COMPLETED="",
        ).returncode, 0)

    def test_required_jobs_reject_failure_cancel_skip_and_unknown(self) -> None:
        for name in ("SCOPE_RESULT", "CORE_RESULT", "BROWSER_RESULT", "ACCEPTANCE_RESULT"):
            for value in ("failure", "cancelled", "skipped", "", "unknown"):
                with self.subTest(name=name, value=value):
                    result = self.complete(**{name: value})
                    self.assertNotEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_invalid_requirement_flags_never_mean_not_applicable(self) -> None:
        for name in ("BROWSER_REQUIRED", "ACCEPTANCE_REQUIRED", "DRIVE_SYNC_REQUIRED"):
            for value in ("", "TRUE", "0", "unknown"):
                with self.subTest(name=name, value=value):
                    self.assertNotEqual(self.complete(**{name: value}).returncode, 0)

    def test_success_without_acceptance_proof_fails(self) -> None:
        for value in ("", "false", "TRUE", "unknown"):
            with self.subTest(value=value):
                self.assertNotEqual(self.complete(ACCEPTANCE_ACCEPTED=value).returncode, 0)

    def test_success_without_required_drive_sync_completion_fails(self) -> None:
        for value in ("", "false", "TRUE", "unknown"):
            with self.subTest(value=value):
                self.assertNotEqual(self.complete(DRIVE_SYNC_COMPLETED=value).returncode, 0)

    def test_last_successful_matrix_output_cannot_hide_other_engine_failure(self) -> None:
        self.assertNotEqual(self.complete(ACCEPTANCE_RESULT="failure", ACCEPTANCE_ACCEPTED="true").returncode, 0)

    def test_not_required_does_not_hide_a_failed_started_job(self) -> None:
        for value in ("failure", "cancelled", "unknown"):
            with self.subTest(value=value):
                self.assertNotEqual(self.complete(ACCEPTANCE_REQUIRED="false", ACCEPTANCE_RESULT=value).returncode, 0)


class WorkflowWiringTests(unittest.TestCase):
    def test_one_matrix_called_for_the_same_merge_candidate(self) -> None:
        required = REQUIRED.read_text()
        parity = PARITY.read_text()
        call = block(required, "  patient-acceptance:")
        self.assertIn("uses: ./.github/workflows/kgg-patient-ui-parity.yml", call)
        self.assertIn("if: needs.scope.outputs.patient_acceptance_required == 'true'", call)
        self.assertIn("candidate_sha: ${{ github.sha }}", call)
        self.assertIn("needs: scope", call)
        self.assertNotIn("matrix:", call)
        self.assertEqual(parity.count("browser: [chromium, webkit]"), 1)
        pull_request = block(parity, "  pull_request:")
        self.assertIn("branches: [feat/patient-react-padgrid-p8-20261014]", pull_request)
        self.assertNotRegex(pull_request, r"\bmain\b")
        self.assertIn("  workflow_dispatch:", parity)
        self.assertIn("  workflow_call:", parity)
        self.assertIn("ref: ${{ inputs.candidate_sha || github.event.pull_request.head.sha || github.sha }}", parity)
        self.assertIn("${{ steps.candidate.outputs.sha }}", parity)

    def test_required_job_depends_on_call_and_binds_proof(self) -> None:
        required = REQUIRED.read_text()
        gate = block(required, "  required-gate:")
        self.assertIn("name: required-gate", gate)
        self.assertIn("needs: [scope, core-gate, patient-browser, patient-acceptance]", gate)
        self.assertIn("if: ${{ always() }}", gate)
        for binding in (
            "ACCEPTANCE_REQUIRED: ${{ needs.scope.outputs.patient_acceptance_required }}",
            "ACCEPTANCE_RESULT: ${{ needs.patient-acceptance.result }}",
            "ACCEPTANCE_ACCEPTED: ${{ needs.patient-acceptance.outputs.accepted }}",
        ):
            self.assertIn(binding, gate)
        parity = PARITY.read_text()
        self.assertIn("value: ${{ jobs.parity.outputs.accepted }}", parity)
        self.assertIn("accepted: ${{ steps.acceptance.outputs.accepted }}", parity)

    def test_guards_and_diagnostics_are_retained(self) -> None:
        parity = PARITY.read_text()
        self.assertIn("if: github.event_name == 'workflow_dispatch' || github.event.pull_request.head.repo.full_name == github.repository", parity)
        self.assertIn("fail-fast: false", parity)
        self.assertIn("group: patient-integrated-${{ github.event.pull_request.number || github.ref }}", parity)
        self.assertNotIn("continue-on-error", parity)
        self.assertIn("persist-credentials: false", parity)
        self.assertIn("node --test release-pipeline/kgg_patient_full_acceptance_report.test.mjs", parity)
        upload = step(parity, "Keep complete evidence including failures")
        self.assertIn("if: always()", upload)
        self.assertIn("if-no-files-found: error", upload)

    def test_baseline_and_new_contract_tests_always_run(self) -> None:
        required = REQUIRED.read_text()
        core = block(required, "  core-gate:")
        # Unmapped/new product paths retain the unconditional critical baseline.
        self.assertNotRegex(core, re.compile(r"^    if:", re.M))
        critical = step(core, "Run critical KGG test battery")
        self.assertNotIn("        if:", critical)
        self.assertIn("--level critical", critical)
        self.assertIn("contains(github.event.pull_request.labels.*.name, 'kgg-no-release')", critical)
        scope = block(required, "  scope:")
        self.assertIn("run: python release-pipeline/test_kgg_required_gate.py", scope)

    def test_freshness_checks_precede_expensive_critical_battery(self) -> None:
        core = block(REQUIRED.read_text(), "  core-gate:")
        for name in (
            "Check Patient Custom GPT resources",
            "Check Custom GPT live context freshness",
            "Check Custom GPT bug knowledge freshness",
            "Check Custom GPT source context freshness",
            "Check Custom GPT knowledge pack freshness",
            "Check Custom GPT resource contract freshness",
        ):
            with self.subTest(name=name):
                self.assertLess(core.index("- name: " + name), core.index("- name: Run critical KGG test battery"))

    def test_scanner_regression_has_one_invocation_for_both_reasons(self) -> None:
        core = block(REQUIRED.read_text(), "  core-gate:")
        self.assertEqual(core.count("--suite patient-scan --level regression"), 1)
        scan = step(core, "Run patient QR camera regression")
        self.assertIn("needs.scope.outputs.patient_scan == 'true' || needs.scope.outputs.admin_camera_qr == 'true'", scan)


class AcceptanceProofTests(unittest.TestCase):
    def test_acceptance_proof_is_emitted_only_after_successful_runner(self) -> None:
        body = script(PARITY.read_text(), "Require one immutable combined acceptance candidate")
        body = body.replace("${{ matrix.browser }}", "chromium")
        self.assertNotIn("${{", body)
        boundary = 'python() { return "$KGG_FIXTURE_EXIT"; }\n'
        for exit_code in (0, 1, 2, 124):
            with self.subTest(exit_code=exit_code), tempfile.TemporaryDirectory(prefix="kgg-acceptance-proof-") as tmp:
                result = run_bash(
                    boundary + body, Path(tmp), RUNNER_TEMP=tmp,
                    GITHUB_OUTPUT=str(Path(tmp) / "outputs"), KGG_FIXTURE_EXIT=str(exit_code),
                )
                self.assertEqual(result.returncode, exit_code)
                self.assertEqual(outputs(Path(tmp) / "outputs").get("accepted"), "true" if exit_code == 0 else None)

    def test_checkout_proof_rejects_a_different_or_invalid_candidate(self) -> None:
        body = script(PARITY.read_text(), "Verify exact acceptance candidate")
        boundary = 'git() { [[ "$*" == "rev-parse HEAD" ]] && printf "%s\\n" "$KGG_ACTUAL_SHA"; }\n'
        for expected, actual, passes in (
            (SHA, SHA, True),
            (SHA, "b" * 40, False),
            ("main", SHA, False),
            ("", SHA, False),
        ):
            with self.subTest(expected=expected, actual=actual), tempfile.TemporaryDirectory(prefix="kgg-candidate-proof-") as tmp:
                result = run_bash(
                    boundary + body, Path(tmp), EXPECTED_CANDIDATE_SHA=expected,
                    KGG_ACTUAL_SHA=actual, GITHUB_OUTPUT=str(Path(tmp) / "outputs"),
                )
                self.assertEqual(result.returncode == 0, passes, result.stdout + result.stderr)
                self.assertEqual(outputs(Path(tmp) / "outputs").get("sha"), SHA if passes else None)


class DriveSyncTests(unittest.TestCase):
    def test_scoped_run_proof_and_exact_run_artifacts_are_wired(self) -> None:
        required = REQUIRED.read_text()
        core = block(required, "  core-gate:")
        scope = block(required, "  scope:")
        self.assertIn("drive_sync: ${{ steps.scope.outputs.drive_sync }}", scope)
        self.assertIn("drive_sync_completed: ${{ steps.drive_sync.outputs.completed }}", core)
        run = step(core, "Run scoped Drive sync end-to-end regression")
        self.assertIn("id: drive_sync", run)
        self.assertIn("if: needs.scope.outputs.drive_sync == 'true'", run)
        self.assertLess(core.index("- name: Run critical KGG test battery"), core.index("- name: Run scoped Drive sync end-to-end regression"))
        self.assertEqual(core.count("node release-pipeline/kgg_drive_sync_e2e.js --run --run-id"), 1)
        self.assertNotIn("continue-on-error", core)
        gate = block(required, "  required-gate:")
        self.assertIn("DRIVE_SYNC_REQUIRED: ${{ needs.scope.outputs.drive_sync }}", gate)
        self.assertIn("DRIVE_SYNC_COMPLETED: ${{ needs.core-gate.outputs.drive_sync_completed }}", gate)
        upload = step(core, "Keep scoped Drive sync evidence including failures")
        self.assertIn("if: ${{ always() && needs.scope.outputs.drive_sync == 'true' }}", upload)
        self.assertIn("uses: actions/upload-artifact@v4", upload)
        self.assertIn("name: drive-sync-e2e-${{ github.sha }}-${{ github.run_id }}-${{ github.run_attempt }}", upload)
        self.assertIn("path: output/drive-sync-e2e-20261015/ci-${{ github.run_id }}-${{ github.run_attempt }}/", upload)
        self.assertIn("if-no-files-found: error", upload)

    def test_completion_is_emitted_only_after_successful_sync_runner(self) -> None:
        body = script(REQUIRED.read_text(), "Run scoped Drive sync end-to-end regression")
        body = body.replace("${{ github.run_id }}", "123456").replace("${{ github.run_attempt }}", "2")
        self.assertNotIn("${{", body)
        boundary = r'''
node() {
  [[ "$*" == "release-pipeline/kgg_drive_sync_e2e.js --run --run-id ci-123456-2" ]] || return 91
  return "$KGG_FIXTURE_EXIT"
}
'''
        for exit_code in (0, 1, 2, 124):
            with self.subTest(exit_code=exit_code), tempfile.TemporaryDirectory(prefix="kgg-sync-proof-") as tmp:
                result = run_bash(
                    boundary + body, Path(tmp), GITHUB_OUTPUT=str(Path(tmp) / "outputs"),
                    KGG_FIXTURE_EXIT=str(exit_code),
                )
                self.assertEqual(result.returncode, exit_code, result.stdout + result.stderr)
                self.assertEqual(outputs(Path(tmp) / "outputs").get("completed"), "true" if exit_code == 0 else None)


class BrowserImageTests(unittest.TestCase):
    def test_only_patient_browser_uses_a_digest_pinned_matching_image(self) -> None:
        required = REQUIRED.read_text()
        browser = block(required, "  patient-browser:")
        image = re.search(r"^      image: mcr\.microsoft\.com/playwright:v(\d+\.\d+\.\d+)-noble@sha256:[a-f0-9]{64}$", browser, re.M)
        self.assertIsNotNone(image, "Pin the prepared image by version and digest")
        version = image.group(1)
        declared = json.loads((ROOT / "release-pipeline/package.json").read_text())
        locked = json.loads((ROOT / "release-pipeline/package-lock.json").read_text())
        self.assertEqual(version, declared["devDependencies"]["playwright"])
        self.assertEqual(version, locked["packages"]["node_modules/playwright"]["version"])
        self.assertIn(f"KGG_PLAYWRIGHT_IMAGE_VERSION: '{version}'", browser)
        self.assertIn("options: --ipc=host", browser)
        self.assertNotIn("    container:", block(required, "  core-gate:"))
        self.assertNotIn("    container:", PARITY.read_text())

    def test_real_version_guard_rejects_declared_locked_or_installed_drift(self) -> None:
        body = script(REQUIRED.read_text(), "Install patient browser dependencies")
        version = json.loads((ROOT / "release-pipeline/package.json").read_text())["devDependencies"]["playwright"]
        # Suppress package/browser downloads; execute the actual Python version guard.
        boundary = 'npm() { [[ "$*" == "ci" ]]; }\nnpx() { return 0; }\n'
        for mismatch in (None, "declared", "locked", "installed", "image"):
            with self.subTest(mismatch=mismatch), tempfile.TemporaryDirectory(prefix="kgg-image-contract-") as tmp:
                versions = dict.fromkeys(("declared", "locked", "installed", "image"), version)
                if mismatch:
                    versions[mismatch] = "0.0.0"
                pipeline = Path(tmp) / "release-pipeline"
                package = pipeline / "node_modules/playwright/package.json"
                package.parent.mkdir(parents=True)
                package.write_text(json.dumps({"version": versions["installed"]}))
                (pipeline / "package.json").write_text(json.dumps({"devDependencies": {"playwright": versions["declared"]}}))
                (pipeline / "package-lock.json").write_text(json.dumps({"packages": {"node_modules/playwright": {"version": versions["locked"]}}}))
                result = run_bash(boundary + body, Path(tmp), KGG_PLAYWRIGHT_IMAGE_VERSION=versions["image"])
                self.assertEqual(result.returncode == 0, mismatch is None, result.stdout + result.stderr)
                if mismatch:
                    self.assertIn("Playwright/image version mismatch", result.stderr)

    def test_prepared_image_avoids_reinstall_without_dropping_patient_checks(self) -> None:
        browser = block(REQUIRED.read_text(), "  patient-browser:")
        self.assertIn("KGG_SKIP_PLAYWRIGHT_INSTALL: '1'", block(browser, "    env:"))
        self.assertIn("PLAYWRIGHT_BROWSERS_PATH: /ms-playwright", browser)
        install = script(browser, "Install patient browser dependencies")
        self.assertIn("npm ci", install)
        self.assertNotRegex(browser, r"playwright(?:/cli\.js)?[\s\S]{0,20}\binstall\b|\bapt(?:-get)?\b")
        for name in (
            "Build and verify patient React UI (when affected)",
            "Run patient React controller smoke (when present)",
            "Run permanent patient continuous day-flow regression",
            "Run patient runtime and progress Playwright smoke",
            "Verify installed-worker React upgrade and guarded existing-PR release",
            "Run patient vertical pain Playwright smoke",
            "Run patient last-value shimmer Playwright smoke",
            "Run patient adaptive set-view browser regressions",
            "Run patient media stability regression",
            "Prepare isolated Patient GPT browser fixture",
            "Run Patient GPT browser smoke",
            "Run local patient update verification",
        ):
            with self.subTest(step=name):
                self.assertTrue(script(browser, name).strip())


if __name__ == "__main__":
    unittest.main(verbosity=2)
