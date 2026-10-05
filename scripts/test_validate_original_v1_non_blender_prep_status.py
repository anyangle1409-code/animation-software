"""Tests for non-Blender preparation boundary."""
import copy,importlib.util
from pathlib import Path
import unittest
P=Path(__file__).with_name("validate_original_v1_non_blender_prep_status.py")
S=importlib.util.spec_from_file_location("prep",P); mod=importlib.util.module_from_spec(S); S.loader.exec_module(mod)
class NonBlenderPrepStatusTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls): cls.d=mod.read(mod.STATUS)
    def test_live_status_is_valid(self):
        out=mod.validate(self.d); self.assertGreaterEqual(out["prepared_components"],10)
    def test_prep_cannot_claim_model_acceptance(self):
        bad=copy.deepcopy(self.d); bad["anatomical_model_accepted"]=True
        with self.assertRaisesRegex(ValueError,"anatomical acceptance"): mod.validate(bad)
    def test_prep_cannot_zero_real_blockers(self):
        bad=copy.deepcopy(self.d); bad["current_model_state"]["open_critical_high_blockers"]=0
        with self.assertRaisesRegex(ValueError,"preserve open body blockers"): mod.validate(bad)
    def test_high_detail_remains_blocked(self):
        bad=copy.deepcopy(self.d); bad["high_detail_anatomy_allowed"]=True
        with self.assertRaisesRegex(ValueError,"high-detail anatomy"): mod.validate(bad)
    def test_missing_prepared_evidence_file_fails(self):
        bad=copy.deepcopy(self.d); bad["prepared_components"][0]["evidence"]=["DOES_NOT_EXIST.json"]
        with self.assertRaisesRegex(ValueError,"evidence file missing"): mod.validate(bad)
if __name__=="__main__": unittest.main()
