import unittest,sys
from pathlib import Path
import numpy as np
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from original_review_r41_checks import sentinels_preserved,front_comparison

class FinalGuardTests(unittest.TestCase):
    def test_changed_s7_sentinel_is_rejected(self):
        before={'key130':np.zeros((2,3)),'key136':np.ones((2,3))};after={k:v.copy() for k,v in before.items()}
        self.assertTrue(sentinels_preserved(before,after))
        after['key136'][0,1]+=.001
        self.assertFalse(sentinels_preserved(before,after))
    def test_missing_sentinel_key_is_rejected(self):
        self.assertFalse(sentinels_preserved({'key':np.zeros((2,3))},{}))
    def test_front_worsening_is_explicit(self):
        old='FRONT_EDGE_130 23\nFRONT_TARGET_FIT 120.0 .08\nFRONT_TARGET_FIT 145.0 .09\n'
        new='FRONT_EDGE_130 30\nFRONT_TARGET_FIT 120.0 .10\nFRONT_TARGET_FIT 145.0 .09\n'
        result=front_comparison(old,new)
        self.assertEqual(result.get('edge_change_degrees'),7.)
        self.assertEqual(result.get('worsened'),['edge_130','sentinel_120'])
    def test_missing_front_metric_cannot_become_zero(self):
        with self.assertRaises(ValueError):front_comparison('','')
    def test_unittest_progress_prefix_preserves_real_front_values(self):
        log='FRONT_EDGE_130 23\n.FRONT_TARGET_FIT 120.0 .08\nFRONT_TARGET_FIT 145.0 .09\n'
        self.assertEqual(front_comparison(log,log)['worsened'],[])

if __name__=='__main__':unittest.main()
