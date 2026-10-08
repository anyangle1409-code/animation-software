"""Regression checks for r95_a003_shoulder_thorax_c003_ansur_coupled. Geometry is re-derived from the stored record
where possible (not read back from the builder's own check block). These pin the candidate; they do not accept it."""
import hashlib, importlib.util, json, math, sys, unittest
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts/anatomy_fit')); sys.path.insert(0, str(ROOT / 'scripts'))
import build_shoulder_candidate_c003 as b3  # noqa: E402
from report_compare import report_differences  # noqa: E402

ANAT = ROOT / 'ORIGINAL_V1_WORK/anatomy'
D = ANAT / 'audit/candidates/shoulder_thorax_c003_ansur_coupled'
C = json.loads((D / 'candidate_record.json').read_text())
A = json.loads((ANAT / 'character_fit_r95_a003.json').read_text())
K = C['candidate']
TF = json.loads((ANAT / 'canonical_thorax_frame_182_review_v1.json').read_text())['ansur_standing_anchors_at_182_mm']
spec = importlib.util.spec_from_file_location('cp2', ROOT / 'scripts/anatomy_fit/cp2_preflight.py')
cp2 = importlib.util.module_from_spec(spec); spec.loader.exec_module(cp2)
mm = lambda v: np.asarray(v, float) * 1000


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def to_thorax(w, side, ij, pitch):
    t = math.radians(pitch)
    up = np.array([0, math.sin(t), math.cos(t)]); ant = np.array([0, -math.cos(t), math.sin(t)])
    lat = np.array([1.0 if side == 'left' else -1.0, 0, 0])
    v = np.asarray(w, float) - ij
    return np.array([v @ ant, v @ up, v @ lat])


class Identity(unittest.TestCase):
    def test_reproduces(self):
        self.assertEqual(report_differences(C, json.loads(json.dumps(b3.build()))), [])

    def test_status_policy_and_baselines(self):
        self.assertEqual(K['id'], 'r95_a003_shoulder_thorax_c003_ansur_coupled')
        self.assertEqual(K['status'], 'AUDIT_PROPOSAL_NOT_CANONICAL_NOT_ACCEPTED')
        self.assertIs(K['freeze_ready'], False); self.assertIs(C['character_accepted'], False)
        self.assertIn('ANSUR measurements govern', K['owner_decision'])
        self.assertEqual(K['base_record']['sha256'], sha(ANAT / 'character_fit_r95_a003.json'))
        for p, pre in ((ANAT / 'audit/HGPT_ANATOMICAL_AUDIT_r95_a003.blend', '670a37bfd206d702'),
                       (ANAT / 'audit/candidates/shoulder_proposal_c001/candidate_record.json', '08e9f2e1187dbeda'),
                       (ANAT / 'audit/candidates/shoulder_proposal_c002_ansur_height/candidate_record.json', 'aa344a6819dde763')):
            self.assertTrue(sha(p).startswith(pre), p)
        self.assertFalse(list(ROOT.glob('ORIGINAL_V1_WORK/**/*HGPT_CANONICAL_SKELETON_FIRST_c001*')))

    def test_blend_log_and_roundtrip(self):
        log = json.loads((D / 'build_stdout.json').read_text())
        self.assertEqual(log['sha256'], sha(D / 'HGPT_ANATOMICAL_AUDIT_r95_a003_shoulder_thorax_c003_ansur_coupled.blend'))
        self.assertEqual(log['source_sha256_before'], log['source_sha256_after'])
        self.assertEqual((log['bones'], log['markers']), (206, 427))
        rt = json.loads((D / 'roundtrip_report.json').read_text())
        self.assertIs(rt['roundtrip']['roundtrip_pass'], True)


