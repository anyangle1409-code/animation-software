"""P007 read-only unconstrained sternum rotation+translation fit checks."""
import copy
import json
import math
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent / 'anatomy_fit'))
import p007_sternum_rigid_fit_audit as p7
import p006_sternocostal_translation_feasibility as p6
import replay_p004_coupled_thorax as p4
import replay_p005_shoulder_chain as p5


P = [[0.03, 0.01, 0.03], [-0.04, 0.02, 0.08],
     [0.01, -0.03, -0.05], [0.07, 0.02, -0.06],
     [-0.01, -0.08, 0.04], [0.04, 0.05, 0.02]]


def moved(R, t):
    return [p7._add(p7._matvec(R, x), t) for x in P]


class PureHornAndJacobi(unittest.TestCase):
    def test_identity_fit_exact(self):
        r = p7.rigid_fit(P, P)
        self.assertLess(max(r['residuals_m']), 1e-10)
        self.assertAlmostEqual(r['angle_deg'], 0, places=7)

    def test_pure_translation_fits_exactly(self):
        t = [0.01, -0.025, .038]
        Q = [p7._add(x, t) for x in P]
        r = p7.rigid_fit(P, Q)
        self.assertLess(max(r['residuals_m']), 1e-9)
        self.assertAlmostEqual(r['angle_deg'], 0, places=6)

    def test_rotation_z_60_and_translation_fits_exactly(self):
        a = math.pi/3
        c,s = math.cos(a), math.sin(a)
        R = [[c,-s,0],[s,c,0],[0,0,1]]
        t = [0.02,-0.03,0.01]
        r = p7.rigid_fit(P, moved(R, t))
        self.assertLess(max(r['residuals_m']), 1e-8)
        self.assertAlmostEqual(r['angle_deg'], 60, places=5)

    def test_rotation_x_minus_25_and_translation_fits_exactly(self):
        a = -25*math.pi/180
        c,s = math.cos(a), math.sin(a)
        R = [[1,0,0],[0,c,-s],[0,s,c]]
        r = p7.rigid_fit(P, moved(R, [-.01,.025,-.035]))
        self.assertLess(max(r['residuals_m']), 1e-8)
        self.assertAlmostEqual(r['angle_deg'], 25, places=5)

    def test_rotation_matrix_is_proper_not_reflection(self):
        a = math.pi/5
        R = [[math.cos(a),-math.sin(a),0],[math.sin(a),math.cos(a),0],[0,0,1]]
        r = p7.rigid_fit(P, moved(R, [0,0,0]))
        X = r['rotation']
        dots = lambda i,j: sum(X[i][k]*X[j][k] for k in range(3))
        for i in range(3):
            for j in range(3):
                self.assertAlmostEqual(dots(i,j), float(i==j), places=8)
        det = (X[0][0]*(X[1][1]*X[2][2]-X[1][2]*X[2][1])
               - X[0][1]*(X[1][0]*X[2][2]-X[1][2]*X[2][0])
               + X[0][2]*(X[1][0]*X[2][1]-X[1][1]*X[2][0]))
        self.assertAlmostEqual(det, 1, places=8)

    def test_reflection_cannot_be_treated_as_proper_rotation(self):
        target = [[-x[0],x[1],x[2]] for x in P]
        r = p7.rigid_fit(P, target)
        self.assertGreater(max(r['residuals_m']), 1e-3)

    def test_mismatched_point_counts_rejected(self):
        with self.assertRaisesRegex(ValueError, 'matching triples'):
            p7.rigid_fit(P, P[:-1])

    def test_nonfinite_coordinate_rejected(self):
        Q = copy.deepcopy(P)
        Q[2][1] = float('nan')
        with self.assertRaisesRegex(ValueError, 'finite triples'):
            p7.rigid_fit(P, Q)


class RealP007(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.base = json.loads(p4.C004.read_text())
        cls.p003 = json.loads(p4.P003.read_text())
        cls.p004 = p4.build(cls.base, cls.p003)
        cls.p005 = p5.build(cls.base, cls.p004)

    def test_p004_and_p005_fit_same_rib_marker_target(self):
        self.assertEqual(p7.audit(self.base, self.p004), p7.audit(self.base, self.p005))

    def test_fit_has_14_marker_pairs_and_is_unapproved(self):
        r = p7.audit(self.base, self.p005)
        self.assertEqual(r['number_of_sternocostal_marker_controls'], 14)
        self.assertFalse(r['canonical_promotion_allowed'])
        self.assertFalse(r['sternum_surface_pose_verified'])
        self.assertFalse(r['sternum_joint_kinematics_verified'])

    def test_rigid_fit_least_squares_no_worse_than_pure_translation_rms(self):
        r = p7.audit(self.base, self.p005)
        pure = p6.audit(self.base, self.p005)
        self.assertLessEqual(r['rms_3d_proxy_vector_residual_mm'],
                             pure['ls_root_mean_square_change_mm'] + .0001)

    def test_finite_rotation_output_and_no_pose_construction(self):
        r = p7.audit(self.base, self.p004)
        self.assertTrue(math.isfinite(r['best_fit_rotation_angle_deg']))
        self.assertTrue(math.isfinite(r['max_3d_proxy_vector_residual_mm']))
        self.assertTrue(r['not_a_candidate_record'])
        self.assertNotIn('bones', r)

    def test_reject_nonrigid_rib_tail_hijack(self):
        bad = copy.deepcopy(self.p005)
        bad['bones']['rib_01_left']['tail_m'][0] += .008
        with self.assertRaisesRegex(ValueError, 'not translated rigidly'):
            p7.audit(self.base, bad)

    def test_reject_sternocostal_wrong_frame_owner(self):
        bad = copy.deepcopy(self.p005)
        bad['joint_markers']['sternocostal_05_left']['frame_bone'] = 'rib_05_left'
        with self.assertRaisesRegex(ValueError, 'does not belong to sternum'):
            p7.audit(self.base, bad)

    def test_record_immutable_and_deterministic(self):
        original = json.dumps([self.base, self.p005], sort_keys=True)
        self.assertEqual(p7.audit(self.base, self.p005), p7.audit(self.base, self.p005))
        self.assertEqual(original, json.dumps([self.base, self.p005], sort_keys=True))


if __name__ == '__main__':
    unittest.main()
