"""Axilla post-validation disposition is objective and never auto-accepts visuals."""
from __future__ import annotations
import unittest

import original_v1_axilla_disposition as d


class AxillaDispositionTests(unittest.TestCase):
    def row(self,parent_regs=0,active_regs=4,dev=0):
        return {
            "development_failure_count":dev,
            "comparisons":{
                "P3B1":{"regression_count":active_regs,"improvement_count":10},
                "r55":{"regression_count":parent_regs,"improvement_count":8},
            },
        }

    def face(self,clear=True):
        return {
            "status":"LOCAL_FACE_NUMERIC_CLEAR" if clear else "LOCAL_FACE_REVIEW_REQUIRED",
            "min_signed_projected_area_ratio":0.31 if clear else -0.01,
            "max_flipped_faces_per_sample":0 if clear else 1,
        }

    def test_ready_for_visual_disposition_while_freeze_still_blocked(self):
        result=d.assess(self.row(),"P3B1","r55",self.face(),"EVIDENCE_CLOSED","REVIEW_PACKAGE_READY")
        self.assertEqual(result["status"],"READY_FOR_VISUAL_DISPOSITION_PHASE4_STILL_BLOCKED")
        self.assertFalse(result["phase4_numeric_ready_after_lineage"])
        self.assertFalse(result["visual_acceptance_inferred"])
        self.assertFalse(result["production_approved"])

    def test_zero_active_regressions_can_only_reach_phase4_after_lineage_and_visual_disposition(self):
        result=d.assess(self.row(active_regs=0),"P3B1","r55",self.face(),"EVIDENCE_CLOSED","REVIEW_PACKAGE_READY")
        self.assertEqual(result["status"],"READY_FOR_VISUAL_DISPOSITION_AND_PHASE4_AFTER_LINEAGE")
        self.assertTrue(result["phase4_numeric_ready_after_lineage"])
        self.assertFalse(result["visual_acceptance_inferred"])

    def test_parent_regression_blocks_repair(self):
        result=d.assess(self.row(parent_regs=1),"P3B1","r55",self.face(),"EVIDENCE_CLOSED","REVIEW_PACKAGE_READY")
        self.assertEqual(result["status"],"NUMERIC_REPAIR_BLOCKED")
        self.assertTrue(any("direct parent" in x for x in result["numeric_blockers"]))

    def test_local_face_failure_blocks_repair(self):
        result=d.assess(self.row(),"P3B1","r55",self.face(False),"EVIDENCE_CLOSED","REVIEW_PACKAGE_READY")
        self.assertEqual(result["status"],"NUMERIC_REPAIR_BLOCKED")

    def test_missing_review_stays_capture_ready_only(self):
        result=d.assess(self.row(),"P3B1","r55",self.face(),"EVIDENCE_CLOSED","NO_REVIEW_CAPTURE_YET")
        self.assertEqual(result["status"],"READY_FOR_REVIEW_CAPTURE")

    def test_missing_active_baseline_comparison_is_invalid(self):
        row=self.row();del row["comparisons"]["P3B1"]
        with self.assertRaisesRegex(ValueError,"active epoch baseline"):
            d.assess(row,"P3B1","r55",self.face(),"EVIDENCE_CLOSED","REVIEW_PACKAGE_READY")


if __name__=="__main__":
    unittest.main()
