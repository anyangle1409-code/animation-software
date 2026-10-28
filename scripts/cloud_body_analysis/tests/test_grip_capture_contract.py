"""Behavior guards for the prospective symmetric grip capture contract."""
import copy
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
MODULE = ROOT / "grip_capture_contract.py"
CONTRACT = ROOT.parents[1] / "docs" / "anatomy" / "HGPT_GRIP_CAPTURE_CONTRACT_V1.json"
capture = None
if MODULE.exists():
    SPEC = importlib.util.spec_from_file_location("grip_capture_contract", MODULE)
    capture = importlib.util.module_from_spec(SPEC)
    SPEC.loader.exec_module(capture)


class GripCaptureContractTests(unittest.TestCase):
    def setUp(self):
        self.assertIsNotNone(capture, "grip_capture_contract module must implement the contract")
        self.contract = json.loads(CONTRACT.read_text())

    def test_valid_contract_requires_symmetric_coverage_without_anatomical_side_claim(self):
        report = capture.validate_contract(self.contract)
        self.assertEqual(report["status"],
                         "PROSPECTIVE_SYMMETRIC_GRIP_CAPTURE_CONTRACT_NOT_ACCEPTANCE")
        self.assertEqual(report["required_authored_runtime_suffixes"], ["l", "r"])
        self.assertEqual(report["pairing_key_fields"], ["object_id", "search_cell_id"])
        self.assertFalse(report["authored_suffix_is_anatomical_side"])
        self.assertFalse(report["native_search_executed"])
        self.assertFalse(report["grip_acceptance"])

    def test_rejects_missing_or_asymmetric_suffix_coverage(self):
        for suffixes in (["l"], ["r", "l"], ["l", "r", "r"]):
            changed = copy.deepcopy(self.contract)
            changed["coverage"]["required_authored_runtime_suffixes"] = suffixes
            with self.subTest(suffixes=suffixes):
                with self.assertRaisesRegex(ValueError, "exact authored suffix coverage"):
                    capture.validate_contract(changed)

    def test_rejects_invented_numeric_acceptance_thresholds(self):
        for field in ("self_intersection", "body_object_contact", "hand_collapse"):
            changed = copy.deepcopy(self.contract)
            changed["acceptance_thresholds"][field] = 5
            with self.subTest(field=field):
                with self.assertRaisesRegex(ValueError, "thresholds must remain undefined"):
                    capture.validate_contract(changed)

    def test_requires_object_frame_contact_geometry_and_return_residual_fields(self):
        cases = [
            ("object_evidence_fields", "object_frame_4x4"),
            ("contact_sample_fields", "signed_surface_separation_m"),
            ("per_trial_observation_fields", "returned_state_residual"),
        ]
        for section, missing in cases:
            changed = copy.deepcopy(self.contract)
            changed["evidence_schema"][section].remove(missing)
            with self.subTest(section=section, missing=missing):
                with self.assertRaisesRegex(ValueError, "required evidence fields"):
                    capture.validate_contract(changed)

    def test_geometric_capture_cannot_claim_force_pressure_or_contact_acceptance(self):
        changed = copy.deepcopy(self.contract)
        changed["limitations"]["force_or_pressure_measurement"] = "MEASURED"
        with self.assertRaisesRegex(ValueError, "force or pressure"):
            capture.validate_contract(changed)
        changed = copy.deepcopy(self.contract)
        changed["limitations"]["contact_acceptance"] = True
        with self.assertRaisesRegex(ValueError, "contact acceptance"):
            capture.validate_contract(changed)

    def test_cli_writes_phone_readable_contract_report(self):
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp)
            report = capture.write_report(self.contract, out)
            self.assertEqual(json.loads((out / "grip_capture_contract.json").read_text()),
                             report)
            markdown = (out / "grip_capture_contract.md").read_text()
            self.assertIn("No native grip search executed", markdown)
            self.assertIn("Object/contact evidence required", markdown)
            self.assertNotIn("anatomically approved", markdown.lower())


if __name__ == "__main__":
    unittest.main()
