"""R41 saved native surface goals, all41 benchmark samples after guards.

Uses the fresh Blender orientation/area diagnostic, not the optimizer prediction.
Run HGPT_R41_NATIVE_AREA=/path/r41_orientation.json python this_test.py.
"""
import json,os,unittest
from pathlib import Path
class SavedNativeStrain(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  report=json.loads(Path(os.environ['HGPT_R41_NATIVE_AREA']).read_text())
  cls.rows=report['area_samples']
  if len(cls.rows)!=83:raise ValueError('Expected82 native path samples plus exact130 front')
 def test_saved_marked_stretch(self):self.assertLessEqual(self.rows[25]['current']['stretch'],40)
 def test_saved_top_stretch(self):self.assertLessEqual(self.rows[40]['current']['stretch'],70)
 def test_all41_saved_benchmark_samples_have_no_crushed_triangles(self):self.assertEqual(max(x['current']['collapse'] for x in self.rows[41:82]),0)
if __name__=='__main__':unittest.main()
