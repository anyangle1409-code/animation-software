"""Adversarial checks for independently sourced scapular landmark geometry."""
import copy
import hashlib
import json
import pathlib
import sys
import unittest

import numpy as np

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
from anatomy_fit import scapula_landmark_model as m
from report_compare import report_differences


class ScapulaLandmarkModelTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.subjects = m.load_subjects(m.DEFAULT_SOURCE)

    def test_committed_report_is_reproducible_from_raw_source(self):
        stored = json.loads(m.DEFAULT_REPORT.read_text())
        actual = m.build_report(self.subjects, target_height_cm=stored['target_height_cm'])
        actual['source_sha256'] = hashlib.sha256(m.DEFAULT_SOURCE.read_bytes()).hexdigest()
        self.assertEqual(report_differences(stored, actual), [])

    def test_true_sheet_data_not_incorrect_dimension_metadata_is_read(self):
        self.assertEqual(len(self.subjects), 125)
        self.assertEqual(sum(s['sex'] == 'Male' for s in self.subjects), 45)
        self.assertEqual(sum(s['sex'] == 'Male' and s['height_cm'] is not None
                             for s in self.subjects), 42)

    def test_committed_source_matches_published_download(self):
        self.assertEqual(hashlib.sha256(m.DEFAULT_SOURCE.read_bytes()).hexdigest(),
                         'c8d9bd697014f350e2145d781bcf37162a9e1377a2d3c20b288c10844bb0b976')

    def test_notch_projection_and_glenoid_tubercle_definitions_remain_distinct(self):
        source = json.loads((ROOT / 'ORIGINAL_V1_WORK/anatomy/canonical_scapula_landmark_sources_v1.json').read_text())
        definitions = source['sources']['SCAPULA_3DCT_NOTCH_2022'].get('measurement_semantics', {})
        self.assertIn('projection', definitions.get('d6', ''))
        self.assertIn('projection', definitions.get('d7', ''))
        self.assertIn('tubercle', definitions.get('d1', ''))

    def test_nonfinite_stature_and_coordinates_cannot_generate_report(self):
        subjects = copy.deepcopy(self.subjects)
        subjects[0]['points_mm'][0][0] = float('nan')
        with self.assertRaises(ValueError):
            m.build_report(subjects, target_height_cm=182.)
        with self.assertRaises(ValueError):
            m.build_report(self.subjects, target_height_cm=float('nan'))

    def test_all_coordinates_and_independent_anterior_direction(self):
        for s in self.subjects:
            p = np.asarray(s['points_mm'])
            self.assertEqual(p.shape, (29, 3))
            local, frame = m.anatomical_local(p)
            self.assertTrue(np.allclose(frame.T @ frame, np.eye(3), atol=1e-10))
            self.assertAlmostEqual(np.linalg.det(frame), 1.0, places=10)
            self.assertGreater(local[16, 0] - local[15, 0], 0)  # anterior vs posterior glenoid
            self.assertLess(local[6, 1], 0)  # inferior angle below exterior acromion

    def test_rotation_translation_invariance_and_round_trip(self):
        p = np.asarray(self.subjects[0]['points_mm'])
        R = np.array([[0., -1., 0.], [1., 0., 0.], [0., 0., 1.]])
        local, frame = m.anatomical_local(p)
        moved, _ = m.anatomical_local(p @ R.T + [32., -18., 11.])
        self.assertTrue(np.allclose(local, moved, atol=1e-10))
        self.assertTrue(np.allclose(local @ frame.T + p[24], p, atol=1e-10))

    def test_reflection_is_not_silently_accepted_as_a_rotation(self):
        p = np.asarray(self.subjects[0]['points_mm']) * [-1, 1, 1]
        with self.assertRaisesRegex(ValueError, 'chirality'):
            m.anatomical_local(p)

    def test_missing_and_degenerate_geometry_rejected(self):
        p = np.asarray(self.subjects[0]['points_mm']).copy()
        p[4] = p[24]
        with self.assertRaises(ValueError):
            m.anatomical_local(p)
        p[4, 0] = np.nan
        with self.assertRaises(ValueError):
            m.anatomical_local(p)

    def test_landmark_id_join_is_independent_of_row_order(self):
        info = [['ID', 'Sym', 'FTT', 'Age', 'Sex', 'Height'],
                ['A', 'Asym', 'no', 50, 'Male', 180],
                ['B', 'Asym', 'no', 40, 'Male', 182]]
        p = self.subjects[0]['points_mm']
        flat = np.asarray(p).reshape(-1).tolist()
        rows = [[None] + [f'pts.{i}' for i in range(1, 88)], ['B'] + flat, ['A'] + flat]
        result = m.join_subjects(info, rows)
        self.assertEqual([(s['id'], s['height_cm']) for s in result], [('A', 180), ('B', 182)])
        rows[-1][0] = 'B'
        with self.assertRaisesRegex(ValueError, 'duplicate'):
            m.join_subjects(info, rows)

    def test_direct_stature_regression_not_inverse_regression(self):
        r = m.regression([170, 180, 190, 200], [60, 62, 64, 66], 182)
        self.assertAlmostEqual(r['predicted'], 62.4, places=10)
        self.assertAlmostEqual(r['slope_per_cm'], 0.2, places=10)
        with self.assertRaisesRegex(ValueError, 'extrapolation'):
            m.regression([170, 180, 190, 200], [60, 62, 64, 66], 210)
        with self.assertRaises(ValueError):
            m.regression([180, 180, 180], [60, 62, 64], 180)

    def test_report_distinguishes_acromial_points_and_health_subgroups(self):
        r = m.build_report(self.subjects, target_height_cm=182.)
        self.assertFalse(r['freeze_ready'])
        self.assertIsNone(r['unmeasured_joint_centres']['AC'])
        self.assertIsNone(r['unmeasured_joint_centres']['GH'])
        self.assertIn('asymptomatic_no_FTT_males', r['groups'])
        d = r['groups']['all_males']['distances_mm']
        self.assertAlmostEqual(d['superior_inferior_angles']['mean'], 165.14422862468552, places=8)
        self.assertNotAlmostEqual(d['medial_spine_to_exterior_acromion']['mean'],
                                  d['medial_spine_to_interior_acromion']['mean'], places=2)

    def test_left_right_templates_reflect_points_without_improper_pose_rotations(self):
        r = m.build_report(self.subjects, target_height_cm=182.)
        g = r['relative_HGPT_landmarks_mm']
        left, right = np.array(g['left']), np.array(g['right'])
        self.assertTrue(np.allclose(left, right * [-1, 1, 1], atol=1e-10))
        self.assertGreater(left[24, 0] - left[4, 0], 0)
        self.assertLess(right[24, 0] - right[4, 0], 0)
        self.assertLess(left[16, 1] - left[15, 1], 0)  # anterior is -Y
        self.assertLess(left[6, 2], 0)


if __name__ == '__main__':
    unittest.main()