class Targets(unittest.TestCase):
    pitch = None

    @classmethod
    def setUpClass(cls):
        cls.pitch = K['construction']['thorax_pitch_deg']
        cls.ij = mm(C['skeleton_input']['trunk']['ij_bone'])

    def test_ij_at_ansur_suprasternale(self):
        self.assertAlmostEqual(self.ij[2], TF['suprasternaleheight']['mean'], places=6)
        self.assertAlmostEqual(mm(C['bones']['sternum']['head_m'])[2], TF['suprasternaleheight']['mean'], places=6)

    def test_acromion_border_crossing_independently(self):
        for side in ('left', 'right'):
            P = [to_thorax(p, side, self.ij, self.pitch) for p in K['scapula_landmarks_world_mm'][side]]
            sc = to_thorax(mm(C['joint_markers'][f'sternoclavicular_{side}']['centre_m']), side, self.ij, self.pitch)
            ac = to_thorax(mm(C['joint_markers'][f'acromioclavicular_{side}']['centre_m']), side, self.ij, self.pitch)
            a25, a27 = P[24], P[26]
            d = np.array([ac[0] - sc[0], ac[2] - sc[2]])                       # clavicle axis in the transverse (ant, lat) plane
            M = np.array([[d[0], a25[0] - a27[0]], [d[1], a25[2] - a27[2]]])
            s, t = np.linalg.solve(M, np.array([a25[0] - ac[0], a25[2] - ac[2]]))
            self.assertTrue(0 < t < 1)
            q = np.asarray(K['scapula_landmarks_world_mm'][side][24]) + t * (np.asarray(K['scapula_landmarks_world_mm'][side][26]) - np.asarray(K['scapula_landmarks_world_mm'][side][24]))
            self.assertAlmostEqual(q[2], TF['acromialheight']['mean'], delta=0.05, msg=side)

    def test_within_subject_relation(self):
        w = K['acceptance_checks']['ansur_targets']
        self.assertAlmostEqual(w['within_subject_acromion_minus_IJ_mm'], 3.2, delta=0.05)
        self.assertLess(abs(w['within_subject_z']), 0.05)

    def test_sc_closure_independently(self):
        rc_sc = np.array(K['acceptance_checks']['sc_closure']['SC_minus_IJ_thorax_frame_mm'])
        for side in ('left', 'right'):
            sc = to_thorax(mm(C['joint_markers'][f'sternoclavicular_{side}']['centre_m']), side, self.ij, self.pitch)
            self.assertTrue(np.allclose(sc, rc_sc, atol=1e-3), side)
            self.assertTrue(np.allclose(C['bones'][f'clavicle_{side}']['head_m'], C['joint_markers'][f'sternoclavicular_{side}']['centre_m']))

    def test_clavicle_angles_independently(self):
        for side in ('left', 'right'):
            v = to_thorax(mm(C['bones'][f'clavicle_{side}']['tail_m']), side, self.ij, self.pitch) - to_thorax(mm(C['bones'][f'clavicle_{side}']['head_m']), side, self.ij, self.pitch)
            el = math.degrees(math.asin(v[1] / np.linalg.norm(v)))
            self.assertAlmostEqual(el, K['acceptance_checks']['angles']['clavicle_elevation_deg'], delta=0.06)
            self.assertLessEqual(abs((el - 8) / 4), 2)
            self.assertAlmostEqual(np.linalg.norm(v), 151.3, delta=0.1)                 # reconciled chord unchanged
        self.assertLessEqual(K['acceptance_checks']['angles']['max_abs_z'], 2)


