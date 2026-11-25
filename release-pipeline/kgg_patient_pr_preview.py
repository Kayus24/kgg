"""Build and verify a synthetic patient preview from a pinned same-repo PR."""
from __future__ import annotations

import argparse
import base64
import hashlib
import json
import re
import struct
import subprocess
from pathlib import Path

from kgg_patient_gpt_write_gate import (
    ROOT, FORBIDDEN_NEW_SINKS, INTERFACE_MARKERS, DIRECT_FIRST_LOAD_MODULES, allowed_patient_path,
    contains_secret, copy_patient_runtime_file, patient_runtime_files, write_json, write_preview,
)

REPO = "Kayus24/kgg"
REQUIRED_PATH = ".github/workflows/kgg-required-gate.yml"
REQUIRED_ID = 305806983
SHA = re.compile(r"[0-9a-f]{40}")
SUPPORT_FILE = re.compile(
    r"docs/kgg-patient-gpt-source(?:-index\.json|/chunk-[0-9]+\.md)"
    r"|release-pipeline/kgg_patient_[a-z0-9_]+_smoke\.js"
    r"|release-pipeline/kgg_dual_device_package\.js"
    r"|release-pipeline/kgg_pwa_contract_smoke\.py"
    r"|\.github/workflows/kgg-patient-ui-parity\.yml"
)
NEW_ICON = re.compile(r"kgg-icon-(192|512|maskable-512)-v[1-9][0-9]{0,5}\.png")
# Narrow, trusted scope for the K2 inline NumPad integration. Do not execute
# candidate support scripts or import candidate gate constants.
K2_MODULE = "patient-set-k2-inline-editor.js"
K2_RUNTIME = {"index.html", "patient-numpad-visibility-fix.js", K2_MODULE}
K2_SUPPORT = {
    "docs/kgg-custom-gpt-resource-manifest.json",
    "docs/kgg-patient-custom-gpt-editor-snapshot.json",
    "docs/kgg-patient-custom-gpt-knowledge-architecture.md",
    "docs/kgg-patient-custom-gpt-knowledge-testing.md",
    "docs/kgg-patient-gpt-context.md",
    "kgg-plugin/references/architecture/source-hashes.json",
    "kgg-plugin/references/source-map.md",
    "release-pipeline/kgg_patient_compact_transfer_playwright.js",
    "release-pipeline/kgg_patient_continuous_days_playwright.js",
    "release-pipeline/kgg_patient_gpt_write_gate.py",
}
K2_GENERATED = re.compile(r"docs/kgg-patient-gpt-source(?:-index\.json|/chunk-[0-9]{3}\.md)")
K2_MAX_FILES = 40
K2_MAX_MODULE_BYTES = 65536

def k2_support(name):
    return name in K2_SUPPORT or bool(K2_GENERATED.fullmatch(name)) or (
        name == "release-pipeline/kgg_patient_numpad_commit_smoke.js"
    )

def preview_modules(candidate):
    modules = list(DIRECT_FIRST_LOAD_MODULES)
    if (candidate / K2_MODULE).is_file() and K2_MODULE not in modules:
        modules.insert(modules.index("patient-version-label.js"), K2_MODULE)
    return tuple(modules)


def require(condition, reason):
    if not condition:
        raise ValueError(reason)


def api(endpoint):
    return json.loads(subprocess.check_output(["gh", "api", f"repos/{REPO}/{endpoint}"]))


def verify_binding(pr, run, jobs, number, sha, run_id, base):
    require(
        pr["number"] == number and pr["state"] == "open"
        and pr["head"]["sha"] == sha and pr["head"]["repo"]["full_name"] == REPO
        and pr["base"]["ref"] == "main" and pr["base"]["sha"] == base
        and pr["base"]["repo"]["full_name"] == REPO
        and "kgg-no-release" in {label["name"] for label in pr["labels"]},
        "open same-repo labeled PR or exact source/base SHA could not be verified",
    )
    require(
        run["id"] == run_id and run["head_sha"] == sha
        and run["head_repository"]["full_name"] == REPO
        and run["event"] == "pull_request" and run["path"] == REQUIRED_PATH
        and run["workflow_id"] == REQUIRED_ID and run["status"] == "completed"
        and run["conclusion"] == "success"
        and any(
            item["id"] == pr["id"] and item["number"] == number and item["base"]["sha"] == base
            for item in run["pull_requests"]
        ),
        "Required Gate run is not successful for the exact PR, head and base",
    )
    required = [job for job in jobs if job["name"] == "required-gate"]
    require(
        len(required) == 1 and required[0]["status"] == "completed"
        and required[0]["conclusion"] == "success",
        "required-gate check is missing, ambiguous or unsuccessful",
    )
    return run["run_attempt"]


