"""Pure Python W8 shoulder pose report guards; no Blender import needed."""
import copy
import importlib.util
from pathlib import Path
from types import SimpleNamespace as NS
import unittest

MODULE = Path(__file__).resolve().parents[2] / "phone_blender" / "pose_state_probe.py"
SPEC = importlib.util.spec_from_file_location("pose_state_probe", MODULE)
probe = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(probe)

def mock_report():
    return {
        "status": "READ_ONLY_IN_MEMORY_POSE_STATE_ANATOMY_NOT_APPROVED",
        "model": "W8", "source_sha256": probe.W8_SHA256,
        "saved_blend": False, "source_unchanged": True,
        "anatomical_approval": "NOT_GRANTED",
        "quality_approval": "NOT_GRANTED",
        "post_benchmark_return_to_start_state": {
            "status": "MEASURED_RUNTIME_RETURN_NOT_ANATOMICAL_NEUTRAL",
            "anatomical_neutral_claimed": False,
            "runtime_state_restored_exactly": False,
            "vertex_count": 2,
            "max_vertex_displacement_m": 0.002,
            "rms_vertex_displacement_m": 0.001,
            "vertices_moved_gt_1e_9_m": 1,
            "active_nonbasis_shape_keys": [
                {"name": "HGPT_S7_DELT_l_156", "actual_value": 0.5}],
            "skeletal_pose_signature_restored_exactly": True,
        },
        "reverse_press_trajectory": {
            "status": "MEASURED_REVERSE_REPLAY_NOT_PHYSIOLOGICAL_RETURN",
            "physiological_return_claimed": False,
            "retraced_forward_samples_exactly": True,
            "samples": [{
                "sample": i,
                "vertex_count": 2,
                "max_vertex_displacement_m": 0.0,
                "rms_vertex_displacement_m": 0.0,
                "vertices_moved_gt_1e_9_m": 0,
            } for i in range(8, -1, -1)],
        },
        "explicit_key_clear_experiment": {
            "status": "EXPLICIT_IN_MEMORY_CLEAR_EXPERIMENT_NOT_MODEL_REPAIR",
            "anatomical_neutral_claimed": False,
            "model_repair_claimed": False,
            "runtime_state_restored_exactly": True,
            "vertex_count": 2,
            "max_vertex_displacement_m": 0.0,
            "rms_vertex_displacement_m": 0.0,
            "vertices_moved_gt_1e_9_m": 0,
            "active_nonbasis_shape_keys": [],
            "skeletal_pose_signature_restored_exactly": True,
        },
        "terminal_corrective_key_clear_attribution": {
            "status": "READ_ONLY_RUNTIME_KEY_CLEAR_ATTRIBUTION_NOT_REPAIR",
            "model_repair_claimed": False,
            "skeletal_skinning_causality_claimed": False,
            "terminal_state_restored_after_trials_exactly": True,
            "trials": [{
                "family": "HGPT_S7_DELT",
                "cleared_key_names": ["HGPT_S7_DELT_l_156"],
                "residual_to_benchmark_reference": {
                    "vertex_count": 2,
                    "max_vertex_displacement_m": 0.0,
                    "rms_vertex_displacement_m": 0.0,
                    "vertices_moved_gt_1e_9_m": 0,
                },
                "displacement_from_observed_terminal": {
                    "vertex_count": 2,
                    "max_vertex_displacement_m": 0.0,
                    "rms_vertex_displacement_m": 0.0,
                    "vertices_moved_gt_1e_9_m": 0,
                },
            }],
        },
        "samples": [{
            "sample": i,
            "authored_press_ht_target_deg_NOT_measured": 90 + 70 * i / 8,
            "sides": {side: {
                "humerothoracic_elevation_measured_by_pinned_driver_deg": 90.0,
                "actual_shape_key_values": [{"name": "HGPT_S7_DELT_" + side + "_156", "actual_value": 0.5}],
            } for side in ("l", "r")},
        } for i in range(9)],
    }

