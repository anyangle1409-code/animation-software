"""Tests for one-command post-edit evidence bundle generation."""
import importlib.util,json,tempfile
from pathlib import Path
import unittest

P=Path(__file__).with_name("create_original_v1_post_edit_evidence_bundle.py")
S=importlib.util.spec_from_file_location("post_bundle",P); mod=importlib.util.module_from_spec(S); S.loader.exec_module(mod)

class PostEditEvidenceBundleTests(unittest.TestCase):
    def declaration(self,root,package="RP-PEC-AX-002",coupling="CP-PEC-AX-002"):
        d={
          "candidate_revision":"r96","candidate_sha256":"a"*64,"pre_edit_candidate_sha256":"a"*64,
          "repair_package_id":package,"coupling_system_id":coupling,"side":"bilateral","source_branch":"fixture"
        }
        p=root/"declaration.json"; p.write_text(json.dumps(d),encoding="utf-8"); return p

    def test_single_shoulder_package_bundle(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td); dec=self.declaration(root); out=root/"bundle"
            result=mod.build(["RP-PEC-AX-002"],"r96","b"*64,"fixture",[str(dec)],out)
            self.assertIn("CP-PEC-AX-002",result["coupling_system_ids"])
            self.assertIn("chest_anterior_axilla",result["region_ids"])
            compare=json.loads((out/"candidate_comparison_manifest.json").read_text())
            self.assertEqual(compare["candidate"]["sha256"],"b"*64)
            self.assertEqual(compare["scope"]["repair_package_ids"],["RP-PEC-AX-002"])
            er=json.loads(next((out/"execution_records").glob("*.json")).read_text())
            self.assertEqual(er["pre_edit_candidate_sha256"],"a"*64)
            self.assertEqual(er["final_candidate_sha256"],"b"*64)

    def test_missing_declaration_for_selected_package_fails(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td)
            dec=self.declaration(root,"RP-DELTOID-004","CP-DELTOID-004")
            with self.assertRaisesRegex(ValueError,"missing pre-edit declarations"):
                mod.build(["RP-PEC-AX-002"],"r96","b"*64,"fixture",[str(dec)],root/"bundle")

    def test_nonempty_output_directory_is_refused(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td); dec=self.declaration(root); out=root/"bundle"; out.mkdir(); (out/"keep.txt").write_text("x")
            with self.assertRaisesRegex(ValueError,"not empty"):
                mod.build(["RP-PEC-AX-002"],"r96","b"*64,"fixture",[str(dec)],out)

if __name__=="__main__": unittest.main()
