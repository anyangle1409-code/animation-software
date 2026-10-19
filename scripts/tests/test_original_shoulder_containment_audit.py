import sys,unittest
import math
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from original_shoulder_containment_audit import classify_hits,closed_triangle_surface
class Containment(unittest.TestCase):
 def test_inside_requires_consistent_odd_votes(self):self.assertEqual(classify_hits([[1.],[2.],[3.]],.01)['classification'],'inside')
 def test_outside_even_votes(self):self.assertEqual(classify_hits([[],[1.,2.],[]],.01)['classification'],'outside')
 def test_mixed_votes_are_not_reported_contained(self):self.assertEqual(classify_hits([[1.],[],[3.]],.01)['classification'],'ambiguous')
 def test_shared_triangle_hit_is_counted_once(self):self.assertEqual(classify_hits([[1.,1.+1e-8],[2.],[3.]],.01)['classification'],'inside')
 def test_surface_point_is_boundary_not_enclosed(self):self.assertEqual(classify_hits([[],[],[]],1e-7)['classification'],'on_skin')
 def test_nonfinite_ray_is_rejected_before_filtering(self):
  for value in (math.nan,-math.inf):
   with self.subTest(value=value),self.assertRaises(ValueError):classify_hits([[value],[value],[value]],.01)
 def test_open_surface_cannot_be_watertight(self):
  tetra=[[0,1,2],[0,3,1],[0,2,3],[1,3,2]]
  self.assertTrue(closed_triangle_surface(tetra));self.assertFalse(closed_triangle_surface(tetra[:-1]))
if __name__=='__main__':unittest.main(verbosity=2)
