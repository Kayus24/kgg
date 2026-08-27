import importlib.util
import sys
import unittest
from pathlib import Path


HERE = Path(__file__).resolve().parent
SPEC = importlib.util.spec_from_file_location("kgg_live_sync_privacy_gate", HERE / "kgg_live_sync_privacy_gate.py")
gate = importlib.util.module_from_spec(SPEC)
assert SPEC.loader
SPEC.loader.exec_module(gate)


def valid_document() -> dict:
    return {
        "schemaVersion": 1,
        "controllerApproved": True,
        "legalBasisDocumented": True,
        "processorDpaReviewed": True,
        "dpiaDecisionDocumented": True,
        "patientNoticeApproved": True,
        "incidentProcessDocumented": True,
        "approvedAt": "2026-08-25",
        "approvalReference": "DPA-2026-08",
    }


class LiveSyncPrivacyGateTests(unittest.TestCase):
    def test_exact_valid_schema(self):
        self.assertEqual(gate.validate_approval_document(valid_document())["schemaVersion"], 1)

    def test_all_required_flags_must_be_true(self):
        for field in gate.APPROVAL_FLAGS:
            with self.subTest(field=field):
                document = valid_document()
                document[field] = False
                with self.assertRaises(gate.PrivacyGateError):
                    gate.validate_approval_document(document)

    def test_exact_schema_rejects_extra_or_missing_fields(self):
        extra = valid_document()
        extra["bypass"] = True
        with self.assertRaises(gate.PrivacyGateError):
            gate.validate_approval_document(extra)
        missing = valid_document()
        del missing["approvalReference"]
        with self.assertRaises(gate.PrivacyGateError):
            gate.validate_approval_document(missing)

    def test_date_and_reference_are_bounded_and_non_phi(self):
        for value in ("2026-02-30", "2026/08/25", "2026-8-25"):
            with self.subTest(value=value):
                document = valid_document()
                document["approvedAt"] = value
                with self.assertRaises(gate.PrivacyGateError):
                    gate.validate_approval_document(document)
        for value in ("", "Patient-Akte-42", "approval@example.invalid", " +49 123 456789"):
            with self.subTest(value=value):
                document = valid_document()
                document["approvalReference"] = value
                with self.assertRaises(gate.PrivacyGateError):
                    gate.validate_approval_document(document)

    def test_production_entrypoint_has_no_alternate_argument_path(self):
        self.assertEqual(gate.main(["--approval", "other.json"]), 1)

    def test_missing_fixed_production_file_fails_closed(self):
        if gate.APPROVAL_PATH.exists():
            self.skipTest("local approval file is intentionally present outside the test fixture")
        with self.assertRaises(gate.PrivacyGateError):
            gate.require_production_approval()


if __name__ == "__main__":
    unittest.main()
