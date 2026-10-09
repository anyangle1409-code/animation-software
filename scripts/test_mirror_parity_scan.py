"""Mirror parity of every moved bone: committed results pinned, and injected motion asymmetry is detected (not excused as
inherited rest asymmetry)."""
import copy, json, math, sys, unittest
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts/anatomy_fit'))
import mirror_parity_scan as m  # noqa: E402

O = ROOT / 'ORIGINAL_V1_WORK/anatomy/audit/mirror_parity_scan'
RUNS = ROOT / 'ORIGINAL_V1_WORK/anatomy/audit/runs'
REC = json.loads((ROOT / 'ORIGINAL_V1_WORK/anatomy/character_fit_r95_a003.json').read_text())
S = json.loads((RUNS / 'isolated_bone_only_014/isolated_samples.json').read_text())
REST_ONLY = ['hallux_mtp_dorsiflexion', 'hip_abduction_adduction', 'hip_flexion_extension', 'knee_flexion_extension',
             'knee_flexion_with_patellar_follower', 'knee_flexion_with_screw_home', 'subtalar_inversion_eversion',
             'talocrural_dorsi_plantarflexion', 'talocrural_with_fibular_follower', 'talonavicular_dorsi_plantarflexion']


def sub(*names):
    return {f'{n}_{s}': copy.deepcopy(S[f'{n}_{s}']) for n in names for s in ('left', 'right')}


def rotz(M, deg):
    c, s = math.cos(math.radians(deg)), math.sin(math.radians(deg))
    R = np.array([[c, -s, 0, 0], [s, c, 0, 0], [0, 0, 1, 0], [0, 0, 0, 1.0]])
    return (R @ np.array(M)).tolist()


class Committed(unittest.TestCase):
    def test_results(self):
        for name in ('a003_isolated_014', 'c003_isolated_001'):
            d = json.loads((O / f'{name}.json').read_text())
            self.assertEqual(d['pairs_compared'], 41); self.assertEqual(d['pairs_failed'], [])
            self.assertEqual(d['pairs_rest_asymmetry_only'], REST_ONLY)
            self.assertEqual(d['side_specific_skipped'], ['hip_rotation_at_0_flexion', 'hip_rotation_at_90_flexion'])
            self.assertLess(d['global_max']['transform'], m.BOUND_T)
            self.assertTrue(all(k.split('_')[0] in ('hallux', 'toe2', 'toe3', 'toe5', 'rib') for k in d['rest_asymmetric_bones_mm']))

    def test_reproduces_subset(self):
        d = json.loads((O / 'a003_isolated_014.json').read_text())
        r = m.scan(REC, sub('knee_flexion_extension', 'elbow_flexion_at_pronation_0'))
        self.assertEqual(r['pairs']['knee_flexion_extension']['status'], d['pairs']['knee_flexion_extension']['status'])
        self.assertEqual(r['pairs']['elbow_flexion_at_pronation_0']['status'], 'PASS')


class Mutations(unittest.TestCase):
    def test_follower_motion_asymmetry_detected(self):
        smp = sub('knee_flexion_with_patellar_follower')
        fr = smp['knee_flexion_with_patellar_follower_right'][40]
        self.assertIn('patella_right', fr['moving_deltas'])
        fr['moving_deltas']['patella_right'] = rotz(fr['moving_deltas']['patella_right'], 0.5)
        self.assertEqual(m.scan(REC, smp)['pairs']['knee_flexion_with_patellar_follower']['status'], 'FAIL')

    def test_commanded_asymmetry_detected_for_carried_descendants(self):
        smp = sub('elbow_flexion_at_pronation_0')
        fr = smp['elbow_flexion_at_pronation_0_right'][30]
        b = next(iter(fr['moving_deltas']))
        fr['moving_deltas'][b] = rotz(fr['moving_deltas'][b], 0.2)
        r = m.scan(REC, smp)['pairs']['elbow_flexion_at_pronation_0']
        self.assertEqual(r['status'], 'FAIL'); self.assertGreater(r['displacement_m'], 1e-5)


if __name__ == '__main__':
    unittest.main()
