"""Tests for controlled human-movement sweep acceptance finalization."""
import importlib.util,json,tempfile
from pathlib import Path
import unittest

P=Path(__file__).with_name("finalize_original_v1_human_movement_sweep_acceptance.py")
S=importlib.util.spec_from_file_location("sweep_accept_finalize",P)
mod=importlib.util.module_from_spec(S); S.loader.exec_module(mod)

class DummyValidator:
    def validate(self,d,base,require_pass=False):
        if require_pass and d.get("engineering_review")!="PASS":
            raise ValueError("engineering PASS required")
        return {"sweep_id":d.get("sweep_id"),"candidate_sha256":d.get("candidate_sha256")}

class SweepAcceptanceFinalizeTests(unittest.TestCase):
    def setUp(self):
        self.old=mod.load_validator
        mod.load_validator=lambda:DummyValidator()

    def tearDown(self):
        mod.load_validator=self.old

    def write(self,root,name,obj):
        p=root/name; p.write_text(json.dumps(obj),encoding="utf-8"); return name

    def fixture(self,root,sweep="trunk_flexion"):
        visual=self.write(root,"visual.json",{"engineering_review":"PASS"})
        motion=self.write(root,"motion.json",{
          "continuity_review":"PASS","reversibility_review":"PASS","engineering_review":"PASS"
        })
        contact=None
        if sweep in mod.CONTACT_BEARING:
            contact=self.write(root,"contact.json",{"engineering_review":"PASS"})
        return {
          "schema_version":1,"status":"HUMAN_MOVEMENT_SWEEP_ACCEPTANCE","production_approved":False,
          "candidate_revision":"r96","candidate_sha256":"a"*64,"sweep_id":sweep,
          "raw_sweep_report_path":"raw.json","runner_calibration_record_path":"cal.json",
          "visual_capture_manifest_path":visual,"contact_report_path":contact,
          "motion_continuity_evidence_path":motion,"motion_reversibility_evidence_path":motion,
          "required_human_evidence_ids":["HE-X"],"human_evidence_review_refs":["HE-X"],
          "continuity_review_status":"PENDING","reversibility_review_status":"PENDING",
          "visual_review_status":"PENDING",
          "contact_review_status":"PENDING" if sweep in mod.CONTACT_BEARING else "NOT_APPLICABLE",
          "engineering_review":"PENDING","owner_review":"PENDING"
        }

    def test_non_contact_review_promotes_to_engineering_pass(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td); out=mod.finalize(self.fixture(root),root)
            self.assertEqual(out["engineering_review"],"PASS")
            self.assertEqual(out["visual_review_status"],"PASS")
            self.assertEqual(out["continuity_review_status"],"PASS")
            self.assertEqual(out["reversibility_review_status"],"PASS")
            self.assertEqual(out["contact_review_status"],"NOT_APPLICABLE")
            self.assertEqual(out["owner_review"],"PENDING")

    def test_missing_human_evidence_blocks(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td); bad=self.fixture(root); bad["human_evidence_review_refs"]=[]
            with self.assertRaisesRegex(ValueError,"missing required human-evidence"):
                mod.finalize(bad,root)

    def test_visual_review_must_be_pass(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td); bad=self.fixture(root)
            (root/"visual.json").write_text(json.dumps({"engineering_review":"PENDING"}),encoding="utf-8")
            with self.assertRaisesRegex(ValueError,"visual capture engineering review PASS"):
                mod.finalize(bad,root)

    def test_motion_continuity_must_be_pass(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td); bad=self.fixture(root)
            (root/"motion.json").write_text(json.dumps({
              "continuity_review":"FAIL","reversibility_review":"PASS","engineering_review":"PASS"
            }),encoding="utf-8")
            with self.assertRaisesRegex(ValueError,"motion continuity review PASS"):
                mod.finalize(bad,root)

    def test_contact_bearing_sweep_requires_contact_report(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td); bad=self.fixture(root,"grip_release"); bad["contact_report_path"]=None
            with self.assertRaisesRegex(ValueError,"requires contact report"):
                mod.finalize(bad,root)

    def test_contact_bearing_sweep_promotes_contact_status(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td); out=mod.finalize(self.fixture(root,"ankle_plantarflexion"),root)
            self.assertEqual(out["contact_review_status"],"PASS")
            self.assertEqual(out["engineering_review"],"PASS")

if __name__=="__main__": unittest.main()
