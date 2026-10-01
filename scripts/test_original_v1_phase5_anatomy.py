"""Phase 5 anatomy execution packets remain ordered and fail-closed."""
from __future__ import annotations

import copy
import json
from pathlib import Path
import tempfile
import unittest

import original_v1_phase5_anatomy as a


class Phase5AnatomyTests(unittest.TestCase):
    def plan(self):
        return a.load_plan(a.ROOT)

    def ref(self, root: Path, path: Path):
        return {"path": path.relative_to(root).as_posix(), "sha256": a.digest(path)}

    def fixture_report(self, root: Path, region: str, parent_sha="b"*64, candidate_sha="c"*64, previous=None):
        plan=self.plan();row=plan["regions"][region]
        raw=root/"raw.txt";raw.write_text("synthetic unit test evidence only",encoding="utf-8")
        raw_ref=self.ref(root,raw)
        artifacts={}
        for i,name in enumerate(plan["per_region_required_evidence"]):
            p=root/f"artifact_{i}.txt";p.write_text(f"{name} fixture",encoding="utf-8")
            artifacts[name]=self.ref(root,p)
        return {
            "schema_version":1,"phase":5,"region":region,"region_name":row["name"],
            "status":"REGION_EVIDENCE_COMPLETE","phase_complete":False,"production_approved":False,
            "candidate_revision":"r101","candidate_sha256":candidate_sha,
            "parent_revision":"r100","parent_candidate_sha256":parent_sha,
            "development_freeze_candidate_sha256":"d"*64,
            "source_git_commit":"e"*40,"evidence_timestamp":"2026-10-01T14:00:00+01:00",
            "work_package":row["work_package"],"permitted_scope":row["permitted_scope"],
            "protected_boundaries":row["protected_boundaries"],
            "focused_poses":row["focused_poses"],"required_views":row["required_views"],
            "owner_review":"pending","blocking":False,
            "previous_region_receipt":previous,
            "checks":[{"id":x,"passed":True,"evidence":[raw_ref]} for x in a.REQUIRED_CHECKS],
            "source_evidence":[raw_ref],"artifacts":artifacts,
        }

    def test_plan_has_all_seven_regions_and_real_packages(self):
        plan=self.plan()
        self.assertEqual(plan["order"],["5A","5B","5C","5D","5E","5F","5G"])

    def test_5a_complete_evidence_contract_verifies(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td);report=self.fixture_report(root,"5A",previous=None)
            self.assertEqual(a.verify_region_report(root,report,self.plan(),"5A"),[])

    def test_5b_requires_verified_5a_receipt_bound_to_parent(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td)
            report=self.fixture_report(root,"5B",previous=None)
            issues=a.verify_region_report(root,report,self.plan(),"5B")
            self.assertTrue(any("previous region" in x for x in issues))

    def test_valid_previous_receipt_allows_next_region(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td);parent="b"*64
            receipt={"schema_version":1,"region":"5A","contract_status":"REGION_EVIDENCE_VERIFIED",
                     "phase_complete":False,"production_approved":False,"candidate_sha256":parent}
            p=root/"5a_receipt.json";p.write_text(json.dumps(receipt),encoding="utf-8")
            report=self.fixture_report(root,"5B",parent_sha=parent,previous=self.ref(root,p))
            self.assertEqual(a.verify_region_report(root,report,self.plan(),"5B"),[])

    def test_wrong_previous_candidate_refused(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td)
            receipt={"region":"5A","contract_status":"REGION_EVIDENCE_VERIFIED",
                     "production_approved":False,"candidate_sha256":"f"*64}
            p=root/"prev.json";p.write_text(json.dumps(receipt),encoding="utf-8")
            report=self.fixture_report(root,"5B",parent_sha="b"*64,previous=self.ref(root,p))
            issues=a.verify_region_report(root,report,self.plan(),"5B")
            self.assertTrue(any("does not equal current parent" in x for x in issues))

    def test_capture_coverage_drift_refused(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td);report=self.fixture_report(root,"5A")
            report["required_views"]=report["required_views"][:-1]
            issues=a.verify_region_report(root,report,self.plan(),"5A")
            self.assertIn("required-view coverage differs from plan",issues)

    def test_missing_artifact_refused(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td);report=self.fixture_report(root,"5A")
            report["artifacts"].pop(next(iter(report["artifacts"])))
            issues=a.verify_region_report(root,report,self.plan(),"5A")
            self.assertTrue(any("artifact inventory" in x for x in issues))

    def test_false_phase_or_production_completion_refused(self):
        for field in ("phase_complete","production_approved"):
            with self.subTest(field=field),tempfile.TemporaryDirectory() as td:
                root=Path(td);report=self.fixture_report(root,"5A");report[field]=True
                issues=a.verify_region_report(root,report,self.plan(),"5A")
                self.assertTrue(any("cannot claim" in x for x in issues))

    def test_template_stays_incomplete(self):
        state={"current_candidate":"r29","last_known_candidate_sha256":"a"*64,
               "current_phase":3,"current_subphase":"3B","phases":{"4":{"state":"not_started"}}}
        t=a.make_template(self.plan(),"5D",state)
        self.assertEqual(t["status"],"INCOMPLETE")
        self.assertFalse(t["phase_complete"]);self.assertFalse(t["production_approved"])
        self.assertTrue(all(x["passed"] is None for x in t["checks"]))
        self.assertEqual(t["entry_state"]["region_predecessor"],"5C")


if __name__=="__main__":
    unittest.main()
