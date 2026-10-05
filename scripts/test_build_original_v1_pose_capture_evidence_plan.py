"""Tests for automatic pose->tissue->camera->evidence planning."""
import importlib.util, json, tempfile
from pathlib import Path
import unittest
MODULE=Path(__file__).with_name("build_original_v1_pose_capture_evidence_plan.py")
SPEC=importlib.util.spec_from_file_location("pose_plan",MODULE); mod=importlib.util.module_from_spec(SPEC); SPEC.loader.exec_module(mod)

class PoseEvidencePlanTests(unittest.TestCase):
    def test_press_top_expands_shoulder_chest_back_scope(self):
        scope={
          "candidate":"fixture.blend","candidate_sha256":"a"*64,"status":"READ_ONLY_POSE_COUPLING_SCOPE",
          "poses":{"press_top":{
            "moved_bone_count":2,
            "required_coupling_system_ids":["CP-NECK-TRAP-001","CP-PEC-AX-002","CP-POSTAX-003","CP-DELTOID-004"],
          }}
        }
        out=mod.build(scope)
        row=out["poses"]["press_top"]
        self.assertIn("vertical_push",row["movement_families"])
        self.assertIn("inferior_axilla_close",row["capture_views"])
        self.assertIn("anterior_axillary_fold",row["close_landmarks"])
        self.assertTrue({"CP-PEC-AX-002","CP-POSTAX-003","CP-DELTOID-004"}.issubset(set(row["required_coupling_system_ids"])))
        self.assertIn("weights_only",row["required_layers"])

if __name__=="__main__": unittest.main()
