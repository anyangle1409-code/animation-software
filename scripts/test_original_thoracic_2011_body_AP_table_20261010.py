"""Adversarial scientific-source tests: actual 2011 thoracic C7-T12 body wedges.

No network or PDF fetch. No Blender or canonical geometry modification.
"""
import copy
import json
import unittest

from anatomy_fit.audit_primary_thoracic_body_AP_heights_20261010 import (
    SOURCE,CANONICAL,PRINTED_TABLE,ALL_DENIALS,audit
)


class Kunkel2011OriginalPrimaryBodyAPTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.paper=json.loads(SOURCE.read_text(encoding="utf-8"))
        cls.canonical=json.loads(CANONICAL.read_text(encoding="utf-8"))

    def validate(self,paper=None,baseline=None):
        return audit(
            paper if paper is not None else copy.deepcopy(self.paper),
            baseline if baseline is not None else copy.deepcopy(self.canonical))

    def test_complete_primary_table_C7_T12_13_levels(self):
        d=self.validate()
        self.assertEqual(d["body_levels_examined_count"],13)
        self.assertEqual(d["thoracic_body_levels_examined_count"],12)
        self.assertEqual(len(PRINTED_TABLE),13)
        self.assertEqual(d["min_posterior_minus_anterior_mm"],0.49)
        self.assertEqual(d["max_posterior_minus_anterior_mm"],3.07)

    def test_primary_anterior_vs_posterior_examples(self):
        d=self.validate()["original_levelled_source_heights"]
        self.assertEqual(d["T1"]["posterior_minus_anterior_mean_mm"],0.79)
        self.assertEqual(d["T4"]["posterior_minus_anterior_mean_mm"],2.73)
        self.assertEqual(d["T8"]["posterior_minus_anterior_mean_mm"],3.06)
        self.assertEqual(d["T11"]["posterior_minus_anterior_mean_mm"],3.07)
        self.assertEqual(d["T12"]["posterior_minus_anterior_mean_mm"],2.32)

    def test_original_cadaver_cohort_is_mixed_and_disassembled(self):
        d=self.validate()
        self.assertEqual(d["original_donor_count"],30)
        self.assertTrue(d["original_72_segments_across_12_disc_levels"])
        self.assertFalse(d["mean_A_P_heights_can_be_read_as_182cm_male_target"])

    def test_separate_2016_Indian_CT_is_not_a_combined_3d_cohort(self):
        d=self.validate()
        self.assertEqual(len(d["cross_source_2016_CT_spotcheck"]),5)
        self.assertTrue(all(x["kunkel_2011_posterior_gt_anterior"] for x in d["cross_source_2016_CT_spotcheck"]))
        self.assertTrue(all(x["separate_indian_CT_2016_posterior_gt_anterior"] for x in d["cross_source_2016_CT_spotcheck"]))
        self.assertFalse(any(x["sources_can_supply_vertebral_depths_for_one_another"] for x in d["cross_source_2016_CT_spotcheck"]))

    def test_noncanonical_explicit_rejections(self):
        d=self.validate()
        self.assertFalse(d["per_level_standing_spinal_cobb_angles_reported"])
        self.assertFalse(d["patient_matched_3d_endplate_depths_reported"])
        self.assertFalse(d["freeze_C2_to_S1_stack_ready"])
        self.assertFalse(d["CP1_gate6_passed"])
        self.assertTrue(d["reused_existing_source_average_body_heights_without_changes"])

    def test_forged_vertebral_angle_acceptance_refused(self):
        for key in ALL_DENIALS:
            with self.subTest(key=key):
                s=copy.deepcopy(self.paper)
                s["explicit_acceptance"][key]=True
                with self.assertRaisesRegex(ValueError,"not canonically approved"):
                    self.validate(paper=s)

    def test_forged_standing_original_population_refused(self):
        s=copy.deepcopy(self.paper)
        s["source"]["source_is_standing_sagittal_curve"]=True
        with self.assertRaisesRegex(ValueError,"cohort or methods"):
            self.validate(paper=s)

    def test_forged_male_only_dataset_refused(self):
        s=copy.deepcopy(self.paper)
        s["source"]["study_donor_female_n"]=0
        with self.assertRaisesRegex(ValueError,"cohort or methods"):
            self.validate(paper=s)

    def test_source_stature_conditional_claim_refused(self):
        s=copy.deepcopy(self.paper)
        s["source"]["eligible_male_182_cm_conditional_cohort"]=True
        with self.assertRaisesRegex(ValueError,"cohort or methods"):
            self.validate(paper=s)

    def test_wrong_anterior_posterior_swap_refused(self):
        s=copy.deepcopy(self.paper)
        s["body_table_2"]["T7"]["anterior_mean_mm"]=18.67
        s["body_table_2"]["T7"]["posterior_mean_mm"]=15.94
        with self.assertRaisesRegex(ValueError,"Table 2"):
            self.validate(paper=s)

    def test_wrong_verbatim_primary_sd_refused(self):
        s=copy.deepcopy(self.paper)
        s["body_table_2"]["T4"]["anterior_sd_mm"]=9.99
        with self.assertRaisesRegex(ValueError,"Table 2"):
            self.validate(paper=s)

    def test_missing_thoracic_level_refused(self):
        s=copy.deepcopy(self.paper)
        del s["body_table_2"]["T9"]
        with self.assertRaisesRegex(ValueError,"every C7-T12"):
            self.validate(paper=s)

    def test_fake_vertebral_ap_depth_source_refused(self):
        s=copy.deepcopy(self.paper)
        s["measurement_caveats"]["original_AP_vertebral_depth_at_each_level_unavailable"]=False
        with self.assertRaisesRegex(ValueError,"angle"):
            self.validate(paper=s)

    def test_wrong_original_DOI_refused(self):
        s=copy.deepcopy(self.paper)
        s["source"]["doi"]="10.fake/2011"
        with self.assertRaisesRegex(ValueError,"identity"):
            self.validate(paper=s)

    def test_canonical_existing_body_means_must_not_be_replaced(self):
        v=copy.deepcopy(self.canonical)
        source=next(s for s in v["sources"] if s["id"]=="THORACIC_BODY_DISC_2011")
        source["body_average_height_mm"]["T4"]=99.9
        source["average_body_height_mm"]["T4"]=99.9
        with self.assertRaisesRegex(ValueError,"Table 2"):
            self.validate(baseline=v)

    def test_prior_source_duplicated_identity_refused(self):
        v=copy.deepcopy(self.canonical)
        source=next(s for s in v["sources"] if s["id"]=="THORACIC_BODY_DISC_2011")
        v["sources"].append(copy.deepcopy(source))
        with self.assertRaisesRegex(ValueError,"absent or duplicated"):
            self.validate(baseline=v)

    def test_separate_CT_different_sign_detection(self):
        v=copy.deepcopy(self.canonical)
        ct=next(s for s in v["sources"] if s["id"]=="THORACIC_CT_2016_INDIA")
        ct["body_height_anterior_posterior_mm"]["T7"]=[24.21,20.0]
        with self.assertRaisesRegex(ValueError,"expected sign"):
            self.validate(baseline=v)

    def test_src_image_bytes_not_silently_promoted(self):
        s=copy.deepcopy(self.paper)
        s["source"]["patient_images_or_3d_mesh_imported"]=True
        with self.assertRaisesRegex(ValueError,"methods"):
            self.validate(paper=s)


if __name__=="__main__":
    unittest.main()
