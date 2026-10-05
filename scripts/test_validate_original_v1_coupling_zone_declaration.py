"""Tests for coupling-zone declaration validation."""
import copy,importlib.util
from pathlib import Path
import unittest

MODULE_PATH=Path(__file__).with_name("validate_original_v1_coupling_zone_declaration.py")
SPEC=importlib.util.spec_from_file_location("coupling_decl",MODULE_PATH)
mod=importlib.util.module_from_spec(SPEC); SPEC.loader.exec_module(mod)

class CouplingZoneDeclarationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.c=mod.read(mod.COUPLING); cls.h=mod.read(mod.HUMAN)

    def fixture(self):
        return {
            "schema_version":1,"status":"candidate_declaration","production_approved":False,
            "candidate_revision":"r96","candidate_sha256":"a"*64,
            "coupling_system_id":"CP-PEC-AX-002","side":"left",
            "vertex_ids":[1,2,3],
            "mirror_rule":"x -> -x",
            "anchor_groups":[
                {"name":"chest_root","bones":["spine_03","clavicle_l"]},
                {"name":"humeral_insertion","bones":["upperarm_l"]}
            ],
            "allowed_bones":["spine_03","clavicle_l","upperarm_l"],
            "protected_bones":[],
            "topology_change_allowed":False,
            "rest_geometry_change_allowed":False,
            "expected_human_behaviour":["pec stays chest-rooted while insertion follows humerus"],
            "forbidden_visual_failures":["membrane","trench"],
            "human_evidence_ids":["HE-AX-001","HE-AX-002"]
        }

    def test_fixture_valid(self):
        self.assertTrue(mod.validate(self.fixture(),self.c,self.h))

    def test_duplicate_vertices_rejected(self):
        bad=self.fixture(); bad["vertex_ids"]=[1,1]
        with self.assertRaisesRegex(ValueError,"duplicates"): mod.validate(bad,self.c,self.h)

    def test_unknown_system_rejected(self):
        bad=self.fixture(); bad["coupling_system_id"]="CP-NOT-REAL-999"
        with self.assertRaisesRegex(ValueError,"unknown coupling_system_id"): mod.validate(bad,self.c,self.h)

    def test_human_evidence_required(self):
        bad=self.fixture(); bad["human_evidence_ids"]=[]
        with self.assertRaisesRegex(ValueError,"human_evidence_ids required"): mod.validate(bad,self.c,self.h)

if __name__=="__main__": unittest.main()
