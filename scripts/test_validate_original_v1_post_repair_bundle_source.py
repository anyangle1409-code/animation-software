"""Tests for post-repair validation bundle static orchestration contract."""
import importlib.util
from pathlib import Path
import unittest
P=Path(__file__).with_name("validate_original_v1_post_repair_bundle_source.py")
S=importlib.util.spec_from_file_location("post_bundle",P); mod=importlib.util.module_from_spec(S); S.loader.exec_module(mod)
class PostRepairBundleSourceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls): cls.text=mod.BATCH.read_text(encoding="utf-8")
    def test_live_bundle_contract(self):
        self.assertEqual(mod.validate(self.text)["status"],"PASS")
    def test_missing_calibration_gate_fails(self):
        bad=self.text.replace("--require-calibrated","--BROKEN")
        with self.assertRaisesRegex(ValueError,"token missing"): mod.validate(bad)
    def test_wrong_sweep_order_fails(self):
        a="RUN_ORIGINAL_V1_HUMAN_MOVEMENT_SWEEPS.bat"; b="RUN_ORIGINAL_V1_HUMAN_MOVEMENT_SWEEP_VISUALS.bat"
        bad=self.text.replace(a,"TEMP_TOKEN",1).replace(b,a,1).replace("TEMP_TOKEN",b,1)
        with self.assertRaisesRegex(ValueError,"command order differs"): mod.validate(bad)
if __name__=="__main__": unittest.main()
