import json
import pathlib
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]

TARGETS = ROOT / "ORIGINAL_V1_WORK/anatomy/canonical_skeleton_proportion_targets_v1.json"
GAP = ROOT / "ORIGINAL_V1_WORK/anatomy/canonical_skeleton_rebuild_gap_v1.json"
HAND = ROOT / "ORIGINAL_V1_WORK/anatomy/canonical_hand_proportion_audit_v1.json"
FOOT = ROOT / "ORIGINAL_V1_WORK/anatomy/canonical_foot_proportion_audit_v1.json"
FOREARM = ROOT / "ORIGINAL_V1_WORK/anatomy/canonical_forearm_proportion_audit_v1.json"
TARSAL = ROOT / "ORIGINAL_V1_WORK/anatomy/canonical_tarsal_geometry_audit_v1.json"
SPINE = ROOT / "ORIGINAL_V1_WORK/anatomy/canonical_spine_geometry_audit_v1.json"


class CanonicalSkeletonRebuildTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.targets = json.loads(TARGETS.read_text())
        cls.gap = json.loads(GAP.read_text())
        cls.hand = json.loads(HAND.read_text())
        cls.foot = json.loads(FOOT.read_text())
        cls.forearm = json.loads(FOREARM.read_text())
        cls.tarsal = json.loads(TARSAL.read_text())
        cls.spine = json.loads(SPINE.read_text())

    def test_skeleton_first_policy_is_hard_gate(self):
        owner = self.targets["owner_decision"]
        self.assertTrue(owner["skeleton_is_source_of_truth"])
        self.assertTrue(owner["mesh_refits_to_skeleton"])
        self.assertEqual(owner["current_a003_role"], "audit baseline only")
        self.assertEqual(self.targets["status"], "PROVISIONAL_REFERENCE_NOT_FROZEN")

    def test_gap_inventory_accounts_for_all_206_bones(self):
        s = self.gap["summary"]
        self.assertEqual(s["total_bones"], 206)
        self.assertEqual(s["moderate_confidence"] + s["low_confidence"], 206)
        self.assertEqual(s["low_confidence"], 193)
        self.assertEqual(
            s["proportional_low"] + s["surface_landmark_low"] + s["surface_station_low"],
            s["low_confidence"],
        )

    def test_hand_shortness_is_not_hidden(self):
        b = self.hand["bones"]
        self.assertLess(b["metacarpal_2"]["z_vs_ayd1998_mean"], -2.0)
        self.assertLess(b["metacarpal_3"]["z_vs_ayd1998_mean"], -2.0)
        self.assertLess(b["metacarpal_4"]["difference_from_2025_ct_mean_mm"], -5.0)
        self.assertEqual(self.hand["status"], "PROVISIONAL_HAND_TARGET_EVIDENCE_NOT_FROZEN")

    def test_foot_surface_defect_and_metatarsal_source_conflict_are_both_retained(self):
        b = self.foot["bones"]
        for key in [f"metatarsal_{i}" for i in range(1, 6)]:
            self.assertGreater(b[key]["z_vs_male_mean"], 2.0, key)
        x = self.foot["stature_conditioned_crosscheck"]
        self.assertGreater(x["spanish_male_M1_max_predicted_mm"], 75.0)
        self.assertGreater(x["portuguese_M2_max_predicted_mm"], 85.0)
        self.assertGreater(self.foot["surface_context"]["z"], 2.0)
        self.assertEqual(
            self.foot["status"],
            "FOOT_SURFACE_PROPORTION_DEFECT_CONFIRMED_SKELETAL_FOREFOOT_TARGET_REOPENED_NOT_FROZEN",
        )

    def test_forearm_radius_and_ulna_are_not_forced_to_same_solution(self):
        d = self.forearm["provisional_decisions"]
        self.assertEqual(d["radius"], "REOPEN_AND_RETARGET")
        self.assertEqual(d["ulna"], "REOPEN_FOR_ENDPOINT_DEFINED_CROSSCHECK_NOT_YET_LENGTHEN")
        self.assertLess(
            self.forearm["stature_conditioned_ansur_chain"]["current_radius_osteometric_proxy_difference_mm"],
            -20.0,
        )

    def test_tarsal_sticks_are_not_treated_as_whole_bone_lengths(self):
        c = self.tarsal["current_a003_reference_sticks_mm"]
        self.assertLess(c["calcaneus"], 25.0)
        self.assertGreater(c["cuboid"], 45.0)
        self.assertEqual(
            self.tarsal["status"],
            "TARSAL_GEOMETRY_REBUILD_REQUIRED_NUMERIC_CENTRES_NOT_FROZEN",
        )

    def test_spine_has_explicit_zero_disc_gap_defect(self):
        gaps = self.spine["current_interlevel_contact_check"]
        self.assertTrue(gaps)
        for g in gaps:
            self.assertAlmostEqual(g["gap_between_parent_tail_and_child_head_mm"], 0.0, places=9)
        self.assertEqual(
            self.spine["status"],
            "SPINE_GEOMETRY_DEFECT_CONFIRMED_CANONICAL_REBUILD_REQUIRED",
        )


if __name__ == "__main__":
    unittest.main()
