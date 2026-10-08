import json
import pathlib
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
PATH = ROOT / "ORIGINAL_V1_WORK/anatomy/canonical_hand_ray_target_constraints_v1.json"


class CanonicalHandRayConstraintTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.d = json.loads(PATH.read_text())

    def test_short_middle_metacarpals_stay_reopened(self):
        for key in ("M2", "M3", "M4"):
            self.assertEqual(self.d["convergence"][key]["decision"], "RETARGET_LONGER")
            lo, hi = self.d["provisional_length_corridors_mm"][key]
            self.assertLess(self.d["a003_mm"][key], lo)
            self.assertLess(lo, hi)

    def test_first_and_fifth_are_not_blindly_lengthened(self):
        self.assertIn("RETAIN", self.d["convergence"]["M1"]["decision"])
        self.assertIn(self.d["convergence"]["M5"]["decision"], ("RETAIN_OR_MINOR_ADJUST",))

    def test_ray_targets_are_not_frozen_coordinates(self):
        self.assertEqual(
            self.d["status"],
            "RAY_LENGTH_CONSTRAINTS_READY_CMC_MCP_COORDINATES_NOT_FROZEN",
        )


if __name__ == "__main__":
    unittest.main()
