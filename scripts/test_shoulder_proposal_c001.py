"""Regression checks for the shoulder-proposal audit candidate r95_a003_shoulder_proposal_c001 and the vertical-relation
audit. These pin identity, scope of change and the recorded defects; they do not grade the candidate as correct."""
import hashlib, importlib.util, json, math, sys, unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts/anatomy_fit')); sys.path.insert(0, str(ROOT / 'scripts'))
import build_shoulder_candidate_record as cr  # noqa: E402
import shoulder_vertical_relation_audit as va  # noqa: E402
from report_compare import report_differences  # noqa: E402

ANAT = ROOT / 'ORIGINAL_V1_WORK/anatomy'
CDIR = ANAT / 'audit/candidates/shoulder_proposal_c001'
CAND = json.loads((CDIR / 'candidate_record.json').read_text())
A003 = json.loads((ANAT / 'character_fit_r95_a003.json').read_text())
SOL = json.loads((ANAT / 'canonical_shoulder_girdle_solution_182_v1.json').read_text())
AUDIT = json.loads((ANAT / 'audit/shoulder_vertical_relation_audit_v1.json').read_text())
A003_BLEND_SHA = '670a37bf'
spec = importlib.util.spec_from_file_location('cp2', ROOT / 'scripts/anatomy_fit/cp2_preflight.py')
cp2 = importlib.util.module_from_spec(spec); spec.loader.exec_module(cp2)


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


class Identity(unittest.TestCase):
    def test_record_reproduces(self):
        self.assertEqual(report_differences(CAND, json.loads(json.dumps(cr.build()))), [])

    def test_status_never_canonical(self):
        c = CAND['candidate']
        self.assertEqual(c['id'], 'r95_a003_shoulder_proposal_c001')
        self.assertEqual(c['status'], 'AUDIT_PROPOSAL_NOT_CANONICAL_NOT_ACCEPTED')
        self.assertIs(c['freeze_ready'], False)
        self.assertIs(CAND['character_accepted'], False)

    def test_pinned_inputs(self):
        c = CAND['candidate']
        self.assertEqual(c['base_record']['sha256'], sha(ANAT / 'character_fit_r95_a003.json'))
        self.assertEqual(c['solution']['sha256'], sha(ANAT / 'canonical_shoulder_girdle_solution_182_v1.json'))
        self.assertTrue(sha(ANAT / 'audit/HGPT_ANATOMICAL_AUDIT_r95_a003.blend').startswith(A003_BLEND_SHA))

    def test_blend_matches_build_log_and_roundtrip(self):
        log = json.loads((CDIR / 'build_stdout.json').read_text())
        self.assertEqual(log['sha256'], sha(CDIR / 'HGPT_ANATOMICAL_AUDIT_r95_a003_shoulder_proposal_c001.blend'))
        self.assertEqual(log['source_sha256_before'], log['source_sha256_after'])
        self.assertEqual(log['scapula_landmark_empties'], 58)
        self.assertEqual(json.loads((CDIR / 'roundtrip_report.json').read_text())['roundtrip']['roundtrip_pass'], True)


class ScopeOfChange(unittest.TestCase):
    def test_only_shoulder_and_arm_bones_changed(self):
        arm = set()
        for side in ('left', 'right'):
            arm |= cr.descendants(A003['bones'], f'humerus_{side}') | {f'clavicle_{side}', f'scapula_{side}'}
        changed = {k for k in A003['bones'] if A003['bones'][k]['head_m'] != CAND['bones'][k]['head_m'] or A003['bones'][k]['tail_m'] != CAND['bones'][k]['tail_m']}
        self.assertTrue(changed <= arm, changed - arm)
        self.assertEqual(set(CAND['candidate']['moved_bones']), arm)

    def test_arm_lengths_kept(self):
        for k, how in CAND['candidate']['moved_bones'].items():
            if how == 'translated with GH' and not k.startswith('humerus_'):
                a, c = A003['bones'][k], CAND['bones'][k]
                self.assertAlmostEqual(math.dist(a['head_m'], a['tail_m']), math.dist(c['head_m'], c['tail_m']), places=9)

    def test_only_listed_markers_changed(self):
        changed = {k for k in A003['joint_markers'] if A003['joint_markers'][k]['centre_m'] != CAND['joint_markers'][k]['centre_m']}
        self.assertEqual(changed, set(CAND['candidate']['moved_markers']))

    def test_cp2_verdicts_unchanged_from_a003(self):
        inv, arts, add = cp2.load_reference()
        ra, rc = cp2.check_candidate(A003, inv, arts, add), cp2.check_candidate(CAND, inv, arts, add)
        self.assertEqual({c['id']: c['status'] for c in ra['checks']}, {c['id']: c['status'] for c in rc['checks']})


