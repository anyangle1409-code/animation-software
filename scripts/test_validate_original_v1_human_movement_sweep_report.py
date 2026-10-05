"""Tests for generic human movement sweep execution spec/report contracts."""
import copy,importlib.util
from pathlib import Path
import unittest

P1=Path(__file__).with_name("validate_original_v1_human_movement_sweep_execution_spec.py")
S1=importlib.util.spec_from_file_location("specval",P1); specval=importlib.util.module_from_spec(S1); S1.loader.exec_module(specval)
P2=Path(__file__).with_name("validate_original_v1_human_movement_sweep_report.py")
S2=importlib.util.spec_from_file_location("reportval",P2); reportval=importlib.util.module_from_spec(S2); S2.loader.exec_module(reportval)

class HumanMovementSweepReportContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.spec=specval.read(specval.SPEC); cls.plan=specval.read(specval.PLAN)

    def test_live_execution_spec_matches_all_11_sweeps(self):
        out=specval.validate(self.spec,self.plan)
        self.assertEqual(out["sweeps"],11)

    def fixture_report(self,name="trunk_flexion"):
        samples=[]
        for row in self.spec["sweeps"][name]["samples"]:
            variants=["l","r"] if name=="hip_abduction_adduction" else [None]
            for variant in variants:
                samples.append({
                  "label":row["label"],"return_leg":bool(row.get("return_leg",False)),
                  "input":{},"variant":variant,
                  "snapshot":{"final_surface":{},"weights_only_surface":{},"corrective_contribution":{},"shape_key_values":{},"joint_state":{}}
                })
        return {
          "schema_version":1,"status":"READ_ONLY_GENERIC_HUMAN_MOVEMENT_SWEEP_AUDIT","production_approved":False,
          "candidate":"x.blend","candidate_sha256":"a"*64,"pose_definition_sha256":"b"*64,
          "flexion_driver_sha256":"c"*64,"movement_plan_sha256":"d"*64,"sweep_execution_spec_sha256":"e"*64,
          "source_saved_or_modified":False,"calibration_state":"EXPERIMENTAL_UNCALIBRATED",
          "sweeps":{name:{"samples":samples,"engineering_review":"PENDING","owner_review":"PENDING"}}
        }

    def test_uncalibrated_report_validates_structure_but_not_clearance(self):
        out=reportval.validate(self.fixture_report(),self.spec)
        self.assertEqual(out["calibration_state"],"EXPERIMENTAL_UNCALIBRATED")

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

    def test_execution_spec_sample_drift_fails(self):
        bad=copy.deepcopy(self.spec); bad["sweeps"]["trunk_flexion"]["samples"].pop()
        with self.assertRaisesRegex(ValueError,"sample labels differ"):
            specval.validate(bad,self.plan)

if __name__=="__main__": unittest.main()
