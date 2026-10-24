"""Synthetic guards for W8 stored-key / observed-press crosswalk."""
import sys
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "cloud_body_analysis"))
import elbow_corrective_crosswalk as mod


def fixtures():
    edge = {
        "source_sha256": mod.W8_SHA, "target_edge_count": 4,
        "anatomical_side_verified": False, "skin_deformation_validated": False,
        "edges": [
            {"ranked_report_label_NOT_anatomical_side": f"middle_suffix_{s}_press_sample6_max_{i}",
             "rest_mesh_edge_vertex_ids": [i, i + 1], "rest_edge_length_mm": 3.5,
             "group_weight_L1_difference_not_tissue_strain": .03,
             "top_stored_shape_keys_by_absolute_edge_ratio_change": [
                 {"key": f"HGPT_S7_DELT_{s}_145", "stored_edge_length_ratio_to_Basis": 2.8},
                 {"key": f"HGPT_K1_ELBOW_{s}_110", "stored_edge_length_ratio_to_Basis": 1.2}]}
            for i, s in enumerate("llrr")]
    }
    pose = {"source_sha256": mod.W8_SHA, "anatomical_approval": "NOT_GRANTED",
            "saved_blend": False, "source_unchanged": True, "samples": [
                {"sample": idx, "sides": {
                    s: {"humerothoracic_elevation_measured_by_pinned_driver_deg": 90 + idx,
                        "actual_shape_key_values": [{"name": f"HGPT_S7_DELT_{s}_145", "actual_value": v}]}
                    for s in "lr"}} for idx, v in [(0, 0.), (6, .93), (8, 0.)]]}
    return edge, pose


class CrosswalkTests(unittest.TestCase):
    def test_active_key_and_unknown_are_distinct(self):
        result = mod.analyze(*fixtures())
        self.assertEqual(result["edge_count"], 4)
        row = result["edges"][0]["samples"][1]
        self.assertEqual(row["active_top_keys_descriptive"], ["HGPT_S7_DELT_l_145"])
        self.assertEqual(row["not_recorded_top_keys"], ["HGPT_K1_ELBOW_l_110"])
        self.assertIsNone(row["stored_top_keys_with_observed_values"][1]["observed_value_or_null_if_not_recorded"])
        self.assertFalse(result["skin_deformation_validated"])

    def test_zero_is_not_missing(self):
        row = mod.analyze(*fixtures())["edges"][0]["samples"][0]
        self.assertEqual(row["active_top_keys_descriptive"], [])
        self.assertEqual(row["stored_top_keys_with_observed_values"][0]["observed_value_or_null_if_not_recorded"], 0)

    def test_wrong_source_rejected(self):
        a, b = fixtures()
        b["source_sha256"] = "0" * 64
        with self.assertRaises(ValueError): mod.analyze(a, b)

    def test_missing_sample_rejected(self):
        a, b = fixtures()
        b["samples"].pop()
        with self.assertRaises(ValueError): mod.analyze(a, b)

    def test_duplicate_observed_key_rejected(self):
        a, b = fixtures()
        b["samples"][0]["sides"]["l"]["actual_shape_key_values"] *= 2
        with self.assertRaises(ValueError): mod.analyze(a, b)

    def test_nonfinite_activation_rejected(self):
        a, b = fixtures()
        b["samples"][0]["sides"]["l"]["actual_shape_key_values"][0]["actual_value"] = float("nan")
        with self.assertRaises(ValueError): mod.analyze(a, b)

    def test_invalid_stored_ratio_rejected(self):
        a, b = fixtures()
        a["edges"][0]["top_stored_shape_keys_by_absolute_edge_ratio_change"][0]["stored_edge_length_ratio_to_Basis"] = -1
        with self.assertRaises(ValueError): mod.analyze(a, b)

    def test_no_anatomical_approval_in_markdown(self):
        r = mod.analyze(*fixtures())
        self.assertIn("NO CAUSALITY OR ANATOMICAL APPROVAL", mod.markdown(r))
        self.assertFalse(r["joint_axes_ISB_calibrated"])


if __name__ == "__main__":
    unittest.main()
