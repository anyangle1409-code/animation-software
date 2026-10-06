import copy,json,unittest
from pathlib import Path
import original_v1_shoulder_foundation_declaration as d
ROOT=Path(__file__).resolve().parents[1]
class T(unittest.TestCase):
 @classmethod
 def setUpClass(cls):cls.x=json.loads((ROOT/"ORIGINAL_V1_SHOULDER_FOUNDATION_DECLARATION_TEMPLATE.json").read_text())
 def test_template_is_intentionally_incomplete(self):
  self.assertTrue(d.validate_declaration(self.x))
 def valid(self):
  x=copy.deepcopy(self.x);x["target_revision"]="r97";x["parent"]={"revision":"r96","sha256":"a"*64,"candidate_path":"candidate.blend"}
  x["scope"]["permitted_regions"]=["shoulder","torso","arm"];x["scope"]["permitted_bones"]=["clavicle_l","clavicle_r","scapula_l","scapula_r","upperarm_l","upperarm_r","spine_02","spine_03"]
  x["scope"]["topology_intent"]="candidate-specific declaration required";x["scope"]["weight_intent"]="candidate-specific declaration required";return x
 def test_valid_fresh_descendant_contract(self):self.assertEqual(d.validate_declaration(self.valid()),[])
 def test_stale_parent_or_same_revision_fails(self):
  x=self.valid();x["target_revision"]="r96";self.assertIn("target must be newer than parent",d.validate_declaration(x))
 def test_missing_issue_or_causal_reorder_fails(self):
  x=self.valid();x["issue_ids"].pop();self.assertIn("linked shoulder issue set incomplete",d.validate_declaration(x))
  x=self.valid();x["causal_order"]=list(reversed(x["causal_order"]));self.assertIn("causal order changed",d.validate_declaration(x))
 def test_corrective_first_shortcut_fails(self):
  x=self.valid();x["scope"]["weights_only_gate_precedes_correctives"]=False;self.assertTrue(d.validate_declaration(x))
if __name__=="__main__":unittest.main()
