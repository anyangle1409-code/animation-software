"""Pure standard-library checks for never-posing shoulder corrective rule metadata."""
import importlib.util
from pathlib import Path
from types import SimpleNamespace as NS
import unittest

SOURCE = Path(__file__).resolve().parents[2] / "phone_blender" / "shoulder_activation_contract.py"
SPEC = importlib.util.spec_from_file_location("shoulder_activation_contract", SOURCE)
act = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(act)

class TestActivationAudit(unittest.TestCase):
    def fixture(self):
        rig = {
            "hgpt_s7_angles_start": 132,
            "hgpt_s7_angles_l": [145, 166],
            "hgpt_s7_angles_r": [145, 166],
            "hgpt_c1_angles_l": [25, 35],
        }
        names = ["Basis", "HGPT_S7_DELT_l_145", "HGPT_S7_DELT_l_166",
                 "HGPT_S7_DELT_r_145", "HGPT_S7_DELT_r_166",
                 "HGPT_C1_ARMTRUNK_l_25", "HGPT_C1_ARMTRUNK_l_35"]
        blocks = [NS(name=x, value=0.0) for x in names]
        return rig, NS(data=NS(shape_keys=NS(key_blocks=blocks)))

    def family(self, report, name, side):
        return next(x for x in report["family_records"]
                    if x["family"] == name and x["side_suffix"] == side)

    def test_linear_hat_values_and_last_key_clamp(self):
        self.assertEqual(act.hat(132, 132, [145, 166], 0), 0)
        self.assertAlmostEqual(act.hat(138.5, 132, [145, 166], 0), 0.5)
        self.assertEqual(act.hat(145, 132, [145, 166], 0), 1)
        self.assertEqual(act.hat(166, 132, [145, 166], 0), 0)
        self.assertEqual(act.hat(166, 132, [145, 166], 1), 1)
        self.assertEqual(act.hat(180, 132, [145, 166], 1), 1)

    def test_existing_S7_side_properties_and_override(self):
        rig, body = self.fixture()
        report = act.inspect(rig, body)
        family = self.family(report, "HGPT_S7_DELT", "l")
        self.assertTrue(family["safe_to_evaluate_rule"])
        self.assertTrue(family["start_override_present"])
        self.assertEqual(family["effective_start_deg"], 132)
        self.assertEqual(family["angle_properties_deg"], [145, 166])
        self.assertEqual(family["keys"][1]["predicted_values_at_hypothetical_degrees"]["166"], 1)
        self.assertEqual(family["warnings"], [])
        self.assertEqual(report["shape_key_count"], 7)
        self.assertIn("Basis", report["unclassified_key_names"])
        self.assertIn("NOT_APPLIED_TO_POSE", report["status"])

    def test_C1_uses_extension_not_elevation(self):
        rig, body = self.fixture()
        family = self.family(act.inspect(rig, body), "HGPT_C1_ARMTRUNK", "l")
        self.assertEqual(family["effective_start_deg"], 18.0)
        self.assertEqual(family["measurement"], "shoulder_extension")
        self.assertTrue(family["safe_to_evaluate_rule"])

    def test_missing_property_is_not_fabricated(self):
        rig, body = self.fixture()
        rig.pop("hgpt_s7_angles_r")
        row = self.family(act.inspect(rig, body), "HGPT_S7_DELT", "r")
        self.assertFalse(row["safe_to_evaluate_rule"])
        self.assertIn("SHAPE_KEYS_WITHOUT_RIG_ANGLE_PROPERTY", row["warnings"])
        self.assertNotIn("predicted_values_at_hypothetical_degrees", row["keys"][0])

    def test_count_mismatch_warns_but_retains_evidence(self):
        rig, body = self.fixture()
        rig["hgpt_s7_angles_l"] = [145]
        row = self.family(act.inspect(rig, body), "HGPT_S7_DELT", "l")
        self.assertFalse(row["safe_to_evaluate_rule"])
        self.assertIn("KEY_COUNT_ANGLE_COUNT_DISAGREEMENT", row["warnings"])

    def test_nonmonotonic_angles_warn(self):
        rig, body = self.fixture()
        rig["hgpt_s7_angles_r"] = [145, 140]
        row = self.family(act.inspect(rig, body), "HGPT_S7_DELT", "r")
        self.assertFalse(row["safe_to_evaluate_rule"])
        self.assertIn("NONMONOTONE_OR_OUT_OF_RANGE_ANGLES", row["warnings"])

    def test_nonfinite_saved_key_value_rejected(self):
        rig, body = self.fixture()
        body.data.shape_keys.key_blocks[2].value = float("nan")
        with self.assertRaisesRegex(ValueError, "nonfinite"):
            act.inspect(rig, body)

    def test_no_unsupported_mesh_editing(self):
        import inspect as pyinspect
        text = pyinspect.getsource(act.inspect)
        self.assertNotIn("bpy.ops", text)
        self.assertNotIn("save_as_mainfile", text)
        self.assertNotIn(".value =", text)

if __name__ == "__main__":
    unittest.main()
