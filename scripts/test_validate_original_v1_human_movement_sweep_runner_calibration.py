"""Tests for generic sweep runner calibration contract."""
import hashlib,importlib.util,json,tempfile
from pathlib import Path
import unittest

P=Path(__file__).with_name("validate_original_v1_human_movement_sweep_runner_calibration.py")
S=importlib.util.spec_from_file_location("cal",P); mod=importlib.util.module_from_spec(S); S.loader.exec_module(mod)
B=Path(__file__).with_name("build_original_v1_human_movement_sweep_runner_calibration.py")
SB=importlib.util.spec_from_file_location("cal_builder",B); builder=importlib.util.module_from_spec(SB); SB.loader.exec_module(builder)

class SweepRunnerCalibrationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls): cls.t=mod.read(mod.TEMPLATE)

    def raw_report(self,root):
        spec=mod.read(mod.SPEC); csha="a"*64; sweeps={}
        for sid,sr in spec["sweeps"].items():
            samples=[]; variants=["l","r"] if sid=="hip_abduction_adduction" else [None]
            for variant in variants:
                seen={}
                for sample in sr["samples"]:
                    norm={k:v for k,v in sample.items() if k not in {"label","return_leg"}}
                    key=(variant,json.dumps(norm,sort_keys=True))
                    if sample.get("return_leg") and key in seen:
                        js,ss=seen[key]
                    else:
                        js=hashlib.sha256(f"{sid}|{variant}|{norm}|joint".encode()).hexdigest()
                        ss=hashlib.sha256(f"{sid}|{variant}|{norm}|snapshot".encode()).hexdigest()
                        seen[key]=(js,ss)
                    samples.append({
                      "label":sample["label"],"return_leg":bool(sample.get("return_leg",False)),
                      "input":{k:v for k,v in sample.items() if k!="label"},"variant":variant,
                      "joint_state_sha256":js,"snapshot_sha256":ss,
                      "snapshot":{"final_surface":{},"weights_only_surface":{},"corrective_contribution":{},"shape_key_values":{},"joint_state":{}}
                    })
            sweeps[sid]={
              "implementation_status":sr["implementation_status"],
              "plan_evidence_ids":sr["evidence_ids"],"plan_regions":sr["regions"],"plan_cameras":sr["cameras"],
              "samples":samples,"visual_capture_status":"NOT_IMPLEMENTED",
              "contact_load_required":bool(sr.get("contact_load_required")),
              "contact_load_status":"NOT_IMPLEMENTED" if sr.get("contact_load_required") else "NOT_APPLICABLE",
              "engineering_review":"PENDING","owner_review":"PENDING"
            }
        raw={
          "schema_version":1,"status":"READ_ONLY_GENERIC_HUMAN_MOVEMENT_SWEEP_AUDIT","production_approved":False,
          "candidate":"fixture.blend","candidate_sha256":csha,"candidate_sha256_before":csha,"candidate_sha256_after":csha,
          "runner_script_sha256":hashlib.sha256(mod.RUNNER.read_bytes()).hexdigest(),
          "pose_definition_sha256":hashlib.sha256(mod.POSE.read_bytes()).hexdigest(),
          "flexion_driver_sha256":hashlib.sha256((mod.ROOT/"scripts/original_v1_flexion_driver.py").read_bytes()).hexdigest(),
          "movement_plan_sha256":hashlib.sha256((mod.ROOT/"ORIGINAL_V1_HUMAN_MOVEMENT_SWEEP_PLAN.json").read_bytes()).hexdigest(),
          "sweep_execution_spec_sha256":hashlib.sha256(mod.SPEC.read_bytes()).hexdigest(),
          "blender_version":"fixture","source_saved_or_modified":False,
          "calibration_state":"EXPERIMENTAL_UNCALIBRATED","evidence_readiness":"DIAGNOSTIC_ONLY_INCOMPLETE",
          "runner_capabilities":{
            "deterministic_joint_state_sampling":"IMPLEMENTED","per_sample_joint_state_hash":"IMPLEMENTED",
            "weights_only_surface_summary":"IMPLEMENTED","corrective_contribution_summary":"IMPLEMENTED",
            "runner_script_hash":"IMPLEMENTED","end_of_run_source_rehash":"IMPLEMENTED",
            "visual_capture_manifest":"NOT_IMPLEMENTED","required_regional_renders":"NOT_IMPLEMENTED","contact_load_state":"NOT_IMPLEMENTED"
          },
          "diagnostic_limitations":["fixture"],"sweeps":sweeps
        }
        p=root/"raw.json"; p.write_text(json.dumps(raw),encoding="utf-8"); return p

    def reviewed_record(self,root):
        raw=self.raw_report(root)
        d=builder.build(raw,"r95")
        for row in d["adapters"]:
            row["state"]="CALIBRATED"
            row["human_evidence_review_refs"]=list(row["required_human_evidence_ids"])
        d["overall_state"]="CALIBRATED"; d["engineering_review"]="PASS"
        return d,raw

    def test_template_valid_but_not_calibrated(self):
        out=mod.validate(self.t,False)
        self.assertEqual(out["adapters"],11); self.assertEqual(out["calibrated"],0)
        self.assertFalse(out["raw_report_bound"])

    def test_require_calibrated_blocks_template(self):
        with self.assertRaisesRegex(ValueError,"calibration incomplete"):
            mod.validate(self.t,True)

    def test_in_review_record_is_bound_to_real_raw_report(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td); raw=self.raw_report(root); d=builder.build(raw,"r95")
            out=mod.validate(d,False)
            self.assertEqual(out["overall_state"],"IN_REVIEW")
            self.assertTrue(out["raw_report_bound"])

    def test_full_calibrated_record_passes(self):
        with tempfile.TemporaryDirectory() as td:
            d,_=self.reviewed_record(Path(td))
            out=mod.validate(d,True)
            self.assertEqual(out["calibrated"],11)
            self.assertEqual(out["overall_state"],"CALIBRATED")

    def test_raw_report_tamper_invalidates_calibration(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td); d,raw=self.reviewed_record(root)
            raw.write_text(raw.read_text()+"\n",encoding="utf-8")
            with self.assertRaisesRegex(ValueError,"raw sweep report SHA mismatch"):
                mod.validate(d,True)

    def test_adapter_evidence_must_point_to_its_raw_sweep(self):
        with tempfile.TemporaryDirectory() as td:
            d,_=self.reviewed_record(Path(td))
            d["adapters"][0]["skeleton_joint_state_manifest"]="other.json"
            with self.assertRaisesRegex(ValueError,"not bound to raw report sweep"):
                mod.validate(d,True)

    def test_human_evidence_review_is_required_for_calibrated_adapter(self):
        with tempfile.TemporaryDirectory() as td:
            d,_=self.reviewed_record(Path(td))
            d["adapters"][0]["human_evidence_review_refs"]=[]
            with self.assertRaisesRegex(ValueError,"without human evidence review"):
                mod.validate(d,True)

    def test_unknown_human_evidence_reference_is_rejected(self):
        with tempfile.TemporaryDirectory() as td:
            d,_=self.reviewed_record(Path(td))
            d["adapters"][0]["human_evidence_review_refs"].append("HE-NOT-REAL")
            with self.assertRaisesRegex(ValueError,"unknown human evidence review refs"):
                mod.validate(d,True)

if __name__=="__main__": unittest.main()
