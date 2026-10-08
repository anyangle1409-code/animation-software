import importlib.util
from pathlib import Path
import unittest
spec=importlib.util.spec_from_file_location('identity',Path(__file__).parent/'anatomy_fit/source_identity.py')
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
class SourceIdentityTests(unittest.TestCase):
 def test_doi_url_case_and_pmid_alias_are_one_source(self):
  rows=[{'id':'a','doi':'https://doi.org/10.1002/CA.22288','pmid':'24142486'},{'id':'b','pmid':24142486},{'id':'c','doi':'10.1002/ca.22288'}]
  self.assertEqual(m.identity_groups(rows),[['a','b','c']])
 def test_transitive_bridge_and_distinct_sources(self):
  rows=[{'id':'a','doi':'10.a/a'},{'id':'b','pmid':'1'},{'id':'c','doi':'10.a/a','pmid':'1'},{'id':'d','pmid':'2'}]
  self.assertEqual(m.identity_groups(rows),[['a','b','c'],['d']])
 def test_missing_identifiers_do_not_prove_independence_or_collapse(self):
  self.assertEqual(m.identity_groups([{'id':'a'},{'id':'b','doi':None}]),[['a'],['b']])
 def test_duplicate_ids_and_bad_identifiers_rejected(self):
  for rows in [[{'id':'a'},{'id':'a'}],[{'id':'a','pmid':'NaN'}],[{'id':'a','doi':'anatomy'}]]:
   with self.assertRaises(ValueError):m.identity_groups(rows)
 def test_clavicle_misattribution_corrected_and_shared_identity_retained(self):
  import json
  root=Path(__file__).resolve().parents[1]/'ORIGINAL_V1_WORK/anatomy'
  rows=json.loads((root/'canonical_proportion_sources_v1.json').read_text())['sources']
  selected=[r for r in rows if r['id'] in ['CLAVICLE_CADAVER_3D_2013','DARUWALLA_2013_CLAVICLE_3D']]
  self.assertEqual(len(selected),2)
  for r in selected:
   self.assertTrue(r['citation'].startswith('Bernat A'))
   self.assertEqual(r['doi'],'10.1002/ca.22288')
  self.assertEqual(len(m.identity_groups(selected)),1)
if __name__=='__main__':unittest.main()
