"""Tests for exact Stage-1 post-edit continuation planning."""
import importlib.util,json,tempfile
from argparse import Namespace
from pathlib import Path
import unittest
from unittest import mock

P=Path(__file__).with_name("build_original_v1_stage1_post_edit_continuation_plan.py")
S=importlib.util.spec_from_file_location("post_edit_plan",P); mod=importlib.util.module_from_spec(S); S.loader.exec_module(mod)

class PostEditContinuationPlanTests(unittest.TestCase):
    def make_workspace(self,root,revision="r96",packages=None,sweeps=None,final_sha=None):
        ws=root/"ws"; ws.mkdir()
        wm={
          "candidate_revision":revision,
          "repair_package_ids":packages or [],
          "validation_selection":{"sweep_only_movements_requiring_generic_runner":sweeps or []}
        }
        (ws/"workspace_manifest.json").write_text(json.dumps(wm),encoding="utf-8")
        if final_sha:
            (ws/"workspace_finalization_manifest.json").write_text(json.dumps({
              "candidate_revision":revision,"final_candidate_sha256":final_sha
            }),encoding="utf-8")
        return ws

    def make_candidate(self,root):
        p=root/"candidate.blend"; p.write_bytes(b"final-candidate"); return p

    def make_calibration(self,root,state="CALIBRATED",review="PASS"):
        p=root/"calibration.json"; p.write_text(json.dumps({
          "runner_id":"generic_human_movement_sweep_v1",
          "overall_state":state,
          "engineering_review":review
        }),encoding="utf-8"); return p

    def args(self,ws,candidate,cal=None):
        return Namespace(
          workspace=str(ws),final_candidate=str(candidate),revision="r96",prior="r95",
          label="postfix",calibration_record=None if cal is None else str(cal),out_dir="unused"
        )

    def calibrated_validator(self):
        fake=mock.Mock()
        fake.validate.return_value={"overall_state":"CALIBRATED"}
        return fake

    def test_no_sweep_package_needs_no_calibration_record(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td); ws=self.make_workspace(root,packages=["RP-QUAD-011"],sweeps=[])
            candidate=self.make_candidate(root)
            d=mod.build(self.args(ws,candidate))
            self.assertEqual(d["required_sweep_only_movements"],[])
            self.assertFalse(any("HUMAN_MOVEMENT_SWEEPS" in x["command"] for x in d["commands"]))

    def test_sweep_package_requires_calibrated_runner(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td); ws=self.make_workspace(root,packages=["RP-PEC-AX-002"],sweeps=["shoulder_abduction_elevation"])
            candidate=self.make_candidate(root)
            with self.assertRaisesRegex(ValueError,"need --calibration-record"):
                mod.build(self.args(ws,candidate))

    def test_unreviewed_or_stale_calibration_is_rejected(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td); ws=self.make_workspace(root,packages=["RP-PEC-AX-002"],sweeps=["shoulder_abduction_elevation"])
            candidate=self.make_candidate(root); cal=self.make_calibration(root,"IN_REVIEW","PENDING")
            fake=mock.Mock(); fake.validate.side_effect=ValueError("runner calibration incomplete")
            with mock.patch.object(mod,"load_calibration_validator",return_value=fake):
                with self.assertRaisesRegex(ValueError,"current-authority CALIBRATED"):
                    mod.build(self.args(ws,candidate,cal))

    def test_sweep_package_generates_raw_visual_motion_and_collection_commands(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td); ws=self.make_workspace(root,packages=["RP-PEC-AX-002"],sweeps=["shoulder_abduction_elevation"])
            candidate=self.make_candidate(root); cal=self.make_calibration(root)
            with mock.patch.object(mod,"load_calibration_validator",return_value=self.calibrated_validator()):
                d=mod.build(self.args(ws,candidate,cal))
            commands="\n".join(x["command"] for x in d["commands"])
            self.assertIn("RUN_ORIGINAL_V1_HUMAN_MOVEMENT_SWEEPS.bat",commands)
            self.assertIn("RUN_ORIGINAL_V1_HUMAN_MOVEMENT_SWEEP_VISUALS.bat",commands)
            self.assertIn("RUN_ORIGINAL_V1_COLLECT_WORKSPACE_SWEEP_EVIDENCE.bat",commands)
            self.assertIn("RUN_ORIGINAL_V1_HUMAN_MOVEMENT_SWEEP_MOTION_REVIEW.bat",commands)

    def test_contact_bearing_sweep_adds_contact_capture(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td); ws=self.make_workspace(root,packages=["RP-CALF-013"],sweeps=["ankle_plantarflexion"])
            candidate=self.make_candidate(root); cal=self.make_calibration(root)
            with mock.patch.object(mod,"load_calibration_validator",return_value=self.calibrated_validator()):
                d=mod.build(self.args(ws,candidate,cal))
            self.assertEqual(d["contact_bearing_required_sweeps"],["ankle_plantarflexion"])
            self.assertTrue(any("HUMAN_MOVEMENT_SWEEP_CONTACT_RAW.bat" in x["command"] for x in d["commands"]))

    def test_existing_finalization_must_match_actual_candidate_sha(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td); candidate=self.make_candidate(root)
            ws=self.make_workspace(root,packages=[],sweeps=[],final_sha="f"*64)
            with self.assertRaisesRegex(ValueError,"different candidate SHA"):
                mod.build(self.args(ws,candidate))

if __name__=="__main__": unittest.main()
