"""Independent checks of stored endpoints, without the probe's mapping/helpers."""
import copy
import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts/anatomy_fit'))
import hand_coordinate_integrity as audit


class HandCoordinateIntegrityTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.a, cls.c = audit.load_records()

    def test_independent_correspondences(self):
        r = audit.analyse(self.a, self.c)
        self.assertEqual((r['points'], r['exact'], r['unresolved']), (108, 98, 10))
        self.assertLess(r['translation_residual_max_mm'], 1e-5)

    def test_symmetry_and_digit_connections(self):
        r = audit.analyse(self.a, self.c)
        self.assertEqual(r['paired_bones'], 27)
        self.assertEqual(r['digit_connections'], 28)
        self.assertLess(r['mirror_max_mm'], 1e-5)
        self.assertLess(r['digit_connection_max_mm'], 0.001)
        self.assertLess(r['digit_marker_max_mm'], 0.001)

    def test_wrist_relative_geometry_is_preserved_not_accepted(self):
        r = audit.analyse(self.a, self.c)
        self.assertEqual(r['wrist_reference_points'], 36)
        self.assertLess(r['wrist_relative_residual_max_mm'], 1e-5)
        self.assertFalse(r['anatomical_acceptance'])
        self.assertFalse(r['promotion_allowed'])

    def test_mutated_endpoint_detected(self):
        c = copy.deepcopy(self.c)
        c['bones']['metacarpal_2_left']['tail_m'][2] += 0.001
        with self.assertRaisesRegex(ValueError, 'rigid translation'):
            audit.analyse(self.a, c)

    def test_mutated_marker_detected(self):
        c = copy.deepcopy(self.c)
        c['joint_markers']['digit2_mcp_left']['centre_m'][0] += 0.001
        with self.assertRaisesRegex(ValueError, 'digit marker'):
            audit.analyse(self.a, c)

    def test_nonfinite_input_rejected(self):
        a = copy.deepcopy(self.a)
        a['skeleton_input']['sides']['left']['hand']['d2_dp'][1][0] = float('nan')
        with self.assertRaisesRegex(ValueError, 'finite'):
            audit.analyse(a, self.c)

    def test_wrist_endpoint_mismatch_rejected(self):
        c = copy.deepcopy(self.c)
        c['bones']['radius_left']['tail_m'][0] += 0.1
        with self.assertRaisesRegex(ValueError, 'wrist relative'):
            audit.analyse(self.a, c)


if __name__ == '__main__':
    unittest.main()
