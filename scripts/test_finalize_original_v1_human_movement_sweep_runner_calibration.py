"""Tests for controlled human-movement sweep calibration finalization."""
import copy,importlib.util,json
from pathlib import Path
import unittest

P=Path(__file__).with_name("finalize_original_v1_human_movement_sweep_runner_calibration.py")
S=importlib.util.spec_from_file_location("cal_finalize",P)
mod=importlib.util.module_from_spec(S); S.loader.exec_module(mod)

class DummyValidator:
    def validate(self,d,require_calibrated=False):
        if require_calibrated and d.get("overall_state")!="CALIBRATED":
            raise ValueError("not calibrated")
        return {"overall_state":d.get("overall_state")}

class CalibrationFinalizeTests(unittest.TestCase):
    def fixture(self):
        t=json.loads((mod.ROOT/"ORIGINAL_V1_HUMAN_MOVEMENT_SWEEP_RUNNER_CALIBRATION_TEMPLATE.json").read_text())
        t["status"]="HUMAN_MOVEMENT_SWEEP_RUNNER_CALIBRATION"
        t["overall_state"]="IN_REVIEW"
        t["engineering_review"]="PENDING"
        for row in t["adapters"]:
            row["state"]="IN_REVIEW"
            row["engineering_review_status"]="PASS"
            row["human_evidence_review_status"]="PASS"
            row["human_evidence_review_refs"]=list(row["required_human_evidence_ids"])
            row["automatic_checks"]={k:True for k in row["automatic_checks"]}
            row["calibration_notes"]=["reviewed"]
        return t

    def setUp(self):
        self.old=mod.load_validator
        mod.load_validator=lambda:DummyValidator()

    def tearDown(self):
        mod.load_validator=self.old

    def test_complete_review_promotes_all_adapters(self):
        out=mod.finalize(self.fixture())
        self.assertEqual(out["overall_state"],"CALIBRATED")
        self.assertEqual(out["engineering_review"],"PASS")
        self.assertTrue(all(x["state"]=="CALIBRATED" for x in out["adapters"]))
        self.assertEqual(out["owner_review"],"PENDING")

    def test_missing_adapter_engineering_review_blocks(self):
        bad=self.fixture(); bad["adapters"][0]["engineering_review_status"]="PENDING"
        with self.assertRaisesRegex(ValueError,"engineering review PASS"):
            mod.finalize(bad)

    def test_missing_human_evidence_refs_blocks(self):
        bad=self.fixture(); bad["adapters"][0]["human_evidence_review_refs"]=[]
        with self.assertRaisesRegex(ValueError,"missing required human-evidence"):
            mod.finalize(bad)

    def test_failed_automatic_check_blocks(self):
        bad=self.fixture(); first=next(iter(bad["adapters"][0]["automatic_checks"]))
        bad["adapters"][0]["automatic_checks"][first]=False
        with self.assertRaisesRegex(ValueError,"automatic checks"):
            mod.finalize(bad)

    def test_non_review_state_cannot_be_promoted(self):
        bad=self.fixture(); bad["overall_state"]="NOT_RUN"
        with self.assertRaisesRegex(ValueError,"overall_state must be IN_REVIEW"):
            mod.finalize(bad)

if __name__=="__main__": unittest.main()
