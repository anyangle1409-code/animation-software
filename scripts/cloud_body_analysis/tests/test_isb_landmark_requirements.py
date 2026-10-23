"""Never infer anatomical landmark positions or sides from Blender bone names."""
import copy
import importlib.util
from pathlib import Path
import unittest

MODULE = Path(__file__).resolve().parents[1] / "isb_landmark_requirements.py"
SPEC = importlib.util.spec_from_file_location("isb_landmark_requirements", MODULE)
mod = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(mod)

class ISBLandmarkChecklistTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.reference = mod.load()

    def test_all_landmarks_unbound_and_unapproved(self):
        self.assertEqual(len(self.reference["landmarks"]), 46)
        self.assertEqual(mod.validate(self.reference), [])
        self.assertFalse(self.reference["native_bindings_approved"])
        self.assertFalse(self.reference["hard_limits_approved"])
        for x in self.reference["landmarks"]:
            self.assertTrue(all(x[k] is None for k in mod.FIELDS_MUST_BE_NULL))
            self.assertTrue(all(x[k] is False for k in mod.FIELDS_MUST_BE_FALSE))

    def test_shoulder_landmarks_and_side_pairing(self):
        names = {x["id"] for x in self.reference["landmarks"]}
        for side in ("L", "R"):
            for item in ("scapula.TS", "scapula.AI", "scapula.AA",
                         "clavicle.SC", "clavicle.AC", "humerus.GH_CENTER",
                         "humerus.EL", "humerus.EM", "forearm.RS", "forearm.US"):
                self.assertIn("hgpt.landmark." + item + "." + side, names)

    def test_no_automatic_bone_or_mesh_attachment(self):
        altered = copy.deepcopy(self.reference)
        altered["landmarks"][0]["model_bone_id"] = "spine_03"
        self.assertTrue(any("remain NULL" in e for e in mod.validate(altered)))
        altered = copy.deepcopy(self.reference)
        altered["landmarks"][1]["model_mesh_vertex_id"] = 77
        self.assertTrue(any("remain NULL" in e for e in mod.validate(altered)))

    def test_anatomical_side_cannot_be_claimed(self):
        altered = copy.deepcopy(self.reference)
        altered["landmarks"][4]["anatomical_side_verified"] = True
        self.assertTrue(any("cannot be approved" in e for e in mod.validate(altered)))

    def test_reject_unearned_segment_axes(self):
        altered = copy.deepcopy(self.reference)
        altered["segment_requirements"][0]["isb_axes_defined"] = True
        self.assertTrue(any("unearned ISB" in e for e in mod.validate(altered)))

    def test_reject_incomplete_pair_and_missing_midline(self):
        altered = copy.deepcopy(self.reference)
        altered["landmarks"] = altered["landmarks"][:-1]
        altered["landmark_count"] -= 1
        errors = mod.validate(altered)
        self.assertTrue(any("coverage" in e for e in errors))
        self.assertTrue(any("contralateral" in e for e in errors))
        altered = copy.deepcopy(self.reference)
        altered["landmarks"][0]["id"] = "hgpt.landmark.thorax.MISSING.MIDLINE"
        self.assertTrue(any("thorax landmark frame incomplete" in e for e in mod.validate(altered)))

    def test_no_false_muscle_highlight_or_hard_limits(self):
        altered = copy.deepcopy(self.reference)
        altered["hard_limits_approved"] = True
        self.assertTrue(any("unearned native or ROM" in e for e in mod.validate(altered)))
        altered = copy.deepcopy(self.reference)
        altered["muscle_highlighting"] = "IMPLEMENTED"
        self.assertTrue(any("deferred" in e for e in mod.validate(altered)))

    def test_no_blender_write_operations(self):
        code = MODULE.read_text()
        self.assertNotIn("import bpy", code)
        self.assertNotIn("save_as_mainfile", code)

if __name__ == "__main__":
    unittest.main()
