"""Tests for complete fail-closed PRE-EDIT repair workspace creation."""
import importlib.util,json,sys,tempfile
from pathlib import Path
import unittest
MODULE=Path(__file__).with_name("create_original_v1_repair_workspace.py")
SPEC=importlib.util.spec_from_file_location("repair_workspace",MODULE)
mod=importlib.util.module_from_spec(SPEC); SPEC.loader.exec_module(mod)

class RepairWorkspaceTests(unittest.TestCase):
    def test_pre_edit_and_final_identities_are_separated(self):
        with tempfile.TemporaryDirectory() as td:
            out=Path(td)/"ws"; old=sys.argv
            try:
                sys.argv=["x","--packages","RP-PEC-AX-002","--candidate","r96","--sha256","b"*64,
                          "--side","bilateral","--source-branch","fixture","--out-dir",str(out)]
                self.assertEqual(mod.main(),0)
            finally:
                sys.argv=old
            wm=json.loads((out/"workspace_manifest.json").read_text())
            self.assertEqual(wm["pre_edit_candidate_sha256"],"b"*64)
            self.assertIsNone(wm["final_candidate_sha256"])
            self.assertEqual(wm["repair_package_ids"],["RP-PEC-AX-002"])
            self.assertIn("CP-PEC-AX-002",wm["coupling_system_ids"])

            pre=json.loads((out/"candidate_issue_ledger_pre_edit.json").read_text())
            blocking=[x for x in pre["issues"] if x["severity"] in {"Critical","High"}]
            self.assertTrue(blocking)
            self.assertTrue(all(x["state"]=="Open" and not x["closure_evidence"] for x in blocking))
            self.assertTrue(all(x["candidate"]["sha256"]=="b"*64 for x in blocking))

            wo=json.loads((out/"weights_only_acceptance_FINAL_TEMPLATE.json").read_text())
            ce=json.loads((out/"anatomical_coupling_evidence_FINAL_TEMPLATE.json").read_text())
            cm=json.loads((out/"candidate_comparison_FINAL_TEMPLATE.json").read_text())
            vr=json.loads((out/"surface_visual_review_FINAL_TEMPLATE.json").read_text())
            self.assertIsNone(wo["candidate_sha256"])
            self.assertIsNone(ce["candidate_sha256"])
            self.assertIsNone(vr["candidate_sha256"])
            self.assertIsNone(cm["candidate"]["sha256"])
            self.assertIn("CP-PEC-AX-002",cm["scope"]["coupling_system_ids"])
            self.assertTrue(cm["evidence"]["repair_declaration_paths"])
            self.assertTrue(cm["evidence"]["repair_execution_record_paths"])
            self.assertEqual(cm["evidence"]["surface_visual_review_path"],"surface_visual_review_final.json")
            self.assertIn("chest_anterior_axilla",vr["scope_region_ids"])
            # A single pec package may not claim closure of global QA defects that require all coupling systems.
            self.assertNotIn("WB-QA-012",cm["scope"]["defect_ids"])

if __name__=="__main__": unittest.main()
