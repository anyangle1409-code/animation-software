"""Amplitude provenance: committed a003/c003/c004 results pinned (every commanded peak traced; thumb intermetacarpal
targets measured at peak) and each rule proven by mutation (an untraceable peak, a split without stated basis, a removed
TEST AMPLITUDE label, an unreached intermetacarpal target)."""
import copy, json, sys, unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts/anatomy_fit'))
import amplitude_provenance_audit as m  # noqa: E402

A = ROOT / 'ORIGINAL_V1_WORK/anatomy'
O = A / 'audit/amplitude_provenance'
REC = json.loads((A / 'character_fit_r95_a003.json').read_text())
ATLAS = json.loads((A / 'whole_body_movement_atlas.json').read_text())
SPECS = {t['id']: t for t in m.it.specs(REC, ATLAS)}


class Committed(unittest.TestCase):
    def test_all_traced(self):
        for n in ('a003_isolated_014', 'c003_isolated_001', 'c004_isolated_001'):
            d = json.loads((O / f'{n}.json').read_text())
            self.assertEqual((d['status'], d['tests'], d['peaks'], d['untraced']), ('TRACED', 135, 278, []), n)
            self.assertEqual(d['by_kind'], {'CONDITION_IN_TEST_ID': 10, 'DRIVEN_TO_MEASURED_TARGET': 2, 'EXACT_CONTEXT': 100, 'HALF_OF_SOURCED_TOTAL': 76,
                                            'LABELLED_TEST_AMPLITUDE': 78, 'STATED_IN_BASIS': 8, 'TARGET_MINUS_FITTED_REST': 4}, n)
            k = {(r['channel'], r['peak']): r['kind'] for r in d['detail']['hip_abduction_adduction_left']['peaks']}
            self.assertEqual(set(k.values()), {'LABELLED_TEST_AMPLITUDE'})      # the unsourced hip 20/30 deg stays unsourced
            self.assertEqual(len(d['intermetacarpal_target_reached']), 6)
            self.assertTrue(all(v['reached'] for v in d['intermetacarpal_target_reached'].values()))


class Mutations(unittest.TestCase):
    def kinds(self, t):
        return {(r['channel'], r['peak']): r['kind'] for r in m.classify(t)}

    def test_untraceable_peak(self):
        t = copy.deepcopy(SPECS['knee_flexion_extension_left'])
        t['keys'][2]['flexion'] = 141.3
        self.assertEqual(self.kinds(t)[('flexion', 141.3)], 'UNTRACED')

    def test_test_amplitude_statement_beats_coincidental_match(self):
        t = copy.deepcopy(SPECS['talocrural_dorsi_plantarflexion_left'])
        self.assertEqual(self.kinds(t)[('angle', 20.0)], 'LABELLED_TEST_AMPLITUDE')
        t['amplitude_basis'] = 'CDC ankle-foot complex mean'
        self.assertNotEqual(self.kinds(t)[('angle', 20.0)], 'LABELLED_TEST_AMPLITUDE')

    def test_population_text_is_not_a_source(self):
        t = copy.deepcopy(SPECS['knee_flexion_extension_left'])
        self.assertIn('674', json.dumps(t['context']))
        t['keys'][2]['flexion'] = 674.0                                       # a sample size, not a value
        self.assertEqual(self.kinds(t)[('flexion', 674.0)], 'UNTRACED')

    def test_length_channel_units(self):
        t = copy.deepcopy(SPECS['tmj_opening'])
        self.assertEqual(self.kinds(t)[('glide', 0.016)], 'LABELLED_TEST_AMPLITUDE')
        for k in t['keys']:
            if k.get('glide'):
                k['glide'] = 0.017
        self.assertEqual(self.kinds(t)[('glide', 0.017)], 'UNTRACED')

    def test_split_requires_stated_basis(self):
        t = copy.deepcopy(SPECS['thoracic_t1_t2_flexion'])
        self.assertEqual(self.kinds(t)[('flexion', 0.95)], 'HALF_OF_SOURCED_TOTAL')
        t['amplitude_basis'] = t['amplitude_basis'].replace('Half', 'One').replace('half', 'one').replace('split', 'spread')
        self.assertEqual(self.kinds(t)[('flexion', 0.95)], 'UNTRACED')

    def test_test_amplitude_label_required(self):
        tid = next(k for k, v in SPECS.items() if 'TEST AMPLITUDE' in (v.get('amplitude_basis') or '').upper()
                   and any(r['kind'] == 'LABELLED_TEST_AMPLITUDE' for r in m.classify(v)))
        t = copy.deepcopy(SPECS[tid]); t['amplitude_basis'] = 'unspecified'
        self.assertIn('UNTRACED', self.kinds(t).values())

    def test_target_minus_rest_exactness(self):
        t = copy.deepcopy(SPECS['thumb_cmc_radial_abduction_left'])
        self.assertIn('TARGET_MINUS_FITTED_REST', self.kinds(t).values())
        t['intermetacarpal']['rest_angle_deg'] += 0.01
        self.assertIn('UNTRACED', self.kinds(t).values())

    def test_unreached_intermetacarpal_target(self):
        S = json.loads((A / 'audit/runs/isolated_bone_only_014/isolated_samples.json').read_text())
        S = {k: S[k] for k in ('thumb_cmc_radial_abduction_left',)}
        for f in S['thumb_cmc_radial_abduction_left']:
            f['intermetacarpal_angle_deg'] -= 0.1 * (abs(f['intermetacarpal_angle_deg'] - 23.5) > 1)
        r = m.audit(REC, ATLAS, S)
        self.assertFalse(r['intermetacarpal_target_reached']['thumb_cmc_radial_abduction_left']['reached'])
        self.assertEqual(r['status'], 'GAPS')


if __name__ == '__main__':
    unittest.main()
