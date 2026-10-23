import importlib.util
from pathlib import Path
import unittest,os
class Flags(unittest.TestCase):
 def module(self):
  p=Path(os.environ['DIAG_DIR'])/'triangle_flags.py'
  self.assertTrue(p.exists(),'Missing diagnostic classifier')
  s=importlib.util.spec_from_file_location('flags',p);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
 def test_exact_thresholds_and_degenerate_rest_are_preserved(self):
  m=self.module();f=[(0,1,2),(3,4,5),(6,7,8),(9,10,11),(12,13,14)]
  r=m.flag_triangles(f,[1,1,1,1,0],[.099,.1,2,2.001,4],[])
  self.assertEqual(r['collapsed'],[0]);self.assertEqual(r['stretched'],[3])
 def test_shared_vertex_pairs_and_duplicate_reverse_are_not_defects(self):
  m=self.module();f=[(0,1,2),(2,3,4),(5,6,7)]
  r=m.flag_triangles(f,[1]*3,[1]*3,[(0,1),(1,0),(0,2),(2,0),(0,0)])
  self.assertEqual(r['intersections'],[(0,2)])
 def test_unstable_lengths_fail_instead_of_truncating(self):
  m=self.module()
  with self.assertRaises(ValueError):m.flag_triangles([(0,1,2)],[1],[],[])
 def test_reproduction_rejects_same_counts_with_changed_volume_or_missing_frame(self):
  m=self.module();self.assertTrue(hasattr(m,'compare_rows'),'Missing complete baseline comparison')
  a=[{'collapse_lt_0_1':0,'body_volume_change_pct':1.0,'t':0}]
  self.assertEqual(m.compare_rows(a,a),[])
  self.assertTrue(m.compare_rows(a,[{'collapse_lt_0_1':0,'body_volume_change_pct':2.0,'t':0}]))
  self.assertTrue(m.compare_rows(a,[]))
if __name__=='__main__':unittest.main()
