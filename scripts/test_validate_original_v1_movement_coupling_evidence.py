"""Tests for automatic joint->tissue movement coupling evidence."""
import importlib.util
from pathlib import Path
import unittest

MODULE_PATH=Path(__file__).with_name("validate_original_v1_movement_coupling_evidence.py")
SPEC=importlib.util.spec_from_file_location("movement_coupling",MODULE_PATH)
mod=importlib.util.module_from_spec(SPEC); SPEC.loader.exec_module(mod)

class MovementCouplingTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.triggers=mod.read(mod.TRIGGERS)
        cls.master=mod.read(mod.MASTER)

    def fixture(self):
        bones=["upperarm_l","clavicle_l","scapula_l"]
        required,_=mod.derive(self.triggers,bones)
        return {
          "schema_version":1,
          "status":"MOVEMENT_COUPLING_EVIDENCE_IN_PROGRESS",
          "production_approved":False,
          "candidate_revision":"r96",
          "candidate_sha256":"a"*64,
          "source_branch":"fixture",
          "samples":[{
            "sample_id":"press_mid_l",
            "movement_family":"vertical_push",
            "fraction":0.5,
            "moved_bones":bones,
            "required_coupling_system_ids":required,
            "reviewed_coupling_system_ids":required,
            "evidence_refs":["capture.json"],
            "contact_refs":[],
            "state":"COMPLETE"
          }]
        }

    def test_humerus_triggers_chest_axilla_and_deltoid(self):
        required,_=mod.derive(self.triggers,["upperarm_l"])
        self.assertIn("CP-PEC-AX-002",required)
        self.assertIn("CP-POSTAX-003",required)
        self.assertIn("CP-DELTOID-004",required)

    def test_complete_fixture_passes(self):
        out=mod.validate(self.fixture(),self.triggers,self.master,True)
        self.assertEqual(out["complete"],1)

    def test_missing_triggered_system_blocks_complete(self):
        bad=self.fixture()
        bad["samples"][0]["reviewed_coupling_system_ids"]=bad["samples"][0]["reviewed_coupling_system_ids"][:-1]
        with self.assertRaisesRegex(ValueError,"missing reviewed coupling systems"):
            mod.validate(bad,self.triggers,self.master)

    def test_declared_required_set_cannot_be_hand_minimized(self):
        bad=self.fixture()
        bad["samples"][0]["required_coupling_system_ids"]=[]
        with self.assertRaisesRegex(ValueError,"trigger-derived"):
            mod.validate(bad,self.triggers,self.master)

    def test_unknown_bone_only_cannot_pass_complete(self):
        bad=self.fixture()
        bad["samples"][0]["moved_bones"]=["mystery_bone"]
        bad["samples"][0]["required_coupling_system_ids"]=[]
        bad["samples"][0]["reviewed_coupling_system_ids"]=[]
        with self.assertRaisesRegex(ValueError,"matched no trigger rules"):
            mod.validate(bad,self.triggers,self.master)

if __name__=="__main__":
    unittest.main()
