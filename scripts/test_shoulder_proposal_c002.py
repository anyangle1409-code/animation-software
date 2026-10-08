"""Regression checks for r95_a003_shoulder_proposal_c002_ansur_height (owner policy SHOULDER_HEIGHT_ANCHOR_ANSUR_LIVING).
They pin identity, the pure vertical rigid translation, preservation of c001/a003, the ANSUR target and the recorded
SC closure FAIL. They do not grade the candidate as correct."""
import csv, hashlib, importlib.util, itertools, json, math, sys, unittest
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts/anatomy_fit')); sys.path.insert(0, str(ROOT / 'scripts'))
import build_shoulder_candidate_c002 as c2  # noqa: E402
from report_compare import report_differences  # noqa: E402

ANAT = ROOT / 'ORIGINAL_V1_WORK/anatomy'
D1 = ANAT / 'audit/candidates/shoulder_proposal_c001'
D2 = ANAT / 'audit/candidates/shoulder_proposal_c002_ansur_height'
C1 = json.loads((D1 / 'candidate_record.json').read_text())
C2 = json.loads((D2 / 'candidate_record.json').read_text())
A003 = json.loads((ANAT / 'character_fit_r95_a003.json').read_text())
K = C2['candidate']
spec = importlib.util.spec_from_file_location('cp2', ROOT / 'scripts/anatomy_fit/cp2_preflight.py')
cp2 = importlib.util.module_from_spec(spec); spec.loader.exec_module(cp2)


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


class Identity(unittest.TestCase):
    def test_record_reproduces(self):
        self.assertEqual(report_differences(C2, json.loads(json.dumps(c2.build()))), [])

    def test_status_and_policy(self):
        self.assertEqual(K['id'], 'r95_a003_shoulder_proposal_c002_ansur_height')
        self.assertEqual(K['status'], 'AUDIT_PROPOSAL_NOT_CANONICAL_NOT_ACCEPTED')
        self.assertIs(K['freeze_ready'], False); self.assertIs(C2['character_accepted'], False)
        self.assertEqual(K['owner_policy'], 'SHOULDER_HEIGHT_ANCHOR_ANSUR_LIVING')
        self.assertIn('not proof', K['policy_caveat'])

    def test_c001_and_a003_preserved(self):
        self.assertEqual(K['base_record']['sha256'], sha(D1 / 'candidate_record.json'))
        self.assertTrue(K['base_record']['sha256'].startswith('08e9f2e1187dbeda'))
        self.assertTrue(sha(D1 / 'HGPT_ANATOMICAL_AUDIT_r95_a003_shoulder_proposal_c001.blend').startswith('63ef703ef3a3b160'))
        self.assertTrue(sha(ANAT / 'audit/HGPT_ANATOMICAL_AUDIT_r95_a003.blend').startswith('670a37bfd206d702'))
        self.assertEqual(C1['candidate']['base_record']['sha256'], sha(ANAT / 'character_fit_r95_a003.json'))

    def test_blend_build_log_and_roundtrip(self):
        log = json.loads((D2 / 'build_stdout.json').read_text())
        self.assertEqual(log['sha256'], sha(D2 / 'HGPT_ANATOMICAL_AUDIT_r95_a003_shoulder_proposal_c002_ansur_height.blend'))
        self.assertEqual(log['source_sha256_before'], log['source_sha256_after'])
        self.assertEqual((log['bones'], log['markers'], log['scapula_landmark_empties']), (206, 427, 58))
        self.assertIs(json.loads((D2 / 'roundtrip_report.json').read_text())['roundtrip']['roundtrip_pass'], True)


class RigidVerticalTranslation(unittest.TestCase):
    def test_translation_is_vertical_and_uniform(self):
        dz = K['translation_mm']['z'] / 1000
        self.assertEqual((K['translation_mm']['x'], K['translation_mm']['y']), (0.0, 0.0))
        for k in A003['bones']:
            for e in ('head_m', 'tail_m'):
                a, b = np.array(C1['bones'][k][e]), np.array(C2['bones'][k][e])
                expect = a + ([0, 0, dz] if k in K['moved_bones'] else 0)
                self.assertTrue(np.allclose(b, expect, atol=6e-5), (k, e))       # dz rounded to 0.1 mm in the record
        for k in A003['joint_markers']:
            a, b = np.array(C1['joint_markers'][k]['centre_m']), np.array(C2['joint_markers'][k]['centre_m'])
            self.assertTrue(np.allclose(b - a, [0, 0, dz] if k in K['moved_markers'] else 0, atol=6e-5), k)

    def test_unmoved_identical_to_a003(self):
        for k, b in A003['bones'].items():
            if k not in K['moved_bones']:
                self.assertEqual(b['head_m'], C2['bones'][k]['head_m']); self.assertEqual(b['tail_m'], C2['bones'][k]['tail_m'])

    def test_internal_geometry_unchanged(self):
        for side in ('left', 'right'):
            p1 = np.array(C1['candidate']['scapula_landmarks_world_mm'][side]); p2 = np.array(K['scapula_landmarks_world_mm'][side])
            for i, j in itertools.combinations(range(29), 2):
                self.assertAlmostEqual(np.linalg.norm(p1[i] - p1[j]), np.linalg.norm(p2[i] - p2[j]), places=6)
        L = lambda r, b: math.dist(r['bones'][b]['head_m'], r['bones'][b]['tail_m'])
        for b in ('clavicle_left', 'clavicle_right', 'scapula_left', 'scapula_right', 'humerus_left', 'radius_right'):
            self.assertAlmostEqual(L(C1, b), L(C2, b), places=9)

    def test_bilateral_mirror(self):
        for k in K['moved_bones']:
            if k.endswith('_left'):
                l, r = C2['bones'][k], C2['bones'][k[:-5] + '_right']
                for e in ('head_m', 'tail_m'):
                    self.assertAlmostEqual(l[e][0], -r[e][0], places=9); self.assertAlmostEqual(l[e][2], r[e][2], places=9)


