import json
import math
import pathlib
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
PATH = ROOT / "ORIGINAL_V1_WORK/anatomy/canonical_shoulder_frame_mapping_v1.json"


class ShoulderFrameMappingTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.d = json.loads(PATH.read_text())

    def test_basis_matches_character_audit(self):
        b = self.d["hgpt_basis"]
        self.assertEqual(b["up"], "+Z")
        self.assertEqual(b["anterior"], "-Y")
        self.assertEqual(b["posterior"], "+Y")
        self.assertEqual(b["anatomical_left"], "+X")

    def test_relative_vectors_are_mirrors(self):
        L = self.d["mean_SC_to_AC_relative_vector_mm"]["left"]
        R = self.d["mean_SC_to_AC_relative_vector_mm"]["right"]
        self.assertAlmostEqual(L[0], -R[0], places=9)
        self.assertAlmostEqual(L[1], R[1], places=9)
        self.assertAlmostEqual(L[2], R[2], places=9)

    def test_retraction_and_elevation_signs(self):
        for side in ("left", "right"):
            v = self.d["mean_SC_to_AC_relative_vector_mm"][side]
            self.assertGreater(v[1], 0.0)  # posterior +Y
            self.assertGreater(v[2], 0.0)  # superior +Z

    def test_vector_magnitude(self):
        for side in ("left", "right"):
            v = self.d["mean_SC_to_AC_relative_vector_mm"][side]
            mag = math.sqrt(sum(x*x for x in v))
            self.assertAlmostEqual(mag, 154.8, places=9)


if __name__ == "__main__":
    unittest.main()
