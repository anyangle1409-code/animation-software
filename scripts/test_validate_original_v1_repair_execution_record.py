"""Tests for post-edit repair execution provenance."""
import hashlib,importlib.util,json,tempfile
from pathlib import Path
import unittest

P=Path(__file__).with_name("validate_original_v1_repair_execution_record.py")
S=importlib.util.spec_from_file_location("repair_exec",P); mod=importlib.util.module_from_spec(S); S.loader.exec_module(mod)

class RepairExecutionRecordTests(unittest.TestCase):
    def fixture(self,root):
        dec={
          "candidate_revision":"r96","candidate_sha256":"a"*64,"pre_edit_candidate_sha256":"a"*64,
          "repair_package_id":"RP-PEC-AX-002","coupling_system_id":"CP-PEC-AX-002","side":"bilateral",
          "allowed_operations":["local_weight_redistribution_after_diagnosis","diagnostic_capture"],
          "forbidden_operations":["undeclared_vertex_edit","threshold_change"],
          "allowed_bones":["spine2","clavicle_l","clavicle_r","upperarm_l","upperarm_r"],
          "zones":{"allowed_edit_vertex_ids":[1,2,3,4],"protected_neighbor_vertex_ids":[9,10]}
        }
        dp=root/"declaration.json"; dp.write_text(json.dumps(dec),encoding="utf-8")
        rec={
          "schema_version":1,"status":"REPAIR_EXECUTION_RECORD",
          "production_approved":False,"candidate_revision":"r96","source_branch":"fixture",
          "repair_package_id":"RP-PEC-AX-002","coupling_system_id":"CP-PEC-AX-002","side":"bilateral",
          "repair_declaration_path":"declaration.json",
          "repair_declaration_sha256":hashlib.sha256(dp.read_bytes()).hexdigest(),
          "pre_edit_candidate_sha256":"a"*64,"final_candidate_sha256":"b"*64,
          "executed_operations":["local_weight_redistribution_after_diagnosis"],
          "edited_vertex_ids":[1,2],"edited_bone_groups":["spine2","upperarm_l"],
          "evidence_refs":["weights.json","renders.json"],
          "change_audit_path":"change.json","regression_report_path":"regression.json",
          "contact_report_path":None,"notes":[]
        }
        return rec

    def test_declared_repair_passes(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td); out=mod.validate(self.fixture(root),root)
            self.assertEqual(out["status"],"PASS")

    def test_edit_outside_declared_vertices_fails(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td); rec=self.fixture(root); rec["edited_vertex_ids"]=[1,99]
            with self.assertRaisesRegex(ValueError,"exceed declaration"):
                mod.validate(rec,root)

    def test_undeclared_bone_group_fails(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td); rec=self.fixture(root); rec["edited_bone_groups"]=["mystery"]
            with self.assertRaisesRegex(ValueError,"exceed declaration"):
                mod.validate(rec,root)

    def test_final_sha_cannot_equal_pre_edit(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td); rec=self.fixture(root); rec["final_candidate_sha256"]="a"*64
            with self.assertRaisesRegex(ValueError,"must differ"):
                mod.validate(rec,root)

    def test_declaration_hash_mismatch_fails(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td); rec=self.fixture(root); rec["repair_declaration_sha256"]="c"*64
            with self.assertRaisesRegex(ValueError,"hash mismatch"):
                mod.validate(rec,root)

if __name__=="__main__": unittest.main()
