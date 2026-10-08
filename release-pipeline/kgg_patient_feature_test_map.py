#!/usr/bin/env python3
"""Read-only preflight for the patient feature↔test map.

This command validates a test inventory or reports potentially affected contracts.
It DOES NOT run tests, declare product readiness, or rewrite test expectations.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MAP_PATH = ROOT / "docs" / "quality" / "patient-feature-test-map.v1.json"
FEATURE_ID = re.compile(r"^PAT-[A-Z]+-[0-9]{3}$")


def safe_path(value: str) -> bool:
    if not isinstance(value, str) or not value or "\\" in value or value.startswith("/"):
        return False
    parts = value.split("/")
    return all(part and part not in {".", ".."} for part in parts)


def validate(data: dict, root: Path) -> list[str]:
    errors: list[str] = []
    if not isinstance(data, dict) or data.get("schema") != "kgg/patient-feature-test-map/v1":
        return ["unexpected mapping schema"]
    features = data.get("features")
    if not isinstance(features, list) or not features:
        return ["features must be a non-empty list"]
    seen: set[str] = set()
    for i, feature in enumerate(features):
        if not isinstance(feature, dict):
            errors.append(f"features[{i}] is not an object")
            continue
        fid = feature.get("id")
        if not isinstance(fid, str) or not FEATURE_ID.fullmatch(fid) or fid in seen:
            errors.append(f"features[{i}] missing, invalid or duplicate id: {fid!r}")
        if isinstance(fid, str):
            seen.add(fid)
        if feature.get("coverage") not in {"DIRECT", "PARTIAL"}:
            errors.append(f"{fid}: unsupported coverage")
        for field in ("source_paths", "test_paths"):
            paths = feature.get(field)
            if not isinstance(paths, list) or not paths:
                errors.append(f"{fid}: {field} must be a non-empty list")
                continue
            if len(paths) != len(set(str(p) for p in paths)):
                errors.append(f"{fid}: {field} contains duplicates")
            for path in paths:
                if not safe_path(path):
                    errors.append(f"{fid}: invalid path {path!r}")
                    continue
                if field == "test_paths" and not path.startswith("release-pipeline/"):
                    errors.append(f"{fid}: test outside release-pipeline: {path}")
                if not (root / path).is_file():
                    errors.append(f"{fid}: file missing: {path}")
    if not data.get("canonical_feature_source", {}).get("url", "").startswith("https://"):
        errors.append("canonical feature source URL missing")
    return errors


def impact(data: dict, paths: list[str]) -> dict:
    changed = set(paths)
    impacted = [
        feature for feature in data["features"]
        if changed.intersection(feature["source_paths"] + feature["test_paths"])
    ]
    mapped_paths = {
        path for feature in data["features"]
        for path in feature["source_paths"] + feature["test_paths"]
    }
    unknown = sorted(changed - mapped_paths)
    react_unknown = [p for p in unknown if p.startswith("patient-ui/")]
    return {
        "status": "REVIEW_REQUIRED",
        "test_execution": "NOT_RUN",
        "impacted_feature_ids": sorted(f["id"] for f in impacted),
        "candidate_test_paths": sorted({t for f in impacted for t in f["test_paths"]}),
        "partial_coverage_feature_ids": sorted(f["id"] for f in impacted if f["coverage"] == "PARTIAL"),
        "unmapped_changed_paths": unknown,
        "react_source_requires_contract_review": bool(react_unknown),
        "note": "Exact-path impact is advisory only; unmapped React files and partial coverage are NOT PASS.",
    }


def self_test() -> None:
    with tempfile.TemporaryDirectory() as folder:
        root = Path(folder)
        (root / "release-pipeline").mkdir()
        (root / "patient.js").write_text("", encoding="utf-8")
        (root / "release-pipeline" / "test.js").write_text("", encoding="utf-8")
        sample = {
            "schema": "kgg/patient-feature-test-map/v1",
            "canonical_feature_source": {"url": "https://docs.google.com/example"},
            "features": [{
                "id": "PAT-NUM-001", "coverage": "PARTIAL",
                "source_paths": ["patient.js"],
                "test_paths": ["release-pipeline/test.js"],
            }],
        }
        assert validate(sample, root) == [], "positive preflight failed"
        r = impact(sample, ["patient.js", "patient-ui/src/Adapter.tsx"])
        assert r["impacted_feature_ids"] == ["PAT-NUM-001"]
        assert r["candidate_test_paths"] == ["release-pipeline/test.js"]
        assert r["react_source_requires_contract_review"]
        assert r["test_execution"] == "NOT_RUN"
        (root / "release-pipeline" / "test.js").unlink()
        assert any("file missing" in s for s in validate(sample, root))
        sample["features"][0]["source_paths"] = ["../escape"]
        assert any("invalid path" in s for s in validate(sample, root))
    print("patient feature-test map self-test: PASS (synthetic only)")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="validate static mapping")
    parser.add_argument("--self-test", action="store_true", help="synthetic validator checks")
    parser.add_argument("--changed", nargs="+", metavar="REPO_PATH", help="report affected contracts (never greenlights merge)")
    args = parser.parse_args()
    if not (args.check or args.self_test or args.changed):
        parser.error("select --check, --self-test or --changed")
    if args.self_test:
        self_test()
    if args.check or args.changed:
        data = json.loads(MAP_PATH.read_text(encoding="utf-8"))
        errors = validate(data, ROOT)
        if errors:
            for err in errors:
                print("ERROR: " + err, file=sys.stderr)
            return 1
        if args.check:
            print("patient feature-test map structure: VALID (tests NOT RUN)")
        if args.changed:
            invalid = [p for p in args.changed if not safe_path(p)]
            if invalid:
                print("invalid --changed paths: " + repr(invalid), file=sys.stderr)
                return 2
            print(json.dumps(impact(data, args.changed), indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
