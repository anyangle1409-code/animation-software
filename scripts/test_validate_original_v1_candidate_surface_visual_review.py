"""Tests for candidate-bound human surface visual review."""
import copy,importlib.util
from pathlib import Path
import unittest

P=Path(__file__).with_name("validate_original_v1_candidate_surface_visual_review.py")
S=importlib.util.spec_from_file_location("surface_review",P); mod=importlib.util.module_from_spec(S); S.loader.exec_module(mod)

class CandidateSurfaceVisualReviewTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.master=mod.read(mod.MASTER); cls.human=mod.read(mod.HUMAN)

    def fixture(self):
        ids=[x["id"] for x in self.master["body_regions"]]
        human_id=self.human["entries"][0]["id"]
        rows=[]
        for rid in ids:
            rows.append({
              "id":rid,"state":"NOT_RUN","human_evidence_ids":[],
              "whole_body_evidence_refs":[],"regional_close_evidence_refs":[],
              "state_evidence":{s:[] for s in mod.REQUIRED},
              "blocking_defect_ids":[],"engineering_notes":[]
            })
        d={
          "schema_version":1,"status":"CANDIDATE_SURFACE_VISUAL_REVIEW",
          "production_approved":False,"candidate_revision":"r96","candidate_sha256":"a"*64,
          "source_branch":"fixture","scope_region_ids":[ids[0]],"required_states":list(mod.REQUIRED),
          "regions":rows,"engineering_review":"PASS","owner_review":"PENDING"
        }
        row=rows[0]; row["state"]="PASS"; row["human_evidence_ids"]=[human_id]
        row["whole_body_evidence_refs"]=["whole.png"]; row["regional_close_evidence_refs"]=["close.png"]
        for s in mod.REQUIRED: row["state_evidence"][s]=[f"{s}.png"]
        return d

    def test_complete_scoped_region_passes(self):
        out=mod.validate(self.fixture(),self.master,self.human,True)
        self.assertEqual(out["incomplete"],[])

    def test_pass_without_return_evidence_fails(self):
        bad=self.fixture(); bad["regions"][0]["state_evidence"]["return_transition"]=[]
        with self.assertRaisesRegex(ValueError,"return_transition"):
            mod.validate(bad,self.master,self.human)

    def test_pass_with_blocking_defect_fails(self):
        bad=self.fixture(); bad["regions"][0]["blocking_defect_ids"]=["WB-TEST"]
        with self.assertRaisesRegex(ValueError,"blocking visual defects"):
            mod.validate(bad,self.master,self.human)

    def test_engineering_pass_cannot_hide_unrun_scope(self):
        bad=self.fixture(); bad["scope_region_ids"].append(bad["regions"][1]["id"])
        with self.assertRaisesRegex(ValueError,"incomplete scope"):
            mod.validate(bad,self.master,self.human)

if __name__=="__main__": unittest.main()
