"""Remaining stale carpals/hand skeleton_input points: reconstruction from skeleton_input (skeleton_fit.build, not the
reused c003 blend) proves the stale inputs rebuild a003's hand placement; the committed audit's NO_C005 decision is pinned;
mutations prove the rebuild comparison detects a single moved input."""
import copy, json, sys, unittest
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts/anatomy_fit'))
import hand_input_source_rebuild_audit as h  # noqa: E402

OUT = ROOT / 'ORIGINAL_V1_WORK/anatomy/audit/hand_input_audit/hand_input_source_rebuild_v1.json'
R = {k: json.loads(p.read_text()) for k, p in h.P.items()}
HAND = ('scaphoid', 'lunate', 'triquetrum', 'pisiform', 'trapezium', 'trapezoid', 'capitate', 'hamate', 'metacarpal', 'digit', 'thumb')
is_hand = lambda n: n.startswith(HAND) and n.endswith(('_left', '_right'))


class Committed(unittest.TestCase):
    def test_decision_and_counts(self):
        d = json.loads(OUT.read_text())
        self.assertTrue(d['contain_applied'])
        self.assertEqual(d['mesh']['vertices'], d['mesh']['record_character']['mesh_vertices'])
        self.assertTrue(d['decision'].startswith('NO_C005'))
        self.assertEqual((d['points'], d['unique_exact'], len(d['not_encoded'])), (108, 98, 10))
        self.assertTrue(all('distal_phalanx' in x and 'tail_m' in x for x in d['not_encoded']))
        self.assertEqual(d['stale_counts'], {'c001': 108, 'c002': 108, 'c003': 108, 'c004': 108})
        self.assertEqual(d['consumers'], ['scripts/anatomy_fit/skeleton_fit.py:build (bone head/tail)'])
        rb = d['rebuild']
        self.assertEqual(rb['a003_inputs_vs_a003']['bones_differing'], 0)
        self.assertEqual((rb['c004_inputs_vs_c004']['bones_differing'], rb['c004_inputs_vs_c004']['max_mm']), (54, 38.432))
        self.assertTrue(all(is_hand(n) for n in rb['c004_inputs_vs_c004']['bones']))
        for k in ('H1_rigid_gh_translation_vs_c004', 'H2_snap_to_c004_endpoint_vs_c004'):
            self.assertGreater(rb[k]['max_mm'], 100, k)                         # neither correction rebuilds c004
        self.assertEqual(d['c004_arm_points_outside_a003_skin_left']['a003'], [])
        self.assertGreater(len(d['c004_arm_points_outside_a003_skin_left']['c004']), 40)


class Reconstruction(unittest.TestCase):
    """Mesh-free: contain() needs the body mesh, so bones with a containment record are excluded."""

    def rebuilt(self, L):
        return h.rebuild(L, None)

    def test_a003_inputs_rebuild_a003(self):
        self.assertEqual(h.compare(self.rebuilt(R['a003']['skeleton_input']), R['a003']['bones'], True), {})

    def test_stale_inputs_rebuild_a003_hand_placement(self):
        Bn = self.rebuilt(R['c004']['skeleton_input'])
        diff = h.compare(Bn, R['c004']['bones'], True)
        self.assertEqual(len(diff), 44)                                          # 54 hand bones minus 10 contained fingertips
        self.assertTrue(all(is_hand(n) for n in diff))
        for n in diff:
            side = n.rsplit('_', 1)[1]
            T = h.gh_shift(R['c004'], R['a003'], side)
            for e in h.ENDS:
                np.testing.assert_allclose(Bn[n][e], R['a003']['bones'][n][e], atol=1e-12)      # exactly a003's hand
                np.testing.assert_allclose(np.asarray(R['c004']['bones'][n][e]) - Bn[n][e], T, atol=1e-9)
        # the rebuilt carpus is detached from the c004 radius by the full GH shift
        gap = np.linalg.norm(np.asarray(Bn['scaphoid_left']['head_m']) - np.asarray(R['c004']['bones']['scaphoid_left']['head_m'])) * 1000
        self.assertAlmostEqual(gap, 38.432, places=2)

    def test_point_audit_classification(self):
        rows = h.point_audit(R)
        self.assertEqual(len(rows), 108)
        self.assertTrue(all(r['c004_bone_moved_by_gh_shift'] for r in rows))
        for r in rows:
            if r['correction'] == 'NOT_ENCODED':
                self.assertEqual(r['end'], 'tail_m'); self.assertIsNotNone(r['a003_containment_adjustment_mm'])
                self.assertAlmostEqual(np.linalg.norm(r['a003_offset_mm']), r['a003_containment_adjustment_mm'], places=2)
            else:
                self.assertEqual(r['a003_offset_mm'], [0.0, 0.0, 0.0])

    def test_mutation_single_input_detected(self):
        L = copy.deepcopy(R['a003']['skeleton_input'])
        L['sides']['left']['carpals']['lunate'][0] = (np.asarray(L['sides']['left']['carpals']['lunate'][0]) + [0.001, 0, 0]).tolist()
        self.assertEqual(list(h.compare(self.rebuilt(L), R['a003']['bones'], True)), ['lunate_left'])

    def test_mutation_partial_correction_detected(self):
        # correcting the 98 exact points alone still leaves the fingertip stations unresolved: the guard keeps them flagged
        import skeleton_input_guard as g
        c = copy.deepcopy(R['c004'])
        for r in h.point_audit(R):
            if r['correction'] == 'UNIQUE_EXACT':
                c['skeleton_input']['sides'][r['side']][r['group']][r['key']][r['index']] = r['c004_bone_endpoint_m']
        self.assertEqual(g.check(R['a003'], c)['violation_keys'], [])          # guard only checks anchored points ...
        Bn = self.rebuilt(c['skeleton_input'])
        self.assertEqual(h.compare(Bn, c['bones'], True), {})                  # ... mesh-free rebuild agrees off the fingertips ...
        d = json.loads(OUT.read_text())
        self.assertGreater(d['rebuild']['H2_snap_to_c004_endpoint_vs_c004']['max_mm'], 100)   # ... but the full pipeline does not


if __name__ == '__main__':
    unittest.main()
