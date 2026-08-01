#!/usr/bin/env python3
"""Run gate-owned declarative regression contracts against generated Admin HTML."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
CONTRACT_ROOT = ROOT / "release-pipeline" / "gpt-regressions"
GENERATED_HTML = ROOT / "kgg-update" / "index.html"
SCHEMA_VERSION = 1


class ContractError(RuntimeError):
    pass


def fail(message: str) -> None:
    raise ContractError(message)


def load_contract(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        fail(f"cannot read regression contract {path}: {exc}")
    if not isinstance(value, dict):
        fail(f"regression contract must be an object: {path}")
    if value.get("schemaVersion") != SCHEMA_VERSION:
        fail(f"unsupported regression contract schema in {path}")
    if not isinstance(value.get("requestId"), str) or not value["requestId"].strip():
        fail(f"missing requestId in {path}")
    assertions = value.get("assertions")
    if not isinstance(assertions, list) or not assertions:
        fail(f"missing assertions in {path}")
    return value


def check_contract(path: Path, html: str) -> int:
    contract = load_contract(path)
    count = 0
    for index, assertion in enumerate(contract["assertions"], start=1):
        if not isinstance(assertion, dict):
            fail(f"assertion {index} must be an object in {path}")
        kind = assertion.get("kind")
        value = assertion.get("value")
        if kind not in {"contains", "not_contains"} or not isinstance(value, str) or not value:
            fail(f"invalid assertion {index} in {path}")
        if kind == "contains" and value not in html:
            fail(f"{contract['requestId']} assertion {index} failed: generated HTML must contain {value!r}")
        if kind == "not_contains" and value in html:
            fail(f"{contract['requestId']} assertion {index} failed: generated HTML must not contain {value!r}")
        count += 1
    print(f"PASS {contract['requestId']}: {count} declarative assertions")
    return count


def run_all() -> None:
    if not GENERATED_HTML.is_file():
        fail(f"missing generated Admin HTML: {GENERATED_HTML}")
    html = GENERATED_HTML.read_text(encoding="utf-8")
    paths = sorted(CONTRACT_ROOT.glob("*.json")) if CONTRACT_ROOT.is_dir() else []
    total = sum(check_contract(path, html) for path in paths)
    print(f"KGG GPT regression contracts OK: {len(paths)} contracts, {total} assertions")


def self_test() -> None:
    sample = {
        "schemaVersion": SCHEMA_VERSION,
        "requestId": "self-test",
        "assertions": [
            {"kind": "contains", "value": "needle"},
            {"kind": "not_contains", "value": "forbidden"},
        ],
    }
    temp = ROOT / "release-pipeline" / ".kgg-gpt-regression-self-test.json"
    temp.write_text(json.dumps(sample), encoding="utf-8")
    try:
        if check_contract(temp, "needle") != 2:
            fail("self-test assertion count mismatch")
        try:
            check_contract(temp, "needle forbidden")
        except ContractError:
            pass
        else:
            fail("self-test expected not_contains failure")
    finally:
        temp.unlink(missing_ok=True)
    print("KGG GPT regression contract self-test OK")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()
    try:
        self_test() if args.self_test else run_all()
        return 0
    except ContractError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
