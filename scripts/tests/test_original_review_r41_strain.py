"""New R41 goals, fixed before implementation; do not replace prior tests."""
import json,os,unittest
from pathlib import Path
class StrainGoals(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  d=Path(os.environ['HGPT_STRAIN_CANDIDATE']);tag=os.environ.get('HGPT_STRAIN_TAG','r41')
  cls.press=json.loads((d/f'{tag}_press.json').read_text())['press'];cls.bench=json.loads((d/f'{tag}_benchmarks.json').read_text())['benchmarks']['shoulder_press']['frames']
 def test_marked_press_stretch_reduced(self):self.assertLessEqual(self.press[25]['stretch'],40)
 def test_top_press_stretch_reduced(self):self.assertLessEqual(self.press[40]['stretch'],70)
 def test_shoulder_benchmark_has_no_crushed_triangles(self):self.assertEqual(max(f['collapse_lt_0_1'] for f in self.bench),0)
if __name__=='__main__':unittest.main()
