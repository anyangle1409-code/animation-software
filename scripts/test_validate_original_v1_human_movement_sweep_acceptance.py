"""Tests for fail-closed human movement sweep acceptance."""
import copy,hashlib,importlib.util,json,tempfile
from pathlib import Path
import unittest

P=Path(__file__).with_name("validate_original_v1_human_movement_sweep_acceptance.py")
S=importlib.util.spec_from_file_location("accept",P); mod=importlib.util.module_from_spec(S); S.loader.exec_module(mod)

class SweepAcceptanceTests(unittest.TestCase):
    def write(self,root,name,obj):
        p=root/name; p.write_text(json.dumps(obj),encoding="utf-8"); return name

    def fixture(self,root,sweep="trunk_flexion"):
        csha="a"*64; plan=mod.read(mod.PLAN)["sweeps"][sweep]
        spec=json.loads((mod.ROOT/"ORIGINAL_V1_HUMAN_MOVEMENT_SWEEP_EXECUTION_SPEC.json").read_text(encoding="utf-8"))
        sr=spec["sweeps"][sweep]
        samples=[]
        variants=["l","r"] if sweep=="hip_abduction_adduction" else [None]
        for variant in variants:
            for sample in sr["samples"]:
                samples.append({
                  "label":sample["label"],
                  "return_leg":bool(sample.get("return_leg",False)),
                  "input":{k:v for k,v in sample.items() if k!="label"},
                  "variant":variant,
                  "joint_state_sha256":"1"*64,
                  "snapshot_sha256":"2"*64,
                  "snapshot":{"final_surface":{},"weights_only_surface":{},"corrective_contribution":{},"shape_key_values":{},"joint_state":{}}
                })
        raw_obj={
          "schema_version":1,"status":"READ_ONLY_GENERIC_HUMAN_MOVEMENT_SWEEP_AUDIT","production_approved":False,
          "candidate":"candidate.blend","candidate_sha256":csha,"candidate_sha256_before":csha,"candidate_sha256_after":csha,
          "runner_script_sha256":hashlib.sha256((mod.ROOT/"scripts/audit_original_v1_human_movement_sweeps_blender.py").read_bytes()).hexdigest(),
          "pose_definition_sha256":hashlib.sha256((mod.ROOT/"scripts/pose_test_original_v1_o4_candidate_blender.py").read_bytes()).hexdigest(),
          "flexion_driver_sha256":hashlib.sha256((mod.ROOT/"scripts/original_v1_flexion_driver.py").read_bytes()).hexdigest(),
          "movement_plan_sha256":hashlib.sha256((mod.ROOT/"ORIGINAL_V1_HUMAN_MOVEMENT_SWEEP_PLAN.json").read_bytes()).hexdigest(),
          "sweep_execution_spec_sha256":hashlib.sha256((mod.ROOT/"ORIGINAL_V1_HUMAN_MOVEMENT_SWEEP_EXECUTION_SPEC.json").read_bytes()).hexdigest(),
          "blender_version":"fixture","source_saved_or_modified":False,
          "calibration_state":"EXPERIMENTAL_UNCALIBRATED","evidence_readiness":"DIAGNOSTIC_ONLY_INCOMPLETE",
          "runner_capabilities":{
            "deterministic_joint_state_sampling":"IMPLEMENTED","per_sample_joint_state_hash":"IMPLEMENTED",
            "weights_only_surface_summary":"IMPLEMENTED","corrective_contribution_summary":"IMPLEMENTED",
            "runner_script_hash":"IMPLEMENTED","end_of_run_source_rehash":"IMPLEMENTED",
            "visual_capture_manifest":"NOT_IMPLEMENTED","required_regional_renders":"NOT_IMPLEMENTED","contact_load_state":"NOT_IMPLEMENTED"
          },
          "diagnostic_limitations":["fixture diagnostic limitations"],
          "sweeps":{sweep:{
            "implementation_status":sr["implementation_status"],
            "plan_evidence_ids":sr["evidence_ids"],"plan_regions":sr["regions"],"plan_cameras":sr["cameras"],
            "samples":samples,"visual_capture_status":"NOT_IMPLEMENTED",
            "contact_load_required":bool(sr.get("contact_load_required")),
            "contact_load_status":"NOT_IMPLEMENTED" if sr.get("contact_load_required") else "NOT_APPLICABLE",
            "engineering_review":"PENDING","owner_review":"PENDING"
          }}
        }
        raw=self.write(root,"raw.json",raw_obj)
        cal_template=json.loads((mod.ROOT/"ORIGINAL_V1_HUMAN_MOVEMENT_SWEEP_RUNNER_CALIBRATION_TEMPLATE.json").read_text(encoding="utf-8"))
        cal_template["calibration_candidate_revision"]="r95"
        cal_template["calibration_candidate_sha256"]="f"*64
        cal_template["runner_sha256"]=hashlib.sha256((mod.ROOT/"scripts/audit_original_v1_human_movement_sweeps_blender.py").read_bytes()).hexdigest()
        cal_template["execution_spec_sha256"]=hashlib.sha256((mod.ROOT/"ORIGINAL_V1_HUMAN_MOVEMENT_SWEEP_EXECUTION_SPEC.json").read_bytes()).hexdigest()
        cal_template["frozen_pose_source_sha256"]=hashlib.sha256((mod.ROOT/"scripts/pose_test_original_v1_o4_candidate_blender.py").read_bytes()).hexdigest()
        for adapter in cal_template["adapters"]:
            adapter["state"]="CALIBRATED"
            adapter["skeleton_joint_state_manifest"]="joint.json"
            adapter["outbound_return_evidence"]="return.json"
            adapter["sample_order_evidence"]="order.json"
            adapter["source_hash_evidence"]="hash.json"
            adapter["human_evidence_review_refs"]=["review"]
            if adapter["id"]=="hip_abduction_adduction":
                adapter["mirrored_input_evidence"]="mirror.json"
        cal_template["overall_state"]="CALIBRATED"
        cal_template["engineering_review"]="PASS"
        cal=self.write(root,"cal.json",cal_template)
        visual_samples=[]
        for label in plan["samples"]:
            views=[]
            for camera in plan["cameras"]:
                img=root/f"{sweep}_{label}_{camera}.png"
                img.write_bytes(f"{sweep}|{label}|{camera}".encode("utf-8"))
                views.append({
                  "camera_id":camera,"path":img.name,"sha256":hashlib.sha256(img.read_bytes()).hexdigest(),
                  "capture":{
                    "candidate_sha256":csha,"sweep_id":sweep,"sample_label":label,"camera_id":camera,
                    "runner_script_sha256":"3"*64,
                    "camera_matrix_world":[[1,0,0,0],[0,1,0,0],[0,0,1,0],[0,0,0,1]],
                    "resolution":[900,900,100]
                  }
                })
            visual_samples.append({"label":label,"views":views})
        vis=self.write(root,"vis.json",{
          "schema_version":1,"status":"HUMAN_MOVEMENT_SWEEP_VISUAL_CAPTURE","production_approved":False,
          "candidate_revision":"r96","candidate_sha256":csha,"sweep_id":sweep,
          "raw_sweep_report_path":raw,"samples":visual_samples,
          "engineering_review":"PASS","owner_review":"PENDING"
        })
        cont=self.write(root,"cont.json",{"candidate_sha256":csha,"sweep_id":sweep})
        rev=self.write(root,"rev.json",{"candidate_sha256":csha,"sweep_id":sweep})
        d={
          "schema_version":1,"status":"HUMAN_MOVEMENT_SWEEP_ACCEPTANCE","production_approved":False,
          "candidate_revision":"r96","candidate_sha256":csha,"sweep_id":sweep,
          "raw_sweep_report_path":raw,"runner_calibration_record_path":cal,
          "visual_capture_manifest_path":vis,"contact_report_path":None,
          "motion_continuity_evidence_path":cont,"motion_reversibility_evidence_path":rev,
          "required_human_evidence_ids":plan["evidence_ids"],
          "human_evidence_review_refs":plan["evidence_ids"],
          "continuity_review_status":"PASS","reversibility_review_status":"PASS",
          "visual_review_status":"PASS","contact_review_status":"NOT_APPLICABLE",
          "engineering_review":"PASS","owner_review":"PENDING"
        }
        return d

    def test_non_contact_sweep_can_pass_with_full_evidence(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td); out=mod.validate(self.fixture(root),root,True)
            self.assertEqual(out["engineering_review"],"PASS")

    def test_visual_sample_gap_blocks_pass(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td); d=self.fixture(root)
            vis=mod.read(root/d["visual_capture_manifest_path"]); vis["samples"].pop()
            (root/d["visual_capture_manifest_path"]).write_text(json.dumps(vis),encoding="utf-8")
            with self.assertRaisesRegex(ValueError,"visual capture missing sample"):
                mod.validate(d,root,True)

    def test_contact_sweep_requires_contact_report(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td); d=self.fixture(root,"ankle_plantarflexion")
            d["contact_review_status"]="PASS"
            with self.assertRaisesRegex(ValueError,"contact report"):
                mod.validate(d,root,True)

    def test_uncalibrated_runner_blocks_pass(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td); d=self.fixture(root)
            cal=mod.read(root/d["runner_calibration_record_path"])
            cal["overall_state"]="NOT_RUN"; cal["engineering_review"]="PENDING"
            (root/d["runner_calibration_record_path"]).write_text(json.dumps(cal),encoding="utf-8")
            with self.assertRaisesRegex(ValueError,"CALIBRATED|calibration incomplete"):
                mod.validate(d,root,True)

if __name__=="__main__": unittest.main()
