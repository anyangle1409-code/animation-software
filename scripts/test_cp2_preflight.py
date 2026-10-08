import copy, importlib.util, json, math, unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('cp2', ROOT / 'scripts/anatomy_fit/cp2_preflight.py')
m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
ANAT = ROOT / 'ORIGINAL_V1_WORK/anatomy'
INV, ARTS, ADD = m.load_reference()
A003 = json.loads((ANAT / 'character_fit_r95_a003.json').read_text())


def status(report, cid):
    return next(c for c in report['checks'] if c['id'] == cid)


def run(cand):
    return m.check_candidate(cand, INV, ARTS, ADD)


def with_gaps(cand, gap_m=0.008):
    """Separate every vertebral body from the one above (synthetic; not an anatomical value)."""
    c = copy.deepcopy(cand)
    order = ['c2', 'c3', 'c4', 'c5', 'c6', 'c7'] + [f't{i}' for i in range(1, 13)] + ['l1', 'l2', 'l3', 'l4', 'l5']
    for i, v in enumerate(order[:-1]):          # shorten each inferior body at its superior end
        inf = order[i + 1]
        h, t = c['bones'][inf]['head_m'], c['bones'][inf]['tail_m']
        L = math.dist(h, t)
        c['bones'][inf]['tail_m'] = [a + (b - a) * (L - gap_m) / L for a, b in zip(h, t)]
    return c


class A003Baseline(unittest.TestCase):
    def setUp(self):
        self.r = run(A003)

    def test_structure_passes(self):
        for cid in ('bone_identity_206', 'bone_coordinates_finite', 'bone_nondegenerate', 'parent_tree',
                    'side_sign_left_plus_x', 'joint_identity_427', 'joint_frames_proper', 'shoulder_centres_distinct'):
            self.assertEqual(status(self.r, cid)['status'], 'PASS', cid)

    def test_known_zero_disc_gap_defect_is_caught(self):
        c = status(self.r, 'spinal_disc_centre_gap_positive')
        self.assertEqual(c['status'], 'FAIL')
        self.assertEqual(len(c['failures']), 22)                       # C2/C3 .. L4/L5
        self.assertTrue(all(abs(v) < 1e-9 for k, v in c['measurements'].items() if k != 'disc_l5_sacrum'))
        self.assertGreater(c['measurements']['disc_l5_sacrum'], 0)

    def test_missing_endplates_never_pass(self):
        c = status(self.r, 'disc_endplate_clearance')
        self.assertEqual(c['status'], 'UNVERIFIED')
        self.assertEqual(len(c['unverified']), 23)
        self.assertEqual(self.r['verdict'], 'FAIL')


