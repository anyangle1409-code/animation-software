#!/usr/bin/env python3
import json,tempfile,unittest
from pathlib import Path
class ContractTests(unittest.TestCase):
 def test_templates_fail_closed(self):
  root=Path(__file__).resolve().parents[1]/"coordination"
  for name in ["MODEL_CANDIDATE_READY.template.json","MODEL_CANDIDATE_FAILURES.template.json","MODEL_CANDIDATE_PASS.template.json"]:
   x=json.loads((root/name).read_text());self.assertEqual(x["schema_version"],1)
  self.assertFalse(json.loads((root/"MODEL_CANDIDATE_PASS.template.json").read_text())["production_approved"])
  self.assertFalse(json.loads((root/"MODEL_CANDIDATE_FAILURES.template.json").read_text())["production_approved"])
if __name__=="__main__":unittest.main()
