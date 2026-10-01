"""Claude session brief is derivative and names the actual selected work."""
from __future__ import annotations
import unittest

import original_v1_claude_brief as b


class ClaudeBriefTests(unittest.TestCase):
    def test_markdown_names_actual_work_command(self):
        data={"branch":"model","source_git_commit":"a"*40,"current_phase":3,"current_subphase":"3B",
              "current_candidate":"r29","candidate_classification":"TRADE-OFF","candidate_state":"experimental",
              "development_failure_count":7,"strict_r2_regression_count":6,
              "next_action":{"action":"RUN r30","command":"RUN_ORIGINAL_V1_R30.bat"},
              "selected_execution_node":{"id":"3B_r30","roadmap":"Phase 3B"},
              "start_commands":["A","B"],"actual_work_command":"RUN_ORIGINAL_V1_R30.bat",
              "non_negotiables":[],"prepared_support":[]}
        text=b.markdown(data)
        self.assertIn("RUN_ORIGINAL_V1_R30.bat",text)
        self.assertIn("Before ending",text)


if __name__=="__main__":
    unittest.main()
