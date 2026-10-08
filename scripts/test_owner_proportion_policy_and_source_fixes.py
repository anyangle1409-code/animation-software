"""Owner proportion decision (8 Oct 2026) and the real-skeleton data fixes it was recorded with."""
import importlib.util, json, unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ANAT = ROOT / 'ORIGINAL_V1_WORK/anatomy'
load = lambda n: json.loads((ANAT / n).read_text())


class OwnerProportionPolicy(unittest.TestCase):
    def test_decision_recorded_without_promotion(self):
        for name in ('canonical_target_selection_v1.json', 'canonical_freeze_readiness_v1.json'):
            d = load(name)
            dec = {x['id']: x for x in d['owner_decisions']}['PROPORTION_POLICY_182CM_MALE']
            self.assertIn('1.82 m adult male', dec['decision'])
            self.assertIn('mesh is refitted', dec['decision'])
        self.assertIs(load('canonical_target_selection_v1.json')['freeze_ready'], False)
        r = load('canonical_freeze_readiness_v1.json')
        self.assertEqual(r['overall_status'], 'NOT_READY_FOR_NEW_CANONICAL_BLENDER_REVISION')
        self.assertTrue(any('owner policy' in b for b in r['regions']['forearm']['blockers']))
        self.assertTrue(any('de Leva' in b and 'femur' in b for b in r['regions']['lower_limb_long_bones']['blockers']))

    def test_every_bone_has_a_readiness_region(self):
        spec = importlib.util.spec_from_file_location('cp2', ROOT / 'scripts/anatomy_fit/cp2_preflight.py')
        m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
        inv, _, _ = m.load_reference()
        led = m.readiness_ledger(inv, load('canonical_freeze_readiness_v1.json'), load('canonical_target_selection_v1.json'),
                                 load('character_fit_r95_a003.json')['bones'])
        self.assertEqual(led['bones_without_readiness_region'], [])
        self.assertEqual(led['regions']['humerus']['readiness'], 'PARTIAL')
        self.assertTrue(any('sternum' in b for b in load('canonical_freeze_readiness_v1.json')['regions']['ribs']['blockers']))


class SourceFixes(unittest.TestCase):
    def test_talus_partial_measure_is_not_a_whole_bone_reference(self):
        t = load('canonical_tarsal_geometry_audit_v1.json')
        self.assertNotIn('talus_length_male', t['direct_whole_bone_reference_examples_mm'])
        self.assertEqual(t['excluded_partial_measure_references_mm']['talus_length_male_ZHANG_2018']['mean'], 44.375)

    def test_c2_dispersion_is_not_used_as_an_sd(self):
        stack = load('canonical_spine_level_stack_v1.json')['vertebral_bodies_mm']['C2']['anterior_height_mm']
        sel = load('canonical_target_selection_v1.json')['regions']['spine']['selected']['C2_body_geometry']['anterior_male_CT_mm']
        self.assertIsNone(stack['male_CT_sd']); self.assertEqual(stack['male_CT_printed_dispersion'], 0.66)
        self.assertIsNone(sel['sd']); self.assertEqual(sel['printed_dispersion'], 0.66)
        self.assertEqual(sel['mean'], 20.8)

    def test_register_annotations(self):
        S = {s['id']: s for s in load('canonical_proportion_sources_v1.json')['sources']}
        self.assertTrue(S['MANDIBLE_POSTMORTEM_INDIA_2023']['quarantine'].startswith('QUARANTINED'))
        self.assertIn('coronoid base', S['RAUSCH_2018_RADIAL_HEAD_FOREARM']['measurement_definition'])
        self.assertIn('per-bone', S['CLAVICLE_QIU_2016_ARTICULAR_CENTRE_CHORD']['sd_basis'])
        self.assertIn('per-bone', load('canonical_clavicle_endpoint_crosscheck_v1.json')['source']['male_chord_mm']['sd_basis'])
        self.assertIn('not whole-talus', S['ZHANG_2018_TALUS_MALE']['measurement_caution'])


if __name__ == '__main__':
    unittest.main()
