import importlib.util,math,unittest
from pathlib import Path
import numpy as np
spec=importlib.util.spec_from_file_location('clearance',Path(__file__).parent/'anatomy_fit/endplate_clearance.py')
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
class EndplateClearanceTests(unittest.TestCase):
 def test_parallel_plates_have_constant_gap(self):
  r=m.clearance([0,0,6],[0,0,1],[0,0,0],[0,0,1],[0,0],[25,18])
  self.assertAlmostEqual(r['minimum_projected_gap_mm'],6);self.assertTrue(r['separated_everywhere'])
 def test_centre_positive_but_edge_intersects(self):
  r=m.clearance([0,0,5],[-.4,-.4,1],[0,0,0],[0,0,1],[0,0],[10,10])
  self.assertTrue(all(5+.4*x+.4*y>0 for x,y in [(10,0),(-10,0),(0,10),(0,-10)]))
  self.assertAlmostEqual(r['minimum_projected_gap_mm'],5-math.sqrt(32))
  self.assertFalse(r['separated_everywhere'])
 def test_tangent_zero_gap_fails_strict_nonbone_space(self):
  r=m.clearance([0,0,4],[-.4,0,1],[0,0,0],[0,0,1],[0,0],[10,10])
  self.assertAlmostEqual(r['minimum_projected_gap_mm'],0);self.assertFalse(r['separated_everywhere'])
 def test_independent_dense_boundary_and_minimum_witness(self):
  r=m.clearance([1,2,11],[-.1,-.2,1],[3,4,0],[.05,.04,1],[2,3],[20,15])
  p=r['minimum_witness_xy_mm']
  gap=lambda x,y:11+.1*(x-1)+.2*(y-2)-(-.05*(x-3)-.04*(y-4))
  self.assertAlmostEqual(gap(*p),r['minimum_projected_gap_mm'])
  self.assertAlmostEqual(((p[0]-2)/20)**2+((p[1]-3)/15)**2,1)
  dense=min(gap(2+20*math.cos(a),3+15*math.sin(a)) for a in np.linspace(0,2*math.pi,10001))
  self.assertAlmostEqual(dense,r['minimum_projected_gap_mm'],places=6)
 def test_plane_normal_scale_does_not_change_clearance(self):
  args=([0,0,6],[-.1,0,1],[0,0,0],[.1,0,1],[0,0],[20,10])
  a=m.clearance(*args);b=m.clearance(args[0],[-1,0,10],args[2],[1,0,10],*args[4:])
  self.assertEqual(a,b)
 def test_invalid_nonfinite_vertical_and_bad_radius_fail(self):
  args=[[0,0,6],[0,0,1],[0,0,0],[0,0,1],[0,0],[20,10]]
  for index,value in [(0,[0,0,float('nan')]),(1,[0,0,0]),(1,[1,0,1e-12]),(3,[0,0,-1]),(5,[0,10]),(5,[20,float('inf')])]:
   bad=list(args);bad[index]=value
   with self.assertRaises(ValueError):m.clearance(*bad)
 def test_sensitivity_report_reproduces_without_selecting_geometry(self):
  import json
  spec=importlib.util.spec_from_file_location('sweep',Path(__file__).parent/'anatomy_fit/build_endplate_clearance_sensitivity.py')
  sweep=importlib.util.module_from_spec(spec);spec.loader.exec_module(sweep)
  saved=json.loads((Path(__file__).resolve().parents[1]/'ORIGINAL_V1_WORK/anatomy/canonical_endplate_clearance_sensitivity_v1.json').read_text())
  self.assertEqual(sweep.build(),saved);self.assertFalse(saved['freeze_ready'])
  cases=[c for f in saved['families'].values() for cs in f.values() for c in cs]
  self.assertEqual(len(cases),90)
  self.assertTrue(any(not c['clearance']['separated_everywhere'] for c in cases))
 def test_finite_but_overflowing_geometry_fails_closed(self):
  with self.assertRaises(ValueError):m.clearance([0,0,1e308],[0,0,1],[0,0,-1e308],[0,0,1],[0,0],[10,10])
if __name__=='__main__':unittest.main()
