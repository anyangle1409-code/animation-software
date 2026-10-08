import importlib.util, json, unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('sr', ROOT / 'scripts/anatomy_fit/sternum_target_review.py')
m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
STORED = json.loads((ROOT / 'ORIGINAL_V1_WORK/anatomy/canonical_sternum_target_review_v1.json').read_text())


class SternumReview(unittest.TestCase):
    def test_reproduces(self):
        self.assertEqual(STORED, json.loads(json.dumps(m.build())))

    def test_review_only(self):
        self.assertEqual(STORED['status'], 'EVIDENCE_REVIEW_NOT_SELECTED')
        self.assertIs(STORED['freeze_ready'], False)
        r = json.loads((ROOT / 'ORIGINAL_V1_WORK/anatomy/canonical_freeze_readiness_v1.json').read_text())['regions']['ribs']
        self.assertEqual(r['readiness'], 'BLOCKED')
        self.assertEqual(r['sternum_target_review'], 'canonical_sternum_target_review_v1.json')

    def test_specimen_obeys_topology_and_a003_does_not(self):
        sp = STORED['specimen_layout_grade_D']
        self.assertLess(abs(sp['costal_attachment_depth_mm']['2'] - sp['manubriosternal_depth_mm']), 2.0)
        self.assertLess(sp['costal_attachment_depth_mm']['1'], sp['manubriosternal_depth_mm'])
        a = STORED['a003']
        self.assertGreater(abs(a['sternocostal_depth_mm']['2'] - a['manubriosternal_depth_mm']), 30)
        self.assertGreater(a['stick_vs_total_with_xiphoid_z'], 3)


if __name__ == '__main__':
    unittest.main()