class Continuity(unittest.TestCase):
    def test_rib_cartilage_links_independently(self):
        D3 = np.array(K['construction']['sternum_translation_mm'])
        for side in ('left', 'right'):
            for n in range(1, 11):
                link = f'sternocostal_{n:02d}_{side}' if n <= 7 else f'interchondral_{n - 1}_{n}_{side}'
                v0 = mm(A['joint_markers'][link]['centre_m']) - mm(A['joint_markers'][f'costochondral_{n:02d}_{side}']['centre_m'])
                v1 = mm(C['joint_markers'][link]['centre_m']) - mm(C['joint_markers'][f'costochondral_{n:02d}_{side}']['centre_m'])
                self.assertLess(np.linalg.norm(v1 - v0), 4.5, link)
                self.assertTrue(np.allclose(C['bones'][f'rib_{n:02d}_{side}']['head_m'], A['bones'][f'rib_{n:02d}_{side}']['head_m']))
                self.assertAlmostEqual(math.dist(*[C['bones'][f'rib_{n:02d}_{side}'][e] for e in ('head_m', 'tail_m')]),
                                       math.dist(*[A['bones'][f'rib_{n:02d}_{side}'][e] for e in ('head_m', 'tail_m')]), places=9)
            for n in (11, 12):
                self.assertEqual(C['bones'][f'rib_{n}_{side}'], A['bones'][f'rib_{n}_{side}'])
        for k in ('manubriosternal', 'xiphisternal'):
            self.assertTrue(np.allclose(mm(C['joint_markers'][k]['centre_m']) - mm(A['joint_markers'][k]['centre_m']), D3, atol=1e-3))   # record rounds the translation to 1e-3 mm

    def test_vertical_only_alternative_was_worse(self):
        self.assertGreater(K['construction']['sternum_translation_mm'][1], 0)              # posterior with descent (pump-handle)
        self.assertLess(K['acceptance_checks']['rib_sternum_continuity']['max_costal_cartilage_vector_change_mm'], 11)

    def test_axial_skull_pelvis_legs_unchanged(self):
        moved = set(K['moved_bones'])
        for k, b in A['bones'].items():
            if k not in moved:
                self.assertEqual(b, C['bones'][k], k)
        import build_shoulder_candidate_record as cr
        allowed = {'sternum'} | {f'rib_{n:02d}_{s}' for n in range(1, 11) for s in ('left', 'right')}
        for side in ('left', 'right'):
            allowed |= {f'clavicle_{side}', f'scapula_{side}'} | cr.descendants(A['bones'], f'humerus_{side}')
        self.assertEqual(moved, allowed)                  # exactly the causally connected set, nothing else

    def test_stature_and_mirror(self):
        z = lambda R: [p[2] for b in R['bones'].values() for p in (b['head_m'], b['tail_m'])]
        self.assertEqual((max(z(A)), min(z(A))), (max(z(C)), min(z(C))))
        for k in ('clavicle', 'scapula', 'humerus'):
            for e in ('head_m', 'tail_m'):
                l, r = C['bones'][f'{k}_left'][e], C['bones'][f'{k}_right'][e]
                self.assertAlmostEqual(l[0], -r[0], places=9); self.assertAlmostEqual(l[2], r[2], places=9)

    def test_no_new_axis_intersections(self):
        self.assertEqual(K['acceptance_checks']['collisions_stick_axes']['new_axis_intersections_below_1mm'], [])

    def test_all_acceptance_checks_pass_and_cp2_parity(self):
        self.assertEqual(set(K['acceptance_checks']['summary'].values()), {'PASS'})
        inv, arts, add = cp2.load_reference()
        ra, rc = cp2.check_candidate(A, inv, arts, add), cp2.check_candidate(C, inv, arts, add)
        self.assertEqual({c['id']: c['status'] for c in ra['checks']}, {c['id']: c['status'] for c in rc['checks']})


class MovementAndEvidence(unittest.TestCase):
    RUN = ANAT / 'audit/runs/isolated_bone_only_c003_shoulder_thorax_001'

    def test_isolated_suite_on_c003(self):
        r = json.loads((self.RUN / 'isolated_report.json').read_text())
        self.assertEqual(r['counts'], {'tests': 135, 'integrity_pass': 135, 'mirror_pairs': 43, 'mirror_pass': 41, 'mirror_solver_test_only': 2})
        self.assertEqual(sorted(k for k, v in r['mirror'].items() if v['status'] != 'PASS'), ['hip_rotation_at_0_flexion', 'hip_rotation_at_90_flexion'])
        self.assertEqual(r['provenance']['source_sha256'], sha(D / 'HGPT_ANATOMICAL_AUDIT_r95_a003_shoulder_thorax_c003_ansur_coupled.blend'))
        self.assertEqual(r['provenance']['source_sha256'], r['provenance']['source_sha256_after'])
        for k in ('shoulder_complex_scapular_plane_left', 'shoulder_complex_scapular_plane_right', 'rib_01_inspiration_left', 'rib_07_inspiration_right'):
            self.assertEqual(r['summary'][k]['integrity_status'], 'PASS', k)

    def test_manifests(self):
        for man_path in (D / 'review/manifest.json', self.RUN / 'clips/manifest.json'):
            man = json.loads(man_path.read_text())
            for rel, h in man['files_sha256'].items():
                self.assertEqual(sha(ROOT / rel), h, rel)
        rv = json.loads((D / 'review/manifest.json').read_text())
        self.assertEqual(rv['sources_sha256']['c003_record'], sha(D / 'candidate_record.json'))
        self.assertEqual(len([k for k in rv['files_sha256'] if '/four_way/' in k]), len(rv['views']) + len(rv['poses']))


if __name__ == '__main__':
    unittest.main()
