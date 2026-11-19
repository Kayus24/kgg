"""Build and verify a synthetic patient preview from a pinned same-repo PR."""
from __future__ import annotations

import argparse
import base64
import hashlib
import json
import re
import subprocess
from pathlib import Path

from kgg_patient_gpt_write_gate import (
    ROOT, FORBIDDEN_NEW_SINKS, INTERFACE_MARKERS, allowed_patient_path,
    contains_secret, copy_patient_runtime_file, patient_runtime_files, write_json, write_preview,
)

REPO = "Kayus24/kgg"
REQUIRED_PATH = ".github/workflows/kgg-required-gate.yml"
REQUIRED_ID = 305806983
SHA = re.compile(r"[0-9a-f]{40}")
SUPPORT_FILE = re.compile(
    r"docs/kgg-patient-gpt-source(?:-index\.json|/chunk-[0-9]+\.md)"
    r"|release-pipeline/kgg_patient_[a-z0-9_]+_smoke\.js"
)


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
    require(0 < len(files) <= 20, "PR exceeds the bounded preview file scope")
    require(all(entry["status"] in {"added", "modified"} for entry in files),
            "deletions and renames are outside the preview scope")
    result = [entry for entry in files if not SUPPORT_FILE.fullmatch(entry["filename"])]
    require(0 < len(result) <= 4, "expected one to four patient runtime changes")
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
        require(
            entry["status"] == "modified" and "/" not in name
            and (allowed_patient_path(name) or re.fullmatch(r"kgg-icon-[a-z0-9-]+\.png", name))
            and target.is_file() and name not in {"patient-storage-scope.js", "update-recovery.html"},
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
        if not name.endswith(".png"):
            old, new = target.read_text(encoding="utf-8"), data.decode("utf-8")
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
        }, hashlib.sha256(json.dumps(binding, sort_keys=True).encode()).hexdigest(), int(version[1]), candidate)
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
