"""Tests for raw read-only human movement sweep contact measurements."""
import copy,hashlib,importlib.util
from pathlib import Path
import unittest
P=Path(__file__).with_name("validate_original_v1_human_movement_sweep_contact_raw.py")
S=importlib.util.spec_from_file_location("raw_contact",P); mod=importlib.util.module_from_spec(S); S.loader.exec_module(mod)
class RawSweepContactTests(unittest.TestCase):
    def fixture(self,sweep="loaded_hip_hinge"):
        req=mod.read(mod.REQ)["sweeps"][sweep]; spec=mod.read(mod.SPEC)["sweeps"][sweep]; csha="a"*64
        by={x["label"]:x for x in spec["samples"]}
        rows=[]
        for label,ar in req["samples"].items():
            domains={domain:{"vertex_count":4,"z_to_floor_m":{"count":4,"min_m":0.0}} for domain in req.get("domains",[])}
            sample=by[label]
            rows.append({
              "label":label,
              "input":{k:v for k,v in sample.items() if k!="label"},
              "return_leg":bool(sample.get("return_leg",False)),
              "joint_state_sha256":"b"*64,
              "domains":domains
            })
        return {
          "schema_version":1,"status":"READ_ONLY_HUMAN_MOVEMENT_SWEEP_CONTACT_RAW","production_approved":False,
          "candidate_revision":"r96","candidate_sha256":csha,"candidate_sha256_before":csha,"candidate_sha256_after":csha,
          "runner_script_sha256":hashlib.sha256(mod.RUNNER.read_bytes()).hexdigest(),
          "capture_script_sha256":hashlib.sha256(mod.CAPTURE.read_bytes()).hexdigest(),
          "contact_requirements_sha256":hashlib.sha256(mod.REQ.read_bytes()).hexdigest(),
          "source_saved_or_modified":False,"classification_state":"RAW_MEASUREMENTS_ONLY",
          "engineering_review":"PENDING","owner_review":"PENDING","sweep_id":sweep,"samples":rows
        }
    def test_complete_raw_loaded_hinge_measurements_pass(self):
        out=mod.validate(self.fixture()); self.assertEqual(out["status"],"PASS")
    def test_candidate_rehash_difference_fails(self):
        bad=self.fixture(); bad["candidate_sha256_after"]="c"*64
        with self.assertRaisesRegex(ValueError,"before/after identity differs"): mod.validate(bad)
    def test_raw_capture_cannot_claim_classification(self):
        bad=self.fixture(); bad["classification_state"]="PASS"
        with self.assertRaisesRegex(ValueError,"may not claim classification"): mod.validate(bad)
    def test_missing_required_domain_fails(self):
        bad=self.fixture(); bad["samples"][0]["domains"].pop("left_foot_to_floor")
        with self.assertRaisesRegex(ValueError,"domains incomplete|required raw domain missing"): mod.validate(bad)
if __name__=="__main__": unittest.main()
