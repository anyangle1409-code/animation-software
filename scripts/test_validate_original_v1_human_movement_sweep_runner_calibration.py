"""Tests for generic sweep runner calibration contract."""
import copy,importlib.util
from pathlib import Path
import unittest
P=Path(__file__).with_name("validate_original_v1_human_movement_sweep_runner_calibration.py")
S=importlib.util.spec_from_file_location("cal",P); mod=importlib.util.module_from_spec(S); S.loader.exec_module(mod)

class SweepRunnerCalibrationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls): cls.t=mod.read(mod.TEMPLATE)

    def test_template_valid_but_not_calibrated(self):
        out=mod.validate(self.t,False)
        self.assertEqual(out["adapters"],11); self.assertEqual(out["calibrated"],0)

    def test_require_calibrated_blocks_template(self):
        with self.assertRaisesRegex(ValueError,"calibration incomplete"):
            mod.validate(self.t,True)

    def test_adapter_cannot_claim_calibrated_without_evidence(self):
        bad=copy.deepcopy(self.t); bad["adapters"][0]["state"]="CALIBRATED"
        with self.assertRaisesRegex(ValueError,"CALIBRATED without"):
            mod.validate(bad)

    def test_overall_cannot_calibrate_early(self):
        bad=copy.deepcopy(self.t); bad["overall_state"]="CALIBRATED"
        with self.assertRaisesRegex(ValueError,"before all adapters"):
            mod.validate(bad)

if __name__=="__main__": unittest.main()
