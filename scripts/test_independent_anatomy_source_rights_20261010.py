"""Offline adversarial source-rights and donor-overlap tests. No network/CT."""
import copy
import json
import tempfile
import unittest
from pathlib import Path

from anatomy_fit.audit_independent_source_rights import DEFAULT, validate


class IndependentSourceRightsTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.original = json.loads(DEFAULT.read_text(encoding="utf-8"))

    def clone(self):
        return copy.deepcopy(self.original)

    def test_known_source_and_cohort_identity(self):
        result = validate(self.clone())
        self.assertEqual(result["source_entries"], 7)
        self.assertEqual(result["independent_nonsoftware_donor_cohorts_at_most"], 5)
        self.assertEqual(result["one_cohort_not_two"]["BASEL_TOTAL_SEGMENTATOR_1204_CT"], 2)
        self.assertFalse(result["anatomical_readiness_changed"])

    def test_vsd_and_appendicular_model_stay_restricted(self):
        result = validate(self.clone())
        self.assertEqual(result["noncommercial_or_model_license_restricted_entries"],
                         ["totalsegmentator_appendicular_tool",
                          "vsd_lower_extremity_30_subjects"])
        self.assertFalse(result["commercial_import_approved"])
        self.assertFalse(result["source_pixels_or_meshes_downloaded"])

    def test_reject_forged_geometry_acceptance(self):
        d = self.clone()
        d["canonical_target_selection_allowed"] = True
        with self.assertRaisesRegex(ValueError, "anatomy approval"):
            validate(d)

    def test_reject_forged_commercial_import(self):
        d = self.clone()
        d["datasets"][0]["commercial_import_approved"] = True
        with self.assertRaisesRegex(ValueError, "Unsupported claim"):
            validate(d)

    def test_reject_raw_subject_data_claim(self):
        d = self.clone()
        d["datasets"][0]["raw_data_inspected_in_this_review"] = True
        with self.assertRaisesRegex(ValueError, "Unsupported claim"):
            validate(d)

    def test_reject_unquarantined_noncommercial_source(self):
        d = self.clone()
        row = next(x for x in d["datasets"] if x["id"]=="vsd_lower_extremity_30_subjects")
        row["recommended_use"] = "commercial product anatomical mesh fitting"
        with self.assertRaisesRegex(ValueError, "improperly recommended"):
            validate(d)

    def test_reject_misclassified_patient_mirror_as_independent(self):
        d = self.clone()
        row = next(x for x in d["datasets"] if x["id"]=="totalsegmentator_ribs_medotter_mirror")
        row["cohort_key"] = "NEW_INDEPENDENT_PATIENTS"
        with self.assertRaisesRegex(ValueError, "deduplication"):
            validate(d)

    def test_reject_duplicating_one_visible_human_donor(self):
        d = self.clone()
        d["datasets"].append(copy.deepcopy(d["datasets"][0]))
        with self.assertRaisesRegex(ValueError, "Duplicate"):
            validate(d)

    def test_reject_dropping_anatomical_verification_requirement(self):
        d = self.clone()
        d["evidence_chain_not_complete"].remove("articular_contact")
        with self.assertRaisesRegex(ValueError, "source verification"):
            validate(d)

    def test_reject_unknown_source_with_provisional_free_license(self):
        d = self.clone()
        d["datasets"][0]["id"] = "imaginary_unlicensed_source"
        with self.assertRaisesRegex(ValueError, "source IDs"):
            validate(d)

    def test_reject_double_counting_vsd_feet_as_new_30_donors(self):
        d = self.clone()
        d["datasets"][6]["cohort_key"] = "VSD_30_DIFFERENT_CASES"
        with self.assertRaisesRegex(ValueError, "deduplication"):
            validate(d)

    def test_reject_unsafe_provenance_url(self):
        d = self.clone()
        d["datasets"][0]["source_url"] = "http://example.com"
        with self.assertRaisesRegex(ValueError, "source URL"):
            validate(d)

    def test_reject_missing_rights_barrier(self):
        d = self.clone()
        d["explicit_rulings"]["may_import_noncommercial_data_in_app"] = True
        with self.assertRaisesRegex(ValueError, "non-promotion"):
            validate(d)


if __name__ == "__main__":
    unittest.main()
