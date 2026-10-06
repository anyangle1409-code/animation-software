#!/usr/bin/env python3
import unittest
from original_v1_phase4_preflight import assess, validate_shoulder_acceptance_receipt

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

def clear_ledger():
    return {
        "schema_version":1,
        "asset":"HomeGymPT_Male_ORIGINAL_v1",
        "issues":[{
            "id":"WB-TEST-999",
            "region":"fixture",
            "severity":"Medium",
            "state":"Open",
            "candidate":{"revision":"r99","sha256":SHA},
            "reproduction":{"poses":["neutral"],"views":["front"],"description":"Fixture only."},
            "evidence_paths":["fixture.png"],
            "human_evidence_ids":[],
            "evidence_gap":"Fixture only; not a real project evidence claim.",
            "defect":"Fixture defect.",
            "acceptance":"Fixture acceptance.",
            "closure_evidence":[],
        }],
    }

def assess_clear(s=None,c=None):
    return assess(s or state(),c or control(),issue_ledger=clear_ledger())

class Phase4PreflightTests(unittest.TestCase):
    def test_shoulder_acceptance_receipt_is_fail_closed(self):
        good={
            "candidate_revision":"r99","pass":True,"production_approved":False,
            "causal_order_violation":False,"weights_only_foundation_pass":True,
            "movement_matrix_complete":True,"human_anatomical_review_recorded":True,
        }
        self.assertEqual(validate_shoulder_acceptance_receipt(good,"r99"),[])
        bad=dict(good); bad["weights_only_foundation_pass"]=False
        self.assertIn("weights-only foundation pass","\n".join(validate_shoulder_acceptance_receipt(bad,"r99")))
        bad=dict(good); bad["movement_matrix_complete"]=False
        self.assertIn("complete movement matrix","\n".join(validate_shoulder_acceptance_receipt(bad,"r99")))
        bad=dict(good); bad["human_anatomical_review_recorded"]=False
        self.assertIn("human anatomical review","\n".join(validate_shoulder_acceptance_receipt(bad,"r99")))

    def test_eligible_contract(self):
        self.assertEqual(assess_clear()["eligibility"],"ELIGIBLE_FOR_PHASE4_VALIDATION")
    def test_regressions_block(self):
        s=state(); s["unresolved_regressions"]=[{"metric":"x"}]
        self.assertIn("strict severity regressions remain",assess_clear(s)["issues"])
    def test_stale_lineage_blocks(self):
        c=control(); c["continuation_decisions"]["r99"]["candidate_sha256"]="b"*64
        self.assertIn("continuation decision is missing/stale for current candidate",assess_clear(c=c)["issues"])
    def test_wrong_next_action_blocks(self):
        s=state(); s["next_action"]["action"]="REPAIR shoulder"
        self.assertIn("production control does not select ENTER development freeze validation",assess_clear(s)["issues"])
    def test_active_epoch_comparison_required(self):
        s=state(); s["latest_evidence"]=s["latest_evidence"][:1]
        self.assertIn("active epoch-baseline comparison missing from current evidence",assess_clear(s)["issues"])
    def test_critical_high_visual_issue_blocks_refreeze(self):
        ledger=clear_ledger()
        ledger["issues"][0]["severity"]="Critical"
        result=assess(state(),control(),issue_ledger=ledger)
        self.assertEqual(result["eligibility"],"PHASE4_BLOCKED")
        self.assertIn("Critical/High whole-body anatomy issues remain",result["issues"])
        self.assertTrue(any("WB-TEST-999" in x for x in result["issues"]))
    def test_fixed_high_issue_does_not_block_if_closure_evidence_exists(self):
        ledger=clear_ledger()
        row=ledger["issues"][0]
        row["severity"]="High"; row["state"]="Fixed"; row["closure_evidence"]=["fixture-closure.json"]
        result=assess(state(),control(),issue_ledger=ledger)
        self.assertEqual(result["eligibility"],"ELIGIBLE_FOR_PHASE4_VALIDATION")

if __name__=="__main__":
    unittest.main()
