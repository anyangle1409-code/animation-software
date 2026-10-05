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
            "schema_version":1,"status":"COUPLING_ZONE_DECLARATION_DRAFT","production_approved":False,
            "candidate_revision":"r96","candidate_sha256":"a"*64,"pre_edit_candidate_sha256":"a"*64,
            "post_edit_execution_record_required":True,
            "coupling_system_id":"CP-PEC-AX-002","side":"left",
            "vertex_ids":[1,2,3,4],
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
            "human_evidence_ids":["HE-AX-001","HE-AX-002"],
            "intent":"repair earliest failing weights-only ownership layer",
            "diagnosis":{
                "observed_defect_ids":["WB-AX-001"],
                "suspected_layer":"D3_WEIGHTS_ONLY",
                "human_evidence_ids":["HE-AX-001","HE-AX-002"],
                "before_evidence":["before.json"]
            },
            "zones":{
                "proximal_anchor_vertex_ids":[1],
                "bridge_tissue_vertex_ids":[2,3],
                "distal_anchor_vertex_ids":[4],
                "protected_neighbor_vertex_ids":[9,10],
                "allowed_edit_vertex_ids":[1,2,3,4]
            },
            "allowed_operations":["local_weight_redistribution_after_diagnosis","diagnostic_capture"],
            "forbidden_operations":[
                "undeclared_vertex_edit","undeclared_bone_weight_edit","threshold_change","baseline_repin",
                "pose_definition_change","rig_change_without_separate_reopen","topology_change_without_separate_declaration"
            ],
            "hashes":{
                "source_blend_sha256":"b"*64,
                "vertex_ids_sha256":"c"*64,
                "pre_edit_weights_sha256":"d"*64,
                "pre_edit_mesh_sha256":"e"*64
            },
            "required_after_evidence":[
                "weights_only_motion_sweep","corrected_motion_sweep_if_correctives_exist",
                "intermediate_and_return_samples","coupling_system_evidence",
                "full_whole_body_regression","contact_load_regression_if_applicable"
            ]
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

    def test_pre_edit_identity_fields_must_match(self):
        bad=self.fixture(); bad["pre_edit_candidate_sha256"]="f"*64
        with self.assertRaisesRegex(ValueError,"pre-edit identity fields differ"): mod.validate(bad,self.c,self.h)

    def test_protected_vertices_cannot_be_editable(self):
        bad=self.fixture(); bad["zones"]["protected_neighbor_vertex_ids"]=[4,9]
        with self.assertRaisesRegex(ValueError,"overlap allowed_edit"): mod.validate(bad,self.c,self.h)

    def test_bridge_zone_must_be_declared(self):
        bad=self.fixture(); bad["zones"]["bridge_tissue_vertex_ids"]=[]
        with self.assertRaisesRegex(ValueError,"must be non-empty"): mod.validate(bad,self.c,self.h)

if __name__=="__main__": unittest.main()
