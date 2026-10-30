"""Synthetic contract tests for the read-only native W8 forearm probe."""
import copy
import importlib.util
import math
from pathlib import Path
import tempfile
import unittest

MODULE = Path(__file__).resolve().parents[2] / "phone_blender" / "forearm_pose_state_probe.py"
SPEC = importlib.util.spec_from_file_location("forearm_pose_state_probe", MODULE)
probe = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(probe)


def control(mode, angle, quaternion=None, x=0.1):
    if quaternion is None:
        half = math.radians(angle) / 2.0
        quaternion = (math.cos(half), math.sin(half), 0.0, 0.0)
    return {
        "control_present": True,
        "pose_rotation_mode": mode,
        "matrix_basis_quaternion_wxyz": list(quaternion),
        "local_delta_angle_deg_not_anatomical": angle,
        "head_world_m_not_anatomical_joint_centre": [x, 0.0, 1.0],
        "tail_world_m": [x, 0.0, 0.7],
    }


def report():
    pronation_mean, supination_mean = 80.0, 85.0
    samples = []
    for sample in range(9):
        t = sample / 8.0
        target = probe.authored_target_deg(t, pronation_mean, supination_mean)
        forearm_angle = math.hypot(90.0, target)
        samples.append({
            "sample": sample,
            "t": t,
            "authored_target_deg_not_isb": target,
            "benchmark_angles_deg_population_means_not_limits": {
                "elbow_flexion": 90.0,
                "forearm_pronation": max(target, 0.0),
                "forearm_supination": max(-target, 0.0),
            },
            "evaluated_forearm_skin": {
                "minimum_slice_radius_ratio_l": 1.0 - 0.01 * sample,
                "minimum_slice_radius_ratio_r": 1.0 - 0.01 * sample,
                "anatomical_tissue_safety_claimed": False,
            },
            "sides": {
                side: {
                    "forearm": control("YXZ", forearm_angle, x=x),
                    "forearm_tw0": control("QUATERNION", abs(target), x=x),
                    "forearm_tw1": control("QUATERNION", abs(target) / 2.0, x=x),
                    "hand": control("XYZ", 0.0, x=x),
                } for side, x in (("l", -0.1), ("r", 0.1))
            },
        })
    return {
        "status": "READ_ONLY_AUTHORED_FOREARM_CONTROL_PATH_ANATOMY_NOT_APPROVED",
        "evidence_kind": "NATIVE_PINNED_MODEL_OBSERVATION",
        "synthetic_test_fixture": False,
        "model": "W8",
        "source_sha256": probe.W8_SHA256,
        "pinned_r57_source_commit": probe.R57_SHA,
        "source_unchanged": True,
        "saved_blend": False,
        "rest_bone_signature_unchanged": True,
        "authored_suffixes_not_anatomical_laterality": ["l", "r"],
        "separate_radius_ulna_controls_observed": False,
        "anatomical_joint_coordinate_system_verified": False,
        "pronation_supination_approved": False,
        "return_to_neutral_tested": False,
        "population_means_deg_not_limits": {
            "forearm_pronation": pronation_mean,
            "forearm_supination": supination_mean,
        },
        "samples": samples,
        "limitations": list(probe.REQUIRED_LIMITATIONS),
    }


