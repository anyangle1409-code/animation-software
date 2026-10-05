"""Tests for fail-closed human movement sweep acceptance."""
import copy,importlib.util,json,tempfile
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
        cal=self.write(root,"cal.json",{"overall_state":"CALIBRATED","engineering_review":"PASS"})
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
            (root/d["runner_calibration_record_path"]).write_text(json.dumps({"overall_state":"NOT_RUN","engineering_review":"PENDING"}),encoding="utf-8")
            with self.assertRaisesRegex(ValueError,"CALIBRATED"):
                mod.validate(d,root,True)

if __name__=="__main__": unittest.main()
