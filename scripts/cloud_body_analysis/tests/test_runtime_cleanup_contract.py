"""Evidence-gated W8 runtime corrective cleanup contract tests."""
import copy
import importlib.util
import io
import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
PROBE_PATH = ROOT.parent / "phone_blender" / "pose_state_probe.py"
PROBE_SPEC = importlib.util.spec_from_file_location("cleanup_contract_pose_probe", PROBE_PATH)
probe = importlib.util.module_from_spec(PROBE_SPEC)
PROBE_SPEC.loader.exec_module(probe)

CONTRACT_PATH = ROOT / "runtime_cleanup_contract.py"
contract = None
if CONTRACT_PATH.exists():
    CONTRACT_SPEC = importlib.util.spec_from_file_location(
        "runtime_cleanup_contract", CONTRACT_PATH)
    contract = importlib.util.module_from_spec(CONTRACT_SPEC)
    CONTRACT_SPEC.loader.exec_module(contract)

POSE_TEST_PATH = Path(__file__).with_name("test_pose_state_probe.py")
POSE_TEST_SPEC = importlib.util.spec_from_file_location(
    "cleanup_contract_pose_fixture", POSE_TEST_PATH)
pose_test = importlib.util.module_from_spec(POSE_TEST_SPEC)
POSE_TEST_SPEC.loader.exec_module(pose_test)


