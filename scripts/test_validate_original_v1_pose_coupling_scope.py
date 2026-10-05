"""Tests for pose -> connected-tissue scope report validation."""
import copy,importlib.util
from pathlib import Path
import unittest

MODULE_PATH=Path(__file__).with_name("validate_original_v1_pose_coupling_scope.py")
SPEC=importlib.util.spec_from_file_location("pose_scope",MODULE_PATH)
mod=importlib.util.module_from_spec(SPEC); SPEC.loader.exec_module(mod)

class PoseCouplingScopeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.c=mod.read(mod.COUPLING); cls.t=mod.read(mod.TRIGGER)

    def fixture(self):
        systems=[x["id"] for x in self.c["coupling_systems"]]
        needed={"CP-PEC-AX-002","CP-POSTAX-003","CP-DELTOID-004","CP-ARM-005","CP-NECK-TRAP-001"}
        ordered=[x for x in systems if x in needed]
        return {
            "schema_version":1,
            "status":"READ_ONLY_POSE_COUPLING_SCOPE",
            "candidate":"fixture.blend",
            "candidate_sha256":"a"*64,
            "pose_definition_script":"pose.py",
            "pose_definition_script_sha256":"b"*64,
            "trigger_map":"ORIGINAL_V1_JOINT_TISSUE_TRIGGER_MAP.json",
            "trigger_map_sha256":"c"*64,
            "coupling_map":"ORIGINAL_V1_ANATOMICAL_COUPLING_MAP.json",
            "coupling_map_sha256":"d"*64,
            "poses":{
                "press_top":{
                    "moved_bone_count":1,
                    "moved_bones":[{"bone":"upperarm_l","rotation_deg":90.0,"translation_m":0.0,"moved":True}],
                    "trigger_matches":[{
                        "trigger_rule_id":"JT-UPPERARM-005",
                        "joint_family":"humerus",
                        "matched_bones":["upperarm_l"],
                        "required_coupling_system_ids":["CP-PEC-AX-002","CP-POSTAX-003","CP-DELTOID-004","CP-ARM-005","CP-NECK-TRAP-001"],
                        "rationale":"fixture"
                    }],
                    "required_coupling_system_ids":ordered,
                    "required_coupling_system_count":len(ordered),
                    "review_rule":"fixture"
                }
            },
            "source_saved_or_modified":False
        }

    def test_fixture_valid(self):
        self.assertEqual(mod.validate(self.fixture(),self.c,self.t)["status"],"PASS")

    def test_missing_connected_system_is_rejected(self):
        bad=self.fixture()
        bad["poses"]["press_top"]["required_coupling_system_ids"]=bad["poses"]["press_top"]["required_coupling_system_ids"][:-1]
        bad["poses"]["press_top"]["required_coupling_system_count"]-=1
        with self.assertRaisesRegex(ValueError,"order/coverage differs"):
            mod.validate(bad,self.c,self.t)

    def test_moved_bone_without_scope_rejected(self):
        bad=self.fixture()
        bad["poses"]["press_top"]["trigger_matches"]=[]
        bad["poses"]["press_top"]["required_coupling_system_ids"]=[]
        bad["poses"]["press_top"]["required_coupling_system_count"]=0
        with self.assertRaisesRegex(ValueError,"produced no connected-tissue review scope"):
            mod.validate(bad,self.c,self.t)

if __name__=="__main__": unittest.main()
