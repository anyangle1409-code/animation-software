import json
import pathlib
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
TARGET = ROOT / "ORIGINAL_V1_WORK/anatomy/canonical_hyoid_geometry_targets_v1.json"
FIT = ROOT / "ORIGINAL_V1_WORK/anatomy/character_fit_r95_a003.json"


class CanonicalHyoidGeometryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.t = json.loads(TARGET.read_text())
        cls.fit = json.loads(FIT.read_text())

    def test_hyoid_remains_one_unpaired_reference_bone(self):
        h = self.fit["bones"]["hyoid"]
        self.assertEqual(h["role"], "REFERENCE")
        self.assertIsNone(h["parent"])
        self.assertEqual(h["parent_relation"]["type"], "root")
        self.assertIn("no osseous articulation", h["parent_relation"]["reason"])

    def test_local_geometry_uses_measurement_defined_adult_male_values(self):
        g = self.t["provisional_local_geometry"]["direct_2025_male_nominals_mm"]
        self.assertGreater(g["total_width"], 40.0)
        self.assertGreater(g["total_AP_length"], 30.0)
        self.assertGreater(g["greater_horn_length_left"], 25.0)
        self.assertGreater(g["greater_horn_length_right"], 25.0)
        self.assertGreater(g["lesser_horn_span"], 20.0)

    def test_a003_stick_is_not_promoted_as_whole_bone_length(self):
        a = self.t["current_a003"]
        self.assertLess(a["control_stick_length_mm"], 20.0)
        self.assertIn("no measurement-compatible", a["control_stick_semantics"])
        self.assertIn("not the same landmarks", a["marker_semantics_warning"])

    def test_position_waits_for_canonical_c3(self):
        self.assertEqual(
            self.t["decision"]["absolute_position"],
            "WAIT_FOR_CANONICAL_CERVICAL_SPINE_FRAME",
        )
        self.assertIn("C3", self.t["local_frame"]["placement_rule"])

    def test_hard_no_osseous_parent_invariant(self):
        rules = self.t["hard_invariants"]
        self.assertTrue(any("no osseous articulation" in r for r in rules))


if __name__ == "__main__":
    unittest.main()
