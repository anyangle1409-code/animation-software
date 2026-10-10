#!/usr/bin/env python3
"""Primary clavicle motion evidence compatibility, no invented shoulder movement."""
import copy
import json
from pathlib import Path
import sys
import unittest

HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE/"anatomy_fit"))
from clavicle_primary_source_compatibility import REVIEW,GAP,assessment

class PrimaryClavicleEvidence(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.e=json.loads(REVIEW.read_text())
        cls.g=json.loads(GAP.read_text())

    def test_primary_sources_contradict_simple_zero_motion_with_distinct_axes(self):
        out=assessment(self.e,self.g)
        self.assertEqual(out["source_2004_reported_SC_elevation_maxima_deg"],[11,15])
        self.assertEqual(out["source_2009_primary_bone_pin_subjects"],12)
        self.assertTrue(out["source_2009_31deg_is_SC_posterior_axial_rotation_not_elevation"])
        self.assertEqual(out["c004_installed_clavicle_elevation"],"NONE")
        self.assertFalse(out["primary_curve_per_HT_angle_verified"])
        self.assertFalse(out["candidate_motion_curve_authorized"])
        self.assertFalse(out["canonical_promotion_allowed"])

    def test_model_sensitivity_not_anatomical_curve_or_hard_ceiling(self):
        r=assessment(self.e,self.g)
        for x in r["sensitivity_not_target"]:
            self.assertEqual([k["humerothoracic_command_deg"] for k in x["hypothetical_generic_model"]],
                             [60,90,120,168])
            model=x["hypothetical_generic_model"]
            self.assertEqual(model[2]["generic_model_elevation_deg"],12.3)
            self.assertEqual(model[3]["generic_model_elevation_deg"],17.22)
            self.assertTrue(model[3]["comparison_to_2004_reported_task_maxima"].startswith("ABOVE_"))
            self.assertFalse(model[3]["literal_2004_midrange_curve_or_target_verified"])
            self.assertFalse(model[3]["candidate_c004_elevation_installed"])

    def test_31_degree_bone_pin_long_axis_must_never_be_elevation(self):
        e=copy.deepcopy(self.e)
        pin=next(x for x in e["sources"] if x["id"]=="ludewig2009_bone_pin_shoulder")
        candidate=next(x for x in pin["measures"] if x["quantity"]=="sternoclavicular_elevation")
        candidate["reported_numeric_trajectory_deg"]=31
        with self.assertRaisesRegex(ValueError,"NOT clavicle elevation"):
            assessment(e,self.g)

    def test_secondary_10degree_snippet_not_set_as_primary_limit(self):
        e=copy.deepcopy(self.e)
        src=next(x for x in e["sources"] if x["id"]=="ludewig2004_clavicle_surface")
        src["measures"][0]["reported_maximum_range_deg"]=[0,10]
        with self.assertRaisesRegex(ValueError,"roles changed"):
            assessment(e,self.g)

    def test_generic_model_slope_and_c004_record_are_separately_protected(self):
        e=copy.deepcopy(self.e)
        e["existing_model_template"]["coefficient_deg_clavicle_elevation_per_deg_humerothoracic"]=.14
        with self.assertRaisesRegex(ValueError,"slope changed"):
            assessment(e,self.g)
        g=copy.deepcopy(self.g)
        g["c004"]["right"]["HT168"]["model_clavicle_elevation_deg"]=31
        with self.assertRaisesRegex(ValueError,"observation mismatch"):
            assessment(self.e,g)

    def test_no_data_envelope_approval_from_primary_sample_size(self):
        for flag in ("has_end_angle_clavicle_elevation_primary_curve",
                     "has_source_matched_rest_pose","has_verified_SC_AC_GH_axis_transforms",
                     "bone_mesh_skeleton_change_authorized","canonical_promotion_allowed"):
            e=copy.deepcopy(self.e);e["unresolved_decision"][flag]=True
            with self.subTest(flag=flag),self.assertRaisesRegex(ValueError,"falsely approved"):
                assessment(e,self.g)

if __name__=="__main__":
    unittest.main()
