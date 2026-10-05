"""Tests for Stage 1 laptop pickup planner."""
import argparse,hashlib,importlib.util,tempfile
from pathlib import Path
import unittest

P=Path(__file__).with_name("build_original_v1_stage1_laptop_pickup_plan.py")
S=importlib.util.spec_from_file_location("pickup",P); mod=importlib.util.module_from_spec(S); S.loader.exec_module(mod)

class LaptopPickupPlanTests(unittest.TestCase):
    def args(self,root,wave="current",new_rev="r96"):
        candidate=root/"candidate.blend"; candidate.write_bytes(b"pickup-candidate")
        return argparse.Namespace(
          candidate=str(candidate),current_revision="r95",new_revision=new_rev,
          source_branch="fixture",side="bilateral",label="pickup_test",
          workspace=str(root/"workspace"),wave=wave,expected_sha=None,out_dir=str(root/"out")
        )

    def test_current_wave_generates_shoulder_pickup(self):
        with tempfile.TemporaryDirectory() as td:
            d=mod.build(self.args(Path(td)))
            self.assertEqual(d["wave_id"],"shoulder_yoke_foundation")
            self.assertIn("RP-PEC-AX-002",d["repair_package_ids"])
            self.assertTrue(any(x["phase"]=="pre_repair_diagnostics" for x in d["commands"]))
            self.assertTrue(any(x["phase"]=="repair_workspace" for x in d["commands"]))

    def test_candidate_sha_is_computed_from_file(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td); a=self.args(root)
            want=hashlib.sha256(Path(a.candidate).read_bytes()).hexdigest()
            d=mod.build(a)
            self.assertEqual(d["current_candidate"]["sha256"],want)

    def test_expected_sha_mismatch_blocks(self):
        with tempfile.TemporaryDirectory() as td:
            a=self.args(Path(td)); a.expected_sha="f"*64
            with self.assertRaisesRegex(ValueError,"candidate SHA differs"):
                mod.build(a)

    def test_same_revision_blocks(self):
        with tempfile.TemporaryDirectory() as td:
            a=self.args(Path(td),new_rev="r95")
            with self.assertRaisesRegex(ValueError,"new revision must differ"):
                mod.build(a)

    def test_pickup_stops_before_actual_model_edit(self):
        with tempfile.TemporaryDirectory() as td:
            d=mod.build(self.args(Path(td)))
            self.assertEqual(d["commands"][-1]["phase"],"model_edit_boundary")
            self.assertFalse(d["commands"][-1]["blocking"])

if __name__=="__main__": unittest.main()
