"""Tests for finalized workspace sweep-acceptance preflight."""
import importlib.util,json,tempfile
from pathlib import Path
import unittest

P=Path(__file__).with_name("validate_original_v1_workspace_sweep_acceptance.py")
S=importlib.util.spec_from_file_location("workspace_sweep_acceptance",P); mod=importlib.util.module_from_spec(S); S.loader.exec_module(mod)

class FakeAcceptance:
    @staticmethod
    def validate(d,base,require_pass=False):
        if require_pass and d.get("engineering_review")!="PASS":
            raise ValueError("engineering PASS required")
        return {
          "sweep_id":d.get("sweep_id"),
          "candidate_sha256":d.get("candidate_sha256"),
          "engineering_review":d.get("engineering_review")
        }

class WorkspaceSweepAcceptanceTests(unittest.TestCase):
    def make_workspace(self,root,states=("PASS","PASS")):
        ws=root/"ws"; ws.mkdir()
        sweeps=["shoulder_abduction_elevation","humeral_internal_external_rotation"]
        records=["human_movement_sweep_acceptance_shoulder_abduction_elevation_final.json",
                 "human_movement_sweep_acceptance_humeral_internal_external_rotation_final.json"]
        (ws/"workspace_manifest.json").write_text(json.dumps({
          "validation_selection":{"sweep_only_movements_requiring_generic_runner":sweeps},
          "files":{"expected_sweep_acceptance_records":records}
        }),encoding="utf-8")
        (ws/"workspace_finalization_manifest.json").write_text(json.dumps({
          "candidate_revision":"r96","final_candidate_sha256":"a"*64
        }),encoding="utf-8")
        for sid,path,state in zip(sweeps,records,states):
            (ws/path).write_text(json.dumps({
              "candidate_revision":"r96","candidate_sha256":"a"*64,
              "sweep_id":sid,"engineering_review":state
            }),encoding="utf-8")
        return ws,records

    def test_all_required_pass_records_clear_preflight(self):
        with tempfile.TemporaryDirectory() as td:
            ws,_=self.make_workspace(Path(td))
            out=mod.validate_workspace(ws,True,FakeAcceptance)
            self.assertEqual(out["accepted"],2)
            self.assertEqual(out["status"],"PASS")

    def test_pending_record_blocks_required_pass_preflight(self):
        with tempfile.TemporaryDirectory() as td:
            ws,_=self.make_workspace(Path(td),("PASS","PENDING"))
            with self.assertRaisesRegex(ValueError,"engineering PASS required"):
                mod.validate_workspace(ws,True,FakeAcceptance)

    def test_candidate_sha_mismatch_blocks(self):
        with tempfile.TemporaryDirectory() as td:
            ws,records=self.make_workspace(Path(td))
            p=ws/records[0]; d=json.loads(p.read_text()); d["candidate_sha256"]="b"*64; p.write_text(json.dumps(d))
            with self.assertRaisesRegex(ValueError,"candidate SHA differs"):
                mod.validate_workspace(ws,True,FakeAcceptance)

    def test_missing_acceptance_record_blocks(self):
        with tempfile.TemporaryDirectory() as td:
            ws,records=self.make_workspace(Path(td)); (ws/records[1]).unlink()
            with self.assertRaisesRegex(ValueError,"acceptance record missing"):
                mod.validate_workspace(ws,True,FakeAcceptance)

    def test_required_count_must_match_workspace_records(self):
        with tempfile.TemporaryDirectory() as td:
            ws,_=self.make_workspace(Path(td))
            wm=json.loads((ws/"workspace_manifest.json").read_text()); wm["files"]["expected_sweep_acceptance_records"].pop()
            (ws/"workspace_manifest.json").write_text(json.dumps(wm))
            with self.assertRaisesRegex(ValueError,"count differs"):
                mod.validate_workspace(ws,True,FakeAcceptance)

if __name__=="__main__": unittest.main()
