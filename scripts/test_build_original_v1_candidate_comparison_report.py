"""Tests for unified parent->candidate comparison builder."""
import importlib.util,json,tempfile
from pathlib import Path
import unittest
MODULE=Path(__file__).with_name("build_original_v1_candidate_comparison_report.py")
SPEC=importlib.util.spec_from_file_location("candidate_compare",MODULE); mod=importlib.util.module_from_spec(SPEC); SPEC.loader.exec_module(mod)

class CandidateComparisonTests(unittest.TestCase):
    def write(self,root,name,obj):
        p=root/name; p.write_text(json.dumps(obj),encoding="utf-8"); return name
    def test_missing_required_evidence_blocks(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td)
            parent=self.write(root,"parent.json",{"issues":[]})
            candidate=self.write(root,"candidate.json",{"candidate_under_review":{"sha256":"b"*64},"issues":[]})
            manifest={
              "parent":{"revision":"r95","sha256":"a"*64,"issue_ledger_path":parent},
              "candidate":{"revision":"r96","sha256":"b"*64,"issue_ledger_path":candidate},
              "scope":{"region_ids":[],"coupling_system_ids":[],"defect_ids":[]},
              "evidence":{
                "weights_only_acceptance_path":None,"anatomical_coupling_evidence_path":None,
                "movement_coupling_evidence_path":None,"motion_reversibility_path":None,
                "motion_continuity_path":None,"continuity_engineering_review_status":"PENDING",
                "regression_status":"PENDING","contact_status":"PENDING",
                "visual_engineering_review_status":"PENDING","change_audit_status":"PENDING"
              }
            }
            report=mod.build(manifest,root)
            self.assertFalse(report["engineering_clear_eligible"])
            self.assertIn("weights_only_present",report["failed_checks"])
    def test_new_critical_high_blocker_is_detected(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td)
            p=self.write(root,"parent.json",{"issues":[]})
            c=self.write(root,"candidate.json",{"candidate_under_review":{"sha256":"b"*64},"issues":[{"id":"NEW","severity":"High","state":"Open","closure_evidence":[]}]})
            # Minimal exact-SHA evidence, statuses deliberately PASS so only the new blocker matters.
            wo=self.write(root,"wo.json",{"candidate_sha256":"b"*64,"regions":[]})
            ce=self.write(root,"ce.json",{"candidate_sha256":"b"*64,"systems":[]})
            me=self.write(root,"me.json",{"candidate_sha256":"b"*64,"samples":[]})
            rev=self.write(root,"rev.json",{"candidate_sha256":"b"*64,"overall_status":"CLEAN"})
            cont=self.write(root,"cont.json",{"candidate_sha256":"b"*64})
            manifest={"parent":{"revision":"r95","sha256":"a"*64,"issue_ledger_path":p},"candidate":{"revision":"r96","sha256":"b"*64,"issue_ledger_path":c},"scope":{"region_ids":[],"coupling_system_ids":[],"defect_ids":[]},"evidence":{"weights_only_acceptance_path":wo,"anatomical_coupling_evidence_path":ce,"movement_coupling_evidence_path":me,"motion_reversibility_path":rev,"motion_continuity_path":cont,"continuity_engineering_review_status":"PASS","regression_status":"PASS","contact_status":"NOT_APPLICABLE","visual_engineering_review_status":"PASS","change_audit_status":"PASS"}}
            report=mod.build(manifest,root)
            self.assertIn("NEW",report["new_open_critical_high"])
            self.assertFalse(report["engineering_clear_eligible"])

if __name__=="__main__": unittest.main()