class ForearmPoseStateProbeTests(unittest.TestCase):
    def test_valid_native_report_contract(self):
        self.assertEqual(probe.validate_report(report()), [])

    def test_authored_target_path_is_hand_derived_and_reverses(self):
        actual = [probe.authored_target_deg(i / 8, 80.0, 85.0) for i in range(9)]
        self.assertEqual(actual, [0.0, 12.5, 40.0, 67.5, 80.0,
                                  54.21875, -2.5, -59.21875, -85.0])

    def test_quaternion_distance_is_sign_invariant(self):
        q = [0.9238795325, 0.0, 0.3826834324, 0.0]
        self.assertAlmostEqual(probe.quaternion_distance_deg(q, [-v for v in q]), 0.0)
        self.assertAlmostEqual(probe.quaternion_distance_deg([1, 0, 0, 0], q), 45.0,
                               places=7)

    def test_rejects_tampered_target_or_sample_sequence(self):
        data = report()
        data["samples"][5]["authored_target_deg_not_isb"] += 1.0
        self.assertIn("authored target drift", probe.validate_report(data))
        data = report()
        data["samples"][3]["sample"] = 2
        self.assertIn("samples 0 through 8 required", probe.validate_report(data))

    def test_rejects_wrong_source_or_evidence_classification(self):
        data = report(); data["source_sha256"] = "0" * 64
        self.assertIn("invalid evidence scope", probe.validate_report(data))
        data = report(); data["synthetic_test_fixture"] = True
        self.assertIn("invalid evidence scope", probe.validate_report(data))

    def test_rejects_radius_ulna_or_anatomical_approval_claims(self):
        for field in ("separate_radius_ulna_controls_observed",
                      "anatomical_joint_coordinate_system_verified",
                      "pronation_supination_approved", "return_to_neutral_tested"):
            data = report(); data[field] = True
            self.assertIn("invalid evidence scope", probe.validate_report(data), field)

    def test_rejects_missing_limitation(self):
        data = report(); data["limitations"].pop()
        self.assertIn("missing required limitations", probe.validate_report(data))

    def test_rejects_nonfinite_and_wrong_control_modes(self):
        data = report()
        data["samples"][2]["sides"]["l"]["forearm_tw1"][
            "local_delta_angle_deg_not_anatomical"] = float("nan")
        self.assertIn("invalid control observation", probe.validate_report(data))
        data = report()
        data["samples"][2]["sides"]["r"]["forearm"]["pose_rotation_mode"] = "XYZ"
        self.assertIn("invalid control observation", probe.validate_report(data))

    def test_rejects_malformed_nested_mappings_without_crashing(self):
        mutations = []
        data = report(); data["samples"][0]["sides"] = [] ; mutations.append(data)
        data = report(); data["samples"][0]["sides"]["l"] = None; mutations.append(data)
        data = report(); data["samples"][0]["evaluated_forearm_skin"] = "bad"; mutations.append(data)
        data = report(); data["population_means_deg_not_limits"] = None; mutations.append(data)
        for data in mutations:
            errors = probe.validate_report(data)
            self.assertTrue(errors)

    def test_rejects_benchmark_angle_or_skin_metric_drift(self):
        data = report()
        data["samples"][4]["benchmark_angles_deg_population_means_not_limits"][
            "forearm_pronation"] = 79.0
        self.assertIn("benchmark angle mismatch", probe.validate_report(data))
        data = report()
        data["samples"][4]["evaluated_forearm_skin"][
            "minimum_slice_radius_ratio_l"] = False
        self.assertIn("invalid evaluated forearm skin observation",
                      probe.validate_report(data))

    def test_rejects_quaternion_magnitude_inconsistency(self):
        data = report()
        data["samples"][8]["sides"]["l"]["forearm_tw0"][
            "matrix_basis_quaternion_wxyz"] = [1.0, 0.0, 0.0, 0.0]
        self.assertIn("control quaternion/angle mismatch", probe.validate_report(data))

    def test_extreme_finite_numbers_return_errors_instead_of_raising(self):
        data = report()
        data["samples"][1]["sides"]["r"]["forearm_tw0"][
            "matrix_basis_quaternion_wxyz"] = [1e308] * 4
        self.assertTrue(probe.validate_report(data))
        data = report()
        data["samples"][1]["t"] = 10 ** 1000
        self.assertTrue(probe.validate_report(data))

    def test_r57_root_without_pinned_revision_is_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaisesRegex(ValueError, "r57 revision"):
                probe.verify_r57_root(Path(tmp))


if __name__ == "__main__":
    unittest.main()
