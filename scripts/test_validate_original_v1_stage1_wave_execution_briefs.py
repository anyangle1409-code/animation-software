"""Tests for Stage 1 wave execution briefs."""
import copy,importlib.util
from pathlib import Path
import unittest
P=Path(__file__).with_name("validate_original_v1_stage1_wave_execution_briefs.py")
S=importlib.util.spec_from_file_location("wave_briefs",P); mod=importlib.util.module_from_spec(S); S.loader.exec_module(mod)
class WaveBriefTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.b=mod.read(mod.BRIEFS); cls.g=mod.read(mod.GRAPH); cls.p=mod.read(mod.PACKAGES); cls.pm=mod.read(mod.POSES); cls.s=mod.read(mod.SWEEPS)
    def test_live_briefs_valid(self):
        out=mod.validate(self.b,self.g,self.p,self.pm,self.s); self.assertEqual(out["waves"],8)
    def test_current_wave_is_shoulder_yoke(self):
        self.assertEqual(self.b["current_wave_id"],"shoulder_yoke_foundation")
    def test_all_waves_have_paste_ready_commands(self):
        for row in self.b["waves"][1:]:
            self.assertIn("RUN_ORIGINAL_V1_PRE_REPAIR_DIAGNOSTIC_BUNDLE.bat",row["operator"]["pre_repair"])
            self.assertIn("RUN_ORIGINAL_V1_CREATE_REPAIR_WORKSPACE.bat",row["operator"]["create_workspace"])
    def test_sweep_definitions_are_not_mislabelled_as_executed(self):
        for row in self.b["waves"]:
            if row["validation"]["deterministic_sweep_definitions"]:
                self.assertEqual(row["validation"]["sweep_runner_status"],"RUNNER_BOUND_CALIBRATION_AND_CANDIDATE_EXECUTION_REQUIRED")
                self.assertEqual(row["validation"]["sweep_runner_binding"],"BOUND_11_OF_11")
                self.assertEqual(row["validation"]["candidate_sweep_acceptance"],"NOT_RUN")
                self.assertIn("RUN_ORIGINAL_V1_HUMAN_MOVEMENT_SWEEPS.bat",row["operator"]["pre_repair_sweeps"])
                self.assertIn("RUN_ORIGINAL_V1_HUMAN_MOVEMENT_SWEEPS.bat",row["operator"]["post_repair_sweeps"])
    def test_package_drift_fails(self):
        bad=copy.deepcopy(self.b); bad["waves"][1]["packages"].pop()
        with self.assertRaisesRegex(ValueError,"packages differ"): mod.validate(bad,self.g,self.p,self.pm,self.s)
if __name__=="__main__": unittest.main()