class Mutations(unittest.TestCase):
    def test_removed_and_extra_bone(self):
        c = copy.deepcopy(A003); del c['bones']['pisiform_left']; c['bones']['os_trigonum_left'] = c['bones']['talus_left']
        f = status(run(c), 'bone_identity_206')['failures']
        self.assertIn('missing pisiform_left', f); self.assertIn('extra os_trigonum_left', f)

    def test_unresolved_and_nonfinite_coordinates(self):
        c = copy.deepcopy(A003); c['bones']['clavicle_left']['tail_m'] = None; c['bones']['femur_left']['head_m'][2] = float('nan')
        self.assertEqual(len(status(run(c), 'bone_coordinates_finite')['failures']), 2)

    def test_zero_length_bone(self):
        c = copy.deepcopy(A003); c['bones']['lunate_left']['tail_m'] = list(c['bones']['lunate_left']['head_m'])
        self.assertEqual(status(run(c), 'bone_nondegenerate')['status'], 'FAIL')

    def test_parent_cycle_wrong_joint_and_hyoid_parent(self):
        c = copy.deepcopy(A003); c['bones']['sacrum']['parent'] = 'coccyx'
        self.assertTrue(any('cycle' in f for f in status(run(c), 'parent_tree')['failures']))
        c = copy.deepcopy(A003); c['bones']['radius_left']['parent_relation']['joint_id'] = 'hip_left'
        self.assertTrue(any('does not join' in f for f in status(run(c), 'parent_tree')['failures']))
        c = copy.deepcopy(A003); c['bones']['hyoid']['parent'] = 'c3'; c['bones']['hyoid']['parent_relation'] = {'type': 'carrier'}
        self.assertTrue(any('hyoid' in f for f in status(run(c), 'parent_tree')['failures']))

    def test_side_swap(self):
        c = copy.deepcopy(A003)
        c['bones']['humerus_left'], c['bones']['humerus_right'] = c['bones']['humerus_right'], c['bones']['humerus_left']
        self.assertEqual(len(status(run(c), 'side_sign_left_plus_x')['failures']), 2)

    def test_reflected_and_skewed_frames(self):
        c = copy.deepcopy(A003); F = c['joint_markers']['glenohumeral_left']['frame_axes_columns_XYZ']
        for row in F: row[2] = -row[2]                                # reflection: det -1
        self.assertEqual(status(run(c), 'joint_frames_proper')['status'], 'FAIL')
        c = copy.deepcopy(A003); c['joint_markers']['hip_left']['frame_axes_columns_XYZ'][0][0] += 1e-3
        self.assertEqual(status(run(c), 'joint_frames_proper')['status'], 'FAIL')

    def test_collapsed_shoulder_centres_and_missing_marker(self):
        c = copy.deepcopy(A003)
        c['joint_markers']['acromioclavicular_right']['centre_m'] = list(c['joint_markers']['glenohumeral_right']['centre_m'])
        self.assertEqual(status(run(c), 'shoulder_centres_distinct')['status'], 'FAIL')
        c = copy.deepcopy(A003); del c['joint_markers']['sternoclavicular_left']
        r = run(c)
        self.assertEqual(status(r, 'joint_identity_427')['status'], 'FAIL')
        self.assertEqual(status(r, 'shoulder_centres_distinct')['status'], 'UNVERIFIED')

    def test_gapped_spine_passes_centre_check_but_not_clearance(self):
        r = run(with_gaps(A003))
        c = status(r, 'spinal_disc_centre_gap_positive')
        self.assertEqual(c['status'], 'PASS')
        self.assertAlmostEqual(c['measurements']['disc_c2_c3'], 8.0, places=6)
        self.assertEqual(status(r, 'disc_endplate_clearance')['status'], 'UNVERIFIED')
        self.assertEqual(r['verdict'], 'INCOMPLETE')

    def test_endplate_surfaces(self):
        flat = {'upper_normal': [0, 0, 1], 'lower_normal': [0, 0, 1], 'footprint_centre_xy_mm': [0, 0], 'footprint_radii_xy_mm': [20, 15]}
        c = with_gaps(A003)
        c['disc_surfaces'] = {d: dict(flat, upper_origin_mm=[0, 0, 8], lower_origin_mm=[0, 0, 0]) for d in m.SPINAL_DISCS}
        r = run(c)
        self.assertEqual(status(r, 'disc_endplate_clearance')['status'], 'PASS')
        self.assertEqual(r['verdict'], 'STRUCTURE_PASS_EVIDENCE_REVIEW_STILL_REQUIRED')
        c['disc_surfaces']['disc_l4_l5'] = dict(flat, upper_origin_mm=[0, 0, 2], lower_origin_mm=[0, 0, 0], upper_normal=[0.2, 0, 1])
        self.assertEqual(status(run(c), 'disc_endplate_clearance')['status'], 'FAIL')     # tilted plate dips below
        c['disc_surfaces'] = dict(c['disc_surfaces'], disc_c1_c2=c['disc_surfaces']['disc_c2_c3'])
        self.assertTrue(any('C1/C2' in f for f in status(run(c), 'disc_endplate_clearance')['failures']))


class Ledger(unittest.TestCase):
    def test_every_bone_accounted_and_counts_match_readiness(self):
        led = m.readiness_ledger(INV, json.loads((ANAT / 'canonical_freeze_readiness_v1.json').read_text()),
                                 json.loads((ANAT / 'canonical_target_selection_v1.json').read_text()), A003['bones'])
        self.assertEqual(led['bones_covered'] + len(led['bones_without_readiness_region']), 206)
        self.assertEqual(led['bones_without_readiness_region'], [])
        self.assertEqual(led['regions']['humerus']['bones'], ['humerus_left', 'humerus_right'])
        self.assertEqual(led['region_counts'], {'READY': 0, 'PARTIAL': 9, 'BLOCKED': 3})
        self.assertFalse(led['freeze_ready'])
        self.assertEqual(sum(sum(r['a003_placement'].values()) for r in led['regions'].values()), led['bones_covered'])


if __name__ == '__main__':
    unittest.main()
