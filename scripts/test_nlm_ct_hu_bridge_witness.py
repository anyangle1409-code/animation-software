#!/usr/bin/env python3
"""First-party HU bridge tests: test geometry, NOT articular bone truth."""
import json
import math
import sys
import unittest
from pathlib import Path

HERE=Path(__file__).resolve().parent
ROOT=HERE.parent
sys.path.insert(0,str(HERE/"anatomy_fit"))
from nlm_ct_hu_bridge_witness import (
    weighted_shortest_intensity_bridge, select_source_pins, source_spacing_mm, analyze
)

AUDIT=ROOT/"ORIGINAL_V1_WORK"/"anatomy"/"audit"
BUNDLE=json.loads((AUDIT/"nlm_pelvic_ct_full_series_candidate_bundle_20261009.json").read_text())
CAL=json.loads((AUDIT/"nlm_pelvic_ct_full_series_hu_calibration_20261009.json").read_text())
REVIEW=json.loads((AUDIT/"nlm_pelvic_ct_full_series_candidate_review_20261009.json").read_text())
ROI=[10,45,10,45]


def bg(s=-481):
    return {
        "plane_TL_RAS_mm":[230.0,230.0,s],
        "plane_TR_RAS_mm":[-230.0,230.0,s],
        "plane_BR_RAS_mm":[-230.0,-230.0,s],
        "scanner_S_mm":s,
    }


