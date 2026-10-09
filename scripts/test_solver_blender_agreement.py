"""Solver <-> Blender agreement: committed a003/c003 results pinned; detectors proven by mutation (spec/series drift,
evaluated-delta corruption, uncomposed-delta substitution, measured-channel corruption, test missing from current specs)."""
import copy, json, sys, unittest
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts/anatomy_fit'))
import solver_blender_agreement as m  # noqa: E402

A = ROOT / 'ORIGINAL_V1_WORK/anatomy'
O = A / 'audit/solver_blender_agreement'
REC = json.loads((A / 'character_fit_r95_a003.json').read_text())
ATLAS = json.loads((A / 'whole_body_movement_atlas.json').read_text())
S = json.loads((A / 'audit/runs/isolated_bone_only_014/isolated_samples.json').read_text())
SUB = ('digit3_flexion_left', 'thumb_cmc_anteposition_left', 'knee_flexion_with_patellar_follower_right')


class Committed(unittest.TestCase):
    def test_both_agree(self):
        for name in ('a003_isolated_014', 'c003_isolated_001'):
            d = json.loads((O / f'{name}.json').read_text())
            self.assertEqual(d['status'], 'AGREE', name)
            self.assertEqual((d['tests_in_samples'], d['frames'], d['deltas_compared']), (135, 9575, 13509))
            self.assertEqual((d['series_drift_tests'], d['evaluation_failure_count'], d['measurement_failure_count']), ([], 0, 0))
            self.assertLess(d['worst_composed_delta'], 1e-5)
            self.assertGreater(d['worst_uncomposed_delta_info'], 1.0)          # composition matters: not a tautology
            self.assertGreater(d['channels_compared'], 49000)


class Mutations(unittest.TestCase):
    def sub(self):
        return {k: copy.deepcopy(S[k]) for k in SUB}

    def test_clean_subset_agrees(self):
        self.assertEqual(m.audit(REC, ATLAS, self.sub())['status'], 'AGREE')

    def test_series_drift_detected(self):
        s = self.sub(); fr = s['digit3_flexion_left'][len(s['digit3_flexion_left']) // 2]
        k = next(iter(fr['commanded'])); fr['commanded'][k] += 0.5
        r = m.audit(REC, ATLAS, s)
        self.assertIn('digit3_flexion_left', r['series_drift_tests'])

    def test_evaluated_delta_corruption_detected(self):
        s = self.sub(); fr = s['knee_flexion_with_patellar_follower_right'][30]
        b = next(iter(fr['moving_deltas'])); D = np.array(fr['moving_deltas'][b]); D[0, 3] += 1e-4; fr['moving_deltas'][b] = D.tolist()
        self.assertEqual(m.audit(REC, ATLAS, s)['evaluation_failure_count'], 1)

    def test_uncomposed_substitution_detected(self):
        s = self.sub(); t = {x['id']: x for x in m.it.specs(REC, ATLAS)}['digit3_flexion_left']
        F = m.it.frames(REC); fr = max(s['digit3_flexion_left'], key=lambda f: sum(abs(v) for v in f['commanded'].values()))
        G = m.it.deltas(t, fr['commanded'], F)
        b = 'digit3_distal_phalanx_left'; fr['moving_deltas'][b] = G[b].tolist()          # child delta without its ancestors
        r = m.audit(REC, ATLAS, s)
        self.assertGreaterEqual(r['evaluation_failure_count'], 1)
        self.assertIn(b, [x['bone'] for x in r['evaluation_failures']])

    def test_measured_channel_corruption_detected(self):
        s = self.sub(); fr = s['thumb_cmc_anteposition_left'][20]
        fr['intermetacarpal_angle_deg'] += 0.01
        r = m.audit(REC, ATLAS, s)
        self.assertEqual([x['channel'] for x in r['measurement_failures']], ['intermetacarpal_angle_deg'])

    def test_unknown_test_detected(self):
        s = self.sub(); s['renamed_test_left'] = s.pop('digit3_flexion_left')
        r = m.audit(REC, ATLAS, s)
        self.assertEqual((r['status'], r['missing_from_current_specs']), ('DISAGREE', ['renamed_test_left']))


if __name__ == '__main__':
    unittest.main()
