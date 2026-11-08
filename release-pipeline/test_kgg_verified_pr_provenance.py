#!/usr/bin/env python3
"""Negative and positive offline tests for KGG generic PR provenance."""

from __future__ import annotations

import base64
import copy
import hashlib
import importlib.util
import json
import os
import subprocess
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path

MODULE = Path(__file__).with_name("kgg_verified_pr_provenance.py")
spec = importlib.util.spec_from_file_location("kgg_verified_pr_provenance", MODULE)
gate = importlib.util.module_from_spec(spec)
assert spec and spec.loader
spec.loader.exec_module(gate)

SHA = "a" * 40
BRANCH = "fix/verified-cockpit"
BASE = "fix/plan-card-space-v132"
BASE_SHA = "c" * 40
RUN_ID = 41614544379
PR_NUM = 359


def valid_records() -> tuple[dict, dict]:
    repo = {"full_name": gate.REPO}
    pr = {
        "number": PR_NUM, "state": "open", "draft": True,
        "head": {"ref": BRANCH, "sha": SHA, "repo": {"full_name": gate.REPO}},
        "base": {"ref": BASE, "sha": BASE_SHA, "repo": {"full_name": gate.REPO}},
        "author_association": "OWNER",
        "labels": [{"name": gate.NO_RELEASE_LABEL}, {"name": gate.APPROVAL_LABEL}],
    }
    run = {
        "id": RUN_ID, "status": "completed", "conclusion": "success",
        "event": "pull_request", "name": gate.WORKFLOW_NAME,
        "path": gate.WORKFLOW_PATH, "workflow_id": gate.WORKFLOW_ID,
        "head_sha": SHA, "head_branch": BRANCH,
        "repository": {"full_name": gate.REPO}, "head_repository": {"full_name": gate.REPO},
        "pull_requests": [{"number": PR_NUM, "head": {"sha": SHA, "ref": BRANCH},
                           "base": {"sha": BASE_SHA, "ref": BASE}}],
    }
    return pr, run


def check(pr: dict, run: dict, **overrides: object) -> dict:
    values = {"pr_number": PR_NUM, "sha": SHA, "branch": BRANCH,
              "base_branch": BASE, "base_sha": BASE_SHA, "run_id": RUN_ID}
    values.update(overrides)
    return gate.validate(pr, run, **values)


def write_mock_apk(path: Path, context: dict, *, include_context: bool = True,
                   embedded_js: bytes | None = None) -> None:
    data = {key: value for key, value in context.items() if key != "webVersion"}
    js = (b"window.KGGPreviewContext=Object.freeze("
          + json.dumps(data, separators=(",", ":")).encode("utf-8")
          + b");\n") if embedded_js is None else embedded_js
    with zipfile.ZipFile(path, "w") as archive:
        archive.writestr("AndroidManifest.xml", b"manifest")
        archive.writestr("classes.dex", b"dummy" * 500)
        if include_context:
            archive.writestr("assets/android/kgg_preview_context.js", js)


