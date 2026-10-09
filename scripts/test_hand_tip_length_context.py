"""Read-only tip-length context must never turn population agreement into acceptance."""
import copy
import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts/anatomy_fit'))
import hand_tip_length_context as h
A = ROOT / 'ORIGINAL_V1_WORK/anatomy'


class HandTipLengthContextTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rec = json.loads((A / 'character_fit_r95_a003.json').read_text())
        cls.source = next(s for s in json.loads((A / 'canonical_proportion_sources_v1.json').read_text())['sources']
                          if s['id'] == 'DOGAN_1998_HAND_RELATIONS')

    def test_every_raw_distal_span_remains_unvalidated(self):
        r = h.analyse(self.rec, self.source)
        self.assertEqual(len(r['rows']), 10)
        self.assertTrue(all(x['raw_context_standardized_difference'] > 2 for x in r['rows']))
        self.assertFalse(r['anatomical_acceptance'])
        self.assertFalse(r['coordinate_replacement_allowed'])

    def test_mm_conversion_and_bilateral_values(self):
        r = h.analyse(self.rec, self.source)['rows']
        left = {x['bone_base']: x for x in r if x['side'] == 'left'}
        right = {x['bone_base']: x for x in r if x['side'] == 'right'}
        for key, value in zip(h.BONES, (31, 27, 30, 28, 22)):
            self.assertAlmostEqual(left[key]['raw_span_mm'], value, places=3)
            self.assertAlmostEqual(left[key]['raw_span_mm'], right[key]['raw_span_mm'], places=9)
        self.assertEqual(left['digit2_distal_phalanx']['source_mean_mm'], 18)

    def test_inputs_unchanged(self):
        rec, source = copy.deepcopy(self.rec), copy.deepcopy(self.source)
        h.analyse(rec, source)
        self.assertEqual(rec, self.rec)
        self.assertEqual(source, self.source)

    def test_population_agreement_never_accepts_containment(self):
        r = h.analyse(self.rec, self.source)
        self.assertTrue(all(abs(x['stored_context_standardized_difference']) <= 2.01 for x in r['rows']))
        self.assertEqual(r['stored_endpoint_origin'], 'legacy_mesh_containment_not_anatomical_evidence')
        self.assertFalse(r['anatomical_acceptance'])

    def test_zero_sd_rejected(self):
        s = copy.deepcopy(self.source)
        s['male_mean_sd_mm']['thumb_distal_phalanx']['sd'] = 0
        with self.assertRaisesRegex(ValueError, 'positive finite'):
            h.analyse(self.rec, s)

    def test_nonfinite_input_rejected(self):
        r = copy.deepcopy(self.rec)
        r['skeleton_input']['sides']['left']['hand']['th_dp'][1][0] = float('nan')
        with self.assertRaisesRegex(ValueError, 'finite'):
            h.analyse(r, self.source)

    def test_stale_input_frame_rejected(self):
        r = copy.deepcopy(self.rec)
        r['bones']['digit2_distal_phalanx_left']['head_m'][0] += 0.001
        with self.assertRaisesRegex(ValueError, 'input and bone frames'):
            h.analyse(r, self.source)

    def test_missing_containment_history_cannot_claim_origin(self):
        r = copy.deepcopy(self.rec)
        for side in ('left', 'right'):
            for name, key in zip(h.BONES, h.INPUT_KEYS):
                bone = r['bones'][name + '_' + side]
                bone['tail_m'] = list(r['skeleton_input']['sides'][side]['hand'][key][1])
                bone.pop('containment_adjustment_m', None)
        result = h.analyse(r, self.source)
        self.assertEqual(result['stored_endpoint_origin'], 'UNVERIFIED_RECORD_ENDPOINT_ORIGIN')
        self.assertTrue(all(x['endpoint_origin'] == 'UNVERIFIED' for x in result['rows']))

    def test_adjustment_metadata_must_match_observed_offset(self):
        r = copy.deepcopy(self.rec)
        r['bones']['digit2_distal_phalanx_left']['containment_adjustment_m']['tail_m'] += .001
        with self.assertRaisesRegex(ValueError, 'containment metadata'):
            h.analyse(r, self.source)

    def test_derived_infinite_comparison_rejected(self):
        s = copy.deepcopy(self.source)
        s['male_mean_sd_mm']['thumb_distal_phalanx']['sd'] = 5e-324
        with self.assertRaisesRegex(ValueError, 'finite standardized'):
            h.analyse(self.rec, s)


if __name__ == '__main__':
    unittest.main()
