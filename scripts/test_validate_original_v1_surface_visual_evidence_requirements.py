"""Tests for real-human surface visual evidence requirements."""
import copy,importlib.util
from pathlib import Path
import unittest

MODULE_PATH=Path(__file__).with_name("validate_original_v1_surface_visual_evidence_requirements.py")
SPEC=importlib.util.spec_from_file_location("surface_visual",MODULE_PATH)
mod=importlib.util.module_from_spec(SPEC); SPEC.loader.exec_module(mod)

class SurfaceVisualRequirementsTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.req=mod.read(mod.REQ); cls.master=mod.read(mod.MASTER); cls.human=mod.read(mod.HUMAN)

    def test_live_requirements_valid(self):
        self.assertTrue(mod.validate(self.req,self.master,self.human))

    def test_all_body_regions_are_present(self):
        self.assertEqual([x["id"] for x in self.req["regions"]],[x["id"] for x in self.master["body_regions"]])

    def test_nonvisual_source_cannot_be_used_as_visual(self):
        bad=copy.deepcopy(self.req)
        row=bad["regions"][0]; row["current_visual_evidence_ids"]=["HE-NECK-001"]; row["state"]="partial"
        with self.assertRaisesRegex(ValueError,"not a visual source type"):
            mod.validate(bad,self.master,self.human)

if __name__=="__main__": unittest.main()
