"""Tests for all 14 practical anatomical repair packages."""
import copy,importlib.util
from pathlib import Path
import unittest

P=Path(__file__).with_name("validate_original_v1_anatomical_repair_packages.py")
S=importlib.util.spec_from_file_location("repair_packages",P); mod=importlib.util.module_from_spec(S); S.loader.exec_module(mod)

class RepairPackageTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.packages=mod.read(mod.PACKAGES); cls.coupling=mod.read(mod.COUPLING); cls.capture=mod.read(mod.CAPTURE)

    def test_live_packages_valid(self):
        out=mod.validate(self.packages,self.coupling,self.capture)
        self.assertEqual(out["packages"],14)

    def test_every_package_has_weights_only_acceptance(self):
        self.assertTrue(all(x["weights_only_acceptance"] for x in self.packages["packages"]))

    def test_current_shoulder_chain_is_current_blocker(self):
        by={x["coupling_system_id"]:x for x in self.packages["packages"]}
        for cid in ("CP-PEC-AX-002","CP-POSTAX-003","CP-DELTOID-004"):
            self.assertEqual(by[cid]["priority"],"current_blocker")

    def test_corrective_masking_shortcut_is_forbidden(self):
        bad=copy.deepcopy(self.packages)
        bad["universal_forbidden_shortcuts"].remove("corrective_used_to_hide_wrong_base_weights")
        with self.assertRaisesRegex(ValueError,"corrective masking"):
            mod.validate(bad,self.coupling,self.capture)

    def test_proof_movement_must_exist_in_capture_plan(self):
        bad=copy.deepcopy(self.packages)
        bad["packages"][0]["proof_movements"].append("not_a_real_motion")
        with self.assertRaisesRegex(ValueError,"outside capture plan"):
            mod.validate(bad,self.coupling,self.capture)

if __name__=="__main__": unittest.main()
