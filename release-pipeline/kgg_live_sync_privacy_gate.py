#!/usr/bin/env python3
"""Fail-closed production privacy approval gate for KGG Live-Sync."""

from __future__ import annotations

import json
import re
import sys
from datetime import date
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
APPROVAL_FILENAME = "kgg-live-sync-privacy-approval.local.json"
APPROVAL_PATH = ROOT / APPROVAL_FILENAME
EXPECTED_KEYS = frozenset(
    {
        "schemaVersion",
        "controllerApproved",
        "legalBasisDocumented",
        "processorDpaReviewed",
        "dpiaDecisionDocumented",
        "patientNoticeApproved",
        "incidentProcessDocumented",
        "approvedAt",
        "approvalReference",
    }
)
APPROVAL_FLAGS = frozenset(
    {
        "controllerApproved",
        "legalBasisDocumented",
        "processorDpaReviewed",
        "dpiaDecisionDocumented",
        "patientNoticeApproved",
        "incidentProcessDocumented",
    }
)
DATE_RE = re.compile(r"\A\d{4}-\d{2}-\d{2}\Z")
REFERENCE_RE = re.compile(r"\A[^\x00-\x1f\x7f-\x9f]{1,256}\Z")
PATIENT_DATA_RE = re.compile(
    r"(?:patient(?:en|in|innen)?|patient|name|geburt|adresse|diagnose|gesundheit|krankheit|"
    r"therap(?:ie|y|ist)|email|e-mail|telefon|phone|street|address|birth|medical|record)",
    re.IGNORECASE,
)


class PrivacyGateError(RuntimeError):
    """Raised whenever the fixed production approval contract is not met."""


def validate_approval_document(document: Any) -> dict[str, Any]:
    """Validate an isolated approval fixture without reading external state."""

    if not isinstance(document, dict):
        raise PrivacyGateError("approval document must be a JSON object")
    if set(document) != EXPECTED_KEYS:
        raise PrivacyGateError("approval document fields do not match the exact schema")
    if document.get("schemaVersion") != 1 or isinstance(document.get("schemaVersion"), bool):
        raise PrivacyGateError("schemaVersion must be 1")
    for field in APPROVAL_FLAGS:
        if document.get(field) is not True:
            raise PrivacyGateError(f"{field} must be true")
    approved_at = document.get("approvedAt")
    if not isinstance(approved_at, str) or not DATE_RE.fullmatch(approved_at):
        raise PrivacyGateError("approvedAt must use YYYY-MM-DD")
    try:
        date.fromisoformat(approved_at)
    except ValueError as exc:
        raise PrivacyGateError("approvedAt is not a valid calendar date") from exc
    reference = document.get("approvalReference")
    if not isinstance(reference, str) or reference != reference.strip() or not REFERENCE_RE.fullmatch(reference):
        raise PrivacyGateError("approvalReference must be a bounded non-empty reference")
    if PATIENT_DATA_RE.search(reference) or "@" in reference or re.search(r"\+?\d[\d ./()-]{6,}\d", reference):
        raise PrivacyGateError("approvalReference must not contain patient data")
    return dict(document)


def require_production_approval() -> dict[str, Any]:
    """Read only the ignored repository-root approval file and validate it."""

    try:
        raw = APPROVAL_PATH.read_text(encoding="utf-8")
    except (OSError, UnicodeError) as exc:
        raise PrivacyGateError(f"missing or unreadable {APPROVAL_FILENAME}") from exc
    try:
        document = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise PrivacyGateError(f"invalid JSON in {APPROVAL_FILENAME}") from exc
    return validate_approval_document(document)


def main(argv: list[str] | None = None) -> int:
    arguments = list(sys.argv[1:] if argv is None else argv)
    if arguments:
        print("ERROR: production privacy gate accepts no path, environment or bypass arguments", file=sys.stderr)
        return 1
    try:
        require_production_approval()
    except PrivacyGateError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
    print(json.dumps({"status": "PASS", "approvalFile": APPROVAL_FILENAME}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
