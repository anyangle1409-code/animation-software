"""Tests for whole-body surface visual evidence requirements."""
import copy
import importlib.util
from pathlib import Path
import unittest

MODULE_PATH=Path(__file__).with_name("validate_original_v1_surface_visual_evidence.py")
SPEC=importlib.util.spec_from_file_location("surface_visual",MODULE_PATH)
mod=importlib.util.module_from_spec(SPEC); SPEC.loader.exec_module(mod)

class SurfaceVisualEvidenceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data=mod.read(mod.VISUAL)
        cls.master=mod.read(mod.MASTER)
        cls.human=mod.read(mod.HUMAN)

    def test_live_requirements_valid(self):
        out=mod.validate(self.data,self.master,self.human)
        self.assertEqual(out["regions"],12)

    def test_every_region_requires_return_transition(self):
        self.assertIn("return_transition",self.data["required_states"])

    def test_unknown_visual_reference_fails(self):
        bad=copy.deepcopy(self.data)
        bad["regions"][0]["current_visual_evidence_ids"]=["HE-NOT-REAL"]
        with self.assertRaisesRegex(ValueError,"unknown visual evidence ids"):
            mod.validate(bad,self.master,self.human)

    def test_incomplete_region_must_state_remaining_needs(self):
        bad=copy.deepcopy(self.data)
        bad["regions"][0]["state"]="partial"
        bad["regions"][0]["needs"]=[]
        with self.assertRaisesRegex(ValueError,"must state remaining needs"):
            mod.validate(bad,self.master,self.human)

if __name__=="__main__":
    unittest.main()
