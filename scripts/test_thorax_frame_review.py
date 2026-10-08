import importlib.util, json, unittest
from pathlib import Path

from report_compare import report_differences

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('tf', ROOT / 'scripts/anatomy_fit/thorax_frame_review.py')
m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
STORED = json.loads((ROOT / 'ORIGINAL_V1_WORK/anatomy/canonical_thorax_frame_182_review_v1.json').read_text())


class ThoraxFrameReview(unittest.TestCase):
    def test_reproduces_from_committed_sources(self):
        self.assertEqual(report_differences(STORED, json.loads(json.dumps(m.build()))), [])

    def test_review_only_and_shoulder_stays_partial(self):
        self.assertEqual(STORED['status'], 'REVIEW_PROVISIONAL_NOT_SELECTED')
        self.assertIs(STORED['freeze_ready'], False)
        r = json.loads((ROOT / 'ORIGINAL_V1_WORK/anatomy/canonical_freeze_readiness_v1.json').read_text())['regions']['shoulder_girdle']
        self.assertEqual(r['readiness'], 'PARTIAL')
        self.assertEqual(r['thorax_frame_review'], 'canonical_thorax_frame_182_review_v1.json')

    def test_pitch_conflict_reported_and_sc_dominated_by_ij(self):
        c = STORED['thorax_pitch_conflict']
        self.assertGreater(c['living_ANSUR_C7_above_IJ_mm'] - c['bodyparts3d_specimen_C7_above_IJ_mm'], 30)
        span = STORED['SC_relative_to_IJ']['SC_height_above_IJ_vs_thorax_pitch_mm'].values()
        self.assertLess(max(span) - min(span), STORED['ansur_standing_anchors_at_182_mm']['suprasternaleheight']['residual_sd'])
        self.assertGreater(STORED['a003']['IJ_z'], 2)


if __name__ == '__main__':
    unittest.main()