def staged_fixture(root: Path) -> tuple[Path, dict, Path]:
    stage = root / "staged"
    stage.mkdir()
    version_raw = json.dumps({"versionCode": 138, "versionName": "v138-test"},
                             sort_keys=True).encode()
    (stage / "version.json").write_bytes(version_raw)
    payload = {
        "schemaVersion": 2, "kind": "kgg_preview_context",
        "requestId": "test-request-48", "baseSha": BASE_SHA, "commitSha": SHA,
        "patchHash": hashlib.sha256(
            f"approved-pr|{PR_NUM}|{SHA}|{RUN_ID}".encode("ascii")
        ).hexdigest(), "webVersion": "v138-test",
        "requiredTests": gate.REQUIRED_TESTS[:],
        "previewVersion": "0.2.14-v404-dual-device-qr-test",
        "stationTestIds": ["admin-portrait", "display-pairing"],
        "deviceTestSessionId": "kgg-test-" + SHA[:32],
        "deviceTestJobHash": "f" * 64,
        "deviceTestJobUrl": "https://raw.githubusercontent.com/Kayus24/kgg/gpt-preview/device-tests/test/job.json",
        "patientPwaUrl": "https://kayus24.github.io/kgg-patient-preview/device-test/",
        "deviceTestProfile": "quick",
    }
    (stage / "kgg-preview-context.json").write_text(json.dumps(payload), encoding="utf-8")
    write_mock_apk(stage / "app-preview-debug.apk", payload)
    blob = hashlib.sha1(b"blob " + str(len(version_raw)).encode() +
                        b"\0" + version_raw).hexdigest()
    api = {
        "type": "file", "path": "kgg-update/version.json",
        "encoding": "base64", "size": len(version_raw), "sha": blob,
        "content": base64.b64encode(version_raw).decode("ascii"),
    }
    sdk = root / "android-sdk"
    signer = sdk / "build-tools" / "35.0.0" / "apksigner"
    signer.parent.mkdir(parents=True)
    signer.write_text("fixture not executed", encoding="utf-8")
    (signer.parent / "aapt2").write_text("fixture not executed", encoding="utf-8")
    return stage, api, sdk


def fake_signer_success(args: list[str], **kwargs: object) -> subprocess.CompletedProcess:
    assert args[1:3] == ["verify", "--verbose"]
    assert "timeout" in kwargs
    return subprocess.CompletedProcess(args, 0, "", "")


def mock_package_id(args: list[str], **kwargs: object) -> subprocess.CompletedProcess:
    assert args[1:3] == ["dump", "packagename"]
    assert "timeout" in kwargs
    return subprocess.CompletedProcess(args, 0, "de.kgg.preview\n", "")


def validate_stage(stage: Path, api: dict, sdk: Path, **overrides: object) -> dict:
    values = {
        "pr_number": PR_NUM, "sha": SHA, "base_sha": BASE_SHA,
        "run_id": RUN_ID, "request_id": "test-request-48",
        "android_home": sdk, "signature_runner": fake_signer_success,
        "package_runner": mock_package_id,
    }
    values.update(overrides)
    return gate.verify_staged_artifact(stage, api, **values)


