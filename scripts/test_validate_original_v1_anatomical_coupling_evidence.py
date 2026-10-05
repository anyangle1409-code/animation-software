"""Tests for candidate-bound anatomical coupling evidence validation."""
import copy
import importlib.util
from pathlib import Path
import unittest

MODULE_PATH=Path(__file__).with_name("validate_original_v1_anatomical_coupling_evidence.py")
SPEC=importlib.util.spec_from_file_location("coupling_evidence",MODULE_PATH)
mod=importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(mod)

class CouplingEvidenceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.cmap=mod.read(mod.MAP)

    def fixture(self):
        systems=[]
        for row in self.cmap["coupling_systems"]:
            needs_contact=bool({"horizontal_push","vertical_pull_hang","wrist_flexion_extension_loaded","loaded_foot_toe_contact","ankle_plantarflexion"}.intersection(row["movement_families"]))
            systems.append({
                "coupling_system_id":row["id"],
                "state":"engineering_clear",
                "movement_families":list(row["movement_families"]),
                "evidence":{
                    "weights_only":["weights.json"],
                    "corrected_surface":["corrected.json"],
                    "intermediate_motion":["arc.json"],
                    "return_motion":["return.json"],
                    "whole_body_renders":["whole.png"],
                    "regional_renders":["close.png"],
                    "numerical_regression":["regression.json"],
                    "contact_load":["contact.json"] if needs_contact else []
                },
                "attachment_sides_verified":True,
                "shared_ownership_gradient_verified":True,
                "lengthening_compression_verified":True,
                "volume_redistribution_verified":True,
                "fold_logic_verified":True,
                "motion_continuity_verified":True,
                "return_reversibility_verified":True,
                "bilateral_consistency_verified":True,
                "contact_load_propagation_verified":True if needs_contact else None,
                "linked_defect_ids":[],
                "engineering_disposition":"CLEAR",
                "owner_review":"pending"
            })
        return {
            "schema_version":1,
            "status":"COUPLING_EVIDENCE_IN_PROGRESS",
            "production_approved":False,
            "candidate_revision":"r96",
            "candidate_sha256":"a"*64,
            "source_branch":"fixture",
            "coupling_map":"ORIGINAL_V1_ANATOMICAL_COUPLING_MAP.json",
            "systems":systems,
            "summary":{"production_approved":False}
        }

    def test_complete_fixture_can_pass_exit(self):
        result=mod.validate(self.fixture(),self.cmap,require_exit=True)
        self.assertEqual(result["clear"],result["total"])

    def test_missing_weights_only_blocks_clear(self):
        bad=self.fixture()
        bad["systems"][0]["evidence"]["weights_only"]=[]
        with self.assertRaisesRegex(ValueError,"CLEAR without weights_only"):
            mod.validate(bad,self.cmap)

    def test_missing_return_motion_blocks_clear(self):
        bad=self.fixture()
        bad["systems"][0]["evidence"]["return_motion"]=[]
        with self.assertRaisesRegex(ValueError,"CLEAR without return_motion"):
            mod.validate(bad,self.cmap)

    def test_not_run_system_blocks_exit(self):
        bad=self.fixture()
        bad["systems"][0]["engineering_disposition"]="NOT_RUN"
        with self.assertRaisesRegex(ValueError,"exit blocked"):
            mod.validate(bad,self.cmap,require_exit=True)

    def test_candidate_sha_required(self):
        bad=self.fixture(); bad["candidate_sha256"]="bad"
        with self.assertRaisesRegex(ValueError,"candidate_sha256"):
            mod.validate(bad,self.cmap)

if __name__=="__main__":
    unittest.main()
