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
        raw=self.write(root,"raw.json",{"candidate_sha256":csha,"source_saved_or_modified":False,"sweeps":{sweep:{}}})
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
        vis=self.write(root,"vis.json",{"candidate_sha256":csha,"sweep_id":sweep,"samples":[{"label":x,"views":plan["cameras"]} for x in plan["samples"]]})
        cont=self.write(root,"cont.json",{"candidate_sha256":csha,"sweep_id":sweep})
        rev=self.write(root,"rev.json",{"candidate_sha256":csha,"sweep_id":sweep})
        d={
          "schema_version":1,"status":"HUMAN_MOVEMENT_SWEEP_ACCEPTANCE","production_approved":False,
          "candidate_revision":"r96","candidate_sha256":csha,"sweep_id":sweep,
          "raw_sweep_report_path":raw,"runner_calibration_record_path":cal,
          "visual_capture_manifest_path":vis,"contact_report_path":None,
          "motion_continuity_evidence_path":cont,"motion_reversibility_evidence_path":rev,
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
