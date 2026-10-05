"""Tests for dependency-aware Stage 1 repair execution graph."""
import copy,importlib.util
from pathlib import Path
import unittest

P=Path(__file__).with_name("validate_original_v1_stage1_repair_execution_graph.py")
S=importlib.util.spec_from_file_location("stage1_graph",P); mod=importlib.util.module_from_spec(S); S.loader.exec_module(mod)

class Stage1RepairGraphTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.g=mod.read(mod.GRAPH); cls.p=mod.read(mod.PACKAGES); cls.m=mod.read(mod.MASTER)

    def test_live_graph_valid(self):
        out=mod.validate(self.g,self.p,self.m)
        self.assertEqual(out["waves"],8)
        self.assertEqual(out["packages"],14)

    def test_shoulder_yoke_is_connected_cluster(self):
        w=next(x for x in self.g["waves"] if x["id"]=="shoulder_yoke_foundation")
        self.assertEqual(w["mode"],"solve_as_connected_cluster")
        self.assertTrue({"RP-PEC-AX-002","RP-POSTAX-003","RP-DELTOID-004","RP-NECK-TRAP-001"}.issubset(set(w["package_ids"])))

    def test_whole_body_integration_contains_all_packages(self):
        final=self.g["waves"][-1]
        self.assertEqual(set(final["package_ids"]),{x["id"] for x in self.p["packages"]})

    def test_high_detail_cannot_precede_whole_body_exit(self):
        self.assertIn("enter high-detail anatomy before whole_body_integration exit",self.g["invalid_sequences"])

    def test_missing_package_from_final_wave_fails(self):
        bad=copy.deepcopy(self.g); bad["waves"][-1]["package_ids"].pop()
        with self.assertRaisesRegex(ValueError,"every repair package"):
            mod.validate(bad,self.p,self.m)

if __name__=="__main__": unittest.main()
