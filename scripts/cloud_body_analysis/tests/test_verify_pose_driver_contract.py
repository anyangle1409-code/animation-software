"""Standard-library proof that actual-driver analysis is not anatomical approval."""
import copy
import importlib.util
from pathlib import Path
import unittest

MODULE = Path(__file__).resolve().parents[1] / "verify_pose_driver_contract.py"
SPEC = importlib.util.spec_from_file_location("verify_pose_driver_contract", MODULE)
mod = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(mod)

def fixtures():
    families=[]
    for f in sorted(mod.FAMILIES):
        for side in ("l","r"):
            families.append({
                "family":f,"side_suffix":side,"safe_to_evaluate_rule":True,
                "measurement":"humerothoracic_elevation",
                "effective_start_deg":90.0,
                "angle_properties_deg":[110.0,130.0,160.0],
                "keys":[{"name":f+"_"+side+"_"+str(angle)} for angle in (110,130,160)],
            })
    static={
        "model":"W8","source_sha256":mod.W8,
        "original_source_unchanged":True,
        "status":"READ_ONLY_ANGULAR_ACTIVATION_CONTRACT_NOT_APPLIED_TO_POSE",
        "family_records":families,
    }
    samples=[]
    for i in range(9):
        row={"sample":i,"authored_press_ht_target_deg_NOT_measured":90+8*i,
             "sides":{},"actual_native_deformation_metrics":{**mod.BASELINE.get(i,mod.BASELINE[0])}}
        for side in ("l","r"):
            measured=90+8*i
            keys=[]
            for family in families:
                if family["side_suffix"]!=side:continue
                for index,key in enumerate(family["keys"]):
                    keys.append({"name":key["name"],
                                 "actual_value":round(mod.value_hat(measured,90,[110,130,160],index),6)})
            row["sides"][side]={
                "humerothoracic_elevation_measured_by_pinned_driver_deg":measured,
                "actual_shape_key_values":keys,
            }
        samples.append(row)
    dynamic={
        "status":"READ_ONLY_IN_MEMORY_POSE_STATE_ANATOMY_NOT_APPROVED",
        "model":"W8","source_sha256":mod.W8,
        "saved_blend":False,"source_unchanged":True,
        "anatomical_approval":"NOT_GRANTED",
        "quality_approval":"NOT_GRANTED",
        "samples":samples,
    }
    return static,dynamic

class DriverConsistencyTests(unittest.TestCase):
    def test_nine_frames_378_keys_and_not_anatomical_approval(self):
        static,dynamic=fixtures()
        report=mod.compare(static,dynamic)
        self.assertEqual(report["actual_compared_shape_key_values"],378)
        self.assertTrue(report["all_measured_driver_hats_match"])
        self.assertFalse(report["shoulder_surface_deformation_approved"])
        self.assertFalse(report["joint_coordinate_ISB_verified"])
        self.assertTrue(report["failing_baseline_metrics_unchanged"])

    def test_reject_tampered_actual_shape_key(self):
        static,dynamic=fixtures()
        dynamic["samples"][6]["sides"]["l"]["actual_shape_key_values"][0]["actual_value"]=0.7
        with self.assertRaisesRegex(ValueError,"do NOT match"):
            mod.compare(static,dynamic)

    def test_reject_unordered_samples(self):
        static,dynamic=fixtures()
        dynamic["samples"][0]["sample"]=8
        with self.assertRaisesRegex(ValueError,"missing or unordered"):
            mod.compare(static,dynamic)

    def test_reject_missing_key(self):
        static,dynamic=fixtures()
        dynamic["samples"][8]["sides"]["r"]["actual_shape_key_values"].pop()
        with self.assertRaisesRegex(ValueError,"missing actual key"):
            mod.compare(static,dynamic)

    def test_reject_baseline_deformation_rewrite(self):
        static,dynamic=fixtures()
        dynamic["samples"][6]["actual_native_deformation_metrics"]["stretch_gt_2"]=0
        with self.assertRaisesRegex(ValueError,"pinned failing deformation"):
            mod.compare(static,dynamic)

    def test_reject_unverified_static_source(self):
        static,dynamic=fixtures()
        static["original_source_unchanged"]=False
        with self.assertRaisesRegex(ValueError,"unverified W8"):
            mod.compare(static,dynamic)

    def test_reject_false_dynamic_anatomical_approval(self):
        static,dynamic=fixtures()
        dynamic["anatomical_approval"]="APPROVED"
        with self.assertRaisesRegex(ValueError,"unverified or promoted"):
            mod.compare(static,dynamic)

    def test_nonfinite_and_nonmonotone_angles(self):
        with self.assertRaisesRegex(ValueError,"nonfinite"):
            mod.value_hat(float("nan"),90,[120],0)
        with self.assertRaisesRegex(ValueError,"nonmonotonic"):
            mod.value_hat(100,90,[80,120],0)

    def test_start_and_terminal_key_behaviour(self):
        self.assertEqual(mod.value_hat(90,95,[110,120],0),0)
        self.assertEqual(mod.value_hat(110,95,[110,120],0),1)
        self.assertEqual(mod.value_hat(120,95,[110,120],0),0)
        self.assertEqual(mod.value_hat(160,95,[110,120],1),1)

if __name__=="__main__":
    unittest.main()
