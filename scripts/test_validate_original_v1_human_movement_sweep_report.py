"""Tests for generic human movement sweep execution spec/report contracts."""
import copy,hashlib,importlib.util
from pathlib import Path
import unittest

P1=Path(__file__).with_name("validate_original_v1_human_movement_sweep_execution_spec.py")
S1=importlib.util.spec_from_file_location("specval",P1); specval=importlib.util.module_from_spec(S1); S1.loader.exec_module(specval)
P2=Path(__file__).with_name("validate_original_v1_human_movement_sweep_report.py")
S2=importlib.util.spec_from_file_location("reportval",P2); reportval=importlib.util.module_from_spec(S2); S2.loader.exec_module(reportval)

def sha(path): return hashlib.sha256(Path(path).read_bytes()).hexdigest()

class HumanMovementSweepReportContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.spec=specval.read(specval.SPEC); cls.plan=specval.read(specval.PLAN)

    def test_live_execution_spec_matches_all_11_sweeps(self):
        out=specval.validate(self.spec,self.plan)
        self.assertEqual(out["sweeps"],11)

    def fixture_report(self,name="trunk_flexion"):
        samples=[]
        variants=["l","r"] if name=="hip_abduction_adduction" else [None]
        for variant in variants:
            for row in self.spec["sweeps"][name]["samples"]:
                samples.append({
                  "label":row["label"],
                  "return_leg":bool(row.get("return_leg",False)),
                  "input":{k:v for k,v in row.items() if k!="label"},
                  "variant":variant,
                  "joint_state_sha256":"1"*64,
                  "snapshot_sha256":"2"*64,
                  "snapshot":{
                    "final_surface":{},"weights_only_surface":{},"corrective_contribution":{},
                    "shape_key_values":{},"joint_state":{}
                  }
                })
        cfg=self.spec["sweeps"][name]
        contact=bool(cfg.get("contact_load_required"))
        csha="a"*64
        return {
          "schema_version":1,
          "status":"READ_ONLY_GENERIC_HUMAN_MOVEMENT_SWEEP_AUDIT",
          "production_approved":False,
          "candidate":"x.blend",
          "candidate_sha256":csha,
          "candidate_sha256_before":csha,
          "candidate_sha256_after":csha,
          "runner_script_sha256":sha(reportval.RUNNER),
          "blender_version":"fixture",
          "pose_definition_sha256":sha(reportval.POSE),
          "flexion_driver_sha256":sha(reportval.FLEXION),
          "movement_plan_sha256":sha(reportval.PLAN),
          "sweep_execution_spec_sha256":sha(reportval.SPEC),
          "source_saved_or_modified":False,
          "calibration_state":"EXPERIMENTAL_UNCALIBRATED",
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
          "diagnostic_limitations":["fixture remains diagnostic-only"],
          "sweeps":{
            name:{
              "implementation_status":cfg["implementation_status"],
              "plan_evidence_ids":cfg["evidence_ids"],
              "plan_regions":cfg["regions"],
              "plan_cameras":cfg["cameras"],
              "samples":samples,
              "visual_capture_status":"NOT_IMPLEMENTED",
              "contact_load_required":contact,
              "contact_load_status":"NOT_IMPLEMENTED" if contact else "NOT_APPLICABLE",
              "engineering_review":"PENDING",
              "owner_review":"PENDING"
            }
          }
        }

    def test_uncalibrated_report_validates_structure_but_not_clearance(self):
        out=reportval.validate(self.fixture_report(),self.spec)
        self.assertEqual(out["calibration_state"],"EXPERIMENTAL_UNCALIBRATED")
        self.assertEqual(out["evidence_readiness"],"DIAGNOSTIC_ONLY_INCOMPLETE")

    def test_uncalibrated_report_cannot_claim_engineering_pass(self):
        bad=self.fixture_report(); bad["sweeps"]["trunk_flexion"]["engineering_review"]="PASS"
        with self.assertRaisesRegex(ValueError,"may not infer"):
            reportval.validate(bad,self.spec)

    def test_missing_sample_fails(self):
        bad=self.fixture_report(); bad["sweeps"]["trunk_flexion"]["samples"].pop()
        with self.assertRaisesRegex(ValueError,"sample labels differ"):
            reportval.validate(bad,self.spec)

    def test_hip_abduction_requires_both_left_and_right_variants(self):
        bad=self.fixture_report("hip_abduction_adduction")
        bad["sweeps"]["hip_abduction_adduction"]["samples"]=[
          x for x in bad["sweeps"]["hip_abduction_adduction"]["samples"] if x["variant"]!="r"
        ]
        with self.assertRaisesRegex(ValueError,"hip_abduction_adduction/r"):
            reportval.validate(bad,self.spec)

    def test_candidate_before_after_identity_must_match(self):
        bad=self.fixture_report(); bad["candidate_sha256_after"]="f"*64
        with self.assertRaisesRegex(ValueError,"before/after identity differs"):
            reportval.validate(bad,self.spec)

    def test_authority_hash_mismatch_fails(self):
        bad=self.fixture_report(); bad["runner_script_sha256"]="f"*64
        with self.assertRaisesRegex(ValueError,"differs from current reviewed authority"):
            reportval.validate(bad,self.spec)

    def test_contact_bearing_sweep_cannot_claim_missing_contact_as_na(self):
        bad=self.fixture_report("grip_release")
        bad["sweeps"]["grip_release"]["contact_load_status"]="NOT_APPLICABLE"
        with self.assertRaisesRegex(ValueError,"contact-load status"):
            reportval.validate(bad,self.spec)

    def test_execution_spec_sample_drift_fails(self):
        bad=copy.deepcopy(self.spec); bad["sweeps"]["trunk_flexion"]["samples"].pop()
        with self.assertRaisesRegex(ValueError,"sample labels differ"):
            specval.validate(bad,self.plan)

if __name__=="__main__": unittest.main()