class GateTests(unittest.TestCase):
    def test_known_good_never_authorizes_publish(self) -> None:
        pr, run = valid_records()
        result = check(pr, run)
        self.assertEqual(result["status"], "PASS")
        self.assertFalse(result["publishingAuthorized"])
        self.assertEqual(result["sha"], SHA)
        self.assertEqual(result["baseSha"], BASE_SHA)
        self.assertEqual(result["contract"], gate.CONTRACT)

    def test_denies_security_and_identity_mismatches(self) -> None:
        cases = {
            "approval": lambda p, r: p.update(labels=[{"name": gate.NO_RELEASE_LABEL}]),
            "release_label": lambda p, r: p.update(labels=[{"name": gate.APPROVAL_LABEL}]),
            "head_drift": lambda p, r: p["head"].update(sha="b" * 40),
            "base_drift": lambda p, r: p["base"].update(ref="main"),
            "base_sha_drift": lambda p, r: p["base"].update(sha="d" * 40),
            "run_pr_base_sha": lambda p, r: r["pull_requests"][0]["base"].update(sha="d" * 40),
            "run_pr_base_ref": lambda p, r: r["pull_requests"][0]["base"].update(ref="main"),
            "run_pr_head_ref": lambda p, r: r["pull_requests"][0]["head"].update(ref="other"),
            "branch_drift": lambda p, r: p["head"].update(ref="malicious"),
            "fork": lambda p, r: p["head"]["repo"].update(full_name="outside/fork"),
            "closed": lambda p, r: p.update(state="closed"),
            "not_draft": lambda p, r: p.update(draft=False),
            "author_untrusted": lambda p, r: p.update(author_association="NONE"),
            "run_failed": lambda p, r: r.update(conclusion="failure"),
            "run_running": lambda p, r: r.update(status="in_progress"),
            "run_event": lambda p, r: r.update(event="workflow_dispatch"),
            "run_name": lambda p, r: r.update(name="Arbitrary green workflow"),
            "run_path": lambda p, r: r.update(path=".github/workflows/bypass.yml"),
            "run_workflow_id": lambda p, r: r.update(workflow_id=999),
            "run_head": lambda p, r: r.update(head_sha="b" * 40),
            "run_branch": lambda p, r: r.update(head_branch="elsewhere"),
            "run_repo": lambda p, r: r["repository"].update(full_name="outside/repo"),
            "run_head_repo": lambda p, r: r["head_repository"].update(full_name="outside/repo"),
            "run_pr_mismatch": lambda p, r: r.update(pull_requests=[{"number": 500, "head": {"sha": SHA}}]),
            "run_pr_sha": lambda p, r: r["pull_requests"][0]["head"].update(sha="b" * 40),
            "run_pr_duplicate": lambda p, r: r["pull_requests"].append(copy.deepcopy(r["pull_requests"][0])),
            "run_id_drift": lambda p, r: r.update(id=123),
            "pr_bool_number": lambda p, r: p.update(number=True),
            "run_bool_id": lambda p, r: r.update(id=True),
        }
        for label, mutate in cases.items():
            with self.subTest(label=label):
                pr, run = valid_records()
                # The two records intentionally get independent object trees.
                pr = copy.deepcopy(pr)
                run = copy.deepcopy(run)
                mutate(pr, run)
                with self.assertRaises(gate.ProvenanceError):
                    check(pr, run)

    def test_denies_invalid_requested_inputs(self) -> None:
        invalid = [
            {"pr_number": True},
            {"run_id": 0},
            {"sha": "not-a-sha"},
            {"branch": "refs/heads/../bad"},
            {"base_branch": "bad//base"},
            {"branch": "x;echo secret"},
            {"base_branch": "/leading-slash"},
            {"base_sha": "not-a-sha"},
        ]
        for bad in invalid:
            with self.subTest(bad=bad):
                pr, run = valid_records()
                with self.assertRaises(gate.ProvenanceError):
                    check(pr, run, **bad)

    def test_independently_pinned_base_blocks_retarget_even_with_matching_live_records(self) -> None:
        pr, run = valid_records()
        pr["base"]["sha"] = "d" * 40
        run["pull_requests"][0]["base"]["sha"] = "d" * 40
        with self.assertRaisesRegex(gate.ProvenanceError, "pr_base_sha_drift"):
            check(pr, run)
        fresh_pr, _ = valid_records()
        with self.assertRaisesRegex(gate.ProvenanceError, "run_pr_base_drift"):
            check(fresh_pr, run)

    def test_staged_artifact_fixture_uses_mock_signature_only(self) -> None:
        with tempfile.TemporaryDirectory(prefix="kgg-artifact-unit-") as tmp:
            stage, api, sdk = staged_fixture(Path(tmp))
            result = validate_stage(stage, api, sdk)
            self.assertEqual(result["status"], "PASS")
            self.assertTrue(result["artifactSignatureVerified"])
            self.assertFalse(result["publishingAuthorized"])
            self.assertEqual(result["sourceSha"], SHA)
            self.assertEqual(result["baseSha"], BASE_SHA)

    def test_rejects_foreign_signed_apk_and_wrong_embedded_context(self) -> None:
        with tempfile.TemporaryDirectory(prefix="kgg-identity-negative-") as tmp:
            stage, api, sdk = staged_fixture(Path(tmp))
            def foreign_package(args: list[str], **kwargs: object) -> subprocess.CompletedProcess:
                return subprocess.CompletedProcess(args, 0, "com.other.app\n", "")
            with self.assertRaisesRegex(gate.ProvenanceError, "apk_application_id_mismatch"):
                validate_stage(stage, api, sdk, package_runner=foreign_package)
            apk = stage / "app-preview-debug.apk"
            sidecar = json.loads((stage / "kgg-preview-context.json").read_text(encoding="utf-8"))
            write_mock_apk(apk, sidecar, include_context=False)
            with self.assertRaisesRegex(gate.ProvenanceError, "apk_context_asset_missing"):
                validate_stage(stage, api, sdk)
            altered = {key: value for key, value in sidecar.items() if key != "webVersion"}
            altered["commitSha"] = "e" * 40
            bad_js = (b"window.KGGPreviewContext=Object.freeze("
                      + json.dumps(altered).encode("utf-8") + b");\n")
            write_mock_apk(apk, sidecar, embedded_js=bad_js)
            with self.assertRaisesRegex(gate.ProvenanceError, "apk_embedded_context_mismatch"):
                validate_stage(stage, api, sdk)

    def test_staged_artifact_rejects_wrong_pinned_metadata(self) -> None:
        with tempfile.TemporaryDirectory(prefix="kgg-artifact-negative-") as tmp:
            stage, api, sdk = staged_fixture(Path(tmp))
            context_file = stage / "kgg-preview-context.json"
            original = json.loads(context_file.read_text(encoding="utf-8"))
            for field, wrong in (
                ("commitSha", "e" * 40), ("baseSha", "e" * 40),
                ("requestId", "wrong-request"), ("patchHash", "f" * 64),
                ("webVersion", "wrong-version"), ("schemaVersion", 1),
                ("requiredTests", ["critical"])
            ):
                with self.subTest(field=field):
                    altered = copy.deepcopy(original)
                    altered[field] = wrong
                    context_file.write_text(json.dumps(altered), encoding="utf-8")
                    with self.assertRaises(gate.ProvenanceError):
                        validate_stage(stage, api, sdk)
            context_file.write_text(json.dumps(original), encoding="utf-8")
            for override in ({"sha": "f" * 40}, {"base_sha": "f" * 40},
                             {"request_id": "other-request"}, {"run_id": RUN_ID + 1}):
                with self.subTest(override=override):
                    with self.assertRaises(gate.ProvenanceError):
                        validate_stage(stage, api, sdk, **override)

    def test_staged_artifact_rejects_version_tamper_and_invalid_api(self) -> None:
        with tempfile.TemporaryDirectory(prefix="kgg-version-negative-") as tmp:
            stage, api, sdk = staged_fixture(Path(tmp))
            version_path = stage / "version.json"
            version_path.write_bytes(b'{"versionCode":999,"versionName":"fake"}')
            with self.assertRaisesRegex(gate.ProvenanceError, "artifact_version_mismatch"):
                validate_stage(stage, api, sdk)
            version_path.write_bytes(base64.b64decode(api["content"]))
            for field, wrong in (("path", "arbitrary/version.json"),
                                 ("sha", "a" * 40), ("size", 0),
                                 ("encoding", "utf-8")):
                with self.subTest(field=field):
                    tampered = dict(api)
                    tampered[field] = wrong
                    with self.assertRaises(gate.ProvenanceError):
                        validate_stage(stage, tampered, sdk)

    def test_staged_artifact_rejects_invalid_zip_manifest_and_size(self) -> None:
        with tempfile.TemporaryDirectory(prefix="kgg-zip-negative-") as tmp:
            stage, api, sdk = staged_fixture(Path(tmp))
            apk = stage / "app-preview-debug.apk"
            apk.write_bytes(b"not a zip" * 400)
            with self.assertRaisesRegex(gate.ProvenanceError, "apk_zip_invalid"):
                validate_stage(stage, api, sdk)
            with zipfile.ZipFile(apk, "w") as archive:
                archive.writestr("classes.dex", b"dummy" * 500)
            with self.assertRaisesRegex(gate.ProvenanceError, "apk_manifest_missing"):
                validate_stage(stage, api, sdk)
            apk.write_bytes(b"tiny")
            with self.assertRaisesRegex(gate.ProvenanceError, "apk_size_invalid"):
                validate_stage(stage, api, sdk)
            (stage / "extra.bin").write_bytes(b"data")
            with self.assertRaisesRegex(gate.ProvenanceError, "artifact_stage_shape_invalid"):
                validate_stage(stage, api, sdk)

    def test_staged_artifact_requires_real_sdk_and_signature_exit_zero(self) -> None:
        with tempfile.TemporaryDirectory(prefix="kgg-signature-negative-") as tmp:
            stage, api, sdk = staged_fixture(Path(tmp))
            with self.assertRaisesRegex(gate.ProvenanceError, "android_build_tools_unavailable"):
                validate_stage(stage, api, sdk / "absent")
            (sdk / "build-tools" / "35.0.0" / "apksigner").unlink()
            with self.assertRaisesRegex(gate.ProvenanceError, "apksigner_unavailable"):
                validate_stage(stage, api, sdk)
            signer = sdk / "build-tools" / "35.0.0" / "apksigner"
            signer.write_text("fixture not executed", encoding="utf-8")
            def reject_signature(args: list[str], **kwargs: object) -> subprocess.CompletedProcess:
                return subprocess.CompletedProcess(args, 1, "", "no signature")
            with self.assertRaisesRegex(gate.ProvenanceError, "apk_signature_invalid"):
                validate_stage(stage, api, sdk, signature_runner=reject_signature)
            (sdk / "build-tools" / "35.0.0" / "aapt2").unlink()
            with self.assertRaisesRegex(gate.ProvenanceError, "aapt2_unavailable"):
                validate_stage(stage, api, sdk)

    def test_artifact_cli_denies_unsigned_data_when_sdk_is_missing(self) -> None:
        with tempfile.TemporaryDirectory(prefix="kgg-artifact-cli-") as tmp:
            root = Path(tmp)
            stage, api, _ = staged_fixture(root)
            api_path = root / "api.json"
            api_path.write_text(json.dumps(api), encoding="utf-8")
            env = dict(os.environ)
            env.pop("ANDROID_HOME", None)
            proc = subprocess.run([
                sys.executable, "-B", str(MODULE), "--verify-artifact",
                "--artifact-dir", str(stage),
                "--github-version-file", str(api_path),
                "--pr-number", str(PR_NUM), "--sha", SHA,
                "--base-sha", BASE_SHA, "--run-id", str(RUN_ID),
                "--request-id", "test-request-48",
            ], env=env, capture_output=True, text=True, timeout=12)
            self.assertEqual(proc.returncode, 1, proc.stdout)
            self.assertEqual(json.loads(proc.stdout)["code"], "android_sdk_unavailable")

    def test_cli_rejects_missing_approval_then_accepts_test_fixture(self) -> None:
        pr, run = valid_records()
        with tempfile.TemporaryDirectory(prefix="kgg-provenance-") as tmp:
            root = Path(tmp)
            pr_path = root / "pr.json"
            run_path = root / "run.json"
            def invoke() -> subprocess.CompletedProcess:
                pr_path.write_text(json.dumps(pr), encoding="utf-8")
                run_path.write_text(json.dumps(run), encoding="utf-8")
                return subprocess.run([
                    sys.executable, str(MODULE), "--pr-file", str(pr_path),
                    "--run-file", str(run_path), "--pr-number", str(PR_NUM),
                    "--sha", SHA, "--branch", BRANCH, "--base-branch", BASE,
                    "--base-sha", BASE_SHA, "--run-id", str(RUN_ID),
                ], capture_output=True, text=True, timeout=12)
            pr["labels"].pop()
            denied = invoke()
            self.assertEqual(denied.returncode, 1, denied.stdout)
            self.assertEqual(json.loads(denied.stdout)["code"], "preview_approval_missing")
            pr["labels"].append({"name": gate.APPROVAL_LABEL})
            accepted = invoke()
            self.assertEqual(accepted.returncode, 0, accepted.stdout)
            self.assertFalse(json.loads(accepted.stdout)["publishingAuthorized"])


if __name__ == "__main__":
    unittest.main()
