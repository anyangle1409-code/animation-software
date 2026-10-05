"""Tests for fail-closed deformation diagnosis tree."""
import copy,importlib.util
from pathlib import Path
import unittest

P=Path(__file__).with_name("validate_original_v1_deformation_diagnosis_tree.py")
S=importlib.util.spec_from_file_location("diag_tree",P); mod=importlib.util.module_from_spec(S); S.loader.exec_module(mod)

class DiagnosisTreeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tree=mod.json.loads(mod.PATH.read_text(encoding="utf-8"))

    def test_live_tree_valid(self):
        out=mod.validate(self.tree)
        self.assertEqual(out["nodes"],10)

    def test_weights_failure_cannot_jump_to_corrective(self):
        by={x["id"]:x for x in self.tree["nodes"]}
        self.assertIn("corrective_shape",by["D3_WEIGHTS_ONLY"]["if_no"]["forbidden"])

    def test_corrective_is_joint_state_not_exercise_name(self):
        by={x["id"]:x for x in self.tree["nodes"]}
        self.assertEqual(by["D5_CORRECTIVES"]["if_yes"]["action"],"FIT_GENERIC_JOINT_STATE_CORRECTIVE")
        self.assertIn("exercise_name_driver",by["D5_CORRECTIVES"]["if_yes"]["forbidden"])

    def test_owner_acceptance_is_not_inferred(self):
        by={x["id"]:x for x in self.tree["nodes"]}
        self.assertEqual(by["D9_HUMAN_VISUAL"]["if_yes"]["action"],"ENGINEERING_CLEAR_ELIGIBLE_NOT_OWNER_ACCEPTED")

    def test_missing_earliest_failure_rule_fails(self):
        bad=copy.deepcopy(self.tree); bad["global_rule"]="later layers may compensate"
        with self.assertRaisesRegex(ValueError,"earliest-failing"):
            mod.validate(bad)

if __name__=="__main__": unittest.main()
