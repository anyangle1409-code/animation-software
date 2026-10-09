"""Evidence queue must retain every unsupported peak and refuse silent omissions."""
import copy
import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts/anatomy_fit'))
import movement_evidence_queue as q


class MovementEvidenceQueueTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        a = ROOT / 'ORIGINAL_V1_WORK/anatomy'
        cls.specs = q.provenance.it.specs(json.loads((a / 'character_fit_r95_a003.json').read_text()),
                                        json.loads((a / 'whole_body_movement_atlas.json').read_text()))

    def test_all_unsupported_peaks_retained_without_reclassification(self):
        result = q.build(self.specs)
        self.assertEqual((result['peak_count'], result['test_count']), (78, 49))
        self.assertEqual(sum(result['by_family'].values()), 78)
        self.assertTrue(all(r['status'] == 'UNSOURCED_TEST_AMPLITUDE' for r in result['peaks']))
        self.assertFalse(result['anatomical_acceptance'])
        self.assertFalse(result['existing_limits_changed'])

    def test_unknown_family_fails_instead_of_dropping_peak(self):
        specs = copy.deepcopy(self.specs)
        t = next(t for t in specs if t['id'] == 'tmj_opening')
        t['id'] = 'new_unreviewed_joint'
        with self.assertRaisesRegex(ValueError, 'unmapped'):
            q.build(specs)

    def test_untraced_peak_fails_instead_of_disappearing(self):
        specs = copy.deepcopy(self.specs)
        t = next(t for t in specs if t['id'] == 'tmj_opening')
        for k in t['keys']:
            if k.get('angle') == 25:
                k['angle'] = 26
        with self.assertRaisesRegex(ValueError, 'untraced'):
            q.build(specs)

    def test_unreviewed_digit_motion_is_not_extension(self):
        specs = copy.deepcopy(self.specs)
        t = next(t for t in specs if t['id'] == 'digit2_flexion_left')
        t['id'] = 'digit2_mcp_abduction_left'
        with self.assertRaisesRegex(ValueError, 'unmapped'):
            q.build(specs)
        for channel, peak in [('abduction', -27), ('mcp', 27)]:
            specs = copy.deepcopy(self.specs)
            t = next(t for t in specs if t['id'] == 'digit2_flexion_left')
            t['keys'] = [{channel: 0}, {channel: peak}]
            t['amplitude_basis'] = 'TEST AMPLITUDE 27 deg'
            with self.assertRaisesRegex(ValueError, 'unmapped'):
                q.build(specs)

    def test_glide_retains_metres_and_separate_mm_value(self):
        rows = q.build(self.specs)['peaks']
        r = next(r for r in rows if r['test'] == 'tmj_opening' and r['channel'] == 'glide')
        self.assertEqual((r['peak'], r['units'], r['peak_mm']), (0.016, 'm', 16.0))

    def test_conditioning_angle_is_not_a_rom_limit(self):
        rows = q.build(self.specs)['peaks']
        conditioned = [r for r in rows if r['family'] == 'knee_conditioning']
        self.assertEqual(len(conditioned), 4)
        self.assertTrue(all(r['role'] == 'conditioning_pose' for r in conditioned))

    def test_c004_has_identical_unsupported_peak_semantics(self):
        a = ROOT / 'ORIGINAL_V1_WORK/anatomy'
        rec = json.loads((a / 'audit/candidates/shoulder_thorax_c004_arm_inputs/candidate_record.json').read_text())
        atlas = json.loads((a / 'whole_body_movement_atlas.json').read_text())
        self.assertEqual(q.build(q.provenance.it.specs(rec, atlas)), q.build(self.specs))


if __name__ == '__main__':
    unittest.main()
