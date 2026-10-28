"""Behavior guards for the prospective symmetric grip capture contract."""
import copy
import importlib.util
import json
import os
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

    def test_rejects_mirrored_copy_instructions_or_geometric_friction_claim(self):
        changed = copy.deepcopy(self.contract)
        changed["coverage"]["pairing_rule"] = "Copy l observations into r."
        with self.assertRaisesRegex(ValueError, "independent suffix observations"):
            capture.validate_contract(changed)
        changed = copy.deepcopy(self.contract)
        changed["limitations"]["friction_or_slip_validation"] = "VALIDATED_FROM_GEOMETRY"
        with self.assertRaisesRegex(ValueError, "friction or slip"):
            capture.validate_contract(changed)

    def test_requires_declared_search_manifest_and_measurable_contact_semantics(self):
        changed = copy.deepcopy(self.contract)
        changed["evidence_schema"]["search_manifest_fields"] = [
            "manifest_id", "manifest_sha256", "object_id", "search_cells",
            "expected_unique_trial_keys"]
        with self.assertRaisesRegex(ValueError, "search manifest"):
            capture.validate_contract(changed)
        changed = copy.deepcopy(self.contract)
        changed["measurement_semantics"] = {
            "required_authored_digit_labels_NOT_anatomical_ids":
                ["thumb", "index", "middle", "ring", "little"],
            "minimum_samples_per_required_digit": 0,
            "point_coordinate_frame": "object_frame_4x4",
            "triangle_indexing": "zero_based_pinned_source_topology",
            "signed_separation_convention": "positive_separated_zero_touching_negative_penetration",
            "object_surface_normal_convention": "unit_outward_in_object_frame",
        }
        with self.assertRaisesRegex(ValueError, "per-digit contact geometry"):
            capture.validate_contract(changed)
        changed = copy.deepcopy(self.contract)
        changed["measurement_semantics"] = {
            "required_authored_digit_labels_NOT_anatomical_ids":
                ["thumb", "index", "middle", "ring", "little"],
            "minimum_samples_per_required_digit": 1,
            "point_coordinate_frame": "unspecified",
            "triangle_indexing": "zero_based_pinned_source_topology",
            "signed_separation_convention": "positive_separated_zero_touching_negative_penetration",
            "object_surface_normal_convention": "unit_outward_in_object_frame",
        }
        with self.assertRaisesRegex(ValueError, "contact geometry semantics"):
            capture.validate_contract(changed)

    def test_requires_exact_schema_and_research_metadata_types(self):
        for version in (True, 1.0):
            changed = copy.deepcopy(self.contract)
            changed["schema_version"] = version
            with self.subTest(version=version):
                with self.assertRaisesRegex(ValueError, "identity"):
                    capture.validate_contract(changed)
        changed = copy.deepcopy(self.contract)
        changed["research_basis"][0]["doi"] = True
        with self.assertRaisesRegex(ValueError, "research basis"):
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

    def test_writer_rejects_contract_or_model_aliases_without_truncating_them(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source_contract = root / "source-contract.json"
            source_contract.write_text(json.dumps(self.contract))
            model = root / "source.blend"
            model.write_bytes(b"immutable model")
            for link_type, target in (("contract", source_contract), ("model", model)):
                out = root / (link_type + "-out")
                out.mkdir()
                destination = out / "grip_capture_contract.json"
                if link_type == "contract":
                    destination.symlink_to(target)
                else:
                    os.link(target, destination)
                before = target.read_bytes()
                with self.subTest(link_type=link_type):
                    with self.assertRaisesRegex(ValueError, "outside and distinct"):
                        capture.write_report(self.contract, out, [source_contract, model])
                    self.assertEqual(target.read_bytes(), before)


if __name__ == "__main__":
    unittest.main()
