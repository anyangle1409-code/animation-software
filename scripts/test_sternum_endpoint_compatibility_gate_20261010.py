"""Safety regressions for noncanonical sternum-source compatibility and 3D underdetermination."""
import copy
import json
import math
import unittest
from anatomy_fit.sternum_endpoint_compatibility_gate import (
    CONTRACT, GEO, OLDER, SELT, THAI, audit,
    check_contract, compare_ids, demonstrate_3d_nondetermination,
    git_blob_sha_lf, verify_original_input_pins, EXPECTED_PINNED_INPUTS, ANATOMY,
)

class SternumEndpointContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.manifest=json.loads(CONTRACT.read_text(encoding="utf-8"))
        cls.old=json.loads(OLDER.read_text(encoding="utf-8"))
        cls.geo=json.loads(GEO.read_text(encoding="utf-8"))
        cls.sel=json.loads(SELT.read_text(encoding="utf-8"))
        cls.thai=json.loads(THAI.read_text(encoding="utf-8"))

    def evidence(self):
        return (copy.deepcopy(self.manifest),copy.deepcopy(self.sel),
                copy.deepcopy(self.thai),copy.deepcopy(self.old),
                copy.deepcopy(self.geo))

    def check(self,items=None):
        c,s,t,o,g=items if items is not None else self.evidence()
        return check_contract(c,s,t,o,g)

    def outcome(self,items=None):
        c,s,t,o,g=items if items is not None else self.evidence()
        return audit(c,s,t,o,g)

    def test_all_twelve_source_measurements_and_five_incompatible_pairs(self):
        out=self.outcome()
        self.assertEqual(out["source_measurement_rows"],12)
        self.assertEqual(len(out["forbidden_cross_source_comparisons"]),5)
        self.assertTrue(out["all_automatic_sternum_targets_rejected"])
        self.assertTrue(out["no_canonical_geometry_changed"])
        self.assertTrue(out["no_CP1_gate_promotion"])

    def test_xiphoid_included_in_2006_but_not_2018(self):
        values=self.check()["measurement_rows"]
        self.assertIs(values["SELTHOFER2006_WHOLE"]["xiphoid_included"],True)
        self.assertIs(values["TURKEY2018_CL"]["xiphoid_included"],False)
        self.assertIs(values["A003_JUGULAR_TO_XIPHISTERNAL_CHORD"]["xiphoid_included"],False)
        result=compare_ids("SELTHOFER2006_WHOLE","TURKEY2018_CL",self.check())
        self.assertEqual(result["reason"],"DISTAL_XIPHOID_INCLUDED_VS_EXCLUDED")
        self.assertEqual(result["status"],"REJECT_FOR_CANONICAL_TARGET")

    def test_cross_study_sum_of_means_not_direct_individual_composite(self):
        rows=self.check()["measurement_rows"]
        self.assertEqual(rows["SELTHOFER2006_SUM_M_B"]["value_mm"],164.9)
        self.assertIsNone(rows["SELTHOFER2006_SUM_M_B"]["sd_mm"])
        self.assertEqual(rows["SELTHOFER2006_SUM_M_B"]["source_measure"],
                         "derived_sum_of_two_group_means_not_subject_aggregates")
        pair=compare_ids("TURKEY2018_CL","SELTHOFER2006_SUM_M_B",self.check())
        self.assertEqual(pair["reason"],"DERIVED_SUM_OF_COHORT_MEANS_VS_DIRECT_COMPOSITE_DIFFERENT_STUDIES")

    def test_Thai_intercostal_vs_model_axis_projection_rejected(self):
        pair=compare_ids("THAI2022_ICL23","A003_LEVEL2_3_Z",self.check())
        self.assertEqual(pair["reason"],"3D_COSTAL_FACET_SPACING_VS_MODEL_Z_PROJECTION")
        self.assertFalse(pair["automatic_sternum_mesh_retarget_allowed"])

    def test_two_distinct_3d_chains_share_all_three_reported_intervals(self):
        d=demonstrate_3d_nondetermination(self.check())
        self.assertEqual(d["identical_three_local_facet_intervals_mm"],[29.3,25.2,19.56])
        self.assertAlmostEqual(d["collinear_chain_end_to_end_mm"],74.06,places=4)
        self.assertLess(d["turned_chain_end_to_end_mm"],74.06)
        self.assertTrue(d["nonunique_3d_geometry_from_three_distances"])
        self.assertFalse(d["source_3d_rib_contact_positions_selected"])

    def test_2006_total_sternum_to_model_control_not_a_valid_match(self):
        pair=compare_ids("SELTHOFER2006_WHOLE","A003_JUGULAR_TO_XIPHISTERNAL_CHORD",self.check())
        self.assertEqual(pair["status"],"REJECT_FOR_CANONICAL_TARGET")

    def test_unknown_or_duplicate_source_pair_is_refused(self):
        with self.assertRaisesRegex(ValueError,"Unknown or identical"):
            compare_ids("UNKNOWN","TURKEY2018_CL",self.check())
        with self.assertRaisesRegex(ValueError,"Unknown or identical"):
            compare_ids("TURKEY2018_CL","TURKEY2018_CL",self.check())

    def test_nondeclared_generic_comparison_fails_closed(self):
        result=compare_ids("TURKEY2018_XIPHOID","THAI2022_ICL34",self.check())
        self.assertEqual(result["reason"],"DIFFERENT_BONE_MEASUREMENT_SEMANTICS")
        self.assertFalse(result["automatic_sternum_mesh_retarget_allowed"])

    def test_reject_declaring_legacy_2018_total_xiphoid_inclusive(self):
        vals=list(self.evidence())
        row=next(x for x in vals[0]["measurement_terms"] if x["id"]=="TURKEY2018_CL")
        row["xiphoid_included"]=True
        with self.assertRaisesRegex(ValueError,"Anatomical endpoint"):
            self.check(vals)

    def test_reject_forged_3d_sternal_cartilage_registration(self):
        vals=list(self.evidence())
        row=next(x for x in vals[0]["measurement_terms"] if x["id"]=="THAI2022_ICL34")
        row["source_to_HGPT_registered"]=True
        with self.assertRaisesRegex(ValueError,"Unsourced registration"):
            self.check(vals)

    def test_reject_forged_182cm_population_conditioning(self):
        vals=list(self.evidence())
        row=next(x for x in vals[0]["measurement_terms"] if x["id"]=="THAI2022_ICL45")
        row["stature_182cm_conditioned"]=True
        with self.assertRaisesRegex(ValueError,"Unsourced registration"):
            self.check(vals)

    def test_reject_model_candidate_passed_off_as_a_human_measurement(self):
        vals=list(self.evidence())
        row=next(x for x in vals[0]["measurement_terms"] if x["id"]=="A003_LEVEL2_3_Z")
        row["source_measure"]="direct_group_mean"
        with self.assertRaisesRegex(ValueError,"Unapproved mesh/model"):
            self.check(vals)

    def test_reject_mischaracterised_2006_derived_sum_sd(self):
        vals=list(self.evidence())
        row=next(x for x in vals[0]["measurement_terms"] if x["id"]=="SELTHOFER2006_SUM_M_B")
        row["sd_mm"]=13.1
        with self.assertRaisesRegex(ValueError,"Anatomical endpoint"):
            self.check(vals)

    def test_reject_forged_inclusion_of_absent_costonotch_levels(self):
        vals=list(self.evidence())
        vals[0]["source_eligibility"]["no_full_1_to7_costal_facet_3d_contact_coords"]=False
        with self.assertRaisesRegex(ValueError,"safeguards"):
            self.check(vals)

    def test_reject_automatic_acceptance_claim(self):
        vals=list(self.evidence())
        vals[0]["approval"]["allow_CP1_Gate6_promotion"]=True
        with self.assertRaisesRegex(ValueError,"Unauthorized anatomy"):
            self.check(vals)

    def test_reject_source_pin_substitution(self):
        vals=list(self.evidence())
        vals[0]["immutable_existing_sources"][2]["git_blob_sha"]="0"*40
        with self.assertRaisesRegex(ValueError,"source pin"):
            self.check(vals)

    def test_reject_duplicate_source_measurement_id(self):
        vals=list(self.evidence())
        vals[0]["measurement_terms"].append(copy.deepcopy(vals[0]["measurement_terms"][0]))
        with self.assertRaisesRegex(ValueError,"duplicate or substituted"):
            self.check(vals)

    def test_reject_dropped_forbidden_crossstudy_pair(self):
        vals=list(self.evidence())
        vals[0]["forbidden_pairs"]=vals[0]["forbidden_pairs"][:-1]
        with self.assertRaisesRegex(ValueError,"Missing forbidden"):
            self.check(vals)

    def test_reject_changed_unaccepted_old_control_frame(self):
        vals=list(self.evidence())
        vals[4]["current_a003"]["tail_definition"]="distal tip of xiphoid"
        with self.assertRaisesRegex(ValueError,"a003 endpoint"):
            self.check(vals)

    def test_reject_historical_semantic_key_mutation(self):
        vals=list(self.evidence())
        vals[3]["population_male_means_mm"]["total_including_xiphoid_turkey_CT"]["mean"]=208.6
        with self.assertRaisesRegex(ValueError,"Legacy numerical datum"):
            self.check(vals)

    def test_actual_four_git_source_blobs_are_immutable(self):
        verify_original_input_pins()
        self.assertEqual(len(EXPECTED_PINNED_INPUTS),4)
        for name,pin in EXPECTED_PINNED_INPUTS.items():
            raw=(ANATOMY / name).read_bytes()
            self.assertEqual(git_blob_sha_lf(raw),pin)
            self.assertNotEqual(git_blob_sha_lf(raw+b" "),pin)

    def test_crlf_checkout_source_bytes_have_same_git_normalized_identity(self):
        first=next(iter(EXPECTED_PINNED_INPUTS))
        raw=(ANATOMY / first).read_bytes()
        lf=raw.replace(b"\r\n",b"\n")
        windows=lf.replace(b"\n",b"\r\n")
        self.assertEqual(git_blob_sha_lf(lf),git_blob_sha_lf(windows))

    def test_no_canonical_source_values_or_cohorts_are_rescaled(self):
        d=self.outcome()
        self.assertTrue(d["Selthofer_208_6mm_and_Turkey_154_1mm_are_not_comparable_totals"])
        self.assertEqual(d["Selthofer_sum_M_B_minus_Turkey_CL_diagnostic_mm"],10.8)
        self.assertTrue(d["legacy_Turkey_source_key_misnamed"])
        self.assertFalse(d["legacy_Turkey_154_1mm_includes_xiphoid"])


if __name__=="__main__":
    unittest.main()