def verified_run(number, sha, run_id, base):
    require(api("branches/main")["commit"]["sha"] == base, "trusted main advanced")
    pr = api(f"pulls/{number}")
    run = api(f"actions/runs/{run_id}")
    attempt = run["run_attempt"]
    jobs = api(f"actions/runs/{run_id}/attempts/{attempt}/jobs?per_page=100")
    require(jobs["total_count"] == len(jobs["jobs"]), "incomplete CI job list")
    latest = api(f"actions/workflows/{REQUIRED_ID}/runs?event=pull_request&head_sha={sha}&per_page=1")
    require(
        latest["workflow_runs"] and latest["workflow_runs"][0]["id"] == run_id
        and latest["workflow_runs"][0]["run_attempt"] == attempt,
        "Required Gate run or attempt was superseded",
    )
    return verify_binding(pr, run, jobs["jobs"], number, sha, run_id, base)


def candidate_files(base, sha):
    diff = api(f"compare/{base}...{sha}")
    require(diff["status"] == "ahead" and diff["merge_base_commit"]["sha"] == base,
            "PR must be based on current trusted main")
    files = diff["files"]
    k2 = any(entry["filename"] == K2_MODULE and entry["status"] == "added" for entry in files)
    require(0 < len(files) <= (K2_MAX_FILES if k2 else 20),
            "PR exceeds the bounded preview file scope")
    require(len({entry["filename"] for entry in files}) == len(files),
            "duplicate paths in candidate diff")
    require(all(entry["status"] in {"added", "modified"} for entry in files),
            "deletions and renames are outside the preview scope")
    if k2:
        result = [entry for entry in files if not k2_support(entry["filename"])]
        require({entry["filename"] for entry in result} == K2_RUNTIME
                and all(entry["status"] == ("added" if entry["filename"] == K2_MODULE else "modified")
                        for entry in result),
                "K2 preview requires the exact bounded runtime scope")
        return result
    result = [entry for entry in files if not SUPPORT_FILE.fullmatch(entry["filename"])]
    added = [entry for entry in result if entry["status"] == "added"]
    require(0 < len(result) <= 7 and len(result) - len(added) <= 4 and len(added) <= 3
            and all(NEW_ICON.fullmatch(entry["filename"]) for entry in added),
            "expected at most four existing runtime changes and three new versioned icons")
    return result


def overlay(candidate, base, sha):
    files = candidate_files(base, sha)
    tree_sha = api(f"git/commits/{sha}")["tree"]["sha"]
    require(SHA.fullmatch(tree_sha), "invalid tree SHA")
    response = api(f"git/trees/{tree_sha}")
    require(response["truncated"] is False, "candidate tree is incomplete")
    tree = {entry["path"]: entry for entry in response["tree"]}
    for entry in files:
        name = entry["filename"]
        target = candidate / name
        new_icon = entry["status"] == "added" and NEW_ICON.fullmatch(name)
        new_k2 = entry["status"] == "added" and name == K2_MODULE
        require(
            ((bool(new_icon) or new_k2) and not target.exists()
             or entry["status"] == "modified" and target.is_file()) and "/" not in name
            and (allowed_patient_path(name) or re.fullmatch(r"kgg-icon-[a-z0-9-]+\.png", name))
            and name not in {"patient-storage-scope.js", "update-recovery.html"},
            "PR contains a change outside the preview runtime scope",
        )
        blob = tree[name]
        require(
            blob["mode"] == "100644" and blob["type"] == "blob" and blob["sha"] == entry["sha"]
            and SHA.fullmatch(blob["sha"]) and 0 < blob["size"] <= 1_000_000,
            "candidate does not point to a bounded regular blob",
        )
        response = api(f"git/blobs/{blob['sha']}")
        require(response["encoding"] == "base64", "unexpected blob encoding")
        data = base64.b64decode("".join(response["content"].split()), validate=True)
        git_blob = f"blob {len(data)}\0".encode() + data
        require(len(data) == blob["size"] and hashlib.sha1(git_blob).hexdigest() == blob["sha"],
                "candidate blob failed integrity check")
        if new_k2:
            require(len(data) <= K2_MAX_MODULE_BYTES, "K2 module exceeds its size limit")
        if new_icon:
            size = 192 if new_icon[1] == "192" else 512
            require(len(data) >= 33 and data[:16] == b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR"
                    and struct.unpack(">II", data[16:24]) == (size, size),
                    "new icon has an invalid PNG header or dimensions")
        if not name.endswith(".png"):
            old, new = ("" if new_k2 else target.read_text(encoding="utf-8")), data.decode("utf-8")
            sensitive = (*FORBIDDEN_NEW_SINKS, *INTERFACE_MARKERS, "localStorage.clear", "sessionStorage.clear")
            require(not contains_secret(new) and all(new.count(item) == old.count(item) for item in sensitive),
                    "candidate changes protected interfaces or contains a token-shaped secret")
        target.write_bytes(data)


