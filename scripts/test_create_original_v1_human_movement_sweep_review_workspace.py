"""Tests for one-command human movement sweep review workspace generation."""
import hashlib,importlib.util,json,tempfile
from pathlib import Path
import unittest

P=Path(__file__).with_name("create_original_v1_human_movement_sweep_review_workspace.py")
S=importlib.util.spec_from_file_location("sweep_review_workspace",P); mod=importlib.util.module_from_spec(S); S.loader.exec_module(mod)

RAW_PATH=Path(__file__).with_name("validate_original_v1_human_movement_sweep_report.py")
RS=importlib.util.spec_from_file_location("raw_validator",RAW_PATH); rv=importlib.util.module_from_spec(RS); RS.loader.exec_module(rv)

class SweepReviewWorkspaceTests(unittest.TestCase):
    def raw_fixture(self,sweep="trunk_flexion"):
        spec=rv.read(rv.SPEC); csha="a"*64
        row=spec["sweeps"][sweep]
        samples=[]
        for sample in row["samples"]:
            snap={
              "final_surface":{},"weights_only_surface":{},"corrective_contribution":{},
              "shape_key_values":{},"joint_state":{}
            }
            samples.append({
              "label":sample["label"],"return_leg":bool(sample.get("return_leg",False)),
              "input":{k:v for k,v in sample.items() if k!="label"},"variant":None,
              "joint_state_sha256":"b"*64,"snapshot_sha256":"c"*64,"snapshot":snap
            })
        return {
          "schema_version":1,"status":"READ_ONLY_GENERIC_HUMAN_MOVEMENT_SWEEP_AUDIT",
          "production_approved":False,"candidate":"fixture.blend","candidate_sha256":csha,
          "candidate_sha256_before":csha,"candidate_sha256_after":csha,
          "runner_script_sha256":hashlib.sha256(rv.RUNNER.read_bytes()).hexdigest(),
          "blender_version":"5.2.1",
          "pose_definition_sha256":hashlib.sha256(rv.POSE.read_bytes()).hexdigest(),
          "flexion_driver_sha256":hashlib.sha256(rv.FLEXION.read_bytes()).hexdigest(),
          "movement_plan_sha256":hashlib.sha256(rv.PLAN.read_bytes()).hexdigest(),
          "sweep_execution_spec_sha256":hashlib.sha256(rv.SPEC.read_bytes()).hexdigest(),
          "source_saved_or_modified":False,"calibration_state":"EXPERIMENTAL_UNCALIBRATED",
          "evidence_readiness":"DIAGNOSTIC_ONLY_INCOMPLETE",
          "runner_capabilities":{
            "deterministic_joint_state_sampling":"IMPLEMENTED",
            "per_sample_joint_state_hash":"IMPLEMENTED",
            "weights_only_surface_summary":"IMPLEMENTED",
            "corrective_contribution_summary":"IMPLEMENTED",
            "runner_script_hash":"IMPLEMENTED",
            "end_of_run_source_rehash":"IMPLEMENTED",
            "visual_capture_manifest":"NOT_IMPLEMENTED",
            "required_regional_renders":"NOT_IMPLEMENTED",
            "contact_load_state":"NOT_IMPLEMENTED"
          },
          "diagnostic_limitations":["fixture diagnostic only"],
          "sweeps":{sweep:{
            "implementation_status":row["implementation_status"],
            "plan_evidence_ids":row["evidence_ids"],"plan_regions":row["regions"],"plan_cameras":row["cameras"],
            "samples":samples,"visual_capture_status":"NOT_IMPLEMENTED",
            "contact_load_required":bool(row.get("contact_load_required")),
            "contact_load_status":"NOT_IMPLEMENTED" if row.get("contact_load_required") else "NOT_APPLICABLE",
            "engineering_review":"PENDING","owner_review":"PENDING"
          }}
        }

    def visual_fixture(self,sweep,csha):
        return {
          "schema_version":1,"status":"HUMAN_MOVEMENT_SWEEP_VISUAL_CAPTURE","production_approved":False,
          "candidate_revision":"r96","candidate_sha256":csha,"sweep_id":sweep,
          "raw_sweep_report_path":None,"samples":[],"engineering_review":"PENDING","owner_review":"PENDING"
        }

    def test_builds_pending_review_workspace_for_non_contact_sweep(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td); raw_path=root/"raw.json"; vis=root/"visual"; out=root/"review"
            raw=self.raw_fixture(); raw_path.write_text(json.dumps(raw),encoding="utf-8")
            vis.mkdir(); (vis/"human_movement_sweep_visual_trunk_flexion.json").write_text(
                json.dumps(self.visual_fixture("trunk_flexion",raw["candidate_sha256"])),encoding="utf-8")
            cal=mod.ROOT/"ORIGINAL_V1_HUMAN_MOVEMENT_SWEEP_RUNNER_CALIBRATION_TEMPLATE.json"
            result=mod.build(raw_path,"r96",cal,vis,None,out,["trunk_flexion"])
            self.assertEqual(result["candidate_sha256"],raw["candidate_sha256"])
            self.assertEqual(result["sweeps"]["trunk_flexion"]["state"],"REVIEW_PENDING")
            acc=json.loads((out/"trunk_flexion"/"acceptance.json").read_text())
            self.assertEqual(acc["engineering_review"],"PENDING")
            self.assertEqual(acc["contact_review_status"],"NOT_APPLICABLE")
            self.assertTrue((out/"trunk_flexion"/"motion_review.json").is_file())

    def test_visual_candidate_mismatch_blocks_workspace(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td); raw_path=root/"raw.json"; vis=root/"visual"; out=root/"review"
            raw=self.raw_fixture(); raw_path.write_text(json.dumps(raw),encoding="utf-8")
            vis.mkdir(); (vis/"human_movement_sweep_visual_trunk_flexion.json").write_text(
                json.dumps(self.visual_fixture("trunk_flexion","d"*64)),encoding="utf-8")
            cal=mod.ROOT/"ORIGINAL_V1_HUMAN_MOVEMENT_SWEEP_RUNNER_CALIBRATION_TEMPLATE.json"
            with self.assertRaisesRegex(ValueError,"visual candidate differs"):
                mod.build(raw_path,"r96",cal,vis,None,out,["trunk_flexion"])

    def test_unknown_requested_sweep_is_rejected(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td); raw_path=root/"raw.json"; vis=root/"visual"; out=root/"review"
            raw=self.raw_fixture(); raw_path.write_text(json.dumps(raw),encoding="utf-8"); vis.mkdir()
            cal=mod.ROOT/"ORIGINAL_V1_HUMAN_MOVEMENT_SWEEP_RUNNER_CALIBRATION_TEMPLATE.json"
            with self.assertRaisesRegex(ValueError,"absent from raw report"):
                mod.build(raw_path,"r96",cal,vis,None,out,["not_real"])

if __name__=="__main__": unittest.main()
