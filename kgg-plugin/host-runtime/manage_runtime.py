"""Host-only KGG UI Lab runtime pointer operations.

Does not restart processes, change the ChatGPT tool catalog, or install a release.
The existing host launcher validates this same manifest before starting a process.
"""
from __future__ import annotations

import argparse
import contextlib
import hashlib
import io
import json
import os
from pathlib import Path
import re
import runpy
import sys
import time
from typing import Callable

ROOT = Path(r"C:\src\kgg-runtime\ui-lab")
SCHEMA = "kgg-ui-lab/active-runtime/v1"
APPROVED_CONTRACT = "0cc291eface08da646164bc0785b78f1800f6b201255ad0cf3d581c13973f071"
KEYS = frozenset(("schema", "release", "server_sha256", "server_version", "tool_contract_sha256"))
RELEASE = re.compile(r"[A-Za-z0-9][A-Za-z0-9._-]{0,79}\Z")
DIGEST = re.compile(r"[0-9a-f]{64}\Z")
SEMVER = re.compile(r"[0-9]+\.[0-9]+\.[0-9]+\Z")


class PromotionError(RuntimeError):
    pass


def sha(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def _validate_release(root: Path, name: str) -> Path:
    if not isinstance(name, str) or not RELEASE.fullmatch(name) or name in (".", ".."):
        raise PromotionError("invalid_release_name")
    folder = root / name
    if folder.is_symlink():
        raise PromotionError("release_symlink_forbidden")
    path = (folder / "mcp" / "server.py").resolve(strict=True)
    if not path.is_relative_to(root.resolve(strict=True)) or not path.is_file():
        raise PromotionError("release_path_outside_root")
    return path


def _read_manifest(root: Path, filename: str, contract: str) -> tuple[bytes, dict]:
    raw = (root / filename).read_bytes()
    if not raw or len(raw) > 4096:
        raise PromotionError("manifest_invalid_size")
    obj = json.loads(raw)
    if not isinstance(obj, dict) or set(obj) != KEYS or obj.get("schema") != SCHEMA:
        raise PromotionError("manifest_invalid_schema")
    if not isinstance(obj["server_sha256"], str) or not DIGEST.fullmatch(obj["server_sha256"]):
        raise PromotionError("manifest_invalid_server_sha")
    if obj["tool_contract_sha256"] != contract:
        raise PromotionError("manifest_contract_changed")
    _validate_release(root, obj["release"])
    if not isinstance(obj["server_version"], str) or not SEMVER.fullmatch(obj["server_version"]):
        raise PromotionError("manifest_invalid_version")
    return raw, obj


def verify(root: Path, manifest: dict, *, contract: str = APPROVED_CONTRACT) -> dict:
    """Fail closed on content, tool schema or version drift."""
    if not isinstance(manifest, dict) or set(manifest) != KEYS or manifest["schema"] != SCHEMA:
        raise PromotionError("manifest_invalid_schema")
    if manifest["tool_contract_sha256"] != contract:
        raise PromotionError("contract_not_approved")
    expected = manifest["server_sha256"]
    if not isinstance(expected, str) or not DIGEST.fullmatch(expected):
        raise PromotionError("invalid_pinned_hash")
    path = _validate_release(root, manifest["release"])
    if sha(path.read_bytes()) != expected:
        raise PromotionError("release_hash_mismatch")
    if not isinstance(manifest["server_version"], str) or not SEMVER.fullmatch(manifest["server_version"]):
        raise PromotionError("invalid_version")
    # Match the already-installed launcher: tool_catalog is evaluated from the
    # hash-pinned server and must not print to MCP protocol stdout.
    with contextlib.redirect_stdout(io.StringIO()) as captured:
        module = runpy.run_path(str(path), run_name="kgg_ui_lab_contract_preflight")
        tools = module["tool_catalog"]()
    if captured.getvalue():
        raise PromotionError("server_emitted_protocol_output")
    digest = sha(json.dumps(tools, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf8"))
    if digest != contract or module.get("SERVER_VERSION") != manifest["server_version"]:
        raise PromotionError("tool_contract_or_version_mismatch")
    if sha(path.read_bytes()) != expected:
        raise PromotionError("release_modified_during_validation")
    return manifest


def candidate(root: Path, name: str, expected_server_sha: str, *, contract: str = APPROVED_CONTRACT) -> dict:
    if not isinstance(expected_server_sha, str) or not DIGEST.fullmatch(expected_server_sha):
        raise PromotionError("candidate_hash_must_be_pinned")
    path = _validate_release(root, name)
    if sha(path.read_bytes()) != expected_server_sha:
        raise PromotionError("candidate_hash_mismatch")
    with contextlib.redirect_stdout(io.StringIO()) as captured:
        module = runpy.run_path(str(path), run_name="kgg_ui_lab_contract_preflight")
        catalog = module["tool_catalog"]()
    if captured.getvalue():
        raise PromotionError("candidate_protocol_stdout")
    version = module.get("SERVER_VERSION")
    if not isinstance(version, str) or not SEMVER.fullmatch(version):
        raise PromotionError("candidate_invalid_version")
    manifest = {"schema": SCHEMA, "release": name, "server_sha256": expected_server_sha,
                "server_version": version, "tool_contract_sha256": contract}
    verify(root, manifest, contract=contract)
    return manifest


def _write_atomic(root: Path, name: str, obj: dict) -> None:
    """Same-directory temp and os.replace; never overwrite a live release."""
    data = (json.dumps(obj, sort_keys=True, indent=2, ensure_ascii=False) + "\n").encode("utf8")
    tmp = root / (name + "." + str(os.getpid()) + ".pending")
    fd = os.open(tmp, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
    try:
        with os.fdopen(fd, "wb") as file:
            file.write(data)
            file.flush()
            os.fsync(file.fileno())
        os.replace(tmp, root / name)
    finally:
        if tmp.exists():
            tmp.unlink()


@contextlib.contextmanager
def _exclusive(root: Path):
    """Bounded exclusive lock. Existing Windows service stays untouched."""
    lockfile = root / ".runtime-promotion.lock"
    file = lockfile.open("a+b")
    try:
        file.seek(0)
        file.write(b"\0")
        file.flush()
        deadline = time.monotonic() + 2.0
        while True:
            try:
                if os.name == "nt":
                    import msvcrt
                    file.seek(0)
                    msvcrt.locking(file.fileno(), msvcrt.LK_NBLCK, 1)
                else:
                    import fcntl
                    fcntl.flock(file.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
                break
            except OSError:
                if time.monotonic() >= deadline:
                    raise PromotionError("runtime_update_busy")
                time.sleep(0.05)
        try:
            yield
        finally:
            if os.name == "nt":
                file.seek(0)
                msvcrt.locking(file.fileno(), msvcrt.LK_UNLCK, 1)
            else:
                fcntl.flock(file.fileno(), fcntl.LOCK_UN)
    finally:
        file.close()


def status(root: Path = ROOT, *, contract: str = APPROVED_CONTRACT) -> dict:
    _, cur = _read_manifest(root, "current.json", contract)
    verify(root, cur, contract=contract)
    return cur


def promote(
    name: str,
    pinned_server_sha: str,
    expected_active_sha: str,
    *,
    root: Path = ROOT,
    contract: str = APPROVED_CONTRACT,
    post_switch_check: Callable[[], None] | None = None,
) -> dict:
    """Compare-and-swap pointer; backup previous and restore on local failure.

    Does NOT claim live health; operator must restart/check the tunnel separately.
    """
    if not DIGEST.fullmatch(expected_active_sha):
        raise PromotionError("expected_active_sha_required")
    root = root.resolve(strict=True)
    with _exclusive(root):
        old_raw, previous = _read_manifest(root, "current.json", contract)
        if sha(old_raw) != expected_active_sha:
            raise PromotionError("active_pointer_changed")
        verify(root, previous, contract=contract)
        nxt = candidate(root, name, pinned_server_sha, contract=contract)
        if nxt == previous:
            return {"state": "UNCHANGED", "release": name, "active_sha": sha(old_raw)}
        _write_atomic(root, "previous.json", previous)
        try:
            _write_atomic(root, "current.json", nxt)
            verify(root, _read_manifest(root, "current.json", contract)[1], contract=contract)
            if post_switch_check:
                post_switch_check()
        except Exception:
            # The old manifest is independently revalidated before restoration.
            verify(root, previous, contract=contract)
            _write_atomic(root, "current.json", previous)
            raise
        return {"state": "POINTER_SWITCHED_NOT_RESTARTED",
                "release": name, "active_sha": sha((root / "current.json").read_bytes())}


def rollback(expected_active_sha: str, *, root: Path = ROOT, contract: str = APPROVED_CONTRACT) -> dict:
    if not DIGEST.fullmatch(expected_active_sha):
        raise PromotionError("expected_active_sha_required")
    root = root.resolve(strict=True)
    with _exclusive(root):
        current_raw, current = _read_manifest(root, "current.json", contract)
        if sha(current_raw) != expected_active_sha:
            raise PromotionError("active_pointer_changed")
        verify(root, current, contract=contract)
        _, previous = _read_manifest(root, "previous.json", contract)
        verify(root, previous, contract=contract)
        if current == previous:
            return {"state": "UNCHANGED", "release": current["release"], "active_sha": sha(current_raw)}
        # Preserve the rolled-back-from revision for potential diagnostics.
        _write_atomic(root, "current.json", previous)
        return {"state": "POINTER_ROLLED_BACK_NOT_RESTARTED", "release": previous["release"],
                "active_sha": sha((root / "current.json").read_bytes())}


def main() -> int:
    parser = argparse.ArgumentParser(description="KGG UI Lab offline runtime pointer management")
    parser.add_argument("operation", choices=("status", "verify-candidate", "promote", "rollback"))
    parser.add_argument("--release")
    parser.add_argument("--server-sha256")
    parser.add_argument("--expect-active-sha256")
    args = parser.parse_args()
    try:
        if args.operation == "status":
            result = {"state": "ACTIVE_VERIFIED", **status()}
            result["active_sha"] = sha((ROOT / "current.json").read_bytes())
        elif args.operation == "verify-candidate":
            result = candidate(ROOT, args.release, args.server_sha256)
        elif args.operation == "promote":
            result = promote(args.release, args.server_sha256, args.expect_active_sha256)
        else:
            result = rollback(args.expect_active_sha256)
        print(json.dumps(result, ensure_ascii=False, sort_keys=True))
        return 0
    except Exception as error:
        print(json.dumps({"state": "FAIL_CLOSED", "reason": str(error)}, ensure_ascii=False), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
