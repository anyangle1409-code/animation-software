import copy,importlib.util,json,pathlib,unittest
ROOT=pathlib.Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('carpalcheck',ROOT/'scripts/validate_canonical_carpal_axes.py')
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
class CarpalAxisProjectionTests(unittest.TestCase):
 def setUp(self):self.d=json.loads(m.PATH.read_text())
 def test_source_projections_and_world_directions_agree(self):self.assertEqual(m.validate(self.d),[])
 def test_unit_mirrored_stubs_do_not_prove_alignment(self):
  for side in ['left','right']:
   for bone in self.d['HGPT_axis_unit_vectors'][side]:self.d['HGPT_axis_unit_vectors'][side][bone]=[0,0,1]
  self.assertTrue(m.validate(self.d))
 def test_palmar_sign_and_side_switch_mutations_fail(self):
  for mutation in ['palmar','side']:
   d=copy.deepcopy(self.d)
   for side in ['left','right']:
    for bone,v in d['HGPT_axis_unit_vectors'][side].items():v[1 if mutation=='palmar' else 0]*=-1
   self.assertTrue(m.validate(d))
 def test_nonfinite_and_missing_vectors_fail(self):
  self.d['HGPT_axis_unit_vectors']['left']['scaphoid'][0]=float('nan');self.assertTrue(m.validate(self.d))
  self.d=json.loads(m.PATH.read_text());del self.d['HGPT_axis_unit_vectors']['right']['hamate'];self.assertTrue(m.validate(self.d))
if __name__=='__main__':unittest.main()
