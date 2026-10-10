"""Noncanonical 2006 sternum primary table / endpoint adversarial QA."""
import copy
import json
import unittest

from anatomy_fit.audit_selthofer_sternum_primary import SOURCE, PREVIOUS, audit


class SelthoferSourceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.paper=json.loads(SOURCE.read_text(encoding="utf-8"))
        cls.prior=json.loads(PREVIOUS.read_text(encoding="utf-8"))

    def check(self,paper=None,prior=None):
        return audit(paper or copy.deepcopy(self.paper),prior or copy.deepcopy(self.prior))

    def test_direct_original_male_mean_and_sd(self):
        out=self.check()
        self.assertEqual(out["selthofer_2006_male_total_jugular_to_xiphoid_mean_mm"],208.6)
        self.assertEqual(out["selthofer_2006_total_sd_mm"],14.6)
        self.assertEqual(out["selthofer_2006_manubrium_mean_mm"],55.2)
        self.assertEqual(out["selthofer_2006_body_mean_mm"],109.7)

    def test_cross_study_discrepancy_never_silently_resolved(self):
        out=self.check()
        self.assertEqual(out["between_studies_unadjusted_means_difference_mm"],54.5)
        self.assertTrue(out["between_studies_difference_may_reflect_endpoint_population_or_method"])
        self.assertFalse(out["anatomical_geometry_promoted"])
        self.assertFalse(out["cp1_gate6_passed"])

    def test_numeric_component_difference_not_direct_xiphoid_target(self):
        out=self.check()
        self.assertEqual(out["source_derived_total_minus_manubrium_minus_body_mean_mm"],43.7)
        self.assertTrue(out["source_derived_component_difference_is_not_xiphoid_accepted_length"])
        self.assertFalse(out["notch_by_notch_verified_coordinates_available"])

    def test_original_a003_comparison_is_semantically_restricted(self):
        out=self.check()
        self.assertEqual(out["a003_difference_from_selthofer_unadjusted_mean_mm"],4.6)
        self.assertTrue(out["old_a003_stick_vs_Turkey_comparison_was_only_reported_arithmetic"])

    def test_reject_forged_geometry_acceptance(self):
        p=copy.deepcopy(self.paper)
        p["explicit_decision"]["canonical_promotion_allowed"]=True
        with self.assertRaisesRegex(ValueError,"cannot promote"):
            self.check(p)

    def test_reject_forged_source_full_notch_table(self):
        p=copy.deepcopy(self.paper)
        p["male_table_primary"]["notch_distances_full_level_table_available"]=True
        with self.assertRaisesRegex(ValueError,"notch"):
            self.check(p)

    def test_reject_forged_sternum_endpoint_match(self):
        p=copy.deepcopy(self.paper)
        p["comparative_existing_evidence"]["matching_physical_endpoints_independently_confirmed"]=True
        with self.assertRaisesRegex(ValueError,"equivalence"):
            self.check(p)

    def test_reject_original_paper_mean_mutation(self):
        p=copy.deepcopy(self.paper)
        p["male_table_primary"]["total_sternum_length_cm"]["mean"]=15.41
        with self.assertRaisesRegex(ValueError,"numeric mismatch"):
            self.check(p)

    def test_reject_original_paper_SD_mutation(self):
        p=copy.deepcopy(self.paper)
        p["male_table_primary"]["manubrium_length_cm"]["sd"]=1.5
        with self.assertRaisesRegex(ValueError,"numeric mismatch"):
            self.check(p)

    def test_reject_claimed_pdf_byte_verification(self):
        p=copy.deepcopy(self.paper)
        p["source"]["pdf_bytes_locally_downloaded_and_hash_verified"]=True
        with self.assertRaisesRegex(ValueError,"downloaded"):
            self.check(p)

    def test_reject_changed_original_primary_source_identity(self):
        p=copy.deepcopy(self.paper)
        p["source"]["pubmed"]="0000000"
        with self.assertRaisesRegex(ValueError,"identity"):
            self.check(p)

    def test_reject_missing_original_prior_sternum_measurements(self):
        prior=copy.deepcopy(self.prior)
        prior["a003"]["manubriosternal_depth_mm"]=55.2
        with self.assertRaisesRegex(ValueError,"Historical"):
            self.check(prior=prior)

    def test_reject_unsafe_rib_control_endpoint_claim(self):
        p=copy.deepcopy(self.paper)
        p["explicit_decision"]["joint_centres_selected"]=True
        with self.assertRaisesRegex(ValueError,"cannot promote"):
            self.check(p)


if __name__=="__main__":
    unittest.main()
