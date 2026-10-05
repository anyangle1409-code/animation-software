"""Tests for preferred ORIGINAL-v1 laptop workflow integrity."""
import importlib.util
from pathlib import Path
import unittest

P=Path(__file__).with_name("validate_original_v1_laptop_workflow_integrity.py")
S=importlib.util.spec_from_file_location("laptop_integrity",P); mod=importlib.util.module_from_spec(S); S.loader.exec_module(mod)

class LaptopWorkflowIntegrityTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.files=set(mod.REQUIRED_FILES)
        cls.contents={p:(mod.ROOT/p).read_text(encoding="utf-8") for p in mod.REQUIRED_FILES if (mod.ROOT/p).suffix in {".py",".md",".json"}}

    def test_live_workflow_integrity(self):
        out=mod.validate()
        self.assertEqual(out["status"],"PASS")
        self.assertEqual(out["master_stage"],1)
        self.assertFalse(out["high_detail_anatomy_allowed"])

    def test_missing_required_runner_fails(self):
        files=set(self.files); files.remove("RUN_ORIGINAL_V1_CANDIDATE_COMPARISON.bat")
        with self.assertRaisesRegex(ValueError,"required laptop workflow files missing"):
            mod.validate(files,self.contents)

    def test_pickup_integrity_requires_one_command_sweep_pipeline(self):
        contents=dict(self.contents)
        p="scripts/build_original_v1_stage1_laptop_pickup_plan.py"
        contents[p]=contents[p].replace("RUN_ORIGINAL_V1_HUMAN_MOVEMENT_SWEEP_PIPELINE.bat","REMOVED_SWEEP_PIPELINE")
        with self.assertRaisesRegex(ValueError,"pickup planner command chain incomplete"):
            mod.validate(self.files,contents)

    def test_calibration_finalizer_cannot_disappear_from_pickup(self):
        contents=dict(self.contents)
        p="scripts/build_original_v1_stage1_laptop_pickup_plan.py"
        contents[p]=contents[p].replace("RUN_ORIGINAL_V1_FINALIZE_HUMAN_MOVEMENT_SWEEP_CALIBRATION.bat","REMOVED_CAL_FINALIZER")
        with self.assertRaisesRegex(ValueError,"pickup planner command chain incomplete"):
            mod.validate(self.files,contents)

    def test_post_edit_acceptance_preflight_cannot_disappear(self):
        contents=dict(self.contents)
        p="scripts/build_original_v1_stage1_post_edit_continuation_plan.py"
        contents[p]=contents[p].replace("RUN_ORIGINAL_V1_VALIDATE_WORKSPACE_SWEEP_ACCEPTANCE.bat","REMOVED_SWEEP_PREFLIGHT")
        with self.assertRaisesRegex(ValueError,"post-edit planner command chain incomplete"):
            mod.validate(self.files,contents)

    def test_collector_must_build_motion_records(self):
        contents=dict(self.contents)
        p="scripts/collect_original_v1_workspace_sweep_evidence.py"
        contents[p]=contents[p].replace("MOTION_BUILDER","REMOVED_MOTION_BUILDER")
        with self.assertRaisesRegex(ValueError,"collector contract token missing"):
            mod.validate(self.files,contents)

    def test_current_handoff_must_name_pickup_packet(self):
        contents=dict(self.contents)
        p="docs/CURRENT_HANDOFF.md"
        contents[p]=contents[p].replace("RUN_ORIGINAL_V1_STAGE1_LAPTOP_PICKUP_PLAN.bat","REMOVED_PICKUP")
        with self.assertRaisesRegex(ValueError,"preferred workflow token missing"):
            mod.validate(self.files,contents)

    def test_status_cannot_enable_high_detail(self):
        import json
        contents=dict(self.contents)
        p="ORIGINAL_V1_HUMAN_BODY_STATUS.json"
        d=json.loads(contents[p]); d["high_detail_anatomy_allowed"]=True
        contents[p]=json.dumps(d)
        with self.assertRaisesRegex(ValueError,"blocks high-detail"):
            mod.validate(self.files,contents)

if __name__=="__main__": unittest.main()
