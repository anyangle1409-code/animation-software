"""Tests for the authoritative anatomical coupling map."""
import copy
import importlib.util
from pathlib import Path
import unittest

MODULE_PATH=Path(__file__).with_name("validate_original_v1_anatomical_coupling.py")
SPEC=importlib.util.spec_from_file_location("anatomical_coupling",MODULE_PATH)
mod=importlib.util.module_from_spec(SPEC); SPEC.loader.exec_module(mod)

class AnatomicalCouplingTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.cmap=mod.read(mod.MAP)
        cls.master=mod.read(mod.MASTER)
        cls.human=mod.read(mod.HUMAN)

    def test_live_map_valid(self):
        self.assertTrue(mod.validate(self.cmap,self.master,self.human))

    def test_all_master_regions_are_covered(self):
        covered={r for row in self.cmap["coupling_systems"] for r in row["body_regions"]}
        expected={x["id"] for x in self.master["body_regions"]}
        self.assertEqual(covered & expected,expected)

    def test_all_master_movements_are_covered(self):
        covered={m for row in self.cmap["coupling_systems"] for m in row["movement_families"]}
        self.assertEqual(covered,set(self.master["movement_families"]))

    def test_missing_distal_anchor_fails(self):
        bad=copy.deepcopy(self.cmap)
        bad["coupling_systems"][0]["distal_anchors"]=[]
        with self.assertRaisesRegex(ValueError,"distal_anchors"):
            mod.validate(bad,self.master,self.human)

    def test_unknown_evidence_fails(self):
        bad=copy.deepcopy(self.cmap)
        bad["coupling_systems"][0]["evidence_ids"]=["HE-NOT-REAL"]
        with self.assertRaisesRegex(ValueError,"unknown human evidence"):
            mod.validate(bad,self.master,self.human)

    def test_map_may_not_claim_production_approval(self):
        bad=copy.deepcopy(self.cmap); bad["production_approved"]=True
        with self.assertRaisesRegex(ValueError,"may not claim production approval"):
            mod.validate(bad,self.master,self.human)

if __name__=="__main__":
    unittest.main()
