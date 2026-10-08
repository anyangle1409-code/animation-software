import json
import math
import pathlib
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
ANAT = ROOT / "ORIGINAL_V1_WORK/anatomy"
AXES = ANAT / "canonical_carpal_axis_targets_v1.json"
ENVELOPES = ANAT / "canonical_carpal_envelopes_v1.json"


class CanonicalCarpalTargetTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.axes = json.loads(AXES.read_text())
        cls.env = json.loads(ENVELOPES.read_text())

    def test_reported_carpal_axes_are_unit_and_mirrored(self):
        left = self.axes["HGPT_axis_unit_vectors"]["left"]
        right = self.axes["HGPT_axis_unit_vectors"]["right"]
        self.assertEqual(set(left), set(right))
        self.assertEqual(len(left), 7)
        for bone, lv in left.items():
            rv = right[bone]
            self.assertAlmostEqual(math.sqrt(sum(x*x for x in lv)), 1.0, places=12)
            self.assertAlmostEqual(math.sqrt(sum(x*x for x in rv)), 1.0, places=12)
            self.assertAlmostEqual(lv[0], -rv[0], places=12)
            self.assertAlmostEqual(lv[1], rv[1], places=12)
            self.assertAlmostEqual(lv[2], rv[2], places=12)

    def test_pisiform_is_not_invented(self):
        self.assertEqual(
            self.axes["bone_axis_definitions"]["pisiform"],
            "UNRESOLVED_NOT_REPORTED_IN_PRIMARY_ALIGNMENT_SOURCE",
        )
        self.assertNotIn("pisiform", self.axes["HGPT_axis_unit_vectors"]["left"])

    def test_all_eight_male_carpal_envelopes_are_present(self):
        expected = {"scaphoid","lunate","triquetrum","pisiform","trapezium","trapezoid","capitate","hamate"}
        self.assertEqual(set(self.env["envelopes"]), expected)
        for bone, axes in self.env["envelopes"].items():
            self.assertEqual(set(axes), {"X","Y","Z"})
            for axis, d in axes.items():
                self.assertGreater(d["mean_mm"], 0)
                self.assertGreater(d["sd_mm"], 0)
                self.assertLess(d["band_1sd_mm"][0], d["mean_mm"])
                self.assertGreater(d["band_1sd_mm"][1], d["mean_mm"])

    def test_source_axes_are_not_silently_relabelled_as_hgpt_axes(self):
        self.assertIn("Do not relabel", self.env["source_axis_note"])
        self.assertIn("HGPT mapping of source X/Y/Z", self.env["not_provided_by_this_source"])


if __name__ == "__main__":
    unittest.main()