def file_hashes(root):
    return {
        path.relative_to(root).as_posix(): hashlib.sha256(path.read_bytes()).hexdigest()
        for path in sorted(root.rglob("*")) if path.is_file() and path != root / "meta.json"
    }


def verify_files(root, expected):
    require(not any(path.is_symlink() for path in root.rglob("*")), "unexpected symlink in artifact")
    require(expected and file_hashes(root) == expected, "artifact file hashes or paths drifted")


def require_new(root, request_id):
    require(not (root / "previews" / request_id).exists(), "exact PR head was already published")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=("build", "verify"))
    parser.add_argument("pr")
    parser.add_argument("head")
    parser.add_argument("run")
    parser.add_argument("base")
    parser.add_argument("work", type=Path)
    args = parser.parse_args()
    require(re.fullmatch(r"[1-9][0-9]{0,8}", args.pr) and re.fullmatch(r"[1-9][0-9]{0,16}", args.run)
            and SHA.fullmatch(args.head) and SHA.fullmatch(args.base), "invalid PR, SHA or run inputs")
    args.pr, args.run = int(args.pr), int(args.run)
    request_id = f"pr-{args.pr}-{args.head}"
    binding = {
        "sourcePr": args.pr, "sourceSha": args.head, "baseSha": args.base,
        "verificationRunId": args.run,
        "verificationRunAttempt": verified_run(args.pr, args.head, args.run, args.base),
    }
    meta_path = args.work / "previews" / request_id / "meta.json"
    if args.mode == "build":
        require_new(args.work, request_id)
        candidate = args.work / "candidate"
        for source in patient_runtime_files(ROOT):
            copy_patient_runtime_file(source, ROOT, candidate)
        overlay(candidate, args.base, args.head)
        worker = (candidate / "service-worker.js").read_text(encoding="utf-8")
        version = re.search(r"const CACHE_NAME = 'kgg-handyplan-v([0-9]+)-", worker)
        require(version, "missing patient version")
        metadata = write_preview(args.work, {
            "request_id": request_id, "base_sha": args.base, "risk_class": "ui",
            "title": f"Verified patient PR #{args.pr}", "summary": "Synthetic patient test plan",
        }, hashlib.sha256(json.dumps(binding, sort_keys=True).encode()).hexdigest(), int(version[1]), candidate,
                                 expected_modules=preview_modules(candidate))
        metadata.update(binding, kind="kgg_patient_verified_pr_preview", files=file_hashes(meta_path.parent))
        write_json(meta_path, metadata)
    else:
        metadata = json.loads(meta_path.read_text(encoding="utf-8"))
        require(metadata["kind"] == "kgg_patient_verified_pr_preview" and metadata["requestId"] == request_id
                and all(metadata[key] == value for key, value in binding.items()),
                "artifact no longer matches PR and CI evidence")
        verify_files(meta_path.parent, metadata["files"])


if __name__ == "__main__":
    main()
