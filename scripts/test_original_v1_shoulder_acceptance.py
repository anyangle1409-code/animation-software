"""Tests for fail-closed ORIGINAL-v1 shoulder anatomical acceptance."""
import copy, json, unittest
from pathlib import Path
import original_v1_shoulder_acceptance as sa
ROOT=Path(__file__).resolve().parents[1]

class ShoulderAcceptanceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.contract=json.loads((ROOT/"ORIGINAL_V1_SHOULDER_ANATOMICAL_ACCEPTANCE_CONTRACT.json").read_text(encoding="utf-8"))
    def valid_review(self):
        return {
          "schema_version":1,"candidate_revision":"r97","candidate_sha256":"a"*64,"parent_sha256":"b"*64,
          "machine_gates":[{"id":x["id"],"pass":True} for x in self.contract["machine_reject_gates"]],
          "visual_gates":[{"id":x["id"],"pass":True,"evidence_paths":["evidence/render.png"],"review_note":"Reviewed against bound human evidence."} for x in self.contract["mandatory_visual_reject_gates"]],
          "weights_only_foundation_pass":True,"movement_matrix_complete":True,
          "human_anatomical_review_recorded":True,"open_critical_high_linked_issues":[],
          "residual_corrective_fitted":False
        }
    def test_live_contract_is_valid(self):self.assertEqual(sa.validate_contract(self.contract),[])
    def test_complete_review_can_pass_but_never_production_approve(self):
        r=sa.evaluate(self.contract,self.valid_review());self.assertTrue(r["pass"]);self.assertFalse(r["production_approved"])
    def test_missing_machine_gate_fails_closed(self):
        x=self.valid_review();x["machine_gates"].pop();r=sa.evaluate(self.contract,x);self.assertFalse(r["pass"]);self.assertTrue(r["missing_machine_gates"])
    def test_visible_failure_overrides_green_machine_results(self):
        x=self.valid_review();x["visual_gates"][0]["pass"]=False;r=sa.evaluate(self.contract,x);self.assertFalse(r["pass"]);self.assertIn("SH-V01",r["failed_visual_gates"])
    def test_visual_pass_requires_evidence_and_note(self):
        x=self.valid_review();x["visual_gates"][0]["evidence_paths"]=[];self.assertFalse(sa.evaluate(self.contract,x)["pass"])
    def test_corrective_before_weights_only_pass_is_causal_violation(self):
        x=self.valid_review();x["weights_only_foundation_pass"]=False;x["residual_corrective_fitted"]=True
        r=sa.evaluate(self.contract,x);self.assertFalse(r["pass"]);self.assertTrue(r["causal_order_violation"])
    def test_open_linked_issue_blocks(self):
        x=self.valid_review();x["open_critical_high_linked_issues"]=["WB-AX-001"];self.assertFalse(sa.evaluate(self.contract,x)["pass"])
    def test_incomplete_movement_matrix_blocks(self):
        x=self.valid_review();x["movement_matrix_complete"]=False;self.assertFalse(sa.evaluate(self.contract,x)["pass"])
if __name__=="__main__":unittest.main()
