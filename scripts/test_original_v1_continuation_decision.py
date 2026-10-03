"""Experimental continuation decisions remain evidence-bound and non-mutating."""
from __future__ import annotations
from pathlib import Path
import tempfile
import unittest

import verify_original_v1_continuation_decision as v


class ContinuationDecisionTests(unittest.TestCase):
    def fixture(self,root:Path):
        vis=root/"review.json";vis.write_text('{"fixture":"real-review-manifest-placeholder"}',encoding="utf-8")
        cmp1=root/"cmp_parent.json";cmp1.write_text("parent comparison",encoding="utf-8")
        cmp2=root/"cmp_epoch.json";cmp2.write_text("epoch comparison",encoding="utf-8")
        face=root/"face.json";face.write_text("face audit",encoding="utf-8")
        row={"revision":"r56","sha256":"c"*64,"parent_sha256":"b"*64,"classification":"STRICT IMPROVEMENT"}
        parent={"revision":"r55","sha256":"b"*64}
        review={"status":"REVIEW_PACKAGE_READY","candidate_sha256":"c"*64,
                "review_sets":[{"manifest":{"path":"review.json","sha256":v.digest(vis)}}]}
        disposition={
            "kind":"AXILLA_POST_VALIDATION_DISPOSITION","candidate_revision":"r56","candidate_sha256":"c"*64,
            "direct_parent":"r55","status":"READY_FOR_VISUAL_DISPOSITION_PHASE4_STILL_BLOCKED",
            "development_failure_count":0,"direct_parent_regression_count":0,
            "local_face_status":"LOCAL_FACE_NUMERIC_CLEAR","evidence_closure_status":"EVIDENCE_CLOSED",
            "review_package_status":"REVIEW_PACKAGE_READY","production_approved":False,
            "visual_acceptance_inferred":False,
            "face_audit":{"path":"face.json","sha256":v.digest(face)},
            "comparisons":{
                "P3B1":{"path":"cmp_epoch.json","sha256":v.digest(cmp2)},
                "r55":{"path":"cmp_parent.json","sha256":v.digest(cmp1)},
            },
        }
        packet={
            "schema_version":1,"kind":v.KIND,"decision":v.DECISION,
            "candidate_revision":"r56","candidate_sha256":"c"*64,
            "parent_revision":"r55","parent_candidate_sha256":"b"*64,
            "classification":"STRICT IMPROVEMENT",
            "visual_review_manifest":{"path":"review.json","sha256":v.digest(vis)},
            "visual_disposition":"retained_after_real_render_review",
            "reason":"Real axilla renders were inspected and the local repair is retained as the experimental continuation.",
            "source_git_commit":"d"*40,"evidence_timestamp":"2026-10-03T12:00:00+01:00",
            "baseline_promotion":False,"phase4_authorized":False,"production_approved":False,
        }
        return packet,row,parent,disposition,review

    def test_valid_packet_verifies_without_approval(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td);packet,row,parent,disp,review=self.fixture(root)
            self.assertEqual(v.validate_decision(root,packet,row,parent,disp,review),[])
            self.assertFalse(packet["production_approved"])

    def test_blocked_numeric_disposition_is_refused(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td);packet,row,parent,disp,review=self.fixture(root)
            disp["status"]="NUMERIC_REPAIR_BLOCKED"
            issues=v.validate_decision(root,packet,row,parent,disp,review)
            self.assertTrue(any("not ready" in x for x in issues))

    def test_direct_parent_regression_is_refused(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td);packet,row,parent,disp,review=self.fixture(root)
            disp["direct_parent_regression_count"]=1
            self.assertTrue(any("direct-parent" in x for x in v.validate_decision(root,packet,row,parent,disp,review)))

    def test_wrong_review_manifest_is_refused(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td);packet,row,parent,disp,review=self.fixture(root)
            other=root/"other.json";other.write_text("other",encoding="utf-8")
            packet["visual_review_manifest"]={"path":"other.json","sha256":v.digest(other)}
            issues=v.validate_decision(root,packet,row,parent,disp,review)
            self.assertTrue(any("verified review package" in x for x in issues))

    def test_phase4_or_production_claim_is_refused(self):
        for field in ("phase4_authorized","production_approved","baseline_promotion"):
            with self.subTest(field=field),tempfile.TemporaryDirectory() as td:
                root=Path(td);packet,row,parent,disp,review=self.fixture(root);packet[field]=True
                self.assertTrue(any("cannot claim" in x for x in v.validate_decision(root,packet,row,parent,disp,review)))

    def test_template_stays_incomplete(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td);packet,row,parent,disp,review=self.fixture(root)
            ref={"path":"disp.json","sha256":"e"*64}
            template=v.make_template(row,parent,ref,review,"f"*40)
            self.assertIsNone(template["visual_disposition"])
            self.assertIsNone(template["reason"])
            self.assertFalse(template["production_approved"])
            self.assertFalse(template["phase4_authorized"])


if __name__=="__main__":
    unittest.main()
