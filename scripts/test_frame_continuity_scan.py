"""Frame-continuity scan: both committed runs are clean, and each defect class is detected when injected (mutation tests)."""
import copy, json, math, sys, unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts/anatomy_fit'))
import frame_continuity_scan as m  # noqa: E402

O = ROOT / 'ORIGINAL_V1_WORK/anatomy/audit/frame_continuity_scan'
RUNS = ROOT / 'ORIGINAL_V1_WORK/anatomy/audit/runs'
SAMPLES = json.loads((RUNS / 'isolated_bone_only_014/isolated_samples.json').read_text())
T = 'knee_flexion_extension_left'


def kinds(frames):
    return {i['kind'] for i in m.check_test(frames)[0]}


class Committed(unittest.TestCase):
    def test_both_runs_clean_and_reproducible(self):
        for name, smp in (('a003_isolated_014', RUNS / 'isolated_bone_only_014/isolated_samples.json'),
                          ('c003_isolated_001', RUNS / 'isolated_bone_only_c003_shoulder_thorax_001/isolated_samples.json')):
            d = json.loads((O / f'{name}.json').read_text())
            summary, tests = m.scan(json.loads(smp.read_text()))
            self.assertEqual(json.loads(json.dumps(summary)), d['summary'], name)
            self.assertEqual(d['summary']['tests'], 135); self.assertEqual(d['summary']['tests_with_issues'], [])
            self.assertEqual(d['summary']['issues_by_kind'], {})
            self.assertLess(d['summary']['global_worst']['det_error'], m.NUM_F32)


class Mutations(unittest.TestCase):
    def setUp(self):
        self.f = copy.deepcopy(SAMPLES[T])

    def test_clean_baseline(self):
        self.assertEqual(kinds(self.f), set())

    def test_reflection_detected(self):
        M = self.f[20]['moving_deltas']['tibia_left']; M[0] = [-x for x in M[0][:3]] + [M[0][3]]
        self.assertIn('improper_transform', kinds(self.f))

    def test_non_finite_detected(self):
        self.f[30]['flexion'] = float('nan')
        self.assertIn('non_finite', kinds(self.f))

    def test_frame_gap_detected(self):
        del self.f[40]
        self.assertIn('frame_gap', kinds(self.f))

    def test_rotation_jump_detected(self):
        c, s = math.cos(math.radians(30)), math.sin(math.radians(30))
        M = self.f[25]['moving_deltas']['tibia_left']
        R = [[M[r][k] for k in range(3)] for r in range(3)]
        Rz = [[c, -s, 0], [s, c, 0], [0, 0, 1]]
        R2 = [[sum(Rz[r][k] * R[k][q] for k in range(3)) for q in range(3)] for r in range(3)]
        for r in range(3):
            M[r][:3] = R2[r]
        self.assertIn('rotation_jump', kinds(self.f))

    def test_not_at_rest_detected(self):
        peak = max(self.f, key=lambda x: abs(x['commanded']['flexion']))           # midpoint of a flex/extend sweep is itself rest
        self.f[-1]['moving_deltas'] = copy.deepcopy(peak['moving_deltas'])
        self.assertIn('not_at_rest', kinds(self.f))

    def test_measured_wrap_detected(self):
        self.f[50]['flexion'] += 360
        self.assertIn('measured_angle_jump', kinds(self.f))


if __name__ == '__main__':
    unittest.main()
