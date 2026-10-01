"""Concise progress summary stays factual and does not invent percentage completion."""
from __future__ import annotations
import unittest

import original_v1_progress_summary as p


class ProgressSummaryTests(unittest.TestCase):
    def fixture(self):
        phases={str(n):{"state":"not_started"} for n in range(13)}
        phases["0"]["state"]=phases["1"]["state"]=phases["2"]["state"]="complete"
        phases["3"]["state"]="active"
        for k,v in {"3A":"complete","3B":"active","3C":"blocked","3D":"refinement","3E":"blocked"}.items():phases[k]={"state":v}
        for k in p.PHASE5_SUB:phases[k]={"state":"not_started"}
        status={"phases":phases,"current_phase":3,"current_subphase":"3B","current_candidate":"r29",
                "candidate_state":"experimental","candidate_classification":"TRADE-OFF",
                "development_failure_count":7,"unresolved_regressions":[1]*6,"production_failure_count":109,
                "next_action":{"action":"RUN r30","command":"RUN_ORIGINAL_V1_R30.bat"},
                "pending_owner_reviews":[],"incomplete_candidates":[],"evidence_timestamp":"x"}
        orchestration={"prepared_support_stages":[{"stage":n} for n in range(1,13)],
                       "critical_path":[{} for _ in range(14)]}
        return status,orchestration

    def test_current_summary_matches_factual_state(self):
        status,orch=self.fixture();s=p.build_summary(status,orch)
        self.assertEqual(s["roadmap"]["complete_phases"],["0","1","2"])
        self.assertEqual(s["roadmap"]["next_major_milestone"]["remaining_subphases"],["3B","3C","3D","3E"])
        self.assertEqual(s["prepared_infrastructure"]["support_stages_prepared"],12)

    def test_no_percentage_completion_field(self):
        status,orch=self.fixture();s=p.build_summary(status,orch)
        text=str(s).lower()
        self.assertNotIn("percent",text)
        self.assertFalse(s["production_approved"])


if __name__=="__main__":
    unittest.main()
