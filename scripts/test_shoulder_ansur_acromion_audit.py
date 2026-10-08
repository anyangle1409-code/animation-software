"""Regression checks for the ANSUR acromion correspondence / c003 feasibility audit. They pin the owner-verified
definition, the mapping decision, the infeasibility verdict and that c002 and c001 stay untouched."""
import hashlib, json, math, sys, unittest
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts/anatomy_fit')); sys.path.insert(0, str(ROOT / 'scripts'))
import shoulder_ansur_acromion_audit as m  # noqa: E402
from report_compare import report_differences  # noqa: E402

ANAT = ROOT / 'ORIGINAL_V1_WORK/anatomy'
A = json.loads((ANAT / 'audit/shoulder_ansur_acromion_correspondence_v1.json').read_text())


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


class Audit(unittest.TestCase):
    def test_reproduces(self):
        self.assertEqual(report_differences(A, json.loads(json.dumps(m.build()))), [])

    def test_definition_is_bony_palpated_no_skin_offset(self):
        d = A['ansur_definition']
        self.assertIn('ADA548497', d['source'])
        self.assertEqual(d['sections'], ['5.2.1 (landmark)', '6.4.2 (acromial height)'])
        self.assertIn('palpated bony point', d['acromion_landmark'])
        self.assertIn('trapezius point', d['acromion_landmark']); self.assertIn('clavicle point', d['acromion_landmark'])
        self.assertTrue(d['skin_offset'].startswith('none'))
        self.assertIn('owner', d['verification'])

    def test_border_crossings_lie_between_lm25_and_lm27(self):
        c = A['correspondence_points_thorax_frame_mm']
        for k in ('border_x_clavicle_axis_line', 'border_x_lateral_line_through_AC'):
            self.assertFalse(c[k]['clamped'])
            self.assertTrue(0 < c[k]['t_on_LM25_LM27'] < 0.5, k)          # nearer the posterolateral angle than LM27
        h = A['heights_reconciled_girdle_on_a003_IJ']
        lm27 = h['bony_specimen_deg__LM27_lateral_distal_acromial_extent']['z_mm']
        for k in ('border_x_clavicle_axis_line', 'border_x_lateral_line_through_AC'):
            self.assertLess(h[f'bony_specimen_deg__{k}']['z_mm'], lm27)         # c002's LM27 was the highest border mapping

    def test_crossing_geometry_independently(self):
        rc = m.sgs.reconcile(1.0); P = rc['scapula_landmarks']
        t = A['correspondence_points_thorax_frame_mm']['border_x_lateral_line_through_AC']['t_on_LM25_LM27']
        q = P[24] + t * (P[26] - P[24])
        self.assertAlmostEqual(q[0], rc['AC'][0], delta=0.05)                    # lateral line through AC: same anterior coordinate

    def test_no_c003_and_absolute_infeasible(self):
        self.assertEqual(A['status'], 'NO_DEFENSIBLE_C003'); self.assertIs(A['c003_created'], False)
        self.assertEqual(A['verdict']['absolute_height_with_SC_closed_on_a003_sternum'], 'INFEASIBLE')
        for k, v in A['feasibility'].items():
            s = v['absolute_ANSUR_acromial_height']['clavicle_and_scapula_min_chi2']
            self.assertLess(abs(s['height_error_mm']), 0.1, k)                   # the height was actually met
            self.assertGreater(s['max_abs_z'], 2, k)
            self.assertLess(s['clavicle_elevation_deg'], 0, k)
        self.assertFalse(list((ANAT / 'audit/candidates').glob('*c003*')))

    def test_within_subject_relation_reported_not_applied(self):
        self.assertIn('bony_specimen_deg__LM25_exterior_acromial_angle', A['verdict']['within_subject_relation_with_SC_closed'])
        self.assertAlmostEqual(A['targets']['a003_IJ_minus_ANSUR_suprasternale_mm'], 24.7, delta=0.05)
        self.assertIn('not applied', A['verdict']['reading'])

    def test_elevation_solution_is_consistent(self):
        rc = m.sgs.reconcile(1.0)
        ac, _ = m.pose_girdle(rc, 0.0, rc['angles_deg'])
        self.assertAlmostEqual(m.elevation(rc, ac), rc['elevation_deg'], places=6)   # phi=0 reproduces the reconciled girdle
        self.assertAlmostEqual(np.linalg.norm(m.pose_girdle(rc, -20.0, rc['angles_deg'])[0] - rc['SC']), rc['clavicle_length_mm'], places=6)

    def test_c001_c002_untouched(self):
        ins = A['inputs_sha256']
        self.assertEqual(ins['ORIGINAL_V1_WORK/anatomy/audit/candidates/shoulder_proposal_c002_ansur_height/candidate_record.json'],
                         sha(ANAT / 'audit/candidates/shoulder_proposal_c002_ansur_height/candidate_record.json'))
        self.assertTrue(sha(ANAT / 'audit/candidates/shoulder_proposal_c002_ansur_height/candidate_record.json').startswith('aa344a6819dde763'))
        self.assertTrue(sha(ANAT / 'audit/candidates/shoulder_proposal_c001/candidate_record.json').startswith('08e9f2e1187dbeda'))
        c2 = json.loads((ANAT / 'audit/candidates/shoulder_proposal_c002_ansur_height/candidate_record.json').read_text())['candidate']
        self.assertEqual(c2['closure_vs_retained_trunk']['status'], 'FAIL')


class Evidence(unittest.TestCase):
    def test_manifest_hashes(self):
        man = json.loads((ANAT / 'audit/shoulder_ansur_acromion_evidence/manifest.json').read_text())
        self.assertEqual(man['audit_sha256'], sha(ANAT / 'audit/shoulder_ansur_acromion_correspondence_v1.json'))
        self.assertEqual(man['status'], 'NO_DEFENSIBLE_C003')
        for rel, h in man['files_sha256'].items():
            self.assertEqual(sha(ROOT / rel), h, rel)
        names = {Path(k).stem for k in man['files_sha256']}
        for v in ('left_front', 'left_side', 'left_rear', 'left_overhead', 'right_front', 'right_side', 'right_rear', 'right_overhead',
                  'chart_required_clavicle_elevation', 'sheet_shoulders_both_sides'):
            self.assertIn(v, names)


if __name__ == '__main__':
    unittest.main()
