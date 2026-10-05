"""Tests for complete candidate-bound pre-edit repair workspace creation."""
import importlib.util,json,sys,tempfile
from pathlib import Path
import unittest
MODULE=Path(__file__).with_name("create_original_v1_repair_workspace.py")
SPEC=importlib.util.spec_from_file_location("repair_workspace",MODULE)
mod=importlib.util.module_from_spec(SPEC); SPEC.loader.exec_module(mod)

class RepairWorkspaceTests(unittest.TestCase):
    def test_workspace_is_candidate_bound_and_fail_closed(self):
        with tempfile.TemporaryDirectory() as td:
            out=Path(td)/"ws"; old=sys.argv
            try:
                sys.argv=["x","--packages","RP-PEC-AX-002","--candidate","r96","--sha256","b"*64,
                          "--side","bilateral","--source-branch","fixture","--out-dir",str(out)]
                self.assertEqual(mod.main(),0)
            finally:
                sys.argv=old
            wm=json.loads((out/"workspace_manifest.json").read_text())
            self.assertEqual(wm["candidate_sha256"],"b"*64)
            self.assertEqual(wm["repair_package_ids"],["RP-PEC-AX-002"])
            self.assertIn("CP-PEC-AX-002",wm["coupling_system_ids"])
            ledger=json.loads((out/"candidate_issue_ledger.json").read_text())
            blocking=[x for x in ledger["issues"] if x["severity"] in {"Critical","High"}]
            self.assertTrue(blocking)
            self.assertTrue(all(x["state"]=="Open" and not x["closure_evidence"] for x in blocking))
            cm=json.loads((out/"candidate_comparison_manifest.json").read_text())
            self.assertEqual(cm["candidate"]["sha256"],"b"*64)
            self.assertIn("CP-PEC-AX-002",cm["scope"]["coupling_system_ids"])
            self.assertTrue(cm["evidence"]["repair_declaration_paths"])

if __name__=="__main__": unittest.main()
