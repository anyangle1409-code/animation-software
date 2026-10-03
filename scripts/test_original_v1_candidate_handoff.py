"""Candidate handoff combines evidence/local state without inventing approval."""
from __future__ import annotations
import unittest

import original_v1_candidate_handoff as h


class CandidateHandoffTests(unittest.TestCase):
    def base(self):
        closure={"evidence_closure_status":"EVIDENCE_CLOSED","candidate_sha256":"a"*64,
                 "candidate_state":"experimental","classification":"STRICT IMPROVEMENT"}
        review={"status":"NO_REVIEW_CAPTURE_YET"}
        blend={"rows":[{"revision":"r30","status":"IDENTITY_VERIFIED"}]}
        status={"current_candidate":"r30","current_phase":3,"current_subphase":"3B",
                "next_action":{"action":"RUN r31","command":"RUN_R31.bat"},
                "development_failure_count":2,"unresolved_regressions":[1],
                "pinned_baseline":{"revision":"P3B1","candidate_sha256":"b"*64}}
        return closure,review,blend,status

    def test_ready_without_owner_review(self):
        args=self.base();data=h.summarise("r30",*args)
        self.assertEqual(data["status"],"HANDOFF_READY")
        self.assertFalse(data["review_blocking"])
        self.assertFalse(data["production_approved"])
        self.assertEqual(data["current_generated_state"]["active_epoch_baseline"]["revision"],"P3B1")
        self.assertEqual(data["current_generated_state"]["strict_active_epoch_regression_count"],1)
        self.assertNotIn("strict_r2_regression_count",data["current_generated_state"])

    def test_missing_local_blend_blocks_handoff(self):
        closure,review,blend,status=self.base();blend={"rows":[]}
        data=h.summarise("r30",closure,review,blend,status)
        self.assertEqual(data["status"],"HANDOFF_NEEDS_ATTENTION")

    def test_unclosed_candidate_blocks_handoff(self):
        closure,review,blend,status=self.base();closure["evidence_closure_status"]="REFUSED"
        data=h.summarise("r30",closure,review,blend,status)
        self.assertTrue(any("not closed" in x for x in data["issues"]))


if __name__=="__main__":
    unittest.main()
