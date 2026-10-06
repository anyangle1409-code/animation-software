import copy,json,unittest
from pathlib import Path
import original_v1_shoulder_foundation_readiness as r
ROOT=Path(__file__).resolve().parents[1]
def load(n):return json.loads((ROOT/n).read_text())
class T(unittest.TestCase):
 def inputs(self):
  c=load("ORIGINAL_V1_SHOULDER_ANATOMICAL_ACCEPTANCE_CONTRACT.json");l=load("ORIGINAL_V1_WHOLE_BODY_ISSUE_LEDGER.json");h=load("ORIGINAL_V1_HUMAN_EVIDENCE_MANIFEST.json");d=load("ORIGINAL_V1_SHOULDER_FOUNDATION_DECLARATION_TEMPLATE.json")
  d["target_revision"]="r97";d["parent"]={"revision":"r96","sha256":"a"*64,"candidate_path":"candidate.blend"};d["scope"]["permitted_regions"]=["shoulder","torso","arm"];d["scope"]["permitted_bones"]=["clavicle_l","clavicle_r","scapula_l","scapula_r","upperarm_l","upperarm_r","spine_02","spine_03"];d["scope"]["topology_intent"]="declared";d["scope"]["weight_intent"]="declared";return c,d,l,h
 def test_valid_infrastructure_allows_blender_edit(self):
  x=r.assess(*self.inputs());self.assertTrue(x["ready"],x["errors"]);self.assertEqual(x["next"],"BLENDER_FOUNDATION_EDIT_ALLOWED")
 def test_incomplete_template_fails_closed(self):
  c,d,l,h=self.inputs();d["parent"]["sha256"]=None;self.assertFalse(r.assess(c,d,l,h)["ready"])
 def test_missing_human_evidence_fails(self):
  c,d,l,h=self.inputs();h["entries"]=[];self.assertFalse(r.assess(c,d,l,h)["ready"])
 def test_premature_issue_closure_fails_pre_edit(self):
  c,d,l,h=self.inputs();l=copy.deepcopy(l);next(x for x in l["issues"] if x["id"]=="WB-AX-001")["state"]="Fixed";self.assertFalse(r.assess(c,d,l,h)["ready"])
if __name__=="__main__":unittest.main()