class RuntimeCleanupContractTests(unittest.TestCase):
    def setUp(self):
        self.assertIsNotNone(
            contract, "runtime_cleanup_contract module must implement the evidence contract")
        self.report = pose_test.mock_report()
        terminal_names = {
            "HGPT_S1_SHOULDER": [
                "HGPT_S1_SHOULDER_l_145", "HGPT_S1_SHOULDER_l_160",
                "HGPT_S1_SHOULDER_r_145", "HGPT_S1_SHOULDER_r_160"],
            "HGPT_S3_SHAPE": [
                "HGPT_S3_SHAPE_l_125", "HGPT_S3_SHAPE_r_125"],
            "HGPT_S5_BAKE": [
                "HGPT_S5_BAKE_l_145", "HGPT_S5_BAKE_l_160",
                "HGPT_S5_BAKE_r_145", "HGPT_S5_BAKE_r_160"],
            "HGPT_S7_DELT": [
                "HGPT_S7_DELT_l_156", "HGPT_S7_DELT_l_166",
                "HGPT_S7_DELT_r_156", "HGPT_S7_DELT_r_166"],
        }
        self.report["post_benchmark_return_to_start_state"][
            "active_nonbasis_shape_keys"] = [
                {"name": name, "actual_value": 1.0, "mute": False}
                for names in terminal_names.values() for name in names]
        residual = {
            "vertex_count": 2, "max_vertex_displacement_m": 0.0,
            "rms_vertex_displacement_m": 0.0, "vertices_moved_gt_1e_9_m": 0,
        }
        self.report["terminal_corrective_key_clear_attribution"]["trials"] = [
            {"family": family, "cleared_key_names": names,
             "residual_to_benchmark_reference": dict(residual),
             "displacement_from_observed_terminal": dict(residual)}
            for family, names in terminal_names.items()
        ]
        for row in self.report["terminal_s3_individual_key_diagnostic"]["keys"]:
            for field in (
                "stored_coordinate_delta_to_relative_key",
                "individual_clear_displacement_from_observed_terminal",
            ):
                row[field].update({
                    "max_vertex_displacement_m": 0.0,
                    "rms_vertex_displacement_m": 0.0,
                    "vertices_moved_gt_1e_9_m": 0,
                })
        self.evidence = {
            "workflow_run_id": 40374313339,
            "artifact_id": 12673313863,
            "artifact_sha256": "129ecc9bc07544e7f3bc0954cb12a531c90eb4e650ea03aa529c6d24db9cd4c2",
            "report_sha256": "2eb9888735444b6ba50282087eb48d0dff43604885e64c97ec0a0995a2c9035e",
        }

    def test_builds_non_mutating_contract_from_failed_reset_and_exact_clear(self):
        result = contract.build_contract(self.report, self.evidence)
        self.assertEqual(
            result["status"],
            "MEASURED_W8_RUNTIME_CORRECTIVE_CLEANUP_CONTRACT_NOT_MODEL_REPAIR")
        self.assertTrue(result["trigger"]["skeleton_reset_alone_insufficient"])
        self.assertEqual(result["trigger"]["vertices_moved_gt_1e_9_m"], 1)
        self.assertEqual(
            result["tested_cleanup_operation"],
            "RESET_SKELETON_AND_ZERO_ALL_NONBASIS_KEY_VALUES_IN_MEMORY")
        self.assertTrue(result["postconditions"]["benchmark_reference_geometry_exact"])
        self.assertEqual(result["postconditions"]["active_nonbasis_shape_keys"], [])
        self.assertEqual(
            list(result["terminal_active_key_partition"]),
            ["HGPT_S1_SHOULDER", "HGPT_S3_SHAPE", "HGPT_S5_BAKE", "HGPT_S7_DELT"])
        self.assertFalse(result["claims"]["anatomical_neutral"])
        self.assertFalse(result["claims"]["model_repair"])
        self.assertFalse(result["claims"]["selective_family_disable_authorized"])

    def test_requires_observed_skeleton_only_reset_failure(self):
        report = copy.deepcopy(self.report)
        returned = report["post_benchmark_return_to_start_state"]
        returned.update({
            "runtime_state_restored_exactly": True,
            "max_vertex_displacement_m": 0.0,
            "rms_vertex_displacement_m": 0.0,
            "vertices_moved_gt_1e_9_m": 0,
            "active_nonbasis_shape_keys": [],
        })
        report["terminal_corrective_key_clear_attribution"]["trials"] = []
        with self.assertRaisesRegex(ValueError, "skeleton-only reset failure"):
            contract.build_contract(report, self.evidence)

    def test_requires_exact_explicit_clear_and_full_terminal_partition(self):
        report = copy.deepcopy(self.report)
        cleared = report["explicit_key_clear_experiment"]
        cleared.update({
            "runtime_state_restored_exactly": False,
            "max_vertex_displacement_m": 0.001,
            "rms_vertex_displacement_m": 0.001,
            "vertices_moved_gt_1e_9_m": 1,
        })
        with self.assertRaisesRegex(ValueError, "exact explicit cleanup"):
            contract.build_contract(report, self.evidence)

        report = copy.deepcopy(self.report)
        cleared = report["explicit_key_clear_experiment"]
        cleared["runtime_state_restored_exactly"] = False
        cleared["skeletal_pose_signature_restored_exactly"] = False
        with self.assertRaisesRegex(ValueError, "exact explicit cleanup"):
            contract.build_contract(report, self.evidence)

        report = copy.deepcopy(self.report)
        cleared = report["explicit_key_clear_experiment"]
        cleared["runtime_state_restored_exactly"] = False
        cleared["active_nonbasis_shape_keys"] = [
            {"name": "HGPT_S7_DELT_l_156", "actual_value": 0.5, "mute": False}]
        with self.assertRaisesRegex(ValueError, "exact explicit cleanup"):
            contract.build_contract(report, self.evidence)

        report = copy.deepcopy(self.report)
        report["terminal_corrective_key_clear_attribution"]["trials"].pop()
        with self.assertRaisesRegex(ValueError, "pose report invalid"):
            contract.build_contract(report, self.evidence)

    def test_s3_noop_claim_requires_zero_stored_and_evaluated_effects(self):
        for field in (
            "stored_coordinate_delta_to_relative_key",
            "individual_clear_displacement_from_observed_terminal",
        ):
            with self.subTest(field=field):
                report = copy.deepcopy(self.report)
                residual = report["terminal_s3_individual_key_diagnostic"]["keys"][0][field]
                residual.update({
                    "max_vertex_displacement_m": 0.001,
                    "rms_vertex_displacement_m": 0.001,
                    "vertices_moved_gt_1e_9_m": 1,
                })
                with self.assertRaisesRegex(ValueError, "S3 numeric-noop evidence"):
                    contract.build_contract(report, self.evidence)

    def test_rejects_unverified_evidence_metadata(self):
        for field, value in (
            ("workflow_run_id", True),
            ("artifact_id", 0),
            ("artifact_sha256", "not-a-sha"),
            ("report_sha256", "0" * 63),
        ):
            with self.subTest(field=field):
                evidence = dict(self.evidence)
                evidence[field] = value
                with self.assertRaisesRegex(ValueError, "evidence metadata"):
                    contract.build_contract(self.report, evidence)

    def test_cli_hashes_input_report_and_writes_phone_readable_outputs(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            report_path = root / "pose.json"
            report_path.write_text(json.dumps(self.report) + "\n", encoding="utf-8")
            evidence = dict(self.evidence)
            evidence["report_sha256"] = contract.digest(report_path)
            json_path = root / "contract.json"
            markdown_path = root / "contract.md"
            contract.run(report_path, json_path, markdown_path, evidence)
            output = json.loads(json_path.read_text(encoding="utf-8"))
            markdown = markdown_path.read_text(encoding="utf-8")
            self.assertEqual(output["evidence"], evidence)
            self.assertIn("Skeleton reset alone", markdown)
            self.assertIn("not anatomical neutral", markdown.lower())
            self.assertIn("S3", markdown)

    def test_run_rejects_input_and_output_path_aliases_before_writing(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            report_path = root / "pose.json"
            report_path.write_text(json.dumps(self.report) + "\n", encoding="utf-8")
            evidence = dict(self.evidence)
            evidence["report_sha256"] = contract.digest(report_path)
            hardlink = root / "pose-hardlink.json"
            os.link(report_path, hardlink)
            symlink = root / "pose-symlink.json"
            symlink.symlink_to(report_path)
            for json_path, markdown_path in (
                (report_path, root / "out.md"),
                (hardlink, root / "out.md"),
                (symlink, root / "out.md"),
                (root / "same", root / "same"),
            ):
                with self.subTest(json_path=json_path, markdown_path=markdown_path):
                    before = report_path.read_bytes()
                    with self.assertRaisesRegex(ValueError, "distinct paths"):
                        contract.run(report_path, json_path, markdown_path, evidence)
                    self.assertEqual(report_path.read_bytes(), before)

    def test_run_hashes_and_parses_one_byte_snapshot(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            report_path = root / "pose.json"
            good = (json.dumps(self.report) + "\n").encode()
            report_path.write_bytes(good)
            evidence = dict(self.evidence)
            evidence["report_sha256"] = contract.hash_bytes(good)
            json_path = root / "contract.json"
            markdown_path = root / "contract.md"
            original_open = Path.open
            report_reads = 0

            def controlled_open(path, *args, **kwargs):
                nonlocal report_reads
                mode = args[0] if args else kwargs.get("mode", "r")
                if path == report_path and "r" in mode:
                    report_reads += 1
                    if report_reads == 1:
                        return io.BytesIO(good)
                    return io.StringIO("{}")
                return original_open(path, *args, **kwargs)

            with mock.patch.object(Path, "open", controlled_open):
                contract.run(report_path, json_path, markdown_path, evidence)
            self.assertEqual(report_reads, 1)
            self.assertEqual(
                json.loads(json_path.read_text(encoding="utf-8"))["status"],
                "MEASURED_W8_RUNTIME_CORRECTIVE_CLEANUP_CONTRACT_NOT_MODEL_REPAIR")


if __name__ == "__main__":
    unittest.main()
