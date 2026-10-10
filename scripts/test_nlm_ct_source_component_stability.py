#!/usr/bin/env python3
"""Adversarial synthetic checks for the multi-slice, multi-HU source review."""
import json
import sys
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
sys.path.insert(0, str(HERE / "anatomy_fit"))
import nlm_ct_source_component_stability as stability

AUDIT = ROOT / "ORIGINAL_V1_WORK" / "anatomy" / "audit"
BUNDLE = AUDIT / "nlm_pelvic_ct_full_series_candidate_bundle_20261009.json"
CAL = AUDIT / "nlm_pelvic_ct_full_series_hu_calibration_20261009.json"


def geometry(s):
    return {
        "plane_TL_RAS_mm": [228, 291, s],
        "plane_TR_RAS_mm": [-232, 291, s],
        "plane_BR_RAS_mm": [-232, -169, s],
    }


def pixels():
    layers = [[0] * (512 * 512) for _ in range(3)]
    layers[0][10 * 512 + 10] = 1550
    layers[1][10 * 512 + 10] = 1550
    layers[2][10 * 512 + 10] = 1350
    layers[1][20 * 512 + 20] = 1330
    return layers


class SourceComponentStability(unittest.TestCase):
    def test_physical_components_truncation_and_hu_stability(self):
        result = stability.analyze_pixels(
            pixels(), geometry(-342), -342, [5, 30, 5, 30],
            [150, 300, 500],
        )
        summaries = result["thresholds"]
        self.assertEqual([s["voxel_count"] for s in summaries], [4, 4, 2])
        self.assertEqual(
            [s["component_count_6_neighbour"] for s in summaries], [2, 2, 1])
        self.assertEqual([s["largest_components"][0]["voxel_count"] for s in summaries],
                         [3, 3, 2])
        self.assertEqual([v["global_occupancy_Jaccard"]
                          for v in result["comparisons"]], [1.0, .5])
        large = summaries[0]["largest_components"][0]
        self.assertIn("source_selection_superior_cut", large["selection_cut_contacts"])
        self.assertIn("source_selection_inferior_cut", large["selection_cut_contacts"])
        self.assertFalse(large["complete_object_surface_in_this_selection"])
        self.assertEqual(
            large["scanner_RAS_outer_edge_assumption_bounds_mm"]["S"],
            [-349.5, -340.5])
        small = summaries[0]["largest_components"][1]
        self.assertEqual(small["selection_cut_contacts"], [])
        self.assertIsNone(small["complete_object_surface_in_this_selection"])

    def test_roi_cut_is_separate_from_slice_cut(self):
        out = stability.components_with_bounds(
            {(1, 8, 7), (1, 9, 7)},
            selected_slices=3, roi=[7, 12, 8, 13],
            geometry=geometry(-342), first_s=-342, thickness=3)
        self.assertEqual(out[0]["voxel_count"], 2)
        self.assertIn("ROI_col_min_cut", out[0]["selection_cut_contacts"])
        self.assertIn("ROI_row_min_cut", out[0]["selection_cut_contacts"])
        self.assertNotIn("source_selection_superior_cut",
                         out[0]["selection_cut_contacts"])

    def test_empty_high_threshold_retains_null_iou(self):
        result = stability.analyze_pixels(
            [[0] * (512 * 512)] * 2, geometry(-342), -342,
            [0, 1, 0, 1], [150, 500])
        self.assertEqual(result["thresholds"][0]["component_count_6_neighbour"], 0)
        self.assertIsNone(result["comparisons"][0]["global_occupancy_Jaccard"])

    def test_invalid_thresholds_and_roi_rejected(self):
        values = pixels()
        for bad in ([300, 150], [150, 150], [150], [150, 300, 5000],
                    [150, True], ["150", 500]):
            with self.subTest(thresholds=bad), self.assertRaises(ValueError):
                stability.analyze_pixels(values, geometry(-342), -342,
                                         [5, 30, 5, 30], bad)
        with self.assertRaisesRegex(ValueError, "ROI"):
            stability.analyze_pixels(values, geometry(-342), -342,
                                     [0, 513, 5, 30], [150, 300])
        with self.assertRaisesRegex(ValueError, "512"):
            stability.analyze_pixels([[0] * 5, [0] * 5],
                                     geometry(-342), -342,
                                     [0, 1, 0, 1], [150, 300])

    def test_actual_pinned_group_selection_with_synthetic_layers(self):
        with tempfile.TemporaryDirectory() as td:
            destination = Path(td) / "topology.json"
            source = Path(td) / "original"
            args = SimpleNamespace(
                ct_dir=str(source), out=str(destination),
                bundle=str(BUNDLE), calibration=str(CAL),
                group=2, start=7, count=3,
                roi=[5, 30, 5, 30], hu=[150, 300, 500])
            source_layers = pixels()
            counter = iter(source_layers)
            def loader(_source, row):
                return geometry(row["scanner_centre_RAS_mm"][2]), next(counter)
            with patch.object(stability, "_private_source_slice", side_effect=loader):
                result = stability.run(args)
            self.assertEqual(result["source_ids"],
                             ["cvm1864f", "cvm1867f", "cvm1870f"])
            self.assertEqual(result["thresholds"][0]["voxel_count"], 4)
            self.assertFalse(result["anatomical_bone_identity_verified"])
            self.assertFalse(result["canonical_promotion_allowed"])
            self.assertFalse(result["pixel_centre_convention_verified"])
            self.assertTrue(destination.is_file())
            self.assertNotIn("patient", destination.read_text().lower())
            with self.assertRaisesRegex(ValueError, "overwrite"):
                stability.run(args)

    def test_three_dimensional_source_seed_pairs_do_not_claim_bone_identity(self):
        occupied = {
            300: {(0, 10, 10), (1, 10, 10), (1, 10, 11), (1, 20, 20)},
            500: {(1, 10, 10), (1, 20, 20)},
        }
        seeds = [
            {"id": "seed_A", "voxel_z_row_col": [1, 10, 10]},
            {"id": "seed_B", "voxel_z_row_col": [1, 10, 11]},
            {"id": "seed_C", "voxel_z_row_col": [1, 20, 20]},
        ]
        reports = stability.seed_relationships(
            occupied, seeds, selected_slices=3, roi=[5, 30, 5, 30])
        pairs = reports[0]["pairwise_HU_connectivity"]
        self.assertEqual([p["same_HU_connected_component"] for p in pairs],
                         [True, False, False])
        self.assertTrue(all(not p["separate_anatomical_bones_proven"]
                            for p in pairs))
        self.assertIsNone(reports[1]["pairwise_HU_connectivity"][0][
            "same_HU_connected_component"])
        self.assertFalse(reports[1]["review_seeds"][1]["seed_meets_threshold"])
        self.assertEqual(reports[0]["review_seeds"][0]["connected_voxels"], 3)

    def test_original_review_pins_drive_only_explicit_3d_source_pair_analysis(self):
        review = AUDIT / "nlm_pelvic_ct_full_series_candidate_review_20261009.json"
        a = "obs-1873-left-femoral-head"
        b = "obs-1873-left-acetabulum"
        with tempfile.TemporaryDirectory() as td:
            result_file = Path(td) / "pairs.json"
            args = SimpleNamespace(
                ct_dir=str(Path(td) / "original"),
                out=str(result_file),
                bundle=str(BUNDLE), calibration=str(CAL),
                group=2, start=9, count=3,
                roi=[335, 380, 245, 280], hu=[300, 500],
                review=str(review), seed_observation=[a, b])
            ct_pixels = [[1024] * (512*512) for _ in range(3)]
            ct_pixels[1][270*512+342] = 1500
            ct_pixels[1][257*512+366] = 1700
            counter = iter(ct_pixels)
            def source(_folder, row):
                return geometry(row["scanner_centre_RAS_mm"][2]), next(counter)
            with patch.object(stability, "_private_source_slice", side_effect=source):
                result = stability.run(args)
            connected = result[
                "proposed_point_HU_connectivity_not_anatomical_identity"]
            self.assertEqual([q["HU"] for q in connected], [300, 500])
            self.assertEqual(
                connected[0]["pairwise_HU_connectivity"][0]["same_HU_connected_component"],
                False)
            self.assertIsNone(
                connected[1]["pairwise_HU_connectivity"][0]["same_HU_connected_component"])
            self.assertEqual(connected[0]["review_seeds"][0]["connected_voxels"], 1)
            self.assertFalse(result["canonical_promotion_allowed"])
            self.assertEqual(result["seven_pelvic_landmarks_verified"], 0)
            self.assertTrue(result_file.is_file())

    def test_review_seed_pair_rejects_duplicates_and_out_of_roi(self):
        vols = {300: {(1, 10, 10), (1, 10, 11)}}
        same = [{"id":"A", "voxel_z_row_col": [1, 10, 10]},
                {"id":"A", "voxel_z_row_col": [1, 10, 11]}]
        with self.assertRaisesRegex(ValueError, "duplicate"):
            stability.seed_relationships(vols, same, 3, [5, 30, 5, 30])
        same[1]["id"] = "B"
        same[1]["voxel_z_row_col"] = [1, 10, 40]
        with self.assertRaisesRegex(ValueError, "outside"):
            stability.seed_relationships(vols, same, 3, [5, 30, 5, 30])
        with self.assertRaisesRegex(ValueError, "two through eight"):
            stability.seed_relationships(vols, same[:1], 3, [5, 30, 5, 30])

    def test_group_or_range_change_must_fail_before_source_io(self):
        with tempfile.TemporaryDirectory() as td:
            args = SimpleNamespace(
                ct_dir=str(Path(td) / "missing"), out=str(Path(td) / "notmade.json"),
                bundle=str(BUNDLE), calibration=str(CAL),
                group=3, start=7, count=3,
                roi=[5, 30, 5, 30], hu=[150, 300])
            with self.assertRaisesRegex(ValueError, "groups"):
                stability.run(args)
            args.group = 2
            args.start = 34
            with self.assertRaisesRegex(ValueError, "within a single"):
                stability.run(args)
            self.assertFalse(Path(args.out).exists())


if __name__ == "__main__":
    unittest.main()