class ShoulderPoseProbeTests(unittest.TestCase):
    def test_valid_mock_does_not_grant_approval(self):
        self.assertEqual(probe.validate_report(mock_report()), [])

    def test_source_hash_and_metadata_fail_closed(self):
        d = mock_report()
        d["source_sha256"] = "not original W8"
        self.assertIn("unrecognised immutable source", probe.validate_report(d))
        d = mock_report()
        d["saved_blend"] = True
        self.assertIn("source preservation not demonstrated", probe.validate_report(d))

    def test_require_nine_samples_and_both_sides(self):
        d = mock_report()
        d["samples"].pop()
        self.assertIn("nine exact pose samples required", probe.validate_report(d))
        d = mock_report()
        d["samples"][1]["sides"].pop("r")
        self.assertIn("both runtime suffix sides required", probe.validate_report(d))

    def test_reject_nonfinite_measurement_and_activation(self):
        d = mock_report()
        d["samples"][0]["sides"]["l"]["humerothoracic_elevation_measured_by_pinned_driver_deg"] = float("nan")
        self.assertIn("missing actual measured elevation", probe.validate_report(d))
        d = mock_report()
        d["samples"][5]["sides"]["r"]["actual_shape_key_values"][0]["actual_value"] = float("inf")
        self.assertIn("invalid shape key activation", probe.validate_report(d))

    def test_actual_shape_key_range_and_semantics(self):
        d = mock_report()
        d["samples"][2]["sides"]["l"]["actual_shape_key_values"][0]["actual_value"] = 1.2
        self.assertIn("invalid shape key activation", probe.validate_report(d))
        d = mock_report()
        d["samples"][2]["sides"]["l"]["actual_shape_key_values"][0]["name"] = "HGPT_S5_BAKE_l_120"
        self.assertIn("missing S7 driver channel", probe.validate_report(d))

    def test_extract_actual_key_value_without_rewriting(self):
        keys = [NS(name="Basis", value=0),
                NS(name="HGPT_S7_DELT_l_156", value=0.4),
                NS(name="HGPT_S5_BAKE_r_160", value=0.75),
                NS(name="HGPT_S1_SHOULDER_l_105", value=0.3)]
        body = NS(data=NS(shape_keys=NS(key_blocks=keys)))
        output = probe.shape_key_state(body, "l")
        self.assertEqual(len(output), 2)
        self.assertEqual(output[0]["name"], "HGPT_S1_SHOULDER_l_105")
        self.assertEqual(output[1]["actual_value"], 0.4)
        self.assertEqual(keys[1].value, 0.4)

    def test_records_actual_k1_elbow_activation_separately_by_suffix(self):
        keys = [NS(name="Basis", value=0),
                NS(name="HGPT_K1_ELBOW_l_90", value=0.37),
                NS(name="HGPT_K1_ELBOW_r_90", value=0.72)]
        body = NS(data=NS(shape_keys=NS(key_blocks=keys)))
        self.assertEqual(probe.shape_key_state(body, "l"),
                         [{"name": "HGPT_K1_ELBOW_l_90", "actual_value": 0.37}])
        self.assertEqual(keys[1].value, 0.37)

    def test_quantified_target_separate_from_measured_angle(self):
        d = mock_report()
        d["samples"][8]["sides"]["l"]["humerothoracic_elevation_measured_by_pinned_driver_deg"] = 149.0
        self.assertEqual(probe.validate_report(d), [])
        self.assertEqual(d["samples"][8]["authored_press_ht_target_deg_NOT_measured"], 160.0)
        self.assertEqual(d["samples"][8]["sides"]["l"]["humerothoracic_elevation_measured_by_pinned_driver_deg"], 149.0)

    def test_return_state_summary_distinguishes_exact_start_from_anatomical_neutral(self):
        self.assertTrue(hasattr(probe, "return_state_summary"))
        result = probe.return_state_summary(
            [(0, 0, 0), (1, 2, 3)], [(0, 0, 0), (1, 2, 3)], [], True)
        self.assertEqual(result["status"], "MEASURED_RUNTIME_RETURN_NOT_ANATOMICAL_NEUTRAL")
        self.assertFalse(result["anatomical_neutral_claimed"])
        self.assertTrue(result["runtime_state_restored_exactly"])
        self.assertEqual(result["max_vertex_displacement_m"], 0.0)

    def test_return_state_summary_reports_geometry_keys_and_pose_residuals(self):
        result = probe.return_state_summary(
            [(0, 0, 0), (1, 0, 0)], [(0, 0, 0), (1, 0.003, 0)],
            [{"name": "HGPT_S7_DELT_l_156", "actual_value": 0.25}], False)
        self.assertAlmostEqual(result["max_vertex_displacement_m"], 0.003)
        self.assertAlmostEqual(result["rms_vertex_displacement_m"],
                               (0.003**2 / 2) ** 0.5)
        self.assertEqual(result["vertices_moved_gt_1e_9_m"], 1)
        self.assertFalse(result["runtime_state_restored_exactly"])

    def test_return_state_summary_rejects_changed_topology_and_nonfinite_data(self):
        with self.assertRaisesRegex(ValueError, "vertex count"):
            probe.return_state_summary([(0, 0, 0)], [], [], True)
        with self.assertRaisesRegex(ValueError, "Nonfinite"):
            probe.return_state_summary([(0, 0, 0)], [(float("nan"), 0, 0)], [], True)

    def test_reverse_trajectory_summary_is_geometric_not_physiological(self):
        forward = {i: [(0, 0, 0), (i, 0, 0)] for i in range(9)}
        reverse = {i: list(vertices) for i, vertices in forward.items()}
        result = probe.reverse_trajectory_summary(forward, reverse)
        self.assertEqual(result["status"], "MEASURED_REVERSE_REPLAY_NOT_PHYSIOLOGICAL_RETURN")
        self.assertFalse(result["physiological_return_claimed"])
        self.assertTrue(result["retraced_forward_samples_exactly"])
        self.assertEqual([row["sample"] for row in result["samples"]], list(range(8, -1, -1)))

    def test_reverse_trajectory_summary_reports_residual_and_rejects_missing_sample(self):
        forward = {i: [(0, 0, 0)] for i in range(9)}
        reverse = {i: [(0, 0, 0)] for i in range(9)}
        reverse[3] = [(0, 0.002, 0)]
        result = probe.reverse_trajectory_summary(forward, reverse)
        self.assertFalse(result["retraced_forward_samples_exactly"])
        self.assertAlmostEqual(result["samples"][5]["max_vertex_displacement_m"], 0.002)
        del reverse[4]
        with self.assertRaisesRegex(ValueError, "samples 0 through 8"):
            probe.reverse_trajectory_summary(forward, reverse)

    def test_explicit_clear_summary_is_not_a_repair_or_neutral_claim(self):
        result = probe.explicit_clear_summary(
            [(0, 0, 0)], [(0, 0, 0)], [], True)
        self.assertEqual(result["status"], "EXPLICIT_IN_MEMORY_CLEAR_EXPERIMENT_NOT_MODEL_REPAIR")
        self.assertFalse(result["model_repair_claimed"])
        self.assertFalse(result["anatomical_neutral_claimed"])
        self.assertTrue(result["runtime_state_restored_exactly"])

    def test_terminal_key_clear_attribution_reports_family_residuals(self):
        result = probe.terminal_key_clear_attribution_summary(
            [(0, 0, 0)], [(0, 0.002, 0)],
            [{"family": "HGPT_S7_DELT",
              "cleared_key_names": ["HGPT_S7_DELT_l_156"],
              "vertices": [(0, 0.001, 0)]}], True)
        self.assertEqual(result["status"], "READ_ONLY_RUNTIME_KEY_CLEAR_ATTRIBUTION_NOT_REPAIR")
        self.assertFalse(result["model_repair_claimed"])
        self.assertFalse(result["skeletal_skinning_causality_claimed"])
        self.assertAlmostEqual(result["trials"][0]["residual_to_benchmark_reference"]["max_vertex_displacement_m"], 0.001)
        self.assertAlmostEqual(result["trials"][0]["displacement_from_observed_terminal"]["max_vertex_displacement_m"], 0.001)

    def test_terminal_key_clear_attribution_rejects_duplicate_family_or_empty_keys(self):
        common = {"family": "HGPT_S7_DELT", "cleared_key_names": ["k"], "vertices": [(0, 0, 0)]}
        with self.assertRaisesRegex(ValueError, "unique"):
            probe.terminal_key_clear_attribution_summary([(0, 0, 0)], [(0, 0, 0)], [common, common], True)
        bad = {"family": "HGPT_S7_DELT", "cleared_key_names": [], "vertices": [(0, 0, 0)]}
        with self.assertRaisesRegex(ValueError, "cleared key"):
            probe.terminal_key_clear_attribution_summary([(0, 0, 0)], [(0, 0, 0)], [bad], True)

    def test_terminal_family_trial_failure_restores_all_key_values_and_mutes(self):
        keys = {
            "HGPT_S7_DELT_l_156": NS(value=0.7, mute=False),
            "HGPT_S5_BAKE_l_160": NS(value=0.4, mute=True),
        }
        before = {name: (key.value, key.mute) for name, key in keys.items()}
        with self.assertRaisesRegex(RuntimeError, "evaluation failed"):
            probe.run_terminal_key_clear_trials(
                keys, {"HGPT_S7_DELT": ["HGPT_S7_DELT_l_156"]},
                lambda: None,
                lambda: (_ for _ in ()).throw(RuntimeError("evaluation failed")),
                lambda: ("same pose",))
        self.assertEqual({name: (key.value, key.mute) for name, key in keys.items()}, before)

    def test_terminal_family_trial_rejects_evaluated_geometry_restore_drift(self):
        keys = {"HGPT_S7_DELT_l_156": NS(value=0.7, mute=False)}
        observed = iter(([(0, 0.001, 0)], [(0, 0.0001, 0)]))
        with self.assertRaisesRegex(ValueError, "evaluated geometry"):
            probe.run_terminal_key_clear_trials(
                keys, {"HGPT_S7_DELT": ["HGPT_S7_DELT_l_156"]},
                lambda: None, lambda: next(observed), lambda: ("same pose",),
                baseline_vertices=[(0, 0, 0)])
        self.assertEqual((keys["HGPT_S7_DELT_l_156"].value,
                          keys["HGPT_S7_DELT_l_156"].mute), (0.7, False))

    def test_terminal_family_trial_rejects_key_reactivation_before_measurement(self):
        key = NS(value=0.7, mute=False)
        def reactivating_refresh():
            if key.value == 0.0:
                key.value = 0.7
        with self.assertRaisesRegex(ValueError, "clear condition"):
            probe.run_terminal_key_clear_trials(
                {"HGPT_S7_DELT_l_156": key},
                {"HGPT_S7_DELT": ["HGPT_S7_DELT_l_156"]},
                reactivating_refresh, lambda: [(0, 0, 0)],
                lambda: ("same pose",), baseline_vertices=[(0, 0, 0)])
        self.assertEqual((key.value, key.mute), (0.7, False))

    def test_report_rejects_reverse_or_clear_claim_inconsistency(self):
        d = mock_report()
        d["reverse_press_trajectory"]["physiological_return_claimed"] = True
        self.assertIn("invalid reverse trajectory evidence", probe.validate_report(d))
        d = mock_report()
        d["explicit_key_clear_experiment"]["model_repair_claimed"] = True
        self.assertIn("invalid explicit-clear evidence", probe.validate_report(d))
        d = mock_report()
        d["reverse_press_trajectory"]["samples"][4]["vertex_count"] = 3
        self.assertIn("invalid reverse trajectory evidence", probe.validate_report(d))
        d = mock_report()
        cleared = d["explicit_key_clear_experiment"]
        cleared["runtime_state_restored_exactly"] = False
        cleared["active_nonbasis_shape_keys"] = [{"name": "", "actual_value": float("nan")}]
        self.assertIn("invalid explicit-clear evidence", probe.validate_report(d))
        d = mock_report()
        d["terminal_corrective_key_clear_attribution"]["trials"][0]["cleared_key_names"] = ["not-active"]
        self.assertIn("invalid terminal key-clear attribution", probe.validate_report(d))
        d = mock_report()
        d["terminal_corrective_key_clear_attribution"]["terminal_state_restored_after_trials_exactly"] = False
        self.assertIn("invalid terminal key-clear attribution", probe.validate_report(d))
        d = mock_report()
        d["terminal_corrective_key_clear_attribution"]["trials"][0]["family"] = "HGPT"
        self.assertIn("invalid terminal key-clear attribution", probe.validate_report(d))

    def test_report_requires_truthful_return_state_without_demanding_a_pass(self):
        d = mock_report()
        d["post_benchmark_return_to_start_state"]["runtime_state_restored_exactly"] = False
        d["post_benchmark_return_to_start_state"]["max_vertex_displacement_m"] = 0.002
        d["post_benchmark_return_to_start_state"]["rms_vertex_displacement_m"] = 0.001
        d["post_benchmark_return_to_start_state"]["vertices_moved_gt_1e_9_m"] = 1
        self.assertEqual(probe.validate_report(d), [])
        d = mock_report()
        d["post_benchmark_return_to_start_state"]["anatomical_neutral_claimed"] = True
        self.assertIn("invalid return-to-start evidence", probe.validate_report(d))
        d = mock_report()
        d.pop("post_benchmark_return_to_start_state")
        self.assertIn("invalid return-to-start evidence", probe.validate_report(d))
        d = mock_report()
        returned = d["post_benchmark_return_to_start_state"]
        returned["runtime_state_restored_exactly"] = False
        returned["active_nonbasis_shape_keys"] = [{"name": "", "actual_value": float("nan")}]
        self.assertIn("invalid return-to-start evidence", probe.validate_report(d))
        d = mock_report()
        returned = d["post_benchmark_return_to_start_state"]
        returned["max_vertex_displacement_m"] = 0.0
        returned["rms_vertex_displacement_m"] = 0.001
        returned["vertices_moved_gt_1e_9_m"] = 1
        self.assertIn("invalid return-to-start evidence", probe.validate_report(d))
        d = mock_report()
        d["post_benchmark_return_to_start_state"]["vertex_count"] = True
        self.assertIn("invalid return-to-start evidence", probe.validate_report(d))
        d = mock_report()
        returned = d["post_benchmark_return_to_start_state"]
        returned["runtime_state_restored_exactly"] = False
        returned["max_vertex_displacement_m"] = 0.002
        returned["rms_vertex_displacement_m"] = 0.001
        returned["vertices_moved_gt_1e_9_m"] = 0
        self.assertIn("invalid return-to-start evidence", probe.validate_report(d))

    def test_no_model_save_in_source(self):
        txt = MODULE.read_text()
        self.assertNotIn("save_as_mainfile(", txt)
        self.assertNotIn("bpy.ops.wm.save", txt)
        self.assertNotIn("keyframe_insert(", txt)

if __name__ == "__main__":
    unittest.main()
