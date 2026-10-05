"""Tests for post-edit repair workspace finalization."""
import importlib.util,json,sys,tempfile
from pathlib import Path
import unittest

CREATE=Path(__file__).with_name("create_original_v1_repair_workspace.py")
FINAL=Path(__file__).with_name("finalize_original_v1_repair_workspace.py")
sp=importlib.util.spec_from_file_location("create_ws",CREATE); create=importlib.util.module_from_spec(sp); sp.loader.exec_module(create)
sp2=importlib.util.spec_from_file_location("final_ws",FINAL); final=importlib.util.module_from_spec(sp2); sp2.loader.exec_module(final)

class FinalizeRepairWorkspaceTests(unittest.TestCase):
    def test_finalization_binds_new_sha_and_preserves_pre_edit_identity(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td); ws=root/"ws"; candidate=root/"candidate.blend"
            # SHA of literal b"pre" is the declared pre-edit candidate.
            import hashlib
            pre_bytes=b"pre"; pre_sha=hashlib.sha256(pre_bytes).hexdigest()
            old=sys.argv
            try:
                sys.argv=["x","--packages","RP-PEC-AX-002","--candidate","r96","--sha256",pre_sha,
                          "--side","bilateral","--source-branch","fixture","--out-dir",str(ws)]
                self.assertEqual(create.main(),0)
            finally: sys.argv=old
            candidate.write_bytes(b"post-edit")
            final_sha=hashlib.sha256(b"post-edit").hexdigest()
            try:
                sys.argv=["x","--workspace",str(ws),"--final-candidate",str(candidate)]
                self.assertEqual(final.main(),0)
            finally: sys.argv=old
            fm=json.loads((ws/"workspace_finalization_manifest.json").read_text())
            self.assertEqual(fm["pre_edit_candidate_sha256"],pre_sha)
            self.assertEqual(fm["final_candidate_sha256"],final_sha)
            cm=json.loads((ws/"candidate_comparison_manifest_final.json").read_text())
            self.assertEqual(cm["candidate"]["sha256"],final_sha)
            dec=json.loads((ws/"repair_declaration_rp_pec_ax_002.json").read_text())
            self.assertEqual(dec["pre_edit_candidate_sha256"],pre_sha)
            rec=json.loads((ws/"repair_execution_rp_pec_ax_002.json").read_text())
            vr=json.loads((ws/"surface_visual_review_final.json").read_text())
            self.assertEqual(rec["pre_edit_candidate_sha256"],pre_sha)
            self.assertEqual(rec["final_candidate_sha256"],final_sha)
            self.assertEqual(vr["candidate_sha256"],final_sha)
            self.assertEqual(cm["evidence"]["surface_visual_review_path"],"surface_visual_review_final.json")
            sweep_paths=cm["evidence"]["human_movement_sweep_acceptance_paths"]
            self.assertEqual(len(sweep_paths),2)
            self.assertEqual(set(sweep_paths),{
              "human_movement_sweep_acceptance_shoulder_abduction_elevation_final.json",
              "human_movement_sweep_acceptance_humeral_internal_external_rotation_final.json"
            })
            for name in sweep_paths:
                sat=json.loads((ws/name).read_text())
                self.assertEqual(sat["candidate_sha256"],final_sha)
                self.assertEqual(sat["candidate_revision"],"r96")
                self.assertEqual(sat["engineering_review"],"PENDING")
            self.assertEqual(set(fm["final_records"]["human_movement_sweep_acceptance_records"]),set(sweep_paths))

    def test_finalization_rejects_unchanged_candidate_sha(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td); ws=root/"ws"; candidate=root/"candidate.blend"
            import hashlib
            data=b"same"; sha=hashlib.sha256(data).hexdigest(); candidate.write_bytes(data)
            old=sys.argv
            try:
                sys.argv=["x","--packages","RP-PEC-AX-002","--candidate","r96","--sha256",sha,
                          "--side","bilateral","--source-branch","fixture","--out-dir",str(ws)]
                self.assertEqual(create.main(),0)
                sys.argv=["x","--workspace",str(ws),"--final-candidate",str(candidate)]
                self.assertEqual(final.main(),2)
            finally: sys.argv=old

if __name__=="__main__": unittest.main()