class GeometryMatchesSolution(unittest.TestCase):
    def test_landmarks_and_centres(self):
        w = SOL['variants'][cr.VARIANT]['world_mm'][cr.WORLD]
        for side in ('left', 'right'):
            self.assertEqual(CAND['candidate']['scapula_landmarks_world_mm'][side], w[side]['scapula_all_29'])
            for jid, key in (('sternoclavicular', 'SC'), ('acromioclavicular', 'AC'), ('glenohumeral', cr.GH_KEY)):
                got = [x * 1000 for x in CAND['joint_markers'][f'{jid}_{side}']['centre_m']]
                for g, e in zip(got, w[side][key]):
                    self.assertAlmostEqual(g, e, places=6)

    def test_bilateral_mirror(self):
        for k in ('clavicle', 'scapula'):
            l, r = CAND['bones'][f'{k}_left'], CAND['bones'][f'{k}_right']
            for e in ('head_m', 'tail_m'):
                self.assertAlmostEqual(l[e][0], -r[e][0], places=9)
                self.assertAlmostEqual(l[e][1], r[e][1], places=9); self.assertAlmostEqual(l[e][2], r[e][2], places=9)

    def test_clavicle_length_is_solution_chord(self):
        L = math.dist(CAND['bones']['clavicle_left']['head_m'], CAND['bones']['clavicle_left']['tail_m']) * 1000
        self.assertAlmostEqual(L, SOL['variants'][cr.VARIANT]['reconciled']['clavicle_joint_centre_length_mm'], delta=0.1)   # reconciled, not the direct 152.4


class VerticalRelationAudit(unittest.TestCase):
    def test_reproduces(self):
        self.assertEqual(report_differences(AUDIT, json.loads(json.dumps(va.build()))), [])

    def test_v1_hypothesis_withdrawn_by_sign(self):
        e = AUDIT['erratum_v1_vertical_relation_reading']
        self.assertIs(e['consistent_single_offset'], False)
        self.assertTrue(all(v < 0 for v in e['offset_required_by_C7_mm'].values()))
        self.assertGreater(e['offset_required_by_acromion_mm'], 0)
        self.assertIs(e['v1_file_edited'], False)

    def test_known_height_defect_recorded_not_passed(self):
        a = AUDIT['absolute_heights_vs_ANSUR_182']
        self.assertGreater(a['records']['c001_candidate']['LM27_minus_ANSUR_acromial_mm'], 0)
        self.assertEqual(AUDIT['status'], 'AUDIT_OPEN_NOT_RESOLVED')
        self.assertGreater(AUDIT['ij_independent_acromion_vs_C7']['smallest_shoulder_excess_over_living_mm'], 0)


class ReviewEvidence(unittest.TestCase):
    def test_manifest_hashes_and_coverage(self):
        man = json.loads((CDIR / 'review/manifest.json').read_text())
        self.assertEqual(man['status'], 'AUDIT_PROPOSAL_NOT_CANONICAL_NOT_ACCEPTED')
        for rel, h in man['files_sha256'].items():
            self.assertEqual(sha(ROOT / rel), h, rel)
        for v in ('full_front', 'full_back', 'full_left_side', 'full_front_left_three_quarter', 'shoulder_left_overhead',
                  'shoulder_right_rear', 'axilla_left_from_below_front', 'axilla_right_from_below_front'):
            self.assertIn(v, man['views'])
        self.assertIn('pose_neutral', man['poses'])
        self.assertEqual(man['sources_sha256']['c001_record'], sha(CDIR / 'candidate_record.json'))


if __name__ == '__main__':
    unittest.main()
