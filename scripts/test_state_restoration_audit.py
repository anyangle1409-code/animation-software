"""State-restoration audit of the isolated runner (recorded Blender results for a003 and c003; the harness itself needs
Blender and is run outside the unit suite)."""
import hashlib, json, unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
O = ROOT / 'ORIGINAL_V1_WORK/anatomy/audit/state_restoration_audit'
SRC = {'a003': ROOT / 'ORIGINAL_V1_WORK/anatomy/audit/HGPT_ANATOMICAL_AUDIT_r95_a003.blend',
       'c003': ROOT / 'ORIGINAL_V1_WORK/anatomy/audit/candidates/shoulder_thorax_c003_ansur_coupled/HGPT_ANATOMICAL_AUDIT_r95_a003_shoulder_thorax_c003_ansur_coupled.blend'}


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


class Restoration(unittest.TestCase):
    def test_all_scenarios(self):
        for name, src in SRC.items():
            d = json.loads((O / f'{name}.json').read_text())
            self.assertEqual(d['source_sha256'], sha(src), name)
            self.assertEqual(d['runner_sha256'], sha(ROOT / 'scripts/anatomy_fit/run_isolated_tests_blender.py'))
            S = d['scenarios']
            self.assertEqual(set(S), {'normal', 'fail_mid_measure', 'interrupt_mid_measure', 'fail_during_authoring'})
            for k, r in S.items():
                self.assertTrue(r['source_sha256_unchanged'], (name, k))
                self.assertEqual(r['source_reopened_state_diff_vs_before'], [], (name, k))
                self.assertEqual(r['session_frame_after'], [1, 0.0], (name, k))
            n = S['normal']
            self.assertIsNone(n['raised']); self.assertTrue(n['report_exists'] and n['samples_exists'])
            self.assertTrue(n['report_frame_restored']); self.assertTrue(n['report_test_blend_sha_matches_file'])
            for k in ('fail_mid_measure', 'interrupt_mid_measure'):
                r = S[k]
                self.assertIsNotNone(r['raised']); self.assertFalse(r['report_exists'] or r['samples_exists'])   # no partial evidence
                self.assertGreater(r['observed']['frame_at_failure'], r['observed']['measure_start_frame'])      # failed mid-sweep
                self.assertTrue(r['test_blend_exists'])                                                           # authored, unmeasured (recorded)
            self.assertIn('KeyboardInterrupt', S['interrupt_mid_measure']['raised'])
            a = S['fail_during_authoring']
            self.assertFalse(a['test_blend_exists'] or a['report_exists'])
            for k in ('normal', 'fail_mid_measure', 'interrupt_mid_measure'):
                r = S[k]
                self.assertEqual(r['test_blend_state_diff_vs_source'], ['armature_has_action', 'frame_range'], (name, k))
                self.assertTrue(r['test_blend_constraints_equal_source'] and r['test_blend_drivers_equal_source'])
                self.assertEqual(r['test_blend_frame'], [1, 0.0])


if __name__ == '__main__':
    unittest.main()
