import importlib.util, json, unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('hr', ROOT / 'scripts/anatomy_fit/humerus_target_review.py')
m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
STORED = json.loads((ROOT / 'ORIGINAL_V1_WORK/anatomy/canonical_humerus_target_review_v1.json').read_text())


class HumerusReview(unittest.TestCase):
    def test_reproduces(self):
        self.assertEqual(STORED, json.loads(json.dumps(m.build())))

    def test_review_only_and_region_stays_partial(self):
        self.assertEqual(STORED['status'], 'EVIDENCE_REVIEW_NOT_SELECTED')
        self.assertIs(STORED['freeze_ready'], False)
        r = json.loads((ROOT / 'ORIGINAL_V1_WORK/anatomy/canonical_freeze_readiness_v1.json').read_text())['regions']['humerus']
        self.assertEqual(r['readiness'], 'PARTIAL')
        self.assertEqual(r['target_review'], 'canonical_humerus_target_review_v1.json')

    def test_conflict_is_reported_not_resolved(self):
        c = STORED['consistency']
        self.assertTrue(c['reading'].startswith('INCONSISTENT'))
        self.assertLess(c['implied_maximum_length_from_joint_spans_mm']['highest'], STORED['maximum_length_evidence_mm']['trotter_gleser_inverted'])
        self.assertGreater(c['implied_GH_EJC_from_trotter_gleser_mm']['lowest'], max(STORED['joint_centre_span_evidence_mm'].values()))


if __name__ == '__main__':
    unittest.main()
