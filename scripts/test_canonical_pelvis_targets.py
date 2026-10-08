import json
import pathlib
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
TARGET = ROOT / "ORIGINAL_V1_WORK/anatomy/canonical_pelvis_landmark_targets_v1.json"
FIT = ROOT / "ORIGINAL_V1_WORK/anatomy/character_fit_r95_a003.json"


class CanonicalPelvisTargetTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.t = json.loads(TARGET.read_text())
        cls.fit = json.loads(FIT.read_text())

    def test_hjc_spacing_is_inside_independent_male_ct_band(self):
        c = self.t["evidence_convergence"]["interacetabular_HJC"]
        self.assertLess(abs(c["z_vs_Tannenbaum"]), 1.0)

    def test_mesh_asis_is_not_frozen_as_bone_target(self):
        self.assertEqual(
            self.t["provisional_decisions"]["ASIS_surface_points"],
            "DO_NOT_FREEZE_REBUILD_BONY_LANDMARKS",
        )
        self.assertIn(
            "surface/groove proxies",
            self.t["evidence_convergence"]["inter_ASIS"]["interpretation"],
        )

    def test_acetabular_scale_uses_multiple_sources(self):
        a = self.t["evidence_convergence"]["acetabular_diameter"]
        self.assertGreaterEqual(a["provisional_corridor_mm"][0], 45.0)
        self.assertLessEqual(a["provisional_corridor_mm"][1], 60.0)
        self.assertNotEqual(a["source_1_mm"]["mean"], a["source_2_mm"]["mean"])

    def test_adult_os_coxae_count_policy_is_preserved(self):
        rules = self.t["hard_invariants"]
        self.assertTrue(any("one conventional bone" in r for r in rules))
        self.assertTrue(any("pubic symphysis" in r for r in rules))

    def test_required_landmarks_include_ring_closure_and_acetabulum(self):
        required = set(self.t["canonical_landmarks_required_per_side"])
        for name in {
            "ASIS",
            "PSIS",
            "ischial spine",
            "ischial tuberosity",
            "pubic symphysis contact",
            "acetabular centre/HJC",
            "SI auricular-surface centre and local frame",
        }:
            self.assertIn(name, required)


if __name__ == "__main__":
    unittest.main()
