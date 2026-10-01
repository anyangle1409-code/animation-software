"""Candidate closure verifies identity/evidence without inventing acceptance."""
from __future__ import annotations
import json
from pathlib import Path
import tempfile
import unittest

import original_v1_candidate_closure as c


class CandidateClosureTests(unittest.TestCase):
    def ref(self,root,p):
        return {"path":p.relative_to(root).as_posix(),"sha256":c.digest(p)}

    def fixture(self,root):
        sha="a"*64
        cand=root/c.CAND/"HomeGymPT_Male_ORIGINAL_v1_O4_CANDIDATE_r30.json"
        cand.parent.mkdir(parents=True)
        cand.write_text(json.dumps({"candidate":"HomeGymPT_Male_ORIGINAL_v1_O4_CANDIDATE_r30.blend","candidate_sha256":sha}))
        pose=root/c.CAND/"repair_checks/full_r30_merged_pose_report.json";pose.parent.mkdir(parents=True)
        pose.write_text(json.dumps({"candidate_sha256":sha}))
        comp=root/c.CAND/"repair_checks/full_r30_comparison_vs_R2.json"
        comp.write_text(json.dumps({"status":"IMPROVED"}))
        ledger={"candidates":[{
            "revision":"r30","sha256":sha,"comparison_baselines":["R2"],
            "comparisons":{"R2":{"evidence":self.ref(root,comp)}},
            "classification":"STRICT IMPROVEMENT","state":"experimental","reason":"fixture",
            "owner_review":"pending","evidence_location":pose.relative_to(root).as_posix(),
            "manifest":self.ref(root,cand)
        }]}
        (root/c.LEDGER).write_text(json.dumps(ledger))
        return sha

    def test_complete_candidate_is_evidence_closed(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td);self.fixture(root)
            result=c.verify_candidate(root,"r30")
            self.assertEqual(result["evidence_closure_status"],"EVIDENCE_CLOSED")
            self.assertFalse(result["production_approved"])

    def test_missing_comparison_refuses_closure(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td);self.fixture(root)
            ledger=json.loads((root/c.LEDGER).read_text())
            ledger["candidates"][0]["comparisons"]={}
            (root/c.LEDGER).write_text(json.dumps(ledger))
            result=c.verify_candidate(root,"r30")
            self.assertEqual(result["evidence_closure_status"],"REFUSED")

    def test_bad_manifest_hash_refuses_closure(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td);self.fixture(root)
            ledger=json.loads((root/c.LEDGER).read_text())
            ledger["candidates"][0]["manifest"]["sha256"]="f"*64
            (root/c.LEDGER).write_text(json.dumps(ledger))
            result=c.verify_candidate(root,"r30")
            self.assertTrue(any("candidate manifest hash differs" in x for x in result["issues"]))

    def test_review_absence_is_nonblocking(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td);self.fixture(root)
            result=c.verify_candidate(root,"r30")
            self.assertEqual(result["evidence_closure_status"],"EVIDENCE_CLOSED")
            self.assertTrue(all(x["status"]=="NOT_CAPTURED" for x in result["review_packages"]))


if __name__=="__main__":
    unittest.main()
