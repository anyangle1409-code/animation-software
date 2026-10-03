#!/usr/bin/env python3
import unittest
from original_v1_phase4_preflight import assess

SHA="a"*64

def state():
    return {
        "current_candidate":"r99",
        "last_known_candidate_sha256":SHA,
        "candidate_state":"experimental",
        "incomplete_candidates":[],
        "development_failure_count":0,
        "unresolved_regressions":[],
        "phases":{**{p:{"state":"complete"} for p in ("3A","3B","3C","3D","3E")},"4":{"state":"not_started"}},
        "pinned_baseline":{"revision":"P3B1"},
        "next_action":{"action":"ENTER development freeze validation"},
        "latest_evidence":[
            {"path":"ORIGINAL_V1_WORK/candidates/repair_checks/full_r99_evidence_manifest.json"},
            {"path":"ORIGINAL_V1_WORK/candidates/repair_checks/full_r99_comparison_vs_P3B1.json"},
        ],
    }

def control():
    return {"continuation_decisions":{"r99":{"candidate_sha256":SHA}}}

class Phase4PreflightTests(unittest.TestCase):
    def test_eligible_contract(self):
        self.assertEqual(assess(state(),control())["eligibility"],"ELIGIBLE_FOR_PHASE4_VALIDATION")
    def test_regressions_block(self):
        s=state(); s["unresolved_regressions"]=[{"metric":"x"}]
        self.assertIn("strict severity regressions remain",assess(s,control())["issues"])
    def test_stale_lineage_blocks(self):
        c=control(); c["continuation_decisions"]["r99"]["candidate_sha256"]="b"*64
        self.assertIn("continuation decision is missing/stale for current candidate",assess(state(),c)["issues"])
    def test_wrong_next_action_blocks(self):
        s=state(); s["next_action"]["action"]="REPAIR shoulder"
        self.assertIn("production control does not select ENTER development freeze validation",assess(s,control())["issues"])
    def test_active_epoch_comparison_required(self):
        s=state(); s["latest_evidence"]=s["latest_evidence"][:1]
        self.assertIn("active epoch-baseline comparison missing from current evidence",assess(s,control())["issues"])

if __name__=="__main__":
    unittest.main()
