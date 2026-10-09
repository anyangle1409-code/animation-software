"""Joint-frame audit: committed results pinned; detectors proven by mutation (improper/handed rest frame, motion-axis drift,
sign flip); and the candidate-specific stale skeleton_input arm-point defect pinned (fix requires a new named revision)."""
import copy, json, math, sys, unittest
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts/anatomy_fit'))
import joint_frame_audit as m  # noqa: E402

O = ROOT / 'ORIGINAL_V1_WORK/anatomy/audit/joint_frame_audit'
ANAT = ROOT / 'ORIGINAL_V1_WORK/anatomy'
REC = json.loads((ANAT / 'character_fit_r95_a003.json').read_text())
S = json.loads((ANAT / 'audit/runs/isolated_bone_only_014/isolated_samples.json').read_text())
CANDS = {'c001': ('audit/candidates/shoulder_proposal_c001/candidate_record.json', 74.2),
         'c002': ('audit/candidates/shoulder_proposal_c002_ansur_height/candidate_record.json', 47.0),
         'c003': ('audit/candidates/shoulder_thorax_c003_ansur_coupled/candidate_record.json', 38.4)}


def rot(axis, deg):
    a = np.asarray(axis, float) / np.linalg.norm(axis); t = math.radians(deg)
    K = np.array([[0, -a[2], a[1]], [a[2], 0, -a[0]], [-a[1], a[0], 0]])
    return np.eye(3) + math.sin(t) * K + (1 - math.cos(t)) * K @ K


class Committed(unittest.TestCase):
    def test_results(self):
        for name in ('a003_isolated_014', 'c003_isolated_001'):
            d = json.loads((O / f'{name}.json').read_text())
            r, mo = d['rest'], d['motion']
            self.assertEqual((r['markers'], r['bilateral_pairs'], r['improper'], r['families_with_mixed_flip']), (427, 180, [], []))
            self.assertLess(r['max_rest_asymmetry_deg'], 0.5)
            self.assertTrue(all(x['joint'].split('_')[0] in ('mtp', 'toe2', 'toe3', 'toe4', 'toe5', 'hallux') for x in r['rest_asymmetry_top'][:6]))
            self.assertEqual((mo['frame_issue_count'], mo['sign_flip_total'], mo['single_channel_tests']), (0, 0, 106))
            self.assertLess(mo['max_axis_drift_deg'], 1e-3)

    def test_candidate_hand_axis_difference_pinned(self):
        a = json.loads((O / 'a003_isolated_014.json').read_text())['motion']['tests']
        c = json.loads((O / 'c003_isolated_001.json').read_text())['motion']['tests']
        for t, j in (('digit2_mcp_abduction_left', 'digit2_mcp_left'), ('thumb_cmc_radial_abduction_right', 'cmc_1_right')):
            self.assertGreater(abs(a[t]['joints_moving'][j]['alignment_deg'] - c[t]['joints_moving'][j]['alignment_deg']), 10)
        self.assertEqual(a['knee_flexion_extension_left'], c['knee_flexion_extension_left'])   # legs untouched by c003

    def test_stale_arm_inputs_in_candidates(self):
        for name, (p, wjc_mm) in CANDS.items():
            c = json.loads((ANAT / p).read_text())
            S0, S1 = REC['skeleton_input']['sides']['left'], c['skeleton_input']['sides']['left']
            for k in ('EJC', 'WJC', 'ulnar_styloid_bone', 'radial_styloid_bone'):
                self.assertEqual(S1[k], S0[k], (name, k))                                       # not moved with the arm
            gap = np.linalg.norm(np.array(S1['WJC']) - np.array(c['joint_markers']['radiocarpal_left']['centre_m'])) * 1000
            ghs = np.linalg.norm(np.array(c['joint_markers']['glenohumeral_left']['centre_m']) - np.array(REC['joint_markers']['glenohumeral_left']['centre_m'])) * 1000
            self.assertAlmostEqual(gap, wjc_mm, delta=0.1); self.assertAlmostEqual(gap, ghs, delta=0.1)

    def test_consistency_json(self):
        d = json.loads((O / 'candidate_input_consistency.json').read_text())
        self.assertIn('UNRESOLVED', d['disposition'])
        for name, (_, mm) in CANDS.items():
            c = d['candidates'][name]
            self.assertEqual(c['classification'], 'CANDIDATE_PROVENANCE_DEFECT')
            for s in c['sides'].values():
                self.assertEqual(s['input_to_marker_gap']['WJC']['a003_mm'], 0.0)
                self.assertAlmostEqual(s['input_to_marker_gap']['WJC']['candidate_mm'], mm, delta=0.1)
                self.assertIn('WJC', s['stale_arm_inputs'])


class Mutations(unittest.TestCase):
    def test_improper_rest_frame_detected(self):
        rec = copy.deepcopy(REC)
        A = np.array(rec['joint_markers']['tibiofemoral_left']['frame_axes_columns_XYZ']); A[:, 0] *= -1          # reflect: det -1
        rec['joint_markers']['tibiofemoral_left']['frame_axes_columns_XYZ'] = A.tolist()
        self.assertIn('tibiofemoral_left', [x['marker'] for x in m.rest_audit(rec)['improper']])

    def test_mixed_mirror_convention_detected(self):
        rec = copy.deepcopy(REC)
        A = np.array(rec['joint_markers']['mtp_2_right']['frame_axes_columns_XYZ'])
        rec['joint_markers']['mtp_2_right']['frame_axes_columns_XYZ'] = (A @ np.diag([-1.0, 1.0, -1.0])).tolist()   # proper; X-flip convention
        r = m.rest_audit(rec)
        self.assertEqual(r['pairs']['mtp_2']['flip_axis'], 'X'); self.assertIn('mtp', r['families_with_mixed_flip'])

    def test_unmirrorable_pair_residual_detected(self):
        rec = copy.deepcopy(REC)
        A = np.array(rec['joint_markers']['tibiofemoral_right']['frame_axes_columns_XYZ'])
        rec['joint_markers']['tibiofemoral_right']['frame_axes_columns_XYZ'] = (A @ np.diag([-1.0, -1.0, 1.0])).tolist()
        self.assertGreater(m.rest_audit(rec)['pairs']['tibiofemoral']['residual_deg'], 90)

    def _knee(self):
        return {'knee_flexion_extension_left': copy.deepcopy(S['knee_flexion_extension_left'])}

    def test_axis_drift_detected(self):
        smp = self._knee()
        for fr in smp['knee_flexion_extension_left'][20:30]:
            D = np.array(fr['moving_deltas']['tibia_left']); D[:3, :3] = rot([0, 1, 0], 3.0) @ D[:3, :3]
            fr['moving_deltas']['tibia_left'] = D.tolist()
        r = m.motion_audit(REC, smp)['tests']['knee_flexion_extension_left']['joints_moving']['tibiofemoral_left']
        self.assertGreater(r['axis_drift_deg'], 1.0)

    def test_sign_flip_detected(self):
        smp = self._knee()
        for fr in smp['knee_flexion_extension_left'][10:20]:
            D = np.array(fr['moving_deltas']['tibia_left']); D[:3, :3] = D[:3, :3].T                       # rotate the wrong way
            fr['moving_deltas']['tibia_left'] = D.tolist()
        self.assertGreater(m.motion_audit(REC, smp)['sign_flip_total'], 0)


if __name__ == '__main__':
    unittest.main()
