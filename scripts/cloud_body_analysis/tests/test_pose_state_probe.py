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

    def test_no_model_save_in_source(self):
        txt = MODULE.read_text()
        self.assertNotIn("save_as_mainfile(", txt)
        self.assertNotIn("bpy.ops.wm.save", txt)
        self.assertNotIn("keyframe_insert(", txt)

if __name__ == "__main__":
    unittest.main()
