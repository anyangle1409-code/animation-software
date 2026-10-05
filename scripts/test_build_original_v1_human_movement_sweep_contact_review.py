"""Tests for human movement sweep contact-review scaffold builder."""
import hashlib,importlib.util,json,tempfile
from pathlib import Path
import unittest

P=Path(__file__).with_name("build_original_v1_human_movement_sweep_contact_review.py")
S=importlib.util.spec_from_file_location("contact_review_builder",P); mod=importlib.util.module_from_spec(S); S.loader.exec_module(mod)

RV_PATH=Path(__file__).with_name("validate_original_v1_human_movement_sweep_contact_raw.py")
RS=importlib.util.spec_from_file_location("raw_contact_validator",RV_PATH); rv=importlib.util.module_from_spec(RS); RS.loader.exec_module(rv)

class SweepContactReviewBuilderTests(unittest.TestCase):
    def raw_fixture(self,sweep="loaded_hip_hinge"):
        req=rv.read(rv.REQ); spec=rv.read(rv.SPEC); csha="a"*64
        d={
          "schema_version":1,"status":"READ_ONLY_HUMAN_MOVEMENT_SWEEP_CONTACT_RAW",
          "production_approved":False,"candidate_revision":"r96","candidate_sha256":csha,
          "candidate_sha256_before":csha,"candidate_sha256_after":csha,
          "sweep_id":sweep,
          "runner_script_sha256":hashlib.sha256(rv.RUNNER.read_bytes()).hexdigest(),
          "capture_script_sha256":hashlib.sha256(rv.CAPTURE.read_bytes()).hexdigest(),
          "contact_requirements_sha256":hashlib.sha256(rv.REQ.read_bytes()).hexdigest(),
          "blender_version":"5.2.1","source_saved_or_modified":False,
          "classification_state":"RAW_MEASUREMENTS_ONLY",
          "engineering_review":"PENDING","owner_review":"PENDING","samples":[]
        }
        for row in spec["sweeps"][sweep]["samples"]:
            authority=req["sweeps"][sweep]["samples"][row["label"]]
            domains={}
            for domain in req["sweeps"][sweep]["domains"]:
                domains[domain]={"fixture":True}
            d["samples"].append({
              "label":row["label"],
              "input":{k:v for k,v in row.items() if k!="label"},
              "return_leg":bool(row.get("return_leg",False)),
              "joint_state_sha256":"b"*64,
              "domains":domains
            })
        return d

    def test_builds_unclassified_review_scaffold(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td); raw=root/"raw.json"; out=root/"review.json"
            raw.write_text(json.dumps(self.raw_fixture()),encoding="utf-8")
            result=mod.build(raw,out)
            self.assertEqual(result["engineering_review"],"PENDING")
            self.assertTrue(out.is_file())
            for sample in result["samples"]:
                for rec in sample["domains"].values():
                    self.assertEqual(rec["classification"],"UNCLASSIFIED")
                    self.assertTrue(rec["raw_measurement_ref"])
                    self.assertEqual(rec["evidence_note"],"")

    def test_builder_preserves_candidate_and_sweep_identity(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td); raw=root/"raw.json"; out=root/"review.json"
            fixture=self.raw_fixture(); raw.write_text(json.dumps(fixture),encoding="utf-8")
            result=mod.build(raw,out)
            self.assertEqual(result["candidate_sha256"],fixture["candidate_sha256"])
            self.assertEqual(result["sweep_id"],fixture["sweep_id"])

    def test_invalid_raw_contact_is_rejected(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td); raw=root/"raw.json"; out=root/"review.json"
            fixture=self.raw_fixture(); fixture["candidate_sha256_after"]="c"*64
            raw.write_text(json.dumps(fixture),encoding="utf-8")
            with self.assertRaisesRegex(ValueError,"candidate before/after"):
                mod.build(raw,out)

if __name__=="__main__": unittest.main()