class PhysicalHueBridge(unittest.TestCase):
    def test_anisotropic_in_plane_path_deterministic_and_no_anatomy(self):
        mask={(1,11,c) for c in range(11,18)}
        mask.update((0,11,c) for c in range(11,18))
        a=(1,11,11)
        b=(1,11,17)
        v=weighted_shortest_intensity_bridge(mask,a,b,ROI,3,[3.0,.9,.9])
        self.assertTrue(v["same_HU_component"])
        self.assertEqual(v["path_voxel_samples"],7)
        self.assertEqual(v["least_physical_length_mm_in_thresholded_ROI"],5.4)
        self.assertEqual(v["seed_direct_euclidean_distance_mm"],5.4)
        self.assertEqual(v["route_length_over_direct_distance"],1.0)
        self.assertEqual(v["path_slice_planes_visited"],1)
        self.assertFalse(v["path_touches_source_or_ROI_cut"])
        self.assertEqual(v["path_scanner_plane_index_extent"]["slice_min_max"],[1,1])
        self.assertFalse(v["anatomical_joint_contact_or_separation_proven"])
        self.assertFalse(v["canonical_promotion_allowed"])

    def test_z_path_and_truncation_flags(self):
        roi=[11,25,10,25]
        mask={(0,10,11),(1,10,11),(2,10,11)}
        v=weighted_shortest_intensity_bridge(
            mask,(0,10,11),(2,10,11),roi,3,[3,.8,.8])
        self.assertEqual(v["least_physical_length_mm_in_thresholded_ROI"],6)
        self.assertEqual(v["path_slice_planes_visited"],3)
        self.assertIn("ROI_row_min",v["path_selection_cut_contacts"])
        self.assertIn("ROI_col_min",v["path_selection_cut_contacts"])
        self.assertIn("source_group_first_plane",v["path_selection_cut_contacts"])
        self.assertIn("source_group_last_plane",v["path_selection_cut_contacts"])

    def test_metric_path_prefers_shorter_mm_over_shorter_route_hops(self):
        # Five 3mm Z steps would cost far more than an in-plane detour.
        a=(1,15,15);b=(1,15,19)
        same={(1,15,c) for c in range(15,20)}
        v=weighted_shortest_intensity_bridge(
            same | {(0,15,c) for c in range(15,20)},
            a,b,ROI,3,[3,.9,.9])
        self.assertEqual(v["least_physical_length_mm_in_thresholded_ROI"],3.6)
        self.assertEqual(v["path_slice_planes_visited"],1)

    def test_disconnected_and_unoccupied_remain_indeterminate(self):
        source={(0,15,15),(0,15,17)}
        v=weighted_shortest_intensity_bridge(
            source,(0,15,15),(0,15,17),ROI,3,[3,.9,.9])
        self.assertIs(v["same_HU_component"],False)
        self.assertFalse(v["path_exists_and_is_hu_only"])
        self.assertEqual(v["no_path_reason"],"disconnected_in_supplied_6_neighbour_HU_mask")
        missing=weighted_shortest_intensity_bridge(
            source,(0,15,15),(0,15,16),ROI,3,[3,.9,.9])
        self.assertIsNone(missing["same_HU_component"])
        self.assertEqual(missing["no_path_reason"],
                         "one_or_both_source_seed_pixels_below_HU_threshold")

    def test_actual_decoded_scalar_minimum_reported(self):
        frames=[[0]*(512*512) for _ in range(2)]
        pts={(0,15,c) for c in (15,16,17)}
        for z,r,c in pts:frames[z][r*512+c]={15:1500,16:1400,17:1800}[c]
        v=weighted_shortest_intensity_bridge(
            pts,(0,15,15),(0,15,17),ROI,2,[3,1,1],scalar_layers=frames)
        self.assertEqual(v["path_minimum_source_HU"],376)

    def test_bad_budget_geometry_seeds_and_source_planes_fail(self):
        base={(0,15,15),(0,15,16)}
        for value in ([3,0.0,.9],[3,float("nan"),.9],[3,.9]):
            with self.subTest(spacing=value),self.assertRaises(ValueError):
                weighted_shortest_intensity_bridge(
                    base,(0,15,15),(0,15,16),ROI,3,value)
        with self.assertRaisesRegex(ValueError,"budget"):
            weighted_shortest_intensity_bridge(
                base,(0,15,15),(0,15,16),ROI,3,[3,.9,.9],
                max_settled=1)
        with self.assertRaisesRegex(ValueError,"outside"):
            weighted_shortest_intensity_bridge(
                base,(0,15,15),(0,15,50),ROI,3,[3,.9,.9])
        with self.assertRaisesRegex(ValueError,"triplets"):
            weighted_shortest_intensity_bridge(
                base,(True,15,15),(0,15,16),ROI,3,[3,.9,.9])

    def test_source_pin_is_exact_and_remains_review_only(self):
        names=["obs-1873-right-femoral-head","obs-1873-right-acetabulum"]
        rows,found=select_source_pins(BUNDLE,REVIEW,2,10,2,names)
        self.assertEqual(len(rows),2)
        self.assertEqual(rows[0]["source_id"],"cvm1873f")
        self.assertEqual(found[0]["voxel_z_row_col"],[0,270,175])
        self.assertEqual(found[1]["voxel_z_row_col"],[0,257,151])
        self.assertTrue(all(not x["anatomical_label_verified"] for x in found))
        with self.assertRaisesRegex(ValueError,"unique|distinct"):
            select_source_pins(BUNDLE,REVIEW,2,10,2,[names[0],names[0]])
        with self.assertRaisesRegex(ValueError,"outside"):
            select_source_pins(BUNDLE,REVIEW,1,10,2,names)
        altered=json.loads(json.dumps(REVIEW))
        p=next(x for x in altered["observations"] if x["observation_id"]==names[0])
        p["source_header_sha256"]="bogus"
        with self.assertRaisesRegex(ValueError,"hash"):
            select_source_pins(BUNDLE,altered,2,10,2,names)

    def test_full_source_calibration_and_anatomical_rejection_with_private_fixture(self):
        names=["obs-1873-right-femoral-head","obs-1873-right-acetabulum"]
        paths=[]
        start=(270,175);finish=(257,151)
        paths += [(270,c) for c in range(151,176)]
        paths += [(r,151) for r in range(257,271)]
        frames=[[0]*(512*512) for _ in range(2)]
        for r,c in paths:frames[0][r*512+c]=1500
        rows=BUNDLE["series"][1]["slices"][10:12]
        ids={p["source_id"]:i for i,p in enumerate(rows)}
        def loader(folder,row):
            z=ids[row["source_id"]]
            return bg(row["scanner_centre_RAS_mm"][2]),frames[z]
        result=analyze(
            BUNDLE,CAL,REVIEW,2,10,2,[140,181,245,275],[300,500],
            "/private/originals",names,source_loader=loader)
        witness=result["HU_thresholds"]["300"][
            "physical_HU_bridge_witness_not_anatomical_contact"]
        self.assertTrue(witness["same_HU_component"])
        self.assertGreater(witness["least_physical_length_mm_in_thresholded_ROI"],20)
        self.assertEqual(witness["path_minimum_source_HU"],476)
        self.assertIsNone(result["HU_thresholds"]["500"][
            "physical_HU_bridge_witness_not_anatomical_contact"]["same_HU_component"])
        self.assertFalse(result["distinct_bone_surface_identity_verified"])
        self.assertFalse(result["hip_joint_articular_gap_verified"])
        self.assertEqual(result["pelvic_landmarks_accepted"],0)
        self.assertFalse(result["canonical_promotion_allowed"])

    def test_actual_scanner_spacing_not_assumed_isotropic(self):
        self.assertAlmostEqual(source_spacing_mm(bg())[1],460/512)
        self.assertAlmostEqual(source_spacing_mm(bg())[2],460/512)


if __name__=="__main__":
    unittest.main()