class AnsurAnchor(unittest.TestCase):
    def test_target_recomputed_from_raw_file(self):
        with open(ANAT / 'sources/ansur2/ANSUR_II_MALE_Public.csv', encoding='latin-1') as f:
            rows = list(csv.DictReader(f))
        s = np.array([float(r['stature']) for r in rows]); y = np.array([float(r['acromialheight']) for r in rows])
        b = np.polyfit(s, y, 1)
        self.assertEqual(len(rows), 4082)
        self.assertAlmostEqual(np.polyval(b, 1820), K['landmark_mapping']['target_mm']['mean'], delta=0.06)
        self.assertAlmostEqual((y - np.polyval(b, s)).std(ddof=2), K['uncertainty_mm']['ANSUR_residual_sd_at_182'], delta=0.06)

    def test_lm27_meets_target_both_sides(self):
        for side in ('left', 'right'):
            self.assertAlmostEqual(K['scapula_landmarks_world_mm'][side][26][2], K['landmark_mapping']['target_mm']['mean'], delta=0.05)

    def test_skin_offset_not_invented(self):
        self.assertTrue(K['landmark_mapping']['skin_to_bone_offset'].startswith('NOT APPLIED'))


class Closure(unittest.TestCase):
    def test_sc_closure_fail_recorded_not_forced(self):
        c = K['closure_vs_retained_trunk']
        self.assertEqual(c['status'], 'FAIL')
        self.assertTrue(c['SC_below_IJ_exceeds_whole_manubrium_length'])
        self.assertLess(c['SC_minus_IJ_mm'], -max(c['published_male_mean_manubrium_length_range_mm']))

    def test_no_recorded_variant_closes(self):
        self.assertTrue(all(v['SC_minus_IJ_after_mm'] < 0 < v['source_SC_minus_IJ_mm'] for v in K['sensitivity_dz_by_world_and_landmark'].values()))
        self.assertTrue(K['closure_in_any_recorded_variant'].startswith('NO'))

    def test_cp2_verdicts_unchanged_from_a003(self):
        inv, arts, add = cp2.load_reference()
        ra, rc = cp2.check_candidate(A003, inv, arts, add), cp2.check_candidate(C2, inv, arts, add)
        self.assertEqual({c['id']: c['status'] for c in ra['checks']}, {c['id']: c['status'] for c in rc['checks']})


class Naming(unittest.TestCase):
    def test_reserved_canonical_c001_not_created(self):
        # audit ids r95_a003_shoulder_proposal_c00x are unrelated to the reserved canonical name
        sel = json.loads((ANAT / 'canonical_target_selection_v1.json').read_text())
        self.assertEqual(sel['candidate_name_when_ready'], 'HGPT_CANONICAL_SKELETON_FIRST_c001')
        self.assertEqual(list(ROOT.glob('ORIGINAL_V1_WORK/**/*HGPT_CANONICAL_SKELETON_FIRST_c001*')), [])


class ReviewEvidence(unittest.TestCase):
    def test_manifest(self):
        man = json.loads((D2 / 'review/manifest.json').read_text())
        self.assertEqual(man['closure_vs_retained_trunk'], 'FAIL')
        for rel, h in man['files_sha256'].items():
            self.assertEqual(sha(ROOT / rel), h, rel)
        self.assertEqual(man['sources_sha256']['c002_record'], sha(D2 / 'candidate_record.json'))
        self.assertEqual(man['sources_sha256']['c001_record'], sha(D1 / 'candidate_record.json'))
        for d in ('before_after_c001_vs_c002', 'before_after_a003_vs_c002'):
            self.assertEqual(len([k for k in man['files_sha256'] if f'/{d}/' in k]), len(man['views']) + len(man['poses']))


if __name__ == '__main__':
    unittest.main()
