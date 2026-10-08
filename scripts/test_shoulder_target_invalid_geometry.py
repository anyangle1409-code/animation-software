import sys,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).parent))
from anatomy_fit import shoulder_target_constraints as m
class ShoulderInvalidGeometryTests(unittest.TestCase):
 def test_infinite_curve_or_invalid_endpoints_cannot_pass(self):
  for length in [float('inf'),float('nan'),-1,0]:
   self.assertFalse(m.endpoint_chord_is_anatomically_possible([0,0,0],[150,0,0],length))
  for point in [[float('nan'),0,0],[float('inf'),0,0],[1,2]]:
   self.assertFalse(m.endpoint_chord_is_anatomically_possible([0,0,0],point,166.8))
 def test_collapsed_chord_cannot_pass(self):
  self.assertFalse(m.endpoint_chord_is_anatomically_possible([0,0,0],[0,0,0],166.8))
 def test_nonfinite_or_boolean_measurements_fail_closed(self):
  for v in [float('nan'),float('inf'),True]:
   for call in [lambda:m.bilateral_ac_breadth_from_transverse_offset(v,30),lambda:m.chord_length_mm([0,0,0],[v,0,0]),lambda:m.minimum_bilateral_sc_breadth_for_lateral_only_chord(360,v),lambda:m.a003_outer_breadth_failure(v,425)]:
    with self.assertRaises(ValueError):call()
if __name__=='__main__':unittest.main()
