"""Regression: mirror comparability of left/right isolated-test commands must ignore float noise but still separate
genuinely side-specific source amplitudes (defect found on the shoulder_proposal_c001 movement run)."""
import json, sys, unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts/anatomy_fit'))
import isolated_tests as it  # noqa: E402

RUN001 = ROOT / 'ORIGINAL_V1_WORK/anatomy/audit/runs/isolated_bone_only_c001_shoulder_proposal_001/mirror_comparability_fixture.json'


class Comparability(unittest.TestCase):
    def test_float_noise_matches(self):
        self.assertTrue(it.commands_match([{'angle': 0.7106317040852255}], [{'angle': 0.7106317040852432}]))
        self.assertFalse([{'angle': 0.7106317040852255}] == [{'angle': 0.7106317040852432}])   # the old exact check failed here

    def test_side_specific_amplitudes_do_not_match(self):
        self.assertFalse(it.commands_match([{'internal': 0.5408254949385535}], [{'internal': 0.5579557142352498}]))

    def test_structure_differences_do_not_match(self):
        self.assertFalse(it.commands_match([{'angle': 1.0}], [{'angle': 1.0}, {'angle': 2.0}]))
        self.assertFalse(it.commands_match([{'angle': 1.0}], [{'abduction': 1.0}]))
        self.assertTrue(it.commands_match([{'pronation': 0.0}], [{'pronation': 0.0}]))

    def test_run001_thumb_noise_and_hip_asymmetry(self):
        s = json.loads(RUN001.read_text())['series']
        for t in ('thumb_cmc_radial_abduction', 'thumb_cmc_anteposition', 'thumb_opposition'):
            L, R = s[t + '_left'], s[t + '_right']
            self.assertNotEqual(L, R); self.assertTrue(it.commands_match(L, R), t)
        for t in ('hip_rotation_at_0_flexion', 'hip_rotation_at_90_flexion'):
            self.assertFalse(it.commands_match(s[t + '_left'], s[t + '_right']), t)

    def test_runs_after_fix(self):
        runs = ROOT / 'ORIGINAL_V1_WORK/anatomy/audit/runs'
        r1 = json.loads((runs / 'isolated_bone_only_c001_shoulder_proposal_001/isolated_report.json').read_text())['counts']
        self.assertEqual((r1['mirror_pass'], r1['mirror_solver_test_only']), (38, 5))          # run that exposed the defect
        for d in ('isolated_bone_only_c001_shoulder_proposal_002', 'isolated_bone_only_a003_mirror_fix_recheck_001', 'isolated_bone_only_014'):
            c = json.loads((runs / d / 'isolated_report.json').read_text())
            self.assertEqual(c['counts'], {'tests': 135, 'integrity_pass': 135, 'mirror_pairs': 43, 'mirror_pass': 41, 'mirror_solver_test_only': 2}, d)
            self.assertEqual(sorted(k for k, v in c['mirror'].items() if v['status'] != 'PASS'), ['hip_rotation_at_0_flexion', 'hip_rotation_at_90_flexion'], d)
        c2 = json.loads((runs / 'isolated_bone_only_c001_shoulder_proposal_002/isolated_report.json').read_text())['provenance']
        self.assertTrue(c2['source_sha256'].startswith('63ef703ef3a3b160')); self.assertEqual(c2['source_sha256'], c2['source_sha256_after'])


if __name__ == '__main__':
    unittest.main()
